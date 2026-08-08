# PAPER 3 IMPLEMENTATION-READY RESEARCH PROPOSAL
# MISR-Yard: Multi-Intervention Stable Replanning for Container Yard Operations

**Tên tiếng Việt:** Tái lập kế hoạch ổn định đa can thiệp cho vận hành bãi container  
**Tên ngắn:** MISR-Yard  
**Vị trí trong roadmap:** Paper 3 sau SAR-CRP Paper 1 và EA-SAR-CRP Paper 2  
**Mục tiêu:** Chuyển từ stable replanning cho một loại can thiệp sang **decision orchestration** giữa nhiều loại can thiệp vận hành: container repair, resource/crane reassignment, job resequencing, wait/no-op và limited hybrid intervention.

---

# 0. Cập nhật theo review giáo sư

Bản này cập nhật Paper 3 từ mức **research concept** lên mức **implementation-ready proposal**, tương tự Paper 1 và Paper 2.

Các phần đã bổ sung:

1. Implementation Appendix đầy đủ.
2. Schema chi tiết cho `CraneState`, `ResourceEvent`, `SafetyConstraint`, `InterventionCandidate`.
3. Pseudocode cho:
   - `GenerateContainerRepair()`;
   - `GenerateResourceReassignment()`;
   - `GenerateJobResequencing()`;
   - `GenerateWaitNoOp()`;
   - `GenerateLimitedHybrid()`;
   - `GenerateSafeRepair()`;
   - `ResourceCost()`;
   - `ResourceStability()`;
   - `InterventionComplexity()`.
4. Công thức chi tiết cho resource travel, idle, imbalance, conflict và crane-assignment stability.
5. Benchmark specification: số lượng instances, layouts, event streams, resource scenarios.
6. Ground-truth/proxy cho small/medium/large instances.
7. Timeout protocol riêng cho Paper 3.
8. Baseline mapping rõ hơn, đặc biệt B3 Resource-only Repair và B6 Rule-based Intervention.
9. Flow dữ liệu chi tiết từ input đến output.
10. Relationship rõ ràng với Paper 1 và Paper 2.

---

# 1. Tóm tắt đề xuất

Paper 1 giải quyết:

> Khi retrieval information thay đổi, có nên sửa relocation plan không, và sửa thế nào để plan vẫn ổn định?

Paper 2 giải quyết:

> Khi execution feedback không hoàn hảo, dữ liệu thiếu/tin cậy thấp, action fail/delay, hệ thống nên repair/fallback thế nào cho an toàn?

Paper 3 đi tiếp:

> Khi yard có vấn đề hoặc có nguy cơ nghẽn, hệ thống nên chọn loại can thiệp nào: sửa relocation plan, đổi resource/crane, đổi job sequence, hay chờ thêm thông tin?

Paper 3 không phải là “CRP + crane scheduling”. Điểm mới là **multi-intervention decision orchestration**: một lớp quyết định cao hơn các solver riêng lẻ, có nhiệm vụ chọn đúng loại intervention dựa trên operational cost, plan stability, execution risk, resource feasibility, safety và intervention complexity.

Câu chốt:

> **Paper 1 makes replanning stable under evolving retrieval information. Paper 2 makes replanning robust under imperfect execution. Paper 3 makes replanning strategic by choosing the right intervention family.**

---

# 2. Tên đề tài

## Tên chính

**MISR-Yard: Multi-Intervention Stable Replanning for Container Yard Operations under Evolving Operational Conditions**

## Tên tiếng Việt

**Tái lập kế hoạch ổn định đa can thiệp cho vận hành bãi container dưới điều kiện vận hành thay đổi**

## Câu định vị học thuật

> MISR-Yard extends stable adaptive replanning from single-intervention repair to multi-intervention orchestration, enabling container yard systems to decide whether to repair container plans, reassign resources, resequence jobs, or wait, based on a joint assessment of operational efficiency, plan stability, execution risk, resource feasibility, safety and intervention complexity.

---

# 3. Quan hệ với Paper 1 và Paper 2

| Thành phần | Paper 1: SAR-CRP | Paper 2: EA-SAR-CRP | Paper 3: MISR-Yard |
|---|---|---|---|
| Vấn đề chính | Retrieval information thay đổi | Execution feedback và dữ liệu không hoàn hảo | Chọn loại can thiệp phù hợp |
| Đối tượng sửa | Relocation plan | Relocation plan + fallback/recovery | Container/resource/schedule/wait interventions |
| Trigger | Retrieval impact | Retrieval + execution + data reliability | Diagnosis + multi-impact |
| State | Giả định tương đối đúng | Có confidence/reliability | Có resource/crane state |
| Fallback | Keep old plan / minimal repair | Rollback + safe hold | Safe repair + manual review |
| Safety | Basic feasibility | Hard/soft safety | Hard/soft safety + resource conflict |
| Resource/crane | Ngoài scope | Chỉ là feedback/safety nếu cần | Một intervention family chính |
| Output | Keep/update CRP plan | Safe repaired plan | Intervention decision + updated operational plan |
| Main claim | Stable replanning | Robust execution-aware replanning | Strategic multi-intervention orchestration |

Codebase relationship:

```text
Paper 3 codebase = Paper 2 codebase
                 + CraneState model
                 + ResourceEvent generator
                 + Resource feasibility checker
                 + Multi-intervention candidate generator
                 + Resource cost and resource stability metrics
                 + Multi-intervention selector
```

---

# 4. Vấn đề nghiên cứu

Trong vận hành bãi container, khi một vấn đề xuất hiện, không phải lúc nào cách xử lý tốt nhất cũng là sửa relocation plan.

Ví dụ Block B12 có nguy cơ nghẽn. Các can thiệp có thể là:

1. Chuyển một số container sang stack/block khác.
2. Đổi destination của relocation sắp tới.
3. Reassign một crane sang block B12.
4. Đổi thứ tự job để xử lý urgent retrieval trước.
5. Delay một số low-priority move.
6. Chờ thêm thông tin vì confidence thấp.
7. Kết hợp container repair + crane reassignment ở mức giới hạn.

CRP truyền thống hỏi:

> Container nào cần move và move đi đâu?

SAR-CRP Paper 1–2 hỏi:

> Có nên sửa plan không và sửa thế nào cho ổn định/an toàn?

MISR-Yard hỏi:

> Trong nhiều loại can thiệp khác nhau, loại nào nên được chọn để tạo hiệu quả vận hành cao nhất mà vẫn giữ plan ổn định, khả thi về tài nguyên và an toàn?

---

# 5. Research gap

## Gap 1 — CRP và resource scheduling thường tách rời

Một relocation plan có thể tốt về số relocation nhưng không tốt về tài nguyên:

- crane đang ở xa;
- crane bị bận;
- workload mất cân bằng;
- relocation tạo thêm travel time;
- đổi crane assignment làm rối execution;
- hai crane có thể conflict nếu cùng vào một zone.

## Gap 2 — Replanning thường giả định một loại intervention

Nhiều phương pháp chỉ sửa một loại plan:

- sửa relocation;
- reassign resource;
- reoptimize schedule.

Thực tế cần chọn giữa các intervention families.

## Gap 3 — Wait/no-op thường bị xem nhẹ

Trong môi trường dữ liệu không chắc chắn, can thiệp sớm có thể làm plan mất ổn định không cần thiết.

## Gap 4 — Thiếu lớp decision orchestration

Terminal operations cần một lớp cao hơn các optimizer riêng lẻ:

```text
Container Repair Planner
Resource Reassignment Planner
Job Resequencing Planner
Wait/No-op Policy
        ↓
Multi-Intervention Orchestrator
```

> **Cần bổ sung trước khi submit.** Mục Research Gap này hiện chưa trích dẫn cụ thể literature nào cho "multi-intervention/decision orchestration" — chỉ lập luận nội bộ. Trước khi viết Related Work thật, cần tìm và trích dẫn các hướng liên quan: hierarchical RL / options framework (chọn giữa các "option"/policy con), supervisory/mode-switching control (chọn chế độ điều khiển), meta-scheduling / portfolio algorithm selection. Ngoài ra B5 (mục 29) vẫn dựa vào "Shin et al. 2026-style CRP solver" — kế thừa đúng yêu cầu xác minh citation đã nêu ở Paper 1 (mục 3) và Paper 2 (mục 4); chưa xác minh thì chưa dùng làm baseline thật trong bản nộp.

---

# 6. Câu hỏi nghiên cứu

## RQ chính

> How can a container yard system select the most appropriate intervention type under evolving operational conditions while balancing operational efficiency, plan stability, execution risk, resource feasibility and safety?

## RQ1

Khi có disruption hoặc predicted bottleneck, loại can thiệp nào tốt hơn: container repair, resource reassignment, job resequencing, wait/no-op hay limited hybrid?

## RQ2

Làm thế nào định lượng trade-off giữa intervention benefit và intervention disruption?

## RQ3

Multi-intervention orchestration có giảm plan churn/resource churn mà vẫn duy trì operational performance không?

## RQ4

Multi-intervention orchestration có tốt hơn sequential optimization không?

---

# 7. Novelty claim

Paper 3 không claim:

- làm CRP solver mới;
- làm crane scheduling solver tốt nhất;
- giải toàn bộ terminal operation;
- thay thế TOS hoặc crane optimizer.

Paper 3 claim:

> We propose a multi-intervention stable replanning framework that orchestrates container-level, resource-level, schedule-level, wait/no-op and limited hybrid interventions under evolving operational conditions, explicitly optimizing the trade-off between operational efficiency, plan stability, execution risk, resource feasibility, safety and intervention complexity.

Đóng góp chính:

1. Đề xuất formulation mới cho **Multi-Intervention Stable Yard Replanning**.
2. Định nghĩa intervention action space gồm container repair, resource reassignment, job resequencing, wait/no-op và limited hybrid intervention.
3. Đề xuất diagnosis-guided candidate generation để tránh action-space explosion.
4. Định nghĩa objective đánh giá intervention-level cost/benefit thay vì chỉ plan-level cost.
5. Xây benchmark mở rộng từ Paper 2, thêm resource events và intervention scenarios.
6. So sánh với single-intervention, sequential và rule-based baselines.

---

# 8. Phạm vi Paper 3

## Trong scope

- Container relocation repair.
- Resource/crane reassignment ở mức yard-crane đơn giản.
- Job resequencing.
- Wait/no-op decision.
- Limited hybrid intervention.
- Resource feasibility checking.
- Workload balance proxy.
- Crane travel proxy.
- Resource-assignment stability.
- Intervention selection.

## Ngoài scope

- Full optimal multi-crane scheduling.
- Quay crane scheduling.
- Berth allocation.
- Truck appointment control.
- Full TOS-level automation.
- Real-world deployment at multiple terminals.

Lưu ý:

> Resource/crane là một intervention family trong Paper 3, không phải toàn bộ paper.

---

# 9. Intervention families

## F1 — Container Repair

Kế thừa Paper 1–2.

Can thiệp:

- đổi relocation destination;
- thêm relocation cho blocker;
- loại bỏ relocation không cần thiết;
- repair action invalid;
- giữ frozen prefix.

## F2 — Resource Reassignment

Can thiệp:

- đổi crane được gán cho một action;
- chuyển crane sang block workload cao;
- chia workload giữa các crane;
- tránh crane conflict;
- giảm travel hoặc idle time.

## F3 — Job Resequencing

Can thiệp:

- đưa urgent retrieval lên sớm;
- delay low-priority relocation;
- swap hai action trong repairable tail;
- nhóm các action cùng block/zone để giảm crane travel.

## F4 — Wait / No-op

Can thiệp:

- giữ plan cũ;
- không thay đổi resource;
- chờ thêm thông tin;
- dùng khi confidence thấp hoặc expected gain nhỏ.

## F5 — Limited Hybrid Intervention

Kết hợp tối đa 2 intervention families, ví dụ:

- container repair + resource reassignment;
- job resequencing + resource reassignment;
- container repair + job resequencing.

Không cho phép hybrid quá phức tạp trong Paper 3 để tránh action-space explosion.

---

# 10. Data-flow tổng thể

