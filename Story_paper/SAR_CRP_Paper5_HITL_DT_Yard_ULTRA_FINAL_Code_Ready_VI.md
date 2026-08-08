# PAPER 5 RESEARCH PROPOSAL — ULTRA-FINAL CODE-READY VERSION

# HITL-DT-Yard: Human-in-the-Loop Digital Twin Learning for Stable Adaptive Container Yard Decision-Making

**Tên tiếng Việt:**  
**Học có người vận hành trong vòng lặp kết hợp Digital Twin cho hệ thống ra quyết định bãi container ổn định**

**Vị trí trong roadmap:**  
Paper 1 làm replanning ổn định.  
Paper 2 làm replanning robust với execution/data không hoàn hảo.  
Paper 3 làm replanning strategic bằng cách chọn đúng intervention family.  
Paper 4 làm framework deployable across terminals.  
**Paper 5 làm framework human-adaptive bằng cách học từ operator feedback trong Digital Twin trước khi triển khai thật.**

---

## 1. Executive Summary

Paper 5 đề xuất một lớp **Human-in-the-Loop Digital Twin Learning** cho hệ thống ra quyết định bãi container. Sau Paper 1–4, hệ thống đã có khả năng tái lập kế hoạch ổn định, robust, strategic và triển khai qua nhiều cảng. Tuy nhiên, trong production thật, các quyết định AI không thể chỉ dựa trên thuật toán. Operator có thể reject, sửa, trì hoãn hoặc override đề xuất của hệ thống vì các lý do thực địa mà simulator hoặc data chưa mô hình hóa hết.

Paper 5 trả lời câu hỏi:

> **How can a stable adaptive yard decision system learn from operator feedback and manual overrides inside a digital-twin replay environment while preserving safety, stability, and operational performance before deploying updated decision policies to production?**

Ý tưởng chính:

```text
AI recommendation
    ↓
Operator feedback / override
    ↓
Feedback interpretation
    ↓
Digital Twin replay and validation
    ↓
Safety-constrained preference update
    ↓
Deployment gate
    ↓
Updated decision policy
```

Paper 5 không cố gắng thay thế con người. Nó xây một cơ chế học có kiểm soát từ con người:

- học preference của operator,
- phát hiện dạng recommendation thường bị reject,
- dùng Digital Twin để replay và kiểm thử policy mới,
- chỉ deploy nếu policy mới vượt qua safety/stability/performance gate.

---

## 2. Positioning in the Paper Series

| Paper | Tên ngắn | Câu hỏi chính | Đóng góp chính |
|---|---|---|---|
| Paper 1 | SAR-CRP | Khi retrieval information thay đổi, có nên replan không? | Stable adaptive replanning |
| Paper 2 | EA-SAR-CRP | Khi execution/data không hoàn hảo, repair/fallback thế nào? | Execution-aware robust replanning |
| Paper 3 | MISR-Yard | Khi có nhiều cách can thiệp, chọn intervention nào? | Multi-intervention orchestration |
| Paper 4 | Port-GSAR | Framework có deploy được qua nhiều cảng không? | Port-configurable cross-terminal deployment |
| Paper 5 | HITL-DT-Yard | Hệ thống học từ operator feedback thế nào mà vẫn an toàn? | Human-in-the-loop digital-twin learning |

Câu chuyện 5 paper:

```text
Stable → Robust → Strategic → Deployable → Human-Adaptive
```

---

## 3. Motivation

Trong terminal thật, operator có thể không làm theo recommendation của hệ thống vì nhiều lý do:

1. Đề xuất hợp lệ về mặt thuật toán nhưng không thuận tiện vận hành.
2. Destination stack hợp lệ nhưng operator biết khu vực đó sắp bị block.
3. Crane reassignment hợp lý trên simulator nhưng khó thực hiện do quy tắc địa phương.
4. Job resequencing giảm cost nhưng tạo churn cao cho đội vận hành.
5. AI tự tin quá mức trong tình huống low-confidence/OOD.
6. Manual override phản ánh tri thức thực địa chưa có trong mô hình.

Nếu hệ thống chỉ ghi nhận override mà không học, nó sẽ lặp lại lỗi cũ. Nếu học trực tiếp online mà không guardrail, nó có thể học sai và gây mất an toàn. Vì vậy cần một cơ chế trung gian:

> **Learn from operator feedback, but validate every update inside a Digital Twin before deployment.**

---

## 4. Research Gap

Các hướng CRP, yard planning, crane scheduling thường tập trung vào optimizer hoặc policy. Một số hệ thống thực tế có dashboard/operator approval, nhưng chưa có cơ chế rõ ràng để:

- biến operator feedback thành tín hiệu học,
- phân loại feedback theo nguyên nhân,
- cập nhật objective preferences một cách có ràng buộc,
- replay policy mới trong digital twin,
- kiểm tra safety/stability trước khi deploy,
- đo adaptation speed và rejection reduction.

Gap chính:

> Existing container yard optimization and replanning methods rarely model operator feedback as a structured learning signal and lack a safety-preserving digital-twin validation loop for adapting yard decision policies before production deployment.

> **Cần bổ sung trước khi submit — quan trọng nhất trong cả 5 paper.** Mục này hiện chưa trích dẫn literature nào, dù "học từ human feedback" hiện là một trong những mảng ML được nghiên cứu nhiều nhất (RLHF/preference learning), cùng với safe/constrained RL, interactive machine learning, và digital-twin/sim-to-real validation. Trước khi viết Related Work thật, cần trích dẫn cụ thể cho: (1) RLHF/preference-based learning cho cơ chế M2-M4, (2) safe/constrained policy optimization cho phần safety-constrained update (mục 15), (3) digital-twin/counterfactual validation trước triển khai cho M5-M6. Ngoài ra, qua "Reuse from Paper 3" (mục A1), Paper 5 gián tiếp kế thừa yêu cầu xác minh citation Shin et al. 2026 đã nêu ở Paper 1 (mục 3).

---

## 5. Core Research Question

### RQ1 — Feedback Learning

> Can operator feedback and manual overrides be converted into structured preference updates that reduce future rejection rates without degrading operational performance?

### RQ2 — Safety-Constrained Adaptation

> How can the system prevent harmful learning from noisy, inconsistent, or unsafe human overrides?

### RQ3 — Digital Twin Validation

> Can digital-twin replay detect whether a feedback-updated policy is safe and stable before deployment?

### RQ4 — Human-Adaptation Tradeoff

> How should the system trade off operator alignment, plan stability, safety, and operational efficiency?

### RQ5 — Production Readiness

> What deployment gate is needed before allowing an updated policy to affect real yard decisions?

---

## 6. Scope and Non-Scope

### In Scope

- Operator feedback schema.
- Feedback classification.
- Human preference update.
- Safety-constrained parameter adaptation.
- Digital Twin replay environment.
- Offline batch learning from feedback logs.
- Deployment gate.
- Synthetic operator models for benchmark.
- Optional real operator log discussion.

### Out of Scope

- Replacing human operators.
- Fully autonomous online reinforcement learning in production.
- Building a full commercial TOS.
- Multi-agent human behavior modeling beyond operator feedback classes.
- Real-time end-to-end learning directly on live terminal without validation.

---

## 7. Proposed Method Overview

Paper 5 introduces **HITL-DT-Yard**, composed of seven modules:

| Module | Name | Role |
|---|---|---|
| M1 | Operator Feedback Collector | Collect accept/reject/modify/override events |
| M2 | Feedback Interpreter | Convert raw feedback into structured feedback classes |
| M3 | Human Preference Estimator | Estimate operator preference shifts |
| M4 | Safety-Constrained Update Engine | Update decision parameters under guardrails |
| M5 | Digital Twin Replay Engine | Replay old/new policies under historical or synthetic events |
| M6 | Deployment Gate | Decide whether updated policy is safe to deploy |
| M7 | Monitoring and Rollback Manager | Monitor post-deployment behavior and rollback if needed |

---

## 8. High-Level Architecture

```text
             +---------------------------+
             |  Paper 4 Port-GSAR Engine |
             |  Paper 3 MISR Orchestrator|
             +-------------+-------------+
                           |
                           v
                 AI Recommendation
                           |
                           v
                  Operator Interface
                           |
       +-------------------+-------------------+
       |                                       |
       v                                       v
 Operator Accept                         Reject / Modify / Override
       |                                       |
       +-------------------+-------------------+
                           |
                           v
              Operator Feedback Collector
                           |
                           v
                Feedback Interpreter
                           |
                           v
             Human Preference Estimator
                           |
                           v
        Safety-Constrained Update Engine
                           |
                           v
              Digital Twin Replay Engine
                           |
                           v
                  Deployment Gate
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
    Deploy Updated Policy              Reject Update
          |
          v
 Monitoring + Rollback Manager
```

---

## 9. Main Novelty Claim

Paper 5 không claim rằng con người luôn đúng hoặc AI tự học online hoàn toàn.

Novelty claim đúng:

> We propose a safety-preserving human-in-the-loop digital-twin learning framework that converts operator feedback and manual overrides into constrained preference updates, validates the updated yard decision policy through digital-twin replay, and deploys it only when safety, stability, and operational performance gates are satisfied.

---

## 10. Objective Function

Paper 5 kế thừa objective từ Paper 4/Paper 3 và thêm human alignment cost. **Dùng đúng bản Paper 4 đã sửa** (bản trước ở đây thiếu `D_resource` và `C_data` — lặp lại đúng lỗi ban đầu của Paper 4 trước khi được sửa).

Với candidate decision/intervention \(a\):

\[
J_5(a;\theta)
=
C_{op}(a)
+\lambda C_{stab}(a)
+\lambda_{res} D_{resource}(a)
+\pi C_{data}(a)
+\mu C_{exec}(a)
+\nu C_{res}(a)
+\omega C_{safety}(a)
+\eta C_{int}(a)
+\xi C_{human}(a)
\]

Trong đó:

- \(C_{op}\): operational cost.
- \(C_{stab}\): stability/churn cost (container-plan, kế thừa Paper 1).
- \(D_{resource}\): resource/crane assignment churn (kế thừa Paper 3/4).
- \(C_{data}\): data confidence cost (kế thừa Paper 1/2).
- \(C_{exec}\): execution risk.
- \(C_{res}\): resource/crane cost.
- \(C_{safety}\): safety penalty.
- \(C_{int}\): intervention complexity.
- \(C_{human}\): predicted human rejection / preference misalignment cost — **mới ở Paper 5**.

