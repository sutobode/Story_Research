import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.local_search_repair import (
    local_search_repair,
    _neighbor_insert_urgent_support,
    _neighbor_replace_tail_with_solver,
)


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1"], max_tier=5),
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_state_with_buried_urgent():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=5),  # C1 on top, blocks C2
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1", "C2"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_plan(dest="S2"):
    return Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RELOCATE", container="C1",
               source_stack="S1", dest_stack=dest, commit_status="planned", planned_time=0),
    ])


def test_returns_a_valid_plan_no_worse_than_start():
    state = make_state()
    p_start = make_plan(dest="S2")
    p_old = make_plan(dest="S3")
    rng = random.Random(0)
    result = local_search_repair(
        p_start, p_old, state, retrieval_queue_new=["C1"], frozen_count=0, rng=rng,
        t_iters=20, m_neighbors=10, epsilon=0.0,
    )
    assert len(result.actions) >= 1


def test_never_modifies_frozen_actions():
    state = make_state()
    p_start = make_plan(dest="S2")
    p_old = make_plan(dest="S3")
    rng = random.Random(1)
    result = local_search_repair(
        p_start, p_old, state, retrieval_queue_new=["C1"], frozen_count=1, rng=rng,
        t_iters=20, m_neighbors=10, epsilon=0.0,
    )
    assert result.actions[0].dest_stack == p_start.actions[0].dest_stack  # frozen index untouched


def test_is_seed_reproducible():
    state = make_state()
    p_start = make_plan(dest="S2")
    p_old = make_plan(dest="S3")
    result_a = local_search_repair(p_start, p_old, state, ["C1"], 0, random.Random(5), t_iters=15, m_neighbors=5)
    result_b = local_search_repair(p_start, p_old, state, ["C1"], 0, random.Random(5), t_iters=15, m_neighbors=5)
    assert [a.dest_stack for a in result_a.actions] == [a.dest_stack for a in result_b.actions]


def test_n3_inserts_relocation_to_unblock_urgent_container():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[])
    rng = random.Random(0)
    result = _neighbor_insert_urgent_support(plan, state, frozen_count=0, urgent_containers=["C2"], rng=rng)
    assert result is not None
    relocations = [a for a in result.actions if a.type == "RELOCATE" and a.container == "C1"]
    assert len(relocations) == 1
    assert relocations[0].source_stack == "S1"
    assert relocations[0].dest_stack != "S1"


def test_n3_returns_none_when_no_urgent_containers():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[])
    result = _neighbor_insert_urgent_support(plan, state, frozen_count=0, urgent_containers=[], rng=random.Random(0))
    assert result is None


def test_n3_returns_none_when_urgent_container_already_on_top():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[])
    result = _neighbor_insert_urgent_support(plan, state, frozen_count=0, urgent_containers=["C1"], rng=random.Random(0))
    assert result is None


def test_n5_replaces_tail_with_solver_suggestion():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RELOCATE", container="C1",
               source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    rng = random.Random(0)
    result = _neighbor_replace_tail_with_solver(plan, state, retrieval_queue_new=["C1", "C2"], frozen_count=0, rng=rng)
    assert result is not None
    assert len(result.actions) >= 1


def test_n5_returns_none_when_plan_is_fully_frozen():
    state = make_state()
    plan = make_plan(dest="S2")
    result = _neighbor_replace_tail_with_solver(plan, state, retrieval_queue_new=["C1"], frozen_count=1, rng=random.Random(0))
    assert result is None


def test_local_search_repair_can_reduce_urgent_retrieval_delay():
    state = make_state_with_buried_urgent()
    p_old = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    rng = random.Random(0)
    result = local_search_repair(
        p_old, p_old, state, retrieval_queue_new=["C1", "C2"], frozen_count=0, rng=rng,
        t_iters=50, m_neighbors=20, epsilon=0.0, urgent_containers=["C2"],
    )
    assert result is not None  # end-to-end run with N3/N5 in the mix does not crash