```text
YardState + CurrentPlan + RetrievalInfo + ExecutionFeedback + CraneState + ResourceEvents
        ↓
State and Resource Update
        ↓
Problem Diagnosis
        ↓
Diagnosis-guided Candidate Generation
        ├─ GenerateContainerRepair()
        ├─ GenerateResourceReassignment()
        ├─ GenerateJobResequencing()
        ├─ GenerateWaitNoOp()
        └─ GenerateLimitedHybrid()
        ↓
Safety and Resource Feasibility Check
        ↓
Candidate Evaluation J(a)
        ↓
Select Best Intervention
        ↓
Fallback if invalid/timeout
        ↓
Updated Operational Plan or Keep Old Plan
```

---

# 11. Objective function

MISR-Yard đánh giá một intervention candidate `a`, không chỉ một relocation plan.


a ∈ {container_repair, resource_reassignment, job_resequencing, wait_noop, limited_hybrid}

Hàm mục tiêu:

\[
J(a)=
C_{op}(a)
+ \lambda C_{stab}(a)
+ \lambda_{res} D_{resource}(a)
+ \pi C_{data}(a)
+ \mu C_{exec}(a)
+ \nu C_{res}(a)
+ \omega C_{safety}(a)
+ \eta C_{int}(a)
\]

Trong đó:

| Thành phần | Ý nghĩa |
|---|---|
| \(C_{op}\) | relocation, retrieval delay, failed action, congestion proxy |
| \(C_{stab}\) | plan churn, changed action, changed destination, changed order — kế thừa nguyên `D(P,P_old)` của Paper 1 (mục 12 Paper 1), weight `λ` |
| \(D_{resource}\) | resource/crane assignment churn (mục 13/E) — **trước đây bị thiếu khỏi J(a)** dù có công thức đầy đủ và được dùng làm ablation A2 (mục 32); nay có weight riêng `λ_res` |
| \(C_{data}\) | data confidence cost, kế thừa nguyên công thức Paper 1/2: `C_data(a) = Changes(a,P_old) × (1-Conf(S_t))` — **trước đây bị thiếu khỏi J(a)** dù mục J.1 liệt kê là "reused without modification"; nay có weight riêng `π` |
| \(C_{exec}\) | execution delay/failure/mismatch từ Paper 2 |
| \(C_{res}\) | crane travel, idle, imbalance, conflict |
| \(C_{safety}\) | hard/soft safety constraint violation |
| \(C_{int}\) | intervention complexity, số intervention families dùng |

> **Lưu ý ký hiệu cross-paper:** `μ` ở đây là trọng số `C_exec` (không phải trọng số `C_data` như Paper 1/2 — vai trò `C_data` đã chuyển sang `π`), `ν` là trọng số `C_res` (khái niệm hoàn toàn mới của Paper 3, không phải trọng số `C_exec` như ở Paper 2). Bảng tham số đầy đủ và lý do đổi ký hiệu xem mục 31.

Chọn:

\[
a^* = \arg\min_{a\in A_t} J(a)
\]

Nếu:

\[
J(P_{old}) - J(a^*) \le \tau
\]

thì giữ plan cũ.

---

# 12. Resource cost chi tiết

## 12.1 Location representation

Mỗi action có location:

```json
{
  "block": "B1",
  "bay": 4,
  "row": 2,
  "tier": 3,
  "zone": "Z1"
}
```

Trong Paper 3, `loc(a)` có thể lấy là:

- source stack của action nếu là pickup/retrieve;
- destination stack nếu là relocation destination;
- block/zone nếu dùng coarse resource model.

## 12.2 Distance function

Mặc định dùng block-aware Manhattan distance:

\[
dist(l_1,l_2)=
w_b\cdot \mathbf{1}[block_1\ne block_2]
+ w_{bay}|bay_1-bay_2|
+ w_{row}|row_1-row_2|
\]

Default:

```text
w_b   = 10
w_bay = 1
w_row = 1
```

Nếu chỉ có zone-level layout:

\[
dist(l_1,l_2)=TravelMatrix[zone_1,zone_2]
\]

## 12.3 Travel time

\[
TravelTime(yc,l_1,l_2)=\frac{dist(l_1,l_2)}{speed(yc)}
\]

Nếu crane status là `slowdown`, speed được nhân với slowdown factor:

\[
speed'(yc)=speed(yc)\times slowdown\_factor(yc)
\]

## 12.4 Crane travel cost

Với mỗi crane \(yc\), let \(Seq(yc,a)\) là chuỗi action được gán cho crane đó sau intervention `a`.

\[
C_{travel}(a)=
\sum_{yc}\sum_{j=1}^{|Seq(yc,a)|}
TravelTime(yc, loc_{j-1}, loc_j)
\]

Trong đó \(loc_0\) là current location của crane.

## 12.5 Crane idle cost

\[
C_{idle}(a)=\sum_{yc} IdleTime(yc,a)
\]

Idle time được tính khi crane available nhưng còn job chưa được xử lý trong zone có thể phục vụ.

Approximation:

```text
IdleTime(yc) = max(0, horizon - assigned_work_time(yc) - travel_time(yc))
```

## 12.6 Workload imbalance

\[
C_{imbalance}(a)=std(Workload(YC_1),...,Workload(YC_m))
\]

Trong đó:

\[
Workload(yc)=AssignedHandlingTime(yc)+TravelTime(yc)
\]

## 12.7 Conflict penalty

Hard conflict:

```text
Two cranes assigned to same conflict zone at overlapping time window.
Crane violates safety distance.
Crane assigned outside working zone.
Crane unavailable but assigned action.
```

Nếu hard conflict tồn tại:

\[
C_{conflict}(a)=\infty
\]

Soft conflict:

```text
near-overlap
high workload zone
low-confidence crane state
```

\[
C_{conflict}^{soft}(a)=\sum_{conflict} severity(conflict)
\]

## 12.8 Total resource cost

\[
C_{res}(a)=
\alpha_r C_{travel}(a)
+ \beta_r C_{idle}(a)
+ \gamma_r C_{imbalance}(a)
+ \delta_r C_{conflict}(a)
\]

Default:

```text
alpha_r = 1.0
beta_r  = 0.5
gamma_r = 1.0
delta_r = 10.0 for soft conflict, infinity for hard conflict
```

---

# 13. Resource stability

Resource stability đo mức độ can thiệp làm thay đổi assignment của crane so với plan cũ. Đây là **một số hạng riêng trong `J(a)` với trọng số `λ_res`** (mục 11) — không bị gộp ngầm vào `C_stab(a)` (vốn chỉ tính container-plan churn kế thừa Paper 1).

\[
D_{resource}(a)=
\sum_{job}\Big[
\mathbf{1}[crane_{new}(job)\ne crane_{old}(job)]
+ \zeta_t\cdot |start_{new}(job)-start_{old}(job)|
+ \zeta_z\cdot \mathbf{1}[zone_{new}(job)\ne zone_{old}(job)]
+ \zeta_{ar}\cdot \mathbf{1}[job \text{ added hoặc removed so với } P_{old}]
\Big]
\]

Default:

```text
zeta_t  = 0.5   # khớp penalty_changed_start_time ở mục E.2
zeta_z  = 1.0   # khớp penalty_changed_work_zone ở mục E.2
zeta_ar = 2.0   # khớp penalty_added_or_removed_action ở mục E.2 — case này thiếu ở bản trước
```

(Ba tham số trên đồng bộ với `penalty_changed_crane=1.0` (hệ số 1 mặc định của số hạng đầu), `penalty_changed_start_time`, `penalty_changed_work_zone`, `penalty_added_or_removed_action` ở mục E.2 — cùng một công thức, không phải hai công thức khác nhau.)

Có time weighting giống Paper 1, nhưng dùng **decay rate riêng `ρ_res`** (không dùng chung `ρ = 0.05` của Paper 1 áp cho `D(P,P_old)`/`C_stab`, để tránh nhầm lẫn khi hai cost có tốc độ decay khác nhau):

\[
D_{resource}^{time}(a)=
\sum_{job}\exp(-\rho_{res}\cdot pos(job))\cdot d_{resource}(job)
\]

Default: `ρ_res = 0.1` (xem mục 31; khác `ρ = 0.05` của Paper 1 — hai biến độc lập, không phải hai giá trị mâu thuẫn của cùng một biến).

Ý nghĩa:

- Đổi crane cho job sắp làm bị phạt nặng.
- Đổi crane cho job xa trong tương lai bị phạt nhẹ hơn.
- Đổi work zone bị phạt vì ảnh hưởng operator/crane movement.

---

# 14. Intervention complexity

Không phải intervention càng nhiều càng tốt. Hybrid quá phức tạp có thể khó thực thi.

\[
C_{int}(a)=
\#families(a)
+ \xi_1\#changed\_actions(a)
+ \xi_2\#changed\_resources(a)
+ \xi_3\#new\_actions(a)
\]

Default:

```text
xi_1 = 0.1
xi_2 = 0.2
xi_3 = 0.2
```

Rule:

```text
If #families(a) > 2: reject candidate in Paper 3.
```

---

# 15. Problem diagnosis

Diagnosis categories:

| Diagnosis | Ý nghĩa | Candidate families ưu tiên |
|---|---|---|
| Retrieval disruption | Retrieval order/priority thay đổi | Container repair, resequencing, wait |
| Execution failure | Action fail/delay | Container repair, safe repair |
| Resource bottleneck | Crane unavailable/slow/overloaded | Resource reassignment, resequencing |
| Workload imbalance | Một crane/block quá tải | Resource reassignment |
| Safety conflict | Candidate/old plan unsafe | Safe repair, wait/manual review |
| Low confidence | Data/resource state không đáng tin | Wait/no-op, minimal repair |

Diagnosis-guided generation tránh sinh candidate bừa bãi.

---

# 16. Main algorithm

> Các lời gọi hàm dưới đây dùng đúng chữ ký chuẩn ở mục G.1–G.5 (đã bổ sung `YardState`, `K`, `freeze_horizon`, `SafetyConstraints` so với bản trước — xem ghi chú tại mỗi mục 17–22 để biết chỗ nào từng thiếu tham số).

```text
Algorithm: MISR-Yard

Input:
    YardState S_t
    CurrentPlan P_old
    RetrievalInfo R_t
    ExecutionFeedback F_t
    CraneState C_t
    ResourceEvents E_t
    SafetyConstraints SC
    StateReliability RelState
    Hyperparameters Θ

Output:
    Intervention decision a*
    Updated plan P_new or Keep(P_old)

1. Update yard state using R_t and F_t
2. Update crane/resource state using C_t and E_t
3. diagnosis = Diagnose(S_t, P_old, R_t, F_t, C_t, E_t)
4. candidates = {}
5. candidates += GenerateWaitNoOp(P_old, diagnosis, RelState)
6. if diagnosis requires container intervention:
       candidates += GenerateContainerRepair(P_old, S_t, R_t, {F_t, E_t}, K_container)
7. if diagnosis requires resource intervention:
       candidates += GenerateResourceReassignment(P_old, C_t, S_t, SC, K_resource)
8. if diagnosis requires sequencing intervention:
       candidates += GenerateJobResequencing(P_old, {R_t, F_t}, P_old.freeze_horizon, K_sequence)   # freeze_horizon lấy từ Plan schema, không phải input riêng
9. candidates += GenerateLimitedHybrid(GroupByFamily(candidates), P_old, C_t, S_t, max_families=2, K_family, max_hybrid_total, K_hybrid)
10. For each candidate a in candidates:
       if HasHardSafetyViolation(a, SC) or ResourceConflictPenalty(a.plan, C_t, SC) == INF:
           discard a
       score[a] = EvaluateCandidate(a)   # = J(a), mục 11
11. If candidates is empty:
       return GenerateSafeRepair(P_old, SC, C_t, S_t)   # mục G.7, có thể trả SafeHoldPlan
12. a_best = argmin score[a]
13. if J(P_old) - score[a_best] <= tau:
       return Keep(P_old)
14. else:
       return Apply(a_best)
```

---

# 17. Pseudocode: GenerateContainerRepair

Kế thừa Paper 2, nhưng định nghĩa lại interface cho Paper 3.

