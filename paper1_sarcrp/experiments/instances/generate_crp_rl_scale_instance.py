"""Generates a yard instance sized within CRP_RL's actual training
distribution (min_n_containers=35, max_n_containers=70, per
external/CRP_RL/baselines/test.py's `args`) so Task 33's greedy-vs-real-model
comparison is not testing the model outside its validated range -- every
other instance in this suite (10-24 containers) is too small for that
comparison to mean anything about the model's true quality. Deterministic,
no RNG: mirrors small_layout_mvp.json's fix (spec 20 SC1) by requesting
each stack's bottom container first, so every relocation is genuinely
necessary rather than the "already sorted" degenerate case."""
import json
from pathlib import Path

NUM_STACKS = 10
CONTAINERS_PER_STACK = 5  # 10 * 5 = 50 containers, inside [35, 70]
MAX_TIER = 6  # headroom above 5 for relocations


def build_instance() -> dict:
    stacks = []
    per_stack_containers = []
    container_id = 1
    for s in range(NUM_STACKS):
        containers = [f"C{c:03d}" for c in range(container_id, container_id + CONTAINERS_PER_STACK)]
        container_id += CONTAINERS_PER_STACK
        per_stack_containers.append(containers)
        stacks.append({"id": f"S{s + 1}", "containers": containers, "max_tier": MAX_TIER})

    # containers[0] = bottom (this schema's convention). Requesting tier 0
    # (bottom) across every stack first, round-robin, guarantees the
    # retrieval order never matches any stack's existing bottom-to-top order.
    retrieval_order = []
    for tier in range(CONTAINERS_PER_STACK):
        for containers in per_stack_containers:
            retrieval_order.append(containers[tier])

    return {
        "instance_id": "crp_rl_scale_fairness_50",
        "layout": {"num_stacks": NUM_STACKS, "max_tier": MAX_TIER},
        "stacks": stacks,
        "initial_retrieval_order": retrieval_order,
        "t_steps": 60,
        "uncertainty_level": "medium",
    }


if __name__ == "__main__":
    instance = build_instance()
    out_path = Path(__file__).parent / "crp_rl_scale_instance.json"
    out_path.write_text(json.dumps(instance, indent=2))
    total = sum(len(s["containers"]) for s in instance["stacks"])
    print(f"Wrote {out_path} with {total} containers (target range: 35-70)")
