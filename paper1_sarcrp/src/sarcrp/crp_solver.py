import copy
import time

from sarcrp.schemas import Action, Plan, YardState
from sarcrp.state_ops import find_stack


def _is_forbidden(container: str, dest_stack: str, constraints: dict | None) -> bool:
    if not constraints:
        return False
    for move in constraints.get("forbidden_moves", []):
        if move.get("container") == container and move.get("dest_stack") == dest_stack:
            return True
    return False


def _choose_relocation_dest(state: YardState, source_stack_id: str, container: str, constraints: dict | None) -> str | None:
    """Relocate to the emptiest eligible stack (greedy leveling heuristic)."""
    candidates = [
        s for s in state.stacks
        if s.id != source_stack_id
        and len(s.containers) < s.max_tier
        and not _is_forbidden(container, s.id, constraints)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda s: (len(s.containers), s.id)).id


def solve_crp(
    yard_state: YardState,
    retrieval_queue: list[str],
    constraints: dict | None = None,
    time_limit_sec: float | None = None,
) -> Plan:
    """Greedy CRP heuristic: for each target in queue order, relocate any
    blockers above it (to the emptiest legal stack) then retrieve it.
    This is the MVP surrogate for the CRP_RL solver (spec 43) -- see Task 7
    rationale for why a trained solver is not used here."""
    start = time.monotonic()
    state = copy.deepcopy(yard_state)
    actions: list[Action] = []
    step = 0

    for container in retrieval_queue:
        if time_limit_sec is not None and time.monotonic() - start > time_limit_sec:
            break

        stack_id = find_stack(state, container)
        if stack_id is None:
            continue  # container already retrieved or not present

        stack = next(s for s in state.stacks if s.id == stack_id)
        while stack.containers[-1] != container:
            blocker = stack.containers[-1]
            dest = _choose_relocation_dest(state, stack.id, blocker, constraints)
            if dest is None:
                break  # no legal destination; leave blocker in place (marks plan invalid downstream)
            dest_stack = next(s for s in state.stacks if s.id == dest)
            stack.containers.pop()
            dest_stack.containers.append(blocker)
            actions.append(Action(
                action_id=f"a{step:04d}", step_index=step, type="RELOCATE", container=blocker,
                source_stack=stack.id, dest_stack=dest, commit_status="planned", planned_time=step,
            ))
            step += 1

        if stack.containers and stack.containers[-1] == container:
            stack.containers.pop()
            actions.append(Action(
                action_id=f"a{step:04d}", step_index=step, type="RETRIEVE", container=container,
                source_stack=stack.id, dest_stack=None, commit_status="planned", planned_time=step,
            ))
            step += 1

    return Plan(plan_id="plan_greedy", created_at=yard_state.time_step, source="greedy_crp_solver", actions=actions)
