from sarcrp.schemas import Action, Layout, Plan, Stack, YardState
from sarcrp.freeze_horizon import apply_frozen_prefix, split_plan


def make_plan(n):
    actions = [Action(action_id=f"a{i}", step_index=i, type="RELOCATE", container=f"C{i}",
                       source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=i)
               for i in range(n)]
    return Plan(plan_id="p", created_at=0, source="t", actions=actions)


def test_split_respects_h_f_default_3():
    plan = make_plan(6)
    frozen, tail = split_plan(plan, h_f=3)
    assert [a.step_index for a in frozen.actions] == [0, 1, 2]
    assert [a.step_index for a in tail.actions] == [3, 4, 5]


def test_split_with_h_f_larger_than_plan_freezes_everything():
    plan = make_plan(2)
    frozen, tail = split_plan(plan, h_f=5)
    assert len(frozen.actions) == 2
    assert len(tail.actions) == 0


def test_split_with_h_f_zero_freezes_nothing():
    plan = make_plan(3)
    frozen, tail = split_plan(plan, h_f=0)
    assert len(frozen.actions) == 0
    assert len(tail.actions) == 3


def test_apply_frozen_prefix_removes_retrieved_containers_from_the_shadow_queue():
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1", "C2"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    frozen = Plan(plan_id="p_frozen", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    shadow_state, remaining_queue = apply_frozen_prefix(state, frozen, retrieval_queue_new=["C1", "C2"])
    assert remaining_queue == ["C2"]  # C1 already retrieved by the frozen prefix
    assert shadow_state.stacks[0].containers == []  # C1 physically popped in the shadow state


def test_apply_frozen_prefix_reflects_relocations_in_the_shadow_state():
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1", "C2"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    frozen = Plan(plan_id="p_frozen", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RELOCATE", container="C1",
               source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=0),
    ])
    shadow_state, remaining_queue = apply_frozen_prefix(state, frozen, retrieval_queue_new=["C2", "C1"])
    assert remaining_queue == ["C2", "C1"]  # RELOCATE doesn't retrieve anything
    assert shadow_state.stacks[0].containers == ["C2"]  # C1 physically moved off S1
    assert shadow_state.stacks[1].containers == ["C1"]  # ...and onto S2


def test_apply_frozen_prefix_does_not_mutate_the_original_state():
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1"], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    frozen = Plan(plan_id="p_frozen", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    apply_frozen_prefix(state, frozen, retrieval_queue_new=["C1"])
    assert state.stacks[0].containers == ["C1"]  # original untouched
