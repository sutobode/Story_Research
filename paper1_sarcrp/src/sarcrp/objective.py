import math

from sarcrp.schemas import Action, Plan

DEFAULT_PENALTIES = {"p_c": 2.0, "p_a": 2.0, "p_d": 1.0, "p_o": 1.0, "p_m": 10.0,
                      "p_f": math.inf, "p_insert": 1.5, "p_delete": 1.5}

BETA_DEFAULT = 0.5  # operational_cost's own beta default, named so the bound below is derivable


def max_delay_driven_gain(beta: float = BETA_DEFAULT, plan_length: int | None = None,
                           normalize_delay: bool = True) -> float:
    """The exact upper bound on the operational gain any repair can obtain
    by expediting urgent containers alone -- the quantity behind this
    project's two proven "dead zones" (tests/test_objective_dead_zones.py).

    RetrievalDelayNorm is normalized into [0, 1] (its denominator is
    len(urgent) * (len(plan) + 1)), so beta * RetrievalDelayNorm is bounded
    by beta REGARDLESS of instance size. With plan_length given, the bound
    is tighter and exact: moving a single urgent container from the last
    plan position to the first changes the normalized delay by
    (L - 1) / (L + 1), so the achievable gain is beta * (L - 1) / (L + 1),
    which approaches beta from below as L grows.

    Two consequences, both provable rather than empirical:
      * DZ1: one relocation costs alpha (=1.0 by default) > beta, so
        expediting an urgent container can never pay for even one extra
        relocation, at any scale.
      * DZ2: a purely relative switching margin tau = tau_frac * J_old
        grows with instance size while this bound does not, so beyond
        J_old = beta / tau_frac no delay-driven repair can ever clear the
        margin. See derive_tau_abs for the fix.

    With normalize_delay=False (retrieval_delay_actions, the DZ1 fix) the
    bound instead GROWS with the plan: moving a single urgent container
    from the last position to the first saves (L-1) actions of waiting, so
    the achievable gain is beta * (L-1) -- unbounded in L, hence able to
    pay for relocations once the instance is large enough. That removes
    DZ1's scale-independent ceiling entirely."""
    if plan_length is None:
        return beta if normalize_delay else float("inf")
    if plan_length <= 1:
        return 0.0
    if not normalize_delay:
        return beta * (plan_length - 1)
    return beta * (plan_length - 1) / (plan_length + 1)


def derive_tau_abs(kappa: float = 0.5, beta: float = BETA_DEFAULT) -> float:
    """Derives the absolute ceiling for the mixed relative-absolute
    switching margin (sarcrp_core.replan's tau_abs) FROM the objective's own
    achievable-gain bound, rather than fixing it as a free constant.

    The margin's job is hysteresis: reject switches whose benefit is
    trivial *relative to what is achievable at all*. Since the maximum
    achievable delay-driven gain is exactly beta (see
    max_delay_driven_gain), requiring a repair to capture at least a
    fraction kappa of it gives tau_abs = kappa * beta. kappa=0.5 ("capture
    at least half the achievable benefit") is the default.

    This is a derivation, not a tuned value: the empirical result it
    produces is insensitive to kappa over the whole range tested
    (kappa in {0.25, 0.5, 0.75} all give an identical 19/20 update rate on
    the 50-container instance where the purely relative margin gives
    0/20), because ANY ceiling below the achievable gain unblocks the
    decision equally. What fails is the unbounded relative FORM of the
    margin, not a particular constant."""
    if not 0.0 < kappa < 1.0:
        raise ValueError(f"kappa must be in (0, 1), got {kappa!r}")
    return kappa * beta


def relocation_count(plan: Plan) -> int:
    return sum(1 for a in plan.actions if a.type == "RELOCATE")


def retrieval_delay_norm(plan: Plan, urgent_containers: list[str]) -> float:
    """RetrievalDelayNorm(P) (spec 11.2 / 45.2). Dimensionless, in [0, 1]."""
    if not urgent_containers:
        return 0.0
    positions = {a.container: i for i, a in enumerate(plan.actions)}
    total = sum(positions.get(c, len(plan.actions) + 1) for c in urgent_containers)
    denom = len(urgent_containers) * (len(plan.actions) + 1)
    return total / denom if denom else 0.0


def retrieval_delay_actions(plan: Plan, urgent_containers: list[str]) -> float:
    """DZ1 fix: the same delay measured in CRANE ACTIONS instead of as a
    dimensionless [0,1] fraction.

    The dead zone DZ1 (tests/test_objective_dead_zones.py) is a dimensional
    inconsistency, not a badly chosen weight: C_op adds alpha*R(P), a COUNT
    of crane actions, to beta*RetrievalDelayNorm(P), a dimensionless RATIO.
    Because the ratio is capped at 1, the delay term's whole contribution is
    capped at beta however large the instance is -- so it can never pay for
    even one relocation (alpha=1.0 > beta=0.5), at any scale.

    Measuring delay in the same unit as relocations removes that
    inconsistency: an urgent container sitting at plan position p means its
    truck waits p crane actions, and one relocation adds one action. beta
    then has a real interpretation -- the cost of one action of urgent-truck
    waiting, relative to alpha, the cost of one relocation -- i.e. the
    terminal's own service-level-vs-throughput tradeoff, a policy choice
    this project characterizes rather than prescribes (no operational
    calibration data is claimed here)."""
    if not urgent_containers:
        return 0.0
    positions = {a.container: i for i, a in enumerate(plan.actions)}
    total = sum(positions.get(c, len(plan.actions) + 1) for c in urgent_containers)
    return total / len(urgent_containers)


def operational_cost(
    plan: Plan,
    urgent_containers: list[str],
    is_valid: bool,
    alpha: float = 1.0,
    beta: float = 0.5,
    gamma: float = 1.0,
    m_inf: float = 1e6,
    normalize_delay: bool = True,
) -> float:
    """C_op(P) = alpha*R(P) + beta*RetrievalDelay(P) + gamma*InvalidPenalty(P) (spec 11, 45.1).

    normalize_delay=True (the default) uses spec's dimensionless
    RetrievalDelayNorm and reproduces every previously reported number
    exactly. normalize_delay=False uses retrieval_delay_actions instead --
    the DZ1 fix, delay in crane actions, commensurate with alpha*R(P)."""
    invalid_penalty = 0.0 if is_valid else m_inf
    delay = (retrieval_delay_norm(plan, urgent_containers) if normalize_delay
             else retrieval_delay_actions(plan, urgent_containers))
    return (
        alpha * relocation_count(plan)
        + beta * delay
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
