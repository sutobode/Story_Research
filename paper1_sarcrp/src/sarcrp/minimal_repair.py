from sarcrp.schemas import Plan
from sarcrp.state_ops import find_stack


def minimal_feasibility_repair(plan_old: Plan, state_new, retrieval_queue_new: list[str]) -> Plan:
    """Candidate C1 (spec 14.2): drop actions for containers that no longer exist
    in the retrieval queue or yard; leave everything else untouched. Destination
    re-pointing for now-invalid RELOCATE destinations is handled by
    local_search_repair's N1 operator (Task 10), which runs on this candidate's
    output next."""
    repaired_actions = []
    for action in plan_old.actions:
        if action.type == "RETRIEVE" and action.container not in retrieval_queue_new:
            continue  # obsolete: container no longer needs retrieval
        if action.type == "RELOCATE" and find_stack(state_new, action.container) is None:
            continue  # obsolete: container no longer in the yard
        repaired_actions.append(action)

    for i, action in enumerate(repaired_actions):
        action.step_index = i

    return Plan(plan_id=f"{plan_old.plan_id}_minrepair", created_at=plan_old.created_at,
                source="minimal_feasibility_repair", actions=repaired_actions)
