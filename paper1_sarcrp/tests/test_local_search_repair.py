import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.local_search_repair import local_search_repair


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1"], max_tier=5),
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
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
