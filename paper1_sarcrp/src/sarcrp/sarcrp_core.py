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


def _score_candidate(plan: Plan, plan_old: Plan, frozen_count: int, urgent_containers: list[str], conf_new: float, state,
                      lam: float = 1.0, mu: float = 0.5, normalize_delay: bool = True, delay_convention: str = "actions"):
    """Scores a candidate plan against spec 11's C_op (which includes the
    M_inf invalidity penalty) -- `is_valid` was hardcoded True here
    unconditionally until this fix, so a candidate that replays illegally
    (e.g. a RETRIEVE for a container no longer on top of its stack) could
    look artificially cheap and win candidate selection instead of being
    excluded. Caught building a multi-urgent-container local-search
    operator (N6) whose destination choices could collide with an
    unrelated later action's assumptions.

    Second bug fix (self-review): `lam`/`mu` were accepted by replan()'s
    own signature but never reached this function, which always used
    compute_objective's defaults (lam=1.0, mu=0.5). SAR-CRP's stability
    and data-confidence weights were therefore inert -- and ablations A3
    ("No Stability Cost", lam=0) and A5 ("No Data Confidence Penalty",
    mu=0) were silent no-ops rather than real ablations. Both are now
    threaded through; the defaults reproduce every previously-reported
    number exactly."""
    is_valid = is_plan_valid(plan, state)
    op = operational_cost(plan, urgent_containers, is_valid=is_valid, normalize_delay=normalize_delay, delay_convention=delay_convention)
    stab, violated = stability_cost(plan, plan_old, frozen_count)
    if violated:
        return float("inf")
    data = data_confidence_cost(plan, plan_old, conf_new)
    return compute_objective(op, stab, data, lam=lam, mu=mu)


