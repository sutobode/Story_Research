"""Existence-proof experiment: Experiments 1/3/4 all show SAR-CRP tying
Static exactly (0/20 nonzero seed pairs, every uncertainty level, every
layout, every confidence level) because that suite's random event streams
almost never cross theta_impact=0.30 (SC4: mean impact 0.090). That is a
benchmark-calibration fact, not proof the trigger+repair mechanism itself
never works -- this script settles that question directly with two
deliberately engineered, deterministic events instead of a random stream.

Building and debugging this scenario caught three real implementation bugs
along the way (all fixed and committed separately, with their own tests):
I_blocking deviated from spec's union(old,new) top-k formula;
local_search_repair's epsilon-greedy walk could return a plan worse than
its own starting candidate (no best-ever-seen tracking); and candidate C3
(and N5, and baselines.mpc_receding_horizon) solved their "tail" against
the ORIGINAL, untouched state/queue instead of the state that results
after the frozen/kept prefix's own actions, wasting relocations on
already-covered containers.

Scenario A (small, 7 containers): TARGET sits buried at the bottom of a
stack under 2 blockers and is placed LAST in the initial retrieval order.
A forced URGENT_INSERTION promotes it to top priority. Impact crosses
theta_impact, but the achievable operational gain (one urgent container's
delay, on a 7-action plan) is smaller than the minimum stability +
data-confidence cost of any repair that touches the plan's tail at all --
SAR-CRP correctly (not buggily) still chooses KEEP.

Scenario B (50 containers, crp_rl_scale_instance.json -- already built
for the CRP_RL fairness comparison, reused here as-is, no new tuning):
the same forced-promotion pattern, at industrially-relevant scale. Impact
crosses threshold once the event's confidence drops to 0.5 (squarely
inside event_generator's own high-uncertainty confidence range,
0.20-0.80 -- not a cherry-picked value). A real improving candidate IS
found (~0.51 gain, ~0.83% of J_old) -- but it falls just under spec's own
1%-of-J_old fallback margin (tau = 0.01 * J(P_old)), confirmed across
every one of the 20 REPORT_SEEDS. This is the precise, well-characterized
boundary this suite's random benchmark never got close enough to see.
"""
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.baselines import full_reoptimization, static_plan  # noqa: E402
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.event_generator import generate_event_stream  # noqa: E402
from sarcrp.impact_estimator import compute_impact  # noqa: E402
from sarcrp.objective import (  # noqa: E402
    compute_objective, data_confidence_cost, operational_cost, relocation_count,
    retrieval_delay_norm, stability_cost,
)
from sarcrp.run_logging import log_run  # noqa: E402
from sarcrp.sarcrp_core import replan  # noqa: E402
from sarcrp.schemas import Layout, Stack, YardState  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS  # noqa: E402
from sarcrp.stats import cliffs_delta, wilcoxon_signed_rank  # noqa: E402

TARGET = "C07"
FORCED_EVENT_CONFIDENCE = 0.75  # plausible mid/high-uncertainty confidence for the forced event (not a flat 1.0)
SCALE_EVENT_CONFIDENCE = 0.5  # inside event_generator.CONFIDENCE_RANGE_BY_UNCERTAINTY["high"] = (0.20, 0.80)


def build_scenario() -> tuple[YardState, list[str]]:
    """7 containers, not 10: is_action_affected's rank-shift rule (spec 8.5,
    r_shift=5 default) only flags TARGET's own action when its shift is
    STRICTLY > 5, which requires TARGET's original queue position to be
    >= 6 (0-indexed) -- and both i_order's Kendall-tau ratio and i_plan's
    affected-fraction ratio for a single-item move-to-front get WEAKER as
    the queue grows longer (more unaffected pairs/actions dilute them). 7
    is the smallest queue where the affected-action term can fire at all,
    which keeps this scenario's Impact score away from the trigger
    threshold by margin rather than by luck."""
    stacks = [
        Stack(id="S1", containers=["C01", "C02"], max_tier=5),
        Stack(id="S2", containers=["C03", "C04"], max_tier=5),
        Stack(id="S3", containers=["C07", "C08", "C09"], max_tier=5),  # TARGET buried under 2
    ]
    layout = Layout(num_stacks=3, max_tier=5)
    initial_order = ["C02", "C01", "C04", "C03", "C09", "C08", "C07"]  # TARGET last (position 6)
    state = YardState(
        instance_id="existence_proof_urgent_unblock", time_step=0, layout=layout, stacks=stacks,
        container_attributes={}, retrieval_queue=initial_order, pickup_prob={},
        data_timestamp=0, state_confidence=1.0,
    )
    return state, initial_order


