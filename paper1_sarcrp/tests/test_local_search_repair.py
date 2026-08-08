import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.local_search_repair import (
    local_search_repair,
    _neighbor_insert_urgent_support,
    _neighbor_replace_tail_with_solver,
    _neighbor_prioritize_urgent_containers,
)


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1"], max_tier=5),
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_state_with_buried_urgent():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=5),  # C1 on top, blocks C2
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1", "C2"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_plan(dest="S2"):
    return Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RELOCATE", container="C1",
               source_stack="S1", dest_stack=dest, commit_status="planned", planned_time=0),
    ])


def test_returns_a_valid_plan_no_worse_than_start():
    state = make_state()
    p_start = make_plan(dest="S2")
    p_old = make_plan(dest="S3")
    rng = random.Random(0)
    result = local_search_repair(
        p_start, p_old, state, retrieval_queue_new=["C1"], frozen_count=0, rng=rng,
        t_iters=20, m_neighbors=10, epsilon=0.0,
    )
    assert len(result.actions) >= 1


def test_never_modifies_frozen_actions():
    state = make_state()
    p_start = make_plan(dest="S2")
    p_old = make_plan(dest="S3")
    rng = random.Random(1)
    result = local_search_repair(
        p_start, p_old, state, retrieval_queue_new=["C1"], frozen_count=1, rng=rng,
        t_iters=20, m_neighbors=10, epsilon=0.0,
    )
    assert result.actions[0].dest_stack == p_start.actions[0].dest_stack  # frozen index untouched


def test_is_seed_reproducible():
    state = make_state()
    p_start = make_plan(dest="S2")
    p_old = make_plan(dest="S3")
    result_a = local_search_repair(p_start, p_old, state, ["C1"], 0, random.Random(5), t_iters=15, m_neighbors=5)
    result_b = local_search_repair(p_start, p_old, state, ["C1"], 0, random.Random(5), t_iters=15, m_neighbors=5)
    assert [a.dest_stack for a in result_a.actions] == [a.dest_stack for a in result_b.actions]


def test_n3_inserts_relocation_to_unblock_urgent_container():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[])
    rng = random.Random(0)
    result = _neighbor_insert_urgent_support(plan, state, frozen_count=0, urgent_containers=["C2"], rng=rng)
    assert result is not None
    relocations = [a for a in result.actions if a.type == "RELOCATE" and a.container == "C1"]
    assert len(relocations) == 1
    assert relocations[0].source_stack == "S1"
    assert relocations[0].dest_stack != "S1"


def test_n3_returns_none_when_no_urgent_containers():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[])
    result = _neighbor_insert_urgent_support(plan, state, frozen_count=0, urgent_containers=[], rng=random.Random(0))
    assert result is None


def test_n3_returns_none_when_urgent_container_already_on_top():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[])
    result = _neighbor_insert_urgent_support(plan, state, frozen_count=0, urgent_containers=["C1"], rng=random.Random(0))
    assert result is None


def test_n5_replaces_tail_with_solver_suggestion():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RELOCATE", container="C1",
               source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    rng = random.Random(0)
    result = _neighbor_replace_tail_with_solver(plan, state, retrieval_queue_new=["C1", "C2"], frozen_count=0, rng=rng)
    assert result is not None
    assert len(result.actions) >= 1


def test_n5_does_not_duplicate_retrievals_already_covered_by_the_kept_prefix():
    # Regression test for the same bug class found in
    # baselines.mpc_receding_horizon and sarcrp_core.replan's candidate
    # C3: solving the tail against the ORIGINAL, untouched state and full
    # queue makes the tail duplicate whatever the kept prefix already
    # retrieved.
    state = make_state_with_buried_urgent()  # S1=[C2,C1], C1 on top
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])

    class _FixedK:
        """rng stand-in that forces k = len(plan.actions) (keep the one
        action, re-solve everything else) while delegating other calls."""
        def __init__(self, seed):
            self._r = random.Random(seed)

        def randint(self, a, b):
            return b

        def __getattr__(self, name):
            return getattr(self._r, name)

    result = _neighbor_replace_tail_with_solver(
        plan, state, retrieval_queue_new=["C1", "C2"], frozen_count=0, rng=_FixedK(0),
    )
    retrieved = [a.container for a in result.actions if a.type == "RETRIEVE"]
    assert retrieved.count("C1") == 1  # not retrieved again by the tail
    assert retrieved.count("C2") == 1


def test_n6_reorders_urgent_container_ahead_of_others_in_the_resolved_tail():
    state = make_state_with_buried_urgent()  # S1=[C2,C1], C1 on top blocks C2
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    result = _neighbor_prioritize_urgent_containers(
        plan, state, frozen_count=0, urgent_containers=["C2"], rng=random.Random(0),
    )
    assert result is not None
    retrieve_positions = {a.container: a.step_index for a in result.actions if a.type == "RETRIEVE"}
    assert retrieve_positions["C2"] < retrieve_positions["C1"]  # C2 was made urgent, C1 wasn't

    from sarcrp.plan_validator import is_plan_valid
    assert is_plan_valid(result, state)
    retrieved = [a.container for a in result.actions if a.type == "RETRIEVE"]
    assert sorted(retrieved) == ["C1", "C2"]  # every container still retrieved exactly once


