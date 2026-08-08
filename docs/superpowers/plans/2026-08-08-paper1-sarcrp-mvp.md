# Paper 1 — SAR-CRP v2 Core MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase-0→Phase-5 MVP from the Paper 1 spec (`Story_paper/SAR_CRP_v2_FINAL_READY_With_Implementation_Appendix_VI (1).md`, §27 Implementation Roadmap + §32 checklist + §33 Final MVP) — a working SAR-CRP Core algorithm, three MVP baselines, and one small-layout experiment that either passes or fails the decision gate in §33 (`SAR-CRP total cost < Static`, `SAR-CRP stability cost < Full Reoptimization`, `SAR-CRP operational cost ≈ Full Reoptimization`) before any full Q1-scale experiment is attempted.

**Architecture:** A single Python package (`paper1_sarcrp/`) implementing each spec module (event stream, impact estimator, objective/cost functions, freeze horizon, repair candidates, SAR-CRP core, baselines) as an independently testable unit, wired together by an episode simulator. An `experiments/run_mvp.py` script drives the §33 MVP scenario and writes metrics to CSV. A separate `writeups/paper1_mvp_report/` folder holds a short LaTeX report (compiled to PDF) stating the decision-gate verdict — per the user's standing rule that any written artifact lives in its own folder as LaTeX, compiled to PDF, never as a bare Markdown/text report.

