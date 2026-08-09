"""R3.1 (reviewer critique on the Q1 report): CRP_RL's real trained model
loses to the greedy heuristic under SAR-CRP's own objective (relocation-
count + delay based, Task 33/34), even in-distribution. Does that mean
CRP_RL's relocation choices are genuinely worse, or does it just mean
CRP_RL was trained to minimize a DIFFERENT (travel-time based) cost and
SAR-CRP's objective doesn't reward that?

This settles it directly: replays BOTH greedy's own move sequence and
CRP_RL's own decoded move sequence through CRP_RL's OWN native cost
engine (env.env.Env's _relocation_cost/_retrieve_cost -- the travel-time
metric the model was actually trained to minimize), on the identical
instance/tensor. If CRP_RL's own sequence wins under its own metric while
losing under ours, that is a clean objective-mismatch story. If it loses
under both, that is a real quality gap, not a mismatch.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.crp_rl_adapter import (  # noqa: E402
    _ensure_crp_rl_on_path, _run_decode_recording_moves, build_priority_tensor, get_cached_model,
)
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402
from sarcrp.schemas import Layout, Stack, YardState  # noqa: E402


def plan_to_moves(plan, stack_id_to_bay: dict) -> list[tuple[int, int]]:
    """Extracts (source_bay_idx, dest_bay_idx) for each RELOCATE action, in
    step order. RETRIEVE actions are not needed: CRP_RL's own Env.step()
    auto-triggers the equivalent retrieval cost via clear() after every
    relocation, exactly mirroring how a greedy plan interleaves explicit
    RETRIEVE actions whenever the next-ranked container reaches the top of
    its stack."""
    return [
        (stack_id_to_bay[a.source_stack], stack_id_to_bay[a.dest_stack])
        for a in sorted(plan.actions, key=lambda a: a.step_index)
        if a.type == "RELOCATE"
    ]


def parse_lee_shin_tensor(file_path, n_bays: int, n_rows: int, n_tiers: int):
    """Re-implements CRP_RL's own benchmarks.parse_container_file logic
    (same file format, same output tensor shape) directly, rather than
    importing benchmarks/benchmarks.py -- that module imports pandas at
    module scope for functionality this comparison doesn't use, and this
    project's standing policy is not to add dependencies (even on the
    server) without a real need."""
    import numpy as np
    import torch

    lines = Path(file_path).read_text().splitlines()
    container_matrix = np.zeros((n_bays * n_rows, n_tiers), dtype=int)
    for line in lines[1:]:
        if not line.strip():
            continue
        values = list(map(int, line.split()))
        bay, row, num_tiers = values[:3]
        raw_ranks = values[3:]
        seen: list[int] = []
        for rank in raw_ranks:
            if rank not in seen:
                seen.append(rank)
        padded = seen + [0] * (n_tiers - len(seen))
        stack_index = (bay - 1) * n_rows + (row - 1)
        container_matrix[stack_index] = padded

    tensor = torch.tensor(container_matrix).unsqueeze(0).float()
    return tensor.reshape(1, n_bays, n_rows, n_tiers)


def replay_native_cost(x, moves: list[tuple[int, int]], device: str = "cpu") -> float:
    """Drives CRP_RL's own Env directly (no model involved) through a
    PRESCRIBED move sequence, summing its native relocation+retrieval cost
    -- the exact metric CRP_RL's own training loop optimizes."""
    import torch
    from env.env import Env

    env = Env(torch.device(device), x.clone())
    env.find_target_stack()
    total_cost = env.clear()  # initial auto-retrieve, before any relocation
    for source_idx, dest_idx in moves:
        src = torch.tensor([[source_idx]], device=device)
        dst = torch.tensor([[dest_idx]], device=device)
        total_cost = total_cost + env.step(dest_index=dst, source_index=src)
    return float(total_cost.sum().item())


