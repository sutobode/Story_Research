"""A second scale instance, built with the identical deterministic recipe
as generate_crp_rl_scale_instance.py (bottom-first round-robin, same
[35, 70]-container CRP_RL training-range target), but different
dimensions (11 stacks x 4 containers = 44, vs. the original's 10x5=50).

Needed for Scenario E (run_existence_proof.py): the existence-proof
report found that only ONE specific queue position (the very last
container in a bottom-first round-robin retrieval order) reliably
produces a real, positive candidate-repair gain on
crp_rl_scale_instance.json -- promoting any other position gave exactly
zero gain across every seed tested, even from a pristine, never-replanned
plan. Chaining two forced events on the SAME instance therefore cannot
give the lookahead margin (carried_gain) a second real opportunity to
combine with. A second, independently-built instance with its OWN
last-position opportunity is used instead.

Dimensions were selected by sweeping several (num_stacks,
containers_per_stack) pairs built with this same deterministic recipe and
keeping the one whose own last-position gain (0.2119 on 18/20
REPORT_SEEDS, 0 on the other 2) stays reliably BELOW its own tau
(0.4649) by itself -- i.e. plain "sarcrp" alone never updates here
either, matching instance A's own sub-margin pattern, so this is a
second genuine near-miss, not a case that would already succeed without
the lookahead margin's help."""
import json
from pathlib import Path

NUM_STACKS = 11
CONTAINERS_PER_STACK = 4  # 11 * 4 = 44 containers, inside [35, 70]
MAX_TIER = 5  # headroom above 4 for relocations


def build_instance() -> dict:
    stacks = []
    per_stack_containers = []
    container_id = 1
    for s in range(NUM_STACKS):
        containers = [f"C{c:03d}" for c in range(container_id, container_id + CONTAINERS_PER_STACK)]
        container_id += CONTAINERS_PER_STACK
        per_stack_containers.append(containers)
        stacks.append({"id": f"S{s + 1}", "containers": containers, "max_tier": MAX_TIER})

    retrieval_order = []
    for tier in range(CONTAINERS_PER_STACK):
        for containers in per_stack_containers:
            retrieval_order.append(containers[tier])

    return {
        "instance_id": "crp_rl_scale_fairness_44b",
        "layout": {"num_stacks": NUM_STACKS, "max_tier": MAX_TIER},
        "stacks": stacks,
        "initial_retrieval_order": retrieval_order,
        "t_steps": 60,
        "uncertainty_level": "medium",
    }


if __name__ == "__main__":
    instance = build_instance()
    out_path = Path(__file__).parent / "crp_rl_scale_instance_b.json"
    out_path.write_text(json.dumps(instance, indent=2))
    total = sum(len(s["containers"]) for s in instance["stacks"])
    print(f"Wrote {out_path} with {total} containers (target range: 35-70)")
