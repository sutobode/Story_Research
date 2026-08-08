import copy

from sarcrp.schemas import Action, Plan, YardState


def _total_containers(state: YardState) -> int:
    return sum(len(s.containers) for s in state.stacks)


def exhaustive_solve(state: YardState, retrieval_queue: list[str], max_containers: int = 8) -> Plan:
    """Branch-and-bound exact solver (spec 21.1): retrieve `retrieval_queue`
    in order with the minimum number of relocations, by trying every legal
    destination for the current target's blockers at each step and pruning
    any branch whose relocation count already reaches the best-known
    solution. Only tractable for small instances -- raises above
    `max_containers` rather than silently taking exponential time."""
    n = _total_containers(state)
    if n > max_containers:
        raise ValueError(f"instance has {n} containers, exceeds max_containers={max_containers}")

    best = {"relocations": None, "actions": None}

    def stack_of(stacks_state: dict[str, list[str]], container: str) -> str | None:
        for sid, containers in stacks_state.items():
            if container in containers:
                return sid
        return None

    def search(stacks_state: dict[str, list[str]], queue: list[str], actions: list[Action], relocations: int, step: int):
        if best["relocations"] is not None and relocations >= best["relocations"]:
            return  # prune: cannot beat the best-known solution from here
        if not queue:
            best["relocations"] = relocations
            best["actions"] = list(actions)
            return

        target = queue[0]
        sid = stack_of(stacks_state, target)
        if sid is None:
            return  # infeasible branch (shouldn't happen with a well-formed instance)

        if stacks_state[sid][-1] == target:
            new_stacks = copy.deepcopy(stacks_state)
            new_stacks[sid].pop()
            new_actions = actions + [Action(
                action_id=f"gt{step:04d}", step_index=step, type="RETRIEVE", container=target,
                source_stack=sid, dest_stack=None, commit_status="planned", planned_time=step,
            )]
            search(new_stacks, queue[1:], new_actions, relocations, step + 1)
            return

        blocker = stacks_state[sid][-1]
        max_tier_by_id = {s.id: s.max_tier for s in state.stacks}
        for dest_sid, dest_containers in stacks_state.items():
            if dest_sid == sid or len(dest_containers) >= max_tier_by_id[dest_sid]:
                continue
            new_stacks = copy.deepcopy(stacks_state)
            new_stacks[sid].pop()
            new_stacks[dest_sid].append(blocker)
            new_actions = actions + [Action(
                action_id=f"gt{step:04d}", step_index=step, type="RELOCATE", container=blocker,
                source_stack=sid, dest_stack=dest_sid, commit_status="planned", planned_time=step,
            )]
            search(new_stacks, queue, new_actions, relocations + 1, step + 1)

    initial_stacks = {s.id: list(s.containers) for s in state.stacks}
    search(initial_stacks, retrieval_queue, [], 0, 0)

    if best["actions"] is None:
        raise ValueError("no feasible solution found -- check retrieval_queue matches the yard's containers")
    return Plan(plan_id="plan_ground_truth", created_at=state.time_step, source="exhaustive_branch_and_bound",
                actions=best["actions"])
