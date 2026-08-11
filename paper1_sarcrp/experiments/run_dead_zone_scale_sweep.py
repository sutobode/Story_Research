"""The decisive experiment for the dead-zone finding: a falsifiable,
quantitative prediction with a sharp threshold, tested across MANY
instances at MANY scales -- not one constructed instance pair.

THEORY (proven in tests/test_objective_dead_zones.py):
  * The largest operational gain any delay-driven repair can obtain is
    g_max(L) = beta * (L-1)/(L+1), bounded above by beta=0.5 for every
    instance size (RetrievalDelayNorm is normalized to [0,1]).
  * The purely relative switching margin is tau_rel = tau_frac * J_old,
    which GROWS with instance size.
  * PREDICTION: a delay-driven UPDATE is possible under the purely
    relative margin if and only if g_max(L) > tau_frac * J_old. Since
    J_old grows roughly linearly in instance size while g_max does not,
    every instance beyond the crossover is blocked -- by construction, not
    by chance.
  * FIX: the mixed relative-absolute margin tau = min(tau_rel, tau_abs)
    with tau_abs = kappa * beta (objective.derive_tau_abs) removes the
    scale dependence, so UPDATE stays possible at every scale.

This sweep builds instances with the same deterministic bottom-first
round-robin recipe already used for the existence-proof instances, spanning
a wide range of J_old, applies the same deterministic forced urgent
insertion, and records for each instance whether the theory's inequality
predicted the observed decision -- under both margin forms. A single
mispredicted instance falsifies the theory.
"""
import csv
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.objective import BETA_DEFAULT, derive_tau_abs, max_delay_driven_gain  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402
from sarcrp.sarcrp_core import replan  # noqa: E402
from sarcrp.schemas import Layout, Stack, YardState  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS  # noqa: E402

SCALE_EVENT_CONFIDENCE = 0.5  # identical to the existence-proof instances
TAU_FRAC = 0.01  # spec default, never varied here

# The INSTANCE is the replication unit here (16 distinct instances spanning
# 9-84 containers), which is what answers the "n is effectively 1" critique
# of the constructed two-instance Scenario E chain. Seeds only absorb the
# local search's own stochasticity within an instance, so a small seed count
# suffices; every number uses the deterministic budget (bug #11).
SEEDS = REPORT_SEEDS[:5]

# (num_stacks, containers_per_stack) pairs spanning small (well under the
# predicted crossover) to large (well past it), same construction recipe.
SCALE_GRID = (
    (3, 3), (4, 3), (4, 4), (5, 4), (6, 4), (5, 5),
    (7, 4), (6, 5), (8, 4), (7, 5), (10, 5), (11, 5),
    (12, 5), (10, 7), (12, 6), (14, 6),
)


def build_instance(num_stacks: int, containers_per_stack: int):
    """Identical recipe to generate_crp_rl_scale_instance[_b].py."""
    max_tier = containers_per_stack + 1
    per_stack, stacks, cid = [], [], 1
    for s in range(num_stacks):
        containers = [f"C{c:03d}" for c in range(cid, cid + containers_per_stack)]
        cid += containers_per_stack
        per_stack.append(containers)
        stacks.append(Stack(id=f"S{s + 1}", containers=list(containers), max_tier=max_tier))
    retrieval_order = [containers[tier] for tier in range(containers_per_stack) for containers in per_stack]
    state = YardState(
        instance_id=f"scale_{num_stacks}x{containers_per_stack}", time_step=0,
        layout=Layout(num_stacks=num_stacks, max_tier=max_tier), stacks=stacks,
        container_attributes={}, retrieval_queue=retrieval_order, pickup_prob={},
        data_timestamp=0, state_confidence=1.0,
    )
    return state, retrieval_order, retrieval_order[-1]


