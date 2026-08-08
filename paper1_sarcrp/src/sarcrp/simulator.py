import random
import time
from dataclasses import dataclass

from sarcrp.ablations import ABLATIONS, replan_with_ablation
from sarcrp.baselines import (
    event_triggered_no_stability, full_reoptimization, mpc_receding_horizon,
    periodic_replan, static_plan,
)
from sarcrp.crp_solver import solve_crp
from sarcrp.event_generator import generate_event_stream
from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, relocation_count, stability_cost
from sarcrp.sarcrp_core import replan
from sarcrp.schemas import Layout, Stack, YardState


@dataclass
class EpisodeMetrics:
    relocation_count_total: int
    changed_actions_total: int
    total_cost_mean: float
    operational_cost_mean: float
    runtime_mean_sec: float
    fallback_rate: float


def _build_state(instance: dict, retrieval_queue: list[str]) -> YardState:
    stacks = [Stack(id=s["id"], containers=list(s["containers"]), max_tier=s["max_tier"]) for s in instance["stacks"]]
    return YardState(
        instance_id=instance["instance_id"], time_step=0,
        layout=Layout(**instance["layout"]), stacks=stacks,
        container_attributes={}, retrieval_queue=retrieval_queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def _plan_changed_count(plan_a, plan_b) -> int:
    by_index_a = {a.step_index: a for a in plan_a.actions}
    by_index_b = {a.step_index: a for a in plan_b.actions}
    indices = set(by_index_a) | set(by_index_b)
    return sum(
        1 for i in indices
        if by_index_a.get(i) is None or by_index_b.get(i) is None
        or by_index_a[i].container != by_index_b[i].container
        or by_index_a[i].dest_stack != by_index_b[i].dest_stack
    )


def run_episode(instance: dict, method_name: str, rng: random.Random, h_f: int | None = None, lam: float | None = None) -> EpisodeMetrics:
    queue = list(instance["initial_retrieval_order"])
    state = _build_state(instance, queue)
    plan = solve_crp(state, queue, time_limit_sec=5.0)

    events = generate_event_stream(queue, instance["t_steps"], instance["uncertainty_level"], rng)

    total_costs = []
    op_costs = []
    runtimes = []
    changed_actions_total = 0
    fallback_count = 0

    for event in events:
        new_queue = event.new_queue
        urgent = [event.affected_containers[0]] if event.type == "URGENT_INSERTION" and event.affected_containers else []
        state.retrieval_queue = new_queue

        replan_kwargs = {}
        if h_f is not None:
            replan_kwargs["h_f"] = h_f
        if lam is not None:
            replan_kwargs["lam"] = lam

        start = time.monotonic()
        if method_name == "static":
            new_plan = static_plan(plan)
            fallback = True
        elif method_name == "full_reopt":
            new_plan = full_reoptimization(state, new_queue, time_limit_sec=5.0)
            fallback = False
        elif method_name == "sarcrp":
            decision = replan(state, plan, queue, new_queue, urgent, rng=rng, conf_new=event.confidence, **replan_kwargs)
            new_plan = decision.plan
            fallback = decision.decision == "KEEP"
        elif method_name == "periodic":
            new_plan = periodic_replan(state, new_queue, plan, event_index=len(total_costs) + 1, time_limit_sec=5.0)
            fallback = new_plan is plan
        elif method_name == "event_triggered_no_stability":
            no_stability_kwargs = {k: v for k, v in replan_kwargs.items() if k == "h_f"}  # lam is fixed at 0 by definition
            decision = event_triggered_no_stability(state, plan, queue, new_queue, urgent, rng, conf_new=event.confidence, **no_stability_kwargs)
            new_plan = decision.plan
            fallback = decision.decision == "KEEP"
        elif method_name == "mpc":
            new_plan = mpc_receding_horizon(state, plan, new_queue, time_limit_sec=5.0)
            fallback = False
        elif method_name.startswith("sarcrp_") and method_name[len("sarcrp_"):] in ABLATIONS:
            ablation_name = method_name[len("sarcrp_"):]
            decision = replan_with_ablation(ablation_name, state, plan, queue, new_queue, urgent, rng, conf_new=event.confidence)
            new_plan = decision.plan
            fallback = decision.decision == "KEEP"
        else:
            raise ValueError(f"unknown method_name: {method_name}")
        runtime = time.monotonic() - start

        changed_actions_total += _plan_changed_count(new_plan, plan)
        if fallback:
            fallback_count += 1

        op = operational_cost(new_plan, urgent, is_valid=True)
        stab, violated = stability_cost(new_plan, plan, frozen_count=0)
        data = data_confidence_cost(new_plan, plan, event.confidence)
        j = compute_objective(op, 0.0 if violated else stab, data)
        total_costs.append(j)
        op_costs.append(op)
        runtimes.append(runtime)

        plan = new_plan
        queue = new_queue

    denom = max(len(events), 1)
    return EpisodeMetrics(
        relocation_count_total=relocation_count(plan),
        changed_actions_total=changed_actions_total,
        total_cost_mean=sum(total_costs) / len(total_costs) if total_costs else 0.0,
        operational_cost_mean=sum(op_costs) / len(op_costs) if op_costs else 0.0,
        runtime_mean_sec=sum(runtimes) / len(runtimes) if runtimes else 0.0,
        fallback_rate=fallback_count / denom if denom else 0.0,
    )