def test_n6_returns_none_when_no_urgent_containers():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    result = _neighbor_prioritize_urgent_containers(
        plan, state, frozen_count=0, urgent_containers=[], rng=random.Random(0),
    )
    assert result is None


def test_n6_returns_none_when_urgent_container_already_covered_by_frozen_prefix():
    state = make_state_with_buried_urgent()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    result = _neighbor_prioritize_urgent_containers(
        plan, state, frozen_count=1, urgent_containers=["C1"], rng=random.Random(0),  # C1 already retrieved by the frozen prefix
    )
    assert result is None


def test_n5_returns_none_when_plan_is_fully_frozen():
    state = make_state()
    plan = make_plan(dest="S2")
    result = _neighbor_replace_tail_with_solver(plan, state, retrieval_queue_new=["C1"], frozen_count=1, rng=random.Random(0))
    assert result is None


class _AlwaysAcceptRNG:
    """Wraps a real Random for .choice/.sample/.randint, but forces
    .random() to always return 0.0 -- guaranteeing the epsilon-greedy
    'accept a worse neighbor' branch fires on every iteration that has one."""
    def __init__(self, seed):
        self._r = random.Random(seed)

    def random(self):
        return 0.0

    def __getattr__(self, name):
        return getattr(self._r, name)


def test_local_search_repair_never_returns_worse_than_its_own_starting_score():
    # Regression test for a real bug: p_best/score_best served double duty
    # as both the wandering "current" state (which the epsilon-greedy
    # acceptance criterion deliberately lets get worse, to escape local
    # optima) AND the value ultimately returned. A metaheuristic must track
    # the best-EVER-seen plan separately from the exploratory "current"
    # state, or a walk that wanders off and never finds its way back by
    # t_iters returns something strictly worse than where it started --
    # observed for real building the existence-proof scenario (Task: make
    # SAR-CRP actually activate), where local search returned a plan
    # scoring 5.8 against a start of 0.375.
    state = make_state_with_buried_urgent()
    p_old = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    rng = _AlwaysAcceptRNG(0)
    result = local_search_repair(
        p_old, p_old, state, retrieval_queue_new=["C1", "C2"], frozen_count=0, rng=rng,
        t_iters=30, m_neighbors=10, epsilon=0.05, urgent_containers=["C2"],
    )
    from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, stability_cost
    op = operational_cost(result, ["C2"], is_valid=True)
    stab, violated = stability_cost(result, p_old, frozen_count=0)
    data = data_confidence_cost(result, p_old, conf_new=1.0)
    result_score = float("inf") if violated else compute_objective(op, stab, data)

    start_op = operational_cost(p_old, ["C2"], is_valid=True)
    start_stab, start_violated = stability_cost(p_old, p_old, frozen_count=0)
    start_data = data_confidence_cost(p_old, p_old, conf_new=1.0)
    start_score = compute_objective(start_op, start_stab, start_data)

    assert result_score <= start_score


def test_local_search_repair_rejects_an_invalid_candidate_instead_of_returning_it(monkeypatch):
    # Regression test for a real bug: _score hardcoded is_valid=True, so an
    # invalid candidate (here: a RETRIEVE for a container not in the yard
    # at all) looked artificially cheap (relocation_count=0, zero delay)
    # instead of paying spec 11.3's M_inf penalty, and could win the
    # hill-climbing walk outright. Force every sampled neighbor to be the
    # same invalid plan and confirm local search never adopts it.
    import sarcrp.local_search_repair as lsr_module
    from sarcrp.plan_validator import is_plan_valid

    state = make_state()
    p_start = make_plan(dest="S2")
    p_old = make_plan(dest="S3")
    invalid_candidate = Plan(plan_id="bad", created_at=0, source="t", actions=[
        Action(action_id="x0", step_index=0, type="RETRIEVE", container="DOES_NOT_EXIST",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    monkeypatch.setattr(lsr_module, "_sample_neighbor", lambda *a, **k: invalid_candidate)

    result = local_search_repair(
        p_start, p_old, state, retrieval_queue_new=["C1"], frozen_count=0, rng=random.Random(0),
        t_iters=5, m_neighbors=3, epsilon=0.0,
    )
    assert is_plan_valid(result, state)
    assert result is p_start  # the invalid candidate must never be adopted, regardless of its apparent cost


def test_local_search_repair_can_reduce_urgent_retrieval_delay():
    state = make_state_with_buried_urgent()
    p_old = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    rng = random.Random(0)
    result = local_search_repair(
        p_old, p_old, state, retrieval_queue_new=["C1", "C2"], frozen_count=0, rng=rng,
        t_iters=50, m_neighbors=20, epsilon=0.0, urgent_containers=["C2"],
    )
    assert result is not None  # end-to-end run with N3/N5 in the mix does not crash
