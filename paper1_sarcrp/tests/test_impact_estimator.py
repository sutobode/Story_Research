import math
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.impact_estimator import compute_impact, is_action_affected


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


def test_is_action_affected_removed_container():
    old_queue = ["C1", "C2", "C3"]
    new_queue = ["C2", "C3"]
    state = make_state(new_queue)
    action = Action(action_id="a1", step_index=0, type="RETRIEVE", container="C1",
                     source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1)
    assert is_action_affected(action, old_queue, new_queue, state, r_shift=5) is True
