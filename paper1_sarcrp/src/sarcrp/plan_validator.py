from sarcrp.schemas import Plan, YardState


def is_plan_valid(plan: Plan, state: YardState) -> bool:
    """Replays `plan`'s actions against a shadow copy of `state`'s stacks,
    checking each action is legal: RETRIEVE must target the current top of
    its source stack; RELOCATE must move the current top of its source
    stack into a destination that still has room. Spec 11.3's
    InvalidPenalty(P)/M_inf is otherwise dead code -- every call site in
    this codebase has passed is_valid=True unconditionally since Task 6,
    so the M_inf branch has never actually been exercised."""
    stacks = {s.id: list(s.containers) for s in state.stacks}
    max_tiers = {s.id: s.max_tier for s in state.stacks}

    for action in sorted(plan.actions, key=lambda a: a.step_index):
        if action.type == "RETRIEVE":
            stack = stacks.get(action.source_stack)
            if not stack or stack[-1] != action.container:
                return False
            stack.pop()
        elif action.type == "RELOCATE":
            source = stacks.get(action.source_stack)
            dest = stacks.get(action.dest_stack)
            if source is None or dest is None or not source or source[-1] != action.container:
                return False
            if len(dest) >= max_tiers.get(action.dest_stack, 0):
                return False
            source.pop()
            dest.append(action.container)
    return True
