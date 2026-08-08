# ĐỀ XUẤT PAPER 2 — IMPLEMENTATION-READY
# EA-SAR-CRP: Execution-Aware Stable Replanning for Container Relocation under Imperfect Operational Feedback

**Vai trò:** Paper 2 sau SAR-CRP Paper 1  
**Mục tiêu tài liệu:** Proposal nghiên cứu Q1 + Implementation Appendix để lập trình viên có thể bắt đầu code  
**Phiên bản:** Paper 2 revised after professor review  
**Ngôn ngữ:** Tiếng Việt  

---

# 0. Tóm tắt một câu

**Paper 1 makes replanning stable under evolving retrieval information. Paper 2 makes replanning robust under imperfect execution.**

Paper 2 không thay thế Paper 1. Paper 2 mở rộng Paper 1 bằng cách đưa vào:

```text
1. Execution feedback
2. State reliability
3. Safety-aware trigger
4. Rollback / fallback
5. Execution-aware repair
```

---

# 1. Vị trí của Paper 2 trong roadmap

## Paper 1

**Stable Adaptive Replanning for Container Relocation under Imperfect and Evolving Retrieval Information**

Paper 1 tập trung vào:

```text
retrieval information changes
→ event impact
→ trigger
→ freeze horizon
→ stability-aware repair
```

Paper 1 giả định:

```text
state tương đối đáng tin
execution feedback chưa phải trọng tâm
fallback đơn giản
safety constraints chỉ ở mức cơ bản
```

## Paper 2

**Execution-Aware Stable Replanning for Container Relocation under Imperfect Operational Feedback**

Paper 2 tập trung vào:

```text
execution delay
execution failure
state mismatch
stale data
operator rejection
unsafe action
rollback / fallback / safe hold
```

Paper 2 không nên đưa multi-crane scheduling vào. Multi-crane nên để Paper 3.

---

# 2. Quan hệ Paper 1 và Paper 2

| Thành phần | Paper 1 | Paper 2 |
|---|---|---|
| Trigger | Retrieval impact | Retrieval + execution + data reliability impact |
| State | Giả định tương đối đúng | Có confidence và stale state |
| Plan update | Retrieval-based repair | Execution-aware repair |
| Fallback | Keep old plan nếu invalid | Minimal Repair → Keep Old Plan → Safe Hold / Manual Review |
| Safety | Basic feasibility | Hard safety constraints + soft safety risk |
| Feedback | Chưa trọng tâm | Delay, failed action, mismatch, operator rejection |
| Codebase | SAR-CRP core | SAR-CRP core + execution modules |

---

# 3. Motivation

Trong thực tế, kế hoạch relocation không chỉ bị ảnh hưởng bởi retrieval information. Khi plan đi vào thực thi, hệ thống có thể nhận được các feedback sau:

```text
- action hoàn thành đúng kế hoạch
- action bị delay
- action failed
- destination stack đầy ngoài dự kiến
- container không ở vị trí hệ thống ghi nhận
- operator từ chối recommendation
- dữ liệu TOS/gate/crane bị trễ
- thông tin container location bị mâu thuẫn
```

Nếu một replanning system không xử lý execution feedback, nó có thể:

```text
- tiếp tục thực hiện plan sai
- replan dựa trên state không đáng tin
- tạo action unsafe
- đổi plan quá nhiều sau một lỗi nhỏ
- không rollback được khi plan mới không khả thi
```

Do đó Paper 2 giải quyết bài toán:

> **How to make stable CRP replanning robust to imperfect execution feedback and unreliable operational state.**

---

# 4. Research Gap

Các hướng CRP hiện có thường giả định:

```text
state đúng
action thực hiện như kế hoạch
feedback từ execution không phải một nguồn bất định chính
```

Ngay cả dynamic/stochastic CRP cũng thường tập trung vào:

```text
retrieval order uncertainty
truck arrival uncertainty
real-time reoptimization
```

Nhưng trong deployment thật, có một gap khác:

> **Plan execution itself is uncertain.**

Một plan tốt trên mô phỏng có thể bị phá vỡ bởi:

```text
crane delay
failed move
stale location
operator override
inconsistent state
```

Paper 2 đóng góp bằng cách đưa **execution feedback + state reliability + safety-aware fallback** vào stable replanning.

> **Cần bổ sung trước khi submit.** Mục này hiện chưa trích dẫn cụ thể literature nào cho "execution uncertainty trong scheduling/planning" — chỉ tự tham chiếu Paper 1 và CRP_RL (Shin et al. 2026, xem cảnh báo xác minh ở mục 3 Paper 1, vẫn áp dụng cho B2 ở mục 43). Trước khi viết Related Work thật, cần tìm và trích dẫn literature thuộc các hướng: robust/reactive scheduling dưới execution uncertainty, fault-tolerant planning, rollback/recovery trong hệ thống production, và (nếu có) human-in-the-loop/operator-trust trong recommendation systems. Không để Research Gap chỉ dựa vào lập luận nội bộ mà không có bằng chứng từ literature.

---

# 5. Research Questions

## RQ1 — Execution Feedback

> How should a CRP replanning system update its plan when execution feedback indicates delay, failure, or mismatch between planned and actual operations?

## RQ2 — State Reliability

> How can replanning decisions account for stale, missing, or inconsistent operational state information?

## RQ3 — Rollback/Fallback

> When should the system repair the current plan, rollback to the previous plan, keep the old plan, or enter safe hold/manual review?

## RQ4 — Safety-Aware Stable Replanning

> Can execution-aware stable replanning reduce failed/unsafe actions while maintaining operational efficiency and plan stability?

---

# 6. Scope của Paper 2

## Trong scope

```text
- Execution feedback events
- State confidence/reliability
- Execution impact estimator
- Safety-aware trigger
- Rollback/fallback manager
- Execution-aware repair planner
- Candidate evaluation with execution and safety cost
```

## Ngoài scope

```text
- Multi-crane scheduling
- Crane assignment optimization
- Truck appointment optimization
- Full TOS integration
- Human-subject user study bắt buộc
- Real terminal deployment
```

Giả định về crane:

> We assume a single-crane abstraction or that crane scheduling is handled separately. This paper focuses on relocation-plan recovery and safety-aware replanning, not crane assignment.

---

# 7. High-level Architecture

```text
Paper 1 SAR-CRP Core
        │
        ▼
Old Plan P_old
        │
        ▼
Execution starts
        │
        ▼
Execution Feedback Collector
        │
        ▼
State Reliability Estimator
        │
        ▼
Execution Impact Estimator
        │
        ▼
Safety-Aware Replanning Trigger
        │
        ├── no trigger ──► Continue / Keep Old Plan
        │
        ▼
Rollback/Fallback Manager
        │
        ▼
Execution-Aware Repair Planner
        │
        ▼
Candidate Evaluator and Selector
        │
        ▼
Safety Validator
        │
        ▼
Updated Plan / Minimal Repair / Keep Old Plan / Safe Hold
```

---

# 8. Module Overview

## M1. Execution Feedback Collector

Nhận feedback từ execution simulator hoặc operational logs.

Input:

```text
executed actions
planned actions
action status
timestamps
failure reasons
operator responses
```

Output:

```text
ExecutionFeedback list
```

---

## M2. State Reliability Estimator

Tính độ tin cậy của state hiện tại.

Input:

```text
state S_t
last_update_time
source type
conflicting observations
execution feedback
```

Output:

```text
container_confidence
stack_confidence
global_state_confidence
stale flags
mismatch flags
```

---

## M3. Execution Impact Estimator

Đo execution feedback có đáng để replan không.

Input:

```text
P_old
ExecutionFeedback
StateReliability
SafetyConstraint violations
```

Output:

```text
I_exec
I_delay
I_failure
I_mismatch
I_operator
I_safety
```

---

## M4. Safety-Aware Replanning Trigger

Quyết định có trigger replanning không.

Input:

```text
I_retrieval từ Paper 1
I_exec
Conf(S_t)
J(P_old)
```

Output:

```text
TRIGGER_REPLAN
KEEP_OLD_PLAN
SAFE_HOLD
MANUAL_REVIEW
```

---

## M5. Rollback/Fallback Manager

Quyết định recovery mode.

Hierarchy:

```text
Candidate Plan
    ↓ invalid / timeout
Minimal Repair
    ↓ failed
Keep Old Plan
    ↓ infeasible
Safe Hold / Manual Review
```

