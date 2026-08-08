import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_mvp import evaluate_decision_gate, run_all_methods  # noqa: E402


def test_run_all_methods_returns_a_row_per_method_per_seed():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_all_methods(instance, methods=("static", "full_reopt", "sarcrp"), seeds=(0, 1))
    assert len(rows) == 3 * 2
    assert {r["method"] for r in rows} == {"static", "full_reopt", "sarcrp"}


def test_evaluate_decision_gate_reports_three_conditions():
    rows = [
        {"method": "static", "total_cost_mean": 10.0, "changed_actions_total": 0},
        {"method": "full_reopt", "total_cost_mean": 6.0, "changed_actions_total": 20},
        {"method": "sarcrp", "total_cost_mean": 7.0, "changed_actions_total": 5},
    ]
    verdict = evaluate_decision_gate(rows)
    assert set(verdict.keys()) == {"sarcrp_beats_static_total_cost", "sarcrp_beats_full_reopt_stability", "sarcrp_close_to_full_reopt_operational"}
    assert verdict["sarcrp_beats_static_total_cost"] is True
    assert verdict["sarcrp_beats_full_reopt_stability"] is True