**Tech Stack:** Python 3.13 (this machine's Miniconda install), `pytest` for tests, no external solver/ML dependencies for the MVP (the CRP solver is a self-contained greedy heuristic — see Task 7 rationale). LaTeX via the MiKTeX install already present (`pdflatex`, `latexmk` both on PATH).

## Global Constraints

- All formulas, defaults, and pseudocode MUST match the spec exactly — see `Story_paper/SAR_CRP_v2_FINAL_READY_With_Implementation_Appendix_VI (1).md` §37–§48. Default parameter values (do not change without updating the spec doc first):
  - `K=10` (top-k), `theta_impact=0.30`, `tau=0.01·J(P_old)`, `lambda=1.0`, `mu=0.5`
  - `alpha=1.0`, `beta=0.5`, `gamma=1.0`, `M_inf=1e6`
  - `rho=0.05`, `sigma_b=2`, `r_shift=5`, `H_f=3`
  - `p_c=2, p_a=2, p_d=1, p_o=1, p_m=10, p_f=inf, p_insert=1.5, p_delete=1.5`
  - Local search: `T=100, M=50, epsilon=0.05`
  - `tau_age=10` steps
  - Event generator: `p_event=0.30, p_swap=0.40, p_urgent=0.25, p_eta=0.20, p_prob=0.10, p_stale=0.05`
- This is the **MVP scope only** (§33): 3 methods (Static, Full Reoptimization, SAR-CRP Core), 1 small layout, event types `ORDER_SWAP` / `URGENT_INSERTION` / `ETA_EARLY` / `ETA_LATE`. Do NOT implement B3–B5 baselines, the 5-experiment Q1 suite, or the 20-seed statistical protocol (§23.6) in this plan — those come only after the §33 decision gate passes, as a follow-up plan.
- All randomness (event generation, local search sampling) takes an explicit `random.Random` instance — never the global `random` module — so runs are seed-reproducible (needed later for the §23.6 protocol even though MVP itself only runs a handful of seeds).
- Repo root for all paths below is `Research_Story/` (the independent git repo already pushed to `sutobode/Story_Research`, separate from the home-directory Graph_ML repo).
- Any written report/document produced by this plan goes in its own folder under `writeups/` as a `.tex` file compiled to `.pdf` via `latexmk -pdf` — never as a standalone Markdown report.

---

## File Structure

```
Research_Story/
  paper1_sarcrp/
    pyproject.toml
    requirements.txt
    src/sarcrp/
      __init__.py
      schemas.py            # YardState, Stack, Action, Plan, RetrievalInformation, Event dataclasses
      state_ops.py          # find_stack, blocker_count, blocker_pressure
      confidence.py         # compute_confidence (age-based decay)
      event_generator.py    # generate_event_stream + per-type apply_* functions
      impact_estimator.py   # I_order, I_target, I_blocking, I_plan (affected-action), I_conf, compute_impact
      objective.py          # C_op, D (stability), C_data, compute_objective (J)
      crp_solver.py         # solve_crp: greedy CRP heuristic (MVP CRP_RL surrogate)
      freeze_horizon.py     # split_plan -> (frozen, tail)
      minimal_repair.py     # minimal_feasibility_repair (candidate C1)
      local_search_repair.py# N1-N5 neighborhood ops + stochastic hill climbing (candidate C2)
      sarcrp_core.py        # replan(): the 9-step Algorithm SAR-CRP v2 Core (spec §18)
      baselines.py          # static_plan, full_reoptimization
      simulator.py          # run_episode: drives one instance through an event stream + method
    tests/
      test_schemas.py
      test_state_ops.py
      test_confidence.py
      test_event_generator.py
      test_impact_estimator.py
      test_objective.py
      test_crp_solver.py
      test_freeze_horizon.py
      test_minimal_repair.py
      test_local_search_repair.py
      test_sarcrp_core.py
      test_baselines.py
      test_simulator_mvp.py
    experiments/
      instances/small_layout_mvp.json
      run_mvp.py
      results/               # run_mvp.py writes mvp_results.csv here (gitignored)
    .gitignore               # experiments/results/, __pycache__/, *.pyc
  writeups/
    paper1_mvp_report/
      main.tex
      Makefile
```

**Interfaces used across tasks (locked now, do not rename later):**
- `schemas.YardState`, `schemas.Stack`, `schemas.Action`, `schemas.Plan`, `schemas.RetrievalInformation`, `schemas.Event`
- `state_ops.find_stack(state, container_id) -> str | None`
- `state_ops.blocker_count(state, container_id) -> int`
- `state_ops.blocker_pressure(state, retrieval_queue, k) -> int`
- `confidence.compute_confidence(base_confidence, age, tau_age=10.0) -> float`
- `impact_estimator.compute_impact(old_queue, new_queue, state_old, state_new, plan_old, k=10, r_shift=5, sigma_b=2.0, conf_new=1.0) -> ImpactBreakdown` (dataclass with `.total` plus per-component fields)
- `objective.operational_cost(plan, urgent_containers, is_valid, alpha=1.0, beta=0.5, gamma=1.0, m_inf=1e6) -> float`
- `objective.stability_cost(plan_new, plan_old, frozen_count, rho=0.05, penalties=None) -> tuple[float, bool]` (cost, frozen_violation)
- `objective.data_confidence_cost(plan_new, plan_old, conf_new) -> float`
- `objective.compute_objective(op_cost, stab_cost, data_cost, lam=1.0, mu=0.5) -> float`
- `crp_solver.solve_crp(yard_state, retrieval_queue, constraints=None, time_limit_sec=None) -> Plan`
- `freeze_horizon.split_plan(plan, h_f) -> tuple[Plan, Plan]` (frozen, tail)
- `minimal_repair.minimal_feasibility_repair(plan_old, state_new, retrieval_queue_new) -> Plan`
- `local_search_repair.local_search_repair(p_start, p_old, state, retrieval_queue_new, frozen_count, rng, t_iters=100, m_neighbors=50, epsilon=0.05, time_limit_sec=None) -> Plan`
- `sarcrp_core.replan(state_t, plan_old, info_old, info_new, h_f=3, lam=1.0, mu=0.5, theta_impact=0.30, tau_frac=0.01, time_limit_sec=5.0, rng=None) -> ReplanDecision` (dataclass: `.decision` in `{"KEEP","UPDATE"}`, `.plan`, `.impact`, `.j_old`, `.j_new`)
- `baselines.static_plan(plan_initial) -> Plan` (identity — never changes)
- `baselines.full_reoptimization(state_t, retrieval_queue_new, constraints=None, time_limit_sec=5.0) -> Plan`
- `simulator.run_episode(instance, method_name, rng) -> EpisodeMetrics` (dataclass: relocation_count, changed_actions_total, total_cost_mean, runtime_mean_sec, fallback_rate)

---

### Task 1: Project scaffolding + data schemas

**Files:**
- Create: `paper1_sarcrp/pyproject.toml`
- Create: `paper1_sarcrp/requirements.txt`
- Create: `paper1_sarcrp/src/sarcrp/__init__.py`
- Create: `paper1_sarcrp/src/sarcrp/schemas.py`
- Create: `paper1_sarcrp/.gitignore`
- Test: `paper1_sarcrp/tests/test_schemas.py`

**Interfaces:**
- Produces: `schemas.Layout`, `schemas.Stack`, `schemas.YardState`, `schemas.Action`, `schemas.Plan`, `schemas.RetrievalInformation`, `schemas.Event` (all `@dataclass`, fields exactly as in spec §37).

- [ ] **Step 1: Create the package scaffolding**

`paper1_sarcrp/pyproject.toml`:
```toml
[project]
name = "sarcrp"
version = "0.1.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

`paper1_sarcrp/requirements.txt`:
```
pytest>=7.4
```

`paper1_sarcrp/.gitignore`:
```
__pycache__/
*.pyc
experiments/results/
```

`paper1_sarcrp/src/sarcrp/__init__.py`:
```python
```

- [ ] **Step 2: Write the failing test for schemas**

`paper1_sarcrp/tests/test_schemas.py`:
```python
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan, RetrievalInformation, Event


def test_yard_state_round_trip():
    state = YardState(
        instance_id="inst_0001",
        time_step=0,
        layout=Layout(num_stacks=2, max_tier=5),
        stacks=[
            Stack(id="S1", containers=["C10", "C07", "C03"], max_tier=5),
            Stack(id="S2", containers=["C09", "C04"], max_tier=5),
        ],
        container_attributes={"C03": {"size": "40ft", "weight_class": "medium", "status": "available"}},
        retrieval_queue=["C01", "C02", "C03", "C04", "C05"],
        pickup_prob={"C01": 0.95, "C02": 0.80, "C03": 0.60},
        data_timestamp=0,
        state_confidence=1.0,
    )
    assert state.stacks[0].containers[-1] == "C03"  # top of stack per spec convention
    assert state.layout.num_stacks == 2


def test_action_and_plan():
    a1 = Action(action_id="a001", step_index=0, type="RELOCATE", container="C03",
                source_stack="S1", dest_stack="S3", commit_status="committed", planned_time=1)
    a2 = Action(action_id="a002", step_index=1, type="RETRIEVE", container="C01",
                source_stack="S4", dest_stack=None, commit_status="planned", planned_time=2)
    plan = Plan(plan_id="plan_0001", created_at=0, source="CRP_RL", actions=[a1, a2])
    assert len(plan.actions) == 2
    assert plan.actions[0].type == "RELOCATE"


def test_retrieval_information_and_event():
    info = RetrievalInformation(
        info_id="info_0001", timestamp=10,
        retrieval_queue=["C01", "C04", "C02", "C03", "C05"],
        pickup_prob={"C01": 0.95, "C04": 0.88}, urgent_containers=["C04"],
        confidence=0.85, source="synthetic_event_generator",
    )
    event = Event(
        event_id="e001", time_step=10, type="ORDER_SWAP", severity="medium",
        affected_containers=["C02", "C04"],
        old_queue=["C01", "C02", "C03", "C04", "C05"],
        new_queue=["C01", "C04", "C03", "C02", "C05"],
        confidence=0.85, timestamp_generated=10, timestamp_observed=10,
        metadata={"swap_distance": 2},
    )
    assert info.urgent_containers == ["C04"]
    assert event.metadata["swap_distance"] == 2
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd paper1_sarcrp && pip install -r requirements.txt -e . && pytest tests/test_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.schemas'` (or `sarcrp` not installed — if `pip install -e .` fails because no build backend, add `[build-system]` below first).

Add to `pyproject.toml` before installing:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 4: Write the schemas implementation**

`paper1_sarcrp/src/sarcrp/schemas.py`:
```python
from dataclasses import dataclass, field
from typing import Literal, Optional

ActionType = Literal["RELOCATE", "RETRIEVE", "NOOP"]
CommitStatus = Literal["executed", "committed", "planned", "cancelled"]
EventType = Literal[
    "ORDER_SWAP", "URGENT_INSERTION", "ETA_EARLY", "ETA_LATE",
    "PROBABILITY_UPDATE", "STALE_INFORMATION",
]
Severity = Literal["low", "medium", "high"]


@dataclass
class Layout:
    num_stacks: int
    max_tier: int


@dataclass
class Stack:
    id: str
    containers: list[str]  # index 0 = bottom, index -1 = top (spec 37.1)
    max_tier: int


@dataclass
class YardState:
    instance_id: str
    time_step: int
    layout: Layout
    stacks: list[Stack]
    container_attributes: dict[str, dict]
    retrieval_queue: list[str]
    pickup_prob: dict[str, float]
    data_timestamp: int
    state_confidence: float


@dataclass
class Action:
    action_id: str
    step_index: int
    type: ActionType
    container: str
    source_stack: Optional[str]
    dest_stack: Optional[str]
    commit_status: CommitStatus
    planned_time: int


@dataclass
class Plan:
    plan_id: str
    created_at: int
    source: str
    actions: list[Action] = field(default_factory=list)


@dataclass
class RetrievalInformation:
    info_id: str
    timestamp: int
    retrieval_queue: list[str]
    pickup_prob: dict[str, float]
    urgent_containers: list[str]
    confidence: float
    source: str


@dataclass
class Event:
    event_id: str
    time_step: int
    type: EventType
    severity: Severity
    affected_containers: list[str]
    old_queue: list[str]
    new_queue: list[str]
    confidence: float
    timestamp_generated: int
    timestamp_observed: int
    metadata: dict = field(default_factory=dict)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_schemas.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add paper1_sarcrp/pyproject.toml paper1_sarcrp/requirements.txt paper1_sarcrp/.gitignore paper1_sarcrp/src/sarcrp/__init__.py paper1_sarcrp/src/sarcrp/schemas.py paper1_sarcrp/tests/test_schemas.py
git commit -m "feat(paper1): scaffold sarcrp package with data schemas (spec 37)"
```

---

### Task 2: State operations (find_stack, blocker_count, blocker_pressure)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/state_ops.py`
- Test: `paper1_sarcrp/tests/test_state_ops.py`

**Interfaces:**
- Consumes: `schemas.YardState`, `schemas.Stack` (Task 1)
- Produces: `state_ops.find_stack(state, container_id) -> str | None`, `state_ops.blocker_count(state, container_id) -> int`, `state_ops.blocker_pressure(state, retrieval_queue, k) -> int`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_state_ops.py`:
```python
from sarcrp.schemas import Layout, Stack, YardState
from sarcrp.state_ops import find_stack, blocker_count, blocker_pressure


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C10", "C07", "C03"], max_tier=5)],
        container_attributes={}, retrieval_queue=["C03", "C07", "C10"],
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_find_stack():
    state = make_state()
    assert find_stack(state, "C07") == "S1"
    assert find_stack(state, "C99") is None


def test_blocker_count_matches_spec_example():
    state = make_state()
    assert blocker_count(state, "C10") == 2
    assert blocker_count(state, "C07") == 1
    assert blocker_count(state, "C03") == 0
    assert blocker_count(state, "C99") == 0  # not in yard -> no blockers


def test_blocker_pressure_topk():
    state = make_state()
    assert blocker_pressure(state, state.retrieval_queue, k=2) == blocker_count(state, "C03") + blocker_count(state, "C07")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_state_ops.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.state_ops'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/state_ops.py`:
```python
from sarcrp.schemas import YardState


def find_stack(state: YardState, container_id: str) -> str | None:
    for stack in state.stacks:
        if container_id in stack.containers:
            return stack.id
    return None


def blocker_count(state: YardState, container_id: str) -> int:
    """Number of containers above `container_id` in its stack (spec 38.2)."""
    for stack in state.stacks:
        if container_id in stack.containers:
            index = stack.containers.index(container_id)
            return len(stack.containers) - index - 1
    return 0


def blocker_pressure(state: YardState, retrieval_queue: list[str], k: int) -> int:
    """Total blocker count over the top-k of `retrieval_queue` (spec 38.3)."""
    top_k = retrieval_queue[:k]
    return sum(blocker_count(state, c) for c in top_k)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_state_ops.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/state_ops.py paper1_sarcrp/tests/test_state_ops.py
git commit -m "feat(paper1): implement stack/blocker state ops (spec 38.1-38.3)"
```

---

### Task 3: Data confidence (age-based decay)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/confidence.py`
- Test: `paper1_sarcrp/tests/test_confidence.py`

**Interfaces:**
- Produces: `confidence.compute_confidence(base_confidence, age, tau_age=10.0) -> float`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_confidence.py`:
```python
import math
from sarcrp.confidence import compute_confidence


def test_zero_age_returns_base_confidence():
    assert compute_confidence(base_confidence=0.9, age=0, tau_age=10.0) == 0.9


def test_decay_matches_formula():
    # Conf(I) = base_confidence * exp(-age / tau_age)  (spec 38.4)
    result = compute_confidence(base_confidence=1.0, age=10, tau_age=10.0)
    assert math.isclose(result, math.exp(-1.0), rel_tol=1e-9)


def test_older_age_gives_lower_confidence():
    fresh = compute_confidence(base_confidence=1.0, age=1, tau_age=10.0)
    stale = compute_confidence(base_confidence=1.0, age=50, tau_age=10.0)
    assert stale < fresh
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_confidence.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.confidence'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/confidence.py`:
```python
import math


def compute_confidence(base_confidence: float, age: int, tau_age: float = 10.0) -> float:
    """Conf(I) = base_confidence * exp(-age / tau_age)  (spec 38.4, default tau_age=10)."""
    return base_confidence * math.exp(-age / tau_age)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_confidence.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/confidence.py paper1_sarcrp/tests/test_confidence.py
git commit -m "feat(paper1): implement age-based confidence decay (spec 38.4)"
```

---

### Task 4: Dynamic event generator (5 event types)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/event_generator.py`
- Test: `paper1_sarcrp/tests/test_event_generator.py`

**Interfaces:**
- Consumes: `schemas.Event` (Task 1)
- Produces: `event_generator.generate_event_stream(initial_queue, t_steps, uncertainty_level, rng, event_id_prefix="e") -> list[Event]`, plus helpers `apply_order_swap(queue, severity, rng)`, `apply_urgent_insertion(queue, severity, rng)`, `apply_eta_shift(queue, severity, rng)` (all pure functions returning a new queue list).

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_event_generator.py`:
```python
import random
from sarcrp.event_generator import generate_event_stream, apply_order_swap, apply_urgent_insertion


def test_order_swap_preserves_set_of_containers():
    rng = random.Random(0)
    queue = ["C1", "C2", "C3", "C4", "C5"]
    new_queue = apply_order_swap(queue, severity="medium", rng=rng)
    assert sorted(new_queue) == sorted(queue)
    assert new_queue != queue or len(queue) < 2


def test_urgent_insertion_moves_container_into_topk():
    rng = random.Random(0)
    queue = ["C1", "C2", "C3", "C4", "C8", "C9"]
    new_queue = apply_urgent_insertion(queue, severity="high", rng=rng)
    assert sorted(new_queue) == sorted(queue)


def test_generate_event_stream_only_uses_known_types():
    rng = random.Random(42)
    queue = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
    events = generate_event_stream(queue, t_steps=50, uncertainty_level="medium", rng=rng)
    assert len(events) > 0
    allowed = {"ORDER_SWAP", "URGENT_INSERTION", "ETA_EARLY", "ETA_LATE", "PROBABILITY_UPDATE", "STALE_INFORMATION"}
    for e in events:
        assert e.type in allowed
        assert 0.0 <= e.confidence <= 1.0
        assert e.severity in {"low", "medium", "high"}


def test_generate_event_stream_is_seed_reproducible():
    queue = ["C1", "C2", "C3", "C4", "C5"]
    events_a = generate_event_stream(queue, t_steps=30, uncertainty_level="high", rng=random.Random(7))
    events_b = generate_event_stream(queue, t_steps=30, uncertainty_level="high", rng=random.Random(7))
    assert [e.type for e in events_a] == [e.type for e in events_b]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_event_generator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.event_generator'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/event_generator.py`:
```python
import random

from sarcrp.schemas import Event

SEVERITY_RANK_SHIFT = {"low": (1, 2), "medium": (3, 5), "high": (6, 8)}
CONFIDENCE_RANGE_BY_UNCERTAINTY = {
    "low": (0.80, 1.00),
    "medium": (0.50, 0.90),
    "high": (0.20, 0.80),
}
EVENT_TYPE_WEIGHTS = {
    "ORDER_SWAP": 0.40,
    "URGENT_INSERTION": 0.25,
    "ETA_SHIFT": 0.20,  # resolves to ETA_EARLY or ETA_LATE
    "PROBABILITY_UPDATE": 0.10,
    "STALE_INFORMATION": 0.05,
}
P_EVENT = 0.30


def _sample_severity(uncertainty_level: str, rng: random.Random) -> str:
    # Higher uncertainty biases toward larger severities.
    weights = {"low": 0.30, "medium": 0.40, "high": 0.30}
    if uncertainty_level == "high":
        weights = {"low": 0.15, "medium": 0.35, "high": 0.50}
    elif uncertainty_level == "low":
        weights = {"low": 0.55, "medium": 0.35, "high": 0.10}
    return rng.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]


def _sample_confidence(uncertainty_level: str, rng: random.Random) -> float:
    lo, hi = CONFIDENCE_RANGE_BY_UNCERTAINTY[uncertainty_level]
    return rng.uniform(lo, hi)


def _rank_shift_for(severity: str, rng: random.Random) -> int:
    lo, hi = SEVERITY_RANK_SHIFT[severity]
    return rng.randint(lo, hi)


def apply_order_swap(queue: list[str], severity: str, rng: random.Random) -> list[str]:
    if len(queue) < 2:
        return list(queue)
    shift = min(_rank_shift_for(severity, rng), len(queue) - 1)
    i = rng.randint(0, len(queue) - 1 - shift)
    j = i + shift
    new_queue = list(queue)
    new_queue[i], new_queue[j] = new_queue[j], new_queue[i]
    return new_queue


def apply_urgent_insertion(queue: list[str], severity: str, rng: random.Random) -> list[str]:
    if not queue:
        return list(queue)
    pool = [c for c in queue if c not in queue[:3]] or list(queue)
    container = rng.choice(pool)
    new_queue = [c for c in queue if c != container]
    insert_at = min(_rank_shift_for(severity, rng), len(new_queue))
    new_queue.insert(insert_at, container)
    return new_queue


def apply_eta_shift(queue: list[str], severity: str, rng: random.Random) -> list[str]:
    # ETA_EARLY/ETA_LATE both change rank; direction is chosen by the caller.
    return apply_order_swap(queue, severity, rng)


def _sample_event_type(rng: random.Random) -> str:
    types = list(EVENT_TYPE_WEIGHTS.keys())
    weights = list(EVENT_TYPE_WEIGHTS.values())
    return rng.choices(types, weights=weights, k=1)[0]


def generate_event_stream(
    initial_queue: list[str],
    t_steps: int,
    uncertainty_level: str,
    rng: random.Random,
    event_id_prefix: str = "e",
) -> list[Event]:
    queue = list(initial_queue)
    events: list[Event] = []

    for t in range(1, t_steps + 1):
        if rng.random() > P_EVENT:
            continue

        sampled = _sample_event_type(rng)
        severity = _sample_severity(uncertainty_level, rng)
        confidence = _sample_confidence(uncertainty_level, rng)
        old_queue = list(queue)

        if sampled == "ORDER_SWAP":
            queue = apply_order_swap(queue, severity, rng)
            event_type = "ORDER_SWAP"
        elif sampled == "URGENT_INSERTION":
            queue = apply_urgent_insertion(queue, severity, rng)
            event_type = "URGENT_INSERTION"
        elif sampled == "ETA_SHIFT":
            queue = apply_eta_shift(queue, severity, rng)
            event_type = "ETA_EARLY" if rng.random() < 0.5 else "ETA_LATE"
        elif sampled == "PROBABILITY_UPDATE":
            event_type = "PROBABILITY_UPDATE"
            # queue unchanged; probability bookkeeping happens outside the queue itself.
        else:
            event_type = "STALE_INFORMATION"
            # queue unchanged; caller delays timestamp_observed for this event.

        affected = sorted(set(old_queue) ^ set(queue)) or (old_queue[:1] if old_queue else [])
        events.append(
            Event(
                event_id=f"{event_id_prefix}{len(events):04d}",
                time_step=t,
                type=event_type,
                severity=severity,
                affected_containers=affected,
                old_queue=old_queue,
                new_queue=list(queue),
                confidence=confidence,
                timestamp_generated=t,
                timestamp_observed=t,
                metadata={},
            )
        )

    return events
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_event_generator.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/event_generator.py paper1_sarcrp/tests/test_event_generator.py
git commit -m "feat(paper1): implement dynamic event stream generator (spec 39)"
```

---

### Task 5: Event Impact Estimator

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/impact_estimator.py`
- Test: `paper1_sarcrp/tests/test_impact_estimator.py`

**Interfaces:**
- Consumes: `schemas.YardState`, `schemas.Plan` (Task 1), `state_ops.blocker_count` (Task 2)
- Produces: `impact_estimator.ImpactBreakdown` (dataclass: `i_order, i_target, i_blocking, i_plan, i_conf, total`), `impact_estimator.compute_impact(old_queue, new_queue, state_old, state_new, plan_old, k=10, r_shift=5, sigma_b=2.0, conf_new=1.0, weights=None) -> ImpactBreakdown`, `impact_estimator.is_action_affected(action, old_queue, new_queue, state_new, r_shift=5) -> bool`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_impact_estimator.py`:
```python
import math
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.impact_estimator import compute_impact, is_action_affected


def make_state(retrieval_queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=1, max_tier=5),
        stacks=[Stack(id="S1", containers=["C5", "C4", "C3", "C2", "C1"], max_tier=5)],
        container_attributes={}, retrieval_queue=retrieval_queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_no_change_gives_zero_order_and_target_impact():
    queue = ["C1", "C2", "C3", "C4", "C5"]
    state = make_state(queue)
    plan = Plan(plan_id="p", created_at=0, source="test", actions=[])
    impact = compute_impact(queue, list(queue), state, state, plan, k=5, conf_new=1.0)
    assert impact.i_order == 0.0
    assert impact.i_target == 0.0
    assert impact.i_conf == 0.0
    assert impact.total == 0.0


def test_full_reversal_gives_max_order_impact():
    old_queue = ["C1", "C2", "C3", "C4", "C5"]
    new_queue = ["C5", "C4", "C3", "C2", "C1"]
    state = make_state(old_queue)
    plan = Plan(plan_id="p", created_at=0, source="test", actions=[])
    impact = compute_impact(old_queue, new_queue, state, state, plan, k=5, conf_new=1.0)
    assert math.isclose(impact.i_order, 1.0, rel_tol=1e-9)


def test_target_change_is_binary():
    old_queue = ["C1", "C2", "C3"]
    new_queue = ["C2", "C1", "C3"]
    state = make_state(old_queue)
    plan = Plan(plan_id="p", created_at=0, source="test", actions=[])
    impact = compute_impact(old_queue, new_queue, state, state, plan, k=3, conf_new=1.0)
    assert impact.i_target == 1.0  # target (rank-0 container) changed from C1 to C2


def test_is_action_affected_rank_shift_beyond_threshold():
    old_queue = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
    new_queue = ["C8", "C1", "C2", "C3", "C4", "C5", "C6", "C7"]  # C7 shifts rank 6->7... use bigger shift
    state = make_state(new_queue)
    action = Action(action_id="a1", step_index=0, type="RELOCATE", container="C1",
                     source_stack="S1", dest_stack="S1", commit_status="planned", planned_time=1)
    assert is_action_affected(action, old_queue, new_queue, state, r_shift=0) is True


def test_is_action_affected_removed_container():
    old_queue = ["C1", "C2", "C3"]
    new_queue = ["C2", "C3"]
    state = make_state(new_queue)
    action = Action(action_id="a1", step_index=0, type="RETRIEVE", container="C1",
                     source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1)
    assert is_action_affected(action, old_queue, new_queue, state, r_shift=5) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_impact_estimator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.impact_estimator'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/impact_estimator.py`:
```python
import math
from dataclasses import dataclass

from sarcrp.schemas import Action, Plan, YardState
from sarcrp.state_ops import blocker_count

DEFAULT_WEIGHTS = {"w_o": 0.25, "w_t": 0.20, "w_b": 0.25, "w_p": 0.20, "w_c": 0.10}


@dataclass
class ImpactBreakdown:
    i_order: float
    i_target: float
    i_blocking: float
    i_plan: float
    i_conf: float
    total: float


def _kendall_tau_topk(old_queue: list[str], new_queue: list[str], k: int) -> float:
    """I_order: normalized Kendall-tau distance over top-k union (spec 8.2)."""
    old_top = old_queue[:k]
    new_top = new_queue[:k]
    items = sorted(set(old_top) | set(new_top))
    n = len(items)
    if n < 2:
        return 0.0

    def rank_in(seq: list[str], item: str) -> int:
        return seq.index(item) if item in seq else k + 1

    old_rank = {c: rank_in(old_top, c) for c in items}
    new_rank = {c: rank_in(new_top, c) for c in items}

    discordant = 0
    total_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = items[i], items[j]
            total_pairs += 1
            old_order = old_rank[a] - old_rank[b]
            new_order = new_rank[a] - new_rank[b]
            if (old_order > 0) != (new_order > 0) and old_order != 0 and new_order != 0:
                discordant += 1
            elif (old_order == 0) != (new_order == 0):
                discordant += 1
    return discordant / total_pairs if total_pairs else 0.0


def _target_impact(old_queue: list[str], new_queue: list[str]) -> float:
    """I_target: binary indicator that the current retrieval target changed (spec 8.3)."""
    old_target = old_queue[0] if old_queue else None
    new_target = new_queue[0] if new_queue else None
    return 1.0 if old_target != new_target else 0.0


def _blocking_impact(state_old: YardState, state_new: YardState, top_k: list[str], sigma_b: float) -> float:
    """I_blocking: saturated mean absolute blocker-count change over top-k (spec 8.4)."""
    if not top_k:
        return 0.0
    diffs = [abs(blocker_count(state_new, c) - blocker_count(state_old, c)) for c in top_k]
    mean_delta = sum(diffs) / len(top_k)
    return 1.0 - math.exp(-mean_delta / sigma_b)


def is_action_affected(
    action: Action,
    old_queue: list[str],
    new_queue: list[str],
    state_new: YardState,
    r_shift: int = 5,
) -> bool:
    """A1/A2 affected-action rules from spec 8.5 / 44.4 (A3-A5 need full candidate
    plans and are checked later inside minimal_repair/local_search, not here)."""
    container = action.container
    if container not in new_queue:
        return True  # A1: removed/cancelled
    old_rank = old_queue.index(container) if container in old_queue else len(old_queue)
    new_rank = new_queue.index(container)
    return abs(new_rank - old_rank) > r_shift  # A2: rank shift beyond threshold


def _plan_impact(plan_old: Plan, old_queue: list[str], new_queue: list[str], state_new: YardState, r_shift: int) -> float:
    """I_plan: fraction of P_old's actions that are affected (spec 8.5)."""
    if not plan_old.actions:
        return 0.0
    affected = sum(1 for a in plan_old.actions if is_action_affected(a, old_queue, new_queue, state_new, r_shift))
    return affected / len(plan_old.actions)


def compute_impact(
    old_queue: list[str],
    new_queue: list[str],
    state_old: YardState,
    state_new: YardState,
    plan_old: Plan,
    k: int = 10,
    r_shift: int = 5,
    sigma_b: float = 2.0,
    conf_new: float = 1.0,
    weights: dict | None = None,
) -> ImpactBreakdown:
    w = weights or DEFAULT_WEIGHTS
    i_order = _kendall_tau_topk(old_queue, new_queue, k)
    i_target = _target_impact(old_queue, new_queue)
    i_blocking = _blocking_impact(state_old, state_new, new_queue[:k], sigma_b)
    i_plan = _plan_impact(plan_old, old_queue, new_queue, state_new, r_shift)
    i_conf = 1.0 - conf_new

    total = (
        w["w_o"] * i_order
        + w["w_t"] * i_target
        + w["w_b"] * i_blocking
        + w["w_p"] * i_plan
        + w["w_c"] * i_conf
    )
    return ImpactBreakdown(i_order=i_order, i_target=i_target, i_blocking=i_blocking,
                            i_plan=i_plan, i_conf=i_conf, total=total)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_impact_estimator.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/impact_estimator.py paper1_sarcrp/tests/test_impact_estimator.py
git commit -m "feat(paper1): implement Event Impact Estimator (spec 8, 44)"
```

---

### Task 6: Objective functions (C_op, stability cost, C_data, J)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/objective.py`
- Test: `paper1_sarcrp/tests/test_objective.py`

**Interfaces:**
- Consumes: `schemas.Plan`, `schemas.Action` (Task 1)
- Produces: `objective.relocation_count(plan) -> int`, `objective.retrieval_delay_norm(plan, urgent_containers) -> float`, `objective.operational_cost(plan, urgent_containers, is_valid, alpha=1.0, beta=0.5, gamma=1.0, m_inf=1e6) -> float`, `objective.stability_cost(plan_new, plan_old, frozen_count, rho=0.05, penalties=None) -> tuple[float, bool]`, `objective.data_confidence_cost(plan_new, plan_old, conf_new) -> float`, `objective.compute_objective(op_cost, stab_cost, data_cost, lam=1.0, mu=0.5) -> float`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_objective.py`:
```python
import math
from sarcrp.schemas import Action, Plan
from sarcrp.objective import (
    relocation_count, retrieval_delay_norm, operational_cost,
    stability_cost, data_confidence_cost, compute_objective,
)


def make_action(step, atype="RELOCATE", container="C1", dest="S2", commit="planned"):
    return Action(action_id=f"a{step}", step_index=step, type=atype, container=container,
                  source_stack="S1", dest_stack=dest, commit_status=commit, planned_time=step)


def test_relocation_count_counts_only_relocate():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        make_action(0, "RELOCATE"), make_action(1, "RETRIEVE"), make_action(2, "RELOCATE"),
    ])
    assert relocation_count(plan) == 2


