import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.baselines import full_reoptimization  # noqa: E402
from sarcrp.objective import relocation_count  # noqa: E402
from sarcrp.schemas import Layout, Stack, YardState  # noqa: E402


def _build_state(instance: dict) -> YardState:
    stacks = [Stack(id=s["id"], containers=list(s["containers"]), max_tier=s["max_tier"]) for s in instance["stacks"]]
    return YardState(
        instance_id=instance["instance_id"], time_step=0, layout=Layout(**instance["layout"]), stacks=stacks,
        container_attributes={}, retrieval_queue=list(instance["initial_retrieval_order"]),
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def run_proxy_comparison(instance: dict, normal_timeout: float, extended_timeout: float = 300.0) -> dict:
    """spec 21.2: for instances too large for exhaustive search, Full
    Reoptimization run with a much longer timeout is an "offline
    high-quality proxy" for the optimum -- NEVER call this a true optimum
    in the report (spec 21.2's own explicit wording)."""
    state = _build_state(instance)
    queue = list(instance["initial_retrieval_order"])
    normal_plan = full_reoptimization(state, queue, time_limit_sec=normal_timeout)
    proxy_plan = full_reoptimization(state, queue, time_limit_sec=extended_timeout)
    normal_relocations = relocation_count(normal_plan)
    proxy_relocations = relocation_count(proxy_plan)
    return {
        "normal_timeout_relocations": normal_relocations,
        "offline_proxy_relocations": proxy_relocations,
        "gap_vs_proxy": (normal_relocations - proxy_relocations) / max(proxy_relocations, 1),
    }


def main():
    instances_dir = Path(__file__).parent / "instances"
    for layout_name, filename, normal_timeout in (("layout_b", "layout_b.json", 5.0), ("layout_c", "layout_c.json", 30.0)):
        instance = json.loads((instances_dir / filename).read_text())
        result = run_proxy_comparison(instance, normal_timeout=normal_timeout)
        print(f"{layout_name}: normal={result['normal_timeout_relocations']} "
              f"offline_proxy={result['offline_proxy_relocations']} "
              f"gap_vs_proxy={result['gap_vs_proxy']:.1%}")


if __name__ == "__main__":
    main()