Parameter vector (đúng ký hiệu Paper 3/4: `μ`=execution, `ν`=resource, `π`=data, `λ_res`=resource stability — xem ghi chú ký hiệu ở mục 17.2):

\[
\theta = \{\lambda,\lambda_{res},\pi,\mu,\nu,\omega,\eta,\xi,\theta_{trigger},\theta_{ood},...\}
\]

Paper 5 học cập nhật \(\theta\) từ feedback, nhưng chỉ trong giới hạn an toàn.

---

## 11. Human Alignment Cost

Human alignment cost đo khả năng một recommendation bị operator reject hoặc modify.

\[
C_{human}(a)=p_{reject}(a) \cdot severity(a)
\]

Trong đó:

\[
p_{reject}(a)=\sigma(w^T\phi(a))
\]

- \(\phi(a)\): feature của action/intervention.
- \(w\): human preference vector học từ feedback.
- \(severity(a)\): mức độ rủi ro nếu operator reject action đó.

Feature có thể gồm:

```text
plan_churn
changed_crane_assignment
destination_stack_occupancy
travel_distance
low_confidence_state
safety_soft_violation
intervention_complexity
historical_rejection_rate_for_similar_action
```

Phiên bản MVP có thể không dùng logistic model, mà dùng heuristic rejection score:

\[
C_{human}(a)=
q_1 I_{churn}
+q_2 I_{crane\_change}
+q_3 I_{low\_confidence}
+q_4 I_{operator\_history}
\]

---

## 12. Feedback Types

| Feedback Type | Meaning | Example |
|---|---|---|
| ACCEPT | Operator accepts recommendation | Do action as suggested |
| REJECT | Operator rejects recommendation | Reject destination S5 |
| MODIFY_DESTINATION | Operator changes relocation destination | S5 → S8 |
| MODIFY_CRANE | Operator changes assigned crane | YC1 → YC2 |
| MODIFY_SEQUENCE | Operator changes job order | Move urgent job earlier |
| DELAY_ACTION | Operator delays suggested action | Wait 5 steps |
| FORCE_ACTION | Operator forces action not suggested by AI | Manual decision |
| MARK_UNSAFE | Operator marks action unsafe | Conflict/unsafe zone |
| MARK_IMPRACTICAL | Operator marks action impractical | Too far, blocked path |
| DATA_CORRECTION | Operator corrects yard state | Container not at S3 |

---

## 13. Feedback Interpretation Classes

Raw feedback is mapped into interpretation classes:

| Class | Meaning | Learning Effect |
|---|---|---|
| SAFETY_REJECTION | Operator rejects for safety | Increase safety/soft-constraint weight |
| PRACTICALITY_REJECTION | Operationally awkward | Increase resource/practicality penalty |
| STABILITY_REJECTION | Too much churn | Increase stability weight |
| RESOURCE_CORRECTION | Crane/resource assignment changed | Update resource preference |
| SEQUENCE_CORRECTION | Order changed | Update sequence preference |
| DATA_CORRECTION | State was wrong | Update data confidence model |
| URGENCY_CORRECTION | Priority changed | Update urgency/trigger parameters |
| NOISE_OR_INCONSISTENT | Feedback not reliable | Ignore or reduce weight |

---

## 14. Data Schemas

### 14.1 OperatorFeedback Schema

```json
{
  "feedback_id": "FB_0001",
  "timestamp": 128,
  "operator_id": "OP_01",
  "port_id": "PORT_A",
  "plan_id": "P_102",
  "action_id": "A_17",
  "recommendation_id": "REC_774",
  "feedback_type": "MODIFY_DESTINATION",
  "reason_code": "unsafe_destination",
  "free_text_reason": "Stack S5 is near a blocked crane zone.",
  "original_action": {
    "type": "RELOCATE",
    "container_id": "C88",
    "from_stack": "S2",
    "to_stack": "S5",
    "assigned_crane": "YC1",
    "estimated_start": 40,
    "estimated_finish": 42
  },
  "operator_action": {
    "type": "RELOCATE",
    "container_id": "C88",
    "from_stack": "S2",
    "to_stack": "S8",
    "assigned_crane": "YC1",
    "estimated_start": 40,
    "estimated_finish": 43
  },
  "operator_confidence": 0.9,
  "safety_flag": true,
  "executed_after_override": true,
  "outcome": {
    "success": true,
    "delay_steps": 1,
    "additional_relocations": 0
  }
}
```

### 14.2 FeedbackInterpretation Schema

```json
{
  "feedback_id": "FB_0001",
  "interpreted_class": "SAFETY_REJECTION",
  "confidence": 0.85,
  "affected_cost_terms": ["C_safety", "C_human"],
  "suggested_parameter_updates": {
    "omega_safety": "+0.05",
    "xi_human": "+0.03"
  },
  "ignore_feedback": false,
  "ignore_reason": null
}
```

### 14.3 HumanPreferenceState Schema

```json
{
  "operator_group_id": "PORT_A_SHIFT_1",
  "updated_at": 500,
  "preference_vector": {
    "stability_preference": 0.65,
    "resource_preference": 0.50,
    "safety_preference": 0.90,
    "low_churn_preference": 0.70,
    "low_confidence_aversion": 0.80,
    "low_complexity_preference": 0.40
  },
  "rejection_model": {
    "model_type": "logistic_or_heuristic",
    "features": [
      "has_safety_issue",
      "soft_safety_penalty",
      "plan_churn",
      "changed_action_count",
      "changed_crane_assignment",
      "crane_travel",
      "low_confidence_state",
      "intervention_complexity",
      "expected_delay",
      "resource_conflict_penalty"
    ],
    "weights": {
      "has_safety_issue": 0.0,
      "soft_safety_penalty": 0.7,
      "plan_churn": 0.4,
      "changed_action_count": 0.0,
      "changed_crane_assignment": 0.2,
      "crane_travel": 0.0,
      "low_confidence_state": 0.5,
      "intervention_complexity": 0.0,
      "expected_delay": 0.0,
      "resource_conflict_penalty": 0.0
    }
  },
  "num_feedback_samples": 120,
  "last_validation_status": "PASSED"
}
```

> **Danh sách 10 feature trên là bộ chuẩn duy nhất** cho rejection model — dùng thống nhất ở mục 17.4, A4.2, A4.4 (bản trước 3 chỗ này dùng 3 bộ tên khác nhau: thiếu field, hoặc `travel_distance` thay vì `crane_travel`, hoặc `changed_crane_assignment_count` thay vì `changed_crane_assignment`). `preference_vector` có thêm field `low_complexity_preference` (trước đây được dùng ở `ProposeConstrainedUpdate` — mục A5.4 — nhưng không tồn tại trong schema).

### 14.4 PolicyUpdate Schema

```json
{
  "update_id": "UPD_003",
  "source_policy_id": "POLICY_OLD",
  "candidate_policy_id": "POLICY_NEW",
  "feedback_batch_id": "BATCH_2026_08_08",
  "updated_parameters": {
    "lambda_stability": 1.15,
    "omega_safety": 2.00,
    "xi_human": 0.50,
    "theta_trigger": 0.32
  },
  "update_constraints": {
    "max_parameter_delta": 0.10,
    "hard_safety_constraints_locked": true,
    "max_allowed_churn_increase": 0.05
  },
  "status": "PENDING_DIGITAL_TWIN_VALIDATION"
}
```

### 14.5 DigitalTwinReplayResult Schema

```json
{
  "replay_id": "REPLAY_001",
  "policy_id": "POLICY_NEW",
  "port_id": "PORT_A",
  "scenario_set_id": "SCENARIO_HIST_001",
  "num_scenarios": 200,
  "metrics": {
    "avg_operational_cost": 120.4,
    "avg_plan_churn": 0.18,
    "hard_safety_violation_rate": 0.0,
    "soft_safety_penalty": 2.5,
    "operator_rejection_rate_predicted": 0.12,
    "fallback_rate": 0.04,
    "timeout_rate": 0.01
  },
  "comparison_to_old_policy": {
    "operational_cost_delta": -0.04,
    "rejection_rate_delta": -0.25,
    "churn_delta": 0.02,
    "safety_violation_delta": 0.0
  },
  "gate_status": "PASSED"
}
```

### 14.6 DeploymentGateResult Schema

```json
{
  "gate_id": "GATE_001",
  "candidate_policy_id": "POLICY_NEW",
  "decision": "APPROVE_FOR_SHADOW_MODE",
  "passed_checks": [
    "NO_HARD_SAFETY_VIOLATION",
    "REJECTION_RATE_REDUCED",
    "CHURN_WITHIN_LIMIT",
    "RUNTIME_WITHIN_LIMIT"
  ],
  "failed_checks": [],
  "recommended_deployment_mode": "SHADOW_MODE",
  "rollback_policy_id": "POLICY_OLD"
}
```

---

## 15. Safety-Constrained Parameter Update

Paper 5 updates parameters only under constraints.

Let \(\theta_t\) be current parameters and \(\Delta\theta\) be proposed update.

\[
\theta_{t+1}=Clip(\theta_t+\Delta\theta,\theta_{min},\theta_{max})
\]

Hard constraints:

1. Hard safety rules cannot be weakened.
2. Any feedback that leads to hard safety violation is not used for learning.
3. Parameter update magnitude is bounded.
4. Updated policy must pass Digital Twin validation.
5. Online deployment starts in shadow mode.

Update bound:

\[
|\theta_{t+1}^{(i)}-\theta_t^{(i)}| \leq \Delta_{max}^{(i)}
\]

Default:

```text
max_parameter_delta = 0.10
```

---

## 16. Digital Twin Role

The Digital Twin is not just a simulator for evaluation. It is the safety buffer between human feedback learning and production deployment.

### Digital Twin Inputs

- PortConfig from Paper 4.
- YardGraph from Paper 4.
- Decision engine from Paper 3.
- Historical or synthetic event stream.
- Execution feedback model from Paper 2.
- Operator feedback model from Paper 5.