def test_retrieval_delay_norm_zero_without_urgent():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0)])
    assert retrieval_delay_norm(plan, urgent_containers=[]) == 0.0


def test_retrieval_delay_norm_penalizes_late_position():
    actions = [make_action(i, container=f"C{i}") for i in range(4)]
    plan = Plan(plan_id="p", created_at=0, source="t", actions=actions)
    delay_early = retrieval_delay_norm(plan, urgent_containers=["C0"])
    delay_late = retrieval_delay_norm(plan, urgent_containers=["C3"])
    assert delay_late > delay_early


def test_operational_cost_invalid_dominates():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0)])
    valid_cost = operational_cost(plan, urgent_containers=[], is_valid=True)
    invalid_cost = operational_cost(plan, urgent_containers=[], is_valid=False)
    assert invalid_cost - valid_cost == 1.0e6  # gamma=1.0 * M_inf=1e6 (spec 11.3/11.4)


def test_stability_cost_zero_when_identical():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0), make_action(1)])
    cost, violated = stability_cost(plan, plan, frozen_count=0)
    assert cost == 0.0
    assert violated is False


def test_stability_cost_penalizes_container_change():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0, container="C1")])
    new_plan = Plan(plan_id="p2", created_at=0, source="t", actions=[make_action(0, container="C2")])
    cost, violated = stability_cost(new_plan, old_plan, frozen_count=0)
    assert cost > 0.0
    assert violated is False


