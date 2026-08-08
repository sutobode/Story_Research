import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_experiment1 import FACTOR_GRID, run_factorial, run_significance_tests  # noqa: E402


def test_factor_grid_matches_spec_23():
    assert set(FACTOR_GRID["uncertainty_level"]) == {"low", "medium", "high"}
    assert set(FACTOR_GRID["freeze_size"]) == {0, 3, 5}
    assert set(FACTOR_GRID["lam"]) == {0.0, 0.5, 1.0}


def test_run_factorial_covers_the_full_grid_for_two_seeds():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_factorial(instance, methods=("static", "sarcrp"), seeds=(0, 1))
    combos = {(r["uncertainty_level"], r["freeze_size"], r["lam"]) for r in rows if r["method"] == "sarcrp"}
    assert len(combos) == 3 * 3 * 3


def test_run_factorial_threads_freeze_size_and_lam_into_run_episode(monkeypatch):
    # Regression guard for the bug this plan's self-review caught: freeze_size
    # and lam were defined in FACTOR_GRID but never threaded through to
    # run_episode, so every combination silently produced identical rows.
    # A behavioral-difference assertion is unreliable here (Task 26/27 found
    # that most random event streams never even reach a real UPDATE decision
    # for this instance's default parameters), so this spies on run_episode's
    # call arguments directly instead.
    import run_experiment1 as run_experiment1_module

    captured_calls = []
    original_run_episode = run_experiment1_module.run_episode

    def spy_run_episode(*args, **kwargs):
        captured_calls.append(kwargs)
        return original_run_episode(*args, **kwargs)

    monkeypatch.setattr(run_experiment1_module, "run_episode", spy_run_episode)

    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    run_factorial(instance, methods=("sarcrp",), seeds=(0,))

    h_f_values_seen = {c.get("h_f") for c in captured_calls}
    lam_values_seen = {c.get("lam") for c in captured_calls}
    assert h_f_values_seen == set(FACTOR_GRID["freeze_size"])
    assert lam_values_seen == set(FACTOR_GRID["lam"])


def _row(method, seed, total_cost_mean, uncertainty_level="medium", freeze_size=3, lam=1.0):
    return {
        "method": method, "seed": seed, "total_cost_mean": total_cost_mean,
        "uncertainty_level": uncertainty_level, "freeze_size": freeze_size, "lam": lam,
    }


def test_run_significance_tests_reports_holm_bonferroni_corrected_flags():
    rows = [_row("static", s, 7.0 + 0.01 * s) for s in range(20)] + [_row("sarcrp", s, 6.0 + 0.01 * s) for s in range(20)]
    result = run_significance_tests(rows, uncertainty_level="medium", baseline_methods=("static",))
    assert "static" in result
    assert "p_value" in result["static"]
    assert "p_value_holm_significant" in result["static"]
    assert "cliffs_delta" in result["static"]


def test_run_significance_tests_only_uses_the_requested_grid_cell():
    # Regression guard for a real bug: collapsing the full factorial grid
    # into a seed-keyed dict without filtering first silently keeps only
    # whichever grid cell happens to be iterated last, not the deliberate
    # (uncertainty_level, freeze_size=3, lam=1.0) default operating point
    # (spec 48's own H_f/lambda defaults). Build two grid cells with
    # deliberately different sarcrp values for the same seeds; only the
    # freeze_size=3, lam=1.0 cell's values should feed the test.
    rows = (
        [_row("static", s, 7.0, freeze_size=3, lam=1.0) for s in range(20)]
        + [_row("sarcrp", s, 6.0, freeze_size=3, lam=1.0) for s in range(20)]  # the requested cell
        + [_row("static", s, 7.0, freeze_size=5, lam=0.0) for s in range(20)]
        + [_row("sarcrp", s, 999.0, freeze_size=5, lam=0.0) for s in range(20)]  # a different cell -- must be ignored
    )
    result = run_significance_tests(rows, uncertainty_level="medium", baseline_methods=("static",), freeze_size=3, lam=1.0)
    assert result["_sarcrp_ci"][0] == 6.0  # mean of the requested cell's sarcrp values, not 999.0


def test_run_significance_tests_filters_by_uncertainty_level():
    rows = (
        [_row("static", s, 7.0, uncertainty_level="low") for s in range(20)]
        + [_row("sarcrp", s, 6.0, uncertainty_level="low") for s in range(20)]
        + [_row("static", s, 7.0, uncertainty_level="high") for s in range(20)]
        + [_row("sarcrp", s, 999.0, uncertainty_level="high") for s in range(20)]
    )
    result = run_significance_tests(rows, uncertainty_level="low", baseline_methods=("static",))
    assert result["_sarcrp_ci"][0] == 6.0