### Digital Twin Outputs

- Replay metrics.
- Safety violation count.
- Predicted rejection rate.
- Plan churn.
- Runtime.
- Deployment gate decision.

### Digital Twin Modes

| Mode | Description |
|---|---|
| Historical Replay | Replay real/synthetic historical events |
| Counterfactual Replay | Compare old policy vs updated policy on same scenarios |
| Stress Test | Inject high disruption / low confidence / resource conflict |
| Shadow Mode | Run updated policy without affecting real operation |
| A/B Replay | Compare two policies offline |

---

## 17. Algorithms and Pseudocode

### 17.1 Main HITL-DT-Yard Algorithm

```text
Algorithm HITL-DT-Yard
Input:
    Current policy π_old
    Feedback batch F
    PortConfig cfg
    YardGraph G
    DigitalTwin DT
    Deployment gate thresholds Γ

Output:
    Deployment decision and optional updated policy π_new

1. interpretations = []
2. For each feedback f in F:
3.     z = InterpretFeedback(f)
4.     If z.ignore_feedback == False:
5.         interpretations.append(z)

6. preference_state = EstimateHumanPreference(interpretations)

7. θ_candidate = ProposeConstrainedUpdate(π_old.θ, preference_state)

8. π_candidate = BuildPolicy(π_old, θ_candidate)

9. replay_result = DigitalTwinReplay(DT, π_old, π_candidate, cfg, G)

10. gate_result = EvaluateDeploymentGate(replay_result, Γ)

11. If gate_result.decision in {"REJECT_UPDATE", "NO_MEANINGFUL_IMPROVEMENT"}:
12.     Return π_old, gate_result     # NO_MEANINGFUL_IMPROVEMENT: an toàn nhưng không đủ lợi ích để đổi

13. If gate_result.decision == "APPROVE_FOR_SHADOW_MODE":
14.     DeployShadowMode(π_candidate)
15.     Return π_candidate, gate_result

# Bước 16-18 KHÔNG xảy ra ngay trong cùng lần gọi EvaluateDeploymentGate ở trên —
# EvaluateDeploymentGate (mục 17.7) chỉ tạo ra REJECT_UPDATE/APPROVE_FOR_SHADOW_MODE/
# NO_MEANINGFUL_IMPROVEMENT từ một lần replay. "APPROVE_FOR_ASSISTED_MODE" là quyết định
# RIÊNG, đưa ra sau khi policy đã chạy Shadow Mode đủ `shadow_mode_days` (mục 23) và
# MonitorAndRollback (17.8) không phát hiện vấn đề gì — xem Production Pathway mục 27.
16. Sau shadow_mode_days ngày, nếu MonitorAndRollback không trigger rollback nào:
17.     DeployAssistedMode(π_candidate)
18.     Return π_candidate, "APPROVE_FOR_ASSISTED_MODE"
```

---

### 17.2 InterpretFeedback

> **Ký hiệu**: dùng đúng quy ước Paper 3/4 — `μ`(`mu_execution`)=execution weight, `ν`(`nu_resource`)=resource weight, `π`(`pi_data`)=data confidence weight, `λ`(`lambda_stability`)=container-plan stability, `λ_res`(`lambda_res`)=resource stability. Bản trước dùng `mu_data` cho data weight — trùng với `μ`=execution của Paper 3/4, đã sửa thành `pi_data`.
>
> **Thứ tự kiểm tra**: `IsInconsistentFeedback(f)` được gọi **đầu tiên** (trước cả nhánh `ACCEPT`) — bản trước gọi nó gần cuối, khiến Case 2 (accept một action đã bị đánh dấu unsafe, mục A3.1) không bao giờ được kiểm tra vì nhánh `ACCEPT` đã return trước đó, và Case 1 (reject/modify nhưng operator_action giống hệt original) cũng bị các nhánh `MODIFY_CRANE`/`MODIFY_SEQUENCE` chặn trước.

```text
Function InterpretFeedback(f):
    z = new FeedbackInterpretation()
    z.feedback_id = f.feedback_id

    If IsInconsistentFeedback(f):
        z.interpreted_class = "NOISE_OR_INCONSISTENT"
        z.ignore_feedback = True
        z.ignore_reason = "Inconsistent or unsafe override"
        Return z

    If f.feedback_type == "ACCEPT":
        z.interpreted_class = "ACCEPTED_RECOMMENDATION"
        z.affected_cost_terms = []
        z.ignore_feedback = False
        Return z

    If f.safety_flag == True or f.reason_code contains "unsafe":
        z.interpreted_class = "SAFETY_REJECTION"
        z.affected_cost_terms = ["C_safety", "C_human"]
        z.suggested_parameter_updates = {"omega_safety": +0.05, "xi_human": +0.03}
        Return z

    If f.feedback_type == "MODIFY_CRANE":
        z.interpreted_class = "RESOURCE_CORRECTION"
        z.affected_cost_terms = ["C_res", "C_human"]
        z.suggested_parameter_updates = {"nu_resource": +0.03}
        Return z

    If f.feedback_type == "MODIFY_SEQUENCE":
        z.interpreted_class = "SEQUENCE_CORRECTION"
        z.affected_cost_terms = ["C_stab", "C_int"]
        z.suggested_parameter_updates = {"lambda_stability": +0.02}
        Return z

    If f.feedback_type == "DATA_CORRECTION":
        z.interpreted_class = "DATA_CORRECTION"
        z.affected_cost_terms = ["C_data"]
        z.suggested_parameter_updates = {"pi_data": +0.03}
        Return z

    z.interpreted_class = "PRACTICALITY_REJECTION"
    z.affected_cost_terms = ["C_res", "C_human"]
    z.suggested_parameter_updates = {"xi_human": +0.02}
    Return z
```

---

### 17.3 EstimateHumanPreference

> Bản trước bỏ sót `stability_preference` (1 trong 5 field khai báo ở schema mục 14.3) — không bao giờ được gán giá trị. Đã bổ sung, cùng với `low_complexity_preference` (field mới thêm vào schema, được `ProposeConstrainedUpdate` mục A5.4 dùng nhưng trước đây không tồn tại). `stability_preference` là tín hiệu rộng (gồm cả `STABILITY_REJECTION` lẫn `SEQUENCE_CORRECTION`, vì cả hai đều phản ánh phản đối do thay đổi/churn của kế hoạch), còn `low_churn_preference` là tín hiệu hẹp hơn (chỉ `STABILITY_REJECTION`).

```text
Function EstimateHumanPreference(interpretations):
    counts = CountByClass(interpretations)
    total = max(1, len(interpretations))

    pref = HumanPreferenceState()

    pref.preference_vector.safety_preference = counts["SAFETY_REJECTION"] / total
    pref.preference_vector.resource_preference = counts["RESOURCE_CORRECTION"] / total
    pref.preference_vector.stability_preference = (counts["STABILITY_REJECTION"] + counts["SEQUENCE_CORRECTION"]) / total
    pref.preference_vector.low_churn_preference = counts["STABILITY_REJECTION"] / total
    pref.preference_vector.low_confidence_aversion = counts["DATA_CORRECTION"] / total
    pref.preference_vector.low_complexity_preference = counts["PRACTICALITY_REJECTION"] / total

    pref.rejection_model = FitOrUpdateRejectionModel(interpretations)
    pref.num_feedback_samples = total

    Return pref
```

---

### 17.4 FitOrUpdateRejectionModel

> Dùng đúng 10 feature chuẩn ở mục 14.3 (`crane_travel`, không phải `travel_distance` như bản trước) và `DefaultHumanWeights()` cụ thể — xem định nghĩa ở mục A4.0 (mới bổ sung, hàm này trước đây được gọi nhưng chưa từng định nghĩa).

MVP heuristic version:

```text
Function FitOrUpdateRejectionModel(interpretations):
    weights = DefaultHumanWeights()

    For each z in interpretations:
        If z.interpreted_class == "SAFETY_REJECTION":
            weights["soft_safety_penalty"] += 0.05
            weights["has_safety_issue"] += 0.05
        If z.interpreted_class == "RESOURCE_CORRECTION":
            weights["changed_crane_assignment"] += 0.03
            weights["crane_travel"] += 0.02
        If z.interpreted_class == "STABILITY_REJECTION":
            weights["plan_churn"] += 0.04
        If z.interpreted_class == "DATA_CORRECTION":
            weights["low_confidence_state"] += 0.04

    weights = NormalizeWeights(weights)

    Return {
        "model_type": "heuristic",
        "features": list(weights.keys()),
        "weights": weights
    }
```

Optional learned version:

```text
Function FitLogisticRejectionModel(feedback_examples):
    X = ExtractRecommendationFeatures(feedback_examples)
    y = 1 if feedback is reject/modify/override else 0
    model = LogisticRegression(class_weight="balanced")
    model.fit(X, y)
    Return model
```

---

### 17.5 ProposeConstrainedUpdate

> Dùng đúng step-size khai báo ở bảng tham số (mục 23) thay vì hardcode `0.05` cho mọi trọng số (bản trước không phân biệt `safety_weight_update=0.05`, `resource_weight_update=0.03`, `stability_weight_update=0.04`). Đổi `mu_data`→`pi_data`; thêm cập nhật `lambda_res` (song song `lambda_stability`, vì `STABILITY_REJECTION`/"too much churn" — mục 13 — bao gồm cả container-plan lẫn resource/crane churn).

```text
Function ProposeConstrainedUpdate(theta_old, preference_state):
    theta_new = copy(theta_old)

    theta_new.omega_safety     += safety_weight_update     * preference_state.safety_preference
    theta_new.nu_resource      += resource_weight_update   * preference_state.resource_preference
    theta_new.lambda_stability += stability_weight_update  * preference_state.low_churn_preference
    theta_new.lambda_res       += stability_weight_update  * preference_state.low_churn_preference
    theta_new.pi_data          += data_weight_update        * preference_state.low_confidence_aversion
    theta_new.xi_human         += human_weight_update

    theta_new = ClipParameterDelta(theta_old, theta_new, max_delta=0.10)
    theta_new = EnforceParameterBounds(theta_new)
    theta_new = LockHardSafetyConstraints(theta_new)

    Return theta_new
```

