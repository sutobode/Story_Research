import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_experiment4 import CONFIDENCE_LEVELS, run_confidence_sweep  # noqa: E402


def test_confidence_levels_match_spec():
    assert CONFIDENCE_LEVELS == (1.0, 0.7, 0.4, 0.2)


def test_run_confidence_sweep_returns_a_row_per_level_per_seed():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_confidence_sweep(instance, methods=("sarcrp",), seeds=(0, 1))
    levels_seen = {r["fixed_confidence"] for r in rows}
    assert levels_seen == set(CONFIDENCE_LEVELS)
    assert len(rows) == len(CONFIDENCE_LEVELS) * 1 * 2
