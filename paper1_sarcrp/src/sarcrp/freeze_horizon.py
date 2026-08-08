import copy

from sarcrp.schemas import Plan, Stack, YardState


def split_plan(plan: Plan, h_f: int) -> tuple[Plan, Plan]:
    """Freeze-by-action-count (spec 10.1): first h_f actions are frozen, rest is the
    repairable tail."""
    frozen_actions = plan.actions[:h_f]
    tail_actions = plan.actions[h_f:]
    frozen = Plan(plan_id=f"{plan.plan_id}_frozen", created_at=plan.created_at, source=plan.source, actions=frozen_actions)
    tail = Plan(plan_id=f"{plan.plan_id}_tail", created_at=plan.created_at, source=plan.source, actions=tail_actions)
    return frozen, tail


def apply_frozen_prefix(state: YardState, frozen: Plan, retrieval_queue_new: list[str]) -> tuple[YardState, list[str]]:
    """Shadow-applies `frozen`'s own actions to a copy of `state`'s stacks,
    returning the resulting physical state and `retrieval_queue_new` with
    already-retrieved containers dropped -- so a tail solved against this
    result doesn't re-plan moves the frozen prefix already made.

    This exact bug was found twice independently in this codebase: both
    baselines.mpc_receding_horizon and sarcrp_core.replan's candidate C3
    used to solve their tail against the ORIGINAL, untouched state/queue,
    making the tail's fresh solve re-plan (or straight-up duplicate)
    moves the frozen prefix already covered."""
    frozen_actions = copy.deepcopy(frozen.actions)
    shadow_stacks = {s.id: list(s.containers) for s in state.stacks}
    retrieved = set()
    for a in frozen_actions:
        stack = shadow_stacks.get(a.source_stack)
        if not stack or stack[-1] != a.container:
            continue  # frozen action no longer applicable to the actual stack -- leave shadow state as-is
        stack.pop()
        if a.type == "RETRIEVE":
            retrieved.add(a.container)
        elif a.type == "RELOCATE":
            shadow_stacks[a.dest_stack].append(a.container)

    shadow_state = YardState(
        instance_id=state.instance_id, time_step=state.time_step, layout=state.layout,
        stacks=[Stack(id=s.id, containers=shadow_stacks[s.id], max_tier=s.max_tier) for s in state.stacks],
        container_attributes=state.container_attributes, retrieval_queue=retrieval_queue_new,
        pickup_prob=state.pickup_prob, data_timestamp=state.data_timestamp, state_confidence=state.state_confidence,
    )
    remaining_queue = [c for c in retrieval_queue_new if c not in retrieved]
    return shadow_state, remaining_queue
