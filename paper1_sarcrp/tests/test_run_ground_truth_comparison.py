import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_ground_truth_comparison import run_comparison  # noqa: E402


def test_run_comparison_reports_optimal_and_greedy_relocations():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "tiny_ground_truth.json").read_text())
    result = run_comparison(instance)
    assert "optimal_relocations" in result
    assert "greedy_relocations" in result
    assert "greedy_gap" in result
    assert result["greedy_relocations"] >= result["optimal_relocations"]
    assert result["greedy_gap"] >= 0.0
