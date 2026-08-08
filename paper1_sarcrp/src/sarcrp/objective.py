import math

from sarcrp.schemas import Action, Plan

DEFAULT_PENALTIES = {"p_c": 2.0, "p_a": 2.0, "p_d": 1.0, "p_o": 1.0, "p_m": 10.0,
                      "p_f": math.inf, "p_insert": 1.5, "p_delete": 1.5}


def relocation_count(plan: Plan) -> int:
    return sum(1 for a in plan.actions if a.type == "RELOCATE")


def retrieval_delay_norm(plan: Plan, urgent_containers: list[str]) -> float:
    """RetrievalDelayNorm(P) (spec 11.2 / 45.2)."""
    if not urgent_containers:
        return 0.0
    positions = {a.container: i for i, a in enumerate(plan.actions)}
    total = sum(positions.get(c, len(plan.actions) + 1) for c in urgent_containers)
    denom = len(urgent_containers) * (len(plan.actions) + 1)
    return total / denom if denom else 0.0


def operational_cost(
    plan: Plan,
    urgent_containers: list[str],
    is_valid: bool,
    alpha: float = 1.0,
    beta: float = 0.5,
    gamma: float = 1.0,
    m_inf: float = 1e6,
) -> float:
    """C_op(P) = alpha*R(P) + beta*RetrievalDelay(P) + gamma*InvalidPenalty(P) (spec 11, 45.1)."""
    invalid_penalty = 0.0 if is_valid else m_inf
    return (
        alpha * relocation_count(plan)
        + beta * retrieval_delay_norm(plan, urgent_containers)
        + gamma * invalid_penalty
    )


def _action_distance(
    action_new: Action | None,
    action_old: Action | None,
    is_frozen_index: bool,
    penalties: dict,
) -> float:
    if action_new is None or action_old is None:
        return penalties["p_insert"] if action_new is not None else penalties["p_delete"]

    changed_container = action_new.container != action_old.container
    changed_type = action_new.type != action_old.type
    changed_dest = action_new.dest_stack != action_old.dest_stack

    d = 0.0
    if changed_container:
        d += penalties["p_c"]
    if changed_type:
        d += penalties["p_a"]
    if changed_dest:
        d += penalties["p_d"]

    any_changed = changed_container or changed_type or changed_dest
    if is_frozen_index and any_changed:
        return penalties["p_f"]  # frozen violation -> infinite (spec 10.2, 12.2)
    if action_old.commit_status == "committed" and any_changed:
        d += penalties["p_m"]
    return d


def stability_cost(
    plan_new: Plan,
    plan_old: Plan,
    frozen_count: int,
    rho: float = 0.05,
    penalties: dict | None = None,
) -> tuple[float, bool]:
    """D(P, P_old) = sum_i exp(-rho*i) * d_i, plus a frozen-violation flag (spec 12, 45.3)."""
    pen = penalties or DEFAULT_PENALTIES
    new_by_index = {a.step_index: a for a in plan_new.actions}
    old_by_index = {a.step_index: a for a in plan_old.actions}
    max_len = max(len(plan_new.actions), len(plan_old.actions))

    total = 0.0
    frozen_violation = False

    for i in range(max_len):
        a_new = new_by_index.get(i)
        a_old = old_by_index.get(i)
        is_frozen_index = i < frozen_count
        d_i = _action_distance(a_new, a_old, is_frozen_index, pen)

        if math.isinf(d_i):
            frozen_violation = True

        weight = math.exp(-rho * i)
        total += weight * d_i if not math.isinf(d_i) else d_i  # keep inf visible, don't multiply inf*weight->nan-safe
    return total, frozen_violation


def data_confidence_cost(plan_new: Plan, plan_old: Plan, conf_new: float) -> float:
    """C_data(P) = Changes(P, P_old) * (1 - Conf(I_new))  (spec 13, 45.4, simple form)."""
    old_by_index = {a.step_index: a for a in plan_old.actions}
    new_by_index = {a.step_index: a for a in plan_new.actions}
    all_indices = set(old_by_index) | set(new_by_index)
    changes = sum(
        1 for i in all_indices
        if old_by_index.get(i) is None
        or new_by_index.get(i) is None
        or old_by_index[i].container != new_by_index[i].container
        or old_by_index[i].dest_stack != new_by_index[i].dest_stack
    )
    return changes * (1.0 - conf_new)


def compute_objective(op_cost: float, stab_cost: float, data_cost: float, lam: float = 1.0, mu: float = 0.5) -> float:
    """J(P) = C_op(P) + lambda*D(P,P_old) + mu*C_data(P)  (spec 4.3, 45)."""
    return op_cost + lam * stab_cost + mu * data_cost