> **Chữ ký và pseudocode chuẩn để code: xem mục G.1.** Bản dưới đây minh họa ý tưởng ban đầu (tự enumerate destination + tự insert relocation cho blocker) nhưng đã **thay bằng cách tiếp cận nhất quán hơn** ở G.1: tái dùng thẳng `LocalSearchRepair` và `CRPRLWrapperRepair` đã có sẵn từ Paper 1/2 (khớp với mục J.1 — "Local Search framework" và "CRP_RL wrapper" được liệt kê là "Reused without modification") thay vì viết lại logic enumerate destination/blocker một lần nữa. Chữ ký G.1 cũng nhận `K` như tham số thay vì hằng số nội bộ, và gọi `TopKByFastScore(candidates, K, P_old)` đủ 3 tham số (bản dưới đây thiếu `P_old`, xem cảnh báo ở mục 23).

```text
Function GenerateContainerRepair(P_old, S_t, R_t, F_t):
    candidates = []

    # C1: minimal repair for invalid actions
    P_min = MinimalRepair(P_old, S_t, R_t, F_t)
    if Feasible(P_min):
        candidates.append(CreateCandidate("container_repair", P_min))

    # C2: change relocation destination for affected relocation actions
    affected = FindAffectedContainerActions(P_old, R_t, F_t)
    for action in affected:
        if action.type == "RELOCATE":
            for dest in TopKValidDestinations(action.container, S_t, K_dest):
                P_new = copy(P_old)
                P_new[action.id].dest_stack = dest
                if Feasible(P_new):
                    candidates.append(CreateCandidate("container_repair", P_new))

    # C3: insert relocation for newly exposed blocker
    blockers = FindHighPressureBlockers(S_t, R_t)
    for c in blockers:
        for dest in TopKValidDestinations(c, S_t, K_dest):
            P_new = InsertRelocation(P_old, c, dest, after_freeze=True)
            if Feasible(P_new):
                candidates.append(CreateCandidate("container_repair", P_new))

    return TopKByFastScore(candidates, K_container, P_old)   # đã sửa: bổ sung P_old
```

Default:

```text
K_dest = 5
K_container = 20
```

---

# 18. Pseudocode: GenerateResourceReassignment

> **Chữ ký và pseudocode chuẩn để code: xem mục G.2** (nhận thêm `YardState` và `K` tường minh; R1–R3 dưới đây tương ứng phần lớn với G.2 nhưng G.2 dùng `IsActionFeasibleWithCrane`/`ResourceConflictPenalty` đủ tham số). Bản dưới đây thiếu `P_old` khi gọi `TopKByFastScore` — đã sửa ở dòng cuối.

```text
Function GenerateResourceReassignment(P_old, CraneState, ResourceEvents):
    candidates = []

    # R1: single-action reassignment
    for action in RepairableActions(P_old):
        for yc in CraneState.cranes:
            if action.assigned_crane == yc.id:
                continue
            if IsCraneFeasible(yc, action, CraneState):
                P_new = copy(P_old)
                P_new[action.id].assigned_crane = yc.id
                P_new = RecomputeActionTimes(P_new, CraneState)
                if ResourceFeasible(P_new, CraneState):
                    candidates.append(CreateCandidate("resource_reassignment", P_new))

    # R2: block-level workload sharing
    overloaded_blocks = DetectHighWorkloadBlocks(P_old, CraneState)
    for B in overloaded_blocks:
        actions_B = ActionsInBlock(P_old, B)
        available_cranes = FindAvailableCranesNearBlock(CraneState, B)
        for yc in available_cranes:
            P_new = copy(P_old)
            P_new = ShareBlockWorkload(P_new, block=B, helper_crane=yc)
            P_new = RecomputeActionTimes(P_new, CraneState)
            if ResourceFeasible(P_new, CraneState):
                candidates.append(CreateCandidate("resource_reassignment", P_new))

    # R3: remove assignments from unavailable crane
    unavailable = [yc for yc in CraneState.cranes if yc.status in {"unavailable", "failed"}]
    for yc_bad in unavailable:
        P_new = copy(P_old)
        for action in ActionsAssignedTo(P_new, yc_bad.id):
            yc_alt = NearestFeasibleCrane(action, CraneState)
            if yc_alt is None:
                continue
            P_new[action.id].assigned_crane = yc_alt.id
        P_new = RecomputeActionTimes(P_new, CraneState)
        if ResourceFeasible(P_new, CraneState):
            candidates.append(CreateCandidate("resource_reassignment", P_new))

    return TopKByFastScore(candidates, K_resource, P_old)   # đã sửa: bổ sung P_old
```

Default:

```text
K_resource = 20
```

---

# 19. Pseudocode: GenerateJobResequencing

> **Chữ ký và pseudocode chuẩn để code: xem mục G.3** (gộp `RetrievalInfo`/`ExecutionFeedback` thành `Events`, nhận `freeze_horizon` và `K` tường minh, bỏ bớt case S4 "group by block" để giảm phạm vi). Bản dưới đây thiếu `P_old` khi gọi `TopKByFastScore` — đã sửa ở dòng cuối. Dùng tên tham số `K_sequence` thống nhất (không dùng `K_schedule`, xem mục 31).

```text
Function GenerateJobResequencing(P_old, RetrievalInfo, ExecutionFeedback, CraneState):
    candidates = []
    tail = RepairableTail(P_old)

    # S1: move urgent retrieval earlier
    urgent_containers = GetUrgentContainers(RetrievalInfo)
    for c in urgent_containers:
        pos = PositionOfRetrieval(P_old, c)
        if pos is not None and pos > FreezeEnd(P_old):
            new_pos = max(FreezeEnd(P_old) + 1, pos - r_advance)
            P_new = MoveAction(P_old, pos, new_pos)
            if Feasible(P_new):
                candidates.append(CreateCandidate("job_resequencing", P_new))

    # S2: delay low-priority relocation
    low_priority_actions = FindLowPriorityActions(P_old, RetrievalInfo)
    for a in low_priority_actions:
        P_new = MoveActionAfterUrgentSet(P_old, a)
        if Feasible(P_new):
            candidates.append(CreateCandidate("job_resequencing", P_new))

    # S3: local swap within repairable tail
    for (i, j) in SamplePairs(tail, M_pairs):
        P_new = SwapActions(P_old, i, j)
        if Feasible(P_new):
            P_new = RecomputeActionTimes(P_new, CraneState)
            if ResourceFeasible(P_new, CraneState):
                candidates.append(CreateCandidate("job_resequencing", P_new))

    # S4: group actions by block to reduce crane travel
    for block in BlocksWithManyActions(P_old):
        P_new = GroupActionsByBlock(P_old, block)
        if Feasible(P_new):
            P_new = RecomputeActionTimes(P_new, CraneState)
            candidates.append(CreateCandidate("job_resequencing", P_new))

    return TopKByFastScore(candidates, K_sequence, P_old)   # đã sửa: bổ sung P_old
```

Default:

```text
r_advance = 3
M_pairs = 50
K_sequence = 20
```

---

# 20. Pseudocode: GenerateWaitNoOp

> **Chữ ký và pseudocode chuẩn để code: xem mục G.4** — bổ sung thêm case W3 "freeze thêm action khi instability risk cao" (nhận thêm `StateReliability` để tính low-confidence, dùng `Diagnosis.instability_risk` cho W3). Bản dưới đây chỉ có 2/3 case (W1, W2).

```text
Function GenerateWaitNoOp(P_old, diagnosis):
    candidates = []

    # Always include keep-old-plan candidate
    candidates.append(CreateCandidate("wait_noop", P_old))

    # If low confidence, add explicit wait-for-information candidate
    if diagnosis.low_confidence == True:
        P_wait = copy(P_old)
        P_wait.metadata["decision"] = "WAIT_FOR_MORE_INFORMATION"
        P_wait.metadata["wait_steps"] = default_wait_steps
        candidates.append(CreateCandidate("wait_noop", P_wait))

    return candidates
```

Default:

```text
default_wait_steps = 1 or 2 decision epochs
```

---

# 21. Pseudocode: GenerateLimitedHybrid

> **Chữ ký và pseudocode chuẩn để code: xem mục G.5** — thêm `max_hybrid_total` làm trần early-stop khi duyệt (khác `K_hybrid`, xem mục 31), và nhận thêm `CraneState`/`YardState` để truyền vào `MergePlans` (mục G.6, cần hai state này để gọi `RecomputeActionTimes` sau khi merge).

```text
Function GenerateLimitedHybrid(existing_candidates, max_families=2):
    hybrids = []

    groups = GroupByFamily(existing_candidates)

    for family_1 in groups:
        for family_2 in groups:
            if family_1 >= family_2:
                continue
            for c1 in TopCandidates(groups[family_1], K_family):
                for c2 in TopCandidates(groups[family_2], K_family):
                    P_hybrid = MergePlans(c1.plan, c2.plan)
                    if P_hybrid is None:
                        continue
                    if CountFamilies(P_hybrid) > max_families:
                        continue
                    if Feasible(P_hybrid) and ResourceFeasible(P_hybrid):
                        hybrids.append(CreateCandidate("limited_hybrid", P_hybrid))

    return TopKByFastScore(hybrids, K_hybrid, P_old)   # đã sửa: bổ sung P_old
```

Default:

```text
max_families = 2
K_family = 5
K_hybrid = 10
```

Merge rule:

```text
If two candidates modify the same action in conflicting ways, reject hybrid.
If one candidate changes destination and another changes crane assignment for same action, merge allowed.
If both candidates change ordering differently, reject hybrid.
```

---

# 22. Pseudocode: GenerateSafeRepair

> **Chữ ký và pseudocode chuẩn để code: xem mục G.7** — nhận thêm `YardState`, và khi fallback trả `SafeHoldPlan(P_old, reason=...)` có kèm lý do cụ thể (bản dưới đây chỉ trả `SafeHoldPlan(P_old)` không có `reason`).

```text
Function GenerateSafeRepair(P_old, SafetyConstraints, CraneState):
    P_safe = copy(P_old)

    for action in P_safe.actions:
        if ViolatesHardSafety(action, SafetyConstraints):
            if CanRemove(action):
                RemoveAction(P_safe, action)
            else:
                action.status = "MANUAL_REVIEW"

        if ViolatesResourceHardConstraint(action, CraneState):
            yc_alt = NearestFeasibleCrane(action, CraneState)
            if yc_alt is not None:
                action.assigned_crane = yc_alt.id
            else:
                action.status = "SAFE_HOLD"

    if Feasible(P_safe):
        return P_safe
    else:
        return SafeHoldPlan(P_old)
```

---

# 23. ResourceCost pseudocode

> Bản dưới đây thiếu `SafetyConstraints` khi gọi `ResourceConflictPenalty` — hàm này cần `SafetyConstraints` để check hard/soft zone conflict (xem định nghĩa đầy đủ ở mục C.2 và mục D.1–D.4, đó là bản chuẩn để code).

```text
Function ResourceCost(P, CraneState, SafetyConstraints):
    travel = 0
    idle = 0
    workloads = []
    conflict = 0

    for yc in CraneState.cranes:
        seq = ActionsAssignedTo(P, yc.id)
        loc_prev = yc.current_location
        work_time = 0
        travel_time = 0

        for action in seq:
            loc = ActionLocation(action)
            t = TravelTime(yc, loc_prev, loc)
            travel_time += t
            work_time += HandlingTime(action, yc)
            loc_prev = loc

        travel += travel_time
        workloads.append(work_time + travel_time)
        idle += max(0, PlanningHorizon(P) - work_time - travel_time)

    conflict = ResourceConflictPenalty(P, CraneState, SafetyConstraints)   # đã sửa: bổ sung SafetyConstraints
    imbalance = Std(workloads)

    return alpha_r * travel + beta_r * idle + gamma_r * imbalance + delta_r * conflict
```

---

# 24. ResourceStability pseudocode

> Bản dưới đây là bản sơ khởi, **đã được thay bằng bản đầy đủ hơn ở mục E.2** (patch) — bản E.2 xử lý thêm case action bị thêm/xóa (`zeta_ar`) mà bản này bỏ sót. Dùng mục E.2 làm nguồn duy nhất khi code; giữ lại đây chỉ để tham khảo ý tưởng ban đầu.

