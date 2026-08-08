import csv
import json
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.simulator import run_episode  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402

METHODS = ("static", "full_reopt", "sarcrp")
SEEDS = tuple(range(10))  # MVP smoke test: 10 seeds. Full study uses >=20 (spec 23.6).
UNCERTAINTY_LEVELS = ("low", "medium", "high")


def run_all_methods(instance: dict, methods=METHODS, seeds=SEEDS, uncertainty_levels=UNCERTAINTY_LEVELS) -> list[dict]:
    rows = []
    for level in uncertainty_levels:
        level_instance = dict(instance, uncertainty_level=level)
        for method in methods:
            for seed in seeds:
                metrics = run_episode(level_instance, method_name=method, rng=random.Random(seed))
                rows.append({
                    "method": method,
                    "uncertainty_level": level,
                    "seed": seed,
                    "relocation_count_total": metrics.relocation_count_total,
                    "changed_actions_total": metrics.changed_actions_total,
                    "total_cost_mean": metrics.total_cost_mean,
                    "operational_cost_mean": metrics.operational_cost_mean,
                    "runtime_mean_sec": metrics.runtime_mean_sec,
                    "fallback_rate": metrics.fallback_rate,
                })
    return rows


def evaluate_decision_gate(rows: list[dict]) -> dict:
    """Spec 33 decision gate, computed once per uncertainty level present in
    `rows`. The 3rd condition compares operational cost alone (spec 11), not
    blended total cost, and is an upper-bound-only check: SAR-CRP sitting
    *below* Full Reoptimization's operational cost is never a failure -- only
    sitting meaningfully *above* it is. The original ±20% band on total cost
    treated "far below" the same as "far above," which flagged a genuinely
    good result as a failure (see the MVP report's Decision Gate discussion)."""
    levels = sorted({r["uncertainty_level"] for r in rows})
    result = {}
    for level in levels:
        level_rows = [r for r in rows if r["uncertainty_level"] == level]
        by_method = {}
        for method in ("static", "full_reopt", "sarcrp"):
            total = [r["total_cost_mean"] for r in level_rows if r["method"] == method]
            op = [r["operational_cost_mean"] for r in level_rows if r["method"] == method]
            changed = [r["changed_actions_total"] for r in level_rows if r["method"] == method]
            by_method[method] = {
                "total_cost_mean": statistics.mean(total) if total else float("nan"),
                "operational_cost_mean": statistics.mean(op) if op else float("nan"),
                "changed_actions_mean": statistics.mean(changed) if changed else float("nan"),
            }

        sarcrp, static, full_reopt = by_method["sarcrp"], by_method["static"], by_method["full_reopt"]
        result[level] = {
            "sarcrp_beats_static_total_cost": sarcrp["total_cost_mean"] < static["total_cost_mean"],
            "sarcrp_beats_full_reopt_stability": sarcrp["changed_actions_mean"] < full_reopt["changed_actions_mean"],
            "sarcrp_operational_cost_not_worse_than_full_reopt": sarcrp["operational_cost_mean"] <= full_reopt["operational_cost_mean"] * 1.20,
        }
    return result


def main():
    _start = time.monotonic()
    instance_path = Path(__file__).parent / "instances" / "small_layout_mvp.json"
    instance = json.loads(instance_path.read_text())

    rows = run_all_methods(instance)

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "mvp_results.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    verdict_by_level = evaluate_decision_gate(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")
    for level, verdict in verdict_by_level.items():
        print(f"Decision gate (spec 33) -- uncertainty_level={level}:")
        for key, passed in verdict.items():
            print(f"  {key}: {'PASS' if passed else 'FAIL'}")

    log_run("run_mvp.py", {"seeds": list(SEEDS), "methods": list(METHODS)}, time.monotonic() - _start, [str(out_path)])


if __name__ == "__main__":
    main()
