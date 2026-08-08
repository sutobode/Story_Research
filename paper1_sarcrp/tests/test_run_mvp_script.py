import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_mvp import evaluate_decision_gate, run_all_methods  # noqa: E402


def test_run_all_methods_returns_a_row_per_method_per_seed_per_level():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_all_methods(instance, methods=("static", "full_reopt", "sarcrp"), seeds=(0, 1), uncertainty_levels=("medium",))
    assert len(rows) == 3 * 2 * 1
    assert {r["method"] for r in rows} == {"static", "full_reopt", "sarcrp"}
    assert {r["uncertainty_level"] for r in rows} == {"medium"}
    assert "operational_cost_mean" in rows[0]


def test_run_all_methods_covers_multiple_uncertainty_levels():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_all_methods(instance, methods=("static",), seeds=(0,), uncertainty_levels=("low", "high"))
    assert {r["uncertainty_level"] for r in rows} == {"low", "high"}


def test_evaluate_decision_gate_reports_three_conditions_per_level():
    rows = [
        {"method": "static", "uncertainty_level": "medium", "total_cost_mean": 10.0, "operational_cost_mean": 10.0, "changed_actions_total": 0},
        {"method": "full_reopt", "uncertainty_level": "medium", "total_cost_mean": 6.0, "operational_cost_mean": 6.0, "changed_actions_total": 20},
        {"method": "sarcrp", "uncertainty_level": "medium", "total_cost_mean": 7.0, "operational_cost_mean": 5.0, "changed_actions_total": 5},
    ]
    verdict_by_level = evaluate_decision_gate(rows)
    assert set(verdict_by_level.keys()) == {"medium"}
    medium = verdict_by_level["medium"]
    assert set(medium.keys()) == {
        "sarcrp_beats_static_total_cost",
        "sarcrp_beats_full_reopt_stability",
        "sarcrp_operational_cost_not_worse_than_full_reopt",
    }
    assert medium["sarcrp_beats_static_total_cost"] is True
    assert medium["sarcrp_beats_full_reopt_stability"] is True
    assert medium["sarcrp_operational_cost_not_worse_than_full_reopt"] is True  # 5.0 <= 6.0*1.2


def test_evaluate_decision_gate_operational_check_is_upper_bound_only():
    # SAR-CRP operational cost far BELOW Full Reopt's must PASS, not FAIL --
    # this is exactly the proxy bug the MVP report flagged.
    rows = [
        {"method": "static", "uncertainty_level": "medium", "total_cost_mean": 7.0, "operational_cost_mean": 7.0, "changed_actions_total": 0},
        {"method": "full_reopt", "uncertainty_level": "medium", "total_cost_mean": 20.0, "operational_cost_mean": 20.0, "changed_actions_total": 66},
        {"method": "sarcrp", "uncertainty_level": "medium", "total_cost_mean": 6.8, "operational_cost_mean": 6.8, "changed_actions_total": 0},
    ]
    verdict = evaluate_decision_gate(rows)["medium"]
    assert verdict["sarcrp_operational_cost_not_worse_than_full_reopt"] is True
