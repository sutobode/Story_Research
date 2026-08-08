import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_cross_layout import run_all_layouts, summarize_performance_drop  # noqa: E402

import pytest


def test_run_all_layouts_covers_all_three_layouts():
    rows = run_all_layouts(methods=("static", "sarcrp"), seeds=(0, 1))
    layouts = {r["layout"] for r in rows}
    assert layouts == {"layout_a", "layout_b", "layout_c"}


def test_summarize_performance_drop_reports_relative_change_from_layout_a():
    rows = [
        {"layout": "layout_a", "method": "sarcrp", "total_cost_mean": 7.0},
        {"layout": "layout_b", "method": "sarcrp", "total_cost_mean": 8.4},
        {"layout": "layout_c", "method": "sarcrp", "total_cost_mean": 10.5},
    ]
    drop = summarize_performance_drop(rows, method="sarcrp")
    assert drop["layout_b"] == pytest.approx(0.20, rel=1e-3)  # (8.4-7.0)/7.0
    assert drop["layout_c"] == pytest.approx(0.50, rel=1e-3)
