import random
import statistics
from collections import Counter
from dataclasses import dataclass

from sarcrp.baselines import full_reoptimization, static_plan
from sarcrp.crp_solver import solve_crp
from sarcrp.event_generator import generate_event_stream
from sarcrp.impact_estimator import compute_impact
from sarcrp.objective import operational_cost
from sarcrp.simulator import _build_state


@dataclass
class SanityReport:
    sc1_not_too_easy: bool
    sc2_not_too_hard: bool
    event_type_frequency: dict[str, float]
    mean_impact: float
    sc4_impact_reasonable: bool
    trigger_rate: float


def run_sanity_checks(
    instance: dict, seeds: tuple = tuple(range(10)),
    weights: dict | None = None, theta_impact: float = 0.30, calibrated: bool = False,
) -> SanityReport:
    """SC1-SC4 (spec 20, 49).

    SC1 measures the Static baseline (spec's own definition: does an
    unchanging plan get worse under events than with no events at all).

    SC2 must measure genuine solver failure ("fail hoac timeout qua nhieu"),
    not Static's fallback rate -- Static never updates *by definition*, so
    its own "fallback rate" is trivially 100% regardless of how hard the
    benchmark is and would make SC2 vacuously fail on every instance. This
    runs Full Reoptimization instead (spec 22 B2, the method that actually
    attempts to solve every event) and checks whether it ever returns an
    incomplete plan -- fewer RETRIEVE actions than containers in the current
    queue, which is exactly what crp_solver.solve_crp's time_limit_sec cutoff
    or an exhausted destination search produces."""
    queue = list(instance["initial_retrieval_order"])
    static_state = _build_state(instance, queue)
    no_event_plan = solve_crp(static_state, queue, time_limit_sec=5.0)
    no_event_cost = operational_cost(no_event_plan, urgent_containers=[], is_valid=True)

    all_event_types: Counter = Counter()
    all_impacts: list[float] = []
    dynamic_costs: list[float] = []
    solver_failure_flags: list[bool] = []

    for seed in seeds:
        rng = random.Random(seed)
        state = _build_state(instance, queue)
        plan = solve_crp(state, queue, time_limit_sec=5.0)
        events = generate_event_stream(queue, instance["t_steps"], instance["uncertainty_level"], rng, calibrated=calibrated)
        local_queue = list(queue)

        for event in events:
            all_event_types[event.type] += 1
            impact = compute_impact(local_queue, event.new_queue, state, state, plan, conf_new=event.confidence, weights=weights)
            all_impacts.append(impact.total)

            static_result = static_plan(plan)
            urgent = [event.affected_containers[0]] if event.type == "URGENT_INSERTION" and event.affected_containers else []
            dynamic_costs.append(operational_cost(static_result, urgent, is_valid=True))

            full_reopt_plan = full_reoptimization(state, event.new_queue, time_limit_sec=5.0)
            retrieved = sum(1 for a in full_reopt_plan.actions if a.type == "RETRIEVE")
            solver_failure_flags.append(retrieved < len(event.new_queue))

            plan = static_result
            local_queue = event.new_queue

    total_events = sum(all_event_types.values())
    frequency = {etype: count / total_events for etype, count in all_event_types.items()} if total_events else {}
    mean_impact = statistics.mean(all_impacts) if all_impacts else 0.0
    mean_dynamic_cost = statistics.mean(dynamic_costs) if dynamic_costs else 0.0
    solver_failure_rate = sum(solver_failure_flags) / len(solver_failure_flags) if solver_failure_flags else 0.0
    trigger_rate = sum(1 for i in all_impacts if i >= theta_impact) / len(all_impacts) if all_impacts else 0.0

    return SanityReport(
        sc1_not_too_easy=mean_dynamic_cost > no_event_cost,
        sc2_not_too_hard=solver_failure_rate < 0.50,
        event_type_frequency=frequency,
        mean_impact=mean_impact,
        sc4_impact_reasonable=0.2 <= mean_impact <= 0.8,
        trigger_rate=trigger_rate,
    )