---

## M6. Execution-Aware Repair Planner

Sinh candidate plan có xét feedback thực thi.

Candidate types:

```text
C0 Keep Old Plan
C1 Minimal Safety Repair
C2 Execution-Aware Local Repair
C3 Paper-1 SAR Repair
C4 Full Reoptimization
```

---

## M7. Candidate Evaluator and Selector

Chọn plan tốt nhất theo objective mở rộng.

---

# 9. Objective Function

Paper 1:

\[
J_1(P)=C_{op}(P)+\lambda D(P,P^{old})+\mu C_{data}(P)
\]

Paper 2:

\[
J_2(P)=C_{op}(P)+\lambda D(P,P^{old})+\mu C_{data}(P)+\nu C_{exec}(P)+\omega C_{safety}(P)
\]

Trong đó:

| Thành phần | Ý nghĩa |
|---|---|
| \(C_{op}\) | relocation, retrieval delay, infeasibility |
| \(D\) | plan instability |
| \(C_{data}\) | penalty do state/data không đáng tin |
| \(C_{exec}\) | penalty do execution delay/failure/mismatch |
| \(C_{safety}\) | hard/soft safety violation |

---

# 10. Công thức cụ thể cho C_exec

Execution cost:

\[
C_{exec}(P)=
\sum_{a\in Actions(P)}
\left[
penalty_{delay}(a)+penalty_{failure}(a)+penalty_{mismatch}(a)
\right]
\]

## 10.1 Delay penalty

Nếu action \(a\) bị delay:

\[
penalty_{delay}(a)=
\min\left(1,\frac{delay\_steps(a)}{d_{max}}\right)
\]

Nếu không delay:

\[
penalty_{delay}(a)=0
\]

## 10.2 Failure penalty

\[
penalty_{failure}(a)=
\begin{cases}
1, & \text{if action } a \text{ failed}\\
0, & \text{otherwise}
\end{cases}
\]

## 10.3 Mismatch penalty

Nếu action phụ thuộc vào container hoặc stack có low confidence:

\[
penalty_{mismatch}(a)=1-Conf(entity(a))
\]

Trong đó:

```text
entity(a) = container hoặc stack liên quan đến action a
```

---

# 11. Công thức cụ thể cho C_safety

Safety cost:

\[
C_{safety}(P)=
\begin{cases}
\infty, & \text{if any hard safety constraint is violated}\\
\sum_{a\in Actions(P)} penalty_{soft\_safety}(a), & \text{otherwise}
\end{cases}
\]

## Hard safety constraints

Ví dụ:

```text
- Không xếp vượt max_tier
- Không đặt container vào stack đầy
- Không move container không tồn tại trong state
- Không move container đang locked/hold
- Không đặt hazardous container sai rule
- Không sửa action đã executed
```

## Soft safety violations

Ví dụ:

```text
- action dựa trên container confidence thấp
- destination stack có stale data
- action gần vùng vừa có failure
- operator từng reject action tương tự
```

Soft safety penalty:

\[
penalty_{soft\_safety}(a)=
\sum_{r\in SoftRules} weight(r)\cdot violation(a,r)
\]

---

# 12. Execution Impact Estimator

Execution impact:

\[
I_{exec}=v_1I_{delay}+v_2I_{failure}+v_3I_{mismatch}+v_4I_{operator}+v_5I_{safety}
\]

Default:

```text
v1 = 0.25
v2 = 0.30
v3 = 0.20
v4 = 0.10
v5 = 0.15
```

## 12.1 Delay impact

\[
I_{delay}=\min\left(1,\frac{\sum_{a\in DelayedActions}delay\_steps(a)}{d_{max}\cdot |DelayedActions|}\right)
\]

Nếu không có delayed action:

\[
I_{delay}=0
\]

## 12.2 Failure impact

\[
I_{failure}=\frac{|FailedActions|}{\max(1,|ExecutedActions|)}
\]

## 12.3 Mismatch impact

\[
I_{mismatch}=1-Conf(S_t)
\]

## 12.4 Operator impact

\[
I_{operator}=\frac{|RejectedActions|}{\max(1,|ProposedActions|)}
\]

## 12.5 Safety impact

\[
I_{safety}=\mathbf{1}[\exists a\in P^{old}: unsafe(a,S_t)]
\]

---

# 13. State Reliability Estimator

## 13.1 Container confidence

\[
Conf(c)=\exp(-\kappa \cdot age(c))\cdot source\_factor(c)
\]

Trong đó:

```text
age(c) = current_time - last_update_time(c)
```

## 13.2 Stack confidence

\[
Conf(stack)=\min_{c\in stack} Conf(c)
\]

Nếu stack rỗng:

\[
Conf(stack)=1
\]

## 13.3 Global state confidence

\[
Conf(S_t)=
\min\left(1,
\frac{1}{|C|}\sum_{c\in C} Conf(c)
\right)
\]

Có thể mở rộng bằng source factor toàn cục:

\[
Conf(S_t)=
\min\left(1,
\frac{1}{|C|}\sum_{c\in C} Conf(c)\cdot source\_factor_{global}
\right)
\]

## 13.4 Source factor mặc định

| Nguồn dữ liệu | source_factor |
|---|---:|
| TOS | 0.90 |
| Crane telemetry | 0.95 |
| OCR / camera | 0.80 |
| Manual entry | 0.50 |
| Synthetic simulator | 1.00 |

---

# 14. Safety-Aware Trigger

Paper 2 dùng trigger kết hợp retrieval impact, execution impact và data reliability.

\[
TriggerScore=\alpha_{trig} I_{retrieval}+\beta_{trig} I_{exec}+\gamma_{trig}(1-Conf(S_t))
\]

(Ký hiệu `α_trig, β_trig, γ_trig` — không dùng lại `α, β, γ` trơn vì ký hiệu đó đã có nghĩa khác trong `C_op` của Paper 1, mục 24 tái sử dụng nguyên `C_op` này.)

Default:

```text
alpha_trig = 0.4
beta_trig  = 0.4
gamma_trig = 0.2
```

Trigger nếu:

\[
TriggerScore \ge \theta_{trigger}
\]

và gain đủ lớn:

\[
J(P^{old})-J(P^{best}) > \tau
\]

Default:

```text
theta_trigger = 0.30
tau = 0.01 * J(P_old)
```

Fast-path (bỏ qua điều kiện gain, trigger ngay không cần đợi tính P_best):

```text
Nếu I_exec >= theta_exec: trigger ngay (execution impact tự nó đã đủ nghiêm trọng,
    không cần chờ TriggerScore tổng hợp — xem mục 16.1 bước 4).
```

Nếu có hard safety violation trong plan cũ:

```text
trigger immediately
```

Nếu Conf(S_t) quá thấp:

```text
route to Safe Hold / Manual Review
```

---

# 15. Data Schema — Implementation Appendix

## 15.1 YardState

```json
{
  "time": 12,
  "stacks": [
    {
      "id": "S1",
      "containers": ["C5", "C2", "C9"],
      "max_tier": 5,
      "last_update_time": 11,
      "source": "simulator"
    },
    {
      "id": "S2",
      "containers": ["C1"],
      "max_tier": 5,
      "last_update_time": 12,
      "source": "simulator"
    }
  ],
  "containers": {
    "C1": {
      "id": "C1",
      "stack_id": "S2",
      "tier": 1,
      "status": "available",
      "hazardous": false,
      "locked": false,
      "last_update_time": 12,
      "source": "simulator"
    }
  },
  "retrieval_queue": ["C1", "C2", "C3", "C4"],
  "pickup_prob": {
    "C1": 0.90,
    "C2": 0.70
  }
}
```

---

## 15.2 PlanAction

```json
{
  "action_id": "A12",
  "type": "RELOCATE",
  "container": "C9",
  "source_stack": "S1",
  "dest_stack": "S3",
  "planned_step": 14,
  "commit_status": "planned",
  "status": "pending",
  "created_by": "SAR_CRP_P1",
  "last_update_time": 12
}
```

Allowed `type`:

```text
RELOCATE
RETRIEVE
WAIT       # tương đương NOOP bên Paper 1, đổi tên cho rõ nghĩa hơn trong ngữ cảnh execution-aware
SAFE_HOLD  # mới ở Paper 2
```

Allowed `commit_status`:

```text
executed
in_progress   # mới ở Paper 2
committed
planned
repairable    # mới ở Paper 2
cancelled     # giữ lại từ Paper 1 (mục 37.2) — action đã hủy do no-show/obsolete
```

Lưu ý: Paper 2 **mở rộng** (superset) enum `type`/`commit_status` của Paper 1 (mục 24: "Plan / Action schema — Yes, reused"), không thay thế. Coder áp dụng Plan schema Paper 1 sẵn có phải bổ sung thêm `WAIT, SAFE_HOLD` vào `type` và `in_progress, repairable` vào `commit_status`, giữ nguyên `cancelled` (bản trước liệt kê thiếu `cancelled`, dễ hiểu nhầm là đã bỏ).

---

## 15.3 Plan

```json
{
  "plan_id": "P_old_001",
  "created_time": 10,
  "source": "Paper1_SAR_CRP",
  "actions": [
    {
      "action_id": "A1",
      "type": "RELOCATE",
      "container": "C9",
      "source_stack": "S1",
      "dest_stack": "S3",
      "planned_step": 11,
      "commit_status": "committed",
      "status": "pending"
    }
  ]
}
```

---

## 15.4 ExecutionFeedback

```json
{
  "feedback_id": "F001",
  "time": 13,
  "action_id": "A1",
  "type": "action_failed",
  "status": "failed",
  "delay_steps": 0,
  "reason": "destination_stack_full",
  "observed_container": "C9",
  "observed_stack": "S1",
  "confidence": 0.90,
  "source": "simulator"
}
```

Allowed feedback `type`:

```text
action_completed
action_delayed
action_failed
container_location_mismatch
operator_rejected
manual_override
state_update_delayed
unsafe_action_detected
```

Lưu ý: `destination_stack_full` **không phải** một `type` riêng — đó là một giá trị của trường `reason` khi `type = action_failed` (đúng như ví dụ JSON phía trên). Bản trước liệt kê nhầm `destination_stack_full` vào danh sách `type` hợp lệ — đã bỏ. Đã bổ sung `state_update_delayed` và `unsafe_action_detected` để khớp với taxonomy event chuẩn ở mục 39.1 (Execution Feedback Collector — M1 — phải thu thập được cả hai loại tín hiệu này).

---

## 15.5 StateReliability

```json
{
  "time": 13,
  "global_confidence": 0.82,
  "container_confidence": {
    "C1": 0.95,
    "C2": 0.73
  },
  "stack_confidence": {
    "S1": 0.73,
    "S2": 0.95
  },
  "stale_entities": ["C2"],
  "mismatch_entities": ["S1"],
  "source_summary": {
    "simulator": 1.0,
    "manual": 0.5
  }
}
```

---

## 15.6 SafetyConstraint

```json
{
  "constraint_id": "SAFE_001",
  "type": "hard",
  "description": "Cannot place container on stack exceeding max_tier",
  "check": "dest_stack.height + 1 <= dest_stack.max_tier",
  "penalty": "infinity"
}
```

```json
{
  "constraint_id": "SAFE_002",
  "type": "hard",
  "description": "Cannot move locked container",
  "check": "container.locked == false",
  "penalty": "infinity"
}
```

```json
{
  "constraint_id": "SAFE_003",
  "type": "soft",
  "description": "Avoid actions depending on low-confidence location",
  "check": "container_confidence >= 0.6",
  "penalty": 0.5
}
```

---

# 16. Pseudocode

## 16.1 Main Algorithm

```text
Algorithm EA-SAR-CRP

Input:
    YardState S_t
    Old plan P_old
    Retrieval impact I_retrieval from Paper 1
    Execution feedback list F_t
    SafetyRules (danh sách SafetyConstraint, mục 15.6)
    Parameters Θ

1. R_t = EstimateStateReliability(S_t, F_t)
2. I_exec = EstimateExecutionImpact(P_old, F_t, R_t, SafetyRules)
3. trigger_score = alpha_trig * I_retrieval + beta_trig * I_exec + gamma_trig * (1 - Conf(S_t))

4. if HasHardSafetyViolation(P_old, S_t, SafetyRules):
       mode = TRIGGER_REPLAN
   else if Conf(S_t) < θ_conf_min:
       return SAFE_HOLD_MANUAL_REVIEW
   else if I_exec >= θ_exec:
       mode = TRIGGER_REPLAN                 # fast-path: execution impact riêng đã đủ nghiêm trọng
   else if trigger_score < θ_trigger:
       return KEEP_OLD_PLAN

5. Generate candidates:
       C0 = KeepOldPlan(P_old)
       C1 = MinimalSafetyRepair(P_old, S_t, SafetyRules)
       C2 = ExecutionAwareLocalRepair(P_old, S_t, F_t, SafetyRules)
       C3 = Paper1SARRepair(P_old, S_t)
       C4 = FullReoptimization(S_t)

6. For each candidate P in candidates:
       if Timeout(P): discard or fallback
       if HardSafetyViolation(P): discard
       score(P) = C_op(P) + λD(P,P_old) + μC_data(P) + νC_exec(P) + ωC_safety(P)

7. P_best = argmin score(P)

8. if score(P_old) - score(P_best) <= τ:
       return KEEP_OLD_PLAN
   else:
       return UPDATE_PLAN(P_best)

9. If no valid candidate:
       return FALLBACK_HIERARCHY
```

---

## 16.2 EstimateStateReliability

```text
Function EstimateStateReliability(S_t, F_t):

1. For each container c:
       age = S_t.time - c.last_update_time
       sf = SourceFactor(c.source)
       conf[c] = exp(-κ * age) * sf

2. For each feedback f in F_t:
       if f.type == container_location_mismatch:
           conf[f.observed_container] *= mismatch_penalty

3. For each stack s:
       if s.containers is empty:
           stack_conf[s] = 1
       else:
           stack_conf[s] = min(conf[c] for c in s.containers)

4. global_conf = average(conf[c] for all containers)

5. return StateReliability(global_conf, conf, stack_conf, stale_entities, mismatch_entities)
```

---

## 16.3 EstimateExecutionImpact

```text
Function EstimateExecutionImpact(P_old, F_t, R_t, SafetyRules):

1. delayed = feedback where type == action_delayed
2. failed = feedback where type == action_failed
3. rejected = feedback where type == operator_rejected
4. executed = feedback where type in {action_completed, action_delayed, action_failed}

5. I_delay = min(1, sum(delay_steps)/max(1, d_max * len(delayed)))
6. I_failure = len(failed) / max(1, len(executed))
7. I_mismatch = 1 - R_t.global_confidence
8. I_operator = len(rejected) / max(1, number_of_proposed_actions)
9. I_safety = 1 if any action in P_old violates hard safety else 0

10. I_exec = v1*I_delay + v2*I_failure + v3*I_mismatch + v4*I_operator + v5*I_safety

11. return I_exec
```

---

## 16.4 MinimalSafetyRepair

```text
Function MinimalSafetyRepair(P_old, S_t, SafetyRules):

1. P = copy(P_old)
2. For each action a in P:
       if a.status == executed:
           continue
       if violates hard safety:
           if a.type == RELOCATE:
               find nearest valid destination stack
               if found:
                   update destination
               else:
                   remove action or mark SAFE_HOLD
           else:
               mark action for manual review
3. Return P
```

---

## 16.5 ExecutionAwareLocalRepair

`Score(P)` trong pseudocode dưới đây là `score(P)` đã định nghĩa ở mục 16.1 bước 6 (`C_op(P) + λD(P,P_old) + μC_data(P) + νC_exec(P) + ωC_safety(P)`, tức `J_2(P)` ở mục 9) — không phải một hàm điểm số khác.

Neighborhood operations:

```text
N1: replace destination stack for failed relocation
N2: remove obsolete action after failure/mismatch
N3: insert safe relocation before failed retrieval
N4: swap two repairable actions outside committed prefix
N5: convert risky action into WAIT or SAFE_HOLD
```

Pseudocode:

```text
Function ExecutionAwareLocalRepair(P_old, S_t, F_t, SafetyRules):

1. P_current = MinimalSafetyRepair(P_old)
2. best = P_current
3. best_score = Score(best)

4. for t in 1..T:
       neighbors = GenerateNeighbors(P_current, N1..N5, max_neighbors=M)
       valid_neighbors = []

       for P in neighbors:
           if not violates hard safety:
               valid_neighbors.append(P)

       if valid_neighbors is empty:
           break

       P_candidate = best plan among valid_neighbors by Score(P)

       if Score(P_candidate) < best_score:
           best = P_candidate
           P_current = P_candidate
           best_score = Score(P_candidate)
       else if random() < epsilon:
           P_current = random valid neighbor

       if runtime exceeds timeout:
           break

5. return best
```