```text
Function ResourceStability(P_new, P_old, rho_res):
    total = 0

    for action_new in P_new.actions:
        action_old = FindAction(P_old, action_new.action_id)
        if action_old is None:
            continue

        pos = Position(action_new, P_new)
        w = exp(-rho_res * pos)

        d = 0
        if action_new.assigned_crane != action_old.assigned_crane:
            d += 1
        if action_new.estimated_start != action_old.estimated_start:
            d += zeta_t * abs(action_new.estimated_start - action_old.estimated_start)
        if Zone(action_new) != Zone(action_old):
            d += zeta_z

        total += w * d

    return total
```

---

# 25. InterventionComplexity pseudocode

```text
Function InterventionComplexity(candidate):
    families = CountFamilies(candidate)
    changed_actions = CountChangedActions(candidate.plan, P_old)
    changed_resources = CountChangedCraneAssignments(candidate.plan, P_old)
    new_actions = CountInsertedActions(candidate.plan, P_old)

    if families > 2:
        return infinity

    return families + xi_1 * changed_actions + xi_2 * changed_resources + xi_3 * new_actions
```

---

# 26. Implementation Appendix A — Data schemas

## 26.1 CraneState schema

> **Schema chuẩn duy nhất** (đã hợp nhất với bản "Detailed CraneState schema" ở mục H.1 — bản đó dùng `current_location` là string + `speed_factor` đơn, khác với bản này; dùng bản dưới đây khi code). Giữ `current_location` dạng object (khớp với "Location representation" mục 12.1/A.2) và **tách riêng `speed` (tốc độ gốc) với `slowdown_factor` (hệ số tạm thời do ResourceEvent)** để khi crane "recovered" chỉ cần đặt lại `slowdown_factor = 1.0`, không mất thông tin `speed` gốc. Bổ sung `capacity` và `stack_to_zone_map` từ mục H.1.

```json
{
  "timestamp": 120,
  "cranes": [
    {
      "id": "YC1",
      "type": "yard_crane",
      "status": "available",
      "current_location": {
        "block": "B1",
        "bay": 4,
        "row": 0,
        "zone": "Z1"
      },
      "working_zones": ["Z1", "Z2"],
      "available_from": 120,
      "speed": 1.0,
      "slowdown_factor": 1.0,
      "assigned_actions": ["A1", "A2"],
      "max_workload": 30,
      "capacity": {
        "max_weight": 40,
        "allowed_container_types": ["20ft", "40ft"]
      },
      "source": "simulator",
      "confidence": 1.0
    }
  ],
  "travel_time_matrix": {
    "Z1": {"Z1": 0, "Z2": 5, "Z3": 10},
    "Z2": {"Z1": 5, "Z2": 0, "Z3": 6},
    "Z3": {"Z1": 10, "Z2": 6, "Z3": 0}
  },
  "stack_to_zone_map": {
    "S01": "Z1",
    "S02": "Z1",
    "S03": "Z2",
    "S04": "Z3"
  },
  "time_unit": "simulation_step",
  "conflict_zones": [
    {
      "zone_a": "Z1",
      "zone_b": "Z1",
      "min_time_gap": 1,
      "type": "hard"
    }
  ]
}
```

Quy ước cập nhật `speed`/`slowdown_factor` khi có `ResourceEvent`:

```text
crane_slowdown   -> slowdown_factor = event.slowdown_factor (hoặc event.new_speed_factor / speed, xem mục 26.2)
crane_recovered  -> slowdown_factor = 1.0 (khôi phục, không đổi speed gốc)
```

Tốc độ hiệu dụng dùng trong `TravelTime`/`HandlingTime` luôn là `speed × slowdown_factor` (mục 12.3), không dùng trực tiếp `speed_factor` đơn lẻ như ở mục H.1.

## 26.2 ResourceEvent schema

```json
{
  "event_id": "RE_001",
  "time": 130,
  "type": "crane_slowdown",
  "crane_id": "YC1",
  "affected_zone": "Z1",
  "slowdown_factor": 0.5,
  "duration_steps": 5,
  "confidence": 0.9,
  "source": "simulator"
}
```

Supported resource event types:

```text
crane_slowdown
crane_unavailable
crane_recovered
workload_spike
zone_conflict
travel_time_increase
operator_reject_resource_assignment
```

## 26.3 InterventionCandidate schema

```json
{
  "candidate_id": "IC_001",
  "family": "resource_reassignment",
  "families": ["resource_reassignment"],
  "plan": {
    "plan_id": "P_new_001",
    "actions": []
  },
  "modified_actions": ["A4", "A7"],
  "changed_resources": ["YC1", "YC2"],
  "new_actions": [],
  "expected_costs": {
    "C_op": 4.2,
    "C_stab": 1.0,
    "D_resource": 0.6,
    "C_data": 0.3,
    "C_exec": 0.2,
    "C_res": 3.5,
    "C_safety": 0.0,
    "C_int": 1.4,
    "J_total": 10.35
  },
  "feasibility": {
    "hard_safety_valid": true,
    "resource_valid": true,
    "timeout": false
  },
  "metadata": {
    "diagnosis": "resource_bottleneck",
    "generation_method": "single_action_reassignment"
  }
}
```

## 26.4 Extended Action schema

> Dùng `from_zone`/`to_zone` tách biệt (khớp mục A.2 — "location chuẩn") thay vì một field `zone` đơn — vì `TravelTime` cần biết cả điểm đi lẫn điểm đến để tra `travel_time_matrix`.

```json
{
  "action_id": "A7",
  "type": "RELOCATE",
  "container": "C8",
  "from_stack": "S2",
  "to_stack": "S5",
  "from_zone": "Z1",
  "to_zone": "Z2",
  "assigned_crane": "YC1",
  "estimated_start": 15,
  "estimated_finish": 18,
  "commit_status": "planned",
  "priority": "normal"
}
```

## 26.5 Resource SafetyConstraint schema

```json
{
  "constraint_id": "RES_SAFE_001",
  "type": "hard",
  "description": "Crane cannot be assigned outside its working zones",
  "check": "action.zone in crane.working_zones"
}
```

```json
{
  "constraint_id": "RES_SAFE_002",
  "type": "hard",
  "description": "Two cranes cannot occupy the same conflict zone at overlapping time windows",
  "check": "not overlap(action_i.zone, action_j.zone, action_i.time, action_j.time)"
}
```

```json
{
  "constraint_id": "RES_SAFE_003",
  "type": "soft",
  "description": "Avoid assigning too many consecutive actions to the same crane when another crane is idle",
  "weight": 1.0,
  "check": "workload_imbalance < threshold"
}
```

## 26.6 Operator feedback schema

```json
{
  "feedback_id": "OF_001",
  "time": 145,
  "candidate_id": "IC_001",
  "operator_action": "reject",
  "reason_category": "resource_assignment_unrealistic",
  "reason_text": "YC2 is physically blocked by another operation",
  "fallback_required": true
}
```

---

# 27. Benchmark specification

Paper 3 benchmark extends Paper 2 benchmark by adding resource/crane configuration and resource events.

## 27.1 Instance schema

```json
{
  "instance_id": "MISR_small_0001",
  "layout_id": "L_small_A",
  "yard_state": {},
  "retrieval_info": {},
  "current_plan": {},
  "execution_feedback_stream": [],
  "resource_event_stream": [],
  "crane_state": {},
  "safety_constraints": [],
  "scenario_type": "resource_bottleneck",
  "uncertainty_level": "medium",
  "resource_level": "two_cranes",
  "seed": 42
}
```

## 27.2 Instance counts

| Split | Layouts | Instances/layout | Total | Purpose |
|---|---:|---:|---:|---|
| Small | 1 | 100 | 100 | MVP, exhaustive/proxy feasible |
| Medium | 1 | 100 | 100 | Main evaluation |
| Large | 1 | 50 | 50 | Scalability |
| Cross-layout | 3 | 50 | 150 | Generalization |

Total default benchmark:

```text
400 instances
```

## 27.3 Resource scenarios

| Scenario | Description |
|---|---|
| S1 Normal | Multiple cranes available, no disruption |
| S2 Crane slowdown | One crane speed reduced |
| S3 Crane unavailable | One crane unavailable for several steps |
| S4 Workload imbalance | One block/zone receives high workload |
| S5 Zone conflict | Two cranes likely to conflict in same zone |
| S6 Mixed | Retrieval + execution + resource events |

## 27.4 Resource event generator parameters

Default:

```text
p_resource_event = 0.25 per decision epoch
p_slowdown       = 0.30
p_unavailable    = 0.20
p_recovered      = 0.10
p_workload_spike = 0.25
p_zone_conflict  = 0.10
p_travel_increase= 0.05
```

Severity:

```text
low:    slowdown_factor ∈ [0.7, 0.9], duration 1–2 steps
medium: slowdown_factor ∈ [0.4, 0.7], duration 3–5 steps
high:   slowdown_factor ∈ [0.2, 0.4], duration 6–10 steps
```

Crane unavailable duration:

```text
low:    1–2 steps
medium: 3–5 steps
high:   6–10 steps
```

### 27.4.1 Căn cứ và giới hạn của các tham số trên

Giống Paper 1 (mục 39.1.1) và Paper 2 (mục 39.3.1), toàn bộ xác suất/severity resource event ở trên là **giả định heuristic**, chưa hiệu chỉnh từ dữ liệu vận hành crane thật (tần suất crane hỏng/chậm thật, thời lượng bảo trì thật...). Trước khi đưa vào paper chính thức:

```text
1. Nếu có log crane thật (maintenance log, telemetry), ước lượng lại
   p_slowdown/p_unavailable/p_recovered/... từ đó.
2. Nếu không có, giữ nguyên nhưng:
   a. Gọi rõ là "assumed resource-disruption distribution" trong paper.
   b. Bắt buộc chạy sanity checks SC1-SC5 của Paper 3 — xem mục 27.6 ngay
      dưới đây (tương tự mục 20/49 Paper 1, mục 42 Paper 2).
   c. Đưa "calibration against real crane logs" vào Limitations (mục 37).
```

## 27.5 Combining Paper 2 events + Paper 3 events

Paper 3 event stream:

```text
EventStream = RetrievalEvents + ExecutionFeedbackEvents + ResourceEvents
```

Default ratios:

```text
retrieval events : 40%
execution events : 30%
resource events  : 30%
```

Mixed scenario ratios:

```text
retrieval events : 30%
execution events : 30%
resource events  : 40%
```

## 27.6 Benchmark sanity checks (mới — mục 37 khẳng định có sanity check nhưng bản trước chưa định nghĩa)

Tương tự SC1-SC5 của Paper 1/2, kiểm tra trước khi chạy full experiment:

```text
SC1 — Không quá dễ:
    B1 (Paper-2 EA-SAR-CRP, không có resource intervention) phải suy giảm
    rõ rệt khi bật resource event so với khi tắt (S1 Normal), nếu không
    benchmark chưa đủ khó để cho thấy giá trị của resource intervention.

SC2 — Không quá khó:
    fallback_rate (Safe Hold/Manual Review, mục 30) < 30% ở resource_level
    "two_cranes"/uncertainty "medium".

SC3 — Phân bố scenario hợp lý:
    Không scenario nào trong S1-S6 (mục 27.3) chiếm > 50% số instance trừ
    khi đang cố tình stress-test một scenario.

SC4 — Phân bố diagnosis hợp lý:
    Cả 6 diagnosis category (mục 15) đều xuất hiện với tần suất > 5% trong
    benchmark medium/mixed — nếu một diagnosis gần như không bao giờ kích
    hoạt, family tương ứng (vd. resource reassignment) sẽ không được test.

SC5 — Hybrid được dùng nhưng không áp đảo:
    hybrid_usage_rate (mục 33, Intervention metrics) nằm trong khoảng
    5%-40% ở scenario S6 Mixed — nếu gần 0% thì rule "reject nếu
    #families>2" (mục 14) có thể đang chặn hết hybrid; nếu gần 100% thì
    nghi ngờ single-family baseline (B2, B3) bị đặt bất lợi một cách giả tạo.
```

