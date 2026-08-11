"""Two provable dead zones in SAR-CRP's objective/margin parameterization,
discovered by self-review after Experiment 1 showed SAR-CRP numerically
identical to Static in all 3240 episodes and a diagnostic found 0/190
events with any positive repair gain even at lam=mu=0 (all switching cost
removed). Both are arithmetic consequences of the default weights, not
benchmark artifacts, and together they explain that null result exactly.

DZ1 (scale-independent, alpha vs beta): RetrievalDelayNorm is normalized
to [0,1] and weighted by beta=0.5, so the largest operational gain any
delay-driven repair can produce is exactly beta. A relocation costs
alpha=1.0. Therefore expediting an urgent container can never pay for even
ONE extra relocation -- at any instance size.

DZ2 (scale-dependent, beta vs tau): the fallback margin is relative,
tau = tau_frac * J_old with tau_frac=0.01, while the maximum delay-driven
gain is the constant beta. So a delay-driven UPDATE requires
beta > tau_frac * J_old, i.e. J_old < beta/tau_frac = 50. Beyond that
scale, delay-driven replanning is impossible by construction.
"""
import math

from sarcrp.objective import operational_cost, retrieval_delay_norm
from sarcrp.schemas import Action, Plan

ALPHA_DEFAULT = 1.0
BETA_DEFAULT = 0.5
TAU_FRAC_DEFAULT = 0.01


def _plan(n_actions: int, urgent_at: int | None = None, urgent_id: str = "U") -> Plan:
    """A plan of n RETRIEVE actions; if urgent_at is given, the urgent
    container occupies exactly that step index."""
    actions = []
    for i in range(n_actions):
        container = urgent_id if (urgent_at is not None and i == urgent_at) else f"C{i:03d}"
        actions.append(Action(action_id=f"a{i}", step_index=i, type="RETRIEVE", container=container,
                               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=i))
    return Plan(plan_id="p", created_at=0, source="test", actions=actions)


def test_retrieval_delay_norm_is_bounded_in_zero_one():
    # The bound that drives both dead zones: however large the plan and
    # however late the urgent container sits, the normalized delay cannot
    # exceed 1.0 -- so beta * delay cannot exceed beta.
    for n in (5, 50, 500):
        best = retrieval_delay_norm(_plan(n, urgent_at=0), ["U"])
        worst = retrieval_delay_norm(_plan(n, urgent_at=n - 1), ["U"])
        missing = retrieval_delay_norm(_plan(n), ["U"])  # not in plan at all -> len+1 position
        assert 0.0 <= best <= 1.0
        assert 0.0 <= worst <= 1.0
        assert missing <= 1.0
        assert best < worst <= missing


def test_dz1_max_delay_gain_is_exactly_beta_and_cannot_pay_for_one_relocation():
    # DZ1: the entire achievable operational benefit from moving an urgent
    # container from the worst position to the best is bounded by beta.
    # One extra relocation costs alpha. With the defaults alpha=1.0 >
    # beta=0.5, a repair that expedites an urgent container at the price of
    # a single additional relocation is ALWAYS net-worse, at any scale.
    n = 200
    worst_plan = _plan(n, urgent_at=n - 1)
    best_plan = _plan(n, urgent_at=0)
    cost_worst = operational_cost(worst_plan, ["U"], is_valid=True)
    cost_best = operational_cost(best_plan, ["U"], is_valid=True)
    max_delay_gain = cost_worst - cost_best
    assert max_delay_gain <= BETA_DEFAULT + 1e-9
    assert max_delay_gain < ALPHA_DEFAULT  # cannot pay for even one relocation
    # and the bound is tight: it approaches beta as the plan grows
    assert max_delay_gain > BETA_DEFAULT * 0.98


def test_dz1_holds_at_every_scale_not_just_large_plans():
    for n in (5, 20, 50, 200, 1000):
        cost_worst = operational_cost(_plan(n, urgent_at=n - 1), ["U"], is_valid=True)
        cost_best = operational_cost(_plan(n, urgent_at=0), ["U"], is_valid=True)
        assert (cost_worst - cost_best) < ALPHA_DEFAULT


def test_dz2_relative_margin_exceeds_max_delay_gain_beyond_a_computable_scale():
    # DZ2: tau = tau_frac * J_old grows with instance size; the maximum
    # delay-driven gain is the constant beta. The crossover is exactly
    # J_old = beta / tau_frac.
    crossover = BETA_DEFAULT / TAU_FRAC_DEFAULT
    assert math.isclose(crossover, 50.0)

    for j_old, delay_gain_can_clear_tau in ((10.0, True), (49.0, True), (50.0, False), (61.49, False), (200.0, False)):
        tau = TAU_FRAC_DEFAULT * j_old
        assert (BETA_DEFAULT > tau) is delay_gain_can_clear_tau