def _apply_fallback_margin(
    j_old: float, j_best: float, tau: float, carried_gain: float,
    carried_gain_cap: float | None = None, carried_gain_decay: float = 1.0,
) -> tuple[str, float]:
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
    memoryless criterion exactly.

    R1.2 (reviewer critique): the mechanism above lets carried_gain
    accumulate across arbitrarily many sub-margin rounds with no bound and
    no decay -- carried_gain_cap and carried_gain_decay are opt-in
    ablation hooks (default None/1.0 reproduce the validated mechanism
    exactly, unused by every existing test/experiment) to check whether
    Scenario E's real win survives a more conservative version: decay
    shrinks the INCOMING carry (money owed from before) before adding
    this round's fresh raw_gain, modeling that older foregone
    opportunities should count for less; cap bounds how much carry can
    ever be in flight at once, so no single round's carry-in can by
    itself exceed a fixed budget. A round with no viable candidate
    (raw_gain<=0) still leaves the existing carry untouched, same as the
    default -- decay only fires on a round that itself found a genuine,
    if sub-margin, improvement.

    FORMAL PROPERTIES (verified numerically in test_sarcrp_core.py's
    test_carried_gain_* tests -- restricting attention, WLOG, to the
    subsequence of rounds with raw_gain>0 within one "epoch" between two
    UPDATEs, since raw_gain<=0 rounds are no-ops for the carry):

    1. Soundness (no premature switching): while decision=="KEEP", the
       cumulative sum of raw_gain since the last UPDATE, S_t, always
       satisfies S_t <= tau -- the mechanism never treats an accumulated
       benefit smaller than the hysteresis margin as sufficient.
    2. Bounded overshoot (default, cap=None, decay=1.0): at the round an
       UPDATE triggers, tau < S_t <= tau + max(raw_gain in that epoch) --
       the mechanism can overshoot tau by at most the single largest
       round's own gain, never more, regardless of epoch length.
    3. Timeliness: if every raw_gain in an epoch is >= epsilon > 0, an
       UPDATE triggers within at most ceil(tau/epsilon) rounds -- genuine,
       recurring improvement is never postponed indefinitely.
    4. Cap sufficiency (permanent KEEP): if carried_gain_cap=C and every
       raw_gain g in the epoch satisfies g < tau - C, the mechanism NEVER
       updates via accumulation once the carry saturates at C, no matter
       how many rounds elapse -- this is the exact, general reason R1.2's
       carried_gain_cap=0.05 ablation erased Scenario E's 18/20 win
       (tau~=0.46-0.48, per-instance gain~=0.2119, and 0.05 < tau-0.2119
       comfortably): not a coincidence of those specific numbers, but a
       guaranteed consequence of this inequality for any instance
       satisfying it.
    5. Decay steady-state (permanent KEEP, dual of property 4): under
       constant carried_gain_decay=lambda<1 and a constant repeated gain
       g, the carry converges to the geometric-series limit g/(1-lambda).
       If that limit is <= tau, the mechanism never updates, however many
       rounds elapse; if the limit exceeds tau, an UPDATE is guaranteed at
       some finite round (the carry increases monotonically toward a
       limit above tau, so it must cross tau).

    Properties 4-5 explain WHY the cap ablation broke Scenario E's result
    while the decay=0.5 ablation did not: Scenario E is a single carry-in
    application (instance A's outcome combined once with instance B's own
    gain), not a many-round accumulation -- decay=0.5 there is a one-shot
    halving (0.2119*0.5=0.10595 combined with B's own ~0.2119, still
    enough to clear tau_B for most seeds), never reaching the asymptotic
    regime properties 4-5 describe. The cap, by contrast, binds
    immediately on the very first application (min(0.2119, 0.05)=0.05),
    which is a one-round instance of property 4's general condition."""
    if j_best == float("inf"):
        return "KEEP", carried_gain
    raw_gain = j_old - j_best
    if raw_gain <= 0:
        return "KEEP", carried_gain
    incoming_carry = carried_gain * carried_gain_decay
    if carried_gain_cap is not None:
        incoming_carry = min(incoming_carry, carried_gain_cap)
    if raw_gain + incoming_carry <= tau:
        new_carry = incoming_carry + raw_gain
        if carried_gain_cap is not None:
            new_carry = min(new_carry, carried_gain_cap)
        return "KEEP", new_carry
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
    tau_abs: float | None = None,
    normalize_delay: bool = True,
    delay_convention: str = "actions",
    # REPRODUCIBILITY (bug #11, self-review): a wall-clock cutoff makes
    # results machine- and load-dependent. Measured on the 44-container
    # existence-proof instance: the local-search walk finishes naturally in
    # 4.10s, i.e. 82% of this 5.0s default budget -- so a machine ~20%
    # slower truncates the walk, the repair gain collapses from 0.2119 to
    # 0.0, and the decision flips KEEP<->UPDATE. That is exactly why the
    # same Scenario E run yields 18/20 updates on an idle machine and 13/20
    # under load. Pass time_limit_sec=None for the DETERMINISTIC budget
    # (iteration-count only, t_iters/m_neighbors), which is what any
    # reported number should use; the float default is retained only so
    # previously logged runs stay reproducible bit-for-bit.
    time_limit_sec: float | None = 5.0,
    rng: random.Random | None = None,
    conf_new: float = 1.0,
    use_local_search: bool = True,
    impact_weights: dict | None = None,
    solver=None,
    carried_gain: float = 0.0,
    carried_gain_cap: float | None = None,
    carried_gain_decay: float = 1.0,
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
        j_old = _score_candidate(plan_old, plan_old, 0, urgent_containers, conf_new, state_t, lam=lam, mu=mu, normalize_delay=normalize_delay, delay_convention=delay_convention)
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
            lam=lam, mu=mu, normalize_delay=normalize_delay, delay_convention=delay_convention,
        )
        candidates.append(c2)
    shadow_state, remaining_queue = apply_frozen_prefix(state_t, frozen, new_queue)
    tail_solution = active_solver(shadow_state, remaining_queue, time_limit_sec=time_limit_sec)
    c3 = _build_c3(plan_old, frozen, tail_solution)
    candidates.append(c3)

    # Step 6: score every candidate.
    scored = [(_score_candidate(c, plan_old, frozen_count, urgent_containers, conf_new, state_t, lam=lam, mu=mu, normalize_delay=normalize_delay, delay_convention=delay_convention), c) for c in candidates]

    # Step 7: select best.
    j_best, p_best = min(scored, key=lambda pair: pair[0])
    j_old = _score_candidate(plan_old, plan_old, 0, urgent_containers, conf_new, state_t, lam=lam, mu=mu, normalize_delay=normalize_delay, delay_convention=delay_convention)

    # Step 8: fallback check (extended with the carried-gain lookahead margin).
    #
    # tau_abs implements the mixed relative-absolute threshold standard in
    # event-triggered control (see Related Work's cited survey), motivated
    # by a provable dead zone in the purely relative form: the largest
    # operational gain any delay-driven repair can produce is exactly beta
    # (RetrievalDelayNorm is normalized to [0,1]), a CONSTANT, while a
    # purely relative tau = tau_frac * j_old grows with instance size. So
    # for j_old >= beta/tau_frac = 50, no delay-driven repair can ever
    # clear the margin -- impossible by construction, not merely unlikely
    # (see tests/test_objective_dead_zones.py, and the arithmetic behind
    # Scenario B's "near miss" at j_old=61.49). Capping tau at an absolute
    # ceiling removes that scale-dependent dead zone. tau_abs=None (the
    # default) reproduces the original purely-relative criterion exactly.
    tau = tau_frac * j_old if j_old not in (0.0, float("inf")) else 0.0
    if tau_abs is not None:
        tau = min(tau, tau_abs)
    decision, carried_gain_next = _apply_fallback_margin(
        j_old, j_best, tau, carried_gain, carried_gain_cap, carried_gain_decay,
    )
    if decision == "KEEP":
        return ReplanDecision(decision="KEEP", plan=plan_old, impact=impact, j_old=j_old, j_new=j_best,
                               carried_gain_next=carried_gain_next)

    # Step 9: update.
    return ReplanDecision(decision="UPDATE", plan=p_best, impact=impact, j_old=j_old, j_new=j_best,
                           carried_gain_next=carried_gain_next)
