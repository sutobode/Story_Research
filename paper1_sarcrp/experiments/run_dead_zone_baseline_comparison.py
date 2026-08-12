"""The decisive experiment the dead-zone fix (run_dead_zone_scale_sweep.py)
did not answer: fixing DZ1/DZ2 makes SAR-CRP's mechanism ACT (14/16
instances produce an UPDATE) -- but acting is not the same as being GOOD.
This compares SAR-CRP against all five baselines (B1-B5) under the FIXED
objective (action-scaled delay, mixed threshold) on the same 16 instances,
answering: once the objective's dead zones are removed, does SAR-CRP's
repair actually beat never-replanning and the other baselines, or does it
merely become capable of acting without being worth it?

Design, reusing exactly the dead-zone sweep's own instance construction and
its single forced-urgent-insertion event (not a full multi-step episode --
this isolates the one decision the dead zones were blocking):
  - All 6 methods (B1-B5, SAR-CRP) face the IDENTICAL instance and event.
  - Every method's resulting plan is scored under the SAME fixed objective
    (normalize_delay=False), so the comparison is apples-to-apples --
    scoring MPC's or Periodic's plan under the old objective while scoring
    SAR-CRP's under the new one would not be a fair test of the fix.
  - Deterministic budget throughout (bug #11): no wall-clock cutoffs.
  - Periodic (B3) is evaluated at event_index=5 (a multiple of its default
    period=5), so it actually replans at this decision point rather than
    trivially keeping by construction of an arbitrary index.
"""
import csv
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))
from run_dead_zone_scale_sweep import SCALE_GRID, build_instance  # noqa: E402

from sarcrp.baselines import full_reoptimization, mpc_receding_horizon, periodic_replan, static_plan  # noqa: E402
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.objective import (  # noqa: E402
    compute_objective, data_confidence_cost, derive_tau_abs, operational_cost, stability_cost,
)
from sarcrp.plan_validator import is_plan_valid  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402
from sarcrp.sarcrp_core import replan  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS  # noqa: E402
from sarcrp.stats import cliffs_delta, wilcoxon_signed_rank  # noqa: E402

SCALE_EVENT_CONFIDENCE = 0.5
TAU_FRAC = 0.01
TAU_ABS = derive_tau_abs()  # kappa=0.5 -> 0.25, same derivation as the sweep
SEEDS = REPORT_SEEDS[:5]  # matches the sweep's own seed count
METHODS = ("static", "full_reopt", "periodic", "event_triggered_no_stability", "mpc", "sarcrp")


def score(plan, plan_old, urgent, conf_new, state) -> float:
    """Every method's resulting plan scored under the IDENTICAL fixed
    objective (normalize_delay=False) -- the whole point of this
    experiment is that this scoring function must not differ by method."""
    is_valid = is_plan_valid(plan, state)
    op = operational_cost(plan, urgent, is_valid=is_valid, normalize_delay=False)
    stab, violated = stability_cost(plan, plan_old, frozen_count=0)
    if violated:
        return float("inf")
    data = data_confidence_cost(plan, plan_old, conf_new)
    return compute_objective(op, stab, data)


def build_event(old_queue: list[str], event_kind: str) -> tuple[list[str], list[str]]:
    """Two deterministic event constructions, not one -- R1.2 (reviewer
    critique): the dead-zone sweep and the original baseline comparison
    both used only "urgent_insertion", so every decisive result in this
    report rested on a single disruption type. "order_swap" is the
    structural opposite case: no container becomes urgent (urgent=[]), so
    RetrievalDelayNorm/retrieval_delay_actions are identically 0 by
    construction (event_generator.py's own convention: only
    URGENT_INSERTION populates the urgent set) -- any gain here can only
    come from the relocation-count channel, not delay, isolating that
    channel's contribution from DZ1/DZ2 entirely."""
    if event_kind == "urgent_insertion":
        target = old_queue[-1]
        return [target] + [c for c in old_queue if c != target], [target]
    if event_kind == "order_swap":
        # A large, deterministic reordering (swap first and last position)
        # -- not sampled, for the same reproducibility reason every other
        # event in this report is constructed deterministically.
        new_queue = list(old_queue)
        new_queue[0], new_queue[-1] = new_queue[-1], new_queue[0]
        return new_queue, []
    raise ValueError(f"unknown event_kind: {event_kind!r}")


