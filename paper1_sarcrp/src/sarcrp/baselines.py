from sarcrp.crp_solver import solve_crp
from sarcrp.schemas import Plan


def static_plan(plan_initial: Plan) -> Plan:
    """B1 (spec 22): never replan, regardless of incoming events."""
    return plan_initial


def full_reoptimization(state_t, retrieval_queue_new: list[str], constraints: dict | None = None, time_limit_sec: float = 5.0) -> Plan:
    """B2 (spec 22): re-solve the whole remaining problem on every event."""
    return solve_crp(state_t, retrieval_queue_new, constraints=constraints, time_limit_sec=time_limit_sec)
