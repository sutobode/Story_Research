import copy
import random
from dataclasses import dataclass

from sarcrp.crp_solver import solve_crp
from sarcrp.freeze_horizon import apply_frozen_prefix, split_plan
from sarcrp.impact_estimator import ImpactBreakdown, compute_impact
from sarcrp.local_search_repair import local_search_repair
from sarcrp.minimal_repair import minimal_feasibility_repair
from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, stability_cost
from sarcrp.plan_validator import is_plan_valid
from sarcrp.schemas import Plan


@dataclass
class ReplanDecision:
    decision: str  # "KEEP" or "UPDATE"
    plan: Plan
    impact: ImpactBreakdown
    j_old: float
    j_new: float
    carried_gain_next: float = 0.0  # feed into the next call's carried_gain (lookahead margin, see _apply_fallback_margin)


def _build_c3(plan_old: Plan, frozen: Plan, tail_solution: Plan) -> Plan:
    """Candidate C3 (spec 18 step 5): frozen prefix + a fresh solve on the
    tail. Actions are deep-copied and renumbered sequentially --
    frozen.actions keeps plan_old's own step_index (freeze_horizon.split_plan
    doesn't renumber), and tail_solution always restarts its own numbering
    at 0 (every solver does this), so concatenating them directly collides
    both at indices 0..h_f-1. stability_cost's index-keyed lookup would
    then silently drop the frozen action and compare against whatever the
    tail put at that index instead, fabricating a "frozen prefix violated"
    (p_f=inf) result on every call with h_f>0."""
    actions = copy.deepcopy(list(frozen.actions)) + list(tail_solution.actions)
    for i, a in enumerate(actions):
        a.step_index = i
    return Plan(plan_id=f"{plan_old.plan_id}_c3", created_at=plan_old.created_at,
                source="frozen+crp_tail", actions=actions)


def _score_candidate(plan: Plan, plan_old: Plan, frozen_count: int, urgent_containers: list[str], conf_new: float, state):
    """Scores a candidate plan against spec 11's C_op (which includes the
    M_inf invalidity penalty) -- `is_valid` was hardcoded True here
    unconditionally until this fix, so a candidate that replays illegally
    (e.g. a RETRIEVE for a container no longer on top of its stack) could
    look artificially cheap and win candidate selection instead of being
    excluded. Caught building a multi-urgent-container local-search
    operator (N6) whose destination choices could collide with an
    unrelated later action's assumptions."""
    is_valid = is_plan_valid(plan, state)
    op = operational_cost(plan, urgent_containers, is_valid=is_valid)
    stab, violated = stability_cost(plan, plan_old, frozen_count)
    if violated:
        return float("inf")
    data = data_confidence_cost(plan, plan_old, conf_new)
    return compute_objective(op, stab, data)


def _apply_fallback_margin(j_old: float, j_best: float, tau: float, carried_gain: float) -> tuple[str, float]:
    """Step 8 (spec 9's EstimatedGain > SwitchingCost + tau), extended with
    a carried-gain hysteresis motivated by the existence-proof report's
    Scenario C finding: the single-step margin is myopic, comparing only
    the immediate decision's own gain against tau with no memory of
    genuine-but-sub-margin improvements passed up before. A real,
    positive gain that doesn't clear tau this round is remembered and
    added to the NEXT round's gain (via the caller threading
    ReplanDecision.carried_gain_next back in as the next call's
    carried_gain), so an improvement that keeps recurring eventually
    clears tau instead of being discarded every single time. A round
    whose own best candidate is not an improvement at all (raw_gain<=0,
    including no viable candidate) never triggers an update by itself --
    carried_gain is a bonus on top of a genuine improvement this round,
    never a standalone reason to adopt a worse plan -- and leaves the
    carry untouched rather than eroding it.

    carried_gain=0.0 (replan()'s default) reproduces spec 9's original,
    memoryless criterion exactly."""
    if j_best == float("inf"):
        return "KEEP", carried_gain
    raw_gain = j_old - j_best
    if raw_gain <= 0:
        return "KEEP", carried_gain
    if raw_gain + carried_gain <= tau:
        return "KEEP", carried_gain + raw_gain
    return "UPDATE", 0.0