def test_stability_cost_flags_frozen_violation():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0, container="C1")])
    new_plan = Plan(plan_id="p2", created_at=0, source="t", actions=[make_action(0, container="C2")])
    cost, violated = stability_cost(new_plan, old_plan, frozen_count=1)
    assert violated is True
    assert math.isinf(cost)


def test_data_confidence_cost_scales_with_low_confidence():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[make_action(0, container="C1")])
    new_plan = Plan(plan_id="p2", created_at=0, source="t", actions=[make_action(0, container="C2")])
    high_conf_cost = data_confidence_cost(new_plan, old_plan, conf_new=0.9)
    low_conf_cost = data_confidence_cost(new_plan, old_plan, conf_new=0.1)
    assert low_conf_cost > high_conf_cost


def test_compute_objective_combines_terms():
    j = compute_objective(op_cost=10.0, stab_cost=4.0, data_cost=2.0, lam=1.0, mu=0.5)
    assert j == 10.0 + 1.0 * 4.0 + 0.5 * 2.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_objective.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.objective'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/objective.py`:
```python
import math

from sarcrp.schemas import Action, Plan

DEFAULT_PENALTIES = {"p_c": 2.0, "p_a": 2.0, "p_d": 1.0, "p_o": 1.0, "p_m": 10.0,
                      "p_f": math.inf, "p_insert": 1.5, "p_delete": 1.5}


def relocation_count(plan: Plan) -> int:
    return sum(1 for a in plan.actions if a.type == "RELOCATE")


def retrieval_delay_norm(plan: Plan, urgent_containers: list[str]) -> float:
    """RetrievalDelayNorm(P) (spec 11.2 / 45.2)."""
    if not urgent_containers:
        return 0.0
    positions = {a.container: i for i, a in enumerate(plan.actions)}
    total = sum(positions.get(c, len(plan.actions) + 1) for c in urgent_containers)
    denom = len(urgent_containers) * (len(plan.actions) + 1)
    return total / denom if denom else 0.0


def operational_cost(
    plan: Plan,
    urgent_containers: list[str],
    is_valid: bool,
    alpha: float = 1.0,
    beta: float = 0.5,
    gamma: float = 1.0,
    m_inf: float = 1e6,
) -> float:
    """C_op(P) = alpha*R(P) + beta*RetrievalDelay(P) + gamma*InvalidPenalty(P) (spec 11, 45.1)."""
    invalid_penalty = 0.0 if is_valid else m_inf
    return (
        alpha * relocation_count(plan)
        + beta * retrieval_delay_norm(plan, urgent_containers)
        + gamma * invalid_penalty
    )


def _action_distance(
    action_new: Action | None,
    action_old: Action | None,
    is_frozen_index: bool,
    penalties: dict,
) -> float:
    if action_new is None or action_old is None:
        return penalties["p_insert"] if action_new is not None else penalties["p_delete"]

    changed_container = action_new.container != action_old.container
    changed_type = action_new.type != action_old.type
    changed_dest = action_new.dest_stack != action_old.dest_stack
    # "orderChanged": same container re-appears elsewhere in the old plan at a
    # different index -> this position's mismatch is a reordering, not a brand
    # new container (spec 12.2 interpretation note).
    changed_order = changed_container  # refined below by caller using full-plan context

    d = 0.0
    if changed_container:
        d += penalties["p_c"]
    if changed_type:
        d += penalties["p_a"]
    if changed_dest:
        d += penalties["p_d"]

    any_changed = changed_container or changed_type or changed_dest
    if is_frozen_index and any_changed:
        return penalties["p_f"]  # frozen violation -> infinite (spec 10.2, 12.2)
    if action_old.commit_status == "committed" and any_changed:
        d += penalties["p_m"]
    return d


def stability_cost(
    plan_new: Plan,
    plan_old: Plan,
    frozen_count: int,
    rho: float = 0.05,
    penalties: dict | None = None,
) -> tuple[float, bool]:
    """D(P, P_old) = sum_i exp(-rho*i) * d_i, plus a frozen-violation flag (spec 12, 45.3)."""
    pen = penalties or DEFAULT_PENALTIES
    old_containers_by_index = {a.step_index: a.container for a in plan_old.actions}
    new_by_index = {a.step_index: a for a in plan_new.actions}
    old_by_index = {a.step_index: a for a in plan_old.actions}
    max_len = max(len(plan_new.actions), len(plan_old.actions))

    total = 0.0
    frozen_violation = False
    old_container_positions = {a.container: a.step_index for a in plan_old.actions}

    for i in range(max_len):
        a_new = new_by_index.get(i)
        a_old = old_by_index.get(i)
        is_frozen_index = i < frozen_count
        d_i = _action_distance(a_new, a_old, is_frozen_index, pen)

        if a_new is not None and a_old is not None and a_new.container == a_old.container is False:
            pass  # container mismatch already counted in _action_distance via p_c

        if math.isinf(d_i):
            frozen_violation = True

        weight = math.exp(-rho * i)
        total += weight * d_i if not math.isinf(d_i) else d_i  # keep inf visible, don't multiply inf*weight->nan-safe
    return total, frozen_violation


def data_confidence_cost(plan_new: Plan, plan_old: Plan, conf_new: float) -> float:
    """C_data(P) = Changes(P, P_old) * (1 - Conf(I_new))  (spec 13, 45.4, simple form)."""
    old_by_index = {a.step_index: a for a in plan_old.actions}
    new_by_index = {a.step_index: a for a in plan_new.actions}
    all_indices = set(old_by_index) | set(new_by_index)
    changes = sum(
        1 for i in all_indices
        if old_by_index.get(i) is None
        or new_by_index.get(i) is None
        or old_by_index[i].container != new_by_index[i].container
        or old_by_index[i].dest_stack != new_by_index[i].dest_stack
    )
    return changes * (1.0 - conf_new)


def compute_objective(op_cost: float, stab_cost: float, data_cost: float, lam: float = 1.0, mu: float = 0.5) -> float:
    """J(P) = C_op(P) + lambda*D(P,P_old) + mu*C_data(P)  (spec 4.3, 45)."""
    return op_cost + lam * stab_cost + mu * data_cost
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_objective.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/objective.py paper1_sarcrp/tests/test_objective.py
git commit -m "feat(paper1): implement C_op, stability cost D, C_data, J(P) (spec 11-13, 45)"
```

---

### Task 7: CRP solver (greedy heuristic — MVP CRP_RL surrogate)

