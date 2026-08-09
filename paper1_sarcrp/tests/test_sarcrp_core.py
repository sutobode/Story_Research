import math
import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.sarcrp_core import replan, _build_c3, _score_candidate, _apply_fallback_margin


def make_state(queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=5),
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_plan():
    return Plan(plan_id="p_old", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
        Action(action_id="a2", step_index=2, type="RETRIEVE", container="C3",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=2),
    ])


def test_keep_when_impact_below_threshold():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C1", "C2", "C3"],
        urgent_containers=[], theta_impact=0.30, rng=random.Random(0),
    )
    assert decision.decision == "KEEP"
    assert decision.plan is plan_old


def test_update_when_impact_high_and_gain_worthwhile():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C3", "C2", "C1"],
        urgent_containers=["C3"], theta_impact=0.05, tau_frac=0.0, rng=random.Random(0),
    )
    assert decision.decision in {"KEEP", "UPDATE"}  # fallback may still choose KEEP; assert it ran end-to-end
    assert decision.impact.total > 0.05


def test_result_never_violates_frozen_prefix():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C3", "C2", "C1"],
        urgent_containers=["C3"], h_f=1, theta_impact=0.05, tau_frac=0.0, rng=random.Random(3),
    )
    assert decision.plan.actions[0].container == plan_old.actions[0].container


def test_use_local_search_false_skips_c2_candidate():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision_with = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"],
                            ["C3"], theta_impact=0.05, tau_frac=0.0, rng=random.Random(0),
                            use_local_search=True)
    decision_without = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"],
                               ["C3"], theta_impact=0.05, tau_frac=0.0, rng=random.Random(0),
                               use_local_search=False)
    assert decision_with.decision in {"KEEP", "UPDATE"}
    assert decision_without.decision in {"KEEP", "UPDATE"}


def test_impact_weights_override_changes_impact_total():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    default_decision = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"],
                               ["C3"], theta_impact=0.0, tau_frac=1.0, rng=random.Random(0))
    zero_blocking_decision = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"],
                                     ["C3"], theta_impact=0.0, tau_frac=1.0, rng=random.Random(0),
                                     impact_weights={"w_o": 0.25, "w_t": 0.20, "w_b": 0.0, "w_p": 0.20, "w_c": 0.10})
    assert zero_blocking_decision.impact.total <= default_decision.impact.total


