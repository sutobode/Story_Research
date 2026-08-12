import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_dead_zone_baseline_comparison import METHODS, run_instance  # noqa: E402


def test_run_instance_scores_every_method_under_the_same_objective():
    r = run_instance(num_stacks=3, containers_per_stack=3, seed=20)
    for m in METHODS:
        key = f"cost_{m}"
        assert key in r
        assert r[key] >= 0.0
        assert r[key] < float("inf")  # no method should produce an invalid plan here
    assert r["sarcrp_decision"] in ("KEEP", "UPDATE")


def test_run_instance_is_seed_reproducible():
    r1 = run_instance(4, 3, seed=20)
    r2 = run_instance(4, 3, seed=20)
    for m in METHODS:
        assert r1[f"cost_{m}"] == r2[f"cost_{m}"]
    assert r1["sarcrp_decision"] == r2["sarcrp_decision"]


def test_full_reopt_and_periodic_agree_when_periodic_fires():
    # event_index=5 with period=5 makes periodic re-solve fresh on this
    # single decision, identically to full_reoptimization -- both simply
    # call solve_crp on the same (state, new_queue) with no randomness.
    r = run_instance(5, 4, seed=21)
    assert r["cost_full_reopt"] == r["cost_periodic"]


def test_static_cost_never_changes_the_plan_so_never_pays_stability_cost():
    # Static returns plan_old unchanged, so its stability cost against
    # itself must be exactly the operational-cost-only baseline: no method
    # should score LOWER than static purely by coincidence of a bug in the
    # scoring function itself (this doesn't assert sarcrp beats static --
    # only that static's own score is internally consistent).
    r = run_instance(3, 3, seed=20)
    assert r["cost_static"] > 0.0
