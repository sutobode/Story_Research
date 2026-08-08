import copy
import random
import time

from sarcrp.crp_solver import choose_relocation_dest, solve_crp
from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, stability_cost
from sarcrp.schemas import Action, Plan
from sarcrp.state_ops import find_stack


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


def _neighbor_insert_urgent_support(
    plan: Plan, state, frozen_count: int, urgent_containers: list[str], rng: random.Random
) -> Plan | None:
    """N3 (spec 15.1/46.2): insert a relocation that unblocks an urgent target,
    placed at the earliest non-frozen slot so the target becomes reachable sooner."""
    if not urgent_containers:
        return None
    container = rng.choice(urgent_containers)
    stack_id = find_stack(state, container)
    if stack_id is None:
        return None
    stack = next(s for s in state.stacks if s.id == stack_id)
    if not stack.containers or stack.containers[-1] == container:
        return None  # already on top -- nothing to unblock
    blocker = stack.containers[-1]
    dest = choose_relocation_dest(state, stack.id, blocker, None)
    if dest is None:
        return None
    new_action = Action(
        action_id=f"n3_{rng.randint(0, 999999)}", step_index=0, type="RELOCATE",
        container=blocker, source_stack=stack.id, dest_stack=dest,
        commit_status="planned", planned_time=0,
    )
    new_actions = [copy.deepcopy(a) for a in plan.actions]
    new_actions.insert(frozen_count, new_action)
    for i, a in enumerate(new_actions):
        a.step_index = i
    return Plan(plan_id=plan.plan_id, created_at=plan.created_at, source=plan.source, actions=new_actions)


def _neighbor_remove_obsolete(plan: Plan, frozen_count: int, rng: random.Random) -> Plan | None:
    """N4: drop one non-frozen action (models "remove no-longer-needed relocation").
    Kept actions are deep-copied before renumbering, same reason as
    minimal_repair.py: mutating shared Action objects in place risks
    corrupting whatever other plan still holds a reference to them."""
    non_frozen = [i for i in range(len(plan.actions)) if i >= frozen_count]
    if not non_frozen:
        return None
    idx = rng.choice(non_frozen)
    new_actions = [copy.deepcopy(a) for i, a in enumerate(plan.actions) if i != idx]
    for k, a in enumerate(new_actions):
        a.step_index = k
    return Plan(plan_id=plan.plan_id, created_at=plan.created_at, source=plan.source, actions=new_actions)


def _neighbor_replace_tail_with_solver(
    plan: Plan, state, retrieval_queue_new: list[str], frozen_count: int, rng: random.Random
) -> Plan | None:
    """N5 (spec 15.1/46.2): keep a k-length prefix (k >= frozen_count), replace
    the rest with the CRP solver's suggestion for the current retrieval queue."""
    if len(plan.actions) <= frozen_count:
        return None
    k = rng.randint(frozen_count, len(plan.actions))
    prefix = [copy.deepcopy(a) for a in plan.actions[:k]]
    tail_solution = solve_crp(state, retrieval_queue_new, time_limit_sec=1.0)
    new_actions = prefix + list(tail_solution.actions)
    for i, a in enumerate(new_actions):
        a.step_index = i
    return Plan(plan_id=plan.plan_id, created_at=plan.created_at, source=plan.source, actions=new_actions)


NEIGHBORHOOD_OP_NAMES = ("N1", "N2", "N3", "N4", "N5")


def _sample_neighbor(
    plan: Plan,
    state,
    frozen_count: int,
    urgent_containers: list[str],
    retrieval_queue_new: list[str],
    rng: random.Random,
) -> Plan | None:
    op_name = rng.choice(NEIGHBORHOOD_OP_NAMES)
    if op_name == "N1":
        return _neighbor_change_destination(plan, state, frozen_count, rng)
    if op_name == "N2":
        return _neighbor_swap_actions(plan, frozen_count, rng)
    if op_name == "N3":
        return _neighbor_insert_urgent_support(plan, state, frozen_count, urgent_containers, rng)
    if op_name == "N4":
        return _neighbor_remove_obsolete(plan, frozen_count, rng)
    return _neighbor_replace_tail_with_solver(plan, state, retrieval_queue_new, frozen_count, rng)


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
    """Stochastic hill climbing over N1-N5 (spec 15.2/46.3)."""
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
            candidate = _sample_neighbor(p_best, state, frozen_count, urgent, retrieval_queue_new, rng)
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
