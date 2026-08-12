"""External validity check for the dead-zone fix (follow-up to a reviewer
critique on the Q1 report): §External Validity's Lee-Shin table shows
SAR-CRP tying Static on both real published Lee et al. instances -- but
that table was run under the ORIGINAL objective, before DZ1/DZ2 were
diagnosed and fixed. This answers the resulting question directly: is
that tie an artifact of this project's own generated 16-instance sweep
never overlapping with real benchmark geometry, or does the dead-zone fix
(normalize_delay=False, tau_abs=derive_tau_abs()) unlock the same kind of
update on real data too?

Uses the SAME forced-single-event, deterministic-budget, fixed-objective
protocol as run_dead_zone_baseline_comparison.py -- not
run_lee_shin_benchmark.py's natural random-event episode. §20 SC4 already
showed natural event streams almost never cross SAR-CRP's impact threshold
regardless of the objective (mean impact 0.09-0.12 against a 0.30
threshold), so re-running the natural-episode benchmark would not isolate
whether the FIX itself works -- it would just reproduce the trigger-rarity
finding again. Forcing the one decision the dead zones were blocking does
isolate it, exactly as it did for the 16 generated instances."""
import csv
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))
from run_dead_zone_baseline_comparison import METHODS, build_event, score  # noqa: E402

from sarcrp.baselines import full_reoptimization, mpc_receding_horizon, periodic_replan, static_plan  # noqa: E402
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.lee_shin_loader import load_lee_instance  # noqa: E402
from sarcrp.objective import derive_tau_abs  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402
from sarcrp.sarcrp_core import replan  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS  # noqa: E402
from sarcrp.stats import cliffs_delta, wilcoxon_signed_rank  # noqa: E402

TAU_FRAC = 0.01
TAU_ABS = derive_tau_abs()  # kappa=0.5, same derivation as every other dead-zone experiment
SEEDS = REPORT_SEEDS[:5]  # matches the 16-instance sweep's own seed count
EVENT_CONFIDENCE = 0.5

# The same two real Lee et al. instances already used in
# run_lee_shin_benchmark.py (external/CRP_RL/benchmarks/Lee_instances).
INSTANCES = (
    {"label": "Lee_R020306_020c", "inst_type": "random", "n_bays": 2, "n_rows": 3, "n_tiers": 6, "idx": 1},
    {"label": "Lee_R011606_070c", "inst_type": "random", "n_bays": 1, "n_rows": 16, "n_tiers": 6, "idx": 1},
)


def run_lee_instance(spec: dict, seed: int, event_kind: str = "urgent_insertion") -> dict:
    state = load_lee_instance(spec["inst_type"], spec["n_bays"], spec["n_rows"], spec["n_tiers"], spec["idx"])
    old_queue = list(state.retrieval_queue)
    plan_old = solve_crp(state, old_queue, time_limit_sec=None)
    new_queue, urgent = build_event(old_queue, event_kind)
    rng = random.Random(seed)

    plans = {}
    plans["static"] = static_plan(plan_old)
    plans["full_reopt"] = full_reoptimization(state, new_queue, time_limit_sec=None)
    plans["periodic"] = periodic_replan(state, new_queue, plan_old, event_index=5, period=5, time_limit_sec=None)
    plans["mpc"] = mpc_receding_horizon(state, plan_old, new_queue, horizon=3, time_limit_sec=None)

    d_ets = replan(state, plan_old, old_queue, new_queue, urgent, rng=rng, conf_new=EVENT_CONFIDENCE,
                    lam=0.0, mu=0.0, tau_frac=TAU_FRAC, tau_abs=TAU_ABS, normalize_delay=False, time_limit_sec=None)
    plans["event_triggered_no_stability"] = d_ets.plan

    rng2 = random.Random(seed)
    d_sarcrp = replan(state, plan_old, old_queue, new_queue, urgent, rng=rng2, conf_new=EVENT_CONFIDENCE,
                        tau_frac=TAU_FRAC, tau_abs=TAU_ABS, normalize_delay=False, time_limit_sec=None)
    plans["sarcrp"] = d_sarcrp.plan

    costs = {m: score(p, plan_old, urgent, EVENT_CONFIDENCE, state) for m, p in plans.items()}
    return {
        "instance": spec["label"], "n_containers": len(old_queue), "seed": seed, "event_kind": event_kind,
        "sarcrp_decision": d_sarcrp.decision,
        **{f"cost_{m}": costs[m] for m in METHODS},
    }


def print_comparison(rows: list[dict], label: str) -> None:
    print(f"\n{'instance':>20} {'n':>4} {'seed':>5} " + "".join(f"{m[:10]:>12}" for m in METHODS) + "  decision")
    for r in rows:
        print(f"{r['instance']:>20} {r['n_containers']:>4} {r['seed']:>5} "
              + "".join(f"{r[f'cost_{m}']:>12.3f}" for m in METHODS) + f"  {r['sarcrp_decision']}")

    print(f"\n=== [{label}] SAR-CRP vs.\\ each baseline on real Lee et al. instances, n={len(rows)} ===")
    sarcrp_costs = [r["cost_sarcrp"] for r in rows]
    for m in METHODS:
        if m == "sarcrp":
            continue
        other = [r[f"cost_{m}"] for r in rows]
        n_sarcrp_better = sum(1 for a, b in zip(sarcrp_costs, other) if a < b)
        n_tied = sum(1 for a, b in zip(sarcrp_costs, other) if a == b)
        n_worse = sum(1 for a, b in zip(sarcrp_costs, other) if a > b)
        wr = wilcoxon_signed_rank(sarcrp_costs, other)
        delta = cliffs_delta(sarcrp_costs, other)
        print(f"  vs {m:>28}: sarcrp better={n_sarcrp_better} tied={n_tied} worse={n_worse}  "
              f"mean(sarcrp)={statistics.mean(sarcrp_costs):.3f} mean({m})={statistics.mean(other):.3f}  "
              f"wilcoxon_p={wr.p_value:.5f} cliffs_delta={delta:.3f}")

    n_update = sum(1 for r in rows if r["sarcrp_decision"] == "UPDATE")
    print(f"\n  SAR-CRP UPDATE rate [{label}]: {n_update}/{len(rows)}")


def main():
    _start = time.monotonic()
    print(f"tau_abs (derived, kappa=0.5) = {TAU_ABS}")

    all_rows = []
    for event_kind in ("urgent_insertion", "order_swap"):
        rows = [run_lee_instance(spec, seed, event_kind=event_kind) for spec in INSTANCES for seed in SEEDS]
        all_rows.extend(rows)
        print_comparison(rows, event_kind)

    out = Path(__file__).parent / "results" / "lee_shin_dead_zone_fix.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)
    print(f"\nWrote {out} ({len(all_rows)} rows)")

    log_run("run_lee_shin_dead_zone_fix.py",
            {"instances": [s["label"] for s in INSTANCES], "seeds": list(SEEDS), "tau_abs": TAU_ABS,
             "event_kinds": ["urgent_insertion", "order_swap"]},
            time.monotonic() - _start, [str(out)])


if __name__ == "__main__":
    main()
