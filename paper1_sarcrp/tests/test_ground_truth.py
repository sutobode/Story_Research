import pytest
from sarcrp.schemas import Layout, Stack, YardState
from sarcrp.ground_truth import exhaustive_solve
from sarcrp.objective import relocation_count


def test_exhaustive_solve_finds_zero_relocations_when_already_sorted():
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=3),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=3)],
        container_attributes={}, retrieval_queue=["C1", "C2"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    plan = exhaustive_solve(state, retrieval_queue=["C1", "C2"])
    assert relocation_count(plan) == 0


def test_exhaustive_solve_finds_minimum_relocations_for_a_small_blocking_case():
    # S1 = [C3, C2, C1] (C1 top), need C3 first -> must relocate C1 and C2 (2 relocations minimum).
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=3),
        stacks=[Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=3), Stack(id="S2", containers=[], max_tier=3)],
        container_attributes={}, retrieval_queue=["C3", "C2", "C1"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    plan = exhaustive_solve(state, retrieval_queue=["C3", "C2", "C1"])
    assert relocation_count(plan) == 2
    retrieved = [a.container for a in plan.actions if a.type == "RETRIEVE"]
    assert retrieved == ["C3", "C2", "C1"]


def test_exhaustive_solve_raises_above_the_container_bound():
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=10),
        stacks=[Stack(id="S1", containers=[f"C{i}" for i in range(9)], max_tier=10)],
        container_attributes={}, retrieval_queue=[f"C{i}" for i in range(9)], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    with pytest.raises(ValueError):
        exhaustive_solve(state, retrieval_queue=[f"C{i}" for i in range(9)], max_containers=8)
