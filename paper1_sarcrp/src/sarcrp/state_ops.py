from sarcrp.schemas import YardState


def find_stack(state: YardState, container_id: str) -> str | None:
    for stack in state.stacks:
        if container_id in stack.containers:
            return stack.id
    return None


def blocker_count(state: YardState, container_id: str) -> int:
    """Number of containers above `container_id` in its stack (spec 38.2)."""
    for stack in state.stacks:
        if container_id in stack.containers:
            index = stack.containers.index(container_id)
            return len(stack.containers) - index - 1
    return 0


def blocker_pressure(state: YardState, retrieval_queue: list[str], k: int) -> int:
    """Total blocker count over the top-k of `retrieval_queue` (spec 38.3)."""
    top_k = retrieval_queue[:k]
    return sum(blocker_count(state, c) for c in top_k)