Default (khớp mục 23, bổ sung `data_weight_update` còn thiếu):

```text
safety_weight_update    = 0.05
resource_weight_update  = 0.03
stability_weight_update = 0.04
data_weight_update      = 0.03   # mới bổ sung
human_weight_update     = 0.05
```

---

### 17.6 DigitalTwinReplay

> `gate_status` được gán bằng cách gọi thẳng `EvaluateDeploymentGate` (mục 17.7) — **nguồn quyết định gate duy nhất trong toàn bộ paper**. Bản trước gọi `PreliminaryGateStatus(replay_result)` chỉ với 1 tham số trong khi hàm đó (A6.2 cũ) cần 2 (`comparison, thresholds`), và có logic/tên threshold khác hẳn `EvaluateDeploymentGate` — đã gộp làm một, xem ghi chú ở mục A6.2.

```text
Function DigitalTwinReplay(DT, pi_old, pi_candidate, cfg, G):
    scenarios = DT.LoadReplayScenarios(cfg.port_id)

    old_metrics = []
    new_metrics = []

    For each scenario s in scenarios:
        result_old = DT.RunPolicy(pi_old, s, cfg, G)
        result_new = DT.RunPolicy(pi_candidate, s, cfg, G)

        old_metrics.append(result_old.metrics)
        new_metrics.append(result_new.metrics)

    replay_result = ComparePolicyMetrics(old_metrics, new_metrics)
    replay_result.gate_status = EvaluateDeploymentGate(replay_result, DT.thresholds).decision

    Return replay_result
```

---

### 17.7 EvaluateDeploymentGate

> **Hàm gate duy nhất** — DT replay (17.6/A6.3) gọi hàm này để điền `gate_status` (chỉ lấy `.decision`), Main Algorithm (17.1) gọi lại để lấy đối tượng `DeploymentGateResult` đầy đủ (`passed_checks`, `recommended_deployment_mode` — khớp schema mục 14.6). Đã gộp thêm check `unsafe_recommendation_rate` và outcome thứ 3 `NO_MEANINGFUL_IMPROVEMENT` từ bản `PreliminaryGateStatus` cũ (A6.2, nay đã bỏ, xem ghi chú ở đó).

```text
Function EvaluateDeploymentGate(replay_result, thresholds):
    gate = DeploymentGateResult()

    If replay_result.metrics.hard_safety_violation_rate > 0:
        gate.decision = "REJECT_UPDATE"
        gate.failed_checks.append("HARD_SAFETY_VIOLATION")
        Return gate

    If replay_result.comparison_to_old_policy.unsafe_recommendation_rate_delta > thresholds.max_unsafe_increase:
        gate.decision = "REJECT_UPDATE"
        gate.failed_checks.append("UNSAFE_RECOMMENDATION_INCREASED")
        Return gate

    If replay_result.comparison_to_old_policy.churn_delta > thresholds.max_churn_increase:
        gate.decision = "REJECT_UPDATE"
        gate.failed_checks.append("CHURN_TOO_HIGH")
        Return gate

    If replay_result.comparison_to_old_policy.operational_cost_delta > thresholds.max_cost_increase:
        gate.decision = "REJECT_UPDATE"
        gate.failed_checks.append("OPERATIONAL_COST_DEGRADED")
        Return gate

    If replay_result.metrics.timeout_rate > thresholds.max_timeout_rate:
        gate.decision = "REJECT_UPDATE"
        gate.failed_checks.append("RUNTIME_UNSTABLE")
        Return gate

    gate.passed_checks.append("NO_HARD_SAFETY_VIOLATION")
    gate.passed_checks.append("CHURN_WITHIN_LIMIT")
    gate.passed_checks.append("RUNTIME_WITHIN_LIMIT")

    If replay_result.comparison_to_old_policy.rejection_rate_delta < -thresholds.min_rejection_reduction:
        gate.passed_checks.append("REJECTION_RATE_REDUCED")
        gate.decision = "APPROVE_FOR_SHADOW_MODE"
        gate.recommended_deployment_mode = "SHADOW_MODE"
        Return gate

    If replay_result.comparison_to_old_policy.operational_cost_delta <= -thresholds.min_cost_improvement:
        gate.passed_checks.append("COST_IMPROVED")
        gate.decision = "APPROVE_FOR_SHADOW_MODE"
        gate.recommended_deployment_mode = "SHADOW_MODE"
        Return gate

    gate.decision = "NO_MEANINGFUL_IMPROVEMENT"
    Return gate
```

Default thresholds (`Γ`, bổ sung 2 field còn thiếu — `max_unsafe_increase`, `min_rejection_reduction`, `min_cost_improvement`):

```text
max_unsafe_increase    = 0.02
max_churn_increase     = epsilon_s = 0.05    # khớp mục 22.5/23
max_cost_increase      = epsilon_c = 0.02    # khớp mục 22.5/23
max_timeout_rate       = 0.05                # khớp mục 23
min_rejection_reduction = 0.0                # bất kỳ giảm nào cũng tính (RejectRate_new < RejectRate_old, mục 22.5)
min_cost_improvement    = 0.0
```

---

### 17.8 Rollback Monitor

```text
Function MonitorAndRollback(policy, live_metrics, rollback_policy):
    If live_metrics.hard_safety_violation_rate > 0:
        Rollback(rollback_policy)
        Return "ROLLBACK_HARD_SAFETY"

    If live_metrics.operator_rejection_rate > policy.expected_rejection_rate + tolerance:
        Rollback(rollback_policy)
        Return "ROLLBACK_REJECTION_SPIKE"

    If live_metrics.plan_churn > policy.max_allowed_churn:
        Rollback(rollback_policy)
        Return "ROLLBACK_CHURN_SPIKE"

    Return "CONTINUE"
```

---

## 18. Benchmark Design

Paper 5 benchmark should include three levels.

### Level 1 — Synthetic Operator Feedback

Simulate operator profiles:

| Profile | Behavior |
|---|---|
| Stability-focused | Rejects high plan churn |
| Safety-focused | Rejects soft safety violations |
| Resource-focused | Rejects long crane travel / reassignment |
| Data-skeptical | Rejects low-confidence state decisions |
| Mixed operator | Combination of all above |

### Level 2 — Digital Twin Replay

Replay scenarios generated from Paper 4/Paper 3 benchmark:

- retrieval disruptions,
- execution failures,
- resource bottlenecks,
- safety conflicts,
- low confidence states,
- cross-terminal layout differences.

### Level 3 — Optional Real Logs

If available, use 1–2 weeks of real logs:

- recommendation logs,
- accept/reject events,
- manual override logs,
- action execution outcome,
- operator comments or reason codes.

If real logs are unavailable, the paper should explicitly state that real-world validation is future work.

---

## 19. Benchmark Instance Counts

| Setting | Number of scenarios | Feedback samples | Purpose |
|---|---:|---:|---|
| Small synthetic | 100 | 500 | Debug and sanity check |
| Medium synthetic | 300 | 2,000 | Main benchmark |
| Large synthetic | 500 | 5,000 | Scalability |
| Stress test | 200 | 1,000 | Safety and rollback |
| Cross-port | 100 per port | 1,000 per port | Generalization with Paper 4 |

---

## 20. Baselines

| Baseline | Description |
|---|---|
| B1 No Learning | Paper 4/3 policy, ignores operator feedback |
| B2 Naive Online Learning | Updates parameters immediately without Digital Twin validation |
| B3 Feedback Logging Only | Records feedback but does not adapt |
| B4 Unconstrained Preference Update | Learns from feedback but no safety-constrained update |
| B5 Digital Twin Validation Only | Tests policy in DT but does not learn from feedback |
| B6 HITL without DT | Learns from feedback but skips replay validation |
| B7 HITL-DT-Yard | Proposed method |

Expected finding:

- B2 may reduce rejection but can hurt safety/stability.
- B4 may overfit noisy operator feedback.
- B6 may improve alignment but lacks deployment safety.
- B7 should reduce rejection while preserving safety and stability.

---

## 21. Metrics

### 21.1 Human Alignment Metrics

```text
operator_rejection_rate
operator_modification_rate
acceptance_rate
feedback_regret
predicted_rejection_accuracy
```

### 21.2 Operational Metrics

```text
relocation count
retrieval delay
total operational cost
completion time
fallback rate
```

### 21.3 Stability Metrics

```text
plan churn
changed actions
changed crane assignment
sequence churn
rollback count
```

### 21.4 Safety Metrics

```text
hard safety violation rate
soft safety penalty
unsafe recommendation rate
manual safety rejection rate
```

### 21.5 Learning Metrics

```text
adaptation speed
samples needed to reduce rejection by X%
preference recovery ratio
parameter drift
feedback noise robustness
```

### 21.6 Digital Twin Validation Metrics

```text
DT replay pass rate
shadow mode failure rate
policy approval rate
rollback trigger rate
old-vs-new counterfactual gap
```

---

## 22. Key Formulas

### 22.1 Rejection Rate Reduction

\[
RRR = \frac{RejectRate_{old}-RejectRate_{new}}{RejectRate_{old}}
\]

### 22.2 Safety-Preserved Improvement

\[
SPI = RRR \cdot \mathbb{1}[HardViolationRate=0] \cdot \mathbb{1}[ChurnIncrease \leq \epsilon]
\]

### 22.3 Feedback Adaptation Speed

\[
AS(k)=RejectRate(0)-RejectRate(k)
\]

where \(k\) is number of feedback samples used.

### 22.4 Policy Drift

\[
Drift(\theta_t,\theta_0)=||\theta_t-\theta_0||_2
\]

### 22.5 Digital Twin Approval Criterion

Policy update is approved if:

\[
HardViolationRate=0
\]

\[
Cost_{new} \leq Cost_{old}(1+\epsilon_c)
\]

\[
Churn_{new} \leq Churn_{old}+\epsilon_s
\]

\[
RejectRate_{new} < RejectRate_{old}
\]

Default:

```text
epsilon_c = 0.02
epsilon_s = 0.05
```

---

## 23. Parameter Table

