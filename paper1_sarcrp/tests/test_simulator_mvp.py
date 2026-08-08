import random
from pathlib import Path
import pytest
from sarcrp.simulator import run_episode

SMALL_INSTANCE = {
    "instance_id": "mvp_small_01",
    "layout": {"num_stacks": 3, "max_tier": 6},
    "stacks": [
        {"id": "S1", "containers": ["C6", "C5", "C4", "C3", "C2", "C1"], "max_tier": 6},
        {"id": "S2", "containers": [], "max_tier": 6},
        {"id": "S3", "containers": [], "max_tier": 6},
    ],
    "initial_retrieval_order": ["C1", "C2", "C3", "C4", "C5", "C6"],
    "t_steps": 20,
    "uncertainty_level": "medium",
}


def test_run_episode_static_produces_metrics():
    metrics = run_episode(SMALL_INSTANCE, method_name="static", rng=random.Random(0))
    assert metrics.relocation_count_total >= 0
    assert metrics.runtime_mean_sec >= 0.0


def test_run_episode_sarcrp_produces_metrics_and_is_reproducible():
    m1 = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(42))
    m2 = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(42))
    assert m1.total_cost_mean == m2.total_cost_mean


def test_all_three_mvp_methods_run_without_error():
    for method in ("static", "full_reopt", "sarcrp"):
        metrics = run_episode(SMALL_INSTANCE, method_name=method, rng=random.Random(1))
        assert metrics.total_cost_mean >= 0.0


def test_operational_cost_mean_is_separate_from_total_cost():
    # full_reopt has no stability/data cost (frozen_count=0, but it replans every
    # event so its plan always matches "old" plan trivially at compute time) --
    # this test just asserts the two means are independently computed fields,
    # not that they must differ in every scenario.
    metrics = run_episode(SMALL_INSTANCE, method_name="full_reopt", rng=random.Random(2))
    assert metrics.operational_cost_mean >= 0.0
    assert isinstance(metrics.operational_cost_mean, float)


def test_run_episode_supports_periodic_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="periodic", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0


def test_run_episode_supports_event_triggered_no_stability_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="event_triggered_no_stability", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0


def test_run_episode_supports_mpc_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="mpc", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0


def test_run_episode_supports_sarcrp_lookahead_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="sarcrp_lookahead", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0


def test_run_episode_supports_ablation_methods():
    for ablation_method in ("sarcrp_A1_no_trigger", "sarcrp_A3_no_stability", "sarcrp_A6_no_blocking_impact"):
        metrics = run_episode(SMALL_INSTANCE, method_name=ablation_method, rng=random.Random(0))
        assert metrics.total_cost_mean >= 0.0


def test_run_episode_rejects_unknown_method():
    try:
        run_episode(SMALL_INSTANCE, method_name="not_a_method", rng=random.Random(0))
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_run_episode_threads_h_f_and_lam_into_replan(monkeypatch):
    # A behavioral difference is NOT a reliable signal here: Task 26's SC4
    # finding (mean impact=0.090, well under the trigger threshold 0.30)
    # means most random event streams never even reach a real UPDATE
    # decision, blocking-instance or not -- 30 seeds of BLOCKING_INSTANCE
    # (genuine physical blocking, high uncertainty) produced zero
    # observable differences for either h_f or lam. That is a benchmark
    # calibration fact (already reported in Task 26), not evidence the
    # override is broken. So verify the plumbing directly: spy on
    # sarcrp_core.replan and assert run_episode actually calls it with the
    # h_f/lam values it was given.
    import sarcrp.simulator as simulator_module
    original_replan = simulator_module.replan
    captured = {}

    def spy_replan(*args, **kwargs):
        captured.update(kwargs)
        return original_replan(*args, **kwargs)

    monkeypatch.setattr(simulator_module, "replan", spy_replan)
    run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(0), h_f=2, lam=0.3)
    assert captured.get("h_f") == 2
    assert captured.get("lam") == 0.3


def test_episode_metrics_reports_the_new_fields():
    metrics = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(0))
    assert metrics.stability_cost_mean >= 0.0
    assert 0.0 <= metrics.invalid_rate <= 1.0
    assert 0.0 <= metrics.timeout_rate <= 1.0
    assert metrics.runtime_p95_sec >= 0.0


def test_time_limit_sec_override_is_accepted():
    metrics = run_episode(SMALL_INSTANCE, method_name="static", rng=random.Random(0), time_limit_sec=1.0)
    assert metrics.total_cost_mean >= 0.0


@pytest.mark.skipif(
    not Path(__file__).parent.parent.joinpath("external", "CRP_RL").is_dir(),
    reason="CRP_RL not cloned (see external/README.md)",
)
def test_run_episode_supports_full_reopt_crp_rl_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="full_reopt_crp_rl", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0