def run_comparison(instance_path: str, model_path: str = "baselines/models/proposed/epoch(100).pt", device: str = "cpu") -> dict:
    import torch

    _ensure_crp_rl_on_path()
    instance = json.loads(Path(instance_path).read_text())
    stacks = [Stack(id=s["id"], containers=list(s["containers"]), max_tier=s["max_tier"]) for s in instance["stacks"]]
    queue = list(instance["initial_retrieval_order"])
    state = YardState(
        instance_id=instance["instance_id"], time_step=0, layout=Layout(**instance["layout"]), stacks=stacks,
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    stack_id_to_bay = {s.id: i for i, s in enumerate(stacks)}

    greedy_plan = solve_crp(state, queue, time_limit_sec=30.0)
    greedy_moves = plan_to_moves(greedy_plan, stack_id_to_bay)

    x = build_priority_tensor(state, queue).to(torch.device(device))
    model = get_cached_model(model_path, device)
    crp_rl_moves = _run_decode_recording_moves(model, x)

    greedy_native_cost = replay_native_cost(x, greedy_moves, device)
    crp_rl_native_cost = replay_native_cost(x, crp_rl_moves, device)

    return {
        "instance": instance["instance_id"],
        "greedy_relocations": len(greedy_moves),
        "crp_rl_relocations": len(crp_rl_moves),
        "greedy_native_cost": greedy_native_cost,
        "crp_rl_native_cost": crp_rl_native_cost,
        "crp_rl_wins_under_its_own_metric": crp_rl_native_cost < greedy_native_cost,
    }


def run_comparison_multirow(inst_type: str, n_bays: int, n_rows: int, n_tiers: int, idx: int,
                             model_path: str = "baselines/models/proposed/epoch(100).pt", device: str = "cpu") -> dict:
    """Same comparison, but on a REAL Lee instance's genuine (n_bays,
    n_rows, n_tiers) geometry -- not this project's own flat-stack
    (n_rows=1 always) simplification. Rules out "the flat-stack schema is
    a degenerate case CRP_RL was never trained for" as an alternative
    explanation for run_comparison's finding: CRP_RL's own training
    distribution normally has multiple rows per bay (cheap same-bay,
    different-row relocations available), which the n_rows=1 case never
    offers at all."""
    import torch
    from sarcrp.lee_shin_loader import find_lee_shin_file

    _ensure_crp_rl_on_path()

    file_path = find_lee_shin_file(inst_type, n_bays, n_rows, n_tiers, idx)
    x = parse_lee_shin_tensor(file_path, n_bays, n_rows, n_tiers)

    # Flatten the SAME file into this project's own YardState (bay-major,
    # row-minor -- lee_shin_loader.py's own ordering already matches
    # Env's flat-index convention: flat_index = (bay-1)*n_rows + (row-1))
    # so this project's own greedy solver can plan on it directly.
    from sarcrp.lee_shin_loader import parse_lee_shin_file
    state = parse_lee_shin_file(file_path, n_bays, n_rows, n_tiers)
    stack_id_to_bay = {s.id: i for i, s in enumerate(state.stacks)}

    greedy_plan = solve_crp(state, state.retrieval_queue, time_limit_sec=30.0)
    greedy_moves = plan_to_moves(greedy_plan, stack_id_to_bay)

    model = get_cached_model(model_path, device)
    crp_rl_moves = _run_decode_recording_moves(model, x.to(torch.device(device)))

    greedy_native_cost = replay_native_cost(x, greedy_moves, device)
    crp_rl_native_cost = replay_native_cost(x, crp_rl_moves, device)

    return {
        "instance": file_path.name,
        "n_bays": n_bays, "n_rows": n_rows, "n_tiers": n_tiers,
        "greedy_relocations": len(greedy_moves),
        "crp_rl_relocations": len(crp_rl_moves),
        "greedy_native_cost": greedy_native_cost,
        "crp_rl_native_cost": crp_rl_native_cost,
        "crp_rl_wins_under_its_own_metric": crp_rl_native_cost < greedy_native_cost,
    }


def main():
    import time
    _start = time.monotonic()
    result_flat = run_comparison("experiments/instances/crp_rl_scale_instance.json")
    print("flat-stack (n_rows=1, this project's own schema):", result_flat)
    result_multirow = run_comparison_multirow(inst_type="random", n_bays=2, n_rows=3, n_tiers=6, idx=1)
    print("genuine multi-row (Lee R020306, CRP_RL's own training geometry):", result_multirow)
    log_run("run_crp_rl_native_cost_comparison.py",
            {"instance_flat": result_flat["instance"], "instance_multirow": result_multirow["instance"]},
            time.monotonic() - _start, [])


if __name__ == "__main__":
    main()