def build_scale_scenario() -> tuple[YardState, list[str], str]:
    """Reuses crp_rl_scale_instance.json (Task 34 Part C) as-is -- no new
    instance tuning. TARGET is whatever container the generator already
    placed last in the retrieval order (deterministic, not hand-picked)."""
    instance = json.loads((Path(__file__).parent / "instances" / "crp_rl_scale_instance.json").read_text())
    stacks = [Stack(id=s["id"], containers=list(s["containers"]), max_tier=s["max_tier"]) for s in instance["stacks"]]
    old_queue = list(instance["initial_retrieval_order"])
    state = YardState(
        instance_id=instance["instance_id"], time_step=0, layout=Layout(**instance["layout"]), stacks=stacks,
        container_attributes={}, retrieval_queue=old_queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    return state, old_queue, old_queue[-1]


def build_scale_scenario_b() -> tuple[YardState, list[str], str]:
    """Second, independently-built scale instance (Scenario E): same
    deterministic bottom-first round-robin recipe as build_scale_scenario,
    different dimensions (11 stacks x 4 = 44, vs. instance A's 10x5=50).
    Needed because only ONE specific queue-position/instance combination
    was found to produce a real repair gain -- promoting any other
    position on instance A gave exactly zero gain, even starting from a
    pristine plan, so a second forced event on instance A cannot give the
    lookahead margin a genuine second opportunity to combine with. This
    second instance's own dimensions were chosen (see
    generate_crp_rl_scale_instance_b.py) by sweeping several
    (num_stacks, containers_per_stack) pairs and keeping the one whose
    own gain (0.2119) stays reliably under its own tau (0.4649) by
    itself, matching instance A's sub-margin pattern -- so plain
    "sarcrp" must KEEP on instance B too, standing alone."""
    instance = json.loads((Path(__file__).parent / "instances" / "crp_rl_scale_instance_b.json").read_text())
    stacks = [Stack(id=s["id"], containers=list(s["containers"]), max_tier=s["max_tier"]) for s in instance["stacks"]]
    old_queue = list(instance["initial_retrieval_order"])
    state = YardState(
        instance_id=instance["instance_id"], time_step=0, layout=Layout(**instance["layout"]), stacks=stacks,
        container_attributes={}, retrieval_queue=old_queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    return state, old_queue, old_queue[-1]


def force_urgent_insertion(old_queue: list[str], target: str) -> list[str]:
    """A deterministic, hand-constructed URGENT_INSERTION -- not sampled by
    event_generator.apply_urgent_insertion -- so the scenario's magnitude
    is a design choice, not a seed artifact."""
    return [target] + [c for c in old_queue if c != target]


def _summarize(plan, plan_old, urgent: list[str], conf_new: float, label: str) -> dict:
    op = operational_cost(plan, urgent, is_valid=True)
    stab, violated = stability_cost(plan, plan_old, frozen_count=0)
    data = data_confidence_cost(plan, plan_old, conf_new=conf_new)
    j = compute_objective(op, 0.0 if violated else stab, data)
    return {
        "method": label,
        "relocation_count": relocation_count(plan),
        "retrieval_delay_norm_target": retrieval_delay_norm(plan, urgent),
        "operational_cost": op,
        "stability_cost": 0.0 if violated else stab,
        "total_cost_J": j,
    }


def run_once(seed: int) -> dict:
    """Scenario A (small, 7 containers)."""
    rng = random.Random(seed)
    state, old_queue = build_scenario()
    plan_old = solve_crp(state, old_queue, time_limit_sec=5.0)
    new_queue = force_urgent_insertion(old_queue, TARGET)
    urgent = [TARGET]

    impact = compute_impact(old_queue, new_queue, state, state, plan_old, conf_new=FORCED_EVENT_CONFIDENCE)
    decision = replan(state, plan_old, old_queue, new_queue, urgent, rng=rng, conf_new=FORCED_EVENT_CONFIDENCE, time_limit_sec=5.0)
    full_reopt_plan = full_reoptimization(state, new_queue, time_limit_sec=5.0)
    static_result = static_plan(plan_old)

    rows = [
        _summarize(static_result, plan_old, urgent, FORCED_EVENT_CONFIDENCE, "static"),
        _summarize(decision.plan, plan_old, urgent, FORCED_EVENT_CONFIDENCE, "sarcrp"),
        _summarize(full_reopt_plan, plan_old, urgent, FORCED_EVENT_CONFIDENCE, "full_reopt"),
    ]
    return {
        "seed": seed,
        "impact_total": impact.total,
        "impact_breakdown": {
            "i_order": impact.i_order, "i_target": impact.i_target,
            "i_blocking": impact.i_blocking, "i_plan": impact.i_plan, "i_conf": impact.i_conf,
        },
        "sarcrp_decision": decision.decision,
        "rows": rows,
    }


def run_once_scale(seed: int) -> dict:
    """Scenario B (50 containers, crp_rl_scale_instance.json)."""
    rng = random.Random(seed)
    state, old_queue, target = build_scale_scenario()
    plan_old = solve_crp(state, old_queue, time_limit_sec=5.0)
    new_queue = force_urgent_insertion(old_queue, target)
    urgent = [target]

    impact = compute_impact(old_queue, new_queue, state, state, plan_old, conf_new=SCALE_EVENT_CONFIDENCE)
    decision = replan(state, plan_old, old_queue, new_queue, urgent, rng=rng, conf_new=SCALE_EVENT_CONFIDENCE, time_limit_sec=5.0)
    gain = decision.j_old - decision.j_new
    tau = 0.01 * decision.j_old
    return {
        "seed": seed,
        "target": target,
        "impact_total": impact.total,
        "sarcrp_decision": decision.decision,
        "j_old": decision.j_old,
        "j_new": decision.j_new,
        "gain": gain,
        "tau": tau,
    }


def run_multistep_scenario(seed: int, extra_steps: int = 10) -> dict:
    """Scenario C: does SAR-CRP's real KEEP decision at the forced event
    (Scenario B) compound into higher cost over the REST of the episode,
    compared to a counterfactual that adopts the exact same candidate
    SAR-CRP already considered best -- forced through by zeroing tau_frac
    for that one decision only (not by changing candidate generation, the
    trigger, or any other parameter)? Both paths face the SAME subsequent
    random event stream (seeded), isolating the effect of the single
    forced-event decision from everything after it."""
    state, old_queue, target = build_scale_scenario()
    plan_initial = solve_crp(state, old_queue, time_limit_sec=5.0)
    forced_new_queue = force_urgent_insertion(old_queue, target)
    urgent = [target]

    subsequent_events = generate_event_stream(
        forced_new_queue, extra_steps, "medium", random.Random(seed), fixed_confidence=SCALE_EVENT_CONFIDENCE,
    )

    def run_path(tau_frac_at_forced_event: float) -> float:
        rng = random.Random(seed)
        decision = replan(
            state, plan_initial, old_queue, forced_new_queue, urgent, rng=rng,
            conf_new=SCALE_EVENT_CONFIDENCE, tau_frac=tau_frac_at_forced_event, time_limit_sec=5.0,
        )
        plan, queue = decision.plan, forced_new_queue
        total_cost = decision.j_new
        for event in subsequent_events:
            ev_urgent = [event.affected_containers[0]] if event.type == "URGENT_INSERTION" and event.affected_containers else []
            step_decision = replan(
                state, plan, queue, event.new_queue, ev_urgent, rng=rng,
                conf_new=event.confidence, time_limit_sec=5.0,  # default tau_frac=0.01 for every later step
            )
            total_cost += step_decision.j_new
            plan, queue = step_decision.plan, event.new_queue
        return total_cost

    real_total = run_path(tau_frac_at_forced_event=0.01)  # SAR-CRP's actual behavior (KEEP, per Scenario B)
    counterfactual_total = run_path(tau_frac_at_forced_event=0.0)  # forced to adopt the considered-best candidate
    return {
        "seed": seed,
        "real_total": real_total,
        "counterfactual_total": counterfactual_total,
        "counterfactual_better": counterfactual_total < real_total,
        "diff": real_total - counterfactual_total,
    }


def run_lookahead_validation(seed: int, extra_steps: int = 10) -> dict:
    """Validates sarcrp_core._apply_fallback_margin's carried_gain
    mechanism for real, not just via Scenario C's manual tau_frac=0
    override: runs the SAME forced-event-then-random-continuation episode
    twice, once with plain SAR-CRP (carried_gain never threaded,
    tau_frac=0.01 throughout, matching the "sarcrp" method) and once with
    the lookahead margin (carried_gain threaded from the very first
    decision onward, tau_frac=0.01 throughout -- no manual override
    anywhere, matching the "sarcrp_lookahead" method). Both face the
    identical subsequent event stream."""
    state, old_queue, target = build_scale_scenario()
    plan_initial = solve_crp(state, old_queue, time_limit_sec=5.0)
    forced_new_queue = force_urgent_insertion(old_queue, target)
    urgent = [target]

    subsequent_events = generate_event_stream(
        forced_new_queue, extra_steps, "medium", random.Random(seed), fixed_confidence=SCALE_EVENT_CONFIDENCE,
    )

    def run_path(use_lookahead: bool) -> float:
        rng = random.Random(seed)
        carried_gain = 0.0
        decision = replan(
            state, plan_initial, old_queue, forced_new_queue, urgent, rng=rng,
            conf_new=SCALE_EVENT_CONFIDENCE, carried_gain=carried_gain, time_limit_sec=5.0,
        )
        plan, queue = decision.plan, forced_new_queue
        total_cost = decision.j_new
        carried_gain = decision.carried_gain_next if use_lookahead else 0.0
        for event in subsequent_events:
            ev_urgent = [event.affected_containers[0]] if event.type == "URGENT_INSERTION" and event.affected_containers else []
            step_decision = replan(
                state, plan, queue, event.new_queue, ev_urgent, rng=rng,
                conf_new=event.confidence, time_limit_sec=5.0, carried_gain=carried_gain,
            )
            total_cost += step_decision.j_new
            plan, queue = step_decision.plan, event.new_queue
            carried_gain = step_decision.carried_gain_next if use_lookahead else 0.0
        return total_cost

    myopic_total = run_path(use_lookahead=False)
    lookahead_total = run_path(use_lookahead=True)
    return {
        "seed": seed,
        "myopic_total": myopic_total,
        "lookahead_total": lookahead_total,
        "lookahead_better": lookahead_total < myopic_total,
        "diff": myopic_total - lookahead_total,
    }


def run_scenario_e(seed: int, carried_gain_cap: float | None = None, carried_gain_decay: float = 1.0) -> dict:
    """Scenario E: a statistically-powered comparison, not a single
    anecdote. Chains two INDEPENDENT forced single-event opportunities
    (instance A: build_scale_scenario; instance B:
    build_scale_scenario_b) into one synthetic two-decision episode, and
    compares plain "sarcrp" (each decision independent, carried_gain
    never threaded) against "sarcrp_lookahead" (carried_gain threaded
    from event A's outcome into event B's decision) -- both using the
    SAME default tau_frac=0.01 throughout, no manual override anywhere.
    Each instance's own gain individually stays under its own tau
    (verified separately for both instances), so plain "sarcrp" must
    KEEP at both events on every seed; the question this answers is
    whether carrying A's foregone gain into B's decision is enough to
    cross B's own margin, across many seeds rather than one.

    carried_gain_cap/carried_gain_decay (both default to the validated
    mechanism's exact behavior, None/1.0) are R1.2's ablation hooks -- see
    run_carried_gain_ablation.py, which reruns this scenario under more
    conservative capped/decayed variants to check whether the win above
    is an artifact of the carry being allowed to accumulate unbounded."""
    state_a, old_queue_a, target_a = build_scale_scenario()
    plan_a = solve_crp(state_a, old_queue_a, time_limit_sec=5.0)
    new_queue_a = force_urgent_insertion(old_queue_a, target_a)
    urgent_a = [target_a]

    state_b, old_queue_b, target_b = build_scale_scenario_b()
    plan_b = solve_crp(state_b, old_queue_b, time_limit_sec=5.0)
    new_queue_b = force_urgent_insertion(old_queue_b, target_b)
    urgent_b = [target_b]

    def _realized_cost(decision) -> float:
        # decision.j_new reports the best CONSIDERED candidate's score in
        # both branches of Step 8 (it feeds the tau comparison itself) --
        # not the cost of whichever plan is actually in effect afterward.
        # On KEEP, the plan actually kept is plan_old (cost j_old); only on
        # UPDATE does the realized cost equal j_new (=j_best, now adopted).
        return decision.j_old if decision.decision == "KEEP" else decision.j_new

    def run_path(use_lookahead: bool, carried_gain_cap: float | None = None, carried_gain_decay: float = 1.0) -> dict:
        rng = random.Random(seed)
        decision_a = replan(state_a, plan_a, old_queue_a, new_queue_a, urgent_a, rng=rng,
                             conf_new=SCALE_EVENT_CONFIDENCE, time_limit_sec=5.0,
                             carried_gain_cap=carried_gain_cap, carried_gain_decay=carried_gain_decay)
        carried = decision_a.carried_gain_next if use_lookahead else 0.0
        decision_b = replan(state_b, plan_b, old_queue_b, new_queue_b, urgent_b, rng=rng,
                             conf_new=SCALE_EVENT_CONFIDENCE, time_limit_sec=5.0, carried_gain=carried,
                             carried_gain_cap=carried_gain_cap, carried_gain_decay=carried_gain_decay)
        total_cost = _realized_cost(decision_a) + _realized_cost(decision_b)
        return {"total_cost": total_cost, "decision_b": decision_b.decision}

    myopic = run_path(use_lookahead=False, carried_gain_cap=carried_gain_cap, carried_gain_decay=carried_gain_decay)
    lookahead = run_path(use_lookahead=True, carried_gain_cap=carried_gain_cap, carried_gain_decay=carried_gain_decay)
    return {
        "seed": seed,
        "myopic_total": myopic["total_cost"],
        "lookahead_total": lookahead["total_cost"],
        "myopic_decision_b": myopic["decision_b"],
        "lookahead_decision_b": lookahead["decision_b"],
        "diff": myopic["total_cost"] - lookahead["total_cost"],
        "lookahead_better": lookahead["total_cost"] < myopic["total_cost"],
    }


def main():
    _start = time.monotonic()

    print("=== Scenario A: small (7 containers) ===")
    results_a = [run_once(seed) for seed in REPORT_SEEDS]
    print(f"Impact.total (deterministic event -> identical across seeds): {results_a[0]['impact_total']:.4f}")
    print(f"Impact breakdown: {results_a[0]['impact_breakdown']}")
    decisions_a = sorted({r["sarcrp_decision"] for r in results_a})
    print(f"SAR-CRP decisions across {len(REPORT_SEEDS)} seeds: {decisions_a}")
    for method in ("static", "sarcrp", "full_reopt"):
        js = [next(row["total_cost_J"] for row in r["rows"] if row["method"] == method) for r in results_a]
        delays = [next(row["retrieval_delay_norm_target"] for row in r["rows"] if row["method"] == method) for r in results_a]
        relocs = [next(row["relocation_count"] for row in r["rows"] if row["method"] == method) for r in results_a]
        print(f"{method}: J mean={sum(js) / len(js):.4f}, "
              f"retrieval_delay_norm(target) mean={sum(delays) / len(delays):.4f}, "
              f"relocations mean={sum(relocs) / len(relocs):.2f}")

    print("\n=== Scenario B: scale (50 containers, crp_rl_scale_instance.json) ===")
    results_b = [run_once_scale(seed) for seed in REPORT_SEEDS]
    print(f"target={results_b[0]['target']}, Impact.total={results_b[0]['impact_total']:.4f}")
    decisions_b = sorted({r["sarcrp_decision"] for r in results_b})
    print(f"SAR-CRP decisions across {len(REPORT_SEEDS)} seeds: {decisions_b}")
    gains = [r["gain"] for r in results_b]
    print(f"gain (J_old - J_new): mean={sum(gains) / len(gains):.4f}, max={max(gains):.4f}, "
          f"tau (1% of J_old)={results_b[0]['tau']:.4f}")

    print("\n=== Scenario C: multi-step cascading cost (10 extra steps after the forced event) ===")
    results_c = [run_multistep_scenario(seed) for seed in REPORT_SEEDS]
    better_count = sum(r["counterfactual_better"] for r in results_c)
    diffs = [r["diff"] for r in results_c]
    print(f"counterfactual (early-fix) better on {better_count}/{len(REPORT_SEEDS)} seeds")
    print(f"real_total - counterfactual_total: mean={sum(diffs) / len(diffs):.4f}, "
          f"min={min(diffs):.4f}, max={max(diffs):.4f}")

    print("\n=== Scenario D: lookahead margin validation (sarcrp vs sarcrp_lookahead, real mechanism) ===")
    results_d = [run_lookahead_validation(seed) for seed in REPORT_SEEDS]
    better_count_d = sum(r["lookahead_better"] for r in results_d)
    diffs_d = [r["diff"] for r in results_d]
    print(f"lookahead better on {better_count_d}/{len(REPORT_SEEDS)} seeds")
    print(f"myopic_total - lookahead_total: mean={sum(diffs_d) / len(diffs_d):.4f}, "
          f"min={min(diffs_d):.4f}, max={max(diffs_d):.4f}")

    print("\n=== Scenario E: statistically-powered lookahead-margin comparison (2 chained instances) ===")
    results_e = [run_scenario_e(seed) for seed in REPORT_SEEDS]
    myopic_totals = [r["myopic_total"] for r in results_e]
    lookahead_totals = [r["lookahead_total"] for r in results_e]
    updates_myopic = sum(r["myopic_decision_b"] == "UPDATE" for r in results_e)
    updates_lookahead = sum(r["lookahead_decision_b"] == "UPDATE" for r in results_e)
    better_count_e = sum(r["lookahead_better"] for r in results_e)
    wilcoxon_result = wilcoxon_signed_rank(lookahead_totals, myopic_totals)
    delta = cliffs_delta(lookahead_totals, myopic_totals)
    print(f"event B UPDATE rate: myopic={updates_myopic}/{len(REPORT_SEEDS)}, lookahead={updates_lookahead}/{len(REPORT_SEEDS)}")
    print(f"lookahead better on {better_count_e}/{len(REPORT_SEEDS)} seeds")
    print(f"Wilcoxon (lookahead vs myopic, paired by seed): p={wilcoxon_result.p_value:.6f}, "
          f"n_nonzero_pairs={wilcoxon_result.n_nonzero_pairs}/{wilcoxon_result.n_pairs}, Cliff's delta={delta:.3f}")

    log_run(
        "run_existence_proof.py",
        {
            "seeds": list(REPORT_SEEDS), "target_a": TARGET, "target_b": results_b[0]["target"],
            "scenario_e_wilcoxon_p": wilcoxon_result.p_value, "scenario_e_cliffs_delta": delta,
        },
        time.monotonic() - _start, [],
    )


if __name__ == "__main__":
    main()
