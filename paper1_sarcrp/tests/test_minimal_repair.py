from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.minimal_repair import minimal_feasibility_repair


def make_state(queue):
    return YardState(
        instance_id="t", time_step=1, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=1, state_confidence=1.0,
    )


def test_removes_action_for_container_no_longer_in_queue():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    state = make_state(queue=["C2"])  # C1 no longer in queue -> obsolete
    repaired = minimal_feasibility_repair(old_plan, state, retrieval_queue_new=["C2"])
    containers = [a.container for a in repaired.actions]
    assert "C1" not in containers
    assert "C2" in containers


def test_keeps_valid_actions_untouched():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    state = make_state(queue=["C2"])
    repaired = minimal_feasibility_repair(old_plan, state, retrieval_queue_new=["C2"])
    assert len(repaired.actions) == 1
    assert repaired.actions[0].container == "C2"
