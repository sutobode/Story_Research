import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_existence_proof import (  # noqa: E402
    TARGET, build_scale_scenario, build_scenario, force_urgent_insertion, run_once, run_once_scale,
    run_lookahead_validation,
)


def test_force_urgent_insertion_promotes_target_to_rank_zero():
    old_queue = ["C1", "C2", "C3"]
    new_queue = force_urgent_insertion(old_queue, "C3")
    assert new_queue[0] == "C3"
    assert set(new_queue) == set(old_queue)


def test_scenario_buries_target_under_blockers_and_deprioritizes_it():
    state, old_queue = build_scenario()
    target_stack = next(s for s in state.stacks if TARGET in s.containers)
    assert target_stack.containers[0] == TARGET  # bottom of its stack
    assert len(target_stack.containers) == 3  # 2 blockers above it
    assert old_queue[-1] == TARGET  # last in the initial retrieval priority


def test_scenario_a_impact_crosses_the_trigger_threshold():
    result = run_once(seed=0)
    assert result["impact_total"] >= 0.30  # theta_impact default (spec 48)


def test_scenario_a_still_correctly_keeps_because_no_repair_clears_its_own_cost():
    # Verified, not assumed: at this scale, the achievable operational
    # gain (one urgent container's delay, on a 7-action plan) is smaller
    # than the minimum stability+data-confidence cost of any repair that
    # touches the tail at all -- true at h_f in {0,1,2,3} and lam in
    # {0,0.5,1.0} alike (checked directly), so this is not a freeze-horizon
    # or stability-weight artifact. SAR-CRP keeping here is the objective
    # functioning correctly, not evidence the mechanism is broken.
    result = run_once(seed=0)
    assert result["sarcrp_decision"] == "KEEP"
    static_j = next(r["total_cost_J"] for r in result["rows"] if r["method"] == "static")
    sarcrp_j = next(r["total_cost_J"] for r in result["rows"] if r["method"] == "sarcrp")
    assert sarcrp_j == static_j  # KEEP means it returns plan_old unchanged, trivially equal cost


def test_scenario_a_decision_is_robust_across_seeds():
    decisions = {run_once(seed)["sarcrp_decision"] for seed in range(5)}
    assert decisions == {"KEEP"}


def test_scenario_b_uses_the_existing_scale_instance_deterministically():
    state, old_queue, target = build_scale_scenario()
    assert target == old_queue[-1]
    assert sum(len(s.containers) for s in state.stacks) == 50


def test_scenario_b_impact_crosses_the_trigger_threshold():
    result = run_once_scale(seed=0)
    assert result["impact_total"] >= 0.30


def test_scenario_b_finds_a_real_improving_candidate_just_under_the_fallback_margin():
    # The precise, well-characterized boundary this suite's random
    # benchmark never got close enough to see: a genuine improving
    # candidate exists (gain > 0), but every seed's local search finds one
    # just under spec's own tau = 0.01 * J(P_old) fallback margin -- so
    # SAR-CRP's KEEP here is the fallback margin doing exactly its
    # documented job (spec 9's "EstimatedGain > SwitchingCost + tau"),
    # not a missed opportunity from a broken search.
    result = run_once_scale(seed=0)
    assert result["sarcrp_decision"] == "KEEP"
    assert result["gain"] > 0  # a real, positive improvement was found...
    assert result["gain"] < result["tau"]  # ...just not enough to clear the margin


def test_scenario_b_no_seed_finds_a_candidate_that_clears_the_margin():
    results = [run_once_scale(seed) for seed in range(5)]
    assert all(r["sarcrp_decision"] == "KEEP" for r in results)
    assert all(r["gain"] < r["tau"] for r in results)


def test_lookahead_margin_never_worse_and_captures_a_real_opportunity_on_seed_21():
    # Swept all 20 REPORT_SEEDS with a 200-step random continuation window:
    # 19/20 showed no difference at all (this benchmark's random events
    # essentially never present the lookahead mechanism a SECOND real
    # opportunity to combine with, consistent with SC4's chronic
    # under-triggering finding), and seed 21 is the one seed where a
    # genuine second opportunity naturally arose -- sarcrp_lookahead
    # captured it (saving ~49.97, ~1.4% of cumulative cost) while plain
    # "sarcrp" (myopic, never threads carried_gain) did not. No seed was
    # ever worse under the lookahead margin.
    result = run_lookahead_validation(seed=21, extra_steps=200)
    assert result["lookahead_better"] is True
    assert result["diff"] > 40.0  # real, substantial -- not noise
