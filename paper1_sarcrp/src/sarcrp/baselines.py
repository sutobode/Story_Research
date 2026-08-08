import random

from sarcrp.crp_solver import solve_crp
from sarcrp.freeze_horizon import split_plan
from sarcrp.sarcrp_core import ReplanDecision, replan
from sarcrp.schemas import Plan


def static_plan(plan_initial: Plan) -> Plan:
    """B1 (spec 22): never replan, regardless of incoming events."""
    return plan_initial


def full_reoptimization(state_t, retrieval_queue_new: list[str], constraints: dict | None = None, time_limit_sec: float = 5.0) -> Plan:
    """B2 (spec 22): re-solve the whole remaining problem on every event."""
    return solve_crp(state_t, retrieval_queue_new, constraints=constraints, time_limit_sec=time_limit_sec)


def periodic_replan(
    state, retrieval_queue_new: list[str], plan_current: Plan, event_index: int,
    period: int = 5, time_limit_sec: float = 5.0,
) -> Plan:
    """B3 (spec 22): re-solve every `period`-th event; otherwise keep the
    current plan unchanged (spec's own example: "every 10 events")."""
    if event_index % period != 0:
        return plan_current
    return solve_crp(state, retrieval_queue_new, time_limit_sec=time_limit_sec)


def event_triggered_no_stability(
    state, plan_old: Plan, old_queue: list[str], new_queue: list[str],
    urgent_containers: list[str], rng: random.Random,
    h_f: int = 3, theta_impact: float = 0.30, tau_frac: float = 0.01,
    time_limit_sec: float = 5.0, conf_new: float = 1.0,
) -> ReplanDecision:
    """B4 (spec 22, 40): same trigger AND freeze horizon as SAR-CRP, but the
    objective drops both the stability term and the data-confidence term
    (lambda=mu=0) -- "objective chi toi uu operational cost" (spec 40).
    `h_f` is exposed (unlike lambda/mu, which are fixed at 0 by this
    baseline's definition) because Experiment 1 (Task 28) varies freeze_size
    across all methods that have a freeze horizon at all -- B4 is one of them."""
    return replan(
        state, plan_old, old_queue, new_queue, urgent_containers,
        h_f=h_f, lam=0.0, mu=0.0, theta_impact=theta_impact, tau_frac=tau_frac,
        time_limit_sec=time_limit_sec, rng=rng, conf_new=conf_new,
    )


def mpc_receding_horizon(
    state, plan_current: Plan, retrieval_queue_new: list[str],
    horizon: int = 5, time_limit_sec: float = 5.0,
) -> Plan:
    """B5 (spec 22, 40): freeze a fixed-size horizon prefix, unconditionally
    re-solve the tail every event -- no trigger, no local repair, no
    stability-aware candidate selection (spec 40's explicit simplification)."""
    frozen, _tail = split_plan(plan_current, horizon)
    tail_solution = solve_crp(state, retrieval_queue_new, time_limit_sec=time_limit_sec)
    actions = list(frozen.actions) + list(tail_solution.actions)
    for i, a in enumerate(actions):
        a.step_index = i
    return Plan(plan_id=f"{plan_current.plan_id}_mpc", created_at=plan_current.created_at,
                source="mpc_receding_horizon", actions=actions)