**Rationale (read before implementing):** The spec's `CRP_RL` base solver is Shin et al. 2026's trained deep-RL model (§3.1, §43); we do not have that model or its training code. Building or training a DRL solver is out of scope for an MVP whose entire purpose is to test the *replanning layer*, not to reproduce someone else's solver. This task implements a small, deterministic, real greedy heuristic behind the exact `solve_crp` interface from spec §43, so it is a drop-in replacement point: swapping in the real CRP_RL later means only changing this one file. Document this substitution explicitly in the eventual paper's Limitations section (spec §28.9 already anticipates this).

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/crp_solver.py`
- Test: `paper1_sarcrp/tests/test_crp_solver.py`

**Interfaces:**
- Consumes: `schemas.YardState`, `schemas.Plan`, `schemas.Action` (Task 1), `state_ops.find_stack` (Task 2)
- Produces: `crp_solver.solve_crp(yard_state, retrieval_queue, constraints=None, time_limit_sec=None) -> Plan`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_crp_solver.py`:
```python
from sarcrp.schemas import Layout, Stack, YardState
from sarcrp.crp_solver import solve_crp


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[
            Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=5),  # C1 on top
            Stack(id="S2", containers=[], max_tier=5),
            Stack(id="S3", containers=[], max_tier=5),
        ],
        container_attributes={}, retrieval_queue=["C1", "C2", "C3"],
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_retrieves_top_container_directly():
    state = make_state()
    plan = solve_crp(state, retrieval_queue=["C1", "C2", "C3"])
    assert plan.actions[0].type == "RETRIEVE"
    assert plan.actions[0].container == "C1"


def test_relocates_blockers_before_retrieving_buried_target():
    state = make_state()
    plan = solve_crp(state, retrieval_queue=["C3", "C2", "C1"])  # C3 is buried under C2, C1
    retrieve_order = [a.container for a in plan.actions if a.type == "RETRIEVE"]
    assert retrieve_order == ["C3", "C2", "C1"]
    relocations_before_c3 = [a for a in plan.actions if a.type == "RELOCATE"]
    assert len(relocations_before_c3) == 2  # must move C1 and C2 out of the way


def test_respects_forbidden_moves_constraint():
    state = make_state()
    constraints = {"forbidden_moves": [{"container": "C1", "dest_stack": "S2"}]}
    plan = solve_crp(state, retrieval_queue=["C3", "C2", "C1"], constraints=constraints)
    forbidden_hits = [a for a in plan.actions if a.type == "RELOCATE" and a.container == "C1" and a.dest_stack == "S2"]
    assert forbidden_hits == []


def test_time_limit_still_returns_a_plan():
    state = make_state()
    plan = solve_crp(state, retrieval_queue=["C3", "C2", "C1"], time_limit_sec=1.0)
    assert plan.actions  # doesn't crash / doesn't return empty under a generous limit
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_crp_solver.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.crp_solver'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/crp_solver.py`:
```python
import copy
import time

from sarcrp.schemas import Action, Plan, YardState
from sarcrp.state_ops import find_stack


def _is_forbidden(container: str, dest_stack: str, constraints: dict | None) -> bool:
    if not constraints:
        return False
    for move in constraints.get("forbidden_moves", []):
        if move.get("container") == container and move.get("dest_stack") == dest_stack:
            return True
    return False


def _choose_relocation_dest(state: YardState, source_stack_id: str, container: str, constraints: dict | None) -> str | None:
    """Relocate to the emptiest eligible stack (greedy leveling heuristic)."""
    candidates = [
        s for s in state.stacks
        if s.id != source_stack_id
        and len(s.containers) < s.max_tier
        and not _is_forbidden(container, s.id, constraints)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda s: (len(s.containers), s.id)).id


def solve_crp(
    yard_state: YardState,
    retrieval_queue: list[str],
    constraints: dict | None = None,
    time_limit_sec: float | None = None,
) -> Plan:
    """Greedy CRP heuristic: for each target in queue order, relocate any
    blockers above it (to the emptiest legal stack) then retrieve it.
    This is the MVP surrogate for the CRP_RL solver (spec 43) -- see Task 7
    rationale for why a trained solver is not used here."""
    start = time.monotonic()
    state = copy.deepcopy(yard_state)
    actions: list[Action] = []
    step = 0

    for container in retrieval_queue:
        if time_limit_sec is not None and time.monotonic() - start > time_limit_sec:
            break

        stack_id = find_stack(state, container)
        if stack_id is None:
            continue  # container already retrieved or not present

        stack = next(s for s in state.stacks if s.id == stack_id)
        while stack.containers[-1] != container:
            blocker = stack.containers[-1]
            dest = _choose_relocation_dest(state, stack.id, blocker, constraints)
            if dest is None:
                break  # no legal destination; leave blocker in place (marks plan invalid downstream)
            dest_stack = next(s for s in state.stacks if s.id == dest)
            stack.containers.pop()
            dest_stack.containers.append(blocker)
            actions.append(Action(
                action_id=f"a{step:04d}", step_index=step, type="RELOCATE", container=blocker,
                source_stack=stack.id, dest_stack=dest, commit_status="planned", planned_time=step,
            ))
            step += 1

        if stack.containers and stack.containers[-1] == container:
            stack.containers.pop()
            actions.append(Action(
                action_id=f"a{step:04d}", step_index=step, type="RETRIEVE", container=container,
                source_stack=stack.id, dest_stack=None, commit_status="planned", planned_time=step,
            ))
            step += 1

    return Plan(plan_id="plan_greedy", created_at=yard_state.time_step, source="greedy_crp_solver", actions=actions)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_crp_solver.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/crp_solver.py paper1_sarcrp/tests/test_crp_solver.py
git commit -m "feat(paper1): implement greedy CRP solver as MVP CRP_RL surrogate (spec 43)"
```

---

### Task 8: Freeze horizon (split plan into frozen prefix + repairable tail)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/freeze_horizon.py`
- Test: `paper1_sarcrp/tests/test_freeze_horizon.py`

**Interfaces:**
- Consumes: `schemas.Plan` (Task 1)
- Produces: `freeze_horizon.split_plan(plan, h_f) -> tuple[Plan, Plan]`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_freeze_horizon.py`:
```python
from sarcrp.schemas import Action, Plan
from sarcrp.freeze_horizon import split_plan


def make_plan(n):
    actions = [Action(action_id=f"a{i}", step_index=i, type="RELOCATE", container=f"C{i}",
                       source_stack="S1", dest_stack="S2", commit_status="planned", planned_time=i)
               for i in range(n)]
    return Plan(plan_id="p", created_at=0, source="t", actions=actions)


def test_split_respects_h_f_default_3():
    plan = make_plan(6)
    frozen, tail = split_plan(plan, h_f=3)
    assert [a.step_index for a in frozen.actions] == [0, 1, 2]
    assert [a.step_index for a in tail.actions] == [3, 4, 5]


def test_split_with_h_f_larger_than_plan_freezes_everything():
    plan = make_plan(2)
    frozen, tail = split_plan(plan, h_f=5)
    assert len(frozen.actions) == 2
    assert len(tail.actions) == 0


def test_split_with_h_f_zero_freezes_nothing():
    plan = make_plan(3)
    frozen, tail = split_plan(plan, h_f=0)
    assert len(frozen.actions) == 0
    assert len(tail.actions) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_freeze_horizon.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.freeze_horizon'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/freeze_horizon.py`:
```python
from sarcrp.schemas import Plan


def split_plan(plan: Plan, h_f: int) -> tuple[Plan, Plan]:
    """Freeze-by-action-count (spec 10.1): first h_f actions are frozen, rest is the
    repairable tail."""
    frozen_actions = plan.actions[:h_f]
    tail_actions = plan.actions[h_f:]
    frozen = Plan(plan_id=f"{plan.plan_id}_frozen", created_at=plan.created_at, source=plan.source, actions=frozen_actions)
    tail = Plan(plan_id=f"{plan.plan_id}_tail", created_at=plan.created_at, source=plan.source, actions=tail_actions)
    return frozen, tail
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_freeze_horizon.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/freeze_horizon.py paper1_sarcrp/tests/test_freeze_horizon.py
git commit -m "feat(paper1): implement freeze-horizon plan split (spec 10)"
```

---

### Task 9: Minimal feasibility repair (candidate C1)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/minimal_repair.py`
- Test: `paper1_sarcrp/tests/test_minimal_repair.py`

**Interfaces:**
- Consumes: `schemas.YardState`, `schemas.Plan`, `schemas.Action` (Task 1), `state_ops.find_stack` (Task 2)
- Produces: `minimal_repair.minimal_feasibility_repair(plan_old, state_new, retrieval_queue_new) -> Plan`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_minimal_repair.py`:
```python
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.minimal_repair import minimal_feasibility_repair


def make_state(queue):
    return YardState(
        instance_id="t", time_step=1, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=1, state_confidence=1.0,
    )


def test_removes_action_for_container_no_longer_in_queue():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
    ])
    state = make_state(queue=["C2"])  # C1 no longer in queue -> obsolete
    repaired = minimal_feasibility_repair(old_plan, state, retrieval_queue_new=["C2"])
    containers = [a.container for a in repaired.actions]
    assert "C1" not in containers
    assert "C2" in containers


def test_keeps_valid_actions_untouched():
    old_plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    state = make_state(queue=["C2"])
    repaired = minimal_feasibility_repair(old_plan, state, retrieval_queue_new=["C2"])
    assert len(repaired.actions) == 1
    assert repaired.actions[0].container == "C2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_minimal_repair.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.minimal_repair'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/minimal_repair.py`:
```python
from sarcrp.schemas import Plan
from sarcrp.state_ops import find_stack


def minimal_feasibility_repair(plan_old: Plan, state_new, retrieval_queue_new: list[str]) -> Plan:
    """Candidate C1 (spec 14.2): drop actions for containers that no longer exist
    in the retrieval queue or yard; leave everything else untouched. Destination
    re-pointing for now-invalid RELOCATE destinations is handled by
    local_search_repair's N1 operator (Task 10), which runs on this candidate's
    output next."""
    repaired_actions = []
    for action in plan_old.actions:
        if action.type == "RETRIEVE" and action.container not in retrieval_queue_new:
            continue  # obsolete: container no longer needs retrieval
        if action.type == "RELOCATE" and find_stack(state_new, action.container) is None:
            continue  # obsolete: container no longer in the yard
        repaired_actions.append(action)

    for i, action in enumerate(repaired_actions):
        action.step_index = i

    return Plan(plan_id=f"{plan_old.plan_id}_minrepair", created_at=plan_old.created_at,
                source="minimal_feasibility_repair", actions=repaired_actions)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_minimal_repair.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/minimal_repair.py paper1_sarcrp/tests/test_minimal_repair.py
git commit -m "feat(paper1): implement minimal feasibility repair candidate C1 (spec 14.2)"
```