| Parameter | Meaning | Default |
|---|---|---:|
| xi_human | Human alignment cost weight | 0.5 |
| max_parameter_delta | Max update per batch | 0.10 |
| min_feedback_batch | Minimum feedback samples before update | 100 |
| epsilon_c | Max allowed operational degradation | 0.02 |
| epsilon_s | Max allowed churn increase | 0.05 |
| max_timeout_rate | Max allowed timeout rate | 0.05 |
| shadow_mode_days | Shadow testing duration | 7 |
| rejection_spike_tolerance | Rollback threshold for rejection spike | 0.10 |
| feedback_noise_threshold | Ignore feedback if inconsistency exceeds | 0.30 |
| safety_weight_update | Safety parameter update step | 0.05 |
| resource_weight_update | Resource parameter update step | 0.03 |
| stability_weight_update | Stability parameter update step (dùng cho cả `lambda_stability` và `lambda_res`) | 0.04 |
| data_weight_update | Data confidence (`π`) parameter update step — mới bổ sung | 0.03 |
| human_weight_update | Human alignment update step | 0.05 |
| max_policy_drift | Maximum L2 drift from base policy | 0.50 |
| replay_scenarios_min | Minimum DT replay scenarios | 100 |
| q1 (churn) | MVP heuristic C_human weight cho plan churn | 0.30 |
| q2 (crane_change) | MVP heuristic C_human weight cho đổi crane | 0.20 |
| q3 (low_confidence) | MVP heuristic C_human weight cho low confidence | 0.30 |
| q4 (operator_history) | MVP heuristic C_human weight cho lịch sử reject tương tự | 0.20 |

---

## 24. Experiments

### Experiment 1 — Feedback Learning Sanity Check

Goal: Verify whether feedback reduces future rejection.

Compare:

- No Learning
- Feedback Logging Only
- HITL-DT-Yard

Metrics:

- rejection rate,
- acceptance rate,
- operational cost,
- churn.

Expected result:

> HITL-DT-Yard reduces rejection while keeping cost/churn within gate thresholds.

---

### Experiment 2 — Safety-Constrained vs Unconstrained Learning

Goal: Show why safety constraints are necessary.

Compare:

- Naive Online Learning
- Unconstrained Preference Update
- HITL-DT-Yard

Metrics:

- hard violation rate,
- soft safety penalty,
- rejection rate,
- rollback rate.

Expected result:

> Naive/unconstrained learning may reduce rejection but increases unsafe or unstable behavior. HITL-DT-Yard preserves safety.

---

### Experiment 3 — Digital Twin Validation Benefit

Goal: Show value of DT replay before deployment.

Compare:

- HITL without DT
- Digital Twin Validation Only
- HITL-DT-Yard

Metrics:

- policy approval quality,
- shadow-mode failure rate,
- rollback count,
- DT pass/fail accuracy.

Expected result:

> DT replay reduces bad policy deployment and rollback.

---

### Experiment 4 — Operator Profile Adaptation

Goal: Test different operator preference profiles.

Profiles:

- stability-focused,
- safety-focused,
- resource-focused,
- data-skeptical,
- mixed.

Metrics:

- samples to adapt,
- rejection reduction,
- parameter drift,
- performance degradation.

Expected result:

> HITL-DT-Yard adapts differently to different operator profiles while staying within safety constraints.

---

### Experiment 5 — Feedback Noise Robustness

Goal: Test noisy or inconsistent feedback.

Noise levels:

```text
0%, 10%, 20%, 30%, 40%
```

Metrics:

- learned parameter stability,
- rejection reduction,
- unsafe recommendation rate,
- ignored feedback ratio.

Expected result:

> Safety-constrained filtering prevents severe degradation under noisy feedback.

---

### Experiment 6 — Cross-Port Human Adaptation

Goal: Combine Paper 4 and Paper 5.

Protocol:

```text
Train/tune base policy on Port A
Deploy to Port B with Port-GSAR calibration
Collect synthetic/operator feedback on Port B
Update with HITL-DT-Yard
Validate in Digital Twin
```

Metrics:

- transfer gap,
- rejection rate after transfer,
- calibration + feedback recovery ratio,
- DT approval rate.

Expected result:

> Port-GSAR handles structural transfer; HITL-DT-Yard handles human/operational preference adaptation.

---

### Statistical Protocol (bắt buộc, dùng chung nguyên tắc với Paper 1 mục 23.6 / Paper 2 mục 44 / Paper 3 mục 32 / Paper 4 mục 24)

Paper 5 hiện chưa có seed/CI/kiểm định nào cho 6 experiment — bổ sung:

```text
Số lần lặp:
    Mỗi (operator profile, noise level, baseline) chạy với >= 20 random seed
    (kiểm soát cả synthetic feedback generation lẫn event stream).

Báo cáo:
    Mean +/- 95% CI cho mọi metric ở mục 21.

Kiểm định ý nghĩa:
    Wilcoxon signed-rank test (paired theo seed) khi so HITL-DT-Yard (B7)
    với từng baseline B1-B6 trên rejection_rate và hard_safety_violation_rate.
    Hiệu chỉnh Holm-Bonferroni cho 6 so sánh cùng lúc.

Effect size:
    Báo cáo effect size bên cạnh p-value, đặc biệt cho hard_safety_violation_rate
    và rollback_trigger_rate (rare-event metrics).

Áp dụng cùng protocol cho Experiment 4 (operator profile) và Experiment 5
(noise robustness) trên từng mức profile/noise riêng.
```

---

## 25. Ground Truth / Proxy

Since human feedback has no universal ground truth, Paper 5 uses three proxy levels:

1. **Synthetic Operator Ground Truth**  
   The operator profile defines known preference weights. The learned weights can be compared to the true synthetic weights.

2. **Counterfactual Digital Twin Outcome**  
   Compare AI recommendation vs operator override under the same scenario in Digital Twin.

3. **Historical Replay Outcome**  
   If real logs exist, use executed outcome after override as a weak label.

---

## 26. Timeout Protocol

| Operation | Timeout | Note |
|---|---:|---|
| InterpretFeedback batch | 10s per 1,000 feedback | Offline |
| EstimateHumanPreference | 30s | Offline batch |
| ProposeConstrainedUpdate | 5s | Lightweight |
| DigitalTwinReplay small | 5 min | Offline |
| DigitalTwinReplay medium | 20 min | Offline |
| DigitalTwinReplay large | 60 min | Offline |
| DeploymentGate evaluation | 10s | After replay |
| Online recommendation | Same as Paper 4 | No online learning delay |

Important:

> Learning and Digital Twin validation are offline. Production recommendation latency must not depend on feedback training.

---

## 27. Production Deployment Pathway

### Stage 0 — Offline Research

- Synthetic feedback.
- Digital Twin replay.
- No real operation.

### Stage 1 — Shadow Mode

- AI gives recommendations.
- Operator cannot see or use updated policy.
- System compares what it would recommend vs actual human decisions.

### Stage 2 — Assisted Mode

- Operator sees recommendation.
- Operator can accept/reject/modify.
- All feedback is logged.

### Stage 3 — Controlled Update

- Policy updates are generated offline.
- DT validation required.
- Human manager approval required.

### Stage 4 — Production with Rollback

- Updated policy used in assisted mode.
- Monitoring and rollback active.

---

## 28. Code Reuse Strategy

Reuse from Paper 4:

```text
PortConfig schema
YardGraph builder
OOD detector
Few-shot calibration pipeline
Deployment mode selector
Transfer metrics
```

Reuse from Paper 3:

```text
MISR-Yard decision orchestrator
Intervention families
Resource cost
Resource stability
Intervention complexity
Candidate evaluation
```

Reuse from Paper 2:

```text
ExecutionFeedback schema
StateReliability estimator
ExecutionImpact estimator
SafetyConstraint schema
Fallback hierarchy
Metrics logger
```

Reuse from Paper 1:

```text
Stable replanning trigger
Freeze horizon
Plan stability cost
Retrieval impact estimator
Repair planner core
```

New in Paper 5:

```text
OperatorFeedback schema
FeedbackInterpreter
HumanPreferenceEstimator
SafetyConstrainedUpdateEngine
DigitalTwinReplayEngine
DeploymentGate
RollbackMonitor
SyntheticOperatorModel
HITL experiment runner
```

---

## 29. Suggested Repository Structure

```text
hitl_dt_yard/
  schemas/
    operator_feedback.py
    feedback_interpretation.py
    human_preference_state.py
    policy_update.py
    replay_result.py
    deployment_gate.py

  feedback/
    collector.py
    interpreter.py
    synthetic_operator.py
    feedback_filters.py

  learning/
    preference_estimator.py
    rejection_model.py
    constrained_update.py
    parameter_bounds.py

  digital_twin/
    replay_engine.py
    counterfactual_runner.py
    stress_scenarios.py
    replay_metrics.py

  deployment/
    gate.py
    shadow_mode.py
    rollback_monitor.py

  experiments/
    exp1_feedback_learning.py
    exp2_safety_constrained.py
    exp3_digital_twin.py
    exp4_operator_profiles.py
    exp5_noise_robustness.py
    exp6_cross_port_hitl.py

  reports/
    feedback_learning_report.md
    digital_twin_validation_report.md
    deployment_gate_report.md
```

---

## 30. MVP Implementation Plan

### MVP Phase 1 — Feedback Schema and Synthetic Operator

Implement:

- OperatorFeedback schema.
- Synthetic operator profiles.
- Feedback generator.

Gate:

```text
Can generate at least 500 feedback samples across 5 operator profiles.
```

### MVP Phase 2 — Feedback Interpretation

Implement:

- InterpretFeedback.
- FeedbackInterpretation schema.
- Noise/inconsistency filter.

Gate:

```text
At least 90% synthetic feedback mapped to expected interpretation classes.
```

### MVP Phase 3 — Preference Update

Implement:

- HumanPreferenceEstimator.
- Heuristic rejection model.
- Safety-constrained parameter update.

Gate:

```text
Parameter updates are bounded and hard safety constraints are unchanged.
```

### MVP Phase 4 — Digital Twin Replay

Implement:

- Replay old policy vs candidate policy.
- Compare metrics.
- DeploymentGate.

Gate:

```text
Any policy with hard safety violation is rejected.
```

### MVP Phase 5 — Experiments

Run:

- Exp 1 Feedback Learning.
- Exp 2 Safety-Constrained Learning.
- Exp 3 Digital Twin Validation.

