"""External validity: runs this suite's own established Static/Full
Reoptimization/SAR-CRP comparison (spec 22, 23) on real literature CRP
benchmark instances (Lee et al., via CRP_RL's own bundled data files)
instead of this project's hand-built/generated instances -- addressing
the Limitations gap flagged in the Q1 report. Lee/Shin instances are
static CRP layouts (no dynamic events of their own); this project's own
event generator/uncertainty layer is applied on top, exactly as it is
for every other instance in this suite.
"""
import csv
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.lee_shin_loader import load_lee_instance  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS  # noqa: E402
from sarcrp.simulator import run_episode  # noqa: E402

METHODS = ("static", "full_reopt", "sarcrp")

# Real Lee et al. random-layout instances bundled with CRP_RL (external/CRP_RL/benchmarks/Lee_instances).
# Timeouts follow spec 17's own size-based tiering (small/medium/large).
INSTANCES = (
    {"label": "Lee_R020306_020c", "inst_type": "random", "n_bays": 2, "n_rows": 3, "n_tiers": 6, "idx": 1, "timeout": 5.0},
    {"label": "Lee_R011606_070c", "inst_type": "random", "n_bays": 1, "n_rows": 16, "n_tiers": 6, "idx": 1, "timeout": 30.0},
)


def _to_instance_dict(state) -> dict:
    return {
        "instance_id": state.instance_id,
        "layout": {"num_stacks": state.layout.num_stacks, "max_tier": state.layout.max_tier},
        "stacks": [{"id": s.id, "containers": list(s.containers), "max_tier": s.max_tier} for s in state.stacks],
        "initial_retrieval_order": list(state.retrieval_queue),
        "t_steps": 40,
        "uncertainty_level": "medium",
    }


def run_all(methods=METHODS, seeds=REPORT_SEEDS) -> list[dict]:
    rows = []
    for spec in INSTANCES:
        state = load_lee_instance(spec["inst_type"], spec["n_bays"], spec["n_rows"], spec["n_tiers"], spec["idx"])
        instance = _to_instance_dict(state)
        for method in methods:
            for seed in seeds:
                metrics = run_episode(instance, method_name=method, rng=random.Random(seed), time_limit_sec=spec["timeout"])
                rows.append({
                    "instance": spec["label"], "n_containers": len(instance["initial_retrieval_order"]),
                    "method": method, "seed": seed,
                    "total_cost_mean": metrics.total_cost_mean,
                    "operational_cost_mean": metrics.operational_cost_mean,
                    "changed_actions_total": metrics.changed_actions_total,
                    "fallback_rate": metrics.fallback_rate,
                })
    return rows


def main():
    _start = time.monotonic()
    rows = run_all()
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "lee_shin_benchmark_results.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")
    for spec in INSTANCES:
        for method in METHODS:
            vals = [r["total_cost_mean"] for r in rows if r["instance"] == spec["label"] and r["method"] == method]
            print(f"{spec['label']} {method}: total_cost_mean mean={sum(vals) / len(vals):.3f}")

    log_run("run_lee_shin_benchmark.py", {"seeds": list(REPORT_SEEDS), "instances": [s["label"] for s in INSTANCES]},
            time.monotonic() - _start, [str(out_path)])


if __name__ == "__main__":
    main()
