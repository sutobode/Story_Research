import copy
import random
import time

from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, stability_cost
from sarcrp.schemas import Plan


def _score(plan: Plan, p_old: Plan, frozen_count: int, urgent_containers: list[str], conf_new: float) -> float:
    op = operational_cost(plan, urgent_containers, is_valid=True)
    stab, violated = stability_cost(plan, p_old, frozen_count)
    if violated:
        return float("inf")
    data = data_confidence_cost(plan, p_old, conf_new)
    return compute_objective(op, stab, data)


def _neighbor_change_destination(plan: Plan, state, frozen_count: int, rng: random.Random) -> Plan | None:
    """N1 (spec 15.1/46.2): change one non-frozen RELOCATE action's destination."""
    candidates = [i for i, a in enumerate(plan.actions) if i >= frozen_count and a.type == "RELOCATE"]
    if not candidates:
        return None
    idx = rng.choice(candidates)
    other_stacks = [s.id for s in state.stacks if s.id != plan.actions[idx].source_stack]
    if not other_stacks:
        return None
    new_plan = copy.deepcopy(plan)
    new_plan.actions[idx].dest_stack = rng.choice(other_stacks)
    return new_plan


def _neighbor_swap_actions(plan: Plan, frozen_count: int, rng: random.Random) -> Plan | None:
    """N2: swap two non-frozen actions."""
    non_frozen = [i for i in range(len(plan.actions)) if i >= frozen_count]
    if len(non_frozen) < 2:
        return None
    i, j = rng.sample(non_frozen, 2)
    new_plan = copy.deepcopy(plan)
    new_plan.actions[i], new_plan.actions[j] = new_plan.actions[j], new_plan.actions[i]
    for k, a in enumerate(new_plan.actions):
        a.step_index = k
    return new_plan


def _neighbor_remove_obsolete(plan: Plan, frozen_count: int, rng: random.Random) -> Plan | None:
    """N4: drop one non-frozen action (models "remove no-longer-needed relocation")."""
    non_frozen = [i for i in range(len(plan.actions)) if i >= frozen_count]
    if not non_frozen:
        return None
    idx = rng.choice(non_frozen)
    new_actions = [a for i, a in enumerate(plan.actions) if i != idx]
    for k, a in enumerate(new_actions):
        a.step_index = k
    return Plan(plan_id=plan.plan_id, created_at=plan.created_at, source=plan.source, actions=new_actions)


NEIGHBORHOOD_OPS = [_neighbor_change_destination, _neighbor_swap_actions, _neighbor_remove_obsolete]


def local_search_repair(
    p_start: Plan,
    p_old: Plan,
    state,
    retrieval_queue_new: list[str],
    frozen_count: int,
    rng: random.Random,
    t_iters: int = 100,
    m_neighbors: int = 50,
    epsilon: float = 0.05,
    time_limit_sec: float | None = None,
    urgent_containers: list[str] | None = None,
    conf_new: float = 1.0,
) -> Plan:
    """Stochastic hill climbing over N1/N2/N4 (spec 15.2/46.3). N3/N5 need the
    CRP solver / urgent-insertion context and are deferred to a follow-up plan
    once the MVP decision gate (spec 33) passes."""
    urgent = urgent_containers or []
    start_time = time.monotonic()
    p_best = p_start
    score_best = _score(p_best, p_old, frozen_count, urgent, conf_new)
    stale_iterations = 0

    for _ in range(t_iters):
        if time_limit_sec is not None and time.monotonic() - start_time > time_limit_sec:
            break

        neighbors = []
        for _ in range(m_neighbors):
            op = rng.choice(NEIGHBORHOOD_OPS)
            if op is _neighbor_change_destination:
                candidate = op(p_best, state, frozen_count, rng)
            else:
                candidate = op(p_best, frozen_count, rng)
            if candidate is not None:
                neighbors.append(candidate)

        if not neighbors:
            stale_iterations += 1
            if stale_iterations >= 10:
                break
            continue
        stale_iterations = 0

        scored = [(_score(n, p_old, frozen_count, urgent, conf_new), n) for n in neighbors]
        candidate_score, candidate_plan = min(scored, key=lambda pair: pair[0])

        if candidate_score < score_best:
            p_best, score_best = candidate_plan, candidate_score
        elif rng.random() < epsilon:
            p_best, score_best = candidate_plan, candidate_score

    return p_best
