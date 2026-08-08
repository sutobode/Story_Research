import random
import time
from dataclasses import dataclass

from sarcrp.baselines import full_reoptimization, static_plan
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


def run_episode(instance: dict, method_name: str, rng: random.Random) -> EpisodeMetrics:
    queue = list(instance["initial_retrieval_order"])
    state = _build_state(instance, queue)
    plan = solve_crp(state, queue, time_limit_sec=5.0)

    events = generate_event_stream(queue, instance["t_steps"], instance["uncertainty_level"], rng)

    total_costs = []
    op_costs = []
    runtimes = []
    changed_actions_total = 0
    fallback_count = 0
    replan_opportunities = 0

    for event in events:
        new_queue = event.new_queue
        urgent = [event.affected_containers[0]] if event.type == "URGENT_INSERTION" and event.affected_containers else []
        state.retrieval_queue = new_queue

        start = time.monotonic()
        if method_name == "static":
            new_plan = static_plan(plan)
            fallback = True
        elif method_name == "full_reopt":
            new_plan = full_reoptimization(state, new_queue, time_limit_sec=5.0)
            fallback = False
        elif method_name == "sarcrp":
            replan_opportunities += 1
            decision = replan(state, plan, queue, new_queue, urgent, rng=rng, conf_new=event.confidence)
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

    denom = replan_opportunities if method_name == "sarcrp" else max(len(events), 1)
    return EpisodeMetrics(
        relocation_count_total=relocation_count(plan),
        changed_actions_total=changed_actions_total,
        total_cost_mean=sum(total_costs) / len(total_costs) if total_costs else 0.0,
        operational_cost_mean=sum(op_costs) / len(op_costs) if op_costs else 0.0,
        runtime_mean_sec=sum(runtimes) / len(runtimes) if runtimes else 0.0,
        fallback_rate=fallback_count / denom if denom else 0.0,
    )