---

# 17. Operator Interaction

Khi operator reject một recommendation:

```text
1. Record rejection reason
2. Store categorical reason + free text
3. Mark candidate as rejected
4. Try next-best safe candidate
5. If multiple rejections occur, route to manual review
6. Optionally adjust trigger threshold or action penalty in future calibration
```

Rejection schema:

```json
{
  "time": 18,
  "recommendation_id": "R102",
  "operator_action": "reject",
  "reason_code": "unsafe_in_practice",
  "free_text": "Stack S4 is blocked by maintenance equipment",
  "confidence": 1.0
}
```

---

# 18. Baseline Mapping

> Bảng chi tiết hơn (kèm cột "Reference/inspiration" và mô tả đầy đủ) nằm ở **mục 43 — Baseline Clarification**, không lặp lại nội dung ở đây nữa — dùng mục 43 làm nguồn duy nhất. Tóm tắt nhanh 6 baseline: B1 Paper-1 SAR-CRP, B2 Full Reoptimization, B3 Reactive Repair, B4 Reliability-Agnostic Repair, B5 Minimal Repair, B6 EA-SAR-CRP (proposed).

Nếu không implement B2 bằng CRP_RL trực tiếp, có thể thay bằng solver baseline của Paper 1, nhưng phải ghi rõ.

---

# 19. Dataset / Benchmark Paper 2

Paper 2 dùng lại benchmark Paper 1 và inject thêm execution/data events.

## 19.1 Input từ Paper 1

```text
initial yard state
initial retrieval queue
P_old generated by SAR-CRP Paper 1
retrieval event stream
```

## 19.2 Execution events mới

> Danh sách event type, xác suất sinh event và severity range **đã chuyển hẳn về mục 39** (Execution Event Generator — bản Ultra-Final) để tránh hai nguồn số liệu khác nhau. Mục 19.2/19.3 trước đây định nghĩa một bộ xác suất/severity khác với mục 39 — đã bỏ, không dùng nữa. Tên event chuẩn dùng `state_update_delayed` và `unsafe_action_detected` (khớp Event Schema mục 40), không dùng `stale_state`/`destination_stack_full` như event type độc lập (các trường hợp này được biểu diễn qua `metadata.reason` của `action_failed`, xem ví dụ mục 40).

Danh sách event type chuẩn (xem mục 39.1):

```text
action_delayed
action_failed
container_location_mismatch
operator_rejected
state_update_delayed
unsafe_action_detected
```

## 19.3 Event generation parameters

> Xem mục 39.2 (xác suất theo loại event) và mục 39.3 (severity range) — đây là nguồn duy nhất. `p_exec_event` tổng quát (xác suất một execution event bất kỳ xảy ra ở mỗi step) tương ứng với `execution_noise_level` ở mục 38.3 (low=0.05, medium=0.15, high=0.30 — không phải hằng số cố định 0.30 như bản cũ).

---

# 20. Default Parameters

> **Bảng này đã được hợp nhất vào mục 45 ("Updated Default Parameter Table") — dùng mục 45 làm nguồn duy nhất khi code.** Giữ bảng dưới đây chỉ để tham khảo ý nghĩa tham số; các giá trị default đã đồng bộ với mục 45 (không còn khác nhau giữa hai bảng).

| Tham số | Ý nghĩa | Default | Sensitivity / Range |
|---|---|---:|---|
| λ | Stability weight | 1.0 (same as Paper 1) | {0.5, 1.0, 2.0} |
| μ | Data cost weight | 0.5 (same as Paper 1) | {0, 0.5, 1.0} |
| ν | Execution cost weight | 1.0 | {0.5, 1.0, 2.0} |
| ω | Safety cost weight | 5.0 | {1.0, 5.0, 10.0} |
| κ | Confidence decay rate | 0.1 | {0.05, 0.1, 0.2} |
| d_max | Max delay steps | 10 | {5, 10, 15} |
| θ_exec | Execution impact threshold (immediate-trigger fast path, mục 14) | 0.25 | {0.15, 0.25, 0.35} |
| α_trig | Retrieval trigger weight (TriggerScore) | 0.4 | fixed initially |
| β_trig | Execution trigger weight (TriggerScore) | 0.4 | fixed initially |
| γ_trig | Data confidence trigger weight (TriggerScore) | 0.2 | fixed initially |
| θ_trigger | Trigger threshold | 0.30 | {0.20, 0.30, 0.40} |
| τ | Gain threshold | 0.01 × J(P_old) | {0.005, 0.01, 0.02} |
| T | Local search iterations | 100 | {50, 100, 200} |
| M | Max neighbors per iteration | 50 | {20, 50, 100} |
| epsilon | Exploration probability | 0.05 | {0, 0.05, 0.10} |
| θ_conf_min | minimum global confidence | 0.40 | {0.3, 0.4, 0.5} |

**Lưu ý ký hiệu:** `α_trig, β_trig, γ_trig` (trọng số của `TriggerScore`) được đổi tên từ `α, β, γ` để **không trùng** với `α, β, γ` của `C_op` bên Paper 1 (relocation/retrieval-delay/invalid-penalty weight, mục 11.4 Paper 1) — Paper 2 tái sử dụng nguyên `C_op` từ Paper 1 (mục 24), nên nếu giữ cùng tên biến, một codebase dùng chung sẽ có hai cấu hình `alpha/beta/gamma` khác nghĩa ghi đè lẫn nhau.

---

# 21. Experiments

> Đây là bản phác thảo ban đầu của 5 experiment. Bản đầy đủ với instance count, layout, metric cụ thể nằm ở **mục 44 — Updated Experimental Design** — dùng mục 44 làm nguồn duy nhất khi lên kế hoạch chạy thực nghiệm. Danh sách ablation ở Experiment 5 đã được hợp nhất, xem ghi chú ở mục tương ứng phía dưới.

## Experiment 1 — Basic execution feedback robustness

Compare:

```text
B1 Paper-1 SAR-CRP
B2 Full Reoptimization
B3 Reactive Repair
B6 EA-SAR-CRP
```

Scenarios:

```text
low / medium / high execution disruption
```

---

## Experiment 2 — Data reliability stress test

Scenarios:

```text
fresh state
stale state
container mismatch
low confidence state
```

Goal:

> Test whether state reliability reduces unsafe or bad replanning decisions.

---

## Experiment 3 — Fallback and safety test

Inject:

```text
destination stack full
locked container
invalid move
operator rejection
```

Measure:

```text
invalid recommendation rate
fallback rate
safe hold rate
recovery success
```

---

## Experiment 4 — Cross-layout validation

Use same protocol as Paper 1:

```text
Layout A: tune parameters
Layout B/C: evaluate without retuning
```

---

## Experiment 5 — Ablation

> Danh sách ablation đầy đủ (đã hợp nhất, không còn khác với mục 44) nằm ở **mục 44 — Experiment 5 — Ablation study**. Bản trước ở đây định nghĩa A1–A6 khác nội dung với mục 44 (vd. A1 ở đây là "no execution cost C_exec" nhưng A1 ở mục 44 là "No State Reliability") — đã bỏ để tránh hai bộ ablation khác nhau cùng đánh số A1–A6. Hai ablation "no operator rejection handling" và "no execution-aware local repair" từng có ở đây được giữ lại làm ablation phụ (optional) trong mục 44.

---

# 22. Metrics

## Operational metrics

```text
relocations
retrieval delay
failed actions
recovery time
infeasible actions
```

## Stability metrics

```text
changed actions
changed committed actions
plan churn
rollback count
```

## Reliability metrics

```text
state confidence
low-confidence decisions
stale-data decisions
confidence-weighted regret
```

## Safety metrics

```text
hard safety violation rate
soft safety penalty
invalid recommendation rate
safe hold rate
manual review rate
```

## Runtime metrics

```text
mean runtime
P95 runtime
timeout rate
fallback rate
```

Hardware reporting:

```text
CPU model
RAM
GPU/no GPU
operating system
Python version
```

---

# 23. Walkthrough Example

Initial plan:

```text
A1: RELOCATE C9 S1 → S3, committed
A2: RETRIEVE C1, planned
A3: RELOCATE C7 S2 → S4, planned
A4: RETRIEVE C2, planned
```