def evaluate_instance(num_stacks: int, containers_per_stack: int, tau_abs: float | None,
                       normalize_delay: bool = True, seeds=SEEDS) -> dict:
    # DETERMINISTIC BUDGET (time_limit_sec=None): bug #11 showed a wall-clock
    # cutoff makes results machine- and load-dependent (the walk finishes in
    # 4.10s of a 5.0s default, so a ~20% slower machine truncates it and the
    # gain collapses to 0). Every number in this sweep uses the
    # iteration-count budget only, so it is reproducible across machines.
    state, old_queue, target = build_instance(num_stacks, containers_per_stack)
    plan_old = solve_crp(state, old_queue, time_limit_sec=None)
    new_queue = [target] + [c for c in old_queue if c != target]
    urgent = [target]

    decisions, gains, j_olds = [], [], []
    for seed in seeds:
        d = replan(state, plan_old, old_queue, new_queue, urgent, rng=random.Random(seed),
                    conf_new=SCALE_EVENT_CONFIDENCE, tau_frac=TAU_FRAC, tau_abs=tau_abs,
                    normalize_delay=normalize_delay, time_limit_sec=None)
        decisions.append(d.decision)
        gains.append(d.j_old - d.j_new)
        j_olds.append(d.j_old)

    j_old = statistics.mean(j_olds)
    plan_len = len(plan_old.actions)
    g_max = max_delay_driven_gain(plan_length=plan_len, normalize_delay=normalize_delay)
    tau_rel = TAU_FRAC * j_old
    tau_eff = tau_rel if tau_abs is None else min(tau_rel, tau_abs)
    # The theory's inequality: an UPDATE is possible iff the achievable
    # gain can exceed the effective margin.
    predicted_update_possible = g_max > tau_eff
    n_update = sum(1 for x in decisions if x == "UPDATE")
    return {
        "num_stacks": num_stacks, "containers_per_stack": containers_per_stack,
        "normalize_delay": normalize_delay,
        "n_containers": num_stacks * containers_per_stack, "plan_length": plan_len,
        "j_old": j_old, "g_max_theory": g_max, "mean_gain_observed": statistics.mean(gains), "max_gain_observed": max(gains),
        "tau_rel": tau_rel, "tau_abs": tau_abs, "tau_effective": tau_eff,
        "predicted_update_possible": predicted_update_possible,
        "n_update": n_update, "n_seeds": len(seeds),
        "observed_any_update": n_update > 0,
        "prediction_correct": predicted_update_possible == (n_update > 0),
    }


def main():
    _start = time.monotonic()
    tau_abs_derived = derive_tau_abs()  # kappa=0.5 -> 0.25
    print(f"beta={BETA_DEFAULT}  tau_frac={TAU_FRAC}  derived tau_abs=kappa*beta={tau_abs_derived}")
    print(f"predicted crossover (purely relative margin): J_old = beta/tau_frac = {BETA_DEFAULT / TAU_FRAC:.0f}\n")

    rows = []
    # Full 2x2 design space: margin form x delay formulation. The theory says
    # only ONE quadrant is non-degenerate (mixed margin + action-scaled delay).
    for normalize_delay, delay_label in ((True, "delay=normalized"), (False, "delay=actions")):
        for tau_abs, margin_label in ((None, "margin=relative"), (tau_abs_derived, "margin=mixed")):
            print(f"=== {delay_label} | {margin_label} (tau_abs={tau_abs}) ===", flush=True)
            print(f"{'inst':>8} {'n_cont':>7} {'J_old':>9} {'g_max':>9} {'gain_obs':>9} "
                  f"{'tau_eff':>8} {'pred':>6} {'UPDATE':>8} {'ok':>4}", flush=True)
            for ns, cps in SCALE_GRID:
                r = evaluate_instance(ns, cps, tau_abs, normalize_delay=normalize_delay)
                r["margin_form"] = margin_label
                r["delay_form"] = delay_label
                rows.append(r)
                print(f"{ns:>3}x{cps:<4} {r['n_containers']:>7} {r['j_old']:>9.3f} {r['g_max_theory']:>9.3f} "
                      f"{r['max_gain_observed']:>9.4f} {r['tau_effective']:>8.4f} "
                      f"{str(r['predicted_update_possible']):>6} {r['n_update']:>3}/{r['n_seeds']:<4} "
                      f"{'OK' if r['prediction_correct'] else 'MISS':>4}", flush=True)
            print(flush=True)

    out = Path(__file__).parent / "results" / "dead_zone_scale_sweep.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n_correct = sum(r["prediction_correct"] for r in rows)
    print(f"THEORY PREDICTION ACCURACY: {n_correct}/{len(rows)} instance-configurations")
    print("\n2x2 DESIGN SPACE (instances where SOME seed updated / total):")
    for delay_label in ("delay=normalized", "delay=actions"):
        for margin_label in ("margin=relative", "margin=mixed"):
            sub = [r for r in rows if r["margin_form"] == margin_label and r["delay_form"] == delay_label]
            n_any = sum(r["observed_any_update"] for r in sub)
            print(f"  {delay_label:>18} x {margin_label:<16}: {n_any:>2}/{len(sub)}")
    print(f"\nWrote {out}")
    log_run("run_dead_zone_scale_sweep.py",
            {"scale_grid": [list(x) for x in SCALE_GRID], "tau_frac": TAU_FRAC,
             "tau_abs_derived": tau_abs_derived, "seeds": list(REPORT_SEEDS)},
            time.monotonic() - _start, [])


if __name__ == "__main__":
    main()
