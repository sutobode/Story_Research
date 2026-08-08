import csv
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.simulator import run_episode  # noqa: E402

METHODS = ("static", "full_reopt", "sarcrp")
SEEDS = tuple(range(10))  # MVP smoke test: 10 seeds. Full study uses >=20 (spec 23.6).


def run_all_methods(instance: dict, methods=METHODS, seeds=SEEDS) -> list[dict]:
    rows = []
    for method in methods:
        for seed in seeds:
            metrics = run_episode(instance, method_name=method, rng=random.Random(seed))
            rows.append({
                "method": method,
                "seed": seed,
                "relocation_count_total": metrics.relocation_count_total,
                "changed_actions_total": metrics.changed_actions_total,
                "total_cost_mean": metrics.total_cost_mean,
                "runtime_mean_sec": metrics.runtime_mean_sec,
                "fallback_rate": metrics.fallback_rate,
            })
    return rows


def evaluate_decision_gate(rows: list[dict]) -> dict:
    """Spec 33 decision gate: SAR-CRP total cost < Static; SAR-CRP stability
    (proxied here by changed_actions_total) < Full Reoptimization; SAR-CRP
    operational cost close to Full Reoptimization (checked via total_cost_mean
    within 20% as a simple MVP proxy -- refine with the real operational-cost
    split once Task 6's components are logged separately per-method)."""
    by_method = {}
    for method in ("static", "full_reopt", "sarcrp"):
        matching = [r["total_cost_mean"] for r in rows if r["method"] == method]
        changed = [r["changed_actions_total"] for r in rows if r["method"] == method]
        by_method[method] = {
            "total_cost_mean": statistics.mean(matching) if matching else float("nan"),
            "changed_actions_mean": statistics.mean(changed) if changed else float("nan"),
        }

    sarcrp, static, full_reopt = by_method["sarcrp"], by_method["static"], by_method["full_reopt"]
    return {
        "sarcrp_beats_static_total_cost": sarcrp["total_cost_mean"] < static["total_cost_mean"],
        "sarcrp_beats_full_reopt_stability": sarcrp["changed_actions_mean"] < full_reopt["changed_actions_mean"],
        "sarcrp_close_to_full_reopt_operational": abs(sarcrp["total_cost_mean"] - full_reopt["total_cost_mean"]) <= 0.20 * full_reopt["total_cost_mean"],
    }


def main():
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

    verdict = evaluate_decision_gate(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")
    print("Decision gate (spec 33):")
    for key, passed in verdict.items():
        print(f"  {key}: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    main()