Execution feedback:

```text
F1: A1 failed because destination_stack_full(S3)
F2: S3 last update age = 6 steps
F3: operator rejected previous action using S3
```

State reliability:

```text
Conf(S3) = exp(-0.1 * 6) * 1.0 = 0.55
Conf(S_t) = 0.78
```

Execution impact:

```text
I_delay = 0
I_failure = 1 / 1 = 1
I_mismatch = 1 - 0.78 = 0.22
I_operator = 1 / 1 = 1
I_safety = 1 because destination stack full affects old plan
```

Trigger:

```text
TriggerScore = 0.4 * I_retrieval + 0.4 * I_exec + 0.2 * (1 - Conf(S_t))
```

If TriggerScore > 0.30, system triggers repair.

Candidate generation:

```text
C0: Keep old plan → invalid because S3 full
C1: Minimal repair → replace S3 with nearest valid stack S5
C2: Local repair → move C9 to S5 and reorder A2/A3 if feasible
C3: Paper-1 SAR repair
C4: Full reoptimization
```

Final decision:

```text
Choose C1 or C2 if it has lower J2(P), no hard safety violation, and gain > τ.
If all candidates invalid → SAFE_HOLD / MANUAL_REVIEW.
```

---

# 24. Code Reuse Strategy

Paper 2 codebase should be:

```text
Paper 2 codebase = Paper 1 SAR-CRP codebase + execution feedback modules
```

Reuse from Paper 1:

```text
YardState schema
Plan schema
Paper-1 Impact Estimator
Stability cost D(P, P_old)
Operational cost C_op
Data cost C_data
Local Search framework
CRP_RL wrapper
Benchmark generator base
Baseline runner
Metrics logger
```

New in Paper 2:

```text
ExecutionFeedback schema
StateReliability estimator
ExecutionImpact estimator
SafetyConstraint schema
Safety-aware trigger
Fallback/Rollback manager
Execution-aware repair operators
Operator interaction logger
Execution event generator
```

---

# 25. Implementation Order

## Phase 0 — Reuse Paper 1

```text
Load Paper 1 SAR-CRP code
Run existing benchmark
Verify old baselines still pass
```

## Phase 1 — Add execution feedback schema/generator

```text
implement ExecutionFeedback
implement execution event injection
log failed/delayed/mismatch events
```

## Phase 2 — Add reliability estimator

```text
container confidence
stack confidence
global confidence
stale/mismatch flags
```

## Phase 3 — Add execution impact and trigger

```text
I_exec
TriggerScore
safety-aware trigger
```

## Phase 4 — Add fallback/repair

```text
MinimalSafetyRepair
ExecutionAwareLocalRepair
SafeHold
ManualReview
```

## Phase 5 — Experiments

```text
basic robustness
data reliability
safety/fallback
cross-layout
ablation
```

---

# 26. Contribution Claims

## C1

We formulate execution-aware stable CRP replanning under imperfect operational feedback.

## C2

We introduce a state reliability estimator that quantifies stale and inconsistent operational state for replanning decisions.

## C3

We propose an execution impact estimator that combines delay, failure, mismatch, operator rejection and safety impact.

## C4

We extend stable replanning with execution and safety costs.

## C5

We design a fallback hierarchy for safe recovery from invalid, failed or low-confidence plans.

## C6

We extend the SAR-CRP benchmark with execution feedback and data reliability events.

---

# 27. Limitations and Future Work

Limitations:

```text
- No multi-crane scheduling in Paper 2
- Execution feedback is synthetic unless real terminal data is available;
  event probabilities/severity (section 38.3, 39.2, 39.3) are heuristic,
  not calibrated against real terminal execution logs (see 39.3.1)
- Operator study is optional
- Safety constraints are simplified for benchmark setting
- Related Work grounding still needs concrete citations on execution-
  uncertainty/robust scheduling literature (see section 4)
- B2 baseline depends on Shin et al. 2026 (CRP_RL), which still needs
  citation verification (same requirement as Paper 1 section 3)
```

Future work:

```text
- Multi-crane/resource-aware stable replanning
- Real TOS/TAS/ECS integration
- Real terminal pilot
- Learning trigger parameters from historical execution logs
- Human-in-the-loop operator acceptance study
```

---

# 28. Final Positioning

Paper 2 should not be presented as a new CRP solver.

Correct positioning:

> **Paper 1 makes replanning stable under evolving retrieval information. Paper 2 makes replanning robust under imperfect execution.**

Final claim:

> EA-SAR-CRP extends stable adaptive CRP replanning by explicitly modeling execution feedback, state reliability, safety constraints and fallback recovery, enabling safer and more deployment-oriented relocation-plan adaptation under imperfect operational feedback.


---

# 29. ULTRA-FINAL UPDATE — Missing Details Before Coding

Phần này cập nhật các thiếu sót cuối cùng trước khi triển khai code. Mục tiêu là biến Paper 2 từ bản **Implementation-Ready** thành bản **Ultra-Final Implementation-Ready**, đặc biệt làm rõ benchmark, ground-truth/proxy, timeout, quan hệ với Paper 1, và các chi tiết còn có thể gây hiểu sai khi lập trình viên bắt tay vào code.

---

# 30. Relationship to Paper 1 — Explicit Reuse

EA-SAR-CRP không viết lại SAR-CRP từ đầu. Paper 2 kế thừa trực tiếp codebase, dữ liệu và công thức từ Paper 1.

```text
Paper 2 codebase = Paper 1 SAR-CRP codebase + execution feedback modules
```

## 30.1 Components reused from Paper 1

| Component | Reused from Paper 1? | Role in Paper 2 |
|---|---:|---|
| YardState schema | Yes | Base state representation |
| Plan / Action schema | Yes | Existing relocation plan |
| Retrieval event generator | Yes | Generates evolving retrieval information |
| Retrieval impact estimator | Yes | Computes retrieval-side replanning pressure |
| Freeze horizon | Yes | Protects committed plan prefix |
| Stability cost | Yes | Penalizes disruptive plan changes |
| Candidate repair planner | Yes | Base repair mechanism |
| CRP_RL wrapper | Yes | Initial planner and reoptimization baseline |
| Benchmark sanity checks | Yes | Applied to Paper 2 benchmark as well |

## 30.2 Components added in Paper 2

| New component | Purpose |
|---|---|
| ExecutionFeedback | Records delay, failure, mismatch, operator rejection |
| StateReliability | Scores whether the current state can be trusted |
| ExecutionImpactEstimator | Measures execution-side pressure to replan |
| SafetyConstraint schema | Encodes hard/soft operational constraints |
| Fallback/Rollback hierarchy | Provides safe recovery when candidate plans fail |
| Execution-aware benchmark generator | Adds execution/data-quality events on top of Paper-1 events |

## 30.3 Paper 1 vs Paper 2

| Thành phần | Paper 1 | Paper 2 |
|---|---|---|
| Main uncertainty | Retrieval information changes | Retrieval + execution feedback + state reliability |
| Trigger | Retrieval impact | Retrieval impact + execution impact + data confidence |
| State assumption | State mostly correct | State can be stale, missing, conflicting, low confidence |
| Main repair | Stable retrieval-aware repair | Safety-aware execution repair |
| Fallback | Basic keep-old-plan fallback | Minimal Repair → Keep Old Plan → Safe Hold / Manual Review |
| Safety | Basic feasibility validation | Explicit hard/soft safety constraints |
| Research question | Stable under evolving information | Robust under imperfect execution |

Câu chốt:

> **Paper 1 makes replanning stable under evolving retrieval information. Paper 2 makes replanning robust under imperfect execution.**

---

# 31. Abstract Update for Paper 2

Bản abstract của Paper 2 cần nói rõ quan hệ với Paper 1 ngay từ đầu.

