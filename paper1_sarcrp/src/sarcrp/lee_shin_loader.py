"""Loads CRP_RL's own Lee/Shin literature-benchmark instance files
(external/CRP_RL/benchmarks/{Lee,Shin}_instances) into this project's
YardState schema, so real published CRP benchmark data can be used
instead of (or alongside) this suite's own hand-built/generated
instances -- addressing the external-validity gap in the Q1 report's
Limitations. File format is CRP_RL's own (see
benchmarks/benchmarks.py's own find_and_process_file/parse_container_file):
a header line (ignored here), then one line per (bay, row) stack:
`bay row num_tiers c1 c1 c2 c2 ... cN cN` -- each container's retrieval
rank is written twice per CRP_RL's own convention; containers are listed
bottom-to-top.

This schema has no bay/row distinction (a flat list of stacks) -- same
simplification crp_rl_adapter.py already makes for the model's own
tensor format. Each (bay, row) pair becomes one flat stack, named
"S{bay}_{row}", which preserves every blocking relationship in the
original instance exactly; only the 2D geometric bay/row labeling is
dropped, and nothing in this project's solver/objective uses it anyway.
"""
from pathlib import Path

from sarcrp.schemas import Layout, Stack, YardState

LEE_SHIN_ROOT = Path(__file__).resolve().parents[2] / "external" / "CRP_RL" / "benchmarks"


def parse_lee_shin_file(file_path: Path, n_bays: int, n_rows: int, n_tiers: int) -> YardState:
    lines = Path(file_path).read_text().splitlines()
    stacks_by_id: dict[str, Stack] = {}
    rank_to_container: dict[int, str] = {}

    for line in lines[1:]:  # skip the header line
        if not line.strip():
            continue
        values = list(map(int, line.split()))
        bay, row, _num_tiers = values[:3]
        raw_ranks = values[3:]

        seen: list[int] = []
        for rank in raw_ranks:
            if rank not in seen:  # each rank is written twice in this file format
                seen.append(rank)

        containers = []
        for rank in seen:
            name = f"C{rank:03d}"
            rank_to_container[rank] = name
            containers.append(name)

        stack_id = f"S{bay}_{row}"
        stacks_by_id[stack_id] = Stack(id=stack_id, containers=containers, max_tier=n_tiers)

    for bay in range(1, n_bays + 1):
        for row in range(1, n_rows + 1):
            stack_id = f"S{bay}_{row}"
            stacks_by_id.setdefault(stack_id, Stack(id=stack_id, containers=[], max_tier=n_tiers))

    stacks = [stacks_by_id[f"S{bay}_{row}"] for bay in range(1, n_bays + 1) for row in range(1, n_rows + 1)]
    retrieval_queue = [rank_to_container[r] for r in sorted(rank_to_container)]

    return YardState(
        instance_id=Path(file_path).stem, time_step=0, layout=Layout(num_stacks=n_bays * n_rows, max_tier=n_tiers),
        stacks=stacks, container_attributes={}, retrieval_queue=retrieval_queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def find_lee_shin_file(inst_type: str, n_bays: int, n_rows: int, n_tiers: int, idx: int, family: str = "Lee") -> Path:
    """Mirrors CRP_RL's own benchmarks.find_and_process_file naming
    convention (bays_str+stacks_str+tiers_str prefix, _{idx:03d}.txt
    suffix), reading directly off disk without importing CRP_RL's own
    (torch-dependent) module."""
    if inst_type == "random":
        subdir, prefix = "Individual, random", "R"
    elif inst_type == "upsidedown":
        subdir, prefix = "Individual, upside down", "U"
    else:
        raise ValueError(f"unknown inst_type: {inst_type!r}")

    folder = LEE_SHIN_ROOT / f"{family}_instances" / subdir
    bays_str, stacks_str, tiers_str, id_str = f"{prefix}{n_bays:02d}", f"{n_rows:02d}", f"{n_tiers:02d}", f"{idx:03d}"
    matches = [
        p for p in folder.iterdir()
        if p.name.startswith(f"{bays_str}{stacks_str}{tiers_str}") and p.name.endswith(f"_{id_str}.txt")
    ]
    if len(matches) != 1:
        raise FileNotFoundError(
            f"expected exactly 1 file for bays={n_bays} rows={n_rows} tiers={n_tiers} idx={idx} in {folder}, got {matches}"
        )
    return matches[0]


def load_lee_instance(inst_type: str, n_bays: int, n_rows: int, n_tiers: int, idx: int, family: str = "Lee") -> YardState:
    file_path = find_lee_shin_file(inst_type, n_bays, n_rows, n_tiers, idx, family=family)
    return parse_lee_shin_file(file_path, n_bays, n_rows, n_tiers)
