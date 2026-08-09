import math
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.impact_estimator import DEFAULT_WEIGHTS, NORMALIZED_WEIGHTS, compute_impact, is_action_affected, _blocking_impact


def make_state(retrieval_queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C5", "C4", "C3", "C2", "C1"], max_tier=5)],
        container_attributes={}, retrieval_queue=retrieval_queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_no_change_gives_zero_order_and_target_impact():
    queue = ["C1", "C2", "C3", "C4", "C5"]
    state = make_state(queue)
    plan = Plan(plan_id="p", created_at=0, source="test", actions=[])
    impact = compute_impact(queue, list(queue), state, state, plan, k=5, conf_new=1.0)
    assert impact.i_order == 0.0
    assert impact.i_target == 0.0
    assert impact.i_conf == 0.0
    assert impact.total == 0.0


def test_full_reversal_gives_max_order_impact():
    old_queue = ["C1", "C2", "C3", "C4", "C5"]
    new_queue = ["C5", "C4", "C3", "C2", "C1"]
    state = make_state(old_queue)
    plan = Plan(plan_id="p", created_at=0, source="test", actions=[])
    impact = compute_impact(old_queue, new_queue, state, state, plan, k=5, conf_new=1.0)
    assert math.isclose(impact.i_order, 1.0, rel_tol=1e-9)


def test_target_change_is_binary():
    old_queue = ["C1", "C2", "C3"]
    new_queue = ["C2", "C1", "C3"]
    state = make_state(old_queue)
    plan = Plan(plan_id="p", created_at=0, source="test", actions=[])
    impact = compute_impact(old_queue, new_queue, state, state, plan, k=3, conf_new=1.0)
    assert impact.i_target == 1.0  # target (rank-0 container) changed from C1 to C2


def test_is_action_affected_rank_shift_beyond_threshold():
    old_queue = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
    new_queue = ["C8", "C1", "C2", "C3", "C4", "C5", "C6", "C7"]  # C7 shifts rank 6->7... use bigger shift
    state = make_state(new_queue)
    action = Action(action_id="a1", step_index=0, type="RELOCATE", container="C1",
                     source_stack="S1", dest_stack="S1", commit_status="planned", planned_time=1)
    assert is_action_affected(action, old_queue, new_queue, state, r_shift=0) is True


def test_blocking_impact_is_zero_when_physical_state_is_unchanged():
    # This is the only situation sarcrp_core.replan ever actually calls
    # compute_impact under today (Paper 1's simulator never executes an
    # action's physical effect onto state.stacks between events -- see
    # docstring on _blocking_impact below), so this is the realistic case,
    # not an edge case.
    queue = ["C1", "C2", "C3", "C4", "C5"]
    state = make_state(queue)
    delta = _blocking_impact(state, state, queue, queue, k=5, sigma_b=2.0)
    assert delta == 0.0


def test_blocking_impact_is_nonzero_when_physical_state_genuinely_differs():
    # Spec 44.3's own pseudocode compares B_old(c) vs B_new(c) -- a real
    # physical blocker-count change -- over union(old_queue[:k], new_queue[:k]).
    # C1 goes from 4 blockers (buried at the bottom of a 5-stack) to 0
    # (alone, after the 4 containers above it were physically removed) --
    # this models what *would* happen if Paper 2's execution layer had
    # actually retrieved C2/C3/C4/C5 in between two impact estimations.
    queue = ["C1", "C2"]
    state_old = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1", "C2", "C3", "C4", "C5"], max_tier=5)],  # C1 at bottom, 4 above it
        container_attributes={}, retrieval_queue=queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    state_new = YardState(
        instance_id="t", time_step=1, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1"], max_tier=5)],  # C2-C5 physically retrieved
        container_attributes={}, retrieval_queue=queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    delta = _blocking_impact(state_old, state_new, queue, queue, k=1, sigma_b=2.0)
    assert delta > 0.0
    assert math.isclose(delta, 1.0 - math.exp(-4 / 2.0), rel_tol=1e-9)  # top-1={C1}: |0-4|=4


def test_blocking_impact_uses_the_union_of_old_and_new_top_k_not_new_alone():
    # Spec 44.3: items = union(first K of old_queue, first K of new_queue).
    # C5 sits in the OLD top-2 but drops out of the NEW top-2 entirely; if
    # only new_queue's top-k were used, C5's real physical change (buried
    # under 2 -> physically retrieved) would be silently missed even though
    # C1/C2 (the only new-top-k members) saw no change at all.
    old_queue = ["C5", "C1", "C2"]
    new_queue = ["C1", "C2", "C3"]
    state_old = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C5", "C1", "C2"], max_tier=5)],  # C5 bottom (2 above), C1 mid (1 above), C2 top (0)
        container_attributes={}, retrieval_queue=old_queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    state_new = YardState(
        instance_id="t", time_step=1, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1", "C2"], max_tier=5)],  # C5 physically retrieved; C1/C2's own blocker counts unchanged
        container_attributes={}, retrieval_queue=new_queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    delta_union = _blocking_impact(state_old, state_new, old_queue, new_queue, k=2, sigma_b=2.0)
    delta_new_only = _blocking_impact(state_old, state_new, new_queue, new_queue, k=2, sigma_b=2.0)
    assert delta_new_only == 0.0  # C1/C2 alone: no change at all
    assert delta_union > 0.0  # union also picks up C5's real 2->0 change


def test_normalized_weights_sum_to_one_and_zero_out_the_dead_blocking_term():
    # R1.1 (reviewer critique): i_blocking is structurally 0.0 in every
    # experiment this suite runs, so DEFAULT_WEIGHTS caps the achievable
    # total at 0.75, not the nominal 1.0. NORMALIZED_WEIGHTS must
    # redistribute that mass, not just drop it (A6_no_blocking_impact in
    # ablations.py zeroes w_b WITHOUT renormalizing -- a different,
    # deliberately non-renormalized ablation, not this fix).
    assert math.isclose(sum(NORMALIZED_WEIGHTS.values()), 1.0, rel_tol=1e-9)
    assert NORMALIZED_WEIGHTS["w_b"] == 0.0


def test_normalized_weights_rescale_total_by_exactly_one_over_point_seven_five():
    # Whenever i_blocking == 0 (the realistic case -- see
    # test_blocking_impact_is_zero_when_physical_state_is_unchanged),
    # normalizing is mathematically just dividing the default total by
    # (1 - w_b) = 0.75, since the four live terms keep their relative
    # proportions.
    old_queue = ["C1", "C2", "C3", "C4", "C5"]
    new_queue = ["C5", "C4", "C3", "C2", "C1"]
    state = make_state(old_queue)
    plan = Plan(plan_id="p", created_at=0, source="test", actions=[])
    default = compute_impact(old_queue, new_queue, state, state, plan, k=5, conf_new=0.5, weights=DEFAULT_WEIGHTS)
    normalized = compute_impact(old_queue, new_queue, state, state, plan, k=5, conf_new=0.5, weights=NORMALIZED_WEIGHTS)
    assert default.i_blocking == 0.0
    assert math.isclose(normalized.total, default.total / 0.75, rel_tol=1e-9)


def test_is_action_affected_removed_container():
    old_queue = ["C1", "C2", "C3"]
    new_queue = ["C2", "C3"]
    state = make_state(new_queue)
    action = Action(action_id="a1", step_index=0, type="RETRIEVE", container="C1",
                     source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1)
    assert is_action_affected(action, old_queue, new_queue, state, r_shift=5) is True