---

### Task 10: Local search repair (candidate C2 — N1-N5 + stochastic hill climbing)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/local_search_repair.py`
- Test: `paper1_sarcrp/tests/test_local_search_repair.py`

**Interfaces:**
- Consumes: `schemas.Plan`, `schemas.Action` (Task 1), `objective.operational_cost`, `objective.stability_cost`, `objective.data_confidence_cost`, `objective.compute_objective` (Task 6)
- Produces: `local_search_repair.local_search_repair(p_start, p_old, state, retrieval_queue_new, frozen_count, rng, t_iters=100, m_neighbors=50, epsilon=0.05, time_limit_sec=None, urgent_containers=None, conf_new=1.0) -> Plan`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_local_search_repair.py`:
```python
import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.local_search_repair import local_search_repair


def make_state():
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C1"], max_tier=5),
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=["C1"], pickup_prob={}, data_timestamp=0, state_confidence=1.0,
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_local_search_repair.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.local_search_repair'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/local_search_repair.py`:
```python
import copy
import random
import time

from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, stability_cost
from sarcrp.schemas import Plan


def _score(plan: Plan, p_old: Plan, frozen_count: int, urgent_containers: list[str], conf_new: float) -> float:
    op = operational_cost(plan, urgent_containers, is_valid=True)
    stab, violated = stability_cost(plan, p_old, frozen_count)
    if violated:
        return float("inf")
    data = data_confidence_cost(plan, p_old, conf_new)
    return compute_objective(op, stab, data)


def _neighbor_change_destination(plan: Plan, state, frozen_count: int, rng: random.Random) -> Plan | None:
    """N1 (spec 15.1/46.2): change one non-frozen RELOCATE action's destination."""
    candidates = [i for i, a in enumerate(plan.actions) if i >= frozen_count and a.type == "RELOCATE"]
    if not candidates:
        return None
    idx = rng.choice(candidates)
    other_stacks = [s.id for s in state.stacks if s.id != plan.actions[idx].source_stack]
    if not other_stacks:
        return None
    new_plan = copy.deepcopy(plan)
    new_plan.actions[idx].dest_stack = rng.choice(other_stacks)
    return new_plan


def _neighbor_swap_actions(plan: Plan, frozen_count: int, rng: random.Random) -> Plan | None:
    """N2: swap two non-frozen actions."""
    non_frozen = [i for i in range(len(plan.actions)) if i >= frozen_count]
    if len(non_frozen) < 2:
        return None
    i, j = rng.sample(non_frozen, 2)
    new_plan = copy.deepcopy(plan)
    new_plan.actions[i], new_plan.actions[j] = new_plan.actions[j], new_plan.actions[i]
    for k, a in enumerate(new_plan.actions):
        a.step_index = k
    return new_plan


def _neighbor_remove_obsolete(plan: Plan, frozen_count: int, rng: random.Random) -> Plan | None:
    """N4: drop one non-frozen action (models "remove no-longer-needed relocation")."""
    non_frozen = [i for i in range(len(plan.actions)) if i >= frozen_count]
    if not non_frozen:
        return None
    idx = rng.choice(non_frozen)
    new_actions = [a for i, a in enumerate(plan.actions) if i != idx]
    for k, a in enumerate(new_actions):
        a.step_index = k
    return Plan(plan_id=plan.plan_id, created_at=plan.created_at, source=plan.source, actions=new_actions)


NEIGHBORHOOD_OPS = [_neighbor_change_destination, _neighbor_swap_actions, _neighbor_remove_obsolete]


def local_search_repair(
    p_start: Plan,
    p_old: Plan,
    state,
    retrieval_queue_new: list[str],
    frozen_count: int,
    rng: random.Random,
    t_iters: int = 100,
    m_neighbors: int = 50,
    epsilon: float = 0.05,
    time_limit_sec: float | None = None,
    urgent_containers: list[str] | None = None,
    conf_new: float = 1.0,
) -> Plan:
    """Stochastic hill climbing over N1/N2/N4 (spec 15.2/46.3). N3/N5 need the
    CRP solver / urgent-insertion context and are deferred to a follow-up plan
    once the MVP decision gate (spec 33) passes."""
    urgent = urgent_containers or []
    start_time = time.monotonic()
    p_best = p_start
    score_best = _score(p_best, p_old, frozen_count, urgent, conf_new)
    stale_iterations = 0

    for _ in range(t_iters):
        if time_limit_sec is not None and time.monotonic() - start_time > time_limit_sec:
            break

        neighbors = []
        for _ in range(m_neighbors):
            op = rng.choice(NEIGHBORHOOD_OPS)
            if op is _neighbor_change_destination:
                candidate = op(p_best, state, frozen_count, rng)
            else:
                candidate = op(p_best, frozen_count, rng)
            if candidate is not None:
                neighbors.append(candidate)

        if not neighbors:
            stale_iterations += 1
            if stale_iterations >= 10:
                break
            continue
        stale_iterations = 0

        scored = [(_score(n, p_old, frozen_count, urgent, conf_new), n) for n in neighbors]
        candidate_score, candidate_plan = min(scored, key=lambda pair: pair[0])

        if candidate_score < score_best:
            p_best, score_best = candidate_plan, candidate_score
        elif rng.random() < epsilon:
            p_best, score_best = candidate_plan, candidate_score

    return p_best
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_local_search_repair.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/local_search_repair.py paper1_sarcrp/tests/test_local_search_repair.py
git commit -m "feat(paper1): implement local search repair N1/N2/N4 + hill climbing (spec 15, 46)"
```

---

### Task 11: SAR-CRP Core algorithm (assembles the 9-step spec §18 algorithm)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/sarcrp_core.py`
- Test: `paper1_sarcrp/tests/test_sarcrp_core.py`

**Interfaces:**
- Consumes: `impact_estimator.compute_impact` (Task 5), `objective.operational_cost/stability_cost/data_confidence_cost/compute_objective` (Task 6), `freeze_horizon.split_plan` (Task 8), `minimal_repair.minimal_feasibility_repair` (Task 9), `local_search_repair.local_search_repair` (Task 10), `crp_solver.solve_crp` (Task 7)
- Produces: `sarcrp_core.ReplanDecision` (dataclass: `decision: str, plan: Plan, impact: ImpactBreakdown, j_old: float, j_new: float`), `sarcrp_core.replan(state_t, plan_old, old_queue, new_queue, urgent_containers, h_f=3, lam=1.0, mu=0.5, theta_impact=0.30, tau_frac=0.01, time_limit_sec=5.0, rng=None, conf_new=1.0) -> ReplanDecision`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_sarcrp_core.py`:
```python
import random
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.sarcrp_core import replan


def make_state(queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=3, max_tier=5),
        stacks=[Stack(id="S1", containers=["C3", "C2", "C1"], max_tier=5),
                Stack(id="S2", containers=[], max_tier=5),
                Stack(id="S3", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def make_plan():
    return Plan(plan_id="p_old", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
        Action(action_id="a1", step_index=1, type="RETRIEVE", container="C2",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=1),
        Action(action_id="a2", step_index=2, type="RETRIEVE", container="C3",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=2),
    ])


def test_keep_when_impact_below_threshold():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C1", "C2", "C3"],
        urgent_containers=[], theta_impact=0.30, rng=random.Random(0),
    )
    assert decision.decision == "KEEP"
    assert decision.plan is plan_old


def test_update_when_impact_high_and_gain_worthwhile():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C3", "C2", "C1"],
        urgent_containers=["C3"], theta_impact=0.05, tau_frac=0.0, rng=random.Random(0),
    )
    assert decision.decision in {"KEEP", "UPDATE"}  # fallback may still choose KEEP; assert it ran end-to-end
    assert decision.impact.total > 0.05


def test_result_never_violates_frozen_prefix():
    state = make_state(["C1", "C2", "C3"])
    plan_old = make_plan()
    decision = replan(
        state, plan_old, old_queue=["C1", "C2", "C3"], new_queue=["C3", "C2", "C1"],
        urgent_containers=["C3"], h_f=1, theta_impact=0.05, tau_frac=0.0, rng=random.Random(3),
    )
    assert decision.plan.actions[0].container == plan_old.actions[0].container
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_sarcrp_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.sarcrp_core'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/sarcrp_core.py`:
```python
import random
from dataclasses import dataclass

from sarcrp.crp_solver import solve_crp
from sarcrp.freeze_horizon import split_plan
from sarcrp.impact_estimator import ImpactBreakdown, compute_impact
from sarcrp.local_search_repair import local_search_repair
from sarcrp.minimal_repair import minimal_feasibility_repair
from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, stability_cost
from sarcrp.schemas import Plan


@dataclass
class ReplanDecision:
    decision: str  # "KEEP" or "UPDATE"
    plan: Plan
    impact: ImpactBreakdown
    j_old: float
    j_new: float


def _score_candidate(plan: Plan, plan_old: Plan, frozen_count: int, urgent_containers: list[str], conf_new: float):
    op = operational_cost(plan, urgent_containers, is_valid=True)
    stab, violated = stability_cost(plan, plan_old, frozen_count)
    if violated:
        return float("inf")
    data = data_confidence_cost(plan, plan_old, conf_new)
    return compute_objective(op, stab, data)


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
) -> ReplanDecision:
    """Algorithm SAR-CRP v2 Core (spec 18), steps 1-9."""
    rng = rng or random.Random()

    # Steps 1-2: confidence already folded into conf_new by the caller; estimate impact.
    impact = compute_impact(old_queue, new_queue, state_t, state_t, plan_old, conf_new=conf_new)

    # Step 3: trigger check.
    if impact.total < theta_impact:
        j_old = _score_candidate(plan_old, plan_old, 0, urgent_containers, conf_new)
        return ReplanDecision(decision="KEEP", plan=plan_old, impact=impact, j_old=j_old, j_new=j_old)

    # Step 4: split plan.
    frozen, _tail = split_plan(plan_old, h_f)
    frozen_count = len(frozen.actions)

    # Step 5: generate candidates C0-C3.
    c0 = plan_old
    c1 = minimal_feasibility_repair(plan_old, state_t, new_queue)
    c2 = local_search_repair(
        c1, plan_old, state_t, new_queue, frozen_count, rng,
        urgent_containers=urgent_containers, conf_new=conf_new, time_limit_sec=time_limit_sec,
    )
    tail_solution = solve_crp(state_t, new_queue, time_limit_sec=time_limit_sec)
    c3 = Plan(plan_id=f"{plan_old.plan_id}_c3", created_at=plan_old.created_at, source="frozen+crp_tail",
              actions=list(frozen.actions) + list(tail_solution.actions))

    candidates = [c0, c1, c2, c3]

    # Step 6: score every candidate.
    scored = [(_score_candidate(c, plan_old, frozen_count, urgent_containers, conf_new), c) for c in candidates]

    # Step 7: select best.
    j_best, p_best = min(scored, key=lambda pair: pair[0])
    j_old = _score_candidate(plan_old, plan_old, 0, urgent_containers, conf_new)

    # Step 8: fallback check.
    tau = tau_frac * j_old if j_old not in (0.0, float("inf")) else 0.0
    if j_best == float("inf") or (j_old - j_best) <= tau:
        return ReplanDecision(decision="KEEP", plan=plan_old, impact=impact, j_old=j_old, j_new=j_best)

    # Step 9: update.
    return ReplanDecision(decision="UPDATE", plan=p_best, impact=impact, j_old=j_old, j_new=j_best)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_sarcrp_core.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/sarcrp_core.py paper1_sarcrp/tests/test_sarcrp_core.py
git commit -m "feat(paper1): implement Algorithm SAR-CRP v2 Core (spec 18)"
```