```text
Building on SAR-CRP, which studies stable adaptive replanning under evolving retrieval information, this paper extends the framework to imperfect execution environments. In real container-yard operations, relocation plans may deviate from execution due to delayed actions, failed moves, inaccurate container locations, stale system updates, operator rejection, or safety conflicts. These execution-side uncertainties are rarely modeled explicitly in classical CRP and real-time replanning studies, which often assume that the current state is accurate and that planned actions are executed as expected.

We propose EA-SAR-CRP, an execution-aware stable replanning framework that augments SAR-CRP with execution feedback, state reliability estimation, safety-aware triggering, and fallback/rollback mechanisms. The proposed method jointly considers operational cost, plan stability, data reliability, execution risk, and safety constraints. It decides whether to keep the current plan, minimally repair it, replan part of it, or escalate to safe hold/manual review when reliable automated repair is not possible.

EA-SAR-CRP is evaluated on a dynamic benchmark that combines retrieval-information changes from SAR-CRP with execution feedback events such as action delay, action failure, container-location mismatch, stale state updates, and operator rejection. The method is compared against Paper-1 SAR-CRP, full reoptimization, reactive repair, reliability-agnostic repair, and minimal repair baselines. The evaluation measures operational efficiency, plan stability, recovery behavior, safety violations, runtime, fallback rate, and robustness under imperfect operational feedback.
```

---

# 32. Reuse of Retrieval Impact Estimator from Paper 1

Paper 2 does not redefine retrieval impact. It reuses the Paper-1 retrieval impact estimator.

Retrieval impact:

```text
I_retrieval = w_order I_order
            + w_target I_target
            + w_blocking I_blocking
            + w_plan I_plan
            + w_conf I_conf
```

Where:

| Component | Meaning |
|---|---|
| `I_order` | Kendall-tau top-k retrieval order change |
| `I_target` | Whether the immediate target changed |
| `I_blocking` | Saturated blocker-pressure change |
| `I_plan` | Fraction of affected actions in the old plan |
| `I_conf` | Retrieval information confidence penalty |

Paper 2 then combines this retrieval-side impact with execution-side impact:

```text
TriggerScore = α_trig I_retrieval + β_trig I_exec + γ_trig (1 - Conf(S_t))
```

(`α_trig, β_trig, γ_trig` — không dùng lại `α, β, γ` của `C_op` bên Paper 1, xem ghi chú ký hiệu ở mục 20/45.)

Default:

```text
α_trig = 0.4
β_trig = 0.4
γ_trig = 0.2
θ_trigger = 0.30
τ = 0.01 × J(P_old)
```

---

# 33. Execution Cost Clarification

Paper 2 uses the following execution cost:

```text
C_exec(P) = Σ_{a ∈ Actions(P)} [
    penalty_delay(a)
  + penalty_failure(a)
  + penalty_mismatch(a)
]
```

## 33.1 Delay penalty

For an action `a`:

```text
penalty_delay(a) = min(1, delay_steps(a) / d_max), if a has delay feedback
penalty_delay(a) = 0, otherwise
```

Default:

```text
d_max = 10
```

Interpretation:

- If an action is delayed by 2 steps and `d_max = 10`, penalty = 0.2.
- If no delay feedback exists for the action, penalty = 0.
- We do not penalize unexecuted future actions unless they are directly affected by a feedback event.

## 33.2 Failure penalty

```text
penalty_failure(a) = 1, if a has failed execution feedback
penalty_failure(a) = 0, otherwise
```

Examples of failure:

```text
- destination stack became full
- target container not accessible
- move cannot be executed due to missing location
- action violates safety validator after state update
```

## 33.3 Mismatch penalty

```text
penalty_mismatch(a) = 1 - Conf(entity(a))
```

Where `entity(a)` can be:

- action container;
- source stack;
- destination stack;
- state region affected by this action.

If no mismatch is reported:

```text
penalty_mismatch(a) = 0
```

---

# 34. Data Confidence Cost Clarification

Paper 2 uses the same simple data confidence cost as Paper 1 unless explicitly extended in future work.

```text
C_data(P) = Changes(P, P_old) × (1 - Conf(S_t))
```

Where:

- `Changes(P, P_old)` is the normalized number of changed actions compared with the old plan;
- `Conf(S_t)` is the global state confidence;
- if state confidence is low, large plan changes are discouraged.

The more detailed importance-weighted variant is reserved for future work:

```text
C_data^advanced(P) = Σ_{a ∈ Changes} importance(a) × (1 - Conf(a))
```

This is not part of the main Paper-2 method to keep the scope controlled.

---

# 35. Source Factor Rationale

Source factors in the State Reliability Estimator are heuristic estimates reflecting typical reliability differences between terminal data sources.

| Source | Factor | Rationale |
|---|---:|---|
| Simulator | 1.00 | Fully controlled synthetic source |
| Crane telemetry | 0.95 | Usually close to physical execution |
| TOS | 0.90 | Authoritative but may be delayed or manually corrected |
| OCR / vision | 0.80 | Useful but prone to recognition error |
| Manual entry | 0.50 | Useful fallback but more error-prone |

Formula:

```text
Conf(container) = exp(-κ × age(container)) × source_factor(container)
```

Default:

```text
κ = 0.1
```

These values are not claimed to be universal. If real operational logs are available, they should be calibrated per terminal. The important modeling decision is that state reliability depends on both information age and source reliability.

---

# 36. Timeout Protocol for Paper 2

Paper 2 adds execution feedback and safety validation, but candidate generation still uses the Paper-1 repair/replanning machinery. Therefore, the default protocol is:

| Instance size | Paper-1 timeout | Paper-2 timeout | Fallback |
|---|---:|---:|---|
| Small | 1s | 2s | Minimal Repair → Keep Old Plan |
| Medium | 5s | 8s | Minimal Repair → Keep Old Plan |
| Large | 30s | 40s | Minimal Repair → Keep Old Plan → Safe Hold |

Rationale:

- Paper 2 allows slightly more runtime because it performs reliability and safety checks.
- Execution modules are lightweight, but safety validation and additional candidate filtering can add overhead.
- If runtime exceeds the limit, local search is stopped immediately and the best feasible candidate found so far is returned.
- If no feasible candidate exists, the system falls back.

Runtime metrics must include:

```text
mean runtime
P95 runtime
timeout rate
fallback rate
safe-hold rate
```

Hardware reporting is mandatory:

```text
CPU model
RAM
number of threads
GPU usage yes/no
operating system
```

Default reporting assumption:

```text
CPU-only execution, no GPU required.
```

---

# 37. Hyperparameter Tuning Protocol

To avoid overfitting to benchmark layouts, Paper 2 follows the same cross-layout protocol as Paper 1.

```text
Hyperparameters are tuned on Layout A only.
Layouts B and C are evaluated using the same hyperparameters without retuning.
```

Parameters tuned on Layout A:

```text
λ, μ, ν, ω, κ, θ_trigger, θ_exec, d_max, timeout scale
```

Evaluation on Layout B/C reports:

```text
performance drop
runtime change
fallback rate change
safety violation rate
recovery quality
```

No parameter search is allowed on Layout B/C.

---

# 38. Paper 2 Benchmark — Ultra-Final Specification

Paper 2 benchmark combines:

```text
Paper-1 dynamic retrieval events
+
Paper-2 execution feedback events
+
state reliability degradation events
+
safety/fallback scenarios
```

The benchmark is named:

```text
EA-Dynamic CRP Benchmark
```

## 38.1 Instance schema

```json
{
  "instance_id": "EA_DCRP_000001",
  "layout_id": "layout_A_small",
  "seed": 42,
  "initial_state": {...},
  "initial_retrieval_queue": ["C1", "C2", "C3", "C4"],
  "initial_plan": {...},
  "retrieval_event_stream": [...],
  "execution_event_stream": [...],
  "state_reliability_events": [...],
  "safety_events": [...],
  "parameters": {
    "uncertainty_level": "medium",
    "execution_noise_level": "medium",
    "data_quality_level": "medium"
  }
}
```

## 38.2 Number of instances

Minimum benchmark size for Paper 2:

| Layout | Size | Instances per setting | Purpose |
|---|---|---:|---|
| Layout A | Small | 100 | tuning + ground-truth/exhaustive tests |
| Layout A | Medium | 100 | main evaluation |
| Layout A | Large | 50 | scalability/runtime |
| Layout B | Medium | 100 | cross-layout generalization |
| Layout C | Medium | 100 | cross-layout generalization |

Minimum total:

```text
450 instances
```

If compute is limited, MVP uses:

```text
Layout A small only
30 instances
3 baselines
```

## 38.3 Uncertainty levels

| Level | Retrieval event probability | Execution event probability | State degradation probability |
|---|---:|---:|---:|
| Low | 0.10 | 0.05 | 0.05 |
| Medium | 0.25 | 0.15 | 0.10 |
| High | 0.40 | 0.30 | 0.20 |

---

# 39. Execution Event Generator