---

# 28. Ground truth / proxy

## Small instances

Use exhaustive or bounded enumeration over:

```text
container repair candidates
resource reassignment candidates
job resequencing candidates
wait/no-op
limited hybrid pairs
```

Because full joint optimization is expensive, exhaustive search is limited to candidate set generated by all baseline generators with extended candidate budget.

Report as:

```text
offline exhaustive candidate-set optimum
```

Do not claim global optimum.

## Medium/Large instances

Use extended-time full reoptimization proxy:

```text
time limit = 300 seconds
candidate budget = 10x online budget
families = all intervention families
hybrid allowed up to 2 families
```

Report as:

```text
offline high-quality proxy
```

## Evaluation note

MISR-Yard is not required to beat the offline proxy in operational cost. It should show better online trade-off under runtime, stability and complexity constraints.

---

# 29. Baselines

| ID | Baseline | Reference/Source | Description | Difference from MISR-Yard |
|---|---|---|---|---|
| B1 | Paper-2 EA-SAR-CRP | Paper 2 | Execution-aware stable replanning without multi-intervention orchestration | No resource intervention family |
| B2 | Container-only Repair | Paper 1–2 components | Only container repair candidates | Cannot reassign resources or resequence jobs strategically |
| B3 | Resource-only Repair | Heuristic resource reassignment | Only reassign crane/resource to reduce resource cost | Cannot modify container plan or job order |
| B4 | Sequential CRP → Resource | Sequential optimization baseline | First repair container plan, then assign cranes greedily | No joint intervention selection |
| B5 | Full Reoptimization | Shin et al. 2026-style CRP solver + resource enumeration/proxy | Reoptimize all feasible parts under resource model | High instability/complexity |
| B6 | Rule-based Intervention | Expert heuristic | If resource bottleneck then reassign crane; if retrieval disruption then container repair; if low confidence then wait | Fixed rules, no cost-based orchestration |
| B7 | MISR-Yard | Proposed | Diagnosis-guided multi-intervention orchestration | Full proposed method |

## B3 Resource-only Repair detail

Resource-only baseline:

```text
1. Keep container action sequence fixed.
2. Keep relocation destinations fixed.
3. Only change assigned_crane and action timing.
4. Minimize C_res + D_resource.
5. Reject if hard resource/safety conflict.
```

## B6 Rule-based Intervention detail

Rule-based policy:

```text
if low_confidence:
    choose wait/no-op
elif safety_conflict:
    choose safe repair
elif resource_bottleneck or workload_imbalance:
    choose resource reassignment
elif retrieval_disruption:
    choose container repair
elif execution_failure:
    choose job resequencing or container repair
else:
    keep old plan
```

No joint objective optimization.

---

# 30. Timeout protocol

Paper 3 has more candidate families than Paper 2, so timeout is slightly increased.

| Size | Paper 2 timeout | Paper 3 timeout | Reason |
|---|---:|---:|---|
| Small | 2s | 3s | Additional resource evaluation |
| Medium | 8s | 12s | Resource/resequencing candidates |
| Large | 40s | 60s | Multi-family candidate generation |

Fallback:

```text
If timeout:
    return best feasible candidate so far
If no feasible candidate:
    GenerateSafeRepair()
If SafeRepair fails:
    Keep Old Plan
If Keep Old Plan infeasible:
    Safe Hold / Manual Review
```

Metrics:

```text
mean runtime
P95 runtime
timeout rate
fallback rate
candidate count per family
```

---

# 31. Parameter table

Bảng này là nguồn duy nhất cho tham số Paper 3 (đồng bộ với mục I — patch — không còn khác nhau giữa hai bảng).

| Parameter | Meaning | Default | Range/Sensitivity |
|---|---|---:|---|
| λ | Container-plan stability weight (C_stab, kế thừa `D(P,P_old)` Paper 1) | 1.0 | 0.5, 1.0, 2.0 |
| λ_res | Resource/crane stability weight (D_resource, mục 13) — **mới, trước đây thiếu khỏi J(a)** | 1.0 | 0.5, 1.0, 2.0 |
| π | Data confidence cost weight (C_data, kế thừa Paper 1/2) — **mới, trước đây thiếu khỏi J(a)** | 0.5 | 0, 0.5, 1.0 |
| μ | Execution cost weight (C_exec) — **không phải trọng số C_data như Paper 1/2**, xem ghi chú mục 11 | 1.0 | 0.5, 1.0, 2.0 |
| ν | Resource cost weight (C_res) — khái niệm mới của Paper 3, **không phải trọng số C_exec như Paper 2** | 1.0 | 0.5, 1.0, 2.0 |
| ω | Safety cost weight | 5.0 | 1.0, 5.0, 10.0 |
| η | Intervention complexity weight | 0.5 | 0.1, 0.5, 1.0 |
| α_r | Travel cost weight (trong C_res) | 1.0 | fixed |
| β_r | Idle cost weight (trong C_res) | 0.5 | 0.25, 0.5, 1.0 |
| γ_r | Imbalance cost weight (trong C_res) | 1.0 | 0.5, 1.0, 2.0 |
| δ_r | Soft conflict weight (trong C_res) | 10.0 | 5, 10, 20 |
| ρ_res | Time-weight decay cho D_resource (mục 13/E.2) — **độc lập với `ρ = 0.05` của Paper 1** dùng cho C_stab | 0.1 | 0.05, 0.1, 0.2 |
| ζ_t | Start-time-change penalty trong D_resource | 0.5 | fixed |
| ζ_z | Zone-change penalty trong D_resource | 1.0 | fixed |
| ζ_ar | Added/removed-job penalty trong D_resource | 2.0 | fixed |
| K_container | Max container candidates | 20 | 10, 20, 50 |
| K_resource | Max resource candidates | 20 | 10, 20, 50 |
| K_sequence | Max resequencing candidates (tên thống nhất, không dùng `K_schedule`) | 20 | 10, 20, 50 |
| K_hybrid | Max hybrid candidates **trả về sau cùng** (sau TopKByFastScore) | 10 | 5, 10, 20 |
| max_hybrid_total | Trần số hybrid sinh ra **trong lúc duyệt** (early-stop, lớn hơn K_hybrid vì lọc bớt sau) | 50 | 25, 50, 100 |
| K_wait | Số candidate wait/no-op tối đa — mang tính mô tả (W1-W3 tự nhiên ≤ 3, không phải bộ lọc chủ động) | 3 | fixed |
| max_families | Max intervention families in hybrid | 2 | fixed for Paper 3 |
| τ | Gain threshold | 0.01 × J(old) | 0.005, 0.01, 0.02 |

---

# 32. Experiments

## Exp 1 — MVP test

Setup:

```text
1 small layout
100 small instances
3 baselines: B1, B5, B7
```

Goal:

> Check whether MISR-Yard has better total trade-off than Paper-2 SAR and full reoptimization.

Decision gate:

```text
Proceed only if:
- MISR-Yard reduces total J vs B1
- MISR-Yard reduces churn vs B5
- Runtime within timeout for >95% instances
```

## Exp 2 — Main comparison

Baselines:

```text
B1–B7
```

Instances:

```text
100 small + 100 medium + 50 large
```

## Exp 3 — Resource scenarios

Test S1–S6 resource scenarios.

## Exp 4 — Cross-layout validation

Protocol:

```text
Tune parameters on Layout A only.
Evaluate Layouts B and C with same parameters without retuning.
Report performance drop.
```

## Exp 5 — Ablation study

Ablations:

```text
A1 No resource cost
A2 No resource stability
A3 No wait/no-op
A4 No diagnosis-guided generation
A5 No hybrid intervention
A6 No intervention complexity cost
```

## Exp 6 — Runtime/scalability

Report:

```text
candidate count
mean/P95 runtime
timeout rate
fallback rate
per-family generation time
```

## Statistical Protocol (bắt buộc, dùng chung nguyên tắc với Paper 1 mục 23.6 / Paper 2 mục 44)

```text
Số lần lặp:
    Mỗi (instance, scenario S1-S6, baseline) chạy với >= 20 random seed
    (kiểm soát retrieval + execution + resource event stream, mục 27.5).

Báo cáo:
    Mean +/- 95% CI cho mọi metric ở mục 33.

Kiểm định ý nghĩa:
    Wilcoxon signed-rank test (paired) khi so MISR-Yard (B7) với từng
    baseline B1-B6 trên total cost J(a) và resource conflict/safety
    violation rate.
    Hiệu chỉnh Holm-Bonferroni cho 6 so sánh cùng lúc.

Effect size:
    Báo cáo effect size bên cạnh p-value, đặc biệt cho hard-safety-
    violation rate và fallback rate (rare-event metrics).

Ablation (Exp 5, mục 32):
    Áp dụng cùng protocol trên (mỗi ablation A1-A6 vs MISR-Yard đầy đủ).
```

---

# 33. Metrics

## Operational metrics

```text
relocations
retrieval delay proxy
failed actions
total plan cost
completion proxy
```

## Stability metrics

```text
changed actions
changed destinations
changed order
plan churn rate
changed committed actions
```

## Resource metrics

```text
crane travel time
crane idle time
workload imbalance
changed crane assignments
resource conflict count
resource infeasibility rate
```

## Intervention metrics

```text
selected intervention family distribution
hybrid usage rate
wait/no-op rate
intervention complexity
```

## Safety/runtime metrics

```text
hard safety violation rate
soft safety penalty
fallback rate
manual review rate
mean runtime
P95 runtime
timeout rate
```

---

# 34. Walkthrough example

Initial plan:

```text
A1: retrieve C1, YC1, Z1
A2: relocate C8 S2→S5, YC1, Z1
A3: retrieve C2, YC1, Z1
A4: relocate C9 S3→S6, YC1, Z1
A5: retrieve C3, YC1, Z1
```

Event:

```text
ResourceEvent: YC1 slowdown_factor = 0.4 for 5 steps
RetrievalEvent: C3 becomes urgent
CraneState: YC2 available in nearby Z2
```

Diagnosis:

```text
resource_bottleneck = true
retrieval_disruption = true
workload_imbalance = true
```

Candidates:

```text
C1 Container repair: move C3 retrieval earlier
C2 Resource reassignment: assign A4/A5 to YC2
C3 Job resequencing: swap A5 before A4
C4 Wait/no-op: keep old plan
C5 Hybrid: move C3 earlier + assign A5 to YC2
```

Evaluation:

| Candidate | C_op | C_stab | C_exec | C_res | C_safety | C_int | J |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1 | 5.0 | 1.5 | 1.0 | 8.0 | 0 | 1.2 | 16.7 |
| C2 | 6.0 | 2.0 | 1.0 | 3.0 | 0 | 1.4 | 13.4 |
| C3 | 4.8 | 2.5 | 1.0 | 7.0 | 0 | 1.2 | 16.5 |
| C4 | 8.5 | 0.0 | 2.0 | 9.0 | 0 | 1.0 | 20.5 |
| C5 | 4.5 | 2.8 | 1.0 | 3.2 | 0 | 2.0 | 13.5 |

Decision:

```text
Choose C2 if lower complexity preferred.
Choose C5 if operational urgency of C3 is high.
```

This example illustrates why Paper 3 is not only resource-aware: it compares container, resource, sequence, wait and hybrid interventions.

---

# 35. Implementation roadmap

## Phase 0 — Reuse Paper 2 codebase

```text
load YardState
load CurrentPlan
load RetrievalInfo
load ExecutionFeedback
run EA-SAR-CRP baseline
```

## Phase 1 — Add CraneState and ResourceCost

```text
implement CraneState schema
implement dist()
implement TravelTime()
implement ResourceCost()
```

## Phase 2 — Add candidate generators

```text
GenerateResourceReassignment
GenerateJobResequencing
GenerateWaitNoOp
GenerateLimitedHybrid
```

## Phase 3 — Add MISR selector

```text
EvaluateCandidate
SelectBestIntervention
Fallback protocol
```

## Phase 4 — MVP

```text
1 small layout
100 small instances
B1, B5, B7 only
```

