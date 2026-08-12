import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_lee_shin_dead_zone_fix import INSTANCES, METHODS, run_lee_instance  # noqa: E402


def test_run_lee_instance_scores_every_method_under_the_fixed_objective():
    r = run_lee_instance(INSTANCES[0], seed=20)
    for m in METHODS:
        key = f"cost_{m}"
        assert key in r
        assert r[key] >= 0.0
        assert r[key] < float("inf")
    assert r["sarcrp_decision"] in ("KEEP", "UPDATE")
    assert r["instance"] == INSTANCES[0]["label"]


def test_run_lee_instance_is_seed_reproducible():
    r1 = run_lee_instance(INSTANCES[1], seed=20)
    r2 = run_lee_instance(INSTANCES[1], seed=20)
    for m in METHODS:
        assert r1[f"cost_{m}"] == r2[f"cost_{m}"]
    assert r1["sarcrp_decision"] == r2["sarcrp_decision"]


def test_run_lee_instance_accepts_the_order_swap_event_kind():
    r = run_lee_instance(INSTANCES[0], seed=20, event_kind="order_swap")
    assert r["event_kind"] == "order_swap"
    for m in METHODS:
        assert r[f"cost_{m}"] >= 0.0
        assert r[f"cost_{m}"] < float("inf")
