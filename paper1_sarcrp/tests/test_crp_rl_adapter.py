import pytest
from sarcrp.schemas import Layout, Stack, YardState
from sarcrp.crp_rl_adapter import (
    CRP_RL_ROOT,
    build_priority_tensor,
    moves_to_plan,
    solve_crp_via_crp_rl,
)


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=4),
        stacks=[
            Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=4),  # C1 on top
            Stack(id="S2", containers=["C4", "C5"], max_tier=4),  # C5 (untracked) blocks C4
            Stack(id="S3", containers=[], max_tier=4),
        ],
        container_attributes={}, retrieval_queue=["C1", "C2", "C3", "C4"],
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_build_priority_tensor_shape_and_ranks():
    state = make_state()
    x = build_priority_tensor(state, retrieval_queue=["C1", "C2", "C3", "C4"])
    assert tuple(x.shape) == (1, 3, 1, 4)
    # S1 bottom-to-top: C3(rank3), C2(rank2), C1(rank1); tier0=bottom.
    assert x[0, 0, 0, 0].item() == 3.0
    assert x[0, 0, 0, 1].item() == 2.0
    assert x[0, 0, 0, 2].item() == 1.0
    assert x[0, 0, 0, 3].item() == 0.0  # empty slot above
    # S2: C4 (rank 4) at the bottom, C5 (not in the queue -> fallback rank 5) on top.
    assert x[0, 1, 0, 0].item() == 4.0
    assert x[0, 1, 0, 1].item() == 5.0
    # S3: fully empty.
    assert x[0, 2, 0, 0].item() == 0.0


def test_moves_to_plan_auto_retrieves_before_any_move_when_top_is_next():
    state = make_state()
    # C1 (rank 0 in the 0-indexed retrieval_queue) is already on top of S1 --
    # moves_to_plan's initial auto_retrieve() should emit it with no RELOCATE.
    plan = moves_to_plan(state, retrieval_queue=["C1", "C2", "C3", "C4"], moves=[])
    types = [a.type for a in plan.actions]
    containers = [a.container for a in plan.actions]
    assert types[0] == "RETRIEVE"
    assert containers[0] == "C1"


def test_moves_to_plan_replays_a_relocation_then_retrieves():
    state = make_state()
    # Initial auto_retrieve() cascades C1, C2, C3 out of S1, then stalls: S2's
    # top is C5, not the now-needed C4, so nothing else auto-retrieves. The
    # single move (S2 -> S3) relocates the blocker C5 out of the way, which
    # immediately makes C4 retrievable -- so the move itself is a RELOCATE of
    # C5, followed by an auto-emitted RETRIEVE of C4.
    plan = moves_to_plan(state, retrieval_queue=["C1", "C2", "C3", "C4"], moves=[(1, 2)])
    relocations = [a for a in plan.actions if a.type == "RELOCATE"]
    retrievals = [a.container for a in plan.actions if a.type == "RETRIEVE"]
    assert len(relocations) == 1
    assert relocations[0].container == "C5"
    assert relocations[0].source_stack == "S2"
    assert relocations[0].dest_stack == "S3"
    assert retrievals == ["C1", "C2", "C3", "C4"]


@pytest.mark.skipif(not CRP_RL_ROOT.is_dir(), reason="CRP_RL not cloned (see external/README.md)")
def test_solve_crp_via_crp_rl_returns_a_valid_plan():
    state = make_state()
    plan = solve_crp_via_crp_rl(state, retrieval_queue=["C1", "C2", "C3", "C4"])
    retrieved = [a.container for a in plan.actions if a.type == "RETRIEVE"]
    assert sorted(retrieved) == ["C1", "C2", "C3", "C4"]
    # Every container must be retrieved in non-decreasing rank order.
    rank = {"C1": 0, "C2": 1, "C3": 2, "C4": 3}
    assert [rank[c] for c in retrieved] == sorted(rank[c] for c in retrieved)


@pytest.mark.skipif(not CRP_RL_ROOT.is_dir(), reason="CRP_RL not cloned (see external/README.md)")
def test_get_cached_model_returns_the_same_object_on_repeated_calls():
    from sarcrp.crp_rl_adapter import get_cached_model
    model_a = get_cached_model("baselines/models/proposed/epoch(100).pt", "cpu")
    model_b = get_cached_model("baselines/models/proposed/epoch(100).pt", "cpu")
    assert model_a is model_b
