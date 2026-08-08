import random

from sarcrp.sarcrp_core import ReplanDecision, replan
from sarcrp.schemas import Plan

# Each entry overrides sarcrp_core.replan's defaults for one ablation (spec 25).
ABLATIONS: dict[str, dict] = {
    "A1_no_trigger": {"theta_impact": 0.0},  # always attempt replan
    "A2_no_freeze": {"h_f": 0},  # no frozen prefix
    "A3_no_stability": {"lam": 0.0},  # optimize operational cost only
    "A4_no_local_search": {"use_local_search": False},  # candidates C0/C1/C3 only
    "A5_no_data_confidence": {"mu": 0.0},  # ignore data-confidence penalty
    "A6_no_blocking_impact": {
        "impact_weights": {"w_o": 0.25, "w_t": 0.20, "w_b": 0.0, "w_p": 0.20, "w_c": 0.10}
    },
}


def replan_with_ablation(
    ablation_name: str,
    state_t,
    plan_old: Plan,
    old_queue: list[str],
    new_queue: list[str],
    urgent_containers: list[str],
    rng: random.Random,
    conf_new: float = 1.0,
) -> ReplanDecision:
    """Runs sarcrp_core.replan with one ablation's parameter overrides applied
    on top of the standard defaults (spec 25: goal is to demonstrate each
    module's contribution)."""
    if ablation_name not in ABLATIONS:
        raise ValueError(f"unknown ablation: {ablation_name!r}, expected one of {sorted(ABLATIONS)}")
    overrides = ABLATIONS[ablation_name]
    return replan(state_t, plan_old, old_queue, new_queue, urgent_containers, rng=rng, conf_new=conf_new, **overrides)
