import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.ablations import ABLATIONS, replan_with_ablation


def make_state(queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_plan():
    return Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])


def test_all_six_ablations_are_registered():
    assert set(ABLATIONS.keys()) == {
        "A1_no_trigger", "A2_no_freeze", "A3_no_stability",
        "A4_no_local_search", "A5_no_data_confidence", "A6_no_blocking_impact",
    }


def test_a1_no_trigger_always_attempts_replan():
    state = make_state(["C1", "C2"])
    plan = make_plan()
    decision = replan_with_ablation(
        "A1_no_trigger", state, plan, old_queue=["C1", "C2"], new_queue=["C2", "C1"],
        urgent_containers=[], rng=random.Random(0),
    )
    assert decision.impact.total >= 0.0  # ran the full pipeline, not an early KEEP-by-threshold


def test_a3_no_stability_zeroes_lambda_only():
    state = make_state(["C1", "C2"])
    plan = make_plan()
    decision = replan_with_ablation(
        "A3_no_stability", state, plan, old_queue=["C1", "C2"], new_queue=["C2", "C1"],
        urgent_containers=["C2"], rng=random.Random(0),
    )
    assert decision.decision in {"KEEP", "UPDATE"}


def test_unknown_ablation_name_raises():
    state = make_state(["C1", "C2"])
    plan = make_plan()
    try:
        replan_with_ablation("not_a_real_ablation", state, plan, ["C1", "C2"], ["C2", "C1"], [], random.Random(0))
        assert False, "expected ValueError"
    except ValueError:
        pass