At each simulation step, execution events are generated according to configured probabilities.

## 39.1 Event types

| Event type | Meaning |
|---|---|
| `action_delayed` | An action takes longer than expected |
| `action_failed` | An action cannot be completed |
| `container_location_mismatch` | Observed location differs from planned/recorded location |
| `operator_rejected` | Operator rejects proposed action |
| `state_update_delayed` | System state becomes stale |
| `unsafe_action_detected` | Safety validator detects a violation |

## 39.2 Default event distribution

Given that an execution event occurs:

| Execution event | Probability |
|---|---:|
| `action_delayed` | 0.35 |
| `action_failed` | 0.20 |
| `container_location_mismatch` | 0.15 |
| `operator_rejected` | 0.10 |
| `state_update_delayed` | 0.15 |
| `unsafe_action_detected` | 0.05 |

The probabilities sum to 1.0.

## 39.3 Event severity

| Severity | Delay steps | Failure probability multiplier | Confidence range |
|---|---:|---:|---|
| Low | 1–2 | 0.5× | [0.75, 1.00] |
| Medium | 3–5 | 1.0× | [0.50, 0.85] |
| High | 6–10 | 1.5× | [0.20, 0.70] |

## 39.3.1 Căn cứ và giới hạn của các tham số trên

Giống Paper 1 (mục 39.1.1 của Paper 1), toàn bộ xác suất/severity ở mục 38.3, 39.2, 39.3 là **giả định heuristic**, chưa hiệu chỉnh từ log thực thi/execution log thật của một cảng cụ thể (tần suất crane delay thật, tỷ lệ failed move thật...). Trước khi đưa vào paper chính thức:

```text
1. Nếu có execution log thật (dù một phần), ước lượng lại p_delay/p_failure/
   p_mismatch/p_operator_reject từ đó thay vì heuristic.
2. Nếu không có, giữ nguyên nhưng:
   a. Gọi rõ là "assumed execution-noise distribution" trong paper.
   b. Bắt buộc chạy đủ benchmark sanity checks SC1-SC5 (mục 42) làm bằng
      chứng gián tiếp benchmark hợp lý.
   c. Đưa "calibration against real execution logs" vào Limitations (mục 27).
```

## 39.4 Pseudocode

```text
Algorithm GenerateExecutionEvents

Input:
    current_step t
    current_plan P
    current_state S
    execution_noise_level L_exec
    data_quality_level L_data
    random_seed

1. Set p_exec based on L_exec
2. Set p_data based on L_data
3. events = []

4. If Random() < p_exec:
       event_type = SampleFromExecutionEventDistribution()
       action = SampleAffectedAction(P)
       severity = SampleSeverity(L_exec)
       events.add(CreateExecutionEvent(event_type, action, severity))

5. If Random() < p_data:
       data_event_type = SampleFrom({state_update_delayed, container_location_mismatch})
       entity = SampleAffectedEntity(S)
       confidence = SampleConfidence(L_data)
       events.add(CreateDataQualityEvent(data_event_type, entity, confidence))

6. Return events
```

## 39.5 Combining retrieval and execution events

Paper 2 benchmark uses both event streams:

```text
At each step t:
    retrieval_events_t = GenerateRetrievalEvents_Paper1(...)
    execution_events_t = GenerateExecutionEvents_Paper2(...)
    combined_events_t = retrieval_events_t ∪ execution_events_t
```

The state update order is:

```text
1. Apply executed actions completed before t
2. Apply execution feedback events
3. Apply state reliability/data-quality updates
4. Apply retrieval information updates
5. Recompute impact and trigger
```

This order avoids using stale state when evaluating new retrieval events.

---

# 40. Execution Event Schema

```json
{
  "event_id": "EXE_00017",
  "time_step": 12,
  "type": "action_delayed",
  "action_id": "A_004",
  "container_id": "C7",
  "delay_steps": 4,
  "source": "crane_telemetry",
  "confidence": 0.92,
  "severity": "medium",
  "metadata": {
    "reason": "crane_slowdown"
  }
}
```

Failure event:

```json
{
  "event_id": "EXE_00021",
  "time_step": 18,
  "type": "action_failed",
  "action_id": "A_009",
  "container_id": "C12",
  "source": "simulator",
  "confidence": 1.0,
  "severity": "high",
  "metadata": {
    "reason": "destination_stack_full",
    "failed_constraint": "SAFE_001"
  }
}
```

Location mismatch event:

```json
{
  "event_id": "EXE_00031",
  "time_step": 22,
  "type": "container_location_mismatch",
  "container_id": "C15",
  "reported_location": "S3-T2",
  "observed_location": "S5-T1",
  "source": "ocr",
  "confidence": 0.72,
  "severity": "medium"
}
```

Operator rejection event:

```json
{
  "event_id": "OP_00005",
  "time_step": 25,
  "type": "operator_rejected",
  "action_id": "A_013",
  "container_id": "C8",
  "reason_code": "unsafe_or_untrusted",
  "free_text": "Stack S4 is temporarily blocked.",
  "confidence": 1.0
}
```

---

# 41. Ground Truth / Proxy Protocol for Paper 2

Paper 2 does not claim true optimality for all instance sizes. It uses different evaluation references by instance size.

## 41.1 Small instances

For small instances:

```text
Use exhaustive search when feasible.
```

Scope:

```text
small layouts
short horizon
limited number of actions
execution feedback enabled for delay/failure only
```

Output:

```text
best known total cost J*(P)
optimality gap if exhaustive search completes
```

## 41.2 Medium and large instances

For medium/large instances:

```text
Use extended-time full reoptimization as an offline high-quality proxy.
```

Default proxy runtime:

```text
300 seconds per replanning episode
```

Important wording:

```text
We do not claim this proxy is globally optimal. We use it as a high-quality offline reference to contextualize online method performance.
```

## 41.3 Reported comparison

For each method:

```text
relative cost vs proxy
stability vs proxy
runtime vs proxy
fallback rate
safety violation rate
```

---

# 42. Benchmark Sanity Checks for Paper 2

Before running main experiments, benchmark instances must pass sanity checks.

## SC1 — Not too easy

Static / Paper-1 SAR-CRP should degrade under execution events.

Check:

```text
EA event benchmark is valid only if execution events increase failed actions, fallback needs, or total cost compared with clean execution.
```

## SC2 — Not too hard

If all methods frequently enter Safe Hold, the benchmark is too hard.

Check:

```text
safe_hold_rate < 30% for medium setting
```

## SC3 — Event distribution reasonable

No event type should dominate the benchmark unless intentionally stress-tested.

Check:

```text
max_event_type_share < 50% in mixed scenario
```

## SC4 — Impact distribution reasonable

Trigger impact should not be always near 0 or always near 1.

Check:

```text
20%–80% of instances should fall in non-trivial trigger-score range [0.2, 0.8]
```

## SC5 — Fallback is exercised but not dominant

Fallback should appear in realistic scenarios but not dominate all decisions.

Check:

```text
fallback_rate between 5% and 40% in medium/high execution-noise settings
```

---

# 43. Baseline Clarification

Paper 2 uses the following main baselines.

| Baseline | Reference / inspiration | Description | Difference from EA-SAR-CRP |
|---|---|---|---|
| B1 Paper-1 SAR-CRP | Paper 1 | Uses retrieval impact and stable repair, but ignores execution feedback | No execution-aware trigger, no reliability/safety fallback |
| B2 Full Reoptimization | Shin et al. 2026 / CRP_RL | Recompute full plan after each event | No stability/fallback hierarchy |
| B3 Reactive Repair | Heuristic / reactive scheduling | Repair only after an action fails | No proactive execution impact trigger |
| B4 Reliability-Agnostic Repair | Ablation baseline | Uses execution feedback but ignores confidence | Tests value of state reliability |
| B5 Minimal Repair | Heuristic fallback | Only repairs invalid/failed actions | Tests value of full EA-SAR-CRP decision logic |
| B6 EA-SAR-CRP | Proposed | Retrieval + execution + reliability + safety-aware fallback | Proposed method |

Optional exploratory baseline:

| Optional baseline | Reason optional |
|---|---|
| RL with stability/execution penalty | Requires substantial training data; harder to guarantee safety, explainability and transferability |

---

# 44. Updated Experimental Design

Paper 2 uses five experiments.

## Experiment 1 — Main execution robustness

Goal:

