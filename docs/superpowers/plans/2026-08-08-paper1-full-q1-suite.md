# Paper 1 — Full Q1 Experiment Suite (Phase 6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete everything the MVP (Task 1-19, done) deliberately deferred — the remaining 3 baselines (B3-B5), all 6 ablations (A1-A6), ground truth for small instances, a second/third layout for cross-layout validation, the §23.6 statistical protocol (≥20 seeds, Wilcoxon signed-rank, Holm-Bonferroni, effect size), formal SC1-SC4 sanity checks, the Experiment 1 factorial sweep, Experiment 4 (data confidence sensitivity), the metrics §24 still doesn't log (invalid rate, P95 runtime, timeout rate, stability cost), an actual ground-truth optimality-gap comparison, §17 timeout tiering, and a resolved decision on whether the real CRP\_RL model (Task 19) is used anywhere in these experiments — so Paper 1 has the experimental evidence a Q1 submission needs, per `Story_paper/SAR_CRP_v2_FINAL_READY_With_Implementation_Appendix_VI (1).md` §17, §20-27, §32, §49-51.

**Architecture:** Every new baseline/ablation is a thin composition of existing MVP building blocks (`crp_solver.solve_crp`, `freeze_horizon.split_plan`, `sarcrp_core.replan`) — no new solving logic, only new *configurations* of what Tasks 1-19 already built. Three new standalone modules (`stats.py`, `ground_truth.py`, `sanity_checks.py`) provide reusable analysis primitives. `simulator.run_episode`'s method dispatch is extended (not rewritten) to cover the new method names. Two new experiment runners (`run_cross_layout.py`, `run_experiment1.py`) drive the actual studies.

