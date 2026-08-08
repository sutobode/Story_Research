from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.baselines import static_plan, full_reoptimization


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
