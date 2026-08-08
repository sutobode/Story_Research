from sarcrp.schemas import Layout, Stack, YardState, Action, Plan, RetrievalInformation, Event


def test_yard_state_round_trip():
    state = YardState(
        instance_id="inst_0001",
        time_step=0,
        layout=Layout(num_stacks=2, max_tier=5),
        stacks=[
            Stack(id="S1", containers=["C10", "C07", "C03"], max_tier=5),
            Stack(id="S2", containers=["C09", "C04"], max_tier=5),
        ],
        container_attributes={"C03": {"size": "40ft", "weight_class": "medium", "status": "available"}},
        retrieval_queue=["C01", "C02", "C03", "C04", "C05"],
        pickup_prob={"C01": 0.95, "C02": 0.80, "C03": 0.60},
        data_timestamp=0,
        state_confidence=1.0,
    )
    assert state.stacks[0].containers[-1] == "C03"  # top of stack per spec convention
    assert state.layout.num_stacks == 2


def test_action_and_plan():
    a1 = Action(action_id="a001", step_index=0, type="RELOCATE", container="C03",
                source_stack="S1", dest_stack="S3", commit_status="committed", planned_time=1)
    a2 = Action(action_id="a002", step_index=1, type="RETRIEVE", container="C01",
                source_stack="S4", dest_stack=None, commit_status="planned", planned_time=2)
    plan = Plan(plan_id="plan_0001", created_at=0, source="CRP_RL", actions=[a1, a2])
    assert len(plan.actions) == 2
    assert plan.actions[0].type == "RELOCATE"


def test_retrieval_information_and_event():
    info = RetrievalInformation(
        info_id="info_0001", timestamp=10,
        retrieval_queue=["C01", "C04", "C02", "C03", "C05"],
        pickup_prob={"C01": 0.95, "C04": 0.88}, urgent_containers=["C04"],
        confidence=0.85, source="synthetic_event_generator",
    )
    event = Event(
        event_id="e001", time_step=10, type="ORDER_SWAP", severity="medium",
        affected_containers=["C02", "C04"],
        old_queue=["C01", "C02", "C03", "C04", "C05"],
        new_queue=["C01", "C04", "C03", "C02", "C05"],
        confidence=0.85, timestamp_generated=10, timestamp_observed=10,
        metadata={"swap_distance": 2},
    )
    assert info.urgent_containers == ["C04"]
    assert event.metadata["swap_distance"] == 2