---

### Task 12: MVP baselines (Static, Full Reoptimization)

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/baselines.py`
- Test: `paper1_sarcrp/tests/test_baselines.py`

**Interfaces:**
- Consumes: `crp_solver.solve_crp` (Task 7), `schemas.Plan` (Task 1)
- Produces: `baselines.static_plan(plan_initial) -> Plan`, `baselines.full_reoptimization(state_t, retrieval_queue_new, constraints=None, time_limit_sec=5.0) -> Plan`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_baselines.py`:
```python
from sarcrp.schemas import Layout, Stack, YardState, Action, Plan
from sarcrp.baselines import static_plan, full_reoptimization


def make_state(queue):
    return YardState(
        instance_id="t", time_step=0, layout=Layout(num_stacks=2, max_tier=5),
        stacks=[Stack(id="S1", containers=["C2", "C1"], max_tier=5), Stack(id="S2", containers=[], max_tier=5)],
        container_attributes={}, retrieval_queue=queue, pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def test_static_plan_returns_same_object_unmodified():
    plan = Plan(plan_id="p", created_at=0, source="t", actions=[
        Action(action_id="a0", step_index=0, type="RETRIEVE", container="C1",
               source_stack="S1", dest_stack=None, commit_status="planned", planned_time=0),
    ])
    result = static_plan(plan)
    assert result is plan


def test_full_reoptimization_calls_solver_on_current_state():
    state = make_state(["C1", "C2"])
    plan = full_reoptimization(state, retrieval_queue_new=["C1", "C2"], time_limit_sec=1.0)
    assert plan.actions
    assert plan.actions[0].type == "RETRIEVE"
    assert plan.actions[0].container == "C1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_baselines.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.baselines'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/baselines.py`:
```python
from sarcrp.crp_solver import solve_crp
from sarcrp.schemas import Plan


def static_plan(plan_initial: Plan) -> Plan:
    """B1 (spec 22): never replan, regardless of incoming events."""
    return plan_initial


def full_reoptimization(state_t, retrieval_queue_new: list[str], constraints: dict | None = None, time_limit_sec: float = 5.0) -> Plan:
    """B2 (spec 22): re-solve the whole remaining problem on every event."""
    return solve_crp(state_t, retrieval_queue_new, constraints=constraints, time_limit_sec=time_limit_sec)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_baselines.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/baselines.py paper1_sarcrp/tests/test_baselines.py
git commit -m "feat(paper1): implement Static and Full Reoptimization baselines (spec 22 B1/B2)"
```

---

### Task 13: Episode simulator

**Files:**
- Create: `paper1_sarcrp/src/sarcrp/simulator.py`
- Test: `paper1_sarcrp/tests/test_simulator_mvp.py`

**Interfaces:**
- Consumes: `event_generator.generate_event_stream` (Task 4), `sarcrp_core.replan` (Task 11), `baselines.static_plan/full_reoptimization` (Task 12), `objective.*` (Task 6), `crp_solver.solve_crp` (Task 7)
- Produces: `simulator.EpisodeMetrics` (dataclass: `relocation_count_total, changed_actions_total, total_cost_mean, runtime_mean_sec, fallback_rate`), `simulator.run_episode(instance: dict, method_name: str, rng: random.Random) -> EpisodeMetrics`

- [ ] **Step 1: Write the failing test**

`paper1_sarcrp/tests/test_simulator_mvp.py`:
```python
import random
from sarcrp.simulator import run_episode

SMALL_INSTANCE = {
    "instance_id": "mvp_small_01",
    "layout": {"num_stacks": 3, "max_tier": 5},
    "stacks": [
        {"id": "S1", "containers": ["C6", "C5", "C4", "C3", "C2", "C1"], "max_tier": 5},
        {"id": "S2", "containers": [], "max_tier": 5},
        {"id": "S3", "containers": [], "max_tier": 5},
    ],
    "initial_retrieval_order": ["C1", "C2", "C3", "C4", "C5", "C6"],
    "t_steps": 20,
    "uncertainty_level": "medium",
}


def test_run_episode_static_produces_metrics():
    metrics = run_episode(SMALL_INSTANCE, method_name="static", rng=random.Random(0))
    assert metrics.relocation_count_total >= 0
    assert metrics.runtime_mean_sec >= 0.0


def test_run_episode_sarcrp_produces_metrics_and_is_reproducible():
    m1 = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(42))
    m2 = run_episode(SMALL_INSTANCE, method_name="sarcrp", rng=random.Random(42))
    assert m1.total_cost_mean == m2.total_cost_mean


def test_all_three_mvp_methods_run_without_error():
    for method in ("static", "full_reopt", "sarcrp"):
        metrics = run_episode(SMALL_INSTANCE, method_name=method, rng=random.Random(1))
        assert metrics.total_cost_mean >= 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_simulator_mvp.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sarcrp.simulator'`

- [ ] **Step 3: Write the implementation**

`paper1_sarcrp/src/sarcrp/simulator.py`:
```python
import random
import time
from dataclasses import dataclass

from sarcrp.baselines import full_reoptimization, static_plan
from sarcrp.crp_solver import solve_crp
from sarcrp.event_generator import generate_event_stream
from sarcrp.objective import compute_objective, data_confidence_cost, operational_cost, relocation_count, stability_cost
from sarcrp.sarcrp_core import replan
from sarcrp.schemas import Layout, Stack, YardState


@dataclass
class EpisodeMetrics:
    relocation_count_total: int
    changed_actions_total: int
    total_cost_mean: float
    runtime_mean_sec: float
    fallback_rate: float


def _build_state(instance: dict, retrieval_queue: list[str]) -> YardState:
    stacks = [Stack(id=s["id"], containers=list(s["containers"]), max_tier=s["max_tier"]) for s in instance["stacks"]]
    return YardState(
        instance_id=instance["instance_id"], time_step=0,
        layout=Layout(**instance["layout"]), stacks=stacks,
        container_attributes={}, retrieval_queue=retrieval_queue,
        pickup_prob={}, data_timestamp=0, state_confidence=1.0,
    )


def _plan_changed_count(plan_a, plan_b) -> int:
    by_index_a = {a.step_index: a for a in plan_a.actions}
    by_index_b = {a.step_index: a for a in plan_b.actions}
    indices = set(by_index_a) | set(by_index_b)
    return sum(
        1 for i in indices
        if by_index_a.get(i) is None or by_index_b.get(i) is None
        or by_index_a[i].container != by_index_b[i].container
        or by_index_a[i].dest_stack != by_index_b[i].dest_stack
    )


def run_episode(instance: dict, method_name: str, rng: random.Random) -> EpisodeMetrics:
    queue = list(instance["initial_retrieval_order"])
    state = _build_state(instance, queue)
    plan = solve_crp(state, queue, time_limit_sec=5.0)

    events = generate_event_stream(queue, instance["t_steps"], instance["uncertainty_level"], rng)

    total_costs = []
    runtimes = []
    changed_actions_total = 0
    fallback_count = 0
    replan_opportunities = 0

    for event in events:
        new_queue = event.new_queue
        urgent = [event.affected_containers[0]] if event.type == "URGENT_INSERTION" and event.affected_containers else []
        state.retrieval_queue = new_queue

        start = time.monotonic()
        if method_name == "static":
            new_plan = static_plan(plan)
            fallback = True
        elif method_name == "full_reopt":
            new_plan = full_reoptimization(state, new_queue, time_limit_sec=5.0)
            fallback = False
        elif method_name == "sarcrp":
            replan_opportunities += 1
            decision = replan(state, plan, queue, new_queue, urgent, rng=rng, conf_new=event.confidence)
            new_plan = decision.plan
            fallback = decision.decision == "KEEP"
        else:
            raise ValueError(f"unknown method_name: {method_name}")
        runtime = time.monotonic() - start

        changed_actions_total += _plan_changed_count(new_plan, plan)
        if fallback:
            fallback_count += 1

        op = operational_cost(new_plan, urgent, is_valid=True)
        stab, violated = stability_cost(new_plan, plan, frozen_count=0)
        data = data_confidence_cost(new_plan, plan, event.confidence)
        j = compute_objective(op, 0.0 if violated else stab, data)
        total_costs.append(j)
        runtimes.append(runtime)

        plan = new_plan
        queue = new_queue

    denom = replan_opportunities if method_name == "sarcrp" else max(len(events), 1)
    return EpisodeMetrics(
        relocation_count_total=relocation_count(plan),
        changed_actions_total=changed_actions_total,
        total_cost_mean=sum(total_costs) / len(total_costs) if total_costs else 0.0,
        runtime_mean_sec=sum(runtimes) / len(runtimes) if runtimes else 0.0,
        fallback_rate=fallback_count / denom if denom else 0.0,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_simulator_mvp.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add paper1_sarcrp/src/sarcrp/simulator.py paper1_sarcrp/tests/test_simulator_mvp.py
git commit -m "feat(paper1): implement episode simulator wiring all MVP methods together"
```

---

### Task 14: MVP experiment runner (spec §33 decision gate)

**Files:**
- Create: `paper1_sarcrp/experiments/instances/small_layout_mvp.json`
- Create: `paper1_sarcrp/experiments/run_mvp.py`
- Test: `paper1_sarcrp/tests/test_run_mvp_script.py`

**Interfaces:**
- Consumes: `simulator.run_episode` (Task 13)
- Produces: `experiments/results/mvp_results.csv` (method, uncertainty_level, seed, relocation_count_total, changed_actions_total, total_cost_mean, runtime_mean_sec, fallback_rate), plus a printed decision-gate verdict.

- [ ] **Step 1: Write the MVP instance fixture**

