"""R1.3/R2.3 (reviewer critique): Scenario E's generalization currently
rests on exactly ONE independently-built second instance (instance B,
crp_rl_scale_instance_b.json) beyond instance A. Is instance B's
sub-margin-gain pattern a one-off coincidence of that specific
(num_stacks, containers_per_stack) pair, or does it recur for other
dimensions built with the identical deterministic recipe? This sweeps a
bounded grid of (num_stacks, containers_per_stack) pairs -- excluding the
two combinations already used for instance A (10x5=50) and instance B
(11x4=44) -- with the SAME bottom-first round-robin construction and the
SAME forced-last-container-promotion event, checking each candidate's own
gain-vs-tau pattern with a cheap 2-seed filter before spending a full
20-seed confirmation on anything promising. No SAR-CRP parameter
(theta_impact, tau_frac, lambda) is ever touched -- only the instance's
own dimensions vary, exactly as instance B was found.
"""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.sarcrp_core import replan  # noqa: E402
from sarcrp.schemas import Layout, Stack, YardState  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS  # noqa: E402

SCALE_EVENT_CONFIDENCE = 0.5  # matches run_existence_proof.py's instances A/B
ALREADY_USED = {(10, 5), (11, 4)}  # instance A, instance B


def build_instance(num_stacks: int, containers_per_stack: int) -> tuple[YardState, list[str], str]:
    """Identical bottom-first round-robin recipe as generate_crp_rl_scale_instance[_b].py."""
    max_tier = containers_per_stack + 1  # headroom above a full stack for relocations
    per_stack_containers = []
    container_id = 1
    stacks = []
    for s in range(num_stacks):
        containers = [f"C{c:03d}" for c in range(container_id, container_id + containers_per_stack)]
        container_id += containers_per_stack
        per_stack_containers.append(containers)
        stacks.append(Stack(id=f"S{s + 1}", containers=list(containers), max_tier=max_tier))

    retrieval_order = []
    for tier in range(containers_per_stack):
        for containers in per_stack_containers:
            retrieval_order.append(containers[tier])

    state = YardState(
        instance_id=f"sweep_{num_stacks}x{containers_per_stack}", time_step=0,
        layout=Layout(num_stacks=num_stacks, max_tier=max_tier), stacks=stacks,
        container_attributes={}, retrieval_queue=retrieval_order, pickup_prob={},
        data_timestamp=0, state_confidence=1.0,
    )
    return state, retrieval_order, retrieval_order[-1]


def force_urgent_insertion(old_queue: list[str], target: str) -> list[str]:
    return [target] + [c for c in old_queue if c != target]


def check_candidate(num_stacks: int, containers_per_stack: int, seeds: tuple) -> list[tuple[float, float]]:
    state, old_queue, target = build_instance(num_stacks, containers_per_stack)
    plan_old = solve_crp(state, old_queue, time_limit_sec=5.0)
    new_queue = force_urgent_insertion(old_queue, target)
    urgent = [target]
    results = []
    for seed in seeds:
        decision = replan(state, plan_old, old_queue, new_queue, urgent, rng=random.Random(seed),
                           conf_new=SCALE_EVENT_CONFIDENCE, time_limit_sec=5.0)
        gain = decision.j_old - decision.j_new
        tau = 0.01 * decision.j_old
        results.append((gain, tau))
    return results


def main():
    _start = time.monotonic()
    candidates = [
        (ns, cps)
        for ns in (6, 7, 8, 9, 12, 13, 14, 15)
        for cps in (4, 5, 6, 7, 8)
        if 35 <= ns * cps <= 70 and (ns, cps) not in ALREADY_USED
    ]
    print(f"Quick-filtering {len(candidates)} candidates on seeds {REPORT_SEEDS[:2]}...")
    promising = []
    for ns, cps in candidates:
        quick = check_candidate(ns, cps, seeds=REPORT_SEEDS[:2])
        any_gain = any(g > 0 for g, _ in quick)
        print(f"  ({ns}x{cps}={ns*cps}): {quick}  {'PROMISING' if any_gain else 'zero gain'}")
        if any_gain:
            promising.append((ns, cps))

    print(f"\n{len(promising)} promising candidate(s): {promising}")
    print("Confirming each on the full REPORT_SEEDS (20 seeds)...")
    for ns, cps in promising:
        full = check_candidate(ns, cps, seeds=REPORT_SEEDS)
        n_positive = sum(1 for g, _ in full if g > 0)
        n_under_tau = sum(1 for g, tau in full if 0 < g < tau)
        n_clears_tau = sum(1 for g, tau in full if g >= tau)
        print(f"  ({ns}x{cps}): gain>0 on {n_positive}/20, sub-margin (0<gain<tau) on {n_under_tau}/20, "
              f"clears tau alone on {n_clears_tau}/20")
        print(f"    raw: {full}")

    print(f"\nTotal sweep time: {time.monotonic() - _start:.1f}s")


if __name__ == "__main__":
    main()