Gate:

```text
HITL-DT-Yard reduces rejection rate by at least 15% without hard safety violations and with churn increase <= 5%.
```

---

## 31. Final Coding Checklist

```text
[ ] OperatorFeedback schema
[ ] FeedbackInterpretation schema
[ ] HumanPreferenceState schema
[ ] PolicyUpdate schema
[ ] DigitalTwinReplayResult schema
[ ] DeploymentGateResult schema
[ ] Synthetic operator profiles
[ ] Feedback generator
[ ] InterpretFeedback()
[ ] IsInconsistentFeedback()
[ ] EstimateHumanPreference()
[ ] FitOrUpdateRejectionModel()
[ ] ProposeConstrainedUpdate()
[ ] ClipParameterDelta()
[ ] EnforceParameterBounds()
[ ] LockHardSafetyConstraints()
[ ] DigitalTwinReplay()
[ ] ComparePolicyMetrics()
[ ] EvaluateDeploymentGate()
[ ] MonitorAndRollback()
[ ] Experiment 1 runner
[ ] Experiment 2 runner
[ ] Experiment 3 runner
[ ] Experiment 4 runner
[ ] Experiment 5 runner
[ ] Experiment 6 runner
[ ] Metrics logger
[ ] Report generator
[ ] MVP gate report
```

---

## 32. Risks and Mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| Synthetic operator unrealistic | Reviewer may question validity | Use multiple profiles + sensitivity analysis |
| Human feedback noisy | Learning can overfit | Feedback filtering + bounded update |
| Unsafe override | Operator may be wrong | Do not learn from unsafe overrides |
| DT not realistic | Replay may not predict live outcome | State limitation + optional real logs |
| Policy drift | Too much adaptation | Max policy drift constraint |
| Rejection reduction hurts cost | Human alignment may overfit | Deployment gate includes operational cost |

---

## 33. Limitations

1. Real human/operator logs may not be available initially.
2. Synthetic operator profiles approximate real behavior.
3. Digital Twin fidelity determines validation quality.
4. Feedback reasons may be noisy or incomplete.
5. The method adapts preferences, not the entire low-level optimizer.
6. Full online learning in live production is intentionally avoided for safety.
7. Related Work grounding still needs concrete citations on RLHF/preference learning, safe RL, and digital-twin validation literature (mục 4).
8. Depends indirectly on Shin et al. 2026 (CRP_RL) via Paper 3 reuse, which still needs citation verification (same requirement as Paper 1 mục 3).

---

## 34. Expected Contributions

### C1 — Problem Formulation

Formulate human-in-the-loop stable adaptive yard decision-making with digital-twin validation.

### C2 — Feedback-to-Preference Learning

Convert operator feedback and overrides into structured preference updates.

### C3 — Safety-Constrained Adaptation

Update decision parameters under hard safety, stability, and drift constraints.

### C4 — Digital Twin Deployment Gate

Validate updated policies through counterfactual replay before deployment.

### C5 — Benchmark and Evaluation Protocol

Introduce synthetic operator profiles, feedback noise tests, and cross-port HITL adaptation experiments.

---

## 35. Abstract Draft

Stable adaptive decision-making for container yard operations must not only optimize relocation, execution recovery, intervention selection, and cross-terminal deployment, but also adapt to the preferences and practical knowledge of human operators. In real terminals, operators frequently reject, modify, or override algorithmic recommendations due to safety concerns, operational inconvenience, local constraints, or incomplete system state. Existing container yard optimization methods rarely treat such feedback as a structured learning signal, and direct online adaptation can introduce unsafe or unstable behavior. This paper proposes HITL-DT-Yard, a human-in-the-loop digital-twin learning framework for stable adaptive container yard decision-making. The proposed framework collects operator feedback, interprets it into structured feedback classes, estimates human preference shifts, and proposes bounded updates to decision parameters. Before deployment, each updated policy is evaluated through digital-twin replay under historical, synthetic, and stress scenarios. A deployment gate approves the update only if safety, stability, runtime, and operational performance constraints are satisfied. Experiments with synthetic operator profiles and digital-twin replay evaluate rejection reduction, safety preservation, feedback noise robustness, and cross-port adaptation. The results are expected to show that human feedback can improve operator alignment without sacrificing safety or stability when updates are constrained and validated before deployment.

---

## 36. Final Positioning Sentence

> Paper 1 makes replanning stable. Paper 2 makes it robust. Paper 3 makes it strategic. Paper 4 makes it deployable across terminals. Paper 5 makes it human-adaptive by learning from operator feedback through safety-constrained digital-twin validation.

---

## 37. Final Recommendation

Paper 5 is a strong extension, but it should be pursued after a working prototype of Paper 3/4 exists. Unlike Paper 1–4, Paper 5 depends heavily on feedback logs, operator modeling, and digital-twin replay quality. Therefore, the best strategy is:

```text
First implement Paper 1–3 core decision engine.
Then implement Paper 4 PortConfig/YardGraph.
Then build Paper 5 feedback logging and Digital Twin replay layer.
```

Paper 5 is especially valuable for production, because it addresses the real deployment question:

> How does the system improve after human operators interact with it?


---

# ADDENDUM — ULTRA-FINAL CODE-READY IMPLEMENTATION APPENDIX

Appendix này bổ sung các thiếu sót còn lại để Paper 5 đạt mức **CODE-READY**, tương đương Paper 1–4. Các phần dưới đây được thiết kế để lập trình viên có thể chuyển trực tiếp thành class, function, unit test và experiment pipeline.

---

## A1. Implementation Boundary

Paper 5 không thay thế decision engine của Paper 1–4. Paper 5 chỉ thêm một lớp học từ phản hồi người vận hành và một lớp kiểm định bằng Digital Twin.

```text
Reuse from Paper 1:
- Stable replanning objective
- Stability cost
- Retrieval-event handling
- Freeze horizon
- Basic repair planner

Reuse from Paper 2:
- ExecutionFeedback schema
- StateReliability estimator
- ExecutionImpact estimator
- Safety-aware fallback hierarchy
- SafetyConstraint schema

Reuse from Paper 3:
- MISR-Yard intervention families
- Resource-aware candidate evaluation
- Intervention complexity cost
- Multi-intervention decision orchestrator

Reuse from Paper 4:
- PortConfig schema
- YardGraph schema
- Cross-terminal deployment mode
- OOD score and calibration logic
- Production deployment fallback mode

New in Paper 5:
- OperatorFeedback logging
- FeedbackInterpretation
- HumanPreferenceState
- SyntheticOperatorProfile
- Feedback noise model
- Safety-constrained parameter update
- Digital Twin replay validation
- Deployment gate
- Rollback monitor
- RollbackEvent schema
```

---

## A2. Additional Data Schemas

### A2.1 SyntheticOperatorProfile Schema

```json
{
  "profile_id": "SAFETY_FOCUSED",
  "description": "Operator who prioritizes safety over other objectives",
  "preference_weights": {
    "safety_weight": 0.90,
    "stability_weight": 0.50,
    "resource_weight": 0.40,
    "data_aversion": 0.60,
    "urgency_weight": 0.30,
    "intervention_complexity_weight": 0.50
  },
  "thresholds": {
    "churn_threshold": 0.20,
    "travel_threshold": 10.0,
    "confidence_threshold": 0.70,
    "delay_threshold": 5.0,
    "complexity_threshold": 0.40
  },
  "noise_level": 0.05,
  "consistency": 0.85,
  "preferred_feedback_types": [
    "REJECT",
    "MARK_UNSAFE",
    "MODIFY_DESTINATION"
  ]
}
```

### A2.2 RollbackEvent Schema

```json
{
  "rollback_id": "RB_001",
  "timestamp": 500,
  "policy_id": "POLICY_NEW",
  "rollback_policy_id": "POLICY_OLD",
  "trigger": "HARD_SAFETY_VIOLATION",
  "details": {
    "violation_count": 3,
    "first_violation_time": 420,
    "affected_actions": ["A17", "A22"],
    "metric_snapshot": {
      "hard_safety_violations": 3,
      "plan_churn": 0.35,
      "operator_rejection_rate": 0.42
    }
  },
  "operator_notified": true,
  "rollback_status": "COMPLETED"
}
```

### A2.3 FeedbackExample Schema for Rejection Model

```json
{
  "example_id": "EX_001",
  "recommendation_id": "REC_104",
  "features": {
    "has_safety_issue": 0,
    "soft_safety_penalty": 0.15,
    "plan_churn": 0.22,
    "changed_action_count": 2,
    "changed_crane_assignment": 1,
    "crane_travel": 12.0,
    "low_confidence_state": 0.36,
    "intervention_complexity": 0.35,
    "expected_delay": 4.0,
    "resource_conflict_penalty": 0.0
  },
  "feedback_type": "REJECT",
  "is_rejected_or_modified": 1
}
```

---

## A3. Detailed Pseudocode for Missing Functions

### A3.1 IsInconsistentFeedback

```text
Function IsInconsistentFeedback(f, confidence_threshold=0.40):
    # Case 1: user rejects/modifies but proposed operator action is identical
    If f.operator_action == f.original_action and f.feedback_type in {"REJECT", "MODIFY_DESTINATION", "MODIFY_CRANE", "MODIFY_SEQUENCE"}:
        Return True

    # Case 2: user accepts an action already marked unsafe by safety validator
    If f.safety_flag == True and f.feedback_type == "ACCEPT":
        Return True

    # Case 3: low confidence human feedback should not drive learning
    If f.operator_confidence < confidence_threshold:
        Return True

    # Case 4: missing required operator action for modification feedback
    If f.feedback_type in {"MODIFY_DESTINATION", "MODIFY_CRANE", "MODIFY_SEQUENCE", "DELAY_ACTION"} and f.operator_action is None:
        Return True

    # Case 5: contradictory free-text reason or reason code
    If ContainsContradictoryReason(f.free_text_reason, f.reason_code):
        Return True

    Return False
```

### A3.2 ContainsContradictoryReason