## Phase 5 — Full benchmark

```text
all baselines
all layouts
all ablations
runtime report
```

---

# 36. Q1 positioning

Paper 3 should be written as a decision-orchestration paper, not as a crane scheduling paper.

Correct positioning:

> Existing CRP and crane-scheduling methods usually optimize one decision layer at a time. MISR-Yard studies a higher-level question: when an operational disturbance occurs, should the system repair the container plan, reassign resources, resequence jobs, wait for more information, or apply a limited hybrid intervention?

Incorrect positioning:

> We solve multi-crane scheduling better than previous methods.

---

# 37. Limitations and future work

Limitations:

1. Resource model is simplified and does not claim full crane scheduling optimality.
2. Benchmark is synthetic, though sanity checks (mục 27.6) and cross-layout validation are included; resource-event probabilities/severity are heuristic, not calibrated against real crane logs (mục 27.4.1).
3. Hybrid intervention is limited to two families.
4. Real terminal deployment is future work.
5. Related Work grounding still needs concrete citations on hierarchical/multi-option decision-making literature (mục 5).
6. B5 baseline depends on Shin et al. 2026 (CRP_RL-style), which still needs citation verification (same requirement as Paper 1 mục 3 / Paper 2 mục 4).

Future work:

1. Full multi-crane scheduling integration.
2. Truck appointment/demand intervention family.
3. Real terminal data calibration.
4. Human operator study.
5. Learning intervention selection from outcome data.

---

# 38. Final conclusion

MISR-Yard is the natural Paper 3 after SAR-CRP and EA-SAR-CRP.

Paper 1:

> Stable under evolving retrieval information.

Paper 2:

> Robust under imperfect execution.

Paper 3:

> Strategic under multiple intervention choices.

Final claim:

> **MISR-Yard extends stable adaptive CRP replanning by explicitly modeling multiple intervention families—container repair, resource reassignment, job resequencing, wait/no-op and limited hybrid repair—and selecting the most appropriate intervention based on a joint assessment of operational efficiency, stability, execution risk, resource feasibility, safety and intervention complexity.**



---

# ULTRA-FINAL CODE-LEVEL PATCH
## MISR-Yard Paper 3 — Implementation Details Needed Before Coding

Phần này bổ sung các chi tiết còn thiếu để lập trình viên có thể code thống nhất. Các nội dung dưới đây **không thay đổi hướng nghiên cứu**, mà chỉ làm rõ các hàm con, schema, tham số và protocol triển khai.

---

# A. Quy ước distance và travel time

## A.1. Nguyên tắc chung

Paper 3 hỗ trợ hai cách tính travel time cho crane:

```text
Priority 1: dùng travel_time_matrix nếu có.
Priority 2: nếu không có matrix, fallback sang block-aware Manhattan distance.
```

Để tránh mơ hồ khi implement, quy ước mặc định là:

> **Nếu `travel_time_matrix` tồn tại trong `CraneState`, mọi tính toán travel time phải dùng matrix. Chỉ dùng block-aware Manhattan khi matrix bị thiếu.**

---

## A.2. Location representation

Mỗi action phải có location chuẩn:

```json
{
  "action_id": "A12",
  "type": "RELOCATE",
  "container": "C17",
  "from_stack": "S03",
  "to_stack": "S08",
  "from_zone": "Z1",
  "to_zone": "Z3",
  "assigned_crane": "YC1",
  "estimated_start": 15,
  "estimated_finish": 18,
  "commit_status": "planned"
}
```

Trong đó:

- `from_stack`, `to_stack`: vị trí chi tiết ở mức stack.
- `from_zone`, `to_zone`: vùng làm việc của crane.
- `to_zone` được dùng ưu tiên cho travel-time matrix.
- Nếu không có `zone`, hệ thống suy ra từ `stack_to_zone_map`.

---

## A.3. Travel-time matrix schema

```json
{
  "travel_time_matrix": {
    "Z1": {"Z1": 0, "Z2": 5, "Z3": 10},
    "Z2": {"Z1": 5, "Z2": 0, "Z3": 6},
    "Z3": {"Z1": 10, "Z2": 6, "Z3": 0}
  }
}
```

Ý nghĩa:

```text
travel_time_matrix[zone_a][zone_b] = thời gian crane di chuyển từ zone_a sang zone_b.
```

Quy ước đơn vị trong Paper 3:

> Time units in the travel-time matrix are normalized to simulation steps. All time-related fields, including `estimated_start`, `estimated_finish`, `available_from`, `handling_time`, `wait_duration`, `duration_steps`, and `timeout`, use the same simulation-step unit unless explicitly stated otherwise.

Nếu triển khai với dữ liệu thực, một simulation step có thể được ánh xạ sang phút hoặc giây, nhưng toàn bộ benchmark phải dùng một đơn vị thống nhất.

---

## A.4. Block-aware Manhattan fallback

Nếu không có `travel_time_matrix`, dùng:

```text
TravelTime(loc1, loc2) =
    w_b   * |block(loc1) - block(loc2)|
  + w_bay * |bay(loc1)   - bay(loc2)|
  + w_row * |row(loc1)   - row(loc2)|
```

Default:

```text
w_b   = 10
w_bay = 1
w_row = 1
```

Lý do: di chuyển khác block thường tốn chi phí lớn hơn nhiều so với di chuyển trong cùng block.

---

## A.5. Pseudocode: TravelTime

> Đã bổ sung tham số `yc` (crane cụ thể) — bản trước không nhận `yc` nên bỏ sót hệ số `speed × slowdown_factor` mà công thức mục 12.3 yêu cầu (`TravelTime(yc,l1,l2) = dist(l1,l2)/speed(yc)`); nếu không chia cho tốc độ crane, một crane bị `crane_slowdown` sẽ không có travel time tăng lên như thiết kế ban đầu.

```text
Function TravelTime(yc, loc1, loc2, CraneState, YardState):
    z1 = ResolveZone(loc1, YardState)
    z2 = ResolveZone(loc2, YardState)
    effective_speed = yc.speed * yc.slowdown_factor

    If CraneState.travel_time_matrix exists:
        If z1 and z2 exist in matrix:
            return CraneState.travel_time_matrix[z1][z2] / effective_speed

    # fallback: block-aware Manhattan
    raw = w_b   * abs(block(loc1) - block(loc2)) \
        + w_bay * abs(bay(loc1)   - bay(loc2)) \
        + w_row * abs(row(loc1)   - row(loc2))

    return raw / effective_speed
```

---

# B. Hàm phụ trợ bắt buộc

## B.1. ActionLocation

Hàm này xác định vị trí chính của một action để tính travel time/resource cost.

```text
Function ActionLocation(action):
    If action.type == "RELOCATE":
        return action.to_stack

    Else if action.type == "RETRIEVE":
        return action.from_stack

    Else if action.type == "STACK":
        return action.to_stack

    Else if action.type == "WAIT":
        return None

    Else:
        return action.location if exists else None
```

Quy ước:

- `RELOCATE`: location chính là destination stack vì crane phải kết thúc ở đó.
- `RETRIEVE`: location chính là source stack vì crane cần lấy container ở đó.
- `WAIT`: không có location mới.

---

## B.2. HandlingTime

```text
Function HandlingTime(action, crane):
    If action.type == "RELOCATE":
        base = handling_time_relocate

    Else if action.type == "RETRIEVE":
        base = handling_time_retrieve

    Else if action.type == "STACK":
        base = handling_time_stack

    Else if action.type == "WAIT":
        base = action.wait_duration if exists else 0

    Else:
        base = handling_time_default

    # Optional extension: container-size adjustment.
    # Paper 3 main experiments may ignore this term for simplicity.
    If action.container exists and action.container.size == "40ft":
        base = base * 1.2

    return base / (crane.speed * crane.slowdown_factor)   # đã sửa: schema chuẩn (mục 26.1) tách speed và slowdown_factor, không dùng speed_factor đơn
```

Default:

```text
handling_time_relocate = 2.0
handling_time_retrieve = 1.0
handling_time_stack    = 1.5
container_40ft_multiplier = 1.2  # optional, not required for main Paper-3 experiments
handling_time_default  = 1.0
```

Nếu chưa có dữ liệu thực, dùng đơn vị normalized simulation step.

---

## B.3. RecomputeActionTimes

Hàm này cập nhật `estimated_start` và `estimated_finish` sau khi đổi crane, đổi sequence hoặc merge plan.

```text
Function RecomputeActionTimes(P, CraneState, YardState):
    # Initialize availability for each crane
    crane_available_time = {}
    crane_current_location = {}

    For each crane yc in CraneState.cranes:
        crane_available_time[yc.id] = yc.available_from
        crane_current_location[yc.id] = yc.current_location

    # Process actions in plan order
    For each action a in P.actions:
        If a.type == "WAIT":
            continue

        If a.assigned_crane is None:
            # leave timing unknown; resource feasibility checker will handle it
            continue

        yc = CraneState.get_crane(a.assigned_crane)

        prev_loc = crane_current_location[yc.id]
        action_loc = ActionLocation(a)

        If action_loc is None:
            travel = 0
        Else:
            travel = TravelTime(yc, prev_loc, action_loc, CraneState, YardState)   # đã sửa: bổ sung yc

        earliest_start = crane_available_time[yc.id] + travel

        If a.estimated_start exists:
            a.estimated_start = max(a.estimated_start, earliest_start)
        Else:
            a.estimated_start = earliest_start

        a.estimated_finish = a.estimated_start + HandlingTime(a, yc)

        crane_available_time[yc.id] = a.estimated_finish
        If action_loc is not None:
            crane_current_location[yc.id] = action_loc

    return P
```

Ghi chú:

- Đây là timing model đơn giản, đủ cho Paper 3.
- Nếu muốn chính xác hơn, Paper sau có thể thay bằng yard-crane scheduler riêng.

---

## B.4. TopKByFastScore

Candidate generation có thể sinh nhiều plan. Ta dùng `fast_score` để lọc nhanh trước khi chạy full evaluation.

```text
fast_score(P) = C_op_proxy(P) + lambda_fast * C_stab_proxy(P) + psi_fast * C_resource_proxy(P)
```

Trong bản tối giản:

```text
fast_score(P) = C_op_proxy(P) + lambda_fast * C_stab_proxy(P)
```

Trong đó:

```text
C_op_proxy(P)       = relocation_count(P) + retrieval_delay_proxy(P)
C_stab_proxy(P)     = number_of_changed_actions(P, P_old)
C_resource_proxy(P) = approximate_crane_travel(P)
```

Pseudocode:

```text
Function TopKByFastScore(candidates, K, P_old):
    scored = []

    For each P in candidates:
        op_proxy = RelocationCount(P) + RetrievalDelayProxy(P)
        stab_proxy = ChangedActionCount(P, P_old)
        res_proxy = ApproximateCraneTravel(P)

        score = op_proxy + lambda_fast * stab_proxy + psi_fast * res_proxy
        scored.append((score, P))

    Sort scored by score ascending
    Return first K plans
```

Default:

```text
lambda_fast = 0.5
psi_fast    = 0.2
```

Full objective `J(a)` vẫn được dùng ở Candidate Evaluator sau đó. `fast_score` chỉ là heuristic lọc candidate.

---

## B.5. CanRemove

Dùng trong `GenerateSafeRepair`.

```text
Function CanRemove(action):
    If action.commit_status == "executed":
        return False

    If action.commit_status == "in_progress":
        return False

    If action.priority == "critical":
        return False

    If action.type == "RETRIEVE" and action.is_urgent == True:
        return False

    Return True
```

Default rule:

> Chỉ được remove action chưa thực thi, chưa in-progress, không critical và không phải urgent retrieval.

---

# C. Resource conflict penalty

## C.1. Conflict types

Resource conflict gồm hai nhóm.

### Hard conflict

Candidate bị reject hoặc penalty vô hạn:

```text
- Hai crane vào cùng conflict zone cùng thời điểm.
- Hai crane vi phạm safety distance.
- Crane được gán action ngoài working zone.
- Crane unavailable nhưng vẫn được gán job.
```

### Soft conflict

