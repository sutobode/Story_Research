import csv
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.event_generator import generate_event_stream  # noqa: E402
from sarcrp.simulator import _build_state, EpisodeMetrics  # noqa: E402
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.baselines import static_plan, full_reoptimization  # noqa: E402
from sarcrp.sarcrp_core import replan  # noqa: E402
from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, relocation_count, stability_cost  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS as SEEDS  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402

CONFIDENCE_LEVELS = (1.0, 0.7, 0.4, 0.2)  # spec 23 Experiment 4


def _run_one(instance: dict, method_name: str, fixed_confidence: float, rng: random.Random) -> EpisodeMetrics:
    """Same event/decision loop as simulator.run_episode, but with confidence
    pinned to `fixed_confidence` for every event instead of sampled from the
    uncertainty level -- spec 23 Experiment 4's whole point is isolating
    confidence's effect from severity/uncertainty."""
    queue = list(instance["initial_retrieval_order"])
    state = _build_state(instance, queue)
    plan = solve_crp(state, queue, time_limit_sec=5.0)
    events = generate_event_stream(queue, instance["t_steps"], instance["uncertainty_level"], rng, fixed_confidence=fixed_confidence)

    total_costs, op_costs, changed_total = [], [], 0
    for event in events:
        new_queue = event.new_queue
        urgent = [event.affected_containers[0]] if event.type == "URGENT_INSERTION" and event.affected_containers else []
        state.retrieval_queue = new_queue

        if method_name == "static":
            new_plan = static_plan(plan)
        elif method_name == "full_reopt":
            new_plan = full_reoptimization(state, new_queue, time_limit_sec=5.0)
        else:
            new_plan = replan(state, plan, queue, new_queue, urgent, rng=rng, conf_new=fixed_confidence).plan

        by_index_a = {a.step_index: a for a in new_plan.actions}
        by_index_b = {a.step_index: a for a in plan.actions}
        changed_total += sum(
            1 for i in set(by_index_a) | set(by_index_b)
            if by_index_a.get(i) is None or by_index_b.get(i) is None
            or by_index_a[i].container != by_index_b[i].container
        )

        op = operational_cost(new_plan, urgent, is_valid=True)
        stab, violated = stability_cost(new_plan, plan, frozen_count=0)
        data = data_confidence_cost(new_plan, plan, fixed_confidence)
        total_costs.append(compute_objective(op, 0.0 if violated else stab, data))
        op_costs.append(op)

        plan, queue = new_plan, new_queue

    # stability_cost_mean/runtime_p95_sec/invalid_rate/timeout_rate are not
    # tracked by this script's own loop (it reimplements run_episode's loop
    # rather than reusing it, to pin confidence per-event) -- 0.0 here only,
    # never cited as a real value in the report.
    return EpisodeMetrics(
        relocation_count_total=relocation_count(plan), changed_actions_total=changed_total,
        total_cost_mean=sum(total_costs) / len(total_costs) if total_costs else 0.0,
        operational_cost_mean=sum(op_costs) / len(op_costs) if op_costs else 0.0,
        stability_cost_mean=0.0, runtime_mean_sec=0.0, runtime_p95_sec=0.0,
        fallback_rate=0.0, invalid_rate=0.0, timeout_rate=0.0,
    )


def run_confidence_sweep(instance: dict, methods=("static", "full_reopt", "sarcrp"), seeds=SEEDS) -> list[dict]:
    rows = []
    for level in CONFIDENCE_LEVELS:
        for method in methods:
            for seed in seeds:
                metrics = _run_one(instance, method, level, random.Random(seed))
                rows.append({
                    "fixed_confidence": level, "method": method, "seed": seed,
                    "changed_actions_total": metrics.changed_actions_total,
                    "total_cost_mean": metrics.total_cost_mean,
                })
    return rows


def main():
    _start = time.monotonic()
    instance = json.loads((Path(__file__).parent / "instances" / "small_layout_mvp.json").read_text())
    rows = run_confidence_sweep(instance)
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "experiment4_results.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")

    log_run("run_experiment4.py", {"seeds": list(SEEDS), "confidence_levels": list(CONFIDENCE_LEVELS)},
            time.monotonic() - _start, [str(out_path)])


if __name__ == "__main__":
    main()
