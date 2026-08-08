import copy
import random
import time

from sarcrp.crp_solver import choose_relocation_dest, solve_crp
from sarcrp.freeze_horizon import apply_frozen_prefix
from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, stability_cost
from sarcrp.plan_validator import is_plan_valid
from sarcrp.schemas import Action, Plan, Stack, YardState
from sarcrp.state_ops import find_stack


def _score(plan: Plan, p_old: Plan, frozen_count: int, urgent_containers: list[str], conf_new: float, state) -> float:
    """`is_valid` was hardcoded True here unconditionally until this fix, so
    a candidate that replays illegally could look artificially cheap and
    win the hill-climbing walk instead of being excluded (spec 11.3's
    M_inf penalty)."""
    is_valid = is_plan_valid(plan, state)
    op = operational_cost(plan, urgent_containers, is_valid=is_valid)
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
    the rest with the CRP solver's suggestion for the current retrieval queue.

    The tail must be solved against the state that results *after* the
    kept prefix's own actions, not the original state -- solving fresh
    against the untouched state and full queue (the same bug class found
    in baselines.mpc_receding_horizon and sarcrp_core.replan's candidate
    C3) makes the tail duplicate retrievals/relocations the prefix
    already covers."""
    if len(plan.actions) <= frozen_count:
        return None
    k = rng.randint(frozen_count, len(plan.actions))
    prefix = [copy.deepcopy(a) for a in plan.actions[:k]]
    kept_prefix_plan = Plan(plan_id="n5_prefix", created_at=0, source="n5", actions=plan.actions[:k])
    shadow_state, remaining_queue = apply_frozen_prefix(state, kept_prefix_plan, retrieval_queue_new)
    tail_solution = solve_crp(shadow_state, remaining_queue, time_limit_sec=1.0)
    new_actions = prefix + list(tail_solution.actions)
    for i, a in enumerate(new_actions):
        a.step_index = i
    return Plan(plan_id=plan.plan_id, created_at=plan.created_at, source=plan.source, actions=new_actions)


def _neighbor_prioritize_urgent_containers(
    plan: Plan, state, frozen_count: int, urgent_containers: list[str], rng: random.Random,
) -> Plan | None:
    """N6 -- an addition beyond spec 15.1's original N1-N5, added after
    finding a real coverage gap. N3 only unblocks ONE random urgent
    container per sample and never reorders its own RETRIEVE action, so it
    cannot by itself realize a retrieval-delay improvement. N5 (and
    sarcrp_core's candidate C3) replace the ENTIRE tail with a fresh solve
    on a reordered queue -- but if the urgent container(s) are already
    first in that queue (the common case: the event that made them urgent
    already put them there), this reduces to exactly the same full
    reshuffle N5/C3 already try, paying stability cost for changes
    unrelated to the urgent fix even when only one container's priority
    actually needs to move. Neither reliably discovers "move the urgent
    container(s) to the front, change nothing else": local search's random
    N1-N5 sampling found an equivalent fix by chance for one urgent
    container on one instance and never for two, across 100 iterations x
    50 neighbors.

    This operator constructs that minimal move directly (no solver call):
    for each urgent container not already on top of its stack, relocate
    its blockers just enough to expose it, then retrieve it -- inserted
    right after the frozen prefix. Every other action from the original
    tail is kept, in its original relative order, EXCEPT that any kept
    action referencing a container we relocated as a blocker has its
    source_stack patched to that container's new location (it wasn't
    retrieved, just moved out of the way, so it must still be retrieved
    later, from wherever it actually ended up)."""
    if not urgent_containers:
        return None
    prefix_plan = Plan(plan_id="n6_prefix", created_at=0, source="n6", actions=plan.actions[:frozen_count])
    shadow_state, _ = apply_frozen_prefix(state, prefix_plan, [])
    shadow_stacks = {s.id: list(s.containers) for s in shadow_state.stacks}
    max_tiers = {s.id: s.max_tier for s in shadow_state.stacks}

    def _current_shadow_state():
        return YardState(
            instance_id=shadow_state.instance_id, time_step=shadow_state.time_step, layout=shadow_state.layout,
            stacks=[Stack(id=sid, containers=list(c), max_tier=max_tiers[sid]) for sid, c in shadow_stacks.items()],
            container_attributes=shadow_state.container_attributes, retrieval_queue=shadow_state.retrieval_queue,
            pickup_prob=shadow_state.pickup_prob, data_timestamp=shadow_state.data_timestamp,
            state_confidence=shadow_state.state_confidence,
        )

    new_leading_actions: list[Action] = []
    retrieved: set[str] = set()
    relocated_to: dict[str, str] = {}

    for container in urgent_containers:
        if container in retrieved:
            continue
        stack_id = next((sid for sid, containers in shadow_stacks.items() if container in containers), None)
        if stack_id is None:
            continue  # not physically present in the shadow state (e.g. already covered by the frozen prefix)
        stack = shadow_stacks[stack_id]
        while stack and stack[-1] != container:
            blocker = stack[-1]
            dest = choose_relocation_dest(_current_shadow_state(), stack_id, blocker, None)
            if dest is None:
                return None  # no legal destination -- bail rather than produce an invalid candidate
            stack.pop()
            shadow_stacks[dest].append(blocker)
            relocated_to[blocker] = dest
            new_leading_actions.append(Action(
                action_id=f"n6_{rng.randint(0, 999999)}", step_index=0, type="RELOCATE",
                container=blocker, source_stack=stack_id, dest_stack=dest,
                commit_status="planned", planned_time=0,
            ))
        if stack and stack[-1] == container:
            stack.pop()
            new_leading_actions.append(Action(
                action_id=f"n6_{rng.randint(0, 999999)}", step_index=0, type="RETRIEVE",
                container=container, source_stack=stack_id, dest_stack=None,
                commit_status="planned", planned_time=0,
            ))
            retrieved.add(container)

    if not new_leading_actions:
        return None

    kept_tail: list[Action] = []
    for a in plan.actions[frozen_count:]:
        if a.container in retrieved:
            continue  # now retrieved early by the block above -- drop the old (later) retrieval
        a_copy = copy.deepcopy(a)
        if a.container in relocated_to:
            a_copy.source_stack = relocated_to[a.container]  # it moved -- kept action must reference its new stack
        kept_tail.append(a_copy)

    prefix = [copy.deepcopy(a) for a in plan.actions[:frozen_count]]
    new_actions = prefix + new_leading_actions + kept_tail
    for i, a in enumerate(new_actions):
        a.step_index = i
    return Plan(plan_id=plan.plan_id, created_at=plan.created_at, source=plan.source, actions=new_actions)


NEIGHBORHOOD_OP_NAMES = ("N1", "N2", "N3", "N4", "N5", "N6")


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
    if op_name == "N5":
        return _neighbor_replace_tail_with_solver(plan, state, retrieval_queue_new, frozen_count, rng)
    return _neighbor_prioritize_urgent_containers(plan, state, frozen_count, urgent_containers, rng)


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
    """Stochastic hill climbing over N1-N5 (spec 15.2/46.3).

    `current`/`score_current` is the exploratory walk state -- the
    epsilon-greedy acceptance criterion deliberately lets it get WORSE
    sometimes, to escape local optima. `best`/`score_best` tracks the
    best plan seen at any point during the walk and is what gets
    returned: conflating the two (returning wherever the walk happened to
    end up) let a walk that wandered off via an epsilon-accept and never
    found its way back by t_iters return something strictly worse than
    p_start itself -- a real bug caught building Paper 1's
    existence-proof scenario (every prior unit test in this file always
    passed epsilon=0.0, which never exercises the accept-worse branch at
    all, so this never surfaced before)."""
    urgent = urgent_containers or []
    start_time = time.monotonic()
    current = p_start
    score_current = _score(current, p_old, frozen_count, urgent, conf_new, state)
    best, score_best = current, score_current
    stale_iterations = 0

    for _ in range(t_iters):
        if time_limit_sec is not None and time.monotonic() - start_time > time_limit_sec:
            break

        neighbors = []
        for _ in range(m_neighbors):
            candidate = _sample_neighbor(current, state, frozen_count, urgent, retrieval_queue_new, rng)
            if candidate is not None:
                neighbors.append(candidate)

        if not neighbors:
            stale_iterations += 1
            if stale_iterations >= 10:
                break
            continue
        stale_iterations = 0

        scored = [(_score(n, p_old, frozen_count, urgent, conf_new, state), n) for n in neighbors]
        candidate_score, candidate_plan = min(scored, key=lambda pair: pair[0])

        if candidate_score < score_current:
            current, score_current = candidate_plan, candidate_score
        elif rng.random() < epsilon:
            current, score_current = candidate_plan, candidate_score

        if score_current < score_best:
            best, score_best = current, score_current

    return best
