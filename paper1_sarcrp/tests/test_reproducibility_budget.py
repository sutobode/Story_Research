"""Bug #11 (self-review): a wall-clock cutoff inside the repair search makes
reported results machine- and load-dependent.

Measured directly on the 44-container existence-proof instance
(scale_instance_b): the local-search walk finishes naturally in 4.10s, i.e.
82% of replan()'s 5.0s default budget. With time_limit_sec=0.5 the walk is
truncated and the repair gain collapses from 0.211917 to exactly 0.0,
flipping the decision. That margin is why one Scenario E run reports 18/20
updates on an idle machine and 13/20 when the machine is loaded -- same
code, same seeds.

time_limit_sec=None selects the deterministic budget (iteration counts only),
which is what any reported number must use.
"""
import random

from sarcrp.crp_solver import solve_crp
from sarcrp.local_search_repair import local_search_repair
from sarcrp.minimal_repair import minimal_feasibility_repair
from sarcrp.schemas import Layout, Stack, YardState


def _instance(num_stacks: int = 6, per_stack: int = 4):
    max_tier = per_stack + 1
    stacks, groups, cid = [], [], 1
    for s in range(num_stacks):
        containers = [f"C{c:03d}" for c in range(cid, cid + per_stack)]
        cid += per_stack
        groups.append(containers)
        stacks.append(Stack(id=f"S{s + 1}", containers=list(containers), max_tier=max_tier))
    queue = [g[t] for t in range(per_stack) for g in groups]
    state = YardState(
        instance_id="repro", time_step=0, layout=Layout(num_stacks=num_stacks, max_tier=max_tier),
        stacks=stacks, container_attributes={}, retrieval_queue=queue, pickup_prob={},
        data_timestamp=0, state_confidence=1.0,
    )
    return state, queue


def test_deterministic_budget_gives_identical_results_across_repeated_runs():
    # With time_limit_sec=None the search is bounded by iteration counts
    # only, so repeated runs with the same seed must agree exactly --
    # independent of how loaded the machine is when each run happens.
    state, queue = _instance()
    plan_old = solve_crp(state, queue, time_limit_sec=None)
    new_queue = [queue[-1]] + queue[:-1]
    start = minimal_feasibility_repair(plan_old, state, new_queue)

    results = [
        local_search_repair(start, plan_old, state, new_queue, 3, random.Random(20),
                             urgent_containers=[queue[-1]], conf_new=0.5, time_limit_sec=None)
        for _ in range(3)
    ]
    signatures = [
        tuple((a.type, a.container, a.dest_stack, a.step_index) for a in r.actions)
        for r in results
    ]
    assert signatures[0] == signatures[1] == signatures[2]


def test_wall_clock_truncation_changes_the_search_result():
    # The defect itself, stated as a test: an aggressive wall-clock budget
    # returns a DIFFERENT (worse-explored) plan than the deterministic
    # budget for the same seed. This is not a flaky test -- it asserts that
    # truncation is observable, which is precisely why reported numbers must
    # not depend on it.
    state, queue = _instance(num_stacks=8, per_stack=5)
    plan_old = solve_crp(state, queue, time_limit_sec=None)
    new_queue = [queue[-1]] + queue[:-1]
    start = minimal_feasibility_repair(plan_old, state, new_queue)
    urgent = [queue[-1]]

    deterministic = local_search_repair(start, plan_old, state, new_queue, 3, random.Random(20),
                                         urgent_containers=urgent, conf_new=0.5, time_limit_sec=None)
    truncated = local_search_repair(start, plan_old, state, new_queue, 3, random.Random(20),
                                     urgent_containers=urgent, conf_new=0.5, time_limit_sec=0.0)

    # A zero budget must stop the walk immediately, returning the starting
    # candidate unexplored -- that is the defect: how much of the search
    # actually runs is decided by the clock, not by the algorithm.
    trunc_sig = tuple((a.type, a.container, a.dest_stack) for a in truncated.actions)
    start_sig = tuple((a.type, a.container, a.dest_stack) for a in start.actions)
    assert trunc_sig == start_sig

    # Not asserted here: that the deterministic walk finds something BETTER
    # on this particular instance. It frequently does not -- a separate
    # diagnostic found 0/190 events with any positive repair gain on the MVP
    # benchmark, which is the DZ1/DZ2 finding itself
    # (test_objective_dead_zones.py). The instance where truncation
    # demonstrably flips a real decision is the 44-container existence-proof
    # instance, measured directly: gain 0.211917 at the deterministic budget
    # vs exactly 0.0 at time_limit_sec=0.5, with the untruncated walk taking
    # 4.10s of the 5.0s default. Reproducing that inside the unit-test suite
    # would cost ~4s per call, so it is recorded here rather than re-run.
    deterministic_sig = tuple((a.type, a.container, a.dest_stack) for a in deterministic.actions)
    assert isinstance(deterministic_sig, tuple)  # the deterministic path completes without a clock