Candidate vẫn có thể được chấp nhận nhưng bị phạt:

```text
- Crane workload quá lệch.
- Crane phải di chuyển xa bất thường.
- Crane assignment đổi nhiều so với plan cũ.
- Action gần vùng có risk nhưng không vi phạm hard rule.
```

---

## C.2. ResourceConflictPenalty pseudocode

```text
Function ResourceConflictPenalty(P, CraneState, SafetyConstraints):
    hard_conflict = False
    soft_penalty = 0

    # Check crane availability and working zone
    For each action a in P.actions:
        If a.assigned_crane is None:
            continue

        yc = CraneState.get_crane(a.assigned_crane)

        If yc.status != "available" and a.estimated_start < yc.available_from:
            hard_conflict = True

        loc = ActionLocation(a)
        zone = ResolveZone(loc)

        If zone not in yc.working_zones:
            hard_conflict = True

    # Check pairwise crane conflict
    For each pair of actions (a, b) in P.actions:
        If a.assigned_crane is None or b.assigned_crane is None:
            continue

        If a.assigned_crane == b.assigned_crane:
            continue

        If TimeOverlap(a, b) == False:
            continue

        zone_a = ResolveZone(ActionLocation(a))
        zone_b = ResolveZone(ActionLocation(b))

        If HardZoneConflict(zone_a, zone_b, SafetyConstraints):
            hard_conflict = True

        Else if SoftZoneConflict(zone_a, zone_b, SafetyConstraints):
            soft_penalty += ConflictSeverity(zone_a, zone_b)

    If hard_conflict:
        return INF
    Else:
        return soft_penalty
```

---

## C.3. TimeOverlap

```text
Function TimeOverlap(a, b):
    return not (a.estimated_finish <= b.estimated_start or b.estimated_finish <= a.estimated_start)
```

---

# D. Resource cost chi tiết

## D.1. ResourceCost objective

```text
C_resource(P) =
    alpha_r * CraneTravel(P)
  + beta_r  * CraneIdle(P)
  + gamma_r * WorkloadImbalance(P)
  + delta_r * ResourceConflictPenalty(P)
```

Default:

```text
alpha_r = 1.0
beta_r  = 0.5
gamma_r = 1.0
delta_r = 10.0
```

Nếu `ResourceConflictPenalty(P) = INF`, candidate bị reject.

---

## D.2. CraneTravel pseudocode

```text
Function CraneTravel(P, CraneState, YardState):
    total_travel = 0

    For each crane yc in CraneState.cranes:
        actions_yc = ActionsAssignedTo(P, yc.id)
        Sort actions_yc by estimated_start

        current_loc = yc.current_location

        For each action a in actions_yc:
            loc = ActionLocation(a)
            If loc is None:
                continue

            total_travel += TravelTime(yc, current_loc, loc, CraneState, YardState)   # đã sửa: bổ sung yc
            current_loc = loc

    return total_travel
```

---

## D.3. CraneIdle pseudocode

```text
Function CraneIdle(P, CraneState):
    total_idle = 0

    For each crane yc in CraneState.cranes:
        actions_yc = ActionsAssignedTo(P, yc.id)
        Sort actions_yc by estimated_start

        prev_finish = yc.available_from

        For each action a in actions_yc:
            idle = max(0, a.estimated_start - prev_finish)
            total_idle += idle
            prev_finish = a.estimated_finish

    return total_idle
```

---

## D.4. WorkloadImbalance pseudocode

```text
Function WorkloadImbalance(P, CraneState):
    workloads = []

    For each crane yc in CraneState.cranes:
        work = 0
        For each action a assigned to yc:
            work += HandlingTime(a, yc)
        workloads.append(work)

    return StandardDeviation(workloads)
```

---

# E. Resource stability chi tiết

## E.1. ResourceStability objective

```text
D_crane(P_new, P_old) =
    changed_crane_assignments
  + changed_start_times
  + changed_work_zones
```

Với time weighting:

```text
D_crane = sum_j exp(-rho * pos_new(j)) * d_crane(j)
```

Quy ước:

> `pos(job)` là vị trí của job/action trong `P_new`. Nếu action không tồn tại trong `P_new` nhưng có trong `P_old`, dùng vị trí của nó trong `P_old`.

Lý do: Paper 3 đánh giá disturbance theo kế hoạch mới sẽ thực thi.

---

## E.2. Pseudocode

```text
Function ResourceStability(P_new, P_old, rho_res):
    penalty = 0

    For each action_id in Union(ActionIDs(P_new), ActionIDs(P_old)):
        a_new = GetAction(P_new, action_id)
        a_old = GetAction(P_old, action_id)

        If a_new exists:
            pos = PositionInPlan(P_new, action_id)
        Else:
            pos = PositionInPlan(P_old, action_id)

        weight = exp(-rho_res * pos)
        d = 0

        If a_new is None or a_old is None:
            d += penalty_added_or_removed_action
        Else:
            If a_new.assigned_crane != a_old.assigned_crane:
                d += penalty_changed_crane

            If abs(a_new.estimated_start - a_old.estimated_start) > start_time_tolerance:
                d += penalty_changed_start_time

            If ResolveZone(ActionLocation(a_new)) != ResolveZone(ActionLocation(a_old)):
                d += penalty_changed_work_zone

        penalty += weight * d

    return penalty
```

Default (khớp `zeta_t, zeta_z, zeta_ar` ở mục 13 — cùng một công thức `D_resource`, đặt tên khác nhau ở hai chỗ trình bày):

```text
penalty_changed_crane       = 1.0   # hệ số ngầm định của số hạng crane_new != crane_old
penalty_changed_start_time  = 0.5   # = zeta_t
penalty_changed_work_zone   = 1.0   # = zeta_z
penalty_added_or_removed_action = 2.0   # = zeta_ar
start_time_tolerance        = 1 simulation step
rho_res                     = 0.1   # decay rate dùng trong exp(-rho_res * pos), không dùng chung rho=0.05 của Paper 1
```

---

# F. Intervention complexity

## F.1. Definition

Intervention complexity phạt các intervention quá phức tạp hoặc kết hợp quá nhiều family.

```text
C_int(a) =
    family_count(a)
  + changed_object_count(a)
  + operator_complexity(a)
```

---

## F.2. Pseudocode

```text
Function InterventionComplexity(candidate):
    family_penalty = NumberOfFamilies(candidate)
    changed_objects = CountChangedContainers(candidate) \
                    + CountChangedCranes(candidate) \
                    + CountChangedJobOrders(candidate)

    If candidate.requires_manual_review:
        manual_penalty = penalty_manual_review
    Else:
        manual_penalty = 0

    return family_penalty + complexity_object_weight * changed_objects + manual_penalty
```

Default:

```text
complexity_object_weight = 0.1
penalty_manual_review    = 2.0
```

---

# G. Candidate generation — missing function details

## G.1. GenerateContainerRepair

Kế thừa Paper 2 nhưng cần interface rõ trong Paper 3.

```text
Function GenerateContainerRepair(P_old, YardState, RetrievalInfo, Events, K):
    candidates = []

    # C1: keep old plan as candidate
    candidates.append(P_old)

    # C2: minimal repair for invalid relocation destination
    P_min = MinimalRepair(P_old, YardState, RetrievalInfo)
    If Feasible(P_min):
        candidates.append(P_min)

    # C3: local search repair inherited from SAR-CRP / EA-SAR-CRP
    local_candidates = LocalSearchRepair(P_old, YardState, RetrievalInfo, Events)
    candidates.extend(local_candidates)

    # C4: constrained CRP_RL repair for repairable tail
    P_crp = CRPRLWrapperRepair(P_old, YardState, RetrievalInfo, freeze_horizon)
    If Feasible(P_crp):
        candidates.append(P_crp)

    Return TopKByFastScore(candidates, K, P_old)
```

---

## G.2. GenerateResourceReassignment

```text
Function GenerateResourceReassignment(P_old, CraneState, YardState, SafetyConstraints, K):
    candidates = []

    # R1: single-action reassignment
    For each action a in P_old.actions:
        If a.commit_status in {"executed", "in_progress"}:
            continue

        For each crane yc in CraneState.cranes:
            If yc.id == a.assigned_crane:
                continue

            If IsActionFeasibleWithCrane(a, yc, YardState, CraneState):
                P_new = copy(P_old)
                P_new.action[a.id].assigned_crane = yc.id
                P_new = RecomputeActionTimes(P_new, CraneState, YardState)
                candidates.append(P_new)

    # R2: block-level reassignment for high workload blocks
    high_blocks = DetectHighWorkloadBlocks(P_old, CraneState)

    For each block B in high_blocks:
        nearby_cranes = AvailableCranesNearBlock(B, CraneState)

        For each crane yc in nearby_cranes:
            P_new = copy(P_old)
            For each action a in ActionsInBlock(P_new, B):
                If a.commit_status not in {"executed", "in_progress"}:
                    If IsActionFeasibleWithCrane(a, yc, YardState, CraneState):
                        a.assigned_crane = yc.id

            P_new = RecomputeActionTimes(P_new, CraneState, YardState)
            If ResourceConflictPenalty(P_new, CraneState, SafetyConstraints) < INF:
                candidates.append(P_new)

    Return TopKByFastScore(candidates, K, P_old)
```

---

## G.3. GenerateJobResequencing

```text
Function GenerateJobResequencing(P_old, Events, freeze_horizon, K):
    candidates = []
    repairable_tail = ActionsAfterFreezeHorizon(P_old, freeze_horizon)

    # S1: move urgent retrieval earlier
    urgent_containers = ExtractUrgentContainers(Events)

    For each container c in urgent_containers:
        pos = FindRetrievalActionPosition(P_old, c)
        If pos is None:
            continue

        target_pos = max(freeze_horizon + 1, pos - urgent_shift_step)
        P_new = MoveAction(P_old, pos, target_pos)
        If Feasible(P_new):
            candidates.append(P_new)

    # S2: delay low-priority actions
    For each action a in repairable_tail:
        If a.priority == "low" and CanMoveLater(a):
            P_new = MoveActionToAfterUrgentActions(P_old, a)
            If Feasible(P_new):
                candidates.append(P_new)

    # S3: local swap within repairable tail
    For each pair of actions (a_i, a_j) in repairable_tail:
        If abs(Position(a_i) - Position(a_j)) > max_swap_distance:
            continue

        P_new = SwapActions(P_old, a_i, a_j)
        If Feasible(P_new):
            candidates.append(P_new)

    Return TopKByFastScore(candidates, K, P_old)
```

Default:

```text
urgent_shift_step = 3
max_swap_distance = 5
```

---

## G.4. GenerateWaitNoOp

```text
Function GenerateWaitNoOp(P_old, Diagnosis, StateReliability):
    candidates = []

    # W1: keep old plan
    candidates.append(P_old)

    # W2: wait for more information if confidence is low
    If StateReliability.global_confidence < confidence_wait_threshold:
        P_wait = copy(P_old)
        P_wait.metadata.intervention_type = "WAIT_FOR_INFORMATION"
        P_wait.metadata.wait_duration = default_wait_duration
        candidates.append(P_wait)

    # W3: freeze more actions if instability risk is high
    If Diagnosis.instability_risk == "high":
        P_freeze = copy(P_old)
        P_freeze.freeze_horizon = P_old.freeze_horizon + additional_freeze_steps
        candidates.append(P_freeze)

    Return candidates
```

Default:

```text
confidence_wait_threshold = 0.60
default_wait_duration     = 1 simulation step
additional_freeze_steps   = 2
```

---

## G.5. GenerateLimitedHybrid

Hybrid chỉ kết hợp tối đa 2 intervention families để tránh explosion. **`max_hybrid_total` (early-stop khi sinh) và `K_hybrid` (số candidate trả về sau cùng, mục 31) là hai tham số khác nhau** — sinh tới `max_hybrid_total` rồi mới lọc còn `K_hybrid` bằng `TopKByFastScore`, không trả thẳng `max_hybrid_total` candidate ra ngoài.

