from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.plan_validator import is_plan_valid


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=2),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=2), Stack(id="S2", containers=[], max_tier=2)],
        container_attributes={}, retrieval_queue=["C1", "C2"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_valid_plan_is_accepted():
    state = make_state()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    assert is_plan_valid(plan, state) is True


def test_retrieve_wrong_container_is_rejected():
    state = make_state()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C2",  # C1 is on top, not C2
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    assert is_plan_valid(plan, state) is False


def test_relocate_into_a_full_stack_is_rejected():
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=2),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=2),
                Stack(id="S2", containers=[], max_tier=2),
                Stack(id="S3", containers=["C3"], max_tier=2)],
        container_attributes={}, retrieval_queue=["C1", "C2", "C3"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RELOCATE", container="C1",
               source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RELOCATE", container="C2",
               source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=1),
        # S2 is now full (max_tier=2, holds C1+C2); relocating C3 into it must be rejected.
        Action(action_id="a2", step_index=2, type="RELOCATE", container="C3",
               source_stack="S3", dest_stack="S2", commit_status="planned", planned_time=2),
    ])
    assert is_plan_valid(plan, state) is False
