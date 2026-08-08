import math
from sarcrp.schemas import Action, Plan
from sarcrp.objective import (
    relocation_count, retrieval_delay_norm, operational_cost,
    stability_cost, data_confidence_cost, compute_objective,
)


def make_action(step, atype="RELOCATE", container="C1", dest="S2", commit="planned"):
    return Action(action_id=f"a{step}", step_index=step, type=atype, container=container,
                  source_stack="S1", dest_stack=dest, commit_status=commit, planned_time=step)


def test_relocation_count_counts_only_relocate():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        make_action(0, "RELOCATE"), make_action(1, "RETRIEVE"), make_action(2, "RELOCATE"),
    ])
    assert relocation_count(plan) == 2


def test_retrieval_delay_norm_zero_without_urgent():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0)])
    assert retrieval_delay_norm(plan, urgent_containers=[]) == 0.0


def test_retrieval_delay_norm_penalizes_late_position():
    actions = [make_action(i, container=f"C{i}") for i in range(4)]
    plan = Plan(plan_id="p", created_at=0, source="t", actions=actions)
    delay_early = retrieval_delay_norm(plan, urgent_containers=["C0"])
    delay_late = retrieval_delay_norm(plan, urgent_containers=["C3"])
    assert delay_late > delay_early


def test_operational_cost_invalid_dominates():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0)])
    valid_cost = operational_cost(plan, urgent_containers=[], is_valid=True)
    invalid_cost = operational_cost(plan, urgent_containers=[], is_valid=False)
    assert invalid_cost - valid_cost == 1.0e6  # gamma=1.0 * M_inf=1e6 (spec 11.3/11.4)


def test_stability_cost_zero_when_identical():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0), make_action(1)])
    cost, violated = stability_cost(plan, plan, frozen_count=0)
    assert cost == 0.0
    assert violated is False


def test_stability_cost_penalizes_container_change():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0, container="C1")])
    new_plan = Plan(plan_id="p2", created_at=0, source="t", actions=[make_action(0, container="C2")])
    cost, violated = stability_cost(new_plan, old_plan, frozen_count=0)
    assert cost > 0.0
    assert violated is False


def test_stability_cost_flags_frozen_violation():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0, container="C1")])
    new_plan = Plan(plan_id="p2", created_at=0, source="t", actions=[make_action(0, container="C2")])
    cost, violated = stability_cost(new_plan, old_plan, frozen_count=1)
    assert violated is True
    assert math.isinf(cost)


def test_data_confidence_cost_scales_with_low_confidence():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0, container="C1")])
    new_plan = Plan(plan_id="p2", created_at=0, source="t", actions=[make_action(0, container="C2")])
    high_conf_cost = data_confidence_cost(new_plan, old_plan, conf_new=0.9)
    low_conf_cost = data_confidence_cost(new_plan, old_plan, conf_new=0.1)
    assert low_conf_cost > high_conf_cost


def test_compute_objective_combines_terms():
    j = compute_objective(op_cost=10.0, stab_cost=4.0, data_cost=2.0, lam=1.0, mu=0.5)
    assert j == 10.0 + 1.0 * 4.0 + 0.5 * 2.0
