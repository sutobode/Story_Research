import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from sweep_chained_instances import build_instance, check_candidate, force_urgent_insertion  # noqa: E402


def test_build_instance_matches_bottom_first_round_robin_recipe():
    state, queue, target = build_instance(num_stacks=3, containers_per_stack=2)
    assert sum(len(s.containers) for s in state.stacks) == 6
    assert len(queue) == 6
    # bottom-first round-robin: tier0 of every stack, then tier1 of every stack.
    assert queue == ["C001", "C003", "C005", "C002", "C004", "C006"]
    assert target == queue[-1] == "C006"


def test_force_urgent_insertion_promotes_target_to_front():
    new_queue = force_urgent_insertion(["C1", "C2", "C3"], "C3")
    assert new_queue[0] == "C3"
    assert set(new_queue) == {"C1", "C2", "C3"}


def test_check_candidate_reproduces_instance_a_own_gain_pattern():
    # Instance A (this report's own crp_rl_scale_instance.json) is 10x5=50
    # and its own standalone gain is documented as ~0.2119, tau ~0.4649,
    # reliably sub-margin. build_instance(10, 5) uses the identical
    # deterministic recipe and must reproduce that same real, if small,
    # sub-margin gain -- this is what run_existence_proof.py's own
    # separately-generated JSON instance already established, so it
    # doubles as a consistency check between the two constructions.
    results = check_candidate(10, 5, seeds=(20,))
    gain, tau = results[0]
    assert gain > 0.0
    assert gain < tau
