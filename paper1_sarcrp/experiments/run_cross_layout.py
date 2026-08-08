import csv
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.simulator import run_episode  # noqa: E402

METHODS = ("static", "full_reopt", "sarcrp")
SEEDS = tuple(range(20))  # spec 23.6: >=20 seeds for a reported experiment
LAYOUT_FILES = {
    "layout_a": "small_layout_mvp.json",
    "layout_b": "layout_b.json",
    "layout_c": "layout_c.json",
}
TIMEOUT_BY_LAYOUT = {"layout_a": 1.0, "layout_b": 5.0, "layout_c": 30.0}  # spec 17: small/medium/large


def run_all_layouts(methods=METHODS, seeds=SEEDS) -> list[dict]:
    """Cross-layout protocol (spec 50): every layout runs with the SAME
    hyperparameters (this codebase's spec-48 defaults) -- no per-layout
    tuning happens anywhere in this function. Only the solver timeout
    varies, per spec 17's own size-based tiering (TIMEOUT_BY_LAYOUT)."""
    instances_dir = Path(__file__).parent / "instances"
    rows = []
    for layout_name, filename in LAYOUT_FILES.items():
        instance = json.loads((instances_dir / filename).read_text())
        for method in methods:
            for seed in seeds:
                metrics = run_episode(instance, method_name=method, rng=random.Random(seed), time_limit_sec=TIMEOUT_BY_LAYOUT[layout_name])
                rows.append({
                    "layout": layout_name, "method": method, "seed": seed,
                    "total_cost_mean": metrics.total_cost_mean,
                    "operational_cost_mean": metrics.operational_cost_mean,
                    "changed_actions_total": metrics.changed_actions_total,
                    "runtime_mean_sec": metrics.runtime_mean_sec,
                })
    return rows


def summarize_performance_drop(rows: list[dict], method: str) -> dict:
    """Relative total-cost change of Layout B/C vs Layout A (spec 50's
    'performance drop' metric, spec 24.5)."""
    by_layout = {}
    for layout in ("layout_a", "layout_b", "layout_c"):
        values = [r["total_cost_mean"] for r in rows if r["layout"] == layout and r["method"] == method]
        by_layout[layout] = statistics.mean(values) if values else float("nan")
    baseline = by_layout["layout_a"]
    return {
        "layout_b": (by_layout["layout_b"] - baseline) / baseline,
        "layout_c": (by_layout["layout_c"] - baseline) / baseline,
    }


def main():
    rows = run_all_layouts()
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "cross_layout_results.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")
    for method in METHODS:
        drop = summarize_performance_drop(rows, method)
        print(f"{method}: performance drop vs layout_a -> B: {drop['layout_b']:+.1%}, C: {drop['layout_c']:+.1%}")


if __name__ == "__main__":
    main()