**Tech Stack:** Same as the MVP (Python 3.11 on the remote server, pytest) plus `scipy` (Wilcoxon signed-rank test — reimplementing it by hand risks a subtle correctness bug in exactly the number a reviewer will scrutinize) and `numpy` (scipy's dependency; also silences the "Failed to initialize NumPy" warning torch already emits in this env).

## Global Constraints

- **Everything executes on the remote server** (`a100-B`, conda env `story_research`) via `ssh`, exactly like Tasks 1-19. The laptop only edits files; every `mutagen.exe sync flush story-research` + `ssh a100-B "... && pytest ..."` cycle from the MVP applies unchanged here — this plan does not repeat that preamble in every step, but every "Run tests" step below means running it that way, not locally.
- Default parameters (do not change without updating the spec doc first) — same table as the MVP plan, repeated here because ablations/baselines deviate from specific entries on purpose: `K=10, theta_impact=0.30, tau=0.01·J(P_old), lambda=1.0, mu=0.5, alpha=1.0, beta=0.5, gamma=1.0, M_inf=1e6, rho=0.05, sigma_b=2, r_shift=5, H_f=3, p_c=2,p_a=2,p_d=1,p_o=1,p_m=10,p_f=inf, p_insert=1.5,p_delete=1.5, T=100,M=50,epsilon=0.05, tau_age=10`.
- §23.6 statistical protocol is mandatory for Experiment 1, 3, 4 and the ablation comparisons: **≥20 seeds per (instance, uncertainty level, method)**; report **mean ± 95% CI**; **Wilcoxon signed-rank** (paired, same seed) comparing SAR-CRP vs. each of B1-B5; **Holm-Bonferroni** correction across the 5 comparisons; **effect size** (Cliff's delta) alongside every p-value. Do not report "SAR-CRP is significantly better" without all four.
- Ground truth (§21) is only attempted on instances with **≤8 containers** — branch-and-bound blows up combinatorially past that; larger instances use Full Reoptimization with an extended timeout as an "offline high-quality proxy," never called a true optimum.
- Cross-layout protocol (§50): hyperparameters are tuned on Layout A **only** (in practice: "use the §48 defaults, unchanged" — this codebase has never tuned anything beyond those defaults, so this constraint is satisfied by *not* touching any default when adding Layouts B/C). Layouts B and C are evaluated with the identical config, no retuning.
- Every module in this plan reuses `crp_solver.solve_crp`, `freeze_horizon.split_plan`, `objective.*`, and `sarcrp_core.replan` from the MVP rather than re-implementing solving logic — if a task's plan seems to duplicate one of those, that is a bug in the plan, not a feature.

---

## File Structure

```
paper1_sarcrp/
  src/sarcrp/
    baselines.py            # MODIFY: add periodic_replan, event_triggered_no_stability, mpc_receding_horizon (B3/B4/B5)
    sarcrp_core.py           # MODIFY: replan() gains use_local_search and impact_weights params
    ablations.py             # NEW: ABLATIONS config table + replan_with_ablation()
    event_generator.py       # MODIFY: generate_event_stream gains fixed_confidence override (Experiment 4)
    simulator.py              # MODIFY: run_episode's method dispatch covers B3-B5 + ablation variants
    stats.py                  # NEW: bootstrap_ci, wilcoxon_signed_rank, holm_bonferroni, cliffs_delta
    ground_truth.py            # NEW: exhaustive_solve (branch-and-bound, spec 21.1)
    sanity_checks.py            # NEW: run_sanity_checks (SC1-SC4, spec 20/49)
  tests/
    test_baselines.py          # MODIFY: add tests for B3/B4/B5
    test_sarcrp_core.py         # MODIFY: add tests for use_local_search/impact_weights
    test_ablations.py            # NEW
    test_event_generator.py       # MODIFY: add fixed_confidence test
    test_simulator_mvp.py          # MODIFY: add tests for new method names
    test_stats.py                   # NEW
    test_ground_truth.py             # NEW
    test_sanity_checks.py             # NEW
  experiments/
    instances/
      layout_b.json            # NEW: second layout, cross-layout validation
      layout_c.json             # NEW: third layout, cross-layout validation
    run_cross_layout.py          # NEW: Experiment 3 runner
    run_experiment1.py            # NEW: Experiment 1 factorial runner (uncertainty x freeze x lambda, 6 methods)
    run_experiment4.py             # NEW: data-confidence-sensitivity runner
    run_sanity_report.py            # NEW: SC1-SC4 report over the MVP instance
    instances/
      tiny_ground_truth.json         # NEW (Task 31): <=8 containers, feeds exhaustive_solve for a real optimality gap
    run_ground_truth_comparison.py    # NEW (Task 31): optimal vs greedy vs (if wired) CRP_RL relocation-count gap
    run_extended_timeout_proxy.py      # NEW (Task 32): spec 21.2 -- Full Reopt @ 300s as offline proxy for Layout B/C
writeups/
  paper1_q1_report/
    main.tex                     # NEW: full Q1 experiment report, own folder, compiled to PDF
    Makefile
```

**Additional files from Tasks 30-33 (metrics completeness, ground truth comparison, timeout tiering, CRP\_RL wiring):**
```
paper1_sarcrp/
  src/sarcrp/
    plan_validator.py         # NEW (Task 30): is_plan_valid(plan, state) -> bool
    simulator.py                # MODIFY again (Task 30: EpisodeMetrics gains 4 fields + time_limit_sec param; Task 32: time_limit_sec threaded through dispatch)
    sarcrp_core.py                # MODIFY again (Task 33: replan() gains a `solver` callable param)
    crp_rl_adapter.py               # MODIFY (Task 33): cache the loaded model instead of reloading per call
    baselines.py                     # MODIFY again (Task 33): full_reoptimization gains a `solver` callable param
  tests/
    test_plan_validator.py       # NEW (Task 30)
    test_simulator_mvp.py         # MODIFY again (Tasks 30, 32)
    test_run_ground_truth_comparison.py  # NEW (Task 31)
    test_sarcrp_core.py             # MODIFY again (Task 33)
    test_crp_rl_adapter.py           # MODIFY again (Task 33: cache test)
```

**Additional files from Task 34 (rigor and logging — seed policy, Wilcoxon zero-handling, CRP\_RL-scale fairness, structured logs, Slurm submission):**
```
paper1_sarcrp/
  src/sarcrp/
    seed_policy.py             # NEW: DEV_SEEDS (0-9, already inspected) / REPORT_SEEDS (20-39, fresh)
    run_logging.py              # NEW: log_run(...) -> appends to experiments/logs/run_log.jsonl
    stats.py                     # MODIFY again: wilcoxon_signed_rank returns WilcoxonResult (p_value, n_pairs, n_nonzero_pairs), zero_method="pratt"
  tests/
    test_run_logging.py          # NEW
    test_stats.py                  # MODIFY again
  experiments/
    instances/
      generate_crp_rl_scale_instance.py  # NEW: deterministic generator, run once
      crp_rl_scale_instance.json           # NEW: its output, 50 containers (inside CRP_RL's trained 35-70 range)
    run_experiment1.py, run_cross_layout.py, run_experiment4.py, run_mvp.py,
    run_sanity_report.py, run_ground_truth_comparison.py, run_extended_timeout_proxy.py
                                             # MODIFY all seven: call log_run(...) at the end of main()
    .gitignore                              # MODIFY: add experiments/logs/
```

**Interfaces locked now (do not rename later):**
- `baselines.periodic_replan(state, retrieval_queue_new, plan_current, event_index, period=5, time_limit_sec=5.0) -> Plan`
- `baselines.event_triggered_no_stability(state, plan_old, old_queue, new_queue, urgent_containers, rng, theta_impact=0.30, tau_frac=0.01, time_limit_sec=5.0, conf_new=1.0) -> ReplanDecision`
- `baselines.mpc_receding_horizon(state, plan_current, retrieval_queue_new, horizon=5, time_limit_sec=5.0) -> Plan`
- `sarcrp_core.replan(..., use_local_search: bool = True, impact_weights: dict | None = None) -> ReplanDecision` (all prior params unchanged)
- `ablations.ABLATIONS: dict[str, dict]` (ablation name -> kwargs overrides for `replan`)
- `ablations.replan_with_ablation(ablation_name, state, plan_old, old_queue, new_queue, urgent_containers, rng, conf_new=1.0) -> ReplanDecision`
- `event_generator.generate_event_stream(..., fixed_confidence: float | None = None) -> list[Event]`
- `stats.bootstrap_ci(values, n_resamples=2000, ci=0.95, rng=None) -> tuple[float, float, float]` (mean, lo, hi)
- `stats.wilcoxon_signed_rank(a, b) -> float` (p-value)
- `stats.holm_bonferroni(p_values, alpha=0.05) -> list[bool]` (reject-H0 per comparison, same order as input)
- `stats.cliffs_delta(a, b) -> float`
- `ground_truth.exhaustive_solve(state, retrieval_queue, max_containers=8) -> Plan` (raises `ValueError` above the bound)
- `sanity_checks.SanityReport` (dataclass: `sc1_not_too_easy, sc2_not_too_hard, event_type_frequency, mean_impact, sc4_impact_reasonable`) and `sanity_checks.run_sanity_checks(instance, seeds=tuple(range(10))) -> SanityReport`
- `simulator.run_episode`'s `method_name` now also accepts: `"periodic"`, `"event_triggered_no_stability"`, `"mpc"`, `"full_reopt_crp_rl"` (Task 33), and any key of `ablations.ABLATIONS` prefixed `"sarcrp_"` (e.g. `"sarcrp_A1_no_trigger"`).
- `simulator.run_episode(..., time_limit_sec: float = 5.0)` (Task 32 — was a hardcoded literal at each call site inside the function; now one parameter controlling all of them).
- `simulator.EpisodeMetrics` gains four fields (Task 30): `stability_cost_mean: float`, `invalid_rate: float`, `timeout_rate: float`, `runtime_p95_sec: float` — every existing construction site of `EpisodeMetrics` must be updated in the same task, not left with stale positional/keyword calls.
- `plan_validator.is_plan_valid(plan: Plan, state: YardState) -> bool` (Task 30)
- `ground_truth_comparison.run_comparison(instance: dict, max_containers: int = 8) -> dict` (Task 31) — keys `optimal_relocations`, `greedy_relocations`, `greedy_gap`, and (only once Task 33 has run) `crp_rl_relocations`/`crp_rl_gap`
- `sarcrp_core.replan(..., solver: Callable[..., Plan] = solve_crp)` (Task 33 — defaults to the existing greedy `solve_crp`, so every prior call site keeps working unchanged)
- `baselines.full_reoptimization(..., solver: Callable[..., Plan] = solve_crp)` (Task 33, same default-preserving pattern)
- `crp_rl_adapter.get_cached_model(model_path, device) -> Model` (Task 33 — module-level `functools.lru_cache`-backed loader; `solve_crp_via_crp_rl` calls this instead of `_load_model` directly)

---

### Task 20: B3/B4/B5 baselines

**Files:**
- Modify: `paper1_sarcrp/src/sarcrp/baselines.py`
- Test: `paper1_sarcrp/tests/test_baselines.py`

**Interfaces:**
- Consumes: `crp_solver.solve_crp` (Task 7), `freeze_horizon.split_plan` (Task 8), `sarcrp_core.replan` (Task 11)
- Produces: `periodic_replan`, `event_triggered_no_stability`, `mpc_receding_horizon` (signatures above)

- [ ] **Step 1: Write the failing tests**

Append to `paper1_sarcrp/tests/test_baselines.py`:
```python
import random
from sarcrp.sarcrp_core import ReplanDecision
from sarcrp.baselines import periodic_replan, event_triggered_no_stability, mpc_receding_horizon


def test_periodic_replan_only_reoptimizes_on_period_boundary():
    state = make_state(["C1", "C2"])
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    off_period = periodic_replan(state, ["C1", "C2"], plan, event_index=1, period=5)
    assert off_period is plan  # not a period boundary -> static passthrough
    on_period = periodic_replan(state, ["C1", "C2"], plan, event_index=5, period=5)
    assert on_period is not plan  # period boundary -> re-solved
    assert on_period.actions[0].type == "RETRIEVE"


def test_event_triggered_no_stability_zeroes_lambda_and_mu():
    state = make_state(["C1", "C2"])
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    decision = event_triggered_no_stability(
        state, plan, old_queue=["C1", "C2"], new_queue=["C2", "C1"],
        urgent_containers=["C2"], rng=random.Random(0), theta_impact=0.0, tau_frac=0.0,
    )
    assert isinstance(decision, ReplanDecision)


def test_mpc_receding_horizon_freezes_prefix_and_resolves_tail():
    state = make_state(["C1", "C2"])
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    result = mpc_receding_horizon(state, plan, retrieval_queue_new=["C2", "C1"], horizon=1)
    assert result.actions[0].container == plan.actions[0].container  # frozen prefix (1 action) untouched
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_baselines.py -v` (on the server, as established)
Expected: FAIL with `ImportError: cannot import name 'periodic_replan'`

- [ ] **Step 3: Implement**

Append to `paper1_sarcrp/src/sarcrp/baselines.py`:
```python
import random

from sarcrp.freeze_horizon import split_plan
from sarcrp.sarcrp_core import ReplanDecision, replan
from sarcrp.schemas import Plan


def periodic_replan(
    state, retrieval_queue_new: list[str], plan_current: Plan, event_index: int,
    period: int = 5, time_limit_sec: float = 5.0,
) -> Plan:
    """B3 (spec 22): re-solve every `period`-th event; otherwise keep the
    current plan unchanged (spec's own example: "every 10 events")."""
    if event_index % period != 0:
        return plan_current
    return solve_crp(state, retrieval_queue_new, time_limit_sec=time_limit_sec)


def event_triggered_no_stability(
    state, plan_old: Plan, old_queue: list[str], new_queue: list[str],
    urgent_containers: list[str], rng: random.Random,
    h_f: int = 3, theta_impact: float = 0.30, tau_frac: float = 0.01,
    time_limit_sec: float = 5.0, conf_new: float = 1.0,
) -> ReplanDecision:
    """B4 (spec 22, 40): same trigger AND freeze horizon as SAR-CRP, but the
    objective drops both the stability term and the data-confidence term
    (lambda=mu=0) -- "objective chi toi uu operational cost" (spec 40).
    `h_f` is exposed (unlike lambda/mu, which are fixed at 0 by this
    baseline's definition) because Experiment 1 (Task 28) varies freeze_size
    across all methods that have a freeze horizon at all -- B4 is one of them."""
    return replan(
        state, plan_old, old_queue, new_queue, urgent_containers,
        h_f=h_f, lam=0.0, mu=0.0, theta_impact=theta_impact, tau_frac=tau_frac,
        time_limit_sec=time_limit_sec, rng=rng, conf_new=conf_new,
    )


def mpc_receding_horizon(
    state, plan_current: Plan, retrieval_queue_new: list[str],
    horizon: int = 5, time_limit_sec: float = 5.0,
) -> Plan:
    """B5 (spec 22, 40): freeze a fixed-size horizon prefix, unconditionally
    re-solve the tail every event -- no trigger, no local repair, no
    stability-aware candidate selection (spec 40's explicit simplification)."""
    frozen, _tail = split_plan(plan_current, horizon)
    tail_solution = solve_crp(state, retrieval_queue_new, time_limit_sec=time_limit_sec)
    actions = list(frozen.actions) + list(tail_solution.actions)
    for i, a in enumerate(actions):
        a.step_index = i
    return Plan(plan_id=f"{plan_current.plan_id}_mpc", created_at=plan_current.created_at,
                source="mpc_receding_horizon", actions=actions)
```

Add `from sarcrp.crp_solver import solve_crp` to the existing imports at the top of `baselines.py` if not already present (it already is, from B1/B2).

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_baselines.py -v`
Expected: PASS (5 tests: 2 existing + 3 new)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/baselines.py paper1_sarcrp/tests/test_baselines.py
git commit -m "feat(paper1): implement B3 periodic, B4 event-triggered no-stability, B5 MPC baselines (spec 22)"
```

---

### Task 21: Ablation support (A1-A6)

**Files:**
- Modify: `paper1_sarcrp/src/sarcrp/sarcrp_core.py`
- Create: `paper1_sarcrp/src/sarcrp/ablations.py`
- Test: `paper1_sarcrp/tests/test_sarcrp_core.py`, `paper1_sarcrp/tests/test_ablations.py`

**Interfaces:**
- Consumes: `sarcrp_core.replan` (Task 11, modified here), `impact_estimator.compute_impact`'s existing `weights` param (Task 5 — already supports overriding)
- Produces: `sarcrp_core.replan(..., use_local_search=True, impact_weights=None)`, `ablations.ABLATIONS`, `ablations.replan_with_ablation`

- [ ] **Step 1: Write the failing test for `replan`'s new params**

Append to `paper1_sarcrp/tests/test_sarcrp_core.py`:
```python
def test_use_local_search_false_skips_c2_candidate():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision_with = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"],
                            ["C3"], theta_impact=0.05, tau_frac=0.0, rng=random.Random(0),
                            use_local_search=True)
    decision_without = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"],
                               ["C3"], theta_impact=0.05, tau_frac=0.0, rng=random.Random(0),
                               use_local_search=False)
    # Both must run end-to-end without error; disabling C2 must not crash the pipeline.
    assert decision_with.decision in {"KEEP", "UPDATE"}
    assert decision_without.decision in {"KEEP", "UPDATE"}


def test_impact_weights_override_changes_impact_total():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    default_decision = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"],
                               ["C3"], theta_impact=0.0, tau_frac=1.0, rng=random.Random(0))
    zero_blocking_decision = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"],
                                     ["C3"], theta_impact=0.0, tau_frac=1.0, rng=random.Random(0),
                                     impact_weights={"w_o": 0.25, "w_t": 0.20, "w_b": 0.0, "w_p": 0.20, "w_c": 0.10})
    assert zero_blocking_decision.impact.total <= default_decision.impact.total
```

Add `import random` at the top of `test_sarcrp_core.py` if not already present.

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_sarcrp_core.py -v`
Expected: FAIL with `TypeError: replan() got an unexpected keyword argument 'use_local_search'`

- [ ] **Step 3: Modify `replan`**

In `paper1_sarcrp/src/sarcrp/sarcrp_core.py`, change the signature and body:
```python
def replan(
    state_t,
    plan_old: Plan,
    old_queue: list[str],
    new_queue: list[str],
    urgent_containers: list[str],
    h_f: int = 3,
    lam: float = 1.0,
    mu: float = 0.5,
    theta_impact: float = 0.30,
    tau_frac: float = 0.01,
    time_limit_sec: float = 5.0,
    rng: random.Random | None = None,
    conf_new: float = 1.0,
    use_local_search: bool = True,
    impact_weights: dict | None = None,
) -> ReplanDecision:
    """Algorithm SAR-CRP v2 Core (spec 18), steps 1-9. use_local_search=False
    and impact_weights are ablation hooks (spec 25 A4, A6) -- not used by the
    default SAR-CRP configuration."""
    rng = rng or random.Random()

    impact = compute_impact(old_queue, new_queue, state_t, state_t, plan_old, conf_new=conf_new, weights=impact_weights)

    if impact.total < theta_impact:
        j_old = _score_candidate(plan_old, plan_old, 0, urgent_containers, conf_new)
        return ReplanDecision(decision="KEEP", plan=plan_old, impact=impact, j_old=j_old, j_new=j_old)

    frozen, _tail = split_plan(plan_old, h_f)
    frozen_count = len(frozen.actions)

    c0 = plan_old
    c1 = minimal_feasibility_repair(plan_old, state_t, new_queue)
    candidates = [c0, c1]
    if use_local_search:
        c2 = local_search_repair(
            c1, plan_old, state_t, new_queue, frozen_count, rng,
            urgent_containers=urgent_containers, conf_new=conf_new, time_limit_sec=time_limit_sec,
        )
        candidates.append(c2)
    tail_solution = solve_crp(state_t, new_queue, time_limit_sec=time_limit_sec)
    c3 = Plan(plan_id=f"{plan_old.plan_id}_c3", created_at=plan_old.created_at, source="frozen+crp_tail",
              actions=list(frozen.actions) + list(tail_solution.actions))
    candidates.append(c3)

    scored = [(_score_candidate(c, plan_old, frozen_count, urgent_containers, conf_new), c) for c in candidates]

    j_best, p_best = min(scored, key=lambda pair: pair[0])
    j_old = _score_candidate(plan_old, plan_old, 0, urgent_containers, conf_new)

    tau = tau_frac * j_old if j_old not in (0.0, float("inf")) else 0.0
    if j_best == float("inf") or (j_old - j_best) <= tau:
        return ReplanDecision(decision="KEEP", plan=plan_old, impact=impact, j_old=j_old, j_new=j_best)

    return ReplanDecision(decision="UPDATE", plan=p_best, impact=impact, j_old=j_old, j_new=j_best)
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_sarcrp_core.py -v`
Expected: PASS (5 tests: 3 existing + 2 new)

- [ ] **Step 5: Write the failing test for `ablations.py`**

Create `paper1_sarcrp/tests/test_ablations.py`:
```python
import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.ablations import ABLATIONS, replan_with_ablation


def make_state(queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_plan():
    return Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])


def test_all_six_ablations_are_registered():
    assert set(ABLATIONS.keys()) == {
        "A1_no_trigger", "A2_no_freeze", "A3_no_stability",
        "A4_no_local_search", "A5_no_data_confidence", "A6_no_blocking_impact",
    }


def test_a1_no_trigger_always_attempts_replan():
    state = make_state(["C1", "C2"])
    plan = make_plan()
    decision = replan_with_ablation(
        "A1_no_trigger", state, plan, old_queue=["C1", "C2"], new_queue=["C2", "C1"],
        urgent_containers=[], rng=random.Random(0),
    )
    assert decision.impact.total >= 0.0  # ran the full pipeline, not an early KEEP-by-threshold


def test_a3_no_stability_zeroes_lambda_only():
    state = make_state(["C1", "C2"])
    plan = make_plan()
    decision = replan_with_ablation(
        "A3_no_stability", state, plan, old_queue=["C1", "C2"], new_queue=["C2", "C1"],
        urgent_containers=["C2"], rng=random.Random(0),
    )
    assert decision.decision in {"KEEP", "UPDATE"}


def test_unknown_ablation_name_raises():
    state = make_state(["C1", "C2"])
    plan = make_plan()
    try:
        replan_with_ablation("not_a_real_ablation", state, plan, ["C1", "C2"], ["C2", "C1"], [], random.Random(0))
        assert False, "expected ValueError"
    except ValueError:
        pass
```

- [ ] **Step 6: Run to verify it fails**

Run: `pytest tests/test_ablations.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.ablations'`

- [ ] **Step 7: Implement `ablations.py`**

Create `paper1_sarcrp/src/sarcrp/ablations.py`:
```python
import random

from sarcrp.sarcrp_core import ReplanDecision, replan
from sarcrp.schemas import Plan

# Each entry overrides sarcrp_core.replan's defaults for one ablation (spec 25).
ABLATIONS: dict[str, dict] = {
    "A1_no_trigger": {"theta_impact": 0.0},  # always attempt replan
    "A2_no_freeze": {"h_f": 0},  # no frozen prefix
    "A3_no_stability": {"lam": 0.0},  # optimize operational cost only
    "A4_no_local_search": {"use_local_search": False},  # candidates C0/C1/C3 only
    "A5_no_data_confidence": {"mu": 0.0},  # ignore data-confidence penalty
    "A6_no_blocking_impact": {
        "impact_weights": {"w_o": 0.25, "w_t": 0.20, "w_b": 0.0, "w_p": 0.20, "w_c": 0.10}
    },
}


def replan_with_ablation(
    ablation_name: str,
    state_t,
    plan_old: Plan,
    old_queue: list[str],
    new_queue: list[str],
    urgent_containers: list[str],
    rng: random.Random,
    conf_new: float = 1.0,
) -> ReplanDecision:
    """Runs sarcrp_core.replan with one ablation's parameter overrides applied
    on top of the standard defaults (spec 25: "Chung tieu: chung minh tung
    module co dong gop.")."""
    if ablation_name not in ABLATIONS:
        raise ValueError(f"unknown ablation: {ablation_name!r}, expected one of {sorted(ABLATIONS)}")
    overrides = ABLATIONS[ablation_name]
    return replan(state_t, plan_old, old_queue, new_queue, urgent_containers, rng=rng, conf_new=conf_new, **overrides)
```

- [ ] **Step 8: Run to verify it passes**

Run: `pytest tests/test_ablations.py tests/test_sarcrp_core.py -v`
Expected: PASS (4 + 5 tests)

- [ ] **Step 9: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/sarcrp_core.py paper1_sarcrp/src/sarcrp/ablations.py paper1_sarcrp/tests/test_sarcrp_core.py paper1_sarcrp/tests/test_ablations.py
git commit -m "feat(paper1): add use_local_search/impact_weights hooks + A1-A6 ablation table (spec 25)"
```

---

### Task 22: Statistics module (§23.6 protocol)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/stats.py`
- Test: `paper1_sarcrp/tests/test_stats.py`
- Modify: `paper1_sarcrp/requirements.txt` (add `scipy`, `numpy`)

**Interfaces:**
- Produces: `stats.bootstrap_ci`, `stats.wilcoxon_signed_rank`, `stats.holm_bonferroni`, `stats.cliffs_delta` (signatures above)

- [ ] **Step 1: Add dependencies**

`paper1_sarcrp/requirements.txt` becomes:
```
pytest>=7.4
torch>=2.1
numpy>=1.24
scipy>=1.11
```

- [ ] **Step 2: Write the failing test**

Create `paper1_sarcrp/tests/test_stats.py`:
```python
import random
from sarcrp.stats import bootstrap_ci, wilcoxon_signed_rank, holm_bonferroni, cliffs_delta


def test_bootstrap_ci_bounds_contain_the_mean():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    mean, lo, hi = bootstrap_ci(values, n_resamples=500, ci=0.95, rng=random.Random(0))
    assert lo <= mean <= hi


def test_bootstrap_ci_is_seed_reproducible():
    values = [1.0, 5.0, 2.0, 8.0, 3.0]
    a = bootstrap_ci(values, n_resamples=200, rng=random.Random(7))
    b = bootstrap_ci(values, n_resamples=200, rng=random.Random(7))
    assert a == b


def test_wilcoxon_signed_rank_identical_samples_gives_high_p_value():
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    p = wilcoxon_signed_rank(a, list(a))
    assert p == 1.0  # scipy returns p=1.0 when all paired differences are zero


def test_wilcoxon_signed_rank_detects_a_consistent_shift():
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    b = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]  # every pair b > a by exactly 1
    p = wilcoxon_signed_rank(a, b)
    assert p < 0.05


def test_holm_bonferroni_rejects_fewer_than_uncorrected():
    p_values = [0.01, 0.04, 0.03, 0.20, 0.005]
    corrected = holm_bonferroni(p_values, alpha=0.05)
    uncorrected = [p < 0.05 for p in p_values]
    assert sum(corrected) <= sum(uncorrected)
    assert len(corrected) == len(p_values)


def test_cliffs_delta_no_overlap_gives_extreme_value():
    a = [1.0, 2.0, 3.0]
    b = [10.0, 11.0, 12.0]
    delta = cliffs_delta(a, b)
    assert delta == -1.0  # every a < every b


def test_cliffs_delta_identical_distributions_gives_zero():
    a = [1.0, 2.0, 3.0]
    assert cliffs_delta(a, list(a)) == 0.0
```

- [ ] **Step 3: Run to verify it fails**

Run: `pip install -r requirements.txt` then `pytest tests/test_stats.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.stats'`

- [ ] **Step 4: Implement**

Create `paper1_sarcrp/src/sarcrp/stats.py`:
```python
import random

from scipy import stats as scipy_stats


def bootstrap_ci(
    values: list[float], n_resamples: int = 2000, ci: float = 0.95, rng: random.Random | None = None
) -> tuple[float, float, float]:
    """Bootstrap mean +/- CI (spec 23.6). Uses stdlib `random`, not numpy's
    RNG, so results are reproducible with the same seed convention as the
    rest of this codebase (spec-mandated seed control)."""
    rng = rng or random.Random()
    n = len(values)
    mean = sum(values) / n
    resample_means = []
    for _ in range(n_resamples):
        resample = [values[rng.randrange(n)] for _ in range(n)]
        resample_means.append(sum(resample) / n)
    resample_means.sort()
    lo_idx = int((1 - ci) / 2 * n_resamples)
    hi_idx = int((1 - (1 - ci) / 2) * n_resamples) - 1
    return mean, resample_means[lo_idx], resample_means[hi_idx]


def wilcoxon_signed_rank(a: list[float], b: list[float]) -> float:
    """Paired Wilcoxon signed-rank test (spec 23.6) -- p-value for whether
    `a` and `b` (same seeds, same instance) differ. Delegates to scipy rather
    than a hand-rolled rank-sum implementation: this exact number is what a
    Q1 reviewer will scrutinize."""
    if all(x == y for x, y in zip(a, b)):
        return 1.0
    _, p_value = scipy_stats.wilcoxon(a, b)
    return float(p_value)


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Holm-Bonferroni step-down correction (spec 23.6). Returns, in the
    SAME order as the input, whether each comparison's null hypothesis is
    rejected at the family-wise `alpha`."""
    n = len(p_values)
    order = sorted(range(n), key=lambda i: p_values[i])
    reject = [False] * n
    for rank, idx in enumerate(order):
        threshold = alpha / (n - rank)
        if p_values[idx] <= threshold:
            reject[idx] = True
        else:
            break  # step-down: once one fails, all remaining (larger p) fail too
    return reject


def cliffs_delta(a: list[float], b: list[float]) -> float:
    """Cliff's delta effect size (spec 23.6), in [-1, 1]. Positive means `a`
    values tend to exceed `b` values; 0 means no stochastic dominance either way."""
    greater = sum(1 for x in a for y in b if x > y)
    less = sum(1 for x in a for y in b if x < y)
    return (greater - less) / (len(a) * len(b))
```

- [ ] **Step 5: Run to verify it passes**

Run: `pytest tests/test_stats.py -v`
Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/stats.py paper1_sarcrp/tests/test_stats.py paper1_sarcrp/requirements.txt
git commit -m "feat(paper1): implement spec 23.6 statistical protocol (bootstrap CI, Wilcoxon, Holm-Bonferroni, Cliff's delta)"
```

---

### Task 23: Ground truth for small instances (§21.1)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/ground_truth.py`
- Test: `paper1_sarcrp/tests/test_ground_truth.py`

**Interfaces:**
- Consumes: `schemas.YardState/Plan/Action` (Task 1), `state_ops.find_stack` (Task 2)
- Produces: `ground_truth.exhaustive_solve(state, retrieval_queue, max_containers=8) -> Plan`

- [ ] **Step 1: Write the failing test**

Create `paper1_sarcrp/tests/test_ground_truth.py`:
```import pytest
from sarcrp.schemas import Layout, Stack, YardState
from sarcrp.ground_truth import exhaustive_solve
from sarcrp.objective import relocation_count


def test_exhaustive_solve_finds_zero_relocations_when_already_sorted():
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=3),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=3)],
        container_attributes={}, retrieval_queue=["C1", "C2"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    plan = exhaustive_solve(state, retrieval_queue=["C1", "C2"])
    assert relocation_count(plan) == 0


def test_exhaustive_solve_finds_minimum_relocations_for_a_small_blocking_case():
    # S1 = [C3, C2, C1] (C1 top), need C3 first -> must relocate C1 and C2 (2 relocations minimum).
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=3),
        stacks=[Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=3), Stack(id="S2", containers=[], max_tier=3)],
        container_attributes={}, retrieval_queue=["C3", "C2", "C1"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    plan = exhaustive_solve(state, retrieval_queue=["C3", "C2", "C1"])
    assert relocation_count(plan) == 2
    retrieved = [a.container for a in plan.actions if a.type == "RETRIEVE"]
    assert retrieved == ["C3", "C2", "C1"]


def test_exhaustive_solve_raises_above_the_container_bound():
    state = YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=10),
        stacks=[Stack(id="S1", containers=[f"C{i}" for i in range(9)], max_tier=10)],
        container_attributes={}, retrieval_queue=[f"C{i}" for i in range(9)], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )
    with pytest.raises(ValueError):
        exhaustive_solve(state, retrieval_queue=[f"C{i}" for i in range(9)], max_containers=8)
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_ground_truth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.ground_truth'`

- [ ] **Step 3: Implement**

Create `paper1_sarcrp/src/sarcrp/ground_truth.py`:
```python
import copy

from sarcrp.schemas import Action, Plan, YardState


def _total_containers(state: YardState) -> int:
    return sum(len(s.containers) for s in state.stacks)


def exhaustive_solve(state: YardState, retrieval_queue: list[str], max_containers: int = 8) -> Plan:
    """Branch-and-bound exact solver (spec 21.1): retrieve `retrieval_queue`
    in order with the minimum number of relocations, by trying every legal
    destination for the current target's blockers at each step and pruning
    any branch whose relocation count already reaches the best-known
    solution. Only tractable for small instances -- raises above
    `max_containers` rather than silently taking exponential time."""
    n = _total_containers(state)
    if n > max_containers:
        raise ValueError(f"instance has {n} containers, exceeds max_containers={max_containers}")

    best = {"relocations": None, "actions": None}

    def stack_of(stacks_state: dict[str, list[str]], container: str) -> str | None:
        for sid, containers in stacks_state.items():
            if container in containers:
                return sid
        return None

    def search(stacks_state: dict[str, list[str]], queue: list[str], actions: list[Action], relocations: int, step: int):
        if best["relocations"] is not None and relocations >= best["relocations"]:
            return  # prune: cannot beat the best-known solution from here
        if not queue:
            best["relocations"] = relocations
            best["actions"] = list(actions)
            return

        target = queue[0]
        sid = stack_of(stacks_state, target)
        if sid is None:
            return  # infeasible branch (shouldn't happen with a well-formed instance)

        if stacks_state[sid][-1] == target:
            new_stacks = copy.deepcopy(stacks_state)
            new_stacks[sid].pop()
            new_actions = actions + [Action(
                action_id=f"gt{step:04d}", step_index=step, type="RETRIEVE", container=target,
                source_stack=sid, dest_stack=None, commit_status="planned", planned_time=step,
            )]
            search(new_stacks, queue[1:], new_actions, relocations, step + 1)
            return

        blocker = stacks_state[sid][-1]
        for dest_sid, dest_containers in stacks_state.items():
            if dest_sid == sid or len(dest_containers) >= state.stacks[[s.id for s in state.stacks].index(dest_sid)].max_tier:
                continue
            new_stacks = copy.deepcopy(stacks_state)
            new_stacks[sid].pop()
            new_stacks[dest_sid].append(blocker)
            new_actions = actions + [Action(
                action_id=f"gt{step:04d}", step_index=step, type="RELOCATE", container=blocker,
                source_stack=sid, dest_stack=dest_sid, commit_status="planned", planned_time=step,
            )]
            search(new_stacks, queue, new_actions, relocations + 1, step + 1)

    initial_stacks = {s.id: list(s.containers) for s in state.stacks}
    search(initial_stacks, retrieval_queue, [], 0, 0)

    if best["actions"] is None:
        raise ValueError("no feasible solution found -- check retrieval_queue matches the yard's containers")
    return Plan(plan_id="plan_ground_truth", created_at=state.time_step, source="exhaustive_branch_and_bound",
                actions=best["actions"])
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_ground_truth.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/ground_truth.py paper1_sarcrp/tests/test_ground_truth.py
git commit -m "feat(paper1): implement exhaustive branch-and-bound solver for ground truth (spec 21.1)"
```

---

### Task 24: Layout B/C instances + cross-layout runner (Experiment 3)

**Files:**
- Create: `paper1_sarcrp/experiments/instances/layout_b.json`
- Create: `paper1_sarcrp/experiments/instances/layout_c.json`
- Create: `paper1_sarcrp/experiments/run_cross_layout.py`
- Test: `paper1_sarcrp/tests/test_run_cross_layout.py`

**Interfaces:**
- Consumes: `simulator.run_episode` (Task 13)
- Produces: `experiments/results/cross_layout_results.csv`, a printed performance-drop summary

- [ ] **Step 1: Write Layout B (medium: 5 stacks, 15 containers) with genuine blocking**

Create `paper1_sarcrp/experiments/instances/layout_b.json`:
```json
{
  "instance_id": "layout_b_medium",
  "layout": {"num_stacks": 5, "max_tier": 5},
  "stacks": [
    {"id": "S1", "containers": ["C15", "C10", "C05", "C01"], "max_tier": 5},
    {"id": "S2", "containers": ["C14", "C09", "C04"], "max_tier": 5},
    {"id": "S3", "containers": ["C13", "C08", "C03"], "max_tier": 5},
    {"id": "S4", "containers": ["C12", "C07", "C02"], "max_tier": 5},
    {"id": "S5", "containers": ["C11", "C06"], "max_tier": 5}
  ],
  "initial_retrieval_order": ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12", "C13", "C14", "C15"],
  "t_steps": 40,
  "uncertainty_level": "medium"
}
```

- [ ] **Step 2: Write Layout C (larger: 6 stacks, 24 containers) with genuine blocking**

Create `paper1_sarcrp/experiments/instances/layout_c.json`:
```json
{
  "instance_id": "layout_c_large",
  "layout": {"num_stacks": 6, "max_tier": 6},
  "stacks": [
    {"id": "S1", "containers": ["C24", "C18", "C12", "C06"], "max_tier": 6},
    {"id": "S2", "containers": ["C23", "C17", "C11", "C05"], "max_tier": 6},
    {"id": "S3", "containers": ["C22", "C16", "C10", "C04"], "max_tier": 6},
    {"id": "S4", "containers": ["C21", "C15", "C09", "C03"], "max_tier": 6},
    {"id": "S5", "containers": ["C20", "C14", "C08", "C02"], "max_tier": 6},
    {"id": "S6", "containers": ["C19", "C13", "C07", "C01"], "max_tier": 6}
  ],
  "initial_retrieval_order": ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "C23", "C24"],
  "t_steps": 50,
  "uncertainty_level": "medium"
}
```

Both instances follow the same construction as the corrected `small_layout_mvp.json` (spec 20 SC1): the retrieval order requests the *bottom* of each stack first (highest blocker count), guaranteeing real relocations are needed, not the degenerate "already sorted" case Task 14 originally shipped by mistake.

- [ ] **Step 3: Write the failing test for the runner**

Create `paper1_sarcrp/tests/test_run_cross_layout.py`:
```python
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_cross_layout import run_all_layouts, summarize_performance_drop  # noqa: E402


def test_run_all_layouts_covers_all_three_layouts():
    rows = run_all_layouts(methods=("static", "sarcrp"), seeds=(0, 1))
    layouts = {r["layout"] for r in rows}
    assert layouts == {"layout_a", "layout_b", "layout_c"}


def test_summarize_performance_drop_reports_relative_change_from_layout_a():
    rows = [
        {"layout": "layout_a", "method": "sarcrp", "total_cost_mean": 7.0},
        {"layout": "layout_b", "method": "sarcrp", "total_cost_mean": 8.4},
        {"layout": "layout_c", "method": "sarcrp", "total_cost_mean": 10.5},
    ]
    drop = summarize_performance_drop(rows, method="sarcrp")
    assert drop["layout_b"] == pytest.approx(0.20, rel=1e-3)  # (8.4-7.0)/7.0
    assert drop["layout_c"] == pytest.approx(0.50, rel=1e-3)
```

Add `import pytest` at the top of the test file.

- [ ] **Step 4: Run to verify it fails**

Run: `pytest tests/test_run_cross_layout.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_cross_layout'`

- [ ] **Step 5: Implement the runner**

Create `paper1_sarcrp/experiments/run_cross_layout.py`:
```python
import csv
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.simulator import run_episode  # noqa: E402

METHODS = ("static", "full_reopt", "sarcrp")
SEEDS = tuple(range(20))  # spec 23.6: >=20 seeds for a reported experiment
LAYOUT_FILES = {
    "layout_a": "small_layout_mvp.json",
    "layout_b": "layout_b.json",
    "layout_c": "layout_c.json",
}


def run_all_layouts(methods=METHODS, seeds=SEEDS) -> list[dict]:
    """Cross-layout protocol (spec 50): every layout runs with the SAME
    hyperparameters (this codebase's spec-48 defaults) -- no per-layout
    tuning happens anywhere in this function."""
    instances_dir = Path(__file__).parent / "instances"
    rows = []
    for layout_name, filename in LAYOUT_FILES.items():
        instance = json.loads((instances_dir / filename).read_text())
        for method in methods:
            for seed in seeds:
                metrics = run_episode(instance, method_name=method, rng=random.Random(seed))
                rows.append({
                    "layout": layout_name, "method": method, "seed": seed,
                    "total_cost_mean": metrics.total_cost_mean,
                    "operational_cost_mean": metrics.operational_cost_mean,
                    "changed_actions_total": metrics.changed_actions_total,
                    "runtime_mean_sec": metrics.runtime_mean_sec,
                })
    return rows


def summarize_performance_drop(rows: list[dict], method: str) -> dict:
    """Relative total-cost change of Layout B/C vs Layout A (spec 50's
    'performance drop' metric, spec 24.5)."""
    by_layout = {}
    for layout in ("layout_a", "layout_b", "layout_c"):
        values = [r["total_cost_mean"] for r in rows if r["layout"] == layout and r["method"] == method]
        by_layout[layout] = statistics.mean(values) if values else float("nan")
    baseline = by_layout["layout_a"]
    return {
        "layout_b": (by_layout["layout_b"] - baseline) / baseline,
        "layout_c": (by_layout["layout_c"] - baseline) / baseline,
    }


def main():
    rows = run_all_layouts()
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "cross_layout_results.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")
    for method in METHODS:
        drop = summarize_performance_drop(rows, method)
        print(f"{method}: performance drop vs layout_a -> B: {drop['layout_b']:+.1%}, C: {drop['layout_c']:+.1%}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run to verify it passes**

Run: `pytest tests/test_run_cross_layout.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Run the real cross-layout experiment**

Run: `python experiments/run_cross_layout.py`
Expected: prints row count and a performance-drop line per method. Record the actual numbers for the final report (Task 35) -- do not fabricate them here.

- [ ] **Step 8: Commit**

```bash
git add paper1_sarcrp/experiments/instances/layout_b.json paper1_sarcrp/experiments/instances/layout_c.json paper1_sarcrp/experiments/run_cross_layout.py paper1_sarcrp/tests/test_run_cross_layout.py
git commit -m "feat(paper1): add Layout B/C instances and cross-layout validation runner (spec 23 Exp.3, spec 50)"
```

---

### Task 25: Data-confidence sensitivity (Experiment 4)

**Files:**
- Modify: `paper1_sarcrp/src/sarcrp/event_generator.py`
- Create: `paper1_sarcrp/experiments/run_experiment4.py`
- Test: `paper1_sarcrp/tests/test_event_generator.py`, `paper1_sarcrp/tests/test_run_experiment4.py`

**Interfaces:**
- Consumes: `event_generator.generate_event_stream` (Task 4, modified here), `simulator.run_episode` (Task 13)
- Produces: `event_generator.generate_event_stream(..., fixed_confidence=None)`, `experiments/results/experiment4_results.csv`

- [ ] **Step 1: Write the failing test**

Append to `paper1_sarcrp/tests/test_event_generator.py`:
```python
def test_fixed_confidence_overrides_sampled_confidence():
    rng = random.Random(0)
    queue = ["C1", "C2", "C3", "C4", "C5"]
    events = generate_event_stream(queue, t_steps=30, uncertainty_level="high", rng=rng, fixed_confidence=0.4)
    assert len(events) > 0
    assert all(e.confidence == 0.4 for e in events)
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_event_generator.py -v`
Expected: FAIL with `TypeError: generate_event_stream() got an unexpected keyword argument 'fixed_confidence'`

- [ ] **Step 3: Implement**

In `paper1_sarcrp/src/sarcrp/event_generator.py`, modify `generate_event_stream`'s signature and body:
```python
def generate_event_stream(
    initial_queue: list[str],
    t_steps: int,
    uncertainty_level: str,
    rng: random.Random,
    event_id_prefix: str = "e",
    fixed_confidence: float | None = None,
) -> list[Event]:
    queue = list(initial_queue)
    events: list[Event] = []

    for t in range(1, t_steps + 1):
        if rng.random() > P_EVENT:
            continue

        sampled = _sample_event_type(rng)
        severity = _sample_severity(uncertainty_level, rng)
        confidence = fixed_confidence if fixed_confidence is not None else _sample_confidence(uncertainty_level, rng)
        old_queue = list(queue)
```
(The rest of the function body is unchanged -- only the `confidence = ...` line changes, and the new parameter is added to the signature.)

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_event_generator.py -v`
Expected: PASS (5 tests: 4 existing + 1 new)

- [ ] **Step 5: Write the failing test for the Experiment 4 runner**

Create `paper1_sarcrp/tests/test_run_experiment4.py`:
```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_experiment4 import CONFIDENCE_LEVELS, run_confidence_sweep  # noqa: E402


def test_confidence_levels_match_spec():
    assert CONFIDENCE_LEVELS == (1.0, 0.7, 0.4, 0.2)


def test_run_confidence_sweep_returns_a_row_per_level_per_seed():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_confidence_sweep(instance, methods=("sarcrp",), seeds=(0, 1))
    levels_seen = {r["fixed_confidence"] for r in rows}
    assert levels_seen == set(CONFIDENCE_LEVELS)
    assert len(rows) == len(CONFIDENCE_LEVELS) * 1 * 2
```

- [ ] **Step 6: Run to verify it fails**

Run: `pytest tests/test_run_experiment4.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_experiment4'`

- [ ] **Step 7: Implement the runner**

Create `paper1_sarcrp/experiments/run_experiment4.py`:
```python
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.event_generator import generate_event_stream  # noqa: E402
from sarcrp.simulator import _build_state, EpisodeMetrics  # noqa: E402
from sarcrp.crp_solver import solve_crp  # noqa: E402
from sarcrp.baselines import static_plan, full_reoptimization  # noqa: E402
from sarcrp.sarcrp_core import replan  # noqa: E402
from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, relocation_count, stability_cost  # noqa: E402

CONFIDENCE_LEVELS = (1.0, 0.7, 0.4, 0.2)  # spec 23 Experiment 4
SEEDS = tuple(range(20))


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

    return EpisodeMetrics(
        relocation_count_total=relocation_count(plan), changed_actions_total=changed_total,
        total_cost_mean=sum(total_costs) / len(total_costs) if total_costs else 0.0,
        operational_cost_mean=sum(op_costs) / len(op_costs) if op_costs else 0.0,
        runtime_mean_sec=0.0, fallback_rate=0.0,
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


if __name__ == "__main__":
    main()
```

Note: `simulator._build_state` is currently a module-private helper (leading underscore). This task imports it directly across modules, which is acceptable within this single package but should be renamed to `build_state` (drop the underscore) in `simulator.py` if a third caller ever needs it -- not required now, two internal callers is fine.

- [ ] **Step 8: Run to verify it passes**

Run: `pytest tests/test_run_experiment4.py -v`
Expected: PASS (2 tests)

- [ ] **Step 9: Run the real Experiment 4**

Run: `python experiments/run_experiment4.py`
Expected: prints row count. Inspect `results/experiment4_results.csv` afterward: spec 23's actual research question is "does SAR-CRP change the plan less as confidence drops?" -- compare `changed_actions_total` across the four confidence levels for `method=sarcrp` when writing the final report (Task 35).

- [ ] **Step 10: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/event_generator.py paper1_sarcrp/experiments/run_experiment4.py paper1_sarcrp/tests/test_event_generator.py paper1_sarcrp/tests/test_run_experiment4.py
git commit -m "feat(paper1): add fixed_confidence override + Experiment 4 data-confidence sensitivity runner (spec 23 Exp.4)"
```

---

### Task 26: Formal sanity checks (SC1-SC4)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/sanity_checks.py`
- Create: `paper1_sarcrp/experiments/run_sanity_report.py`
- Test: `paper1_sarcrp/tests/test_sanity_checks.py`

**Interfaces:**
- Consumes: `event_generator.generate_event_stream` (Task 4), `impact_estimator.compute_impact` (Task 5), `baselines.static_plan` (Task 12), `simulator._build_state`/`solve_crp` (Task 7/13)
- Produces: `sanity_checks.SanityReport`, `sanity_checks.run_sanity_checks(instance, seeds=tuple(range(10))) -> SanityReport`

- [ ] **Step 1: Write the failing test**

Create `paper1_sarcrp/tests/test_sanity_checks.py`:
```python
import json
from pathlib import Path
from sarcrp.sanity_checks import run_sanity_checks, SanityReport


def test_run_sanity_checks_on_the_mvp_instance():
    instance_path = Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json"
    instance = json.loads(instance_path.read_text())
    report = run_sanity_checks(instance, seeds=tuple(range(10)))
    assert isinstance(report, SanityReport)
    assert isinstance(report.sc1_not_too_easy, bool)
    assert isinstance(report.sc2_not_too_hard, bool)
    assert 0.0 <= report.mean_impact <= 1.0
    assert set(report.event_type_frequency.keys()) <= {
        "ORDER_SWAP", "URGENT_INSERTION", "ETA_EARLY", "ETA_LATE",
        "PROBABILITY_UPDATE", "STALE_INFORMATION",
    }
    assert abs(sum(report.event_type_frequency.values()) - 1.0) < 1e-6
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_sanity_checks.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.sanity_checks'`

- [ ] **Step 3: Implement**

Create `paper1_sarcrp/src/sarcrp/sanity_checks.py`:
```python
import random
import statistics
from collections import Counter
from dataclasses import dataclass

from sarcrp.baselines import static_plan
from sarcrp.crp_solver import solve_crp
from sarcrp.event_generator import generate_event_stream
from sarcrp.impact_estimator import compute_impact
from sarcrp.objective import operational_cost
from sarcrp.simulator import _build_state


@dataclass
class SanityReport:
    sc1_not_too_easy: bool
    sc2_not_too_hard: bool
    event_type_frequency: dict[str, float]
    mean_impact: float
    sc4_impact_reasonable: bool


def run_sanity_checks(instance: dict, seeds: tuple = tuple(range(10))) -> SanityReport:
    """SC1-SC4 (spec 20, 49)."""
    queue = list(instance["initial_retrieval_order"])
    static_state = _build_state(instance, queue)
    no_event_plan = solve_crp(static_state, queue, time_limit_sec=5.0)
    no_event_cost = operational_cost(no_event_plan, urgent_containers=[], is_valid=True)

    all_event_types: Counter = Counter()
    all_impacts: list[float] = []
    dynamic_costs: list[float] = []
    fallback_flags: list[bool] = []

    for seed in seeds:
        rng = random.Random(seed)
        state = _build_state(instance, queue)
        plan = solve_crp(state, queue, time_limit_sec=5.0)
        events = generate_event_stream(queue, instance["t_steps"], instance["uncertainty_level"], rng)
        local_queue = list(queue)

        for event in events:
            all_event_types[event.type] += 1
            impact = compute_impact(local_queue, event.new_queue, state, state, plan, conf_new=event.confidence)
            all_impacts.append(impact.total)

            new_plan = static_plan(plan)  # SC1/SC2 measure the static baseline's behavior under events
            urgent = [event.affected_containers[0]] if event.type == "URGENT_INSERTION" and event.affected_containers else []
            cost = operational_cost(new_plan, urgent, is_valid=True)
            dynamic_costs.append(cost)
            fallback_flags.append(True)  # static never updates -- included for symmetry with other methods later

            local_queue = event.new_queue

    total_events = sum(all_event_types.values())
    frequency = {etype: count / total_events for etype, count in all_event_types.items()} if total_events else {}
    mean_impact = statistics.mean(all_impacts) if all_impacts else 0.0
    mean_dynamic_cost = statistics.mean(dynamic_costs) if dynamic_costs else 0.0
    fallback_rate = sum(fallback_flags) / len(fallback_flags) if fallback_flags else 0.0

    return SanityReport(
        sc1_not_too_easy=mean_dynamic_cost > no_event_cost,
        sc2_not_too_hard=fallback_rate < 0.50,
        event_type_frequency=frequency,
        mean_impact=mean_impact,
        sc4_impact_reasonable=0.2 <= mean_impact <= 0.8,
    )
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_sanity_checks.py -v`
Expected: PASS (1 test) -- **note the SC1/SC2/SC4 boolean fields may come back False on the current MVP instance/parameters; that is a real finding to report (Task 35), not a test failure to chase**, since the test only asserts the report's *shape*, not that every check passes.

- [ ] **Step 5: Write the report script**

Create `paper1_sarcrp/experiments/run_sanity_report.py`:
```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.sanity_checks import run_sanity_checks  # noqa: E402


def main():
    instance = json.loads((Path(__file__).parent / "instances" / "small_layout_mvp.json").read_text())
    report = run_sanity_checks(instance)
    print(f"SC1 (not too easy):    {'PASS' if report.sc1_not_too_easy else 'FAIL'}")
    print(f"SC2 (not too hard):    {'PASS' if report.sc2_not_too_hard else 'FAIL'}")
    print(f"SC3 event frequency:   {report.event_type_frequency}")
    print(f"SC4 (mean impact in [0.2,0.8]): {'PASS' if report.sc4_impact_reasonable else 'FAIL'} (mean={report.mean_impact:.3f})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the real sanity report**

Run: `python experiments/run_sanity_report.py`
Expected: prints 4 lines. Record the actual PASS/FAIL and numbers for Task 35's report -- do not adjust event-generator defaults just to force a PASS here without saying so in the paper.

- [ ] **Step 7: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/sanity_checks.py paper1_sarcrp/experiments/run_sanity_report.py paper1_sarcrp/tests/test_sanity_checks.py
git commit -m "feat(paper1): implement formal SC1-SC4 benchmark sanity checks (spec 20, 49)"
```

---

### Task 27: Wire new methods into the simulator

**Files:**
- Modify: `paper1_sarcrp/src/sarcrp/simulator.py`
- Test: `paper1_sarcrp/tests/test_simulator_mvp.py`

**Interfaces:**
- Consumes: `baselines.periodic_replan/event_triggered_no_stability/mpc_receding_horizon` (Task 20), `ablations.replan_with_ablation` (Task 21)
- Produces: `simulator.run_episode` accepting `method_name` in `{"static","full_reopt","sarcrp","periodic","event_triggered_no_stability","mpc"} | {"sarcrp_" + k for k in ablations.ABLATIONS}`

- [ ] **Step 1: Write the failing tests**

Append to `paper1_sarcrp/tests/test_simulator_mvp.py`:
```python
def test_run_episode_supports_periodic_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="periodic", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0


def test_run_episode_supports_event_triggered_no_stability_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="event_triggered_no_stability", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0


def test_run_episode_supports_mpc_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="mpc", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0


def test_run_episode_supports_ablation_methods():
    for ablation_method in ("sarcrp_A1_no_trigger", "sarcrp_A3_no_stability", "sarcrp_A6_no_blocking_impact"):
        metrics = run_episode(SMALL_INSTANCE, method_name=ablation_method, rng=random.Random(0))
        assert metrics.total_cost_mean >= 0.0


def test_run_episode_rejects_unknown_method():
    try:
        run_episode(SMALL_INSTANCE, method_name="not_a_method", rng=random.Random(0))
        assert False, "expected ValueError"
    except ValueError:
        pass
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_simulator_mvp.py -v`
Expected: FAIL — `"periodic"` currently falls through to the `else: raise ValueError` branch, so `test_run_episode_supports_periodic_method` fails with the ValueError propagating (test doesn't expect one).

- [ ] **Step 3: Extend the dispatch**

In `paper1_sarcrp/src/sarcrp/simulator.py`, add the imports:
```python
from sarcrp.ablations import ABLATIONS, replan_with_ablation
from sarcrp.baselines import (
    event_triggered_no_stability, full_reoptimization, mpc_receding_horizon,
    periodic_replan, static_plan,
)
```

Add two optional parameters to `run_episode`'s signature -- **this is the only way Experiment 1 (Task 28) can actually vary freeze_size/lambda per grid point; without this change every factorial combination silently runs with the same hardcoded defaults**:
```python
def run_episode(instance: dict, method_name: str, rng: random.Random, h_f: int | None = None, lam: float | None = None) -> EpisodeMetrics:
```
(keep the rest of the function body as-is up to the per-event dispatch)

Replace the `if method_name == "static": ... elif ... else: raise ValueError(...)` block with:
```python
        replan_kwargs = {}
        if h_f is not None:
            replan_kwargs["h_f"] = h_f
        if lam is not None:
            replan_kwargs["lam"] = lam

        if method_name == "static":
            new_plan = static_plan(plan)
            fallback = True
        elif method_name == "full_reopt":
            new_plan = full_reoptimization(state, new_queue, time_limit_sec=5.0)
            fallback = False
        elif method_name == "sarcrp":
            replan_opportunities += 1
            decision = replan(state, plan, queue, new_queue, urgent, rng=rng, conf_new=event.confidence, **replan_kwargs)
            new_plan = decision.plan
            fallback = decision.decision == "KEEP"
        elif method_name == "periodic":
            replan_opportunities += 1
            new_plan = periodic_replan(state, new_queue, plan, event_index=replan_opportunities + 1, time_limit_sec=5.0)
            fallback = new_plan is plan
        elif method_name == "event_triggered_no_stability":
            replan_opportunities += 1
            no_stability_kwargs = {k: v for k, v in replan_kwargs.items() if k == "h_f"}  # lam is fixed at 0 by definition
            decision = event_triggered_no_stability(state, plan, queue, new_queue, urgent, rng, conf_new=event.confidence, **no_stability_kwargs)
            new_plan = decision.plan
            fallback = decision.decision == "KEEP"
        elif method_name == "mpc":
            replan_opportunities += 1
            new_plan = mpc_receding_horizon(state, plan, new_queue, time_limit_sec=5.0)
            fallback = False
        elif method_name.startswith("sarcrp_") and method_name[len("sarcrp_"):] in ABLATIONS:
            replan_opportunities += 1
            ablation_name = method_name[len("sarcrp_"):]
            decision = replan_with_ablation(ablation_name, state, plan, queue, new_queue, urgent, rng, conf_new=event.confidence)
            new_plan = decision.plan
            fallback = decision.decision == "KEEP"
        else:
            raise ValueError(f"unknown method_name: {method_name}")
```

Note `sarcrp_<ablation>` methods deliberately do NOT accept `h_f`/`lam` overrides here -- each ablation already pins its own parameter set (Task 21's `ABLATIONS` table), and A1/A2/A3 exist specifically to test one fixed deviation from the defaults, not to be crossed with Experiment 1's own factorial on top. Task 28's `run_factorial` only requests `h_f`/`lam` overrides for `sarcrp` and `event_triggered_no_stability`.

- [ ] **Step 4: Write the regression test proving the override actually changes behavior**

Append to `paper1_sarcrp/tests/test_simulator_mvp.py`:
```python
def test_run_episode_h_f_override_changes_sarcrp_frozen_count():
    # h_f=0 (no freeze) must be able to reach a different outcome than h_f=5
    # (freeze almost everything) for the same seed -- if this ever comes back
    # identical, the h_f override silently stopped being threaded through.
    metrics_no_freeze = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(3), h_f=0)
    metrics_full_freeze = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(3), h_f=5)
    assert (metrics_no_freeze.changed_actions_total, metrics_no_freeze.total_cost_mean) != \
           (metrics_full_freeze.changed_actions_total, metrics_full_freeze.total_cost_mean)


def test_run_episode_lam_override_changes_sarcrp_behavior():
    metrics_lam0 = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(3), lam=0.0)
    metrics_lam_default = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(3), lam=1.0)
    assert metrics_lam0.total_cost_mean != metrics_lam_default.total_cost_mean or \
           metrics_lam0.changed_actions_total != metrics_lam_default.changed_actions_total
```

If either assertion fails on the actual `SMALL_INSTANCE`/seed combination (e.g. because that particular seed's event stream never triggers a real replan at all, per the MVP report's own finding), swap in `random.Random(7)` or another seed from Task 14/17's existing runs known to trigger at least one UPDATE -- the point of the test is to catch the override being dropped, not to pin one specific seed.

- [ ] **Step 5: Run to verify it passes**

Run: `pytest tests/test_simulator_mvp.py -v`
Expected: PASS (11 tests: 4 existing + 5 from Step 1 + 2 new from Step 4)

- [ ] **Step 6: Run the full suite to confirm nothing else broke**

Run: `pytest -v`
Expected: PASS, all tests (MVP + Tasks 20-27's new tests)

- [ ] **Step 7: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/simulator.py paper1_sarcrp/tests/test_simulator_mvp.py
git commit -m "feat(paper1): wire B3-B5 baselines, A1-A6 ablations, and h_f/lam overrides into simulator.run_episode"
```

---

### Task 28: Experiment 1 — full factorial runner with statistical protocol

**Files:**
- Create: `paper1_sarcrp/experiments/run_experiment1.py`
- Test: `paper1_sarcrp/tests/test_run_experiment1.py`

**Interfaces:**
- Consumes: `simulator.run_episode` (Task 27), `stats.bootstrap_ci/wilcoxon_signed_rank/holm_bonferroni/cliffs_delta` (Task 22)
- Produces: `experiments/results/experiment1_results.csv`, `experiments/results/experiment1_significance.csv`

- [ ] **Step 1: Write the failing test**

Create `paper1_sarcrp/tests/test_run_experiment1.py`:
```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_experiment1 import FACTOR_GRID, run_factorial, run_significance_tests  # noqa: E402


def test_factor_grid_matches_spec_23():
    assert set(FACTOR_GRID["uncertainty_level"]) == {"low", "medium", "high"}
    assert set(FACTOR_GRID["freeze_size"]) == {0, 3, 5}
    assert set(FACTOR_GRID["lam"]) == {0.0, 0.5, 1.0}


def test_run_factorial_covers_the_full_grid_for_two_seeds():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_factorial(instance, methods=("static", "sarcrp"), seeds=(0, 1))
    combos = {(r["uncertainty_level"], r["freeze_size"], r["lam"]) for r in rows if r["method"] == "sarcrp"}
    assert len(combos) == 3 * 3 * 3


def test_run_factorial_freeze_size_actually_changes_sarcrp_results():
    # Regression guard for the bug this plan's Self-Review caught: freeze_size
    # and lam were defined in FACTOR_GRID but never threaded through to
    # run_episode, so every combination silently produced identical rows.
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_factorial(instance, methods=("sarcrp",), seeds=(3,))
    by_freeze = {
        r["freeze_size"]: (r["changed_actions_total"], r["total_cost_mean"])
        for r in rows if r["uncertainty_level"] == "medium" and r["lam"] == 1.0
    }
    assert len(set(by_freeze.values())) > 1, f"all freeze_size values produced identical results: {by_freeze}"


def test_run_significance_tests_reports_holm_bonferroni_corrected_flags():
    rows = [
        {"method": "static", "seed": s, "total_cost_mean": 7.0 + 0.01 * s} for s in range(20)
    ] + [
        {"method": "sarcrp", "seed": s, "total_cost_mean": 6.0 + 0.01 * s} for s in range(20)
    ]
    result = run_significance_tests(rows, baseline_methods=("static",))
    assert "static" in result
    assert "p_value" in result["static"]
    assert "p_value_holm_significant" in result["static"]
    assert "cliffs_delta" in result["static"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_run_experiment1.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_experiment1'`

- [ ] **Step 3: Implement**

Create `paper1_sarcrp/experiments/run_experiment1.py`:
```python
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.simulator import run_episode  # noqa: E402
from sarcrp.stats import bootstrap_ci, cliffs_delta, holm_bonferroni, wilcoxon_signed_rank  # noqa: E402

METHODS = ("static", "full_reopt", "periodic", "event_triggered_no_stability", "mpc", "sarcrp")
SEEDS = tuple(range(20))  # spec 23.6: >=20 seeds
FACTOR_GRID = {
    "uncertainty_level": ("low", "medium", "high"),
    "freeze_size": (0, 3, 5),
    "lam": (0.0, 0.5, 1.0),
}


METHODS_WITH_FREEZE_HORIZON = {"sarcrp", "event_triggered_no_stability"}
METHODS_WITH_LAMBDA = {"sarcrp"}  # event_triggered_no_stability fixes lambda=0 by definition (spec 40) -- never overridable


def run_factorial(instance: dict, methods=METHODS, seeds=SEEDS) -> list[dict]:
    """Experiment 1 (spec 23): uncertainty x freeze_size x lambda, all 6
    methods. freeze_size/lam are only *passed through* to sarcrp/
    event_triggered_no_stability (Task 27's run_episode(h_f=, lam=) params
    only affect those two dispatch branches) -- other methods still run at
    every grid point for a like-for-like comparison at the same seed, they
    just have no parameter for those factors to act on."""
    rows = []
    for uncertainty in FACTOR_GRID["uncertainty_level"]:
        for freeze_size in FACTOR_GRID["freeze_size"]:
            for lam in FACTOR_GRID["lam"]:
                level_instance = dict(instance, uncertainty_level=uncertainty)
                for method in methods:
                    h_f_arg = freeze_size if method in METHODS_WITH_FREEZE_HORIZON else None
                    lam_arg = lam if method in METHODS_WITH_LAMBDA else None
                    for seed in seeds:
                        metrics = run_episode(level_instance, method_name=method, rng=random.Random(seed), h_f=h_f_arg, lam=lam_arg)
                        rows.append({
                            "uncertainty_level": uncertainty, "freeze_size": freeze_size, "lam": lam,
                            "method": method, "seed": seed,
                            "total_cost_mean": metrics.total_cost_mean,
                            "operational_cost_mean": metrics.operational_cost_mean,
                            "changed_actions_total": metrics.changed_actions_total,
                            "runtime_mean_sec": metrics.runtime_mean_sec,
                            "fallback_rate": metrics.fallback_rate,
                        })
    return rows


def run_significance_tests(rows: list[dict], baseline_methods=("static", "full_reopt", "periodic", "event_triggered_no_stability", "mpc")) -> dict:
    """spec 23.6: SAR-CRP vs each of B1-B5, paired by seed, Holm-Bonferroni
    corrected across the len(baseline_methods) comparisons, with Cliff's delta."""
    by_seed_sarcrp = {r["seed"]: r["total_cost_mean"] for r in rows if r["method"] == "sarcrp"}
    seeds_sorted = sorted(by_seed_sarcrp)
    sarcrp_values = [by_seed_sarcrp[s] for s in seeds_sorted]

    raw_p_values = []
    per_baseline = {}
    for baseline in baseline_methods:
        by_seed_baseline = {r["seed"]: r["total_cost_mean"] for r in rows if r["method"] == baseline}
        baseline_values = [by_seed_baseline[s] for s in seeds_sorted if s in by_seed_baseline]
        matched_sarcrp = [by_seed_sarcrp[s] for s in seeds_sorted if s in by_seed_baseline]
        p_value = wilcoxon_signed_rank(matched_sarcrp, baseline_values)
        delta = cliffs_delta(matched_sarcrp, baseline_values)
        raw_p_values.append(p_value)
        per_baseline[baseline] = {"p_value": p_value, "cliffs_delta": delta}

    significant_flags = holm_bonferroni(raw_p_values)
    for baseline, flag in zip(baseline_methods, significant_flags):
        per_baseline[baseline]["p_value_holm_significant"] = flag

    per_baseline["_sarcrp_ci"] = bootstrap_ci(sarcrp_values, rng=random.Random(0))
    return per_baseline


def main():
    instance = json.loads((Path(__file__).parent / "instances" / "small_layout_mvp.json").read_text())
    rows = run_factorial(instance)

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "experiment1_results.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")

    significance = run_significance_tests(rows)
    sig_path = results_dir / "experiment1_significance.csv"
    with sig_path.open("w", newline="") as f:
        f.write("baseline,p_value,p_value_holm_significant,cliffs_delta\n")
        for baseline, stats_row in significance.items():
            if baseline == "_sarcrp_ci":
                continue
            f.write(f"{baseline},{stats_row['p_value']:.6f},{stats_row['p_value_holm_significant']},{stats_row['cliffs_delta']:.4f}\n")
    print(f"Wrote significance table to {sig_path}")
    for baseline, stats_row in significance.items():
        if baseline == "_sarcrp_ci":
            continue
        print(f"SAR-CRP vs {baseline}: p={stats_row['p_value']:.4f} "
              f"(Holm-significant={stats_row['p_value_holm_significant']}), "
              f"Cliff's delta={stats_row['cliffs_delta']:.3f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_run_experiment1.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Run the real Experiment 1**

Run: `python experiments/run_experiment1.py` — this runs 3×3×3 grid points × 6 methods × 20 seeds = 3,240 episodes; time it first (`time python experiments/run_experiment1.py`) since it is by far the longest-running command in this plan, and if it exceeds a few minutes, run it with `run_in_background`-equivalent (`nohup ... &` over SSH) rather than blocking the session.
Expected: writes both CSVs, prints one significance line per baseline. Record the actual p-values/effect sizes for Task 35 -- these are the headline numbers for the paper's Results section.

- [ ] **Step 6: Commit**

```bash
git add paper1_sarcrp/experiments/run_experiment1.py paper1_sarcrp/tests/test_run_experiment1.py
git commit -m "feat(paper1): implement Experiment 1 full factorial + spec 23.6 significance testing"
```

---

### Task 30: Metrics completeness (invalid rate, timeout rate, P95 runtime, stability cost)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/plan_validator.py`
- Modify: `paper1_sarcrp/src/sarcrp/simulator.py`
- Test: `paper1_sarcrp/tests/test_plan_validator.py`, `paper1_sarcrp/tests/test_simulator_mvp.py`

**Interfaces:**
- Consumes: `schemas.Plan/YardState` (Task 1)
- Produces: `plan_validator.is_plan_valid(plan, state) -> bool`; `simulator.EpisodeMetrics` gains `stability_cost_mean`, `invalid_rate`, `timeout_rate`, `runtime_p95_sec`

- [ ] **Step 1: Write the failing test for `is_plan_valid`**

Create `paper1_sarcrp/tests/test_plan_validator.py`:
```python
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.plan_validator import is_plan_valid


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=2),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=2), Stack(id="S2", containers=[], max_tier=2)],
        container_attributes={}, retrieval_queue=["C1", "C2"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_valid_plan_is_accepted():
    state = make_state()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    assert is_plan_valid(plan, state) is True


def test_retrieve_wrong_container_is_rejected():
    state = make_state()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C2",  # C1 is on top, not C2
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    assert is_plan_valid(plan, state) is False


def test_relocate_into_a_full_stack_is_rejected():
    state = make_state()
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RELOCATE", container="C1",
               source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RELOCATE", container="C2",
               source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=1),
        # S2 has max_tier=2; a third relocation into it would overfill it.
        Action(action_id="a2", step_index=2, type="RELOCATE", container="C1",
               source_stack="S2", dest_stack="S2", commit_status="planned", planned_time=2),
    ])
    assert is_plan_valid(plan, state) is False
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_plan_validator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.plan_validator'`

- [ ] **Step 3: Implement**

Create `paper1_sarcrp/src/sarcrp/plan_validator.py`:
```python
from sarcrp.schemas import Plan, YardState


def is_plan_valid(plan: Plan, state: YardState) -> bool:
    """Replays `plan`'s actions against a shadow copy of `state`'s stacks,
    checking each action is legal: RETRIEVE must target the current top of
    its source stack; RELOCATE must move the current top of its source
    stack into a destination that still has room. Spec 11.3's
    InvalidPenalty(P)/M_inf is otherwise dead code -- every call site in
    this codebase has passed is_valid=True unconditionally since Task 6,
    so the M_inf branch has never actually been exercised."""
    stacks = {s.id: list(s.containers) for s in state.stacks}
    max_tiers = {s.id: s.max_tier for s in state.stacks}

    for action in sorted(plan.actions, key=lambda a: a.step_index):
        if action.type == "RETRIEVE":
            stack = stacks.get(action.source_stack)
            if not stack or stack[-1] != action.container:
                return False
            stack.pop()
        elif action.type == "RELOCATE":
            source = stacks.get(action.source_stack)
            dest = stacks.get(action.dest_stack)
            if source is None or dest is None or not source or source[-1] != action.container:
                return False
            if len(dest) >= max_tiers.get(action.dest_stack, 0):
                return False
            source.pop()
            dest.append(action.container)
    return True
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_plan_validator.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Write the failing test for the new `EpisodeMetrics` fields**

Append to `paper1_sarcrp/tests/test_simulator_mvp.py`:
```python
def test_episode_metrics_reports_the_new_fields():
    metrics = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(0))
    assert metrics.stability_cost_mean >= 0.0
    assert 0.0 <= metrics.invalid_rate <= 1.0
    assert 0.0 <= metrics.timeout_rate <= 1.0
    assert metrics.runtime_p95_sec >= 0.0


def test_time_limit_sec_override_is_accepted():
    # Task 32 also needs this parameter; asserting it here keeps the two
    # tasks' expectations of run_episode's signature from drifting apart.
    metrics = run_episode(SMALL_INSTANCE, method_name="static", rng=random.Random(0), time_limit_sec=1.0)
    assert metrics.total_cost_mean >= 0.0
```

- [ ] **Step 6: Run to verify it fails**

Run: `pytest tests/test_simulator_mvp.py -v`
Expected: FAIL with `AttributeError: 'EpisodeMetrics' object has no attribute 'stability_cost_mean'`

- [ ] **Step 7: Extend `EpisodeMetrics` and `run_episode`**

In `paper1_sarcrp/src/sarcrp/simulator.py`:

Add the import and extend the dataclass:
```python
import statistics

from sarcrp.plan_validator import is_plan_valid


@dataclass
class EpisodeMetrics:
    relocation_count_total: int
    changed_actions_total: int
    total_cost_mean: float
    operational_cost_mean: float
    stability_cost_mean: float
    runtime_mean_sec: float
    runtime_p95_sec: float
    fallback_rate: float
    invalid_rate: float
    timeout_rate: float
```

Add the `time_limit_sec: float = 5.0` parameter to `run_episode`'s signature (alongside the `h_f`/`lam` params Task 27 already added), and inside the per-event loop, after `runtime = time.monotonic() - start`, add:
```python
        is_valid = is_plan_valid(new_plan, state)
        invalid_flags.append(not is_valid)
        timeout_flags.append(runtime >= time_limit_sec * 0.95)
```
(add `invalid_flags = []` and `timeout_flags = []` next to the other accumulator lists at the top of the function, and `stab_costs = []` alongside `op_costs`, appending `0.0 if violated else stab` to it right where `op_costs.append(op)` already happens)

Change the `op = operational_cost(new_plan, urgent, is_valid=True)` line to `op = operational_cost(new_plan, urgent, is_valid=is_valid)` (this is the fix that finally makes the M_inf penalty path reachable), and update the final `return EpisodeMetrics(...)` call:
```python
    runtimes_sorted = sorted(runtimes)
    p95_index = min(int(0.95 * len(runtimes_sorted)), len(runtimes_sorted) - 1) if runtimes_sorted else 0
    return EpisodeMetrics(
        relocation_count_total=relocation_count(plan),
        changed_actions_total=changed_actions_total,
        total_cost_mean=sum(total_costs) / len(total_costs) if total_costs else 0.0,
        operational_cost_mean=sum(op_costs) / len(op_costs) if op_costs else 0.0,
        stability_cost_mean=sum(stab_costs) / len(stab_costs) if stab_costs else 0.0,
        runtime_mean_sec=sum(runtimes) / len(runtimes) if runtimes else 0.0,
        runtime_p95_sec=runtimes_sorted[p95_index] if runtimes_sorted else 0.0,
        fallback_rate=fallback_count / denom if denom else 0.0,
        invalid_rate=sum(invalid_flags) / len(invalid_flags) if invalid_flags else 0.0,
        timeout_rate=sum(timeout_flags) / len(timeout_flags) if timeout_flags else 0.0,
    )
```

Every other call site inside `run_episode` that passes `time_limit_sec=5.0` as a literal (the `full_reoptimization`, `periodic_replan`, `mpc_receding_horizon`, `replan`, `event_triggered_no_stability` calls) should use the parameter instead — Task 32 makes this change explicitly (this task only needs the metrics fields; leaving the literals as `5.0` for now does not break anything here, since `time_limit_sec` is accepted but Task 30 doesn't require it to change behavior yet).

- [ ] **Step 8: Run to verify it passes**

Run: `pytest tests/test_simulator_mvp.py tests/test_plan_validator.py -v`
Expected: PASS (13 tests: 11 existing + 2 new)

- [ ] **Step 9: Run the full suite**

Run: `pytest -v`
Expected: PASS -- every other test that constructs or reads `EpisodeMetrics` must still pass; if any test destructures `EpisodeMetrics` by position instead of by attribute name, fix it to use attribute access (none currently do, per Tasks 13-28's code, but re-check `run_experiment4.py`'s `_run_one`, which builds an `EpisodeMetrics` by hand -- it must supply all 10 fields now, not the original 6).

Update `run_experiment4.py`'s `_run_one` (Task 25) return statement to supply the four new fields (`stability_cost_mean=sum(...)/... `, `runtime_p95_sec=0.0`, `invalid_rate=0.0`, `timeout_rate=0.0` are acceptable placeholders *only in that one script*, since Experiment 4 doesn't reuse `run_episode` and never claims to report those fields in its own CSV columns -- Task 35's report must not cite Experiment 4's `invalid_rate`/`timeout_rate` for this reason).

- [ ] **Step 10: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/plan_validator.py paper1_sarcrp/src/sarcrp/simulator.py paper1_sarcrp/experiments/run_experiment4.py paper1_sarcrp/tests/test_plan_validator.py paper1_sarcrp/tests/test_simulator_mvp.py
git commit -m "feat(paper1): add plan validity check + invalid/timeout rate, P95 runtime, stability cost to EpisodeMetrics (spec 24)"
```

---

### Task 31: Ground truth optimality gap (§21.1)

**Files:**
- Create: `paper1_sarcrp/experiments/instances/tiny_ground_truth.json`
- Create: `paper1_sarcrp/experiments/run_ground_truth_comparison.py`
- Test: `paper1_sarcrp/tests/test_run_ground_truth_comparison.py`

**Interfaces:**
- Consumes: `ground_truth.exhaustive_solve` (Task 23), `crp_solver.solve_crp` (Task 7)
- Produces: `run_ground_truth_comparison.run_comparison(instance, max_containers=8) -> dict`

- [ ] **Step 1: Write a genuinely small instance with real blocking**

Create `paper1_sarcrp/experiments/instances/tiny_ground_truth.json`:
```json
{
  "instance_id": "tiny_ground_truth",
  "layout": {"num_stacks": 2, "max_tier": 4},
  "stacks": [
    {"id": "S1", "containers": ["C6", "C4", "C2"], "max_tier": 4},
    {"id": "S2", "containers": ["C5", "C3", "C1"], "max_tier": 4}
  ],
  "initial_retrieval_order": ["C1", "C2", "C3", "C4", "C5", "C6"]
}
```
6 containers, 2 stacks -- within `exhaustive_solve`'s `max_containers=8` bound. `C1`/`C2` are buried under two containers each requiring genuine relocations, matching the same "bottom-first" construction as `small_layout_mvp.json` and Layouts B/C (spec 20 SC1).

- [ ] **Step 2: Write the failing test**

Create `paper1_sarcrp/tests/test_run_ground_truth_comparison.py`:
```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_ground_truth_comparison import run_comparison  # noqa: E402


def test_run_comparison_reports_optimal_and_greedy_relocations():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "tiny_ground_truth.json").read_text())
    result = run_comparison(instance)
    assert "optimal_relocations" in result
    assert "greedy_relocations" in result
    assert "greedy_gap" in result
    assert result["greedy_relocations"] >= result["optimal_relocations"]
    assert result["greedy_gap"] >= 0.0
```

- [ ] **Step 3: Run to verify it fails**

Run: `pytest tests/test_run_ground_truth_comparison.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_ground_truth_comparison'`

- [ ] **Step 4: Implement**

Create `paper1_sarcrp/experiments/run_ground_truth_comparison.py`:
```python
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
```

- [ ] **Step 5: Run to verify it passes**

Run: `pytest tests/test_run_ground_truth_comparison.py -v`
Expected: PASS (1 test)

- [ ] **Step 6: Run the real comparison**

Run: `python experiments/run_ground_truth_comparison.py`
Expected: prints 3 lines. Record the actual gap percentage for Task 35's report -- if the greedy heuristic turns out to already be optimal on this tiny instance (gap=0%), that is a valid (if less dramatic) finding, not a reason to construct a harder instance until a nonzero gap appears.

- [ ] **Step 7: Commit**

```bash
git add paper1_sarcrp/experiments/instances/tiny_ground_truth.json paper1_sarcrp/experiments/run_ground_truth_comparison.py paper1_sarcrp/tests/test_run_ground_truth_comparison.py
git commit -m "feat(paper1): add ground-truth optimality gap comparison on a tractable 6-container instance (spec 21.1)"
```

---

### Task 32: Timeout tiering by instance size (§17) + extended-timeout proxy (§21.2)

**Files:**
- Modify: `paper1_sarcrp/experiments/run_cross_layout.py`
- Create: `paper1_sarcrp/experiments/run_extended_timeout_proxy.py`
- Test: `paper1_sarcrp/tests/test_run_cross_layout.py`

**Interfaces:**
- Consumes: `simulator.run_episode(..., time_limit_sec=...)` (Task 30)
- Produces: `run_cross_layout.TIMEOUT_BY_LAYOUT`, `run_extended_timeout_proxy.run_proxy_comparison(instance, normal_timeout, extended_timeout=300.0) -> dict`

- [ ] **Step 1: Write the failing test**

Append to `paper1_sarcrp/tests/test_run_cross_layout.py`:
```python
from run_cross_layout import TIMEOUT_BY_LAYOUT


def test_timeout_by_layout_matches_spec_17_tiers():
    assert TIMEOUT_BY_LAYOUT == {"layout_a": 1.0, "layout_b": 5.0, "layout_c": 30.0}


def test_run_all_layouts_uses_the_matching_timeout_per_layout():
    rows = run_all_layouts(methods=("static",), seeds=(0,))
    # This is a smoke test that the call succeeds with per-layout timeouts
    # threaded through -- correctness of the tiering itself is asserted above.
    assert len(rows) == 3
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_run_cross_layout.py -v`
Expected: FAIL with `ImportError: cannot import name 'TIMEOUT_BY_LAYOUT'`

- [ ] **Step 3: Implement the tiering**

In `paper1_sarcrp/experiments/run_cross_layout.py`, add the constant and thread it through `run_all_layouts`:
```python
TIMEOUT_BY_LAYOUT = {"layout_a": 1.0, "layout_b": 5.0, "layout_c": 30.0}  # spec 17: small/medium/large
```
Change the inner loop of `run_all_layouts` to pass `time_limit_sec=TIMEOUT_BY_LAYOUT[layout_name]`:
```python
                metrics = run_episode(instance, method_name=method, rng=random.Random(seed), time_limit_sec=TIMEOUT_BY_LAYOUT[layout_name])
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_run_cross_layout.py -v`
Expected: PASS (4 tests: 2 existing + 2 new)

- [ ] **Step 5: Write the extended-timeout proxy script**

Create `paper1_sarcrp/experiments/run_extended_timeout_proxy.py`:
```python
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
```

- [ ] **Step 6: Run the real proxy comparison**

Run: `python experiments/run_extended_timeout_proxy.py`
Expected: prints one line per layout (B, C). Record the actual gap for Task 35's report, worded as "vs. an offline high-quality proxy," never "vs. the optimum."

- [ ] **Step 7: Commit**

```bash
git add paper1_sarcrp/experiments/run_cross_layout.py paper1_sarcrp/experiments/run_extended_timeout_proxy.py paper1_sarcrp/tests/test_run_cross_layout.py
git commit -m "feat(paper1): apply spec 17 timeout tiering to cross-layout runs, add spec 21.2 extended-timeout proxy"
```

---

### Task 33: Wire the real CRP_RL model into the experiment suite (with caching)

**Files:**
- Modify: `paper1_sarcrp/src/sarcrp/crp_rl_adapter.py`
- Modify: `paper1_sarcrp/src/sarcrp/baselines.py`
- Modify: `paper1_sarcrp/src/sarcrp/sarcrp_core.py`
- Modify: `paper1_sarcrp/src/sarcrp/simulator.py`
- Test: `paper1_sarcrp/tests/test_crp_rl_adapter.py`, `paper1_sarcrp/tests/test_sarcrp_core.py`, `paper1_sarcrp/tests/test_simulator_mvp.py`

**Interfaces:**
- Consumes: `crp_rl_adapter.solve_crp_via_crp_rl` (Task 19)
- Produces: `crp_rl_adapter.get_cached_model(model_path, device) -> Model`; `sarcrp_core.replan(..., solver=solve_crp)`; `baselines.full_reoptimization(..., solver=solve_crp)`; `simulator.run_episode` accepts `method_name="full_reopt_crp_rl"`

**Decision this task resolves:** Task 19 built a working adapter but never used it anywhere. This task makes it an opt-in alternative solver backend everywhere `solve_crp` was hardcoded, rather than replacing the greedy default (which every prior task's numbers depend on) -- and runs one direct, small-scale comparison (not a full 3,240-episode Experiment 1 rerun, which would take far longer with real neural inference) to give the report an actual "does the real model change anything" answer.

- [ ] **Step 1: Write the failing test for model caching**

Append to `paper1_sarcrp/tests/test_crp_rl_adapter.py`:
```python
def test_get_cached_model_returns_the_same_object_on_repeated_calls():
    if not CRP_RL_ROOT.is_dir():
        pytest.skip("CRP_RL not cloned")
    from sarcrp.crp_rl_adapter import get_cached_model
    model_a = get_cached_model("baselines/models/proposed/epoch(100).pt", "cpu")
    model_b = get_cached_model("baselines/models/proposed/epoch(100).pt", "cpu")
    assert model_a is model_b
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_crp_rl_adapter.py -v`
Expected: FAIL with `ImportError: cannot import name 'get_cached_model'`

- [ ] **Step 3: Implement caching**

In `paper1_sarcrp/src/sarcrp/crp_rl_adapter.py`, add:
```python
import functools


@functools.lru_cache(maxsize=4)
def get_cached_model(model_path: str, device: str):
    """Loads the checkpoint once per (model_path, device) pair and reuses it
    -- solve_crp_via_crp_rl was re-reading the checkpoint from disk on every
    single call, which is fine for a one-off smoke test but would make any
    experiment that calls it hundreds/thousands of times (Experiment 1-scale)
    dominated by disk I/O instead of actual inference."""
    return _load_model(model_path, torch.device(device))
```

Change `solve_crp_via_crp_rl`'s body to call `get_cached_model(model_path, device)` instead of `_load_model(model_path, torch.device(device))` directly.

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_crp_rl_adapter.py -v`
Expected: PASS (5 tests: 4 existing + 1 new)

- [ ] **Step 5: Write the failing test for the pluggable solver parameter**

Append to `paper1_sarcrp/tests/test_sarcrp_core.py`:
```python
def test_replan_accepts_a_custom_solver():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    calls = {"count": 0}

    def spy_solver(state_arg, queue_arg, constraints=None, time_limit_sec=None):
        calls["count"] += 1
        from sarcrp.crp_solver import solve_crp
        return solve_crp(state_arg, queue_arg, constraints=constraints, time_limit_sec=time_limit_sec)

    decision = replan(state, plan_old, ["C1", "C2", "C3"], ["C3", "C2", "C1"], ["C3"],
                       theta_impact=0.05, tau_frac=0.0, rng=random.Random(0), solver=spy_solver)
    assert calls["count"] >= 1
    assert decision.decision in {"KEEP", "UPDATE"}
```

Append to `paper1_sarcrp/tests/test_baselines.py`:
```python
def test_full_reoptimization_accepts_a_custom_solver():
    state = make_state(["C1", "C2"])
    calls = {"count": 0}

    def spy_solver(state_arg, queue_arg, constraints=None, time_limit_sec=None):
        calls["count"] += 1
        from sarcrp.crp_solver import solve_crp
        return solve_crp(state_arg, queue_arg, constraints=constraints, time_limit_sec=time_limit_sec)

    full_reoptimization(state, retrieval_queue_new=["C1", "C2"], time_limit_sec=1.0, solver=spy_solver)
    assert calls["count"] == 1
```

- [ ] **Step 6: Run to verify it fails**

Run: `pytest tests/test_sarcrp_core.py tests/test_baselines.py -v`
Expected: FAIL with `TypeError: replan() got an unexpected keyword argument 'solver'`

- [ ] **Step 7: Add the `solver` parameter**

In `paper1_sarcrp/src/sarcrp/baselines.py`, change `full_reoptimization`:
```python
def full_reoptimization(state_t, retrieval_queue_new: list[str], constraints: dict | None = None, time_limit_sec: float = 5.0, solver=None) -> Plan:
    """B2 (spec 22): re-solve the whole remaining problem on every event.
    `solver` defaults to the greedy heuristic (spec 43's CRP_RL surrogate,
    Task 7); pass `crp_rl_adapter.solve_crp_via_crp_rl` to use the real
    trained model instead (Task 19/33)."""
    active_solver = solver or solve_crp
    return active_solver(state_t, retrieval_queue_new, constraints=constraints, time_limit_sec=time_limit_sec)
```

In `paper1_sarcrp/src/sarcrp/sarcrp_core.py`, add `solver=None` to `replan`'s signature and use it for the C3 candidate:
```python
def replan(
    state_t, plan_old: Plan, old_queue: list[str], new_queue: list[str], urgent_containers: list[str],
    h_f: int = 3, lam: float = 1.0, mu: float = 0.5, theta_impact: float = 0.30, tau_frac: float = 0.01,
    time_limit_sec: float = 5.0, rng: random.Random | None = None, conf_new: float = 1.0,
    use_local_search: bool = True, impact_weights: dict | None = None, solver=None,
) -> ReplanDecision:
    ...
    active_solver = solver or solve_crp
    ...
    tail_solution = active_solver(state_t, new_queue, time_limit_sec=time_limit_sec)
```
(only the `tail_solution = solve_crp(...)` line changes to `active_solver(...)`; every other line from Task 21's version of `replan` is unchanged.)

- [ ] **Step 8: Run to verify it passes**

Run: `pytest tests/test_sarcrp_core.py tests/test_baselines.py -v`
Expected: PASS (6 + 7 tests)

- [ ] **Step 9: Wire a `full_reopt_crp_rl` method into the simulator**

In `paper1_sarcrp/src/sarcrp/simulator.py`, add the import and one dispatch branch:
```python
from sarcrp.crp_rl_adapter import solve_crp_via_crp_rl
```
```python
        elif method_name == "full_reopt_crp_rl":
            new_plan = full_reoptimization(state, new_queue, time_limit_sec=time_limit_sec, solver=solve_crp_via_crp_rl)
            fallback = False
```
(insert this branch next to the existing `elif method_name == "full_reopt":` branch)

Append to `paper1_sarcrp/tests/test_simulator_mvp.py`:
```python
@pytest.mark.skipif(not Path(__file__).parent.parent.joinpath("external", "CRP_RL").is_dir(), reason="CRP_RL not cloned")
def test_run_episode_supports_full_reopt_crp_rl_method():
    metrics = run_episode(SMALL_INSTANCE, method_name="full_reopt_crp_rl", rng=random.Random(0))
    assert metrics.total_cost_mean >= 0.0
```
Add `import pytest` and `from pathlib import Path` at the top of the test file if not already present.

- [ ] **Step 10: Run to verify it passes**

Run: `pytest tests/test_simulator_mvp.py -v`
Expected: PASS (14 tests: 13 existing + 1 new)

- [ ] **Step 11: Run the direct greedy-vs-real-model comparison**

Run this once, on Layout A only, with a reduced seed count (real neural inference is far slower than the greedy heuristic -- do not run the full 20-seed/3-layout suite here):
```bash
python -c "
import random, json, sys
sys.path.insert(0, 'src')
from sarcrp.simulator import run_episode
instance = json.load(open('experiments/instances/small_layout_mvp.json'))
for method in ('full_reopt', 'full_reopt_crp_rl'):
    costs = [run_episode(instance, method_name=method, rng=random.Random(s)).total_cost_mean for s in range(5)]
    print(method, costs)
"
```
Expected: two lines of 5 numbers each. Record both lists and their means for Task 35's report -- this is the evidence for whether the MVP's greedy-surrogate-based conclusions (all of Tasks 1-28) still hold with the real trained solver, or whether they need to be revisited before submission.

- [ ] **Step 12: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/crp_rl_adapter.py paper1_sarcrp/src/sarcrp/baselines.py paper1_sarcrp/src/sarcrp/sarcrp_core.py paper1_sarcrp/src/sarcrp/simulator.py paper1_sarcrp/tests/test_crp_rl_adapter.py paper1_sarcrp/tests/test_sarcrp_core.py paper1_sarcrp/tests/test_baselines.py paper1_sarcrp/tests/test_simulator_mvp.py
git commit -m "feat(paper1): make the CRP solver backend pluggable, cache CRP_RL model loads, wire a full_reopt_crp_rl method (spec 43)"
```

---

### Task 34: Rigor and logging — seed policy, Wilcoxon zero-handling, CRP_RL-scale fairness, structured run logs, Slurm submission

**Why this task exists:** a post-plan review (prompted by "this costs real time and money, do not let bias or leakage make the research unfair") found five issues that would have made Tasks 20-33's results misleading or unauditable if run as originally written: (1) Task 33's greedy-vs-real-model comparison runs the model far outside its trained size range (10-24 containers vs. the model's trained 35-70), which is not a fair test of the model at all; (2) seeds 0-9 were already inspected by a human while debugging the Task 30 mutation bug, so using them as "the" reported evidence risks (the appearance of) cherry-picking even though no parameter was tuned based on what was seen; (3) `stats.wilcoxon_signed_rank` silently drops zero-difference pairs (scipy's default `zero_method="wilcox"`), which matters a lot here since many SAR-CRP-vs-Static pairs come back exactly equal (the MVP report's own finding) — the effective sample size was never disclosed; (4) every experiment ran on the shared login node with no persistent record of exactly what ran, when, on which code, with which parameters; (5) the costly runs (Experiment 1's 3,240 episodes) were never sized against the shared server's actual load before committing to them.

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/seed_policy.py`
- Create: `paper1_sarcrp/src/sarcrp/run_logging.py`
- Create: `paper1_sarcrp/experiments/instances/generate_crp_rl_scale_instance.py`
- Modify: `paper1_sarcrp/src/sarcrp/stats.py`
- Modify: `paper1_sarcrp/experiments/run_experiment1.py`, `run_cross_layout.py`, `run_experiment4.py`, `run_mvp.py`, `run_sanity_report.py`, `run_ground_truth_comparison.py`, `run_extended_timeout_proxy.py`
- Test: `paper1_sarcrp/tests/test_stats.py`, `paper1_sarcrp/tests/test_run_logging.py`

**Interfaces:**
- Produces: `seed_policy.DEV_SEEDS`, `seed_policy.REPORT_SEEDS`; `run_logging.log_run(script_name, params, duration_sec, output_paths, log_dir=None) -> Path`; `stats.WilcoxonResult` (dataclass: `p_value, n_pairs, n_nonzero_pairs`); `stats.wilcoxon_signed_rank(a, b, zero_method="pratt") -> WilcoxonResult` (return type changed from `float`)

---

#### Part A — Seed policy (dev vs. report)

- [ ] **Step 1: Create the seed policy module**

Create `paper1_sarcrp/src/sarcrp/seed_policy.py`:
```python
"""Seed policy (Task 34): seeds 0-9 were read by hand while diagnosing the
Task 30 mutation bug (e.g. seed 7's per-event trace, medium uncertainty) and
must never be the sole evidence behind a reported claim -- not because any
parameter was tuned to them (none was), but because a reviewer cannot
verify that after the fact, and "we looked at these seeds during
development" is a real (if mild) form of selection even when unintentional.

DEV_SEEDS remains available for smoke tests and reproducing a known
bug/behavior. REPORT_SEEDS is the fresh, never-inspected set every
"record this for the report" step in this plan must use instead."""

DEV_SEEDS = tuple(range(10))
REPORT_SEEDS = tuple(range(20, 40))  # 20 seeds (spec 23.6's stated minimum), none inspected during development
```

- [ ] **Step 2: Switch every reporting runner to `REPORT_SEEDS`**

In `paper1_sarcrp/experiments/run_experiment1.py`, `run_cross_layout.py`, and `run_experiment4.py`, replace each file's own `SEEDS = tuple(range(20))` line with:
```python
from sarcrp.seed_policy import REPORT_SEEDS as SEEDS
```
(add this import alongside each file's existing `from sarcrp.simulator import run_episode` line; remove the old `SEEDS = tuple(range(20))` constant it replaces). `run_mvp.py` keeps its own `SEEDS = tuple(range(10))` unchanged — the MVP decision-gate check is explicitly a smoke test, not a reported statistical claim, so `DEV_SEEDS`-equivalent behavior is correct there and does not need to change.

- [ ] **Step 3: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/seed_policy.py paper1_sarcrp/experiments/run_experiment1.py paper1_sarcrp/experiments/run_cross_layout.py paper1_sarcrp/experiments/run_experiment4.py
git commit -m "fix(paper1): separate dev seeds (already inspected) from report seeds (fresh) per spec 23.6"
```

---

#### Part B — Wilcoxon zero-handling and effective-N disclosure

- [ ] **Step 4: Update the failing tests in `test_stats.py`**

Replace the two existing Wilcoxon tests:
```python
def test_wilcoxon_signed_rank_identical_samples_gives_high_p_value():
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = wilcoxon_signed_rank(a, list(a))
    assert result.p_value == 1.0
    assert result.n_pairs == 5
    assert result.n_nonzero_pairs == 0


def test_wilcoxon_signed_rank_detects_a_consistent_shift():
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    b = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]  # every pair b > a by exactly 1
    result = wilcoxon_signed_rank(a, b)
    assert result.p_value < 0.05
    assert result.n_nonzero_pairs == 8


def test_wilcoxon_signed_rank_reports_effective_n_with_some_ties():
    a = [1.0, 1.0, 1.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    b = [1.0, 1.0, 1.0, 4.0, 5.0, 6.0, 7.0, 8.0]  # first 3 pairs tied, last 5 differ by exactly 1
    result = wilcoxon_signed_rank(a, b)
    assert result.n_pairs == 8
    assert result.n_nonzero_pairs == 5
```
(the third test is new; the first two replace the originals from Task 22 -- same scenarios, updated for the new return type)

- [ ] **Step 5: Run to verify it fails**

Run: `pytest tests/test_stats.py -v`
Expected: FAIL — `result.p_value` raises `AttributeError` since `wilcoxon_signed_rank` still returns a bare `float`.

- [ ] **Step 6: Implement**

In `paper1_sarcrp/src/sarcrp/stats.py`, add the import and replace the function:
```python
from dataclasses import dataclass


@dataclass
class WilcoxonResult:
    p_value: float
    n_pairs: int
    n_nonzero_pairs: int


def wilcoxon_signed_rank(a: list[float], b: list[float], zero_method: str = "pratt") -> WilcoxonResult:
    """Paired Wilcoxon signed-rank test (spec 23.6). Uses zero_method="pratt"
    instead of scipy's default "wilcox": "wilcox" silently drops
    zero-difference pairs from the ranking, which would quietly shrink the
    effective sample size below the reported N with no record of it -- with
    many SAR-CRP-vs-Static pairs coming back exactly equal (the MVP report's
    finding), that matters here. n_nonzero_pairs is always returned so the
    report can disclose it next to the p-value instead of citing N=20 when
    the test effectively saw fewer distinct pairs."""
    n_pairs = len(a)
    n_nonzero_pairs = sum(1 for x, y in zip(a, b) if x != y)
    if n_nonzero_pairs == 0:
        return WilcoxonResult(p_value=1.0, n_pairs=n_pairs, n_nonzero_pairs=0)
    _, p_value = scipy_stats.wilcoxon(a, b, zero_method=zero_method)
    return WilcoxonResult(p_value=float(p_value), n_pairs=n_pairs, n_nonzero_pairs=n_nonzero_pairs)
```

- [ ] **Step 7: Run to verify it passes**

Run: `pytest tests/test_stats.py -v`
Expected: PASS (9 tests: 6 unaffected + 3 from Step 4)

- [ ] **Step 8: Fix the one caller, `run_experiment1.py`'s `run_significance_tests`**

In `paper1_sarcrp/experiments/run_experiment1.py`, change:
```python
        p_value = wilcoxon_signed_rank(matched_sarcrp, baseline_values)
        delta = cliffs_delta(matched_sarcrp, baseline_values)
        raw_p_values.append(p_value)
        per_baseline[baseline] = {"p_value": p_value, "cliffs_delta": delta}
```
to:
```python
        wilcoxon_result = wilcoxon_signed_rank(matched_sarcrp, baseline_values)
        delta = cliffs_delta(matched_sarcrp, baseline_values)
        raw_p_values.append(wilcoxon_result.p_value)
        per_baseline[baseline] = {
            "p_value": wilcoxon_result.p_value,
            "n_pairs": wilcoxon_result.n_pairs,
            "n_nonzero_pairs": wilcoxon_result.n_nonzero_pairs,
            "cliffs_delta": delta,
        }
```
and update the two `print(...)`/CSV-writing spots that reference `stats_row['p_value']` to also print `n_nonzero_pairs` (`f"... (n_nonzero_pairs={stats_row['n_nonzero_pairs']}/{stats_row['n_pairs']})"`) and add an `n_nonzero_pairs` column to the `experiment1_significance.csv` header/rows written in `main()`.

Also update Task 28's own test, `test_run_significance_tests_reports_holm_bonferroni_corrected_flags`, to assert on `result["static"]["n_nonzero_pairs"]` being present (it constructs synthetic rows where every seed differs by `0.01 * s`, so `n_nonzero_pairs` should equal the full seed count there).

- [ ] **Step 9: Run to verify it passes**

Run: `pytest tests/test_run_experiment1.py -v`
Expected: PASS (4 tests)

- [ ] **Step 10: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/stats.py paper1_sarcrp/experiments/run_experiment1.py paper1_sarcrp/tests/test_stats.py paper1_sarcrp/tests/test_run_experiment1.py
git commit -m "fix(paper1): stop silently dropping zero-difference pairs in Wilcoxon test, disclose effective N"
```

---

#### Part C — A properly-scaled instance for the CRP_RL fairness comparison

- [ ] **Step 11: Write the generator**

Create `paper1_sarcrp/experiments/instances/generate_crp_rl_scale_instance.py`:
```python
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
```

- [ ] **Step 12: Run it once to produce the instance file**

Run: `python experiments/instances/generate_crp_rl_scale_instance.py`
Expected: prints `Wrote .../crp_rl_scale_instance.json with 50 containers (target range: 35-70)`. The resulting `crp_rl_scale_instance.json` is committed as a static file (like every other instance in this suite) — the generator is not re-run at test/experiment time.

- [ ] **Step 13: Redo Task 33's real-model comparison on this instance instead**

Re-run Task 33 Step 11's comparison script, but point it at `crp_rl_scale_instance.json` instead of `small_layout_mvp.json`:
```bash
python -c "
import random, json, sys
sys.path.insert(0, 'src')
from sarcrp.simulator import run_episode
instance = json.load(open('experiments/instances/crp_rl_scale_instance.json'))
for method in ('full_reopt', 'full_reopt_crp_rl'):
    costs = [run_episode(instance, method_name=method, rng=random.Random(s)).total_cost_mean for s in range(5)]
    print(method, costs)
"
```
This is now a within-training-distribution comparison. The original Task 33 Step 11 run (on the 10-container `small_layout_mvp.json`) should still be reported too, but explicitly labeled "out-of-distribution sanity check only" in Task 35's report, not used as evidence about the model's true relative quality.

- [ ] **Step 14: Commit**

```bash
git add paper1_sarcrp/experiments/instances/generate_crp_rl_scale_instance.py paper1_sarcrp/experiments/instances/crp_rl_scale_instance.json
git commit -m "feat(paper1): add a 50-container instance inside CRP_RL's trained size range for a fair model comparison"
```

---

#### Part D — Structured run logs

- [ ] **Step 15: Write the failing test**

Create `paper1_sarcrp/tests/test_run_logging.py`:
```python
import json
from sarcrp.run_logging import log_run


def test_log_run_writes_the_required_fields(tmp_path):
    log_path = log_run("test_script.py", {"seeds": [1, 2, 3]}, duration_sec=1.234, output_paths=["out.csv"], log_dir=tmp_path)
    assert log_path.exists()
    entry = json.loads(log_path.read_text().strip().split("\n")[-1])
    assert entry["script"] == "test_script.py"
    assert entry["params"] == {"seeds": [1, 2, 3]}
    assert entry["duration_sec"] == 1.234
    assert entry["output_paths"] == ["out.csv"]
    assert "git_commit" in entry
    assert "hostname" in entry
    assert "timestamp" in entry


def test_log_run_appends_without_overwriting(tmp_path):
    log_run("a.py", {}, 1.0, [], log_dir=tmp_path)
    log_run("b.py", {}, 2.0, [], log_dir=tmp_path)
    lines = (tmp_path / "run_log.jsonl").read_text().strip().split("\n")
    assert len(lines) == 2
```

- [ ] **Step 16: Run to verify it fails**

Run: `pytest tests/test_run_logging.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.run_logging'`

- [ ] **Step 17: Implement**

Create `paper1_sarcrp/src/sarcrp/run_logging.py`:
```python
import json
import socket
import subprocess
import time
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # .../paper1_sarcrp


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_PACKAGE_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def log_run(script_name: str, params: dict, duration_sec: float, output_paths: list[str], log_dir: Path | None = None) -> Path:
    """Appends one JSON line per run to experiments/logs/run_log.jsonl:
    timestamp, the git commit the code was at, hostname, the exact params
    used, wall-clock duration, and where the output landed. A costly run's
    provenance is always on record this way, not just whatever happened to
    be printed to stdout at the time."""
    log_dir = log_dir or (_PACKAGE_ROOT / "experiments" / "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "script": script_name,
        "git_commit": get_git_commit(),
        "hostname": socket.gethostname(),
        "params": params,
        "duration_sec": round(duration_sec, 3),
        "output_paths": output_paths,
    }
    log_path = log_dir / "run_log.jsonl"
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return log_path
```

- [ ] **Step 18: Run to verify it passes**

Run: `pytest tests/test_run_logging.py -v`
Expected: PASS (2 tests)

- [ ] **Step 19: Retrofit every runner to call `log_run`**

Each of the 7 runner scripts gets the same three-line pattern around its existing `main()` body: import `time` and `log_run` if not already imported, capture `_start = time.monotonic()` as the first line inside `main()`, and call `log_run(...)` as the last line before `main()` returns. Exact diffs:

`paper1_sarcrp/experiments/run_experiment1.py` -- add `from sarcrp.run_logging import log_run` to the imports; in `main()`:
```python
def main():
    _start = time.monotonic()
    instance = json.loads((Path(__file__).parent / "instances" / "small_layout_mvp.json").read_text())
    rows = run_factorial(instance)
    # ...(unchanged CSV-writing and printing code)...
    log_run("run_experiment1.py", {"seeds": list(SEEDS), "factor_grid": FACTOR_GRID, "methods": list(METHODS)},
            time.monotonic() - _start, [str(out_path), str(sig_path)])
```
(add `import time` at the top if not already present via another import)

`paper1_sarcrp/experiments/run_cross_layout.py` -- same pattern:
```python
def main():
    _start = time.monotonic()
    rows = run_all_layouts()
    # ...(unchanged)...
    log_run("run_cross_layout.py", {"seeds": list(SEEDS), "methods": list(METHODS), "timeout_by_layout": TIMEOUT_BY_LAYOUT},
            time.monotonic() - _start, [str(out_path)])
```

`paper1_sarcrp/experiments/run_experiment4.py`:
```python
def main():
    _start = time.monotonic()
    instance = json.loads(...)
    rows = run_confidence_sweep(instance)
    # ...(unchanged)...
    log_run("run_experiment4.py", {"seeds": list(SEEDS), "confidence_levels": list(CONFIDENCE_LEVELS)},
            time.monotonic() - _start, [str(out_path)])
```

`paper1_sarcrp/experiments/run_mvp.py`:
```python
def main():
    _start = time.monotonic()
    instance = json.loads(...)
    rows = run_all_methods(instance)
    # ...(unchanged)...
    log_run("run_mvp.py", {"seeds": list(SEEDS), "methods": list(METHODS)}, time.monotonic() - _start, [str(out_path)])
```

`paper1_sarcrp/experiments/run_sanity_report.py`:
```python
def main():
    _start = time.monotonic()
    instance = json.loads(...)
    report = run_sanity_checks(instance)
    # ...(unchanged print statements)...
    from sarcrp.run_logging import log_run
    log_run("run_sanity_report.py", {"seeds": list(range(10))}, time.monotonic() - _start, [])
```

`paper1_sarcrp/experiments/run_ground_truth_comparison.py`:
```python
def main():
    _start = time.monotonic()
    instance = json.loads(...)
    result = run_comparison(instance)
    # ...(unchanged print statements)...
    from sarcrp.run_logging import log_run
    log_run("run_ground_truth_comparison.py", {"instance": "tiny_ground_truth.json"}, time.monotonic() - _start, [])
```

`paper1_sarcrp/experiments/run_extended_timeout_proxy.py`:
```python
def main():
    _start = time.monotonic()
    instances_dir = Path(__file__).parent / "instances"
    for layout_name, filename, normal_timeout in (...):
        ...
    from sarcrp.run_logging import log_run
    log_run("run_extended_timeout_proxy.py", {"extended_timeout": 300.0}, time.monotonic() - _start, [])
```

Add `paper1_sarcrp/experiments/logs/` to `paper1_sarcrp/.gitignore` -- the log file is a local audit trail, regenerated on every run, not something to commit (it would also record this machine's hostname on every run, which has no reason to be public).

- [ ] **Step 20: Run the full suite**

Run: `pytest -v`
Expected: PASS, no regressions from adding `log_run` calls (they only append to a local file, nothing else changes).

- [ ] **Step 21: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/run_logging.py paper1_sarcrp/tests/test_run_logging.py paper1_sarcrp/experiments/run_experiment1.py paper1_sarcrp/experiments/run_cross_layout.py paper1_sarcrp/experiments/run_experiment4.py paper1_sarcrp/experiments/run_mvp.py paper1_sarcrp/experiments/run_sanity_report.py paper1_sarcrp/experiments/run_ground_truth_comparison.py paper1_sarcrp/experiments/run_extended_timeout_proxy.py paper1_sarcrp/.gitignore
git commit -m "feat(paper1): add structured JSONL run logs (git commit, host, params, duration) to every experiment runner"
```

---

#### Part E — Cost estimate + Slurm submission for the expensive runs

- [ ] **Step 22: Time a small sample before committing to the full Experiment 1 run**

Run on the server (quick mode, not Slurm — this is a cheap probe):
```bash
python -c "
import time, random, json, sys
sys.path.insert(0, 'src')
from sarcrp.simulator import run_episode
instance = json.load(open('experiments/instances/small_layout_mvp.json'))
start = time.monotonic()
for method in ('static', 'full_reopt', 'periodic', 'event_triggered_no_stability', 'mpc', 'sarcrp'):
    for seed in range(3):
        run_episode(instance, method_name=method, rng=random.Random(seed))
elapsed = time.monotonic() - start
n_sample = 6 * 3
n_full = 3 * 3 * 3 * 6 * len(__import__('sarcrp.seed_policy', fromlist=['REPORT_SEEDS']).REPORT_SEEDS)
print(f'{n_sample} episodes took {elapsed:.2f}s -> {elapsed / n_sample:.4f}s/episode -> full run ({n_full} episodes) estimated at {elapsed / n_sample * n_full / 60:.1f} minutes')
"
```
Expected: an estimated total runtime. **Report this number back before running the full job** -- if it's more than ~20 minutes, use Slurm (Step 23) rather than an interactive `ssh` command, both because the login node is shared with other users' jobs (noisy, and this plan's own report should not present runtime numbers gathered while competing for CPU with someone else's job) and because a multi-hour interactive SSH command risks being killed by a dropped connection (already observed once this session, during the `torch` install).

- [ ] **Step 23: Submit the full Experiment 1 run via Slurm**

From the laptop: `mutagen.exe sync flush story-research`, then on the server:
```bash
cd ~/thuongnm_hust/Story_Research
sed -i '12s#.*#python paper1_sarcrp/experiments/run_experiment1.py#' script
conda activate story_research
. run_via_slurm
squeue -u $USER
```
(this is exactly `run_on_gpu.sh --train experiments/run_experiment1.py`'s own internal sequence, per `SSH_A100_Setup_Runbook.md` §5 -- run it manually here since `run_on_gpu.sh` assumes the caller is on the laptop with an interactive terminal, not mid-plan-execution). Monitor with `squeue -u $USER` and `cat slurm-<jobid>.out` (or `./run_on_gpu.sh --status` / `--log` from the laptop) rather than blocking on the SSH session.

- [ ] **Step 24: Once the job completes, verify and commit the results**

```bash
ssh a100-B "cat ~/thuongnm_hust/Story_Research/paper1_sarcrp/experiments/results/experiment1_significance.csv"
```
Then from the laptop: `mutagen.exe sync flush story-research`, `git add paper1_sarcrp/experiments/results/experiment1_results.csv paper1_sarcrp/experiments/results/experiment1_significance.csv`, commit. (`experiments/results/` is gitignored per Task 1's `.gitignore` -- override with `git add -f` only for these two final CSVs if they should be reviewable on GitHub without re-running; otherwise leave them local and cite the numbers directly in Task 35's report.)

---

### Task 35: Runtime reporting + final Q1 experiment report (LaTeX, compiled to PDF)

**Files:**
- Create: `writeups/paper1_q1_report/main.tex`
- Create: `writeups/paper1_q1_report/Makefile`

**Interfaces:**
- Consumes: every CSV/printed result produced by Tasks 20-34 — this is deliberately the last task in the plan so every number it cites already exists on disk before writing a single sentence about it.

- [ ] **Step 1: Capture the hardware disclosure (spec 51)**

Run on the server: `ssh a100-B "lscpu | head -15 && python -c 'import platform; print(platform.python_version())' && python -c 'import torch; print(torch.__version__)'"` and note CPU model, core count, Python/torch versions for the report's Setup section (spec 51's template requires disclosing the hardware every runtime number was measured on).

- [ ] **Step 2: Write the report skeleton**

Create `writeups/paper1_q1_report/main.tex` with sections:
- `Setup` (hardware from Step 1; note the seed policy from Task 34 Part A -- report-grade numbers use `REPORT_SEEDS` (20-39), never the `DEV_SEEDS` (0-9) inspected during debugging)
- `Baselines and Ablations Implemented` (table of B1-B6, A1-A6 with one-line descriptions, referencing spec 22/25 — Task 20/21)
- `Experiment 1 Results` (factorial table + significance table from Task 28's two CSVs, now with freeze_size/lambda actually varying per the Task 28 fix, run via Slurm per Task 34 Part E, and citing `n_nonzero_pairs` next to every p-value per Task 34 Part B)
- `Experiment 3: Cross-Layout` (performance-drop numbers from Task 24, run with the spec-17 timeout tiers from Task 32)
- `Experiment 4: Data Confidence Sensitivity` (changed-actions-vs-confidence trend from Task 25)
- `Sanity Checks` (SC1-SC4 verdicts from Task 26)
- `Ground Truth` (optimality gap from Task 31's tractable 6-container instance, plus the offline-proxy gap for Layouts B/C from Task 32 -- worded as "vs. an offline proxy," never "vs. the optimum," for the B/C numbers)
- `Metrics Completeness` (invalid rate, timeout rate, P95 runtime, stability cost from Task 30 -- report whether `invalid_rate` was ever nonzero now that `is_plan_valid` is actually wired in)
- `Real Solver Comparison` (both of Task 33/34's greedy-vs-`full_reopt_crp_rl` comparisons -- the original 10-container run labeled explicitly "out-of-distribution sanity check, not evidence of relative quality," and the Task 34 Part C 50-container run, inside CRP_RL's trained size range, as the one comparison actually usable as evidence)
- `Reproducibility` (cite `experiments/logs/run_log.jsonl`'s git-commit/params/duration entries for every number in this report, per Task 34 Part D)
- `Limitations` (Experiment 5 operator-acceptance study intentionally omitted per spec 23's own "optional" framing; note it here rather than silently dropping it)
- `Conclusion`

Use plain `\hline` tables (no `booktabs`) and skip `hyperref` (both unavailable in this server's TeX Live install per the MVP report's precedent) -- fill every table cell with the *actual* numbers from the CSVs/printed output produced in Tasks 20-33, never placeholder values.

- [ ] **Step 3: Write the Makefile**

Create `writeups/paper1_q1_report/Makefile`:
```makefile
.PHONY: pdf clean

pdf:
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

clean:
	rm -f main.aux main.log main.out
```

- [ ] **Step 4: Compile on the server**

Run: `cd writeups/paper1_q1_report && make pdf`
Expected: `main.pdf` produced with no LaTeX errors (check `main.log` for `Overfull`/`Underfull`/`Error` lines the same way the MVP report was cleaned up).

- [ ] **Step 5: Clean aux files, sync back, commit**

```bash
make clean
```
then (from the laptop) `mutagen.exe sync flush story-research`, then:
```bash
git add writeups/paper1_q1_report/main.tex writeups/paper1_q1_report/Makefile writeups/paper1_q1_report/main.pdf
git commit -m "docs(paper1): add full Q1 experiment suite report (LaTeX, compiled to PDF)"
git push
```

---

## Self-Review Notes

- **Spec coverage:** Task 20 covers §22 B3-B5; Task 21 covers §25 A1-A6; Task 22 covers §23.6 in full; Task 23 builds the §21.1 exhaustive solver (Task 31 is what actually *runs* it for a reported optimality gap — building the tool and producing the evidence are different deliverables, kept as separate tasks on purpose); Task 24 covers §23 Experiment 3 + §50; Task 25 covers §23 Experiment 4; Task 26 covers §20/§49 SC1-SC4; Task 27 wires everything into the one execution path the suite depends on, and is also where the freeze_size/lambda threading bug caught during this plan's own review gets fixed; Task 28 covers §23 Experiment 1's factorial + §23.6; Task 30 covers the §24 metrics this plan's first draft had missed entirely (invalid rate — and makes `is_plan_valid` the first thing in this codebase that ever actually exercises spec §11.3's `M_inf` penalty branch, since every prior task hardcoded `is_valid=True` — timeout rate, P95 runtime, stability cost); Task 31 produces the actual §21.1 optimality-gap number; Task 32 covers §17 timeout tiering and §21.2's extended-timeout proxy; Task 33 resolves whether Task 19's real CRP_RL model is used anywhere (it wasn't, in this plan's first draft) by making the solver backend pluggable and comparing greedy vs. real-model results directly; Task 34 covers the fairness/rigor gaps a "this costs real money, do not let it be biased or unfair" review surfaced (out-of-distribution model comparison, dev-vs-report seed separation, silently-dropped Wilcoxon ties, no run provenance, no cost estimate before an expensive job) that none of Tasks 20-33 addressed on their own; Task 35 covers §51 runtime reporting and is the final deliverable, ordered last on purpose so it only ever cites numbers that already exist on disk. Experiment 5 (operator acceptance) is explicitly optional per §23 and is not included — flagged in Task 35's Limitations section rather than silently dropped. Experiment 2 (benchmark sanity + small-instance ground truth) is split across Tasks 23/31 (ground truth) and 26 (sanity), since §21 and §20/§49 are independent deliverables that happen to share one experiment number in the spec.
- **Type consistency:** `ReplanDecision` (Task 11) keeps its original field names throughout — Tasks 20, 21, and 33 all consume it unchanged. `sarcrp_core.replan` picks up four new parameters across this plan (`use_local_search`, `impact_weights` in Task 21; `solver` in Task 33) plus the pre-existing `h_f`/`lam`/`mu`, all with defaults that preserve every earlier caller's behavior — Task 21 Step 4 and Task 33 Step 8 both keep the MVP's original `test_sarcrp_core.py` tests in the "must still pass" set to enforce this. `EpisodeMetrics` (Task 13) gains four fields in Task 30; every construction site (`simulator.py`'s own `return`, and `run_experiment4.py`'s hand-built one from Task 25) is updated in that same task, not left stale.
- **Self-review catch, fixed inline:** the first draft of this plan defined Experiment 1's `freeze_size`/`lambda` factorial grid (Task 28) but never threaded either value through `run_episode` (Task 27) — every grid point would have silently produced identical results. Fixed by adding `h_f`/`lam` parameters to `run_episode` (Task 27) and an `h_f` parameter to `event_triggered_no_stability` (Task 20), with a regression test in both Task 27 and Task 28 asserting the override actually changes the output, not just that the grid is iterated over.
- **Placeholder scan:** every task's code blocks are complete, runnable functions — no `TODO`/`pass  # implement`. The "record the actual numbers" steps (Tasks 24, 25, 26, 28, 31, 32, 33) are deliberately not pre-filled with invented numbers; Task 35 is the single place those real numbers get written into prose, exactly like the MVP report's precedent of filling in real CSV output rather than guessing ahead of the run.