```text
Function ContainsContradictoryReason(text, reason_code):
    If text is None:
        Return False

    text_lower = LowerCase(text)

    contradiction_pairs = [
        ("safe", "unsafe"),
        ("available", "unavailable"),
        ("low priority", "urgent"),
        ("near", "too far"),
        ("valid", "invalid")
    ]

    For each (word_a, word_b) in contradiction_pairs:
        If word_a in text_lower and word_b in text_lower:
            Return True

    If reason_code == "UNSAFE" and "safe" in text_lower and "unsafe" not in text_lower:
        Return True

    Return False
```

---

## A4. Rejection Model: Heuristic and Logistic Versions

### A4.0 DefaultHumanWeights

Được gọi ở mục 17.4 và A4.2 nhưng trước đây chưa từng định nghĩa — bổ sung giá trị khởi tạo trước khi có feedback nào (10 feature chuẩn, khớp mục 14.3):

```text
Function DefaultHumanWeights():
    Return {
        "has_safety_issue": 0.0,
        "soft_safety_penalty": 0.5,
        "plan_churn": 0.3,
        "changed_action_count": 0.0,
        "changed_crane_assignment": 0.2,
        "crane_travel": 0.1,
        "low_confidence_state": 0.3,
        "intervention_complexity": 0.1,
        "expected_delay": 0.1,
        "resource_conflict_penalty": 0.1
    }
```

### A4.1 FitOrUpdateRejectionModel

```text
Function FitOrUpdateRejectionModel(feedback_examples, mode="auto"):
    If len(feedback_examples) < MIN_LOGISTIC_SAMPLES:
        Return FitHeuristicRejectionModel(feedback_examples)

    If mode == "heuristic":
        Return FitHeuristicRejectionModel(feedback_examples)

    If mode == "logistic" or mode == "auto":
        Return FitLogisticRejectionModel(feedback_examples)
```

### A4.2 FitHeuristicRejectionModel

```text
Function FitHeuristicRejectionModel(feedback_examples):
    weights = DefaultHumanWeights()

    For each example in feedback_examples:
        z = example.interpretation

        If z.interpreted_class == "SAFETY_REJECTION":
            weights["soft_safety_penalty"] += 0.05
            weights["has_safety_issue"] += 0.05

        If z.interpreted_class == "RESOURCE_CORRECTION":
            weights["changed_crane_assignment"] += 0.03
            weights["crane_travel"] += 0.02

        If z.interpreted_class == "STABILITY_REJECTION":
            weights["plan_churn"] += 0.04

        If z.interpreted_class == "DATA_CORRECTION":
            weights["low_confidence_state"] += 0.04

        If z.interpreted_class == "URGENCY_CORRECTION":
            weights["expected_delay"] += 0.03

    weights = NormalizeWeights(weights)

    Return {
        "model_type": "heuristic",
        "features": list(weights.keys()),
        "weights": weights
    }
```

### A4.3 FitLogisticRejectionModel

```text
Function FitLogisticRejectionModel(feedback_examples):
    X = []
    y = []

    For each example in feedback_examples:
        features = ExtractRecommendationFeatures(example)
        X.append(features)

        If example.feedback_type in {"REJECT", "MODIFY_DESTINATION", "MODIFY_CRANE", "MODIFY_SEQUENCE", "DELAY_ACTION", "MARK_UNSAFE", "MARK_IMPRACTICAL"}:
            y.append(1)
        Else:
            y.append(0)

    model = LogisticRegression(
        penalty="l2",
        C=1.0,
        class_weight="balanced",
        max_iter=1000
    )
    model.fit(X, y)

    Return {
        "model_type": "logistic_regression",
        "features": FeatureNames(),
        "model": model,
        "num_samples": len(feedback_examples)
    }
```

### A4.4 ExtractRecommendationFeatures

> Thứ tự 10 phần tử khớp đúng thứ tự `features` khai báo ở schema mục 14.3. Đổi `changed_crane_assignment_count` → `changed_crane_assignment` cho khớp tên field dùng ở A4.1/A4.2/17.4 (bản trước lệch tên giữa vector đặc trưng và dict trọng số).

```text
Function ExtractRecommendationFeatures(example):
    r = example.recommendation

    Return [
        Binary(r.has_safety_issue),
        r.soft_safety_penalty,
        r.plan_churn,
        r.changed_action_count,
        r.changed_crane_assignment,
        r.crane_travel,
        1.0 - r.state_confidence,
        r.intervention_complexity,
        r.expected_delay,
        r.resource_conflict_penalty
    ]
```

---

## A5. Safety-Constrained Parameter Update Functions

### A5.1 ClipParameterDelta

```text
Function ClipParameterDelta(theta_old, theta_candidate, max_delta):
    theta_new = {}

    For each param in theta_candidate:
        old_value = theta_old[param]
        candidate_value = theta_candidate[param]
        delta = candidate_value - old_value
        clipped_delta = Clip(delta, -max_delta, max_delta)
        theta_new[param] = old_value + clipped_delta

    Return theta_new
```

### A5.2 EnforceParameterBounds

```text
PARAM_MIN_MAX = {
    "lambda_stability": [0.0, 10.0],
    "lambda_res": [0.0, 10.0],
    "pi_data": [0.0, 10.0],
    "mu_execution": [0.0, 10.0],
    "nu_resource": [0.0, 10.0],
    "omega_safety": [1.0, 100.0],
    "eta_intervention": [0.0, 10.0],
    "xi_human": [0.0, 10.0],
    "theta_trigger": [0.0, 1.0],
    "theta_ood": [0.0, 1.0]
}

Function EnforceParameterBounds(theta):
    For each param in theta:
        If param in PARAM_MIN_MAX:
            lower = PARAM_MIN_MAX[param][0]
            upper = PARAM_MIN_MAX[param][1]
            theta[param] = Clip(theta[param], lower, upper)

    Return theta
```

### A5.3 LockHardSafetyConstraints

```text
Function LockHardSafetyConstraints(theta, locked_safety_config):
    # Hard safety constraints must not be weakened by human feedback learning.
    # Paper 5 may increase soft safety penalties, but cannot reduce hard-safety rules.

    For each key in locked_safety_config:
        theta[key] = locked_safety_config[key]

    If theta["omega_safety"] < locked_safety_config["min_omega_safety"]:
        theta["omega_safety"] = locked_safety_config["min_omega_safety"]

    Return theta
```

### A5.4 ProposeConstrainedUpdate — Full Version

> Đồng bộ ký hiệu (`pi_data` thay `mu_data`) và step-size (mục 23) với bản MVP ở mục 17.5 — hai bản trước đây khác nhau về cả tên tham số lẫn hệ số cập nhật.

```text
Function ProposeConstrainedUpdate(theta_old, preference_state, locked_safety_config):
    theta_candidate = copy(theta_old)

    theta_candidate["omega_safety"]     += safety_weight_update     * preference_state.safety_preference
    theta_candidate["nu_resource"]      += resource_weight_update   * preference_state.resource_preference
    theta_candidate["lambda_stability"] += stability_weight_update  * preference_state.low_churn_preference
    theta_candidate["lambda_res"]       += stability_weight_update  * preference_state.low_churn_preference
    theta_candidate["pi_data"]          += data_weight_update        * preference_state.low_confidence_aversion
    theta_candidate["eta_intervention"] += resource_weight_update   * preference_state.low_complexity_preference
    theta_candidate["xi_human"]         += human_weight_update

    theta_candidate = ClipParameterDelta(theta_old, theta_candidate, max_delta=0.10)
    theta_candidate = EnforceParameterBounds(theta_candidate)
    theta_candidate = LockHardSafetyConstraints(theta_candidate, locked_safety_config)

    Return theta_candidate
```

---

## A6. Digital Twin Replay and Deployment Gate Details

### A6.1 ComparePolicyMetrics

```text
Function ComparePolicyMetrics(old_metrics, new_metrics):
    result = {}

    For each metric in old_metrics.keys():
        old_value = old_metrics[metric]
        new_value = new_metrics[metric]

        result[metric + "_old"] = old_value
        result[metric + "_new"] = new_value
        result[metric + "_delta"] = new_value - old_value
        result[metric + "_relative"] = (new_value - old_value) / max(1.0, abs(old_value))

    Return result
```

### A6.2 PreliminaryGateStatus — ĐÃ GỘP VÀO EvaluateDeploymentGate

> **Đã bỏ, không dùng riêng nữa.** Bản trước định nghĩa gate logic thứ hai với tên threshold khác (`max_runtime_increase` thay vì `max_timeout_rate`, thiếu `max_cost_increase`...) và được gọi thiếu tham số ở mục 17.6 cũ. Toàn bộ logic (kể cả check `unsafe_recommendation_rate` và outcome `NO_MEANINGFUL_IMPROVEMENT`) đã được gộp vào **`EvaluateDeploymentGate`, mục 17.7** — dùng hàm đó làm nguồn quyết định gate duy nhất.

### A6.3 DigitalTwinReplay — Full Version

> Sửa `DigitalTwinReplayResult` khớp đúng schema mục 14.5 (field `policy_id` số ít + `port_id` + `scenario_set_id`, bản trước dùng `policy_old`/`policy_candidate` và thiếu 2 field kia). `gate_status` lấy từ `EvaluateDeploymentGate` (mục 17.7), không dùng `PreliminaryGateStatus` nữa.

```text
Function DigitalTwinReplay(DT, pi_old, pi_candidate, cfg, G):
    scenarios = DT.LoadReplayScenarios(cfg.port_id)

    old_metrics = []
    new_metrics = []

    For each scenario s in scenarios:
        result_old = DT.RunPolicy(pi_old, s, cfg, G)
        result_new = DT.RunPolicy(pi_candidate, s, cfg, G)

        old_metrics.append(result_old.metrics)
        new_metrics.append(result_new.metrics)

    old_avg = AverageMetrics(old_metrics)
    new_avg = AverageMetrics(new_metrics)

    comparison = ComparePolicyMetrics(old_avg, new_avg)

    replay_result = DigitalTwinReplayResult(
        replay_id = GenerateID("REPLAY"),
        policy_id = pi_candidate.policy_id,
        port_id = cfg.port_id,
        scenario_set_id = DT.CurrentScenarioSetId(cfg.port_id),
        num_scenarios = len(scenarios),
        metrics = new_avg,
        comparison_to_old_policy = comparison,
        gate_status = None
    )
    replay_result.gate_status = EvaluateDeploymentGate(replay_result, DT.thresholds).decision

    Return replay_result
```

