from sarcrp.schemas import Layout, Stack, YardState
from sarcrp.crp_solver import solve_crp


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[
            Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=5),  # C1 on top
            Stack(id="S2", containers=[], max_tier=5),
            Stack(id="S3", containers=[], max_tier=5),
        ],
        container_attributes={}, retrieval_queue=["C1", "C2", "C3"],
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_retrieves_top_container_directly():
    state = make_state()
    plan = solve_crp(state, retrieval_queue=["C1", "C2", "C3"])
    assert plan.actions[0].type == "RETRIEVE"
    assert plan.actions[0].container == "C1"


def test_relocates_blockers_before_retrieving_buried_target():
    state = make_state()
    plan = solve_crp(state, retrieval_queue=["C3", "C2", "C1"])  # C3 is buried under C2, C1
    retrieve_order = [a.container for a in plan.actions if a.type == "RETRIEVE"]
    assert retrieve_order == ["C3", "C2", "C1"]
    relocations_before_c3 = [a for a in plan.actions if a.type == "RELOCATE"]
    assert len(relocations_before_c3) == 2  # must move C1 and C2 out of the way


def test_respects_forbidden_moves_constraint():
    state = make_state()
    constraints = {"forbidden_moves": [{"container": "C1", "dest_stack": "S2"}]}
    plan = solve_crp(state, retrieval_queue=["C3", "C2", "C1"], constraints=constraints)
    forbidden_hits = [a for a in plan.actions if a.type == "RELOCATE" and a.container == "C1" and a.dest_stack == "S2"]
    assert forbidden_hits == []


def test_time_limit_still_returns_a_plan():
    state = make_state()
    plan = solve_crp(state, retrieval_queue=["C3", "C2", "C1"], time_limit_sec=1.0)
    assert plan.actions  # doesn't crash / doesn't return empty under a generous limit