```text
Evaluate whether EA-SAR-CRP improves robustness under execution feedback.
```

Settings:

```text
Layout A medium
100 instances
low/medium/high execution noise
all six baselines
```

Metrics:

```text
total cost
failed actions
recovery time
fallback rate
stability cost
runtime
```

## Experiment 2 — Data reliability stress test

Goal:

```text
Evaluate whether state confidence prevents harmful replanning under stale/mismatched data.
```

Settings:

```text
Layout A medium
100 instances
low/medium/high data quality degradation
```

Metrics:

```text
low-confidence decision rate
confidence-weighted regret
fallback rate
safe-hold rate
```

## Experiment 3 — Safety and fallback analysis

Goal:

```text
Test fallback hierarchy under invalid candidates, hard safety violations and timeouts.
```

Settings:

```text
targeted safety stress scenarios
50–100 instances
```

Metrics:

```text
invalid recommendation rate
hard violation rate
safe repair success rate
manual review rate
```

## Experiment 4 — Cross-layout generalization

Goal:

```text
Measure whether parameters tuned on one layout transfer to other layouts.
```

Protocol:

```text
Tune on Layout A only.
Test Layout B and C without retuning.
```

Metrics:

```text
performance drop
timeout change
fallback change
safety violation change
```

## Experiment 5 — Ablation study

Ablations:

```text
A1 No State Reliability          (Conf(S_t) cố định = 1, bỏ mismatch penalty/trigger term — kiểm tra C2)
A2 No Execution Impact in Trigger (beta_trig = 0, theta_exec vô hiệu — kiểm tra vai trò I_exec trong trigger, C3)
A3 No Execution Cost in Objective (nu = 0, bỏ C_exec khỏi J2 — kiểm tra vai trò C_exec trong scoring, C3/C4)
A4 No Safety Cost                (omega = 0, chỉ giữ hard constraint như feasibility filter — kiểm tra C4)
A5 No Fallback Hierarchy         (mọi candidate invalid/timeout đi thẳng Safe Hold, bỏ qua Minimal Repair/Keep Old Plan — kiểm tra C5)
A6 No Execution-Aware Local Repair (bỏ candidate C2, chỉ còn C0/C1/C3/C4 — kiểm tra riêng giá trị của local repair)
```

Ablation phụ (optional, chạy nếu còn compute — không bắt buộc cho MVP):

```text
A7 No Stability Cost            (lambda = 0 — kiểm tra D(P,P_old) kế thừa từ Paper 1 còn cần thiết trong bối cảnh Paper 2 không)
A8 No Retrieval Impact Reuse    (alpha_trig = 0 — trigger chỉ dựa execution + confidence, không dùng I_retrieval)
A9 No Operator Rejection Handling (bỏ qua rejection log/next-best-candidate ở mục 17, coi mọi candidate đề xuất là chấp nhận)
```

Goal:

```text
A1-A6 map trực tiếp tới các contribution claims C2-C5 (mục 26) — bắt buộc chạy đủ 6 cái này.
A7-A9 chỉ để bổ sung insight nếu còn thời gian/compute, không bắt buộc.
```

---

## Statistical Protocol (bắt buộc, dùng chung nguyên tắc với Paper 1 mục 23.6)

Áp dụng đúng protocol thống kê của Paper 1 (mục 23.6), điều chỉnh cho 5 baseline so sánh (B1-B5 vs B6 EA-SAR-CRP) thay vì 5 baseline của Paper 1:

```text
Số lần lặp:
    Mỗi (instance, uncertainty/execution-noise level, baseline) chạy với
    >= 20 random seed khác nhau (seed kiểm soát cả retrieval event stream
    lẫn execution event stream — mục 39.5).

Báo cáo:
    Mean +/- 95% CI cho mọi metric ở mục 22 (operational, stability,
    reliability, safety, runtime).

Kiểm định ý nghĩa:
    Wilcoxon signed-rank test (paired) khi so EA-SAR-CRP với từng baseline
    B1-B5 trên total cost, stability cost, safety violation rate.
    Hiệu chỉnh Holm-Bonferroni cho 5 so sánh cùng lúc (giống Paper 1).

Effect size:
    Báo cáo effect size (rank-biserial hoặc Cliff's delta) bên cạnh p-value,
    đặc biệt quan trọng cho safety/fallback rate vì đây là metric hiếm
    (rare-event) dễ bị nhiễu khi n nhỏ.

Ablation (mục 44, Experiment 5 — Ablation study):
    Áp dụng cùng protocol trên (mỗi ablation A1-A6 vs EA-SAR-CRP đầy đủ).
```

---

# 45. Updated Default Parameter Table

Bảng này là **nguồn duy nhất** cho mọi tham số Paper 2 (đã hợp nhất với mục 20 — không còn bảng nào khác cần tra cứu thêm).

| Parameter | Meaning | Default | Range / sensitivity |
|---|---|---:|---|
| λ | Stability cost weight (same as Paper 1) | 1.0 | {0.5, 1.0, 2.0} |
| μ | Data confidence cost weight (same as Paper 1) | 0.5 | {0, 0.5, 1.0} |
| ν | Execution cost weight | 1.0 | {0.5, 1.0, 2.0} |
| ω | Safety cost weight | 5.0 | {1.0, 5.0, 10.0} |
| κ | Confidence decay rate | 0.1 | {0.05, 0.1, 0.2} |
| d_max | Max delay steps for normalization | 10 | {5, 10, 15} |
| α_trig | Retrieval impact trigger weight (TriggerScore — không trùng α của C_op Paper 1) | 0.4 | fixed main setting |
| β_trig | Execution impact trigger weight (TriggerScore) | 0.4 | fixed main setting |
| γ_trig | State unreliability trigger weight (TriggerScore) | 0.2 | fixed main setting |
| θ_trigger | Trigger threshold (trên TriggerScore tổng hợp) | 0.30 | {0.20, 0.30, 0.40} |
| τ | Gain threshold | 0.01 × J(P_old) | {0.005, 0.01, 0.02} |
| θ_exec | Execution impact threshold — fast-path trigger độc lập khi I_exec riêng đã cao (mục 14/16.1) | 0.25 | {0.15, 0.25, 0.35} |
| θ_conf_min | Minimum global state confidence trước khi route sang Safe Hold/Manual Review | 0.40 | {0.3, 0.4, 0.5} |
| T | Local search iterations (ExecutionAwareLocalRepair) | 100 | {50, 100, 200} |
| M | Max neighbors per iteration | 50 | {20, 50, 100} |
| epsilon | Exploration probability | 0.05 | {0, 0.05, 0.10} |
| timeout_small | Small timeout | 2s | fixed |
| timeout_medium | Medium timeout | 8s | fixed |
| timeout_large | Large timeout | 40s | fixed |
| source_factor_TOS | TOS source reliability | 0.90 | calibratable |
| source_factor_crane | Crane telemetry reliability | 0.95 | calibratable |
| source_factor_OCR | OCR reliability | 0.80 | calibratable |
| source_factor_manual | Manual input reliability | 0.50 | calibratable |

---

# 46. Updated MVP Before Full Experiments

Before running full Paper-2 experiments, run a small MVP.

## MVP setting

```text
Layout A small
30 instances
3 baselines:
    B1 Paper-1 SAR-CRP
    B2 Full Reoptimization
    B6 EA-SAR-CRP
execution noise: medium
state degradation: medium
```

## MVP success gate

Continue to full experiments only if:

```text
EA-SAR-CRP reduces failed/infeasible decisions compared with Paper-1 SAR-CRP
AND
EA-SAR-CRP reduces plan churn compared with Full Reoptimization
AND
EA-SAR-CRP total cost is better than at least one strong baseline
AND
fallback/safe-hold rates are not excessive
```

If not:

```text
Stop and revise C_exec, trigger weights or fallback hierarchy before scaling.
```

---

# 47. Final Ultra-Ready Status

After this update, Paper 2 is implementation-ready at the same level as Paper 1.

Remaining optional enhancements:

```text
1. RL baseline with execution/stability penalty
2. small operator user study
3. real terminal log calibration
4. multi-crane/resource-aware extension for Paper 3
```

These are not required for Paper 2.

Final positioning:

> **EA-SAR-CRP extends stable adaptive CRP replanning by explicitly modeling execution feedback, state reliability, safety constraints and fallback recovery, enabling safer and more deployment-oriented relocation-plan adaptation under imperfect operational feedback.**
