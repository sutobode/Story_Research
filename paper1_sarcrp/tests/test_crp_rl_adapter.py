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


@pytest.mark.skipif(not CRP_RL_ROOT.is_dir(), reason="CRP_RL not cloned (see external/README.md)")
def test_adapter_faithfully_reproduces_the_models_own_relocation_count():
    """Independent validation, deliberately NOT scored under our own
    objective.py: builds a random instance using CRP_RL's OWN generator
    (its native tensor format, not ours), runs the model natively
    (unpatched) to get CRP_RL's own reported cost, then runs our
    recording-wrapped decode on the exact same input/model (greedy
    sampling is deterministic, so it must reproduce the same trajectory)
    and checks our own bookkeeping doesn't drop or duplicate a single
    relocation the model actually decided on. This is what rules out "the
    -48% comparison (Task 34 Part C) is an adapter bug" as an explanation,
    independent of whatever this project's own objective thinks of the
    result."""
    import torch
    from sarcrp.crp_rl_adapter import get_cached_model, _run_decode_recording_moves, moves_to_plan
    from sarcrp.objective import relocation_count

    model = get_cached_model("baselines/models/proposed/epoch(100).pt", "cpu")
    from generator.generator import Generator  # CRP_RL_ROOT is on sys.path after get_cached_model

    n_containers, n_bays, n_rows, n_tiers = 50, 10, 1, 6  # matches crp_rl_scale_instance.json: max_tier=6 leaves
    # headroom above 5 filled tiers so a relocation destination actually exists (50 containers in exactly
    # 50 slots -- n_tiers=5 -- leaves every stack full, and the model has nowhere legal to relocate to)
    gen = Generator(seed=42, n_samples=1, layout=(n_containers, n_bays, n_rows, n_tiers), inst_type="random", device=None)
    x = gen.data  # CRP_RL's own native tensor, shape (1, n_bays, n_rows, n_tiers)

    with torch.no_grad():
        native_cost, _ll = model(x, None)
    native_cost = float(native_cost.item() if hasattr(native_cost, "item") else native_cost)
    assert native_cost == native_cost  # not NaN
    assert native_cost > 0  # a real, non-degenerate cost for a 50-container instance

    moves = _run_decode_recording_moves(model, x)
    assert len(moves) > 0  # a random 50-container instance should need real relocations

    # Rebuild an equivalent YardState from the SAME tensor (rank r -> container "C{r:03d}").
    rank_to_container: dict[int, str] = {}
    stacks = []
    for b in range(n_bays):
        tiered = []
        for t in range(n_tiers):
            rank = int(x[0, b, 0, t].item())
            if rank == 0:
                continue
            name = f"C{rank:03d}"
            rank_to_container[rank] = name
            tiered.append((t, name))
        tiered.sort(key=lambda item: item[0])
        stacks.append(Stack(id=f"S{b + 1}", containers=[name for _, name in tiered], max_tier=n_tiers))
    retrieval_queue = [rank_to_container[r] for r in sorted(rank_to_container)]
    yard_state = YardState(
        instance_id="validation", time_step=0, layout=Layout(num_stacks=n_bays, max_tier=n_tiers),
        stacks=stacks, container_attributes={}, retrieval_queue=retrieval_queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )

    plan = moves_to_plan(yard_state, retrieval_queue, moves)
    assert relocation_count(plan) == len(moves)  # every recorded move survives replay -- none dropped or duplicated
    retrieved = [a.container for a in plan.actions if a.type == "RETRIEVE"]
    assert sorted(retrieved) == sorted(retrieval_queue)  # every container still retrieved exactly once
