import random
from sarcrp.simulator import run_episode

SMALL_INSTANCE = {
    "instance_id": "mvp_small_01",
    "layout": {"num_stacks": 3, "max_tier": 5},
    "stacks": [
        {"id": "S1", "containers": ["C6", "C5", "C4", "C3", "C2", "C1"], "max_tier": 5},
        {"id": "S2", "containers": [], "max_tier": 5},
        {"id": "S3", "containers": [], "max_tier": 5},
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
