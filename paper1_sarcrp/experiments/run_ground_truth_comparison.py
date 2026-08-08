import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.ground_truth import exhaustive_solve  # noqa: E402
from sarcrp.objective import relocation_count  # noqa: E402
from sarcrp.schemas import Layout, Stack, YardState  # noqa: E402


def _build_state(instance: dict) -> YardState:
    stacks = [Stack(id=s["id"], containers=list(s["containers"]), max_tier=s["max_tier"]) for s in instance["stacks"]]
    return YardState(
        instance_id=instance["instance_id"], time_step=0, layout=Layout(**instance["layout"]), stacks=stacks,
        container_attributes={}, retrieval_queue=list(instance["initial_retrieval_order"]),
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def run_comparison(instance: dict, max_containers: int = 8) -> dict:
    """spec 21.1: optimality gap = (algorithm_relocations - optimal_relocations)
    / max(optimal_relocations, 1) on a small instance where exhaustive search
    is tractable. Reports the *initial static plan's* solve quality -- this
    experiment is about the underlying CRP solver, not the dynamic
    replanning layer, per spec 21's own framing ("kiem tra chat luong thuat
    toan")."""
    queue = list(instance["initial_retrieval_order"])
    state = _build_state(instance)

    optimal_plan = exhaustive_solve(state, queue, max_containers=max_containers)
    greedy_plan = solve_crp(state, queue, time_limit_sec=30.0)

    optimal_relocations = relocation_count(optimal_plan)
    greedy_relocations = relocation_count(greedy_plan)
    greedy_gap = (greedy_relocations - optimal_relocations) / max(optimal_relocations, 1)

    return {
        "optimal_relocations": optimal_relocations,
        "greedy_relocations": greedy_relocations,
        "greedy_gap": greedy_gap,
    }


def main():
    instance = json.loads((Path(__file__).parent / "instances" / "tiny_ground_truth.json").read_text())
    result = run_comparison(instance)
    print(f"Optimal relocations:  {result['optimal_relocations']}")
    print(f"Greedy relocations:   {result['greedy_relocations']}")
    print(f"Greedy optimality gap: {result['greedy_gap']:.1%}")


if __name__ == "__main__":
    main()