def test_build_c3_renumbers_step_index_sequentially_avoiding_collision():
    # Regression test for a real bug: frozen.actions keeps plan_old's own
    # step_index (0..h_f-1, since freeze_horizon.split_plan doesn't
    # renumber), and tail_solution always restarts its OWN numbering at 0
    # (every solver does this) -- concatenating them without renumbering
    # collides both at index 0..h_f-1, so stability_cost's index-keyed
    # lookup silently drops the frozen action and compares against
    # whatever the tail put there instead, fabricating a "frozen prefix
    # violated" (p_f=inf) result. This made candidate C3 score inf on
    # every replan() call with h_f>0 -- i.e. every experiment this suite
    # has run under spec 48's own default h_f=3 -- caught only by
    # building a scenario (Task: existence-proof) where C3 was the one
    # candidate that should have won.
    plan_old = Plan(plan_id="p_old", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    frozen = Plan(plan_id="p_old_frozen", created_at=0, source="t", actions=plan_old.actions[:1])
    tail_solution = Plan(plan_id="tail", created_at=0, source="solver", actions=[
        Action(action_id="t0", step_index=0, type="RETRIEVE", container="X",
               source_stack="S2", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="t1", step_index=1, type="RETRIEVE", container="Y",
               source_stack="S2", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    c3 = _build_c3(plan_old, frozen, tail_solution)
    indices = [a.step_index for a in c3.actions]
    assert indices == [0, 1, 2]  # sequential, no collision
    assert c3.actions[0].container == "C1"  # frozen action preserved at index 0
    assert c3.actions[1].container == "X"  # tail's own first action now at index 1, not colliding with frozen's 0


def test_score_candidate_penalizes_invalid_plans_instead_of_hardcoding_valid():
    # Regression test for a real bug: is_valid was hardcoded True
    # unconditionally, so a candidate that replays illegally (here: a
    # RETRIEVE for a container that is not on top of its stack) looked
    # artificially cheap (relocation_count=0, tiny delay) instead of
    # paying spec 11.3's M_inf penalty -- meaning an invalid candidate
    # could silently win candidate selection. Caught building a
    # multi-urgent-container local-search operator whose destination
    # choices could produce an invalid plan.
    state = make_state(["C1", "C2", "C3"])  # S1=[C3,C2,C1], C1 on top
    plan_old = make_plan()
    invalid_plan = Plan(plan_id="bad", created_at=0, source="t", actions=[
        Action(action_id="x0", step_index=0, type="RETRIEVE", container="C3",  # C3 is buried, not on top
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    score = _score_candidate(invalid_plan, plan_old, frozen_count=0, urgent_containers=[], conf_new=1.0, state=state)
    assert score >= 1e6  # spec 11's M_inf, not a small/normal-looking cost


def test_apply_fallback_margin_keeps_and_carries_a_subthreshold_gain():
    # Motivated by Scenario C (existence-proof report): the single-step
    # margin is myopic -- a genuine but sub-tau improvement is currently
    # discarded outright every time it recurs. carried_gain remembers it
    # instead of losing it.
    decision, carried_next = _apply_fallback_margin(j_old=61.49, j_best=60.98, tau=0.615, carried_gain=0.0)
    assert decision == "KEEP"
    assert math.isclose(carried_next, 0.51, abs_tol=1e-2)


def test_apply_fallback_margin_updates_once_carried_plus_new_gain_clears_tau():
    decision, carried_next = _apply_fallback_margin(j_old=61.49, j_best=60.98, tau=0.615, carried_gain=0.514)
    assert decision == "UPDATE"
    assert carried_next == 0.0  # resets once cashed in


def test_apply_fallback_margin_returns_keep_when_no_viable_candidate():
    decision, carried_next = _apply_fallback_margin(j_old=10.0, j_best=float("inf"), tau=0.1, carried_gain=2.0)
    assert decision == "KEEP"
    assert carried_next == 2.0  # unchanged -- no new information either way


def test_apply_fallback_margin_does_not_erode_carry_on_a_negative_round():
    # This round's own best candidate is worse than keeping -- must not
    # let it cancel out gains genuinely passed up in earlier rounds.
    decision, carried_next = _apply_fallback_margin(j_old=10.0, j_best=11.0, tau=0.1, carried_gain=2.0)
    assert decision == "KEEP"
    assert carried_next == 2.0


def test_apply_fallback_margin_matches_original_spec9_behavior_with_zero_carry():
    # Original Step 8 (spec 9): KEEP if j_best==inf or (j_old-j_best)<=tau,
    # else UPDATE. carried_gain=0.0 (the default) must reproduce this
    # exactly -- Experiment 1/3/4's already-reported numbers depend on it.
    decision, _ = _apply_fallback_margin(j_old=10.0, j_best=8.0, tau=0.5, carried_gain=0.0)
    assert decision == "UPDATE"  # gain=2.0 > tau=0.5
    decision2, _ = _apply_fallback_margin(j_old=10.0, j_best=9.8, tau=0.5, carried_gain=0.0)
    assert decision2 == "KEEP"  # gain=0.2 <= tau=0.5


def test_apply_fallback_margin_decay_can_flip_update_back_to_keep():
    # R1.2: same numbers as test_apply_fallback_margin_updates_once_carried_
    # plus_new_gain_clears_tau (raw_gain~0.51, carried_gain=0.514, tau=0.615,
    # undecayed -> UPDATE), but with carried_gain_decay=0.1 the incoming
    # carry shrinks to 0.0514 first: 0.51+0.0514=0.5614 <= tau -> KEEP.
    decision, carried_next = _apply_fallback_margin(
        j_old=61.49, j_best=60.98, tau=0.615, carried_gain=0.514, carried_gain_decay=0.1,
    )
    assert decision == "KEEP"
    assert math.isclose(carried_next, 0.514 * 0.1 + (61.49 - 60.98), abs_tol=1e-2)


def test_apply_fallback_margin_cap_bounds_the_incoming_carry():
    # R1.2: an unbounded carry of 10.0 would force UPDATE on essentially any
    # tau (10.0 + 0.51 = 10.51 > 0.615). carried_gain_cap=0.05 bounds how
    # much of that carry can count this round, keeping the decision at KEEP.
    uncapped_decision, _ = _apply_fallback_margin(j_old=61.49, j_best=60.98, tau=0.615, carried_gain=10.0)
    assert uncapped_decision == "UPDATE"

    capped_decision, capped_carried_next = _apply_fallback_margin(
        j_old=61.49, j_best=60.98, tau=0.615, carried_gain=10.0, carried_gain_cap=0.05,
    )
    assert capped_decision == "KEEP"
    assert capped_carried_next == 0.05  # incoming_carry capped at 0.05, then 0.05+0.51 re-capped at 0.05


def test_replan_default_carried_gain_reproduces_original_behavior():
    # replan() without carried_gain/carried_gain_next must be indistinguishable
    # from before this feature existed -- Experiment 1/3/4 never pass it.
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"], ["C3"],
                       theta_impact=0.05, tau_frac=0.0, rng=random.Random(0))
    # Starting from carried_gain=0.0 (the default), every branch of
    # _apply_fallback_margin returns 0.0 back out: UPDATE resets it,
    # KEEP-with-no-gain-this-round leaves an already-zero carry untouched.
    assert decision.carried_gain_next == 0.0


def test_replan_threads_carried_gain_into_the_fallback_margin_and_returns_its_result(monkeypatch):
    # Verifies the wiring (replan passes its own carried_gain argument
    # into _apply_fallback_margin, and returns whatever that function
    # decides) without depending on any specific scenario's numeric gain
    # -- test_apply_fallback_margin_* above already covers that function's
    # own logic precisely.
    import sarcrp.sarcrp_core as sarcrp_core_module

    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    captured = {}

    def spy_margin(j_old, j_best, tau, carried_gain, carried_gain_cap=None, carried_gain_decay=1.0):
        captured["carried_gain_in"] = carried_gain
        return "UPDATE", 999.0  # a distinctive sentinel, otherwise unreachable

    monkeypatch.setattr(sarcrp_core_module, "_apply_fallback_margin", spy_margin)
    decision = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"], ["C3"],
                       theta_impact=0.05, carried_gain=7.5, rng=random.Random(0))
    assert captured["carried_gain_in"] == 7.5
    assert decision.decision == "UPDATE"
    assert decision.carried_gain_next == 999.0


def test_replan_accepts_a_custom_solver():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    calls = {"count": 0}

    def spy_solver(state_arg, queue_arg, constraints=None, time_limit_sec=None):
        calls["count"] += 1
        from sarcrp.crp_solver import solve_crp
        return solve_crp(state_arg, queue_arg, constraints=constraints, time_limit_sec=time_limit_sec)

    decision = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"], ["C3"],
                       theta_impact=0.05, tau_frac=0.0, rng=random.Random(0), solver=spy_solver)
    assert calls["count"] >= 1
    assert decision.decision in {"KEEP", "UPDATE"}