def run_instance(num_stacks: int, containers_per_stack: int, seed: int, event_kind: str = "urgent_insertion") -> dict:
    state, old_queue, _ = build_instance(num_stacks, containers_per_stack)
    plan_old = solve_crp(state, old_queue, time_limit_sec=None)
    new_queue, urgent = build_event(old_queue, event_kind)
    rng = random.Random(seed)

    plans = {}
    plans["static"] = static_plan(plan_old)
    plans["full_reopt"] = full_reoptimization(state, new_queue, time_limit_sec=None)
    plans["periodic"] = periodic_replan(state, new_queue, plan_old, event_index=5, period=5, time_limit_sec=None)
    plans["mpc"] = mpc_receding_horizon(state, plan_old, new_queue, horizon=3, time_limit_sec=None)

    d_ets = replan(state, plan_old, old_queue, new_queue, urgent, rng=rng, conf_new=SCALE_EVENT_CONFIDENCE,
                    lam=0.0, mu=0.0, tau_frac=TAU_FRAC, tau_abs=TAU_ABS, normalize_delay=False, time_limit_sec=None)
    plans["event_triggered_no_stability"] = d_ets.plan

    rng2 = random.Random(seed)
    d_sarcrp = replan(state, plan_old, old_queue, new_queue, urgent, rng=rng2, conf_new=SCALE_EVENT_CONFIDENCE,
                        tau_frac=TAU_FRAC, tau_abs=TAU_ABS, normalize_delay=False, time_limit_sec=None)
    plans["sarcrp"] = d_sarcrp.plan

    costs = {m: score(p, plan_old, urgent, SCALE_EVENT_CONFIDENCE, state) for m, p in plans.items()}
    return {
        "num_stacks": num_stacks, "containers_per_stack": containers_per_stack,
        "n_containers": num_stacks * containers_per_stack, "seed": seed, "event_kind": event_kind,
        "sarcrp_decision": d_sarcrp.decision,
        **{f"cost_{m}": costs[m] for m in METHODS},
    }


def print_comparison(rows: list[dict], label: str) -> None:
    print(f"\n{'inst':>8} {'n':>4} " + "".join(f"{m[:10]:>12}" for m in METHODS) + "  decision")
    for r in rows:
        print(f"{r['num_stacks']:>3}x{r['containers_per_stack']:<4} {r['n_containers']:>4} "
              + "".join(f"{r[f'cost_{m}']:>12.3f}" for m in METHODS) + f"  {r['sarcrp_decision']}")

    print(f"\n=== [{label}] SAR-CRP vs.\\ each baseline, paired by (instance, seed), n={len(rows)} ===")
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

    # R2.1 (reviewer critique): n=80 is not 80 statistically independent
    # points -- 5 seeds within the same instance only absorb local-search
    # noise, the instance is the real unit of independence. Aggregate to
    # one point per instance (mean over seeds) and re-test at n=16.
    by_instance = {}
    for r in rows:
        key = (r["num_stacks"], r["containers_per_stack"])
        by_instance.setdefault(key, []).append(r)
    inst_sarcrp = [statistics.mean(r["cost_sarcrp"] for r in grp) for grp in by_instance.values()]
    print(f"\n  --- same comparison aggregated to n={len(inst_sarcrp)} instances (mean over seeds) ---")
    for m in METHODS:
        if m == "sarcrp":
            continue
        inst_other = [statistics.mean(r[f"cost_{m}"] for r in grp) for grp in by_instance.values()]
        n_better = sum(1 for a, b in zip(inst_sarcrp, inst_other) if a < b)
        n_tied = sum(1 for a, b in zip(inst_sarcrp, inst_other) if a == b)
        n_worse = sum(1 for a, b in zip(inst_sarcrp, inst_other) if a > b)
        wr = wilcoxon_signed_rank(inst_sarcrp, inst_other)
        delta = cliffs_delta(inst_sarcrp, inst_other)
        print(f"  vs {m:>28}: sarcrp better={n_better} tied={n_tied} worse={n_worse}  "
              f"wilcoxon_p={wr.p_value:.5f} cliffs_delta={delta:.3f}")

    n_update = sum(1 for r in rows if r["sarcrp_decision"] == "UPDATE")
    print(f"\n  SAR-CRP UPDATE rate [{label}]: {n_update}/{len(rows)}")


def main():
    _start = time.monotonic()
    print(f"tau_abs (derived, kappa=0.5) = {TAU_ABS}")

    all_rows = []
    for event_kind in ("urgent_insertion", "order_swap"):
        rows = [run_instance(ns, cps, seed, event_kind=event_kind)
                for ns, cps in SCALE_GRID for seed in SEEDS]
        all_rows.extend(rows)
        print_comparison(rows, event_kind)

    out = Path(__file__).parent / "results" / "dead_zone_baseline_comparison.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)
    print(f"\nWrote {out} ({len(all_rows)} rows)")

    log_run("run_dead_zone_baseline_comparison.py",
            {"scale_grid": [list(x) for x in SCALE_GRID], "seeds": list(SEEDS), "tau_abs": TAU_ABS,
             "event_kinds": ["urgent_insertion", "order_swap"]},
            time.monotonic() - _start, [])


if __name__ == "__main__":
    main()