def replan(
    state_t,
    plan_old: Plan,
    old_queue: list[str],
    new_queue: list[str],
    urgent_containers: list[str],
    h_f: int = 3,
    lam: float = 1.0,
    mu: float = 0.5,
    theta_impact: float = 0.30,
    tau_frac: float = 0.01,
    time_limit_sec: float = 5.0,
    rng: random.Random | None = None,
    conf_new: float = 1.0,
    use_local_search: bool = True,
    impact_weights: dict | None = None,
    solver=None,
    carried_gain: float = 0.0,
) -> ReplanDecision:
    """Algorithm SAR-CRP v2 Core (spec 18), steps 1-9. use_local_search=False
    and impact_weights are ablation hooks (spec 25 A4, A6) -- not used by the
    default SAR-CRP configuration. `solver` defaults to the greedy heuristic
    and is used for candidate C3's tail (spec 43/33 -- pass
    crp_rl_adapter.solve_crp_via_crp_rl to use the real trained model).
    `carried_gain` defaults to 0.0, reproducing the original memoryless
    Step 8 exactly -- callers that want the lookahead margin (see
    _apply_fallback_margin) must explicitly thread
    ReplanDecision.carried_gain_next from the previous call back in
    (simulator.py's "sarcrp_lookahead" method does this; the default
    "sarcrp" method does not, so Experiment 1/3/4's numbers are
    unaffected)."""
    rng = rng or random.Random()
    active_solver = solver or solve_crp

    # Steps 1-2: confidence already folded into conf_new by the caller; estimate impact.
    impact = compute_impact(old_queue, new_queue, state_t, state_t, plan_old, conf_new=conf_new, weights=impact_weights)

    # Step 3: trigger check.
    if impact.total < theta_impact:
        j_old = _score_candidate(plan_old, plan_old, 0, urgent_containers, conf_new, state_t)
        return ReplanDecision(decision="KEEP", plan=plan_old, impact=impact, j_old=j_old, j_new=j_old,
                               carried_gain_next=carried_gain)

    # Step 4: split plan.
    frozen, _tail = split_plan(plan_old, h_f)
    frozen_count = len(frozen.actions)

    # Step 5: generate candidates C0-C3.
    c0 = plan_old
    c1 = minimal_feasibility_repair(plan_old, state_t, new_queue)
    candidates = [c0, c1]
    if use_local_search:
        c2 = local_search_repair(
            c1, plan_old, state_t, new_queue, frozen_count, rng,
            urgent_containers=urgent_containers, conf_new=conf_new, time_limit_sec=time_limit_sec,
        )
        candidates.append(c2)
    shadow_state, remaining_queue = apply_frozen_prefix(state_t, frozen, new_queue)
    tail_solution = active_solver(shadow_state, remaining_queue, time_limit_sec=time_limit_sec)
    c3 = _build_c3(plan_old, frozen, tail_solution)
    candidates.append(c3)

    # Step 6: score every candidate.
    scored = [(_score_candidate(c, plan_old, frozen_count, urgent_containers, conf_new, state_t), c) for c in candidates]

    # Step 7: select best.
    j_best, p_best = min(scored, key=lambda pair: pair[0])
    j_old = _score_candidate(plan_old, plan_old, 0, urgent_containers, conf_new, state_t)

    # Step 8: fallback check (extended with the carried-gain lookahead margin).
    tau = tau_frac * j_old if j_old not in (0.0, float("inf")) else 0.0
    decision, carried_gain_next = _apply_fallback_margin(j_old, j_best, tau, carried_gain)
    if decision == "KEEP":
        return ReplanDecision(decision="KEEP", plan=plan_old, impact=impact, j_old=j_old, j_new=j_best,
                               carried_gain_next=carried_gain_next)

    # Step 9: update.
    return ReplanDecision(decision="UPDATE", plan=p_best, impact=impact, j_old=j_old, j_new=j_best,
                           carried_gain_next=carried_gain_next)
