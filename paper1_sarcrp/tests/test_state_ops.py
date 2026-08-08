from sarcrp.schemas import Layout, Stack, YardState
from sarcrp.state_ops import find_stack, blocker_count, blocker_pressure


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C10", "C07", "C03"], max_tier=5)],
        container_attributes={}, retrieval_queue=["C03", "C07", "C10"],
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_find_stack():
    state = make_state()
    assert find_stack(state, "C07") == "S1"
    assert find_stack(state, "C99") is None


def test_blocker_count_matches_spec_example():
    state = make_state()
    assert blocker_count(state, "C10") == 2
    assert blocker_count(state, "C07") == 1
    assert blocker_count(state, "C03") == 0
    assert blocker_count(state, "C99") == 0  # not in yard -> no blockers


def test_blocker_pressure_topk():
    state = make_state()
    assert blocker_pressure(state, state.retrieval_queue, k=2) == blocker_count(state, "C03") + blocker_count(state, "C07")