### A6.4 Replay Scenario Types

```text
DigitalTwinReplay scenarios must include:
1. Normal operation scenarios.
2. High retrieval-disruption scenarios.
3. Execution-failure scenarios.
4. Resource-bottleneck scenarios.
5. Low-confidence data scenarios.
6. Safety-conflict stress scenarios.
7. High-feedback-noise scenarios.
8. Cross-port target scenarios if Paper 4 deployment mode is active.
```

---

## A7. Synthetic Operator and Feedback Generation

### A7.1 SyntheticOperatorModel

```text
Function SyntheticOperatorModel(recommendation, operator_profile, state):
    rejection_score = 0.0

    If recommendation.has_safety_issue:
        rejection_score += operator_profile.preference_weights.safety_weight * 1.0

    If recommendation.churn > operator_profile.thresholds.churn_threshold:
        rejection_score += operator_profile.preference_weights.stability_weight * (
            recommendation.churn / max(0.001, operator_profile.thresholds.churn_threshold)
        )

    If recommendation.crane_travel > operator_profile.thresholds.travel_threshold:
        rejection_score += operator_profile.preference_weights.resource_weight * (
            recommendation.crane_travel / max(0.001, operator_profile.thresholds.travel_threshold)
        )

    If state.confidence < operator_profile.thresholds.confidence_threshold:
        rejection_score += operator_profile.preference_weights.data_aversion * 0.5

    If recommendation.intervention_complexity > operator_profile.thresholds.complexity_threshold:
        rejection_score += operator_profile.preference_weights.intervention_complexity_weight * 0.5

    threshold = 0.5 + RandomUniform(-operator_profile.noise_level, operator_profile.noise_level)

    If RandomUniform(0, 1) > operator_profile.consistency:
        Return RandomFeedbackType()

    If rejection_score > threshold:
        Return SelectFeedbackTypeFromDominantReason(rejection_score, recommendation, operator_profile)
    Else:
        Return "ACCEPT"
```

### A7.2 SelectFeedbackTypeFromDominantReason

```text
Function SelectFeedbackTypeFromDominantReason(score, recommendation, operator_profile):
    If recommendation.has_safety_issue:
        Return "MARK_UNSAFE"

    If recommendation.churn > operator_profile.thresholds.churn_threshold:
        Return "MODIFY_SEQUENCE"

    If recommendation.crane_travel > operator_profile.thresholds.travel_threshold:
        Return "MODIFY_CRANE"

    If recommendation.state_confidence < operator_profile.thresholds.confidence_threshold:
        Return "DATA_CORRECTION"

    If recommendation.intervention_complexity > operator_profile.thresholds.complexity_threshold:
        Return "MARK_IMPRACTICAL"

    Return "REJECT"
```

### A7.3 GenerateSyntheticFeedback

```text
Function GenerateSyntheticFeedback(recommendations, operator_profile, state_sequence):
    feedback_batch = []

    For i from 1 to len(recommendations):
        rec = recommendations[i]
        state = state_sequence[i]

        feedback_type = SyntheticOperatorModel(rec, operator_profile, state)

        feedback = OperatorFeedback()
        feedback.feedback_id = GenerateID("FB")
        feedback.recommendation_id = rec.recommendation_id
        feedback.plan_id = rec.plan_id
        feedback.action_id = rec.primary_action_id
        feedback.feedback_type = feedback_type
        feedback.operator_id = operator_profile.profile_id
        feedback.operator_confidence = operator_profile.consistency
        feedback.timestamp = state.timestamp
        feedback.reason_code = InferReasonCode(feedback_type)
        feedback.operator_action = GenerateOperatorAction(feedback_type, rec, state)

        feedback = AddFeedbackNoise(feedback, operator_profile.noise_level)
        feedback_batch.append(feedback)

    Return feedback_batch
```

### A7.4 AddFeedbackNoise

```text
Function AddFeedbackNoise(feedback, noise_level):
    If RandomUniform(0, 1) < noise_level:
        feedback.feedback_type = RandomOtherType(feedback.feedback_type)

    If RandomUniform(0, 1) < noise_level * 0.5:
        feedback.reason_code = RandomReasonCode()

    If RandomUniform(0, 1) < noise_level * 0.5:
        feedback.operator_confidence = Max(0.0, feedback.operator_confidence - RandomUniform(0.1, 0.4))

    Return feedback
```

---

## A8. Timeout Protocol — Detailed Version

| Operation | Timeout | Mode | Rationale |
|---|---:|---|---|
| InterpretFeedback batch | 10s per 1,000 feedback | Offline/nearline | Simple rule-based classification |
| IsInconsistentFeedback batch | 5s per 1,000 feedback | Offline/nearline | Lightweight validation |
| EstimateHumanPreference | 30s | Offline batch | Aggregation + rejection model |
| FitHeuristicRejectionModel | 10s | Offline batch | Rule-based update |
| FitLogisticRejectionModel | 120s | Offline batch | Only used when enough samples exist |
| ProposeConstrainedUpdate | 5s | Offline batch | Lightweight parameter update |
| DigitalTwinReplay small | 5 min | Offline | Small replay set |
| DigitalTwinReplay medium | 20 min | Offline | Standard replay set |
| DigitalTwinReplay large | 60 min | Offline | Stress and cross-port replay |
| DeploymentGate evaluation | 10s | Offline/nearline | Metric comparison only |
| Rollback monitor check | 5s per monitoring window | Online monitoring | Must be lightweight |
| Online recommendation | Same as Paper 4 | Online | Feedback learning must not affect online latency |

Important production rule:

> Paper 5 does not perform unconstrained online learning. Feedback learning, parameter update, and Digital Twin replay happen offline or in shadow mode. The online decision path keeps the same latency requirement as Paper 4.

---

## A9. Rollback Logic

### A9.1 MonitorAndRollback — Full Version

```text
Function MonitorAndRollback(policy_current, policy_previous, monitoring_metrics, thresholds):
    If monitoring_metrics.hard_safety_violations > thresholds.max_hard_safety_violations:
        event = CreateRollbackEvent(
            policy_current,
            policy_previous,
            trigger="HARD_SAFETY_VIOLATION",
            metrics=monitoring_metrics
        )
        DeployPolicy(policy_previous)
        NotifyOperator(event)
        Return event

    If monitoring_metrics.operator_rejection_rate > thresholds.max_rejection_rate:
        event = CreateRollbackEvent(
            policy_current,
            policy_previous,
            trigger="HIGH_OPERATOR_REJECTION_RATE",
            metrics=monitoring_metrics
        )
        DeployPolicy(policy_previous)
        NotifyOperator(event)
        Return event

    If monitoring_metrics.plan_churn > thresholds.max_plan_churn:
        event = CreateRollbackEvent(
            policy_current,
            policy_previous,
            trigger="EXCESSIVE_PLAN_CHURN",
            metrics=monitoring_metrics
        )
        DeployPolicy(policy_previous)
        NotifyOperator(event)
        Return event

    Return None
```

### A9.2 CreateRollbackEvent

```text
Function CreateRollbackEvent(policy_current, policy_previous, trigger, metrics):
    event = RollbackEvent()
    event.rollback_id = GenerateID("RB")
    event.timestamp = CurrentTime()
    event.policy_id = policy_current.policy_id
    event.rollback_policy_id = policy_previous.policy_id
    event.trigger = trigger
    event.details = {
        "metric_snapshot": metrics,
        "affected_actions": metrics.affected_actions,
        "first_violation_time": metrics.first_violation_time
    }
    event.operator_notified = False
    event.rollback_status = "CREATED"
    Return event
```

---

## A10. Final Code-Ready Checklist for Paper 5

| ID | Item | Status |
|---|---|---|
| C1 | OperatorFeedback schema | Ready |
| C2 | FeedbackInterpretation schema | Ready |
| C3 | HumanPreferenceState schema | Ready |
| C4 | PolicyUpdate schema | Ready |
| C5 | DigitalTwinReplayResult schema | Ready |
| C6 | DeploymentGateResult schema | Ready |
| C7 | SyntheticOperatorProfile schema | Ready |
| C8 | RollbackEvent schema | Ready |
| C9 | InterpretFeedback pseudocode | Ready |
| C10 | IsInconsistentFeedback pseudocode | Ready |
| C11 | FitOrUpdateRejectionModel pseudocode | Ready |
| C12 | FitLogisticRejectionModel pseudocode | Ready |
| C13 | ClipParameterDelta pseudocode | Ready |
| C14 | EnforceParameterBounds pseudocode | Ready |
| C15 | LockHardSafetyConstraints pseudocode | Ready |
| C16 | ComparePolicyMetrics pseudocode | Ready |
| C17 | PreliminaryGateStatus pseudocode | Ready |
| C18 | DigitalTwinReplay full pseudocode | Ready |
| C19 | SyntheticOperatorModel pseudocode | Ready |
| C20 | GenerateSyntheticFeedback pseudocode | Ready |
| C21 | AddFeedbackNoise pseudocode | Ready |
| C22 | Rollback monitor pseudocode | Ready |
| C23 | Timeout protocol detailed | Ready |
| C24 | MVP gate | Ready |
| C25 | Code reuse boundary from Paper 1–4 | Ready |

---

## A11. Updated Final Assessment

After this appendix, Paper 5 is no longer only a **research concept with architecture**. It reaches **ULTRA-FINAL CODE-READY** level because it now contains:

```text
1. Full missing Implementation Appendix.
2. Missing pseudocode for feedback consistency, parameter constraints, policy comparison, synthetic operator generation, noise injection, and rollback.
3. Additional schemas for SyntheticOperatorProfile, RollbackEvent, and FeedbackExample.
4. Detailed Digital Twin replay scenario protocol.
5. Detailed operation-level timeout protocol.
6. Clear safety-constrained offline learning rule.
7. Final code-ready checklist.
```

Final positioning:

> Paper 1 makes replanning stable. Paper 2 makes it robust. Paper 3 makes it strategic. Paper 4 makes it deployable across terminals. Paper 5 makes it human-adaptive by learning from operator feedback through safety-constrained digital-twin validation.

