import math
from dataclasses import dataclass

from sarcrp.schemas import Action, Plan, YardState
from sarcrp.state_ops import blocker_count

DEFAULT_WEIGHTS = {"w_o": 0.25, "w_t": 0.20, "w_b": 0.25, "w_p": 0.20, "w_c": 0.10}


@dataclass
class ImpactBreakdown:
    i_order: float
    i_target: float
    i_blocking: float
    i_plan: float
    i_conf: float
    total: float


def _kendall_tau_topk(old_queue: list[str], new_queue: list[str], k: int) -> float:
    """I_order: normalized Kendall-tau distance over top-k union (spec 8.2)."""
    old_top = old_queue[:k]
    new_top = new_queue[:k]
    items = sorted(set(old_top) | set(new_top))
    n = len(items)
    if n < 2:
        return 0.0

    def rank_in(seq: list[str], item: str) -> int:
        return seq.index(item) if item in seq else k + 1

    old_rank = {c: rank_in(old_top, c) for c in items}
    new_rank = {c: rank_in(new_top, c) for c in items}

    discordant = 0
    total_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = items[i], items[j]
            total_pairs += 1
            old_order = old_rank[a] - old_rank[b]
            new_order = new_rank[a] - new_rank[b]
            if (old_order > 0) != (new_order > 0) and old_order != 0 and new_order != 0:
                discordant += 1
            elif (old_order == 0) != (new_order == 0):
                discordant += 1
    return discordant / total_pairs if total_pairs else 0.0


def _target_impact(old_queue: list[str], new_queue: list[str]) -> float:
    """I_target: binary indicator that the current retrieval target changed (spec 8.3)."""
    old_target = old_queue[0] if old_queue else None
    new_target = new_queue[0] if new_queue else None
    return 1.0 if old_target != new_target else 0.0


def _blocking_impact(
    state_old: YardState, state_new: YardState, old_queue: list[str], new_queue: list[str],
    k: int, sigma_b: float,
) -> float:
    """I_blocking: saturated mean absolute blocker-count change over
    union(old_queue[:k], new_queue[:k]) (spec 8.4/44.3's own pseudocode --
    the union, not new_queue's top-k alone, so a container that drops out
    of the near-term window but whose physical blocker count still changed
    is not silently missed).

    NOTE: every call site in this codebase (sarcrp_core.replan,
    sanity_checks.run_sanity_checks) currently passes the SAME state
    object for both state_old and state_new, because Paper 1's simulator
    never executes an action's physical effect onto state.stacks between
    two impact estimations (commit_status never transitions to
    "committed" anywhere in src/ -- see test_impact_estimator.py's
    test_blocking_impact_is_zero_when_physical_state_is_unchanged). This
    term is therefore always 0.0 in every experiment this suite has run;
    giving it genuine signal needs a physical-execution model, which is
    explicitly Paper 2's scope ("imperfect execution"), not Paper 1's."""
    items = sorted(set(old_queue[:k]) | set(new_queue[:k]))
    if not items:
        return 0.0
    diffs = [abs(blocker_count(state_new, c) - blocker_count(state_old, c)) for c in items]
    mean_delta = sum(diffs) / len(items)
    return 1.0 - math.exp(-mean_delta / sigma_b)


def is_action_affected(
    action: Action,
    old_queue: list[str],
    new_queue: list[str],
    state_new: YardState,
    r_shift: int = 5,
) -> bool:
    """A1/A2 affected-action rules from spec 8.5 / 44.4 (A3-A5 need full candidate
    plans and are checked later inside minimal_repair/local_search, not here)."""
    container = action.container
    if container not in new_queue:
        return True  # A1: removed/cancelled
    old_rank = old_queue.index(container) if container in old_queue else len(old_queue)
    new_rank = new_queue.index(container)
    return abs(new_rank - old_rank) > r_shift  # A2: rank shift beyond threshold


def _plan_impact(plan_old: Plan, old_queue: list[str], new_queue: list[str], state_new: YardState, r_shift: int) -> float:
    """I_plan: fraction of P_old's actions that are affected (spec 8.5)."""
    if not plan_old.actions:
        return 0.0
    affected = sum(1 for a in plan_old.actions if is_action_affected(a, old_queue, new_queue, state_new, r_shift))
    return affected / len(plan_old.actions)


def compute_impact(
    old_queue: list[str],
    new_queue: list[str],
    state_old: YardState,
    state_new: YardState,
    plan_old: Plan,
    k: int = 10,
    r_shift: int = 5,
    sigma_b: float = 2.0,
    conf_new: float = 1.0,
    weights: dict | None = None,
) -> ImpactBreakdown:
    w = weights or DEFAULT_WEIGHTS
    i_order = _kendall_tau_topk(old_queue, new_queue, k)
    i_target = _target_impact(old_queue, new_queue)
    i_blocking = _blocking_impact(state_old, state_new, old_queue, new_queue, k, sigma_b)
    i_plan = _plan_impact(plan_old, old_queue, new_queue, state_new, r_shift)
    i_conf = 1.0 - conf_new

    total = (
        w["w_o"] * i_order
        + w["w_t"] * i_target
        + w["w_b"] * i_blocking
        + w["w_p"] * i_plan
        + w["w_c"] * i_conf
    )
    return ImpactBreakdown(i_order=i_order, i_target=i_target, i_blocking=i_blocking,
                            i_plan=i_plan, i_conf=i_conf, total=total)