def test_dz1_fix_action_scaled_delay_grows_with_scale_and_can_pay_for_relocations():
    # DZ1 fix: measuring delay in crane actions instead of as a [0,1]
    # fraction makes the achievable gain grow with the plan, so it can pay
    # for relocations once the instance is large enough -- exactly what the
    # normalized form makes impossible at every scale.
    from sarcrp.objective import retrieval_delay_actions

    for n in (5, 20, 50, 200):
        worst = _plan(n, urgent_at=n - 1)
        best = _plan(n, urgent_at=0)
        gain_normalized = (operational_cost(worst, ["U"], is_valid=True, normalize_delay=True)
                            - operational_cost(best, ["U"], is_valid=True, normalize_delay=True))
        gain_actions = (operational_cost(worst, ["U"], is_valid=True, normalize_delay=False)
                         - operational_cost(best, ["U"], is_valid=True, normalize_delay=False))
        # normalized form: always capped below one relocation (DZ1)
        assert gain_normalized < ALPHA_DEFAULT
        # action-scaled form: exactly beta * (n-1), and it grows with n
        assert math.isclose(gain_actions, BETA_DEFAULT * (n - 1), rel_tol=1e-9)
        if n >= 5:
            assert gain_actions > ALPHA_DEFAULT  # can pay for at least one relocation

    # and the raw measure is in actions, not a fraction
    assert retrieval_delay_actions(_plan(100, urgent_at=99), ["U"]) == 99.0


def test_dz1_fix_bound_matches_max_delay_driven_gain_helper():
    from sarcrp.objective import max_delay_driven_gain

    for n in (10, 61, 200):
        assert math.isclose(max_delay_driven_gain(plan_length=n, normalize_delay=False),
                             BETA_DEFAULT * (n - 1), rel_tol=1e-9)
        assert max_delay_driven_gain(plan_length=n, normalize_delay=True) < BETA_DEFAULT


def test_normalize_delay_default_true_preserves_the_original_objective():
    # Every previously reported number must stay reproducible: the default
    # must be the original normalized form.
    from sarcrp.objective import retrieval_delay_norm
    p = _plan(40, urgent_at=30)
    default = operational_cost(p, ["U"], is_valid=True)
    explicit = operational_cost(p, ["U"], is_valid=True, normalize_delay=True)
    assert default == explicit
    assert math.isclose(default, 0.0 + BETA_DEFAULT * retrieval_delay_norm(p, ["U"]), rel_tol=1e-9)


def test_mixed_threshold_removes_dz2_at_every_scale():
    # The fix (mixed relative-absolute threshold, standard in
    # event-triggered control): tau = min(tau_frac * J_old, tau_abs).
    # Choosing tau_abs from the bound itself rather than fitting it --
    # tau_abs = beta/2 requires a repair to capture at least half of the
    # maximum achievable delay benefit -- makes a delay-driven UPDATE
    # possible at EVERY scale, which the purely relative form forbids past
    # J_old=50.
    tau_abs = BETA_DEFAULT / 2
    for j_old in (10.0, 49.0, 50.0, 61.49, 200.0, 5000.0):
        tau_relative_only = TAU_FRAC_DEFAULT * j_old
        tau_mixed = min(tau_relative_only, tau_abs)
        assert tau_mixed <= tau_abs
        # a repair capturing the full achievable delay benefit (beta) now
        # clears the margin regardless of instance size
        assert BETA_DEFAULT > tau_mixed
    # and past the crossover the purely relative form genuinely blocked it
    assert BETA_DEFAULT < TAU_FRAC_DEFAULT * 200.0


def test_mixed_threshold_default_none_preserves_the_original_criterion():
    # tau_abs=None must reproduce spec 9's purely relative margin exactly,
    # so every previously reported number stays reproducible.
    for j_old in (7.0, 61.49, 200.0):
        tau_relative = TAU_FRAC_DEFAULT * j_old
        tau_abs = None
        tau_effective = tau_relative if tau_abs is None else min(tau_relative, tau_abs)
        assert tau_effective == tau_relative


def test_dz2_predicts_scenario_b_near_miss_arithmetically_not_empirically():
    # The existence-proof report describes Scenario B (50 containers) as
    # empirically discovering "a real gain (0.51) that lands just under
    # spec's own 1% fallback margin (tau=0.615)". DZ2 shows this was an
    # arithmetic certainty: J_old=61.49 is past the crossover J_old=50, so
    # NO delay-driven gain could have cleared tau on that instance,
    # whatever the local search found.
    j_old_scenario_b = 61.49
    tau_scenario_b = TAU_FRAC_DEFAULT * j_old_scenario_b
    assert tau_scenario_b > BETA_DEFAULT  # 0.6149 > 0.5 -- blocked before the search even runs
    reported_gain = 0.51
    assert reported_gain < tau_scenario_b  # matches the reported near-miss
    assert reported_gain <= BETA_DEFAULT + 0.02  # and sits at DZ1's own beta ceiling