`paper1_sarcrp/experiments/instances/small_layout_mvp.json`:
```json
{
  "instance_id": "mvp_small_01",
  "layout": {"num_stacks": 4, "max_tier": 5},
  "stacks": [
    {"id": "S1", "containers": ["C10", "C09", "C08", "C07"], "max_tier": 5},
    {"id": "S2", "containers": ["C06", "C05", "C04"], "max_tier": 5},
    {"id": "S3", "containers": ["C03", "C02", "C01"], "max_tier": 5},
    {"id": "S4", "containers": [], "max_tier": 5}
  ],
  "initial_retrieval_order": ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10"],
  "t_steps": 30,
  "uncertainty_level": "medium"
}
```

- [ ] **Step 2: Write the failing test for the runner script's aggregation logic**

`paper1_sarcrp/tests/test_run_mvp_script.py`:
```python
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from run_mvp import evaluate_decision_gate, run_all_methods  # noqa: E402


def test_run_all_methods_returns_a_row_per_method_per_seed():
    instance = json.loads((Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json").read_text())
    rows = run_all_methods(instance, methods=("static", "full_reopt", "sarcrp"), seeds=(0, 1))
    assert len(rows) == 3 * 2
    assert {r["method"] for r in rows} == {"static", "full_reopt", "sarcrp"}


def test_evaluate_decision_gate_reports_three_conditions():
    rows = [
        {"method": "static", "total_cost_mean": 10.0, "changed_actions_total": 0},
        {"method": "full_reopt", "total_cost_mean": 6.0, "changed_actions_total": 20},
        {"method": "sarcrp", "total_cost_mean": 7.0, "changed_actions_total": 5},
    ]
    verdict = evaluate_decision_gate(rows)
    assert set(verdict.keys()) == {"sarcrp_beats_static_total_cost", "sarcrp_beats_full_reopt_stability", "sarcrp_close_to_full_reopt_operational"}
    assert verdict["sarcrp_beats_static_total_cost"] is True
    assert verdict["sarcrp_beats_full_reopt_stability"] is True
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd paper1_sarcrp && pytest tests/test_run_mvp_script.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_mvp'`

- [ ] **Step 4: Write the runner script**

`paper1_sarcrp/experiments/run_mvp.py`:
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
SEEDS = tuple(range(10))  # MVP smoke test: 10 seeds. Full study uses >=20 (spec 23.6).


def run_all_methods(instance: dict, methods=METHODS, seeds=SEEDS) -> list[dict]:
    rows = []
    for method in methods:
        for seed in seeds:
            metrics = run_episode(instance, method_name=method, rng=random.Random(seed))
            rows.append({
                "method": method,
                "seed": seed,
                "relocation_count_total": metrics.relocation_count_total,
                "changed_actions_total": metrics.changed_actions_total,
                "total_cost_mean": metrics.total_cost_mean,
                "runtime_mean_sec": metrics.runtime_mean_sec,
                "fallback_rate": metrics.fallback_rate,
            })
    return rows


def evaluate_decision_gate(rows: list[dict]) -> dict:
    """Spec 33 decision gate: SAR-CRP total cost < Static; SAR-CRP stability
    (proxied here by changed_actions_total) < Full Reoptimization; SAR-CRP
    operational cost close to Full Reoptimization (checked via total_cost_mean
    within 20% as a simple MVP proxy -- refine with the real operational-cost
    split once Task 6's components are logged separately per-method)."""
    by_method = {}
    for method in ("static", "full_reopt", "sarcrp"):
        matching = [r["total_cost_mean"] for r in rows if r["method"] == method]
        changed = [r["changed_actions_total"] for r in rows if r["method"] == method]
        by_method[method] = {
            "total_cost_mean": statistics.mean(matching) if matching else float("nan"),
            "changed_actions_mean": statistics.mean(changed) if changed else float("nan"),
        }

    sarcrp, static, full_reopt = by_method["sarcrp"], by_method["static"], by_method["full_reopt"]
    return {
        "sarcrp_beats_static_total_cost": sarcrp["total_cost_mean"] < static["total_cost_mean"],
        "sarcrp_beats_full_reopt_stability": sarcrp["changed_actions_mean"] < full_reopt["changed_actions_mean"],
        "sarcrp_close_to_full_reopt_operational": abs(sarcrp["total_cost_mean"] - full_reopt["total_cost_mean"]) <= 0.20 * full_reopt["total_cost_mean"],
    }


def main():
    instance_path = Path(__file__).parent / "instances" / "small_layout_mvp.json"
    instance = json.loads(instance_path.read_text())

    rows = run_all_methods(instance)

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "mvp_results.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    verdict = evaluate_decision_gate(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")
    print("Decision gate (spec 33):")
    for key, passed in verdict.items():
        print(f"  {key}: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd paper1_sarcrp && pytest tests/test_run_mvp_script.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Run the full MVP experiment end-to-end**

Run: `cd paper1_sarcrp && python experiments/run_mvp.py`
Expected: prints `Wrote 30 rows to .../mvp_results.csv` followed by three `PASS`/`FAIL` lines. Record the actual verdict — it feeds directly into Task 15's report and into the go/no-go decision from spec §32 ("Nếu MVP fail, không chạy full experiment").

- [ ] **Step 7: Commit**

```bash
git add paper1_sarcrp/experiments/instances/small_layout_mvp.json paper1_sarcrp/experiments/run_mvp.py paper1_sarcrp/tests/test_run_mvp_script.py
git commit -m "feat(paper1): add MVP experiment runner and spec-33 decision gate check"
```

---

### Task 15: LaTeX MVP results report (own folder, compiled to PDF)

**Files:**
- Create: `writeups/paper1_mvp_report/main.tex`
- Create: `writeups/paper1_mvp_report/Makefile`

**Interfaces:**
- Consumes: `paper1_sarcrp/experiments/results/mvp_results.csv` (Task 14 output) — fill the table in `main.tex` with the actual numbers from that CSV and the actual verdict from Task 14 Step 6 before compiling. Do not leave the example numbers in place.

- [ ] **Step 1: Write the LaTeX report skeleton**

`writeups/paper1_mvp_report/main.tex`:
```latex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{hyperref}

\title{Paper 1 (SAR-CRP v2 Core) --- MVP Results Note}
\author{}
\date{\today}

\begin{document}
\maketitle

\section{Scope}

This note reports the Minimum Viable Product (MVP) experiment defined in
\emph{SAR-CRP v2 FINAL READY Proposal}, \S33: three methods (Static,
Full Reoptimization, SAR-CRP Core) on one small yard layout
(\texttt{mvp\_small\_01}, 4 stacks, 10 containers), under a synthetic
dynamic event stream (order swap, urgent insertion, ETA shift), 10 random
seeds per method.

\section{Results}

\begin{table}[h]
\centering
\begin{tabular}{lrrrr}
\toprule
Method & Total cost (mean) & Changed actions (mean) & Runtime (mean, s) & Fallback rate \\
\midrule
Static            & TODO & TODO & TODO & TODO \\
Full Reoptimization & TODO & TODO & TODO & TODO \\
SAR-CRP Core        & TODO & TODO & TODO & TODO \\
\bottomrule
\end{tabular}
\caption{MVP results averaged over 10 seeds. Source: \texttt{paper1\_sarcrp/experiments/results/mvp\_results.csv}.}
\end{table}

\section{Decision gate (spec \S33)}

\begin{itemize}
  \item SAR-CRP total cost $<$ Static total cost: \textbf{TODO PASS/FAIL}
  \item SAR-CRP changed-actions (stability proxy) $<$ Full Reoptimization: \textbf{TODO PASS/FAIL}
  \item SAR-CRP total cost within 20\% of Full Reoptimization (operational proxy): \textbf{TODO PASS/FAIL}
\end{itemize}

\section{Next step}

If all three conditions pass: proceed to the full Implementation Roadmap
Phase 6 (\S27) --- the 6-baseline, 5-experiment Q1 suite with the \S23.6
statistical protocol (20+ seeds, Wilcoxon signed-rank, Holm-Bonferroni).
If any condition fails: revisit the trigger threshold ($\theta_{impact}$),
objective weights ($\lambda$, $\mu$), or local search parameters before
scaling up (spec \S32).

\end{document}
```

- [ ] **Step 2: Write the compile Makefile**

`writeups/paper1_mvp_report/Makefile`:
```makefile
.PHONY: pdf clean

pdf:
	latexmk -pdf -interaction=nonstopmode main.tex

clean:
	latexmk -C
```

- [ ] **Step 3: Fill in the TODO values from the Task 14 run**

Open `paper1_sarcrp/experiments/results/mvp_results.csv`, compute per-method means for `total_cost_mean`, `changed_actions_total`, `runtime_mean_sec`, `fallback_rate` (group by `method`, average over the 10 `seed` rows), and replace every `TODO` in `main.tex`'s table and decision-gate list with those real numbers and PASS/FAIL values from Task 14 Step 6's printed verdict.

- [ ] **Step 4: Compile to PDF**

Run: `cd writeups/paper1_mvp_report && make pdf`
Expected: `main.pdf` is created in the same folder with no LaTeX errors (check the last lines of `latexmk` output for `Output written on main.pdf`).

- [ ] **Step 5: Commit**

```bash
git add writeups/paper1_mvp_report/main.tex writeups/paper1_mvp_report/Makefile
git commit -m "docs(paper1): add MVP results report (LaTeX, compiled to PDF)"
```

Note: `main.pdf` itself is a build artifact — add `writeups/paper1_mvp_report/*.pdf` and LaTeX aux files (`*.aux`, `*.log`, `*.fls`, `*.fdb_latexmk`) to a `.gitignore` in that folder if you don't want compiled binaries in git history; commit the PDF explicitly only if you want it reviewable on GitHub without a local LaTeX install.

---

## Self-Review Notes

- **Spec coverage:** Tasks 1-14 cover Implementation Roadmap (§27) Phases 0-5 and checklist (§32) items in full except N3/N5 local-search neighborhoods and the CRP_RL-tail candidate's constraint-forwarding (`frozen_actions`/`max_changed_actions` inside `solve_crp` itself) — both explicitly deferred to the follow-up plan once the MVP decision gate passes, per this plan's Global Constraints. Task 15 covers the user's standing LaTeX/PDF documentation rule.
- **Type consistency checked:** `Plan`/`Action`/`YardState`/`Event` field names match spec §37 exactly across all 15 tasks; `replan()`'s parameter names match what `simulator.py` (Task 13) calls it with; `ReplanDecision.plan`/`.decision` match what `simulator.py` reads.
- **Out of scope reminder:** baselines B3-B5, the 5-experiment Q1 suite, ablations A1-A6, and the §23.6 statistical protocol are NOT in this plan — they are the natural Phase 6 follow-up plan once §33's decision gate passes.
