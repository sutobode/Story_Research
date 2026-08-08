from sarcrp.schemas import Plan


def split_plan(plan: Plan, h_f: int) -> tuple[Plan, Plan]:
    """Freeze-by-action-count (spec 10.1): first h_f actions are frozen, rest is the
    repairable tail."""
    frozen_actions = plan.actions[:h_f]
    tail_actions = plan.actions[h_f:]
    frozen = Plan(plan_id=f"{plan.plan_id}_frozen", created_at=plan.created_at, source=plan.source, actions=frozen_actions)
    tail = Plan(plan_id=f"{plan.plan_id}_tail", created_at=plan.created_at, source=plan.source, actions=tail_actions)
    return frozen, tail
