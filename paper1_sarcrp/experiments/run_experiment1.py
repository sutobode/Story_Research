import csv
import json
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.simulator import run_episode  # noqa: E402
from sarcrp.stats import bootstrap_ci, cliffs_delta, holm_bonferroni, wilcoxon_signed_rank  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS as SEEDS  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402

METHODS = ("static", "full_reopt", "periodic", "event_triggered_no_stability", "mpc", "sarcrp")
FACTOR_GRID = {
    "uncertainty_level": ("low", "medium", "high"),
    "freeze_size": (0, 3, 5),
    "lam": (0.0, 0.5, 1.0),
}

METHODS_WITH_FREEZE_HORIZON = {"sarcrp", "event_triggered_no_stability"}
METHODS_WITH_LAMBDA = {"sarcrp"}  # event_triggered_no_stability fixes lambda=0 by definition (spec 40) -- never overridable


def run_factorial(instance: dict, methods=METHODS, seeds=SEEDS) -> list[dict]:
    """Experiment 1 (spec 23): uncertainty x freeze_size x lambda, all 6
    methods. freeze_size/lam are only *passed through* to sarcrp/
    event_triggered_no_stability (run_episode's h_f=/lam= params only affect
    those two dispatch branches) -- other methods still run at every grid
    point for a like-for-like comparison at the same seed, they just have no
    parameter for those factors to act on."""
    rows = []
    for uncertainty in FACTOR_GRID["uncertainty_level"]:
        for freeze_size in FACTOR_GRID["freeze_size"]:
            for lam in FACTOR_GRID["lam"]:
                level_instance = dict(instance, uncertainty_level=uncertainty)
                for method in methods:
                    h_f_arg = freeze_size if method in METHODS_WITH_FREEZE_HORIZON else None
                    lam_arg = lam if method in METHODS_WITH_LAMBDA else None
                    for seed in seeds:
                        metrics = run_episode(level_instance, method_name=method, rng=random.Random(seed), h_f=h_f_arg, lam=lam_arg)
                        rows.append({
                            "uncertainty_level": uncertainty, "freeze_size": freeze_size, "lam": lam,
                            "method": method, "seed": seed,
                            "total_cost_mean": metrics.total_cost_mean,
                            "operational_cost_mean": metrics.operational_cost_mean,
                            "changed_actions_total": metrics.changed_actions_total,
                            "runtime_mean_sec": metrics.runtime_mean_sec,
                            "fallback_rate": metrics.fallback_rate,
                        })
    return rows


def run_significance_tests(rows: list[dict], baseline_methods=("static", "full_reopt", "periodic", "event_triggered_no_stability", "mpc")) -> dict:
    """spec 23.6: SAR-CRP vs each of B1-B5, paired by seed, Holm-Bonferroni
    corrected across the len(baseline_methods) comparisons, with Cliff's delta."""
    by_seed_sarcrp = {r["seed"]: r["total_cost_mean"] for r in rows if r["method"] == "sarcrp"}
    seeds_sorted = sorted(by_seed_sarcrp)
    sarcrp_values = [by_seed_sarcrp[s] for s in seeds_sorted]

    raw_p_values = []
    per_baseline = {}
    for baseline in baseline_methods:
        by_seed_baseline = {r["seed"]: r["total_cost_mean"] for r in rows if r["method"] == baseline}
        baseline_values = [by_seed_baseline[s] for s in seeds_sorted if s in by_seed_baseline]
        matched_sarcrp = [by_seed_sarcrp[s] for s in seeds_sorted if s in by_seed_baseline]
        wilcoxon_result = wilcoxon_signed_rank(matched_sarcrp, baseline_values)
        delta = cliffs_delta(matched_sarcrp, baseline_values)
        raw_p_values.append(wilcoxon_result.p_value)
        per_baseline[baseline] = {
            "p_value": wilcoxon_result.p_value,
            "n_pairs": wilcoxon_result.n_pairs,
            "n_nonzero_pairs": wilcoxon_result.n_nonzero_pairs,
            "cliffs_delta": delta,
        }

    significant_flags = holm_bonferroni(raw_p_values)
    for baseline, flag in zip(baseline_methods, significant_flags):
        per_baseline[baseline]["p_value_holm_significant"] = flag

    per_baseline["_sarcrp_ci"] = bootstrap_ci(sarcrp_values, rng=random.Random(0))
    return per_baseline


def main():
    _start = time.monotonic()
    instance = json.loads((Path(__file__).parent / "instances" / "small_layout_mvp.json").read_text())
    rows = run_factorial(instance)

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "experiment1_results.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")

    significance = run_significance_tests(rows)
    sig_path = results_dir / "experiment1_significance.csv"
    with sig_path.open("w", newline="") as f:
        f.write("baseline,p_value,n_pairs,n_nonzero_pairs,p_value_holm_significant,cliffs_delta\n")
        for baseline, stats_row in significance.items():
            if baseline == "_sarcrp_ci":
                continue
            f.write(f"{baseline},{stats_row['p_value']:.6f},{stats_row['n_pairs']},{stats_row['n_nonzero_pairs']},"
                    f"{stats_row['p_value_holm_significant']},{stats_row['cliffs_delta']:.4f}\n")
    print(f"Wrote significance table to {sig_path}")
    for baseline, stats_row in significance.items():
        if baseline == "_sarcrp_ci":
            continue
        print(f"SAR-CRP vs {baseline}: p={stats_row['p_value']:.4f} "
              f"(n_nonzero_pairs={stats_row['n_nonzero_pairs']}/{stats_row['n_pairs']}, "
              f"Holm-significant={stats_row['p_value_holm_significant']}), "
              f"Cliff's delta={stats_row['cliffs_delta']:.3f}")

    log_run("run_experiment1.py", {"seeds": list(SEEDS), "factor_grid": FACTOR_GRID, "methods": list(METHODS)},
            time.monotonic() - _start, [str(out_path), str(sig_path)])


if __name__ == "__main__":
    main()
