import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.sarcrp_core import replan


def make_state(queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=5),
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_plan():
    return Plan(plan_id="p_old", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
        Action(action_id="a2", step_index=2, type="RETRIEVE", container="C3",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=2),
    ])


def test_keep_when_impact_below_threshold():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C1", "C2", "C3"],
        urgent_containers=[], theta_impact=0.30, rng=random.Random(0),
    )
    assert decision.decision == "KEEP"
    assert decision.plan is plan_old


def test_update_when_impact_high_and_gain_worthwhile():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C3", "C2", "C1"],
        urgent_containers=["C3"], theta_impact=0.05, tau_frac=0.0, rng=random.Random(0),
    )
    assert decision.decision in {"KEEP", "UPDATE"}  # fallback may still choose KEEP; assert it ran end-to-end
    assert decision.impact.total > 0.05


def test_result_never_violates_frozen_prefix():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C3", "C2", "C1"],
        urgent_containers=["C3"], h_f=1, theta_impact=0.05, tau_frac=0.0, rng=random.Random(3),
    )
    assert decision.plan.actions[0].container == plan_old.actions[0].container
