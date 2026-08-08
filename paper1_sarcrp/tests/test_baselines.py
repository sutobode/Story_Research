import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.sarcrp_core import ReplanDecision
from sarcrp.baselines import static_plan, full_reoptimization, periodic_replan, event_triggered_no_stability, mpc_receding_horizon


def make_state(queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_static_plan_returns_same_object_unmodified():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    result = static_plan(plan)
    assert result is plan


def test_full_reoptimization_calls_solver_on_current_state():
    state = make_state(["C1", "C2"])
    plan = full_reoptimization(state, retrieval_queue_new=["C1", "C2"], time_limit_sec=1.0)
    assert plan.actions
    assert plan.actions[0].type == "RETRIEVE"
    assert plan.actions[0].container == "C1"


def test_periodic_replan_only_reoptimizes_on_period_boundary():
    state = make_state(["C1", "C2"])
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    off_period = periodic_replan(state, ["C1", "C2"], plan, event_index=1, period=5)
    assert off_period is plan  # not a period boundary -> static passthrough
    on_period = periodic_replan(state, ["C1", "C2"], plan, event_index=5, period=5)
    assert on_period is not plan  # period boundary -> re-solved
    assert on_period.actions[0].type == "RETRIEVE"


def test_event_triggered_no_stability_zeroes_lambda_and_mu():
    state = make_state(["C1", "C2"])
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    decision = event_triggered_no_stability(
        state, plan, old_queue=["C1", "C2"], new_queue=["C2", "C1"],
        urgent_containers=["C2"], rng=random.Random(0), theta_impact=0.0, tau_frac=0.0,
    )
    assert isinstance(decision, ReplanDecision)


def test_mpc_receding_horizon_freezes_prefix_and_resolves_tail():
    state = make_state(["C1", "C2"])
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    result = mpc_receding_horizon(state, plan, retrieval_queue_new=["C2", "C1"], horizon=1)
    assert result.actions[0].container == plan.actions[0].container  # frozen prefix (1 action) untouched


def test_mpc_receding_horizon_does_not_double_plan_the_frozen_prefixs_containers():
    # Regression test for a real bug: the tail used to be solved against the
    # ORIGINAL state as if the frozen prefix's own actions never happened,
    # so the tail's fresh solve would re-plan moves for containers the
    # frozen prefix already retrieved/relocated -- is_plan_valid on the
    # concatenated result then correctly rejects it (e.g. a RETRIEVE for a
    # container no longer on top because the frozen prefix already popped
    # it). Use a 3-container stack so horizon=2 forces the frozen prefix to
    # actually retrieve something the tail must not touch again.
    from sarcrp.plan_validator import is_plan_valid
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1", "C2", "C3"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    plan = full_reoptimization(state, retrieval_queue_new=["C1", "C2", "C3"], time_limit_sec=1.0)
    result = mpc_receding_horizon(state, plan, retrieval_queue_new=["C1", "C2", "C3"], horizon=2)
    assert is_plan_valid(result, state)
    retrieved = [a.container for a in result.actions if a.type == "RETRIEVE"]
    assert sorted(retrieved) == ["C1", "C2", "C3"]  # every container retrieved exactly once


def test_full_reoptimization_accepts_a_custom_solver():
    state = make_state(["C1", "C2"])
    calls = {"count": 0}

    def spy_solver(state_arg, queue_arg, constraints=None, time_limit_sec=None):
        calls["count"] += 1
        from sarcrp.crp_solver import solve_crp
        return solve_crp(state_arg, queue_arg, constraints=constraints, time_limit_sec=time_limit_sec)

    full_reoptimization(state, retrieval_queue_new=["C1", "C2"], time_limit_sec=1.0, solver=spy_solver)
    assert calls["count"] == 1