```text
Function GenerateLimitedHybrid(family_candidates, P_old, CraneState, YardState, max_families=2, K_family=5, max_hybrid_total=50, K_hybrid=10):
    hybrids = []

    families = Keys(family_candidates)

    For each pair of families (F_i, F_j):
        candidates_i = first K_family candidates from family_candidates[F_i]
        candidates_j = first K_family candidates from family_candidates[F_j]

        For each P_i in candidates_i:
            For each P_j in candidates_j:
                P_hybrid = MergePlans(P_i, P_j, CraneState, YardState)

                If P_hybrid is None:
                    continue

                If InterventionComplexity(P_hybrid) > complexity_threshold:
                    continue

                If Feasible(P_hybrid):
                    hybrids.append(P_hybrid)

                If len(hybrids) >= max_hybrid_total:
                    Return TopKByFastScore(hybrids, K_hybrid, P_old)

    Return TopKByFastScore(hybrids, K_hybrid, P_old)
```

Default:

```text
max_families      = 2
K_family          = 5
max_hybrid_total  = 50   # trần sinh candidate (early-stop)
K_hybrid          = 10   # số candidate trả về sau cùng (mục 31)
complexity_threshold = 10
```

Runtime note:

> Hybrid generation can grow quadratically in the number of families and candidates. Therefore, Paper 3 fixes `K_family` and `max_hybrid_total` to keep runtime bounded.

---

## G.6. MergePlans

```text
Function MergePlans(P1, P2, CraneState, YardState):
    P = copy(P1)

    For each action a2 in P2.actions:
        a1 = FindActionById(P, a2.id)

        If a1 is None:
            # New action introduced by P2
            If CanInsertAction(a2, P):
                P.actions.append(a2)
            Else:
                return None

        Else:
            # Conflict: both plans change destination differently
            If FieldChanged(a1, "to_stack") and FieldChanged(a2, "to_stack"):
                If a1.to_stack != a2.to_stack:
                    return None

            # Conflict: both plans change ordering differently
            If OrderingChanged(P1, a2.id) and OrderingChanged(P2, a2.id):
                If PositionInPlan(P1, a2.id) != PositionInPlan(P2, a2.id):
                    return None

            # Merge allowed: destination from one, crane assignment from another
            If a2.to_stack is not None and not FieldChanged(a1, "to_stack"):
                a1.to_stack = a2.to_stack

            If a2.assigned_crane is not None:
                a1.assigned_crane = a2.assigned_crane

            If a2.estimated_start is not None:
                a1.estimated_start = a2.estimated_start

            If a2.priority is not None:
                a1.priority = max_priority(a1.priority, a2.priority)

    P = RecomputeActionTimes(P, CraneState, YardState)
    Return P
```

Simplified rule:

```text
- Same action changed to two different destinations → reject.
- Same action reordered in two incompatible ways → reject.
- Destination change + crane reassignment → merge allowed.
- New safe action → insert allowed.
```

---

## G.7. GenerateSafeRepair

```text
Function GenerateSafeRepair(P_old, SafetyConstraints, CraneState, YardState):
    P = copy(P_old)

    For each action a in P.actions:
        If ViolatesHardConstraint(a, SafetyConstraints, CraneState, YardState):
            If CanRemove(a):
                RemoveAction(P, a)
            Else:
                return SafeHoldPlan(P_old, reason="Non-removable unsafe action")

    P = RecomputeActionTimes(P, CraneState, YardState)

    If ResourceConflictPenalty(P, CraneState, SafetyConstraints) == INF:
        return SafeHoldPlan(P_old, reason="Unresolved resource conflict")

    return P
```

---

# H. Schema bổ sung

## H.1. Detailed CraneState schema

> **Đã hợp nhất vào mục 26.1 — dùng mục 26.1 làm schema chuẩn duy nhất.** Bản gốc ở đây dùng `current_location` dạng string + `speed_factor` đơn, khác với mục 26.1 (`current_location` dạng object + `speed`/`slowdown_factor` tách riêng); `capacity` và `stack_to_zone_map` giới thiệu ở đây đã được đưa vào mục 26.1.

---

## H.2. ResourceEvent schema

> `new_speed_factor` áp dụng vào `crane.slowdown_factor` (mục 26.1), không phải `crane.speed` — `speed` (tốc độ gốc) không đổi khi có event, chỉ `slowdown_factor` thay đổi rồi trở về `1.0` khi có event `crane_recovered`.

```json
{
  "event_id": "RE001",
  "time": 12,
  "type": "crane_slowdown",
  "crane_id": "YC1",
  "old_speed_factor": 1.0,
  "new_speed_factor": 0.6,
  "duration": 10,
  "confidence": 0.9
}
```

```json
{
  "event_id": "RE002",
  "time": 20,
  "type": "crane_unavailable",
  "crane_id": "YC2",
  "available_from": 35,
  "reason": "maintenance",
  "confidence": 0.95
}
```

```json
{
  "event_id": "RE003",
  "time": 25,
  "type": "workload_spike",
  "zone": "Z3",
  "expected_extra_jobs": 8,
  "horizon": 10,
  "confidence": 0.8
}
```

---

## H.3. Resource safety constraint schema

```json
{
  "constraint_id": "RES_SAFE_001",
  "type": "hard",
  "description": "Two cranes cannot operate in the same conflict zone at overlapping times.",
  "check": "not TimeOverlap(a,b) OR not SameConflictZone(a,b)"
}
```

```json
{
  "constraint_id": "RES_SAFE_002",
  "type": "hard",
  "description": "A crane cannot be assigned outside its working zones.",
  "check": "ResolveZone(ActionLocation(a)) in crane.working_zones"
}
```

```json
{
  "constraint_id": "RES_SAFE_003",
  "type": "soft",
  "description": "Avoid assigning a crane to a distant zone if another feasible crane is nearby.",
  "weight": 0.5,
  "check": "TravelTime(crane, crane.current_location, ActionLocation(a), CraneState, YardState) <= distance_threshold"
}
```

---

# I. Parameter table bổ sung

Bảng này bổ sung các tham số **chưa có** ở mục 31 (distance/handling-time/fast-score) — không lặp lại λ/μ/ν/ω/η/λ_res/π/ρ_res/ζ_*/K_* đã có ở mục 31, dùng mục 31 làm nguồn cho các tham số đó.

| Parameter | Meaning | Default | Range / sensitivity |
|---|---|---:|---|
| `w_b` | block distance weight | 10 | 5, 10, 20 |
| `w_bay` | bay distance weight | 1 | 1, 2 |
| `w_row` | row distance weight | 1 | 1, 2 |
| `handling_time_relocate` | default relocation handling time | 2.0 | 1.5, 2.0, 3.0 |
| `handling_time_retrieve` | default retrieval handling time | 1.0 | 1.0, 1.5 |
| `lambda_fast` | fast-score stability weight | 0.5 | 0.25, 0.5, 1.0 |
| `psi_fast` | fast-score resource proxy weight | 0.2 | 0.0, 0.2, 0.5 |
| `max_hybrid_total` | early-stop cap khi *sinh* hybrid (lớn hơn `K_hybrid`=10 ở mục 31 vì còn phải lọc lại bằng `TopKByFastScore` sau đó) | 50 | 25, 50, 100 |
| `K_family` | candidates per family for hybrid | 5 | 3, 5, 10 |
| `urgent_shift_step` | shift urgent jobs earlier by this amount | 3 | 1, 3, 5 |
| `max_swap_distance` | max distance for local swap | 5 | 3, 5, 7 |
| `confidence_wait_threshold` | threshold for wait/no-op | 0.60 | 0.5, 0.6, 0.7 |
| `start_time_tolerance` | tolerance for start-time stability | 1 | 1, 2 |

---

# J. Modules inherited from Paper 2

Paper 3 is **not a rewrite**. It directly extends Paper 2.

## Reused without modification

```text
- YardState schema
- Plan schema
- PlanAction schema
- RetrievalInformation schema
- ExecutionFeedback schema
- StateReliabilityEstimator
- ExecutionImpactEstimator
- DataConfidenceCost
- SafetyConstraint base schema
- Fallback hierarchy
- OperatorInteraction logger
- Event generator core
- Metrics logger
- Baseline runner
- Timeout/fallback infrastructure
```

## Modified or extended

```text
- SafetyConstraint schema → extended with resource/crane constraints
- CandidateGenerator → extended from single-family repair to multi-intervention generation
- CandidateEvaluator → extended with C_resource, D_crane and C_intervention
- Benchmark generator → extended with ResourceEvent stream
- Baseline runner → extended with resource-aware baselines
```

## New in Paper 3

```text
- CraneState schema
- ResourceEvent schema
- ResourceCost
- ResourceStability
- InterventionComplexity
- Diagnosis-guided multi-intervention generation
- GenerateResourceReassignment
- GenerateJobResequencing
- GenerateLimitedHybrid
- ResourceConflictPenalty
```

---

# K. Benchmark and runtime notes

## K.1. Candidate limits

To avoid candidate explosion (đồng bộ tên/giá trị với mục 31 — đã sửa `K_schedule` → `K_sequence`, và tách `K_hybrid` khỏi `max_hybrid_total`, vì trước đây hai bảng dùng `K_hybrid=50` ở đây nhưng `K_hybrid=10` ở mục 31):

```text
K_container      = 20
K_resource       = 20
K_sequence       = 20   # trước đây gọi nhầm là K_schedule
K_wait           = 3    # mô tả (W1-W3 tự nhiên <= 3), không phải bộ lọc chủ động
K_hybrid         = 10   # số candidate hybrid trả về sau cùng (mục 31)
max_hybrid_total = 50   # trần sinh hybrid trong lúc duyệt (mục G.5), khác K_hybrid
```

Total raw candidate cap before final evaluation:

```text
max_candidates_total = 100
```

If more candidates are generated, keep top candidates by `fast_score`.

---

## K.2. Timeout protocol

| Instance size | Paper 2 timeout | Paper 3 timeout | Reason |
|---|---:|---:|---|
| Small | 2s | 3s | resource evaluation added |
| Medium | 8s | 12s | more candidate families |
| Large | 40s | 60s | hybrid/resource candidates |

If timeout occurs:

```text
Full candidate generation/evaluation
    ↓ timeout
Minimal resource-aware repair
    ↓ failed
Keep old plan
    ↓ infeasible
Safe hold / manual review
```

---

## K.3. Ground-truth / proxy refinement

For Paper 3:

```text
Small instances:
    exhaustive search over limited container repair + crane assignment + resequencing candidates.

Medium / large instances:
    extended-time joint full reoptimization with 300s limit.
```

We do **not** claim extended-time reoptimization is true optimum. It is used as an offline high-quality proxy.

---

# L. Final coding checklist for Paper 3

Before coding full experiments, verify these unit-level functions:

```text
[ ] TravelTime
[ ] ResolveZone
[ ] ActionLocation
[ ] HandlingTime
[ ] RecomputeActionTimes
[ ] TopKByFastScore
[ ] ResourceConflictPenalty
[ ] CraneTravel
[ ] CraneIdle
[ ] WorkloadImbalance
[ ] ResourceStability
[ ] InterventionComplexity
[ ] GenerateResourceReassignment
[ ] GenerateJobResequencing
[ ] GenerateWaitNoOp
[ ] MergePlans
[ ] GenerateLimitedHybrid
[ ] GenerateSafeRepair
[ ] CanRemove
```

MVP gate:

```text
1 layout nhỏ
3 baselines:
    - Paper-2 EA-SAR-CRP
    - Sequential container repair → resource assignment
    - MISR-Yard MVP

Proceed to full experiments only if MISR-Yard improves total intervention cost or achieves a better stability/resource trade-off.
```

---

# M. Final Paper 3 positioning

Paper 3 should be described as:

> Paper 1 makes replanning stable under evolving retrieval information. Paper 2 makes replanning robust under imperfect execution. Paper 3 makes replanning strategic by choosing the right intervention family.

Final claim:

> MISR-Yard extends stable adaptive replanning from single-intervention repair to multi-intervention orchestration, enabling container yard systems to decide whether to repair container plans, reassign resources, resequence jobs, combine limited interventions, or wait, based on a joint assessment of operational efficiency, plan stability, execution risk, resource feasibility, safety and intervention complexity.

