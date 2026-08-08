# PAPER 4 RESEARCH PROPOSAL
# Port-GSAR: Port-Configurable Generalizable Stable Adaptive Replanning for Container Yard Operations

**Mục tiêu:** Công bố Q1 và tạo nền tảng triển khai production đa cảng.

**Vai trò trong chuỗi nghiên cứu:**

- **Paper 1:** Stable replanning khi retrieval information thay đổi.
- **Paper 2:** Robust replanning khi execution feedback và dữ liệu không hoàn hảo.
- **Paper 3:** Strategic replanning bằng cách chọn đúng intervention family.
- **Paper 4:** Generalizable replanning để framework có thể triển khai sang nhiều terminal/layout khác nhau.

Câu chốt:

> **Paper 1 makes replanning stable. Paper 2 makes it robust. Paper 3 makes it strategic. Paper 4 makes it deployable across terminals.**

---

# 1. Tên đề tài

## Port-GSAR

**Port-Configurable Generalizable Stable Adaptive Replanning for Container Yard Operations**

Tên tiếng Việt:

> **Tái lập kế hoạch ổn định có khả năng tổng quát hóa giữa nhiều cảng thông qua cấu hình cảng**

---

# 2. Tóm tắt ý tưởng

Các nghiên cứu Paper 1–3 tạo ra một framework ra quyết định cho yard operation:

- khi nào cần replan;
- sửa plan thế nào cho ổn định;
- xử lý execution feedback và dữ liệu không hoàn hảo;
- chọn intervention phù hợp: container repair, resource reassignment, job resequencing, wait/no-op, hybrid intervention.

Nhưng nếu framework chỉ chạy tốt trên một layout hoặc một benchmark cố định thì chưa đủ để triển khai sản phẩm thật.

Trong thực tế, mỗi cảng khác nhau về:

- số block;
- số bay;
- số row;
- chiều cao stack;
- loại crane;
- travel time;
- safety rules;
- rule vận hành;
- objective ưu tiên;
- mức độ dữ liệu đầy đủ;
- cấu trúc workflow.

Do đó Paper 4 trả lời câu hỏi:

> **Làm thế nào để một stable adaptive yard decision framework có thể chuyển từ terminal/layout này sang terminal/layout khác với ít hoặc không cần hiệu chỉnh lại?**

---

# 3. Vấn đề nghiên cứu

## 3.1. Vấn đề học thuật

Các thuật toán CRP, replanning, resource scheduling hoặc multi-intervention thường được đánh giá trên một tập layout/benchmark cụ thể.

Tuy nhiên, terminal thật có topology và rule rất khác nhau.

Nếu mỗi terminal mới đều phải:

- viết lại code;
- tune lại toàn bộ tham số;
- train lại toàn bộ policy;
- xây lại simulator;

thì phương pháp không còn khả năng triển khai rộng.

## 3.2. Vấn đề production

Một sản phẩm cho cảng không thể chỉ trả lời:

> Tôi chạy tốt trên benchmark A.

Mà phải trả lời:

> Tôi có thể onboard terminal B/C/D bằng configuration, limited calibration, và biết khi nào tôi không đủ tự tin để tự động đề xuất.

---

# 4. Câu hỏi nghiên cứu

## RQ chính

> **Can a stable adaptive yard decision framework generalize across heterogeneous terminal layouts using port configuration, graph-based terminal representation, and limited calibration?**

Tiếng Việt:

> **Liệu một framework ra quyết định tái lập kế hoạch ổn định cho bãi container có thể tổng quát hóa qua nhiều layout/cảng khác nhau bằng PortConfig, biểu diễn graph của terminal và hiệu chỉnh giới hạn hay không?**

## RQ phụ

### RQ1 — Zero-shot transfer

> Khi tune trên một terminal nguồn, framework có hoạt động được trên terminal đích mà không retune không?

### RQ2 — Few-shot calibration

> Cần bao nhiêu dữ liệu hiệu chỉnh để phục hồi phần lớn hiệu năng trên terminal mới?

### RQ3 — Layout sensitivity

> Loại khác biệt layout nào gây suy giảm hiệu năng lớn nhất?

### RQ4 — OOD detection

> Hệ thống có phát hiện được khi terminal mới quá khác terminal đã tune không?

### RQ5 — Production readiness

> PortConfig + YardGraph có đủ để triển khai framework mà không sửa code lõi không?

---

# 5. Gap nghiên cứu

## Gap 1 — From single-layout optimization to cross-terminal decision-making

Nhiều nghiên cứu tối ưu hóa yard/CRP tập trung vào một layout hoặc một nhóm benchmark cố định.

Thiếu nghiên cứu xem:

> decision framework có thể chuyển qua nhiều terminal khác nhau như thế nào.

## Gap 2 — From algorithm generalization to deployment generalization

Một số model có thể generalize theo kích thước instance, nhưng production deployment cần nhiều hơn:

- rule khác;
- resource khác;
- travel matrix khác;
- safety constraints khác;
- objective weights khác;
- data reliability khác.

## Gap 3 — Lack of calibration protocol

Khi sang terminal mới, cần biết:

- tham số nào giữ nguyên;
- tham số nào cần tune;
- cần bao nhiêu dữ liệu;
- performance drop bao nhiêu;
- khi nào fallback.

## Gap 4 — Lack of OOD/failure detection

Nếu framework áp dụng sang một terminal quá khác, nó cần biết:

> “Tôi không đủ tự tin.”

Không có OOD detection, sản phẩm dễ đưa khuyến nghị sai.

> **Cần bổ sung trước khi submit.** Bốn gap trên hiện chỉ lập luận nội bộ, chưa trích dẫn literature nào — đây là thiếu sót đáng ngại nhất trong 4 paper vì các mảng liên quan (transfer learning/domain adaptation, out-of-distribution detection, few-shot learning, meta-learning, sim-to-real transfer) đều là các nhánh ML rất mainstream với khối lượng literature lớn. Trước khi viết Related Work thật, cần trích dẫn cụ thể cho: (1) domain adaptation/covariate-shift cho lý do Gap 1-2, (2) density-ratio hoặc distance-based OOD detection cho Gap 4, (3) few-shot/meta-learning cho cơ chế calibration ở M5. Ngoài ra, baseline B2 (per-layout tuned Paper 3 MISR-Yard, mục 43) vẫn phụ thuộc gián tiếp "Shin et al. 2026" qua Paper 3 — kế thừa yêu cầu xác minh citation đã nêu ở Paper 1 (mục 3) và Paper 2/3.

---

# 6. Định vị novelty

Paper 4 không claim:

> Chúng tôi có một model chạy tốt cho mọi cảng.

Paper 4 claim:

> **Chúng tôi đề xuất một framework ra quyết định bãi container có khả năng cấu hình theo cảng, biểu diễn terminal dưới dạng graph, dùng shared decision modules từ SAR/MISR, và hỗ trợ zero-shot/few-shot transfer với đo lường transfer gap, calibration efficiency và OOD risk.**

Novelty gồm 5 điểm:

1. **PortConfig schema** cho stable adaptive yard decision-making.
2. **YardGraph representation** độc lập layout.
3. **Cross-terminal transfer protocol** cho SAR/MISR framework.
4. **Few-shot calibration mechanism** cho terminal mới.
5. **OOD/failure detection + deployment fallback** để tăng production readiness.

---

# 7. Mô hình tổng thể

```text
Terminal A / Layout A
        ↓
PortConfig_A + YardGraph_A
        ↓
Tune SAR/MISR parameters
        ↓
Shared Decision Framework
        ↓
Transfer to Terminal B/C/D
        ↓
PortConfig_B + YardGraph_B
        ↓
Zero-shot Evaluation
        ↓
Few-shot Calibration
        ↓
OOD / Confidence Check
        ↓
Deployable Decision Policy
```

---

# 8. Thành phần chính của Port-GSAR

Port-GSAR gồm 7 module.

```text
M1. PortConfig Schema
M2. YardGraph Builder
M3. Layout-Invariant Feature Extractor
M4. Shared Stable Decision Engine
M5. Few-Shot Calibration Layer
M6. Cross-Terminal OOD Detector
M7. Deployment Fallback Controller
```

---

# 9. M1 — PortConfig Schema

## 9.1. Mục tiêu

PortConfig mô tả **cấu hình tĩnh** của terminal mới mà không cần sửa code. PortConfig **không chứa state động** (occupancy hiện tại, crane đang bận hay rảnh, plan hiện tại) — state động vẫn dùng `YardState`/`CraneState`/`Plan` đã có từ Paper 1–3 (mục 42.1 tái sử dụng nguyên các schema này). `BuildYardGraph` nhận cả `PortConfig` (tĩnh) lẫn `YardState`/`CraneState` (động) làm tham số riêng biệt — xem mục 10.5/36.2.

> **Đây là schema chuẩn duy nhất** (đã hợp nhất với mọi chỗ dùng field trong `BuildYardGraph` mục 36.2, `GetTravelTime` mục 37, `ExtractRiskFeatures` mục 38.5 — các mục đó trước đây dùng đường dẫn field khác với schema ở đây, nay đã đồng bộ).

## 9.2. Schema đề xuất

```json
{
  "port_id": "PORT_A",
  "layout_id": "LAYOUT_A",
  "layout_family": "symmetric_small",
  "layout": {
    "num_blocks": 3,
    "blocks": [
      {
        "block_id": "B1",
        "num_bays": 6,
        "num_rows": 4,
        "max_stack_height": 5,
        "block_type": "import",
        "zone_id": "Z1",
        "is_active": true
      }
    ]
  },
  "resources": {
    "cranes": [
      {
        "crane_id": "YC1",
        "working_zones": ["Z1", "Z2"],
        "speed_factor": 1.0,
        "available_from": 0,
        "status": "available"
      }
    ],
    "crane_zones": [
      {
        "zone_id": "Z1",
        "safety_distance": 1
      }
    ]
  },
  "travel": {
    "mode": "matrix",
    "time_unit": "simulation_step",
    "travel_time_matrix": {
      "Z1": {"Z1": 0, "Z2": 5, "Z3": 10},
      "Z2": {"Z1": 5, "Z2": 0, "Z3": 6},
      "Z3": {"Z1": 10, "Z2": 6, "Z3": 0}
    },
    "fallback_distance": {
      "type": "block_aware_manhattan",
      "w_block": 10,
      "w_bay": 1,
      "w_row": 1
    }
  },
  "safety_rules": [
    {
      "rule_id": "SAFE_STACK_HEIGHT",
      "type": "hard",
      "description": "Cannot exceed stack max tier",
      "is_hard": true,
      "zone_a": null,
      "zone_b": null,
      "penalty_weight": null
    },
    {
      "rule_id": "SAFE_ZONE_CONFLICT_Z1_Z2",
      "type": "zone_conflict",
      "description": "Z1 and Z2 share a boundary and cannot both be busy at once",
      "is_hard": false,
      "zone_a": "Z1",
      "zone_b": "Z2",
      "penalty_weight": 0.5
    }
  ],
  "objectives": {
    "relocation_weight": 1.0,
    "stability_weight": 1.0,
    "resource_stability_weight": 1.0,
    "data_confidence_weight": 0.5,
    "execution_weight": 1.0,
    "resource_weight": 1.0,
    "safety_weight": 5.0,
    "intervention_complexity_weight": 0.5
  },
  "data_reliability": {
    "sources": [
      {"source_name": "simulator", "reliability_factor": 1.0},
      {"source_name": "tos", "reliability_factor": 0.9},
      {"source_name": "crane_telemetry", "reliability_factor": 0.95},
      {"source_name": "manual", "reliability_factor": 0.5}
    ],
    "manual_update_ratio": 0.1
  }
}
```

## 9.2.1. Mapping `objectives` sang ký hiệu toán học

Bảng dưới đây bắt buộc phải có để coder biết field JSON nào tương ứng ký hiệu nào trong mục 16/22 (trước đây không có mapping này, dễ đoán sai):

| Field trong `objectives` | Ký hiệu | Vai trò |
|---|---|---|
| `relocation_weight` | (ngầm định = 1, hệ số của `C_op`) | Operational cost |
| `stability_weight` | `λ` | Container-plan stability (`C_stab`) |
| `resource_stability_weight` | `λ_res` | Resource/crane stability (`D_resource`) — **mới, xem mục 16.1** |
| `data_confidence_weight` | `π` | Data confidence cost (`C_data`) — **mới, xem mục 16.1** |
| `execution_weight` | `μ` | Execution cost (`C_exec`) |
| `resource_weight` | `ν` | Resource cost (`C_res`) |
| `safety_weight` | `ω` | Safety cost (`C_safety`) |
| `intervention_complexity_weight` | `η` | Intervention complexity (`C_int`) |

## 9.3. Production value

Với PortConfig:

```text
Terminal mới = config mới
Không cần sửa decision engine
```

Đây là phần quan trọng để biến nghiên cứu thành product.

---

# 10. M2 — YardGraph Builder

## 10.1. Mục tiêu

Biểu diễn terminal dưới dạng graph để model không phụ thuộc layout cố định.

## 10.2. Graph definition


graph:

\[
G=(V,E)
\]

Nodes:

```text
block nodes
bay nodes
stack nodes
gate nodes
crane zone nodes
transfer point nodes
```

Edges:

```text
adjacency edges
travel edges
accessibility edges
conflict edges
resource-zone edges
```

## 10.3. Node features

```text
node_type
occupancy
capacity
avg_stack_height
retrieval_pressure
workload
resource_availability
safety_flags
```

## 10.4. Edge features

```text
travel_time
distance
conflict_type
same_block
reachable_by_crane
```

## 10.5. Pseudocode

> Đây là bản phác thảo ý tưởng. **Pseudocode đầy đủ và chuẩn để code nằm ở mục 36.2** — cùng chữ ký `(PortConfig cfg, YardState state, CraneState craneState)`, đọc field theo schema chuẩn mục 9.2 (`cfg.layout.blocks`, không phải `cfg.yard.blocks`).

```text
Function BuildYardGraph(PortConfig cfg, YardState state, CraneState craneState):
    G = empty graph

    For each block in cfg.layout.blocks:
        add block node
        For each bay in block:
            add bay node
            add edge block -> bay
            For each row/stack in bay:
                add stack node (dùng occupancy từ `state`, không phải từ cfg)
                add edge bay -> stack
                attach stack occupancy/capacity features

    For each crane in craneState.cranes:
        add crane node
        For each working zone of crane:
            add edge crane -> zone

    For each pair of zones:
        travel_time = GetTravelTime(cfg, zone_i, zone_j)
        add travel edge with travel_time

    Add conflict edges based on cfg.safety_rules

    return G
```

---

# 11. M3 — Layout-Invariant Feature Extractor

## 11.1. Mục tiêu

Chuyển YardGraph và state thành feature vector có thể dùng chung qua nhiều layout.

## 11.2. Không bắt buộc phải dùng deep learning ngay

Paper 4 có thể bắt đầu với feature aggregation:

```text
mean occupancy
max occupancy
std workload
retrieval pressure histogram
resource imbalance
conflict density
travel-time statistics
```

Sau đó có thể mở rộng bằng GNN.

## 11.3. Feature groups

### Yard features

```text
occupancy_mean
occupancy_max
occupancy_std
num_near_full_stacks
retrieval_pressure_top_k
blocking_pressure_mean
```

### Resource features

```text
num_cranes
crane_availability_ratio
workload_imbalance
avg_travel_time
max_travel_time
```

### Layout features

```text
num_blocks
num_stacks
avg_stack_capacity
travel_matrix_density
crane_zone_overlap
```

### Risk features

```text
safety_violation_risk
data_confidence
OOD_score
```

---

# 12. M4 — Shared Stable Decision Engine

Paper 4 kế thừa từ Paper 3:

```text
MISR-Yard Decision Orchestrator
```

Giữ nguyên:

- diagnosis-guided candidate generation;
- intervention families;
- objective function;
- stability cost;
- execution risk;
- resource cost;
- safety validation;
- intervention complexity;
- fallback hierarchy.

Điểm mới của Paper 4:

> các module trên không phụ thuộc layout cố định mà đọc thông tin qua PortConfig + YardGraph.

---

# 13. M5 — Few-Shot Calibration Layer

## 13.1. Vấn đề

Khi sang terminal mới, một số tham số có thể lệch:

```text
travel speed
handling time
resource weight
stability preference
trigger threshold
confidence decay
```

Không nên tune toàn bộ từ đầu.

## 13.2. Calibration targets

Chỉ hiệu chỉnh một tập nhỏ tham số:

```text
lambda_stability
mu_execution
nu_resource
omega_safety
theta_trigger
kappa_confidence
speed_factor
handling_time_factor
```

## 13.3. Few-shot calibration data

Một số ít episodes/instances từ terminal đích:

```text
5 episodes
10 episodes
25 episodes
50 episodes
100 episodes
```

## 13.4. Calibration objective

\[
\theta^*_{target}
=
\arg\min_{\theta}
J_{target}(\theta)
\]

Trong đó chỉ tune subset nhỏ của \(\theta\), không retrain toàn bộ framework.

## 13.5. Calibration strategies

### Strategy A — No calibration

Dùng tham số từ source terminal.

### Strategy B — Global scalar calibration

Chỉ scale một vài cost weights.

### Strategy C — Trigger calibration

Tune threshold trigger.

### Strategy D — Resource calibration

Tune travel/handling factors.

### Strategy E — Full limited calibration

Tune toàn bộ subset nhỏ được cho phép.

---

# 14. M6 — Cross-Terminal OOD Detector

## 14.1. Mục tiêu

Phát hiện terminal/layout mới quá khác so với source.

Nếu OOD cao:

```text
không tự tin deploy
chạy conservative mode
fallback rule-based
cần calibration thêm
```

## 14.2. OOD features

> **7 nhóm feature chuẩn: xem mục 39.3.** Danh sách dưới đây là bản phác thảo ban đầu, có 2 tên khác với bản chuẩn (`stack_capacity_difference`→`stack_height_shift`, `workload_distribution_shift`→`data_reliability_shift`) — không dùng danh sách này để code.

```text
layout_size_difference
stack_capacity_difference
travel_time_distribution_shift
crane_zone_difference
occupancy_distribution_shift
workload_distribution_shift
safety_rule_difference
```

## 14.3. OOD score

> **Công thức và pseudocode chuẩn để code: xem mục 39.1–39.2.** Công thức dưới đây là ý tưởng ban đầu (weighted sum trên giá trị thô, chưa chuẩn hóa) — bản mục 39 chuẩn hóa feature theo thống kê source (`NormalizeFeatures`) trước khi tính khoảng cách theo từng nhóm, và có `GroupFeatures` map từ output phẳng của `ExtractPortFeatures` (mục 38.1) sang 7 nhóm dùng trong `ComputeOODScore` (xem mục 39.2.1, mới bổ sung).

\[
OOD(G_t,G_s)
=
\sum_i w_i \cdot |f_i(G_t)-f_i(G_s)|
\]

Trong đó:

- \(G_s\): source terminal graph;
- \(G_t\): target terminal graph;
- \(f_i\): layout/resource/statistical feature;
- \(w_i\): trọng số.

## 14.4. Deployment decision

> **Ngưỡng chuẩn để code: xem mục 33.3/48** (`theta_zero_shot = 0.30`, `theta_few_shot = 0.60`) — bản dưới đây dùng ngưỡng khác (0.2/0.5), đã lỗi thời, không dùng để code.

```text
If OOD < 0.2:
    allow zero-shot deployment in advisory mode
Elif OOD < 0.5:
    require few-shot calibration
Else:
    conservative fallback + manual validation required
```

---

# 15. M7 — Deployment Fallback Controller

## 15.1. Mục tiêu

Khi transfer không đáng tin, hệ thống không nên cưỡng ép decision engine.

## 15.2. Modes

> Danh sách mode chuẩn (đồng bộ với mục 47.1 — không dùng "Mode 1..5" như bản trước, đã đổi tên/số lượng cho khớp):

```text
MODE_0: Manual configuration only (chưa đủ thông tin để đề xuất tự động)
MODE_1: Zero-shot recommendation (OOD thấp, dùng thẳng tham số nguồn)
MODE_2: Few-shot calibrated recommendation (đã calibrate và recovery_ratio đạt ngưỡng)
MODE_3: Assisted deployment with human approval (calibrate nhưng chưa đủ tin cậy)
MODE_4: Safe fallback / no autonomous recommendation (OOD cao hoặc vi phạm safety cứng)
```

## 15.3. Mode selection

Logic chọn mode đầy đủ xem `SelectDeploymentMode` ở mục 47.2. Dựa trên:

```text
OOD score
state confidence
calibration data size
runtime timeout
safety validation rate
operator rejection rate
```

---

# 16. Objective của Paper 4

Paper 4 không thay objective lõi của Paper 3, mà thêm transfer/generalization criteria.

## 16.1. Operational objective

Kế thừa MISR-Yard — **đúng bản Paper 3 đã sửa** (bản trước ở đây thiếu 2 số hạng `D_resource` và `C_data` giống lỗi ban đầu của Paper 3):

\[
J_{yard}(a)
=
C_{op}
+\lambda C_{stab}
+\lambda_{res} D_{resource}
+\pi C_{data}
+\mu C_{exec}
+\nu C_{res}
+\omega C_{safety}
+\eta C_{int}
\]

Mapping với `PortConfig.objectives` xem mục 9.2.1. `μ` = execution weight, `ν` = resource weight (không phải ngược lại — xem ghi chú ký hiệu ở mục 40.1).

## 16.2. Transfer objective

\[
J_{transfer}
=
J_{yard}
+\xi C_{calibration}
+\zeta C_{OOD}
\]

Trong đó:

```text
C_calibration = amount of target data required
C_OOD         = risk of applying source parameters to target terminal
```

---

# 17. Metrics

## 17.1. Core yard metrics

Kế thừa Paper 1–3:

```text
operational cost
plan stability
execution risk
resource cost
safety violation
runtime
fallback rate
```

## 17.2. Transfer metrics

### Transfer Gap

\[
TransferGap
=
J_{target}^{transfer}
-
J_{target}^{tuned}
\]

### Relative Transfer Gap

\[
RTG
=
\frac{J_{target}^{transfer}-J_{target}^{tuned}}
{J_{target}^{tuned}}
\]

### Calibration Efficiency

\[
CE(n)
=
J_{zero-shot}-J_{few-shot(n)}
\]

### Recovery Ratio

\[
Recovery(n)
=
\frac{J_{zero-shot}-J_{few-shot(n)}}
{J_{zero-shot}-J_{fully-tuned}}
\]

### OOD Detection Accuracy

Nếu có labels ID/OOD:

```text
AUROC
F1
Precision/Recall
```

Nếu không có labels:

```text
correlation between OOD score and performance drop
```

---

# 18. Dataset / benchmark design

## 18.1. Layout families

Tạo ít nhất 5 layout families.

### Layout A — Source small symmetric

```text
3 blocks
same stack height
uniform travel
2 cranes
```

### Layout B — Medium scaled

```text
5 blocks
more stacks
same rule family
3 cranes
```

### Layout C — Asymmetric layout

```text
uneven block sizes
non-uniform travel matrix
3 cranes
```

### Layout D — Resource-different

```text
different crane working zones
crane speed heterogeneity
resource bottlenecks
```

### Layout E — Rule-different

```text
different safety constraints
reserved zones
restricted stack classes
```

## 18.2. Instance count

> **Số liệu chuẩn để code: xem mục 44.2** — đã đồng bộ K-value set (`{0,5,10,20,50}`, không dùng `25` như bản trước) và cỡ dataset (`300` instance nguồn thay vì `200+50+100`) với `EvaluateFewShotCalibration` (mục 41.3) và toàn bộ patch. Bản dưới đây là phác thảo ban đầu, không dùng để code.

```text
Source Layout A:
  train/tune: 200 instances
  validation: 50 instances
  test: 100 instances

Target Layouts B/C/D/E:
  zero-shot test: 100 instances/layout
  few-shot calibration: 5, 10, 25, 50 instances/layout
  final test: 100 instances/layout
```

## 18.3. Event types

Kế thừa Paper 1–3:

```text
retrieval order update
urgent insertion
ETA update
execution delay
action failed
state mismatch
crane slowdown
crane unavailable
workload spike
safety conflict
```

---

# 19. Experimental protocol

## Experiment 1 — Within-layout upper reference

Tune and test on Layout A.

Mục tiêu:

> Xác định performance upper reference khi source và target giống nhau.

## Experiment 2 — Zero-shot cross-layout transfer

Tune on A, test directly on B/C/D/E.

Không retune.

Mục tiêu:

> Đo transfer gap.

## Experiment 3 — Few-shot calibration

Tune on A, calibrate using small number of target instances.

Test on held-out target instances.

Mục tiêu:

> Đo cần bao nhiêu data để phục hồi performance.

## Experiment 4 — Per-layout tuned upper bound

Tune riêng trên từng target layout.

Mục tiêu:

> Upper bound nhưng deployment cost cao.

## Experiment 5 — OOD detection

Đánh giá OOD score có tương quan với performance drop không.

## Experiment 6 — Ablation

Ablations:

```text
A1 No PortConfig
A2 No YardGraph features
A3 No calibration
A4 No OOD detector
A5 No resource/layout features
A6 No fallback mode selection
```

## Statistical Protocol (bắt buộc, dùng chung nguyên tắc với Paper 1 mục 23.6 / Paper 2 mục 44 / Paper 3 mục 32)

Paper 4 đã có cấu trúc lặp theo seed (mục 44.2: 5 seeds) nhưng chưa có hướng dẫn báo cáo CI/kiểm định — bổ sung:

```text
Số lần lặp:
    Đã có: 5 seeds {0,1,2,3,4} × mỗi K value (mục 44.2) — giữ nguyên, không cần thêm.

Báo cáo:
    Mean +/- 95% CI qua 5 seed cho mọi metric ở mục 17 (kể cả Transfer Gap,
    Relative Transfer Gap, Calibration Efficiency, Recovery Ratio).

Kiểm định ý nghĩa:
    Wilcoxon signed-rank test (paired theo seed) khi so Port-GSAR (B8) với
    từng baseline B1-B7 trên Relative Transfer Gap và total cost.
    Hiệu chỉnh Holm-Bonferroni cho 7 so sánh cùng lúc.

Effect size:
    Báo cáo effect size bên cạnh p-value, đặc biệt cho OOD Detection Accuracy
    (mục 41.4) vì số cặp source-target thường nhỏ.

Ablation (Exp 6):
    Áp dụng cùng protocol trên (mỗi ablation A1-A6 vs Port-GSAR đầy đủ).
```

---

# 20. Baselines

> **Bảng baseline chuẩn để code: xem mục 43** — bản dưới đây đánh số B1-B7 khác hoàn toàn với mục 43 (ví dụ B5 ở đây là "Few-shot Port-GSAR/proposed", nhưng B5 ở mục 43 là "Train/tune from scratch"; proposed method ở mục 43 là **B8**). Không dùng bảng dưới để code — chỉ giữ lại để tham khảo ý tưởng ban đầu.

| Baseline (bản cũ, không dùng) | Mô tả | Mục tiêu so sánh |
|---|---|---|
| B1 Per-layout tuned MISR | Tune riêng từng layout | Upper bound |
| B2 Zero-shot MISR | Tune A, test B/C/D/E | Transfer baseline |
| B3 Rule-based default config | Dùng rule mặc định | Production fallback |
| B4 Few-shot scalar calibration | Tune vài hệ số global | Simple calibration baseline |
| B5 Few-shot Port-GSAR | Proposed calibration | Main proposed |
| B6 Train-from-scratch target | Tune/train target từ đầu | Data-expensive upper bound |
| B7 No-OOD transfer | Transfer không detection | Chứng minh OOD cần thiết |

---

# 21. Implementation Appendix

## 21.1. Function: GetTravelTime

> **Chữ ký và pseudocode chuẩn để code: xem mục 37.** Bản dưới đây là phác thảo ban đầu; bản mục 37 bổ sung tham số `crane` để áp `speed_factor × slowdown_factor` — thiếu tham số này thì crane bị `crane_slowdown` sẽ không có travel time tăng lên (đúng lỗi đã phát hiện và sửa ở `TravelTime` của Paper 3). Lưu ý: `crane` ở đây là entry trong `CraneState` **động** (có cả `speed_factor` gốc lẫn `slowdown_factor` hiện tại), không phải `PortConfig.resources.cranes` tĩnh (chỉ có `speed_factor` gốc, không có `slowdown_factor`).

```text
Function GetTravelTime(PortConfig cfg, loc_i, loc_j, crane = None):
    if cfg.travel.mode == "matrix":
        zone_i = ZoneOf(loc_i, cfg)
        zone_j = ZoneOf(loc_j, cfg)
        raw = cfg.travel.travel_time_matrix[zone_i][zone_j]
    else:
        raw = BlockAwareManhattan(loc_i, loc_j,
                                   cfg.travel.fallback_distance.w_block,
                                   cfg.travel.fallback_distance.w_bay,
                                   cfg.travel.fallback_distance.w_row)

    if crane is None:
        return raw

    return raw / (crane.speed_factor * crane.slowdown_factor)
```

## 21.2. Function: BuildPortFeatures

```text
Function BuildPortFeatures(PortConfig, YardGraph):
    features = {}
    features.num_blocks = count_blocks(PortConfig)
    features.num_stacks = count_stacks(PortConfig)
    features.avg_capacity = mean_stack_capacity(PortConfig)
    features.travel_mean = mean_travel_time(PortConfig)
    features.travel_std = std_travel_time(PortConfig)
    features.crane_count = count_cranes(PortConfig)
    features.zone_overlap = crane_zone_overlap(CraneConfig)
    features.safety_rule_count = count_safety_rules(PortConfig)
    return features
```

## 21.3. Function: ComputeOODScore

> **Pseudocode chuẩn để code: xem mục 39.1–39.2** (chuẩn hóa theo `source_stats` trước khi tính khoảng cách theo 7 nhóm feature qua `GroupFeatures`/`GroupDistance`, mục 39.1.1). Bản dưới đây tính trực tiếp trên giá trị thô theo từng feature đơn lẻ — không dùng để code.

```text
Function ComputeOODScore(source_features, target_features, weights):
    score = 0
    For each feature f:
        diff = abs(target_features[f] - source_features[f])
        norm_diff = diff / max(epsilon, abs(source_features[f]))
        score += weights[f] * norm_diff
    return min(1, score)
```

## 21.4. Function: CalibrateTarget

```text
Function CalibrateTarget(source_params, target_calibration_set):
    params = copy(source_params)
    candidate_param_sets = GenerateLocalParamGrid(params)

    best_params = params
    best_score = INF

    For theta in candidate_param_sets:
        score = Evaluate(theta, target_calibration_set)
        if score < best_score:
            best_score = score
            best_params = theta

    return best_params
```

## 21.5. Function: SelectDeploymentMode

> **Chữ ký, mode taxonomy và pseudocode chuẩn để code: xem mục 47.2.** Bản dưới đây là phác thảo ban đầu, dùng ngưỡng OOD thô 0.2/0.5/0.7 và 4 mode (`FULL_RECOMMENDATION/ADVISORY_ONLY/CONSERVATIVE_REPAIR/MANUAL_REVIEW`) — khác cả ngưỡng (mục 47 dùng `theta_zero_shot=0.30`/`theta_few_shot=0.60`, không có mốc 0.7 riêng) lẫn tên/số lượng mode (mục 47.1 dùng `MODE_0..MODE_4`, có thêm check an toàn cứng `safety_status` mà bản dưới không có). Không dùng bản dưới để code.

```text
Function SelectDeploymentMode(OOD, state_confidence, calibration_size):
    if OOD < 0.2 and state_confidence > 0.8:
        return FULL_RECOMMENDATION

    if OOD < 0.5 and calibration_size >= 10:
        return ADVISORY_ONLY

    if OOD < 0.7:
        return CONSERVATIVE_REPAIR

    return MANUAL_REVIEW
```

---

# 22. Parameter table

> Bảng này đã đồng bộ với mục 48 (patch) — dùng chung một nguồn, không còn giá trị khác nhau giữa hai bảng.

| Parameter | Meaning | Default | Range |
|---|---|---:|---|
| `w_block` | block distance weight | 10 | 5, 10, 20 |
| `w_bay` | bay distance weight | 1 | 1, 2 |
| `w_row` | row distance weight | 1 | 1, 2 |
| `lambda` | container-plan stability weight (`λ`) | 1.0 | 0.5, 1, 2 |
| `lambda_res` | resource-stability weight (`λ_res`) — mới, khớp Paper 3 | 1.0 | 0.5, 1, 2 |
| `pi` | data confidence weight (`π`) — mới, khớp Paper 3 | 0.5 | 0, 0.5, 1 |
| `mu` | execution weight (`μ`) | 1.0 | 0.5, 1, 2 |
| `nu` | resource weight (`ν`) | 1.0 | 0.5, 1, 2 |
| `omega` | safety weight | 5.0 | 1, 5, 10 |
| `eta` | intervention complexity weight | 0.5 | 0.1, 0.5, 1 |
| `xi` | calibration cost weight | 0.2 | 0.1, 0.2, 0.5 |
| `zeta` | OOD risk weight | 1.0 | 0.5, 1, 2 |
| `theta_zero_shot` | zero-shot threshold (trước gọi là `OOD_low=0.2`, đã sửa khớp mục 33.3/48) | 0.30 | 0.1, 0.2, 0.3 |
| `theta_few_shot` | calibration threshold (trước gọi là `OOD_mid=0.5`, đã sửa khớp mục 33.3/48) | 0.60 | 0.4, 0.5, 0.6 |
| `calib_n` | calibration samples | 10 | 0, 5, 10, 20, 50 |
| `epsilon` | numeric stability | 1e-6 | fixed |

---

# 23. Ground truth / proxy

Paper 4 không cần true optimum tuyệt đối cho mọi layout.

Dùng:

```text
Small instances:
  exhaustive search / enumerated parameter tuning where possible

Medium/Large:
  per-layout tuned MISR with extended time budget as high-quality proxy

Transfer comparison:
  compare zero-shot/few-shot against per-layout tuned upper reference
```

Không gọi per-layout tuned là true optimum.

Gọi là:

> offline high-quality per-layout reference.

---

# 24. Timeout protocol

> **Số liệu chuẩn để code: xem mục 46.1/46.2** — bản dưới đây (Small 3s/Medium 12s/Large 60s cho decision runtime, và bucket 10/30 phút cho calibration) là bản phác thảo ban đầu, **khác số** với mục 46 (Small 5s/Medium 20s/Large 90s; calibration theo K cụ thể 120/300/600/1200s). Không dùng số ở đây để code.

```text
Decision runtime:      xem mục 46.1
Calibration runtime:   xem mục 46.2 (theo từng K, không dùng bucket 5-10/25-50 mẫu)
```

Báo cáo:

```text
mean runtime
P95 runtime
timeout rate
calibration time
fallback rate
```

---

# 25. Walkthrough example

## Source layout A

```text
3 blocks, 2 cranes, uniform travel
Tune MISR parameters on 200 instances.
```

## Target layout C

```text
5 blocks, asymmetric travel, 3 cranes.
```

## Step 1 — Build PortConfig_C

```text
Load layout, crane zones, travel matrix, safety rules.
```

## Step 2 — Build YardGraph_C

```text
Create block/bay/stack/crane-zone graph.
```

## Step 3 — Compute OOD

```text
OOD(A,C) = 0.43
```

Decision:

```text
Few-shot calibration required.
```

## Step 4 — Calibrate with 10 target instances

Tune:

```text
theta_trigger
resource_weight
travel_speed_factor
stability_weight
```

## Step 5 — Test on 100 held-out instances

Compare:

```text
zero-shot
few-shot calibrated
per-layout tuned
rule-based fallback
```

Expected result:

```text
few-shot Port-GSAR reduces transfer gap significantly while using much less target data than full per-layout tuning.
```

---

# 26. Q1 contribution claims

## C1

Đề xuất bài toán **cross-terminal generalization for stable adaptive yard decision-making**.

## C2

Đề xuất **PortConfig + YardGraph representation** để tách decision logic khỏi layout cụ thể.

## C3

Đề xuất **zero-shot/few-shot transfer protocol** cho SAR/MISR framework.

## C4

Đề xuất **OOD-aware deployment mode selection** để tránh áp dụng framework quá tự tin trên terminal khác biệt.

## C5

Xây dựng benchmark đa layout để đánh giá transfer gap, calibration efficiency và OOD risk.

---

# 27. Production value

Paper 4 là paper có giá trị sản phẩm mạnh nhất.

Nó trả lời trực tiếp:

> Cùng một nền tảng có triển khai được cho nhiều cảng không?

Production architecture sau Paper 4:

```text
Core Decision Engine
        +
PortConfig Adapter
        +
YardGraph Builder
        +
Calibration Layer
        +
OOD/Fallback Controller
```

Khi onboard terminal mới:

```text
Step 1: Create PortConfig
Step 2: Build YardGraph
Step 3: Run zero-shot shadow evaluation
Step 4: Compute OOD
Step 5: Few-shot calibration if needed
Step 6: Advisory mode deployment
Step 7: Gradual production rollout
```

---

# 28. Limitations

Paper 4 vẫn có giới hạn:

- chưa chứng minh chạy mọi terminal thật;
- benchmark đa layout vẫn có thể là synthetic;
- PortConfig cần được mapping từ dữ liệu thực;
- few-shot calibration có thể không đủ nếu target terminal quá khác;
- OOD detector là heuristic trong phiên bản đầu;
- Related Work grounding còn thiếu citation cho transfer learning/OOD detection/few-shot learning (mục 5);
- B2 (per-layout tuned Paper 3 MISR-Yard) vẫn phụ thuộc gián tiếp Shin et al. 2026 qua Paper 3, chưa xác minh citation.

Nhưng các giới hạn này chấp nhận được nếu paper trình bày đúng mức.

---

# 29. Future work

Sau Paper 4 có thể mở rộng:

```text
real terminal historical logs
operator-in-the-loop calibration
continual learning across terminals
federated learning for port groups
economic ROI model
integration with real TOS/TAS/ECS APIs
```

---

# 30. Kết luận

Paper 4 đủ mạnh nếu không định vị là “test nhiều layout”, mà định vị là:

> **Port-configurable and generalizable stable adaptive yard decision intelligence.**

Đây là bước cuối cùng biến chuỗi SAR-CRP/MISR-Yard từ một nhóm thuật toán thành nền tảng có khả năng triển khai thực tế.

Câu chuyện cuối:

```text
Paper 1: stable under evolving retrieval information
Paper 2: robust under imperfect execution
Paper 3: strategic under multiple intervention options
Paper 4: deployable across heterogeneous terminals
```

Câu chốt:

> **Port-GSAR makes stable adaptive yard decision-making configurable, transferable and deployment-ready across heterogeneous container terminals.**

---

# 31. ULTRA IMPLEMENTATION APPENDIX — CODE-READY VERSION

Phần này cập nhật Paper 4 theo review mới nhất của giáo sư. Mục tiêu là đưa Port-GSAR từ mức **research concept with architecture** lên mức **CODE-READY**, tương đương Paper 1, Paper 2 và Paper 3.

Các bổ sung chính:

1. Schema đầy đủ cho `YardGraph`, `OODScore`, `CalibrationResult`.
2. Pseudocode chi tiết cho `BuildYardGraph`, `ExtractLayoutFeatures`, `ExtractResourceFeatures`, `ExtractRiskFeatures`.
3. Pseudocode cho `ComputeTransferGap`, `EvaluateFewShotCalibration`, `OODDetectionAccuracy`.
4. Chi tiết hóa `CalibrateTarget`, `GenerateLocalParamGrid`, parameter space và stop condition.
5. Mô tả baseline B4 và B7 rõ hơn.
6. Làm rõ module nào kế thừa từ Paper 3 và module nào cần sửa để đọc `PortConfig/YardGraph`.
7. Bổ sung discussion về real terminal data và synthetic-to-real gap.
8. Bổ sung coding checklist cuối cùng trước khi code.

---

# 32. Schema chi tiết cho YardGraph

## 32.1. Mục tiêu

`YardGraph` là biểu diễn graph chuẩn hóa của một terminal. Nó giúp Port-GSAR không phụ thuộc vào layout cố định.

Một terminal mới được đưa vào hệ thống qua:

```text
PortConfig
    ↓
BuildYardGraph(PortConfig)
    ↓
YardGraph
    ↓
Feature extraction + shared decision engine
```

`YardGraph` phải biểu diễn được:

- block;
- bay;
- row;
- stack;
- crane zone;
- gate/vessel interface nếu có;
- travel relation;
- accessibility relation;
- conflict relation;
- containment relation.

## 32.2. JSON schema

```json
{
  "graph_id": "YG_PORT_A",
  "port_id": "PORT_A",
  "version": "1.0",
  "time_unit": "simulation_step",
  "nodes": [
    {
      "id": "B1",
      "type": "block",
      "features": {
        "num_bays": 10,
        "num_rows": 6,
        "max_stack_height": 5,
        "current_occupancy": 0.72,
        "zone_id": "Z1",
        "is_active": true
      }
    },
    {
      "id": "S_B1_03_02",
      "type": "stack",
      "features": {
        "block_id": "B1",
        "bay": 3,
        "row": 2,
        "capacity": 5,
        "height": 4,
        "occupancy_ratio": 0.80,
        "top_container_priority": 7,
        "is_full": false,
        "is_locked": false,
        "hazard_class_allowed": true,
        "zone_id": "Z1"
      }
    },
    {
      "id": "Z1",
      "type": "crane_zone",
      "features": {
        "num_cranes": 2,
        "available_cranes": 1,
        "workload": 14.0,
        "conflict_level": 0.2,
        "safety_distance": 1
      }
    }
  ],
  "edges": [
    {
      "from": "B1",
      "to": "S_B1_03_02",
      "type": "contains",
      "weight": 1.0,
      "features": {
        "relation": "block_contains_stack"
      }
    },
    {
      "from": "S_B1_03_02",
      "to": "S_B1_03_03",
      "type": "adjacency",
      "weight": 1.0,
      "features": {
        "distance_unit": 1,
        "same_block": true
      }
    },
    {
      "from": "Z1",
      "to": "Z2",
      "type": "travel",
      "weight": 5.0,
      "features": {
        "travel_time": 5.0,
        "time_unit": "simulation_step",
        "source": "travel_time_matrix"
      }
    },
    {
      "from": "Z1",
      "to": "Z2",
      "type": "conflict",
      "weight": 1.0,
      "features": {
        "conflict_type": "shared_boundary",
        "hard_conflict": false,
        "soft_penalty": 0.5
      }
    }
  ],
  "metadata": {
    "num_blocks": 3,
    "num_stacks": 180,
    "num_crane_zones": 4,
    "num_cranes": 5,
    "layout_family": "asymmetric_medium",
    "created_from": "PortConfig",
    "supports_travel_matrix": true,
    "supports_safety_rules": true
  }
}
```

## 32.3. Quy ước thời gian

Tất cả trường thời gian trong Paper 4 dùng cùng đơn vị:

```text
time_unit = simulation_step
```

Các trường sau đều dùng `simulation_step`:

- `travel_time_matrix`;
- `estimated_start`;
- `estimated_finish`;
- `handling_time`;
- `available_from`;
- `timeout` khi mô phỏng theo step.

Nếu dùng dữ liệu thực, thời gian thực tế như giây/phút phải được chuẩn hóa về `simulation_step` trước khi đưa vào benchmark.

---

# 33. Schema cho OODScore

## 33.1. Mục tiêu

`OODScore` cho biết terminal đích khác terminal nguồn đến mức nào. Nếu khác biệt quá lớn, hệ thống không nên dùng zero-shot một cách mù quáng.

## 33.2. JSON schema

```json
{
  "ood_id": "OOD_PORT_A_TO_PORT_C_001",
  "source_port": "PORT_A",
  "target_port": "PORT_C",
  "ood_score": 0.43,
  "thresholds": {
    "zero_shot_max": 0.30,
    "few_shot_max": 0.60,
    "manual_review_min": 0.60
  },
  "feature_contributions": {
    "layout_size_shift": 0.12,
    "stack_height_shift": 0.04,
    "travel_time_shift": 0.18,
    "crane_zone_shift": 0.08,
    "occupancy_shift": 0.05,
    "safety_rule_shift": 0.06,
    "data_reliability_shift": 0.03
  },
  "decision": "FEW_SHOT_CALIBRATION_REQUIRED",
  "recommended_mode": "CALIBRATED_DEPLOYMENT",
  "explanation": "Target port has larger travel-time shift and different crane-zone structure than the source port.",
  "created_at_step": 0
}
```

## 33.3. Decision rule

```text
if ood_score <= theta_zero_shot:
    decision = ZERO_SHOT_ALLOWED
elif ood_score <= theta_few_shot:
    decision = FEW_SHOT_CALIBRATION_REQUIRED
else:
    decision = MANUAL_REVIEW_OR_SAFE_FALLBACK
```

Default:

```text
theta_zero_shot = 0.30
theta_few_shot  = 0.60
```

---

# 34. Schema cho CalibrationResult

## 34.1. Mục tiêu

`CalibrationResult` ghi lại quá trình hiệu chỉnh khi chuyển framework từ terminal nguồn sang terminal đích.

Nó phục vụ 3 mục tiêu:

1. reproducibility cho paper;
2. audit trail cho production;
3. đo calibration efficiency.

## 34.2. JSON schema

```json
{
  "calibration_id": "CAL_PORT_A_TO_PORT_C_K10",
  "source_port": "PORT_A",
  "target_port": "PORT_C",
  "calibration_samples": 10,
  "validation_samples": 30,
  "params_tuned": [
    "theta_trigger",
    "lambda_stability",
    "nu_resource",
    "eta_intervention",
    "theta_ood"
  ],
  "params_source": {
    "theta_trigger": 0.30,
    "lambda_stability": 1.00,
    "nu_resource": 1.00,
    "eta_intervention": 0.50,
    "theta_ood": 0.30
  },
  "params_final": {
    "theta_trigger": 0.35,
    "lambda_stability": 1.20,
    "nu_resource": 1.30,
    "eta_intervention": 0.50,
    "theta_ood": 0.30
  },
  "search_method": "local_grid_search",
  "search_budget": 81,
  "stop_condition": "grid_exhausted",
  "transfer_gap_before": 0.35,
  "transfer_gap_after": 0.12,
  "recovery_ratio": 0.66,
  "best_validation_score": 118.5,
  "runtime_seconds": 42.0,
  "status": "SUCCESS"
}
```

---

# 35. Schema cho PortTransferExperiment

Để chạy thí nghiệm cross-terminal có kiểm soát, mỗi experiment nên có schema riêng.

```json
{
  "experiment_id": "TRANSFER_A_TO_C_K10_SEED0",
  "source_port": "PORT_A",
  "target_port": "PORT_C",
  "source_train_instances": 200,
  "target_calibration_instances": 10,
  "target_test_instances": 100,
  "transfer_mode": "few_shot_calibration",
  "ood_detection_enabled": true,
  "calibration_enabled": true,
  "baseline_name": "Port-GSAR",
  "random_seed": 0,
  "metrics": {
    "J_source_tuned": null,
    "J_target_zero_shot": null,
    "J_target_calibrated": null,
    "J_target_per_layout_tuned": null,
    "transfer_gap": null,
    "relative_transfer_gap": null,
    "recovery_ratio": null,
    "ood_accuracy": null
  }
}
```

---

# 36. Pseudocode chi tiết: BuildYardGraph

## 36.1. Input/Output

Input:

```text
PortConfig cfg           (bắt buộc — cấu hình tĩnh, mục 9.2)
YardState state           (tùy chọn — occupancy/stack động; mặc định state trung lập nếu None)
CraneState craneState     (tùy chọn — trạng thái crane động; mặc định trung lập nếu None)
```

`state`/`craneState` là **tùy chọn** vì `BuildYardGraph` phục vụ 2 mục đích khác nhau:

```text
(a) Feature extraction / OOD (mục 38-41): chỉ cần cấu trúc layout (block/bay/stack/zone/travel/
    safety) để so sánh source vs target — dùng state trung lập (occupancy=0, mọi crane
    "available") vì OOD quan tâm khác biệt CẤU TRÚC, không phải state tức thời.
(b) Decision engine tại runtime (Paper 3 MISR-Yard adapter, mục 42.2): cần state/craneState
    thật của instance đang xử lý.
```

Output:

```text
YardGraph
```

## 36.2. Pseudocode

```text
Function BuildYardGraph(PortConfig cfg, YardState state = None, CraneState craneState = None):
    G = EmptyGraph()
    If state is None:
        state = NeutralYardState(cfg)          # occupancy = 0 mọi stack
    If craneState is None:
        craneState = NeutralCraneState(cfg)    # mọi crane "available", workload = 0

    # 1. Add block nodes
    For each block in cfg.layout.blocks:
        node = {
            id: block.block_id,
            type: "block",
            features: {
                num_bays: block.num_bays,
                num_rows: block.num_rows,
                max_stack_height: block.max_stack_height,
                current_occupancy: ComputeBlockOccupancy(block, state),
                zone_id: block.zone_id,
                is_active: block.is_active
            }
        }
        G.add_node(node)

    # 2. Add stack nodes and containment edges
    For each block in cfg.layout.blocks:
        For bay in 1..block.num_bays:
            For row in 1..block.num_rows:
                stack_id = MakeStackId(block.block_id, bay, row)
                stack = state.stacks[stack_id]
                stack_node = {
                    id: stack_id,
                    type: "stack",
                    features: {
                        block_id: block.block_id,
                        bay: bay,
                        row: row,
                        capacity: block.max_stack_height,
                        height: stack.height,
                        occupancy_ratio: stack.height / block.max_stack_height,
                        top_container_priority: GetTopPriority(stack),
                        is_full: stack.height >= block.max_stack_height,
                        is_locked: stack.is_locked,
                        hazard_class_allowed: stack.hazard_class_allowed,
                        zone_id: block.zone_id
                    }
                }
                G.add_node(stack_node)
                G.add_edge(block.block_id, stack_id, type="contains", weight=1.0)

    # 3. Add crane-zone nodes
    For each zone in cfg.resources.crane_zones:
        zone_node = {
            id: zone.zone_id,
            type: "crane_zone",
            features: {
                num_cranes: CountCranes(zone, cfg.resources.cranes),
                available_cranes: CountAvailableCranes(zone, craneState),
                workload: EstimateZoneWorkload(zone, craneState),
                conflict_level: EstimateZoneConflictLevel(zone, cfg.safety_rules),
                safety_distance: zone.safety_distance
            }
        }
        G.add_node(zone_node)

    # 4. Add stack adjacency edges
    For each pair of stack nodes (s_i, s_j):
        If SameBlock(s_i, s_j) and ManhattanAdjacent(s_i, s_j):
            G.add_edge(s_i.id, s_j.id, type="adjacency", weight=1.0)

    # 5. Add stack-to-zone accessibility edges
    For each stack node s:
        z = s.features.zone_id
        G.add_edge(z, s.id, type="access", weight=1.0)

    # 6. Add travel edges between zones
    For each zone pair (z_i, z_j):
        travel_time = GetTravelTime(cfg, z_i, z_j)
        G.add_edge(z_i.id, z_j.id, type="travel", weight=travel_time)

    # 7. Add conflict edges between zones
    For each safety rule in cfg.safety_rules:
        If safety_rule.type in {"zone_conflict", "crane_interference"}:
            G.add_edge(
                safety_rule.zone_a,
                safety_rule.zone_b,
                type="conflict",
                weight=safety_rule.penalty_weight,
                features={
                    hard_conflict: safety_rule.is_hard,
                    conflict_type: safety_rule.type
                }
            )

    # 8. Attach metadata
    G.metadata = {
        graph_id: "YG_" + cfg.port_id,
        port_id: cfg.port_id,
        num_blocks: CountBlockNodes(G),
        num_stacks: CountStackNodes(G),
        num_crane_zones: CountZoneNodes(G),
        num_cranes: CountTotalCranes(cfg.resources.cranes),   # đổi tên để hết trùng với CountCranes(zone, cranes) ở bước 3
        layout_family: cfg.layout_family,                     # field top-level, không nằm trong cfg.layout
        supports_travel_matrix: cfg.travel.travel_time_matrix is not None,
        supports_safety_rules: cfg.safety_rules is not None
    }

    Return G
```

---

# 37. Pseudocode: GetTravelTime

Paper 4 ưu tiên `travel_time_matrix` vì gần với production hơn. Nếu terminal chưa có matrix, dùng block-aware Manhattan làm fallback. Khi gọi cho mục đích cấu trúc/OOD thuần túy (không có crane cụ thể — vd. `ExtractLayoutFeatures`), truyền `crane = None` để bỏ qua hệ số tốc độ.

```text
Function GetTravelTime(PortConfig cfg, location_a, location_b, crane = None):
    # location can be zone_id, block_id, or stack_id.
    zone_a = ResolveZone(location_a, cfg)
    zone_b = ResolveZone(location_b, cfg)

    If cfg.travel.travel_time_matrix exists:
        If zone_a in cfg.travel.travel_time_matrix and zone_b in cfg.travel.travel_time_matrix[zone_a]:
            raw = cfg.travel.travel_time_matrix[zone_a][zone_b]
        Else:
            raw = None
    Else:
        raw = None

    If raw is None:
        # Fallback: block-aware Manhattan distance
        coord_a = ResolveCoordinate(location_a, cfg)
        coord_b = ResolveCoordinate(location_b, cfg)

        block_diff = 1 if coord_a.block_id != coord_b.block_id else 0
        bay_diff   = abs(coord_a.bay - coord_b.bay)
        row_diff   = abs(coord_a.row - coord_b.row)

        raw = cfg.travel.fallback_distance.w_block * block_diff \
            + cfg.travel.fallback_distance.w_bay   * bay_diff \
            + cfg.travel.fallback_distance.w_row   * row_diff

    If crane is None:
        return raw

    return raw / (crane.speed_factor * crane.slowdown_factor)
```

Default (nếu `cfg.travel.fallback_distance` không có sẵn):

```text
w_block = 10
w_bay   = 1
w_row   = 1
```

---

# 38. Pseudocode: Feature extraction

Port-GSAR dùng feature vector cấp terminal để:

- so sánh source và target terminal;
- tính OOD score;
- chọn deployment mode;
- hỗ trợ few-shot calibration.

## 38.1. ExtractPortFeatures

```text
Function ExtractPortFeatures(YardGraph G, PortConfig cfg):
    yard_features     = ExtractYardFeatures(G)
    layout_features   = ExtractLayoutFeatures(G, cfg)
    resource_features = ExtractResourceFeatures(G, cfg)
    risk_features     = ExtractRiskFeatures(G, cfg)

    return Concatenate(
        yard_features,
        layout_features,
        resource_features,
        risk_features
    )
```

## 38.2. ExtractYardFeatures

```text
Function ExtractYardFeatures(YardGraph G):
    occupancy = []
    heights = []
    capacities = []
    top_priorities = []

    For each node in G.nodes:
        If node.type == "stack":
            occupancy.append(node.features.occupancy_ratio)
            heights.append(node.features.height)
            capacities.append(node.features.capacity)
            top_priorities.append(node.features.top_container_priority)

    return {
        "occupancy_mean": Mean(occupancy),
        "occupancy_max": Max(occupancy),
        "occupancy_std": Std(occupancy),
        "height_mean": Mean(heights),
        "height_max": Max(heights),
        "capacity_mean": Mean(capacities),
        "num_near_full_stacks": Count(x > 0.80 for x in occupancy),
        "near_full_ratio": Count(x > 0.80 for x in occupancy) / Len(occupancy),
        "priority_mean": Mean(top_priorities),
        "priority_std": Std(top_priorities)
    }
```

## 38.3. ExtractLayoutFeatures

```text
Function ExtractLayoutFeatures(YardGraph G, PortConfig cfg):
    block_nodes = FilterNodes(G, type="block")
    stack_nodes = FilterNodes(G, type="stack")
    zone_nodes  = FilterNodes(G, type="crane_zone")

    bays_per_block = []
    rows_per_block = []
    heights_per_block = []

    For each block in block_nodes:
        bays_per_block.append(block.features.num_bays)
        rows_per_block.append(block.features.num_rows)
        heights_per_block.append(block.features.max_stack_height)

    adjacency_edges = FilterEdges(G, type="adjacency")
    travel_edges = FilterEdges(G, type="travel")
    conflict_edges = FilterEdges(G, type="conflict")

    return {
        "num_blocks": Len(block_nodes),
        "num_stacks": Len(stack_nodes),
        "num_crane_zones": Len(zone_nodes),
        "bays_mean": Mean(bays_per_block),
        "bays_std": Std(bays_per_block),
        "rows_mean": Mean(rows_per_block),
        "rows_std": Std(rows_per_block),
        "max_stack_height_mean": Mean(heights_per_block),
        "max_stack_height_std": Std(heights_per_block),
        "adjacency_density": Len(adjacency_edges) / Max(1, Len(stack_nodes)),
        "travel_edge_density": Len(travel_edges) / Max(1, Len(zone_nodes)^2),
        "conflict_edge_density": Len(conflict_edges) / Max(1, Len(zone_nodes)^2),
        "is_asymmetric": ComputeAsymmetryScore(block_nodes)
    }
```

## 38.4. ExtractResourceFeatures

```text
Function ExtractResourceFeatures(YardGraph G, PortConfig cfg):
    cranes = cfg.resources.cranes
    zones = FilterNodes(G, type="crane_zone")

    speed_factors = []
    availability = []
    workloads = []

    For each crane in cranes:
        speed_factors.append(crane.speed_factor)
        availability.append(1 if crane.status == "available" else 0)

    For each zone in zones:
        workloads.append(zone.features.workload)

    travel_times = []
    For each edge in G.edges:
        If edge.type == "travel":
            travel_times.append(edge.weight)

    return {
        "num_cranes": Len(cranes),
        "available_crane_ratio": Mean(availability),
        "crane_speed_mean": Mean(speed_factors),
        "crane_speed_min": Min(speed_factors),
        "crane_speed_std": Std(speed_factors),
        "workload_mean": Mean(workloads),
        "workload_max": Max(workloads),
        "workload_std": Std(workloads),
        "workload_imbalance": Std(workloads),
        "travel_time_mean": Mean(travel_times),
        "travel_time_max": Max(travel_times),
        "travel_time_std": Std(travel_times)
    }
```

## 38.5. ExtractRiskFeatures

```text
Function ExtractRiskFeatures(YardGraph G, PortConfig cfg):
    safety_rules = cfg.safety_rules
    reliability = cfg.data_reliability

    hard_rules = Count(rule.is_hard == true for rule in safety_rules)
    soft_rules = Count(rule.is_hard == false for rule in safety_rules)

    source_factors = []
    For each source in reliability.sources:
        source_factors.append(source.reliability_factor)

    conflict_edges = FilterEdges(G, type="conflict")
    hard_conflict_edges = Count(e.features.hard_conflict == true for e in conflict_edges)

    return {
        "num_safety_rules": Len(safety_rules),
        "num_hard_rules": hard_rules,
        "num_soft_rules": soft_rules,
        "hard_rule_ratio": hard_rules / Max(1, Len(safety_rules)),
        "num_conflict_edges": Len(conflict_edges),
        "hard_conflict_ratio": hard_conflict_edges / Max(1, Len(conflict_edges)),
        "data_reliability_mean": Mean(source_factors),
        "data_reliability_min": Min(source_factors),
        "data_reliability_std": Std(source_factors),
        "manual_data_dependency": reliability.manual_update_ratio
    }
```

---

# 39. Pseudocode: OOD score

## 39.1. Feature normalization

Trước khi tính OOD, các feature cần được chuẩn hóa theo thống kê của source layouts.

```text
Function NormalizeFeatures(x, source_stats):
    x_norm = {}
    For each feature k in x:
        mean_k = source_stats[k].mean
        std_k  = source_stats[k].std
        x_norm[k] = (x[k] - mean_k) / Max(std_k, epsilon)
    Return x_norm
```

## 39.1.1. GroupFeatures — cầu nối giữa `ExtractPortFeatures` (phẳng) và `ComputeOODScore` (theo nhóm)

`ExtractPortFeatures` (mục 38.1) trả về một dict phẳng ~30 field riêng lẻ (gộp từ 4 hàm con `ExtractYardFeatures/ExtractLayoutFeatures/ExtractResourceFeatures/ExtractRiskFeatures`). `ComputeOODScore` (mục 39.2) lại cần dữ liệu theo **7 nhóm** (`layout_size, stack_height, travel_time, crane_zone, occupancy, safety_rule, data_reliability`). Trước đây không có hàm nối hai bên — bổ sung `GroupFeatures`:

```text
Function GroupFeatures(flat_features):
    Return {
        "layout_size": Select(flat_features,
            ["num_blocks", "num_stacks", "num_crane_zones", "bays_mean", "rows_mean", "num_cranes"]),
        "stack_height": Select(flat_features,
            ["max_stack_height_mean", "max_stack_height_std", "height_mean", "height_max", "capacity_mean"]),
        "travel_time": Select(flat_features,
            ["travel_time_mean", "travel_time_max", "travel_time_std", "travel_edge_density"]),
        "crane_zone": Select(flat_features,
            ["crane_speed_mean", "crane_speed_min", "crane_speed_std", "available_crane_ratio",
             "conflict_edge_density", "is_asymmetric"]),
        "occupancy": Select(flat_features,
            ["occupancy_mean", "occupancy_max", "occupancy_std", "num_near_full_stacks",
             "near_full_ratio", "workload_mean", "workload_max", "workload_std", "workload_imbalance"]),
        "safety_rule": Select(flat_features,
            ["num_safety_rules", "num_hard_rules", "num_soft_rules", "hard_rule_ratio",
             "num_conflict_edges", "hard_conflict_ratio"]),
        "data_reliability": Select(flat_features,
            ["data_reliability_mean", "data_reliability_min", "data_reliability_std",
             "manual_data_dependency"])
    }
```

`Select(dict, keys)` trả về sub-dict chỉ gồm các key liệt kê. `GroupDistance(source_group, target_group)` (dùng ở mục 39.2) = trung bình `|target[k] - source[k]|` đã chuẩn hóa (mục 39.1) trên toàn bộ key trong nhóm.

## 39.2. ComputeOODScore

```text
Function ComputeOODScore(source_features, target_features, weights, source_stats):
    # source_features, target_features: output phẳng của ExtractPortFeatures (mục 38.1)
    source_norm = NormalizeFeatures(source_features, source_stats)
    target_norm = NormalizeFeatures(target_features, source_stats)

    source_grouped = GroupFeatures(source_norm)
    target_grouped = GroupFeatures(target_norm)

    contributions = {}
    total = 0

    For each feature group g in {
        layout_size,
        stack_height,
        travel_time,
        crane_zone,
        occupancy,
        safety_rule,
        data_reliability
    }:
        # weights và contributions dùng key "<g>_shift" để khớp OOD_WEIGHTS (mục 39.3)
        # và OODScore.feature_contributions (mục 33.2); GroupFeatures (mục 39.1.1) vẫn
        # dùng key trần "g" vì đó là tên nhóm nội bộ, không phải tên report ra ngoài.
        diff_g = GroupDistance(source_grouped[g], target_grouped[g])
        contrib_g = weights[g + "_shift"] * diff_g
        contributions[g + "_shift"] = contrib_g
        total += contrib_g

    ood_score = Min(1.0, total)

    If ood_score <= theta_zero_shot:
        decision = "ZERO_SHOT_ALLOWED"
    Else if ood_score <= theta_few_shot:
        decision = "FEW_SHOT_CALIBRATION_REQUIRED"
    Else:
        decision = "MANUAL_REVIEW_OR_SAFE_FALLBACK"

    Return OODScore(
        ood_score=ood_score,
        feature_contributions=contributions,
        decision=decision
    )
```

## 39.3. OOD weights

Default heuristic weights:

```text
layout_size_shift      = 0.15
stack_height_shift     = 0.10
travel_time_shift      = 0.25
crane_zone_shift       = 0.15
occupancy_shift        = 0.10
safety_rule_shift      = 0.15
data_reliability_shift = 0.10
```

Trong paper này, OOD weights được đặt theo domain knowledge. Học OOD weights từ dữ liệu transfer lịch sử là future work.

## 39.4. OOD validation protocol

Để validate OOD detector, tạo cặp source-target với nhãn:

```text
in_distribution: transfer gap <= tau_good
ood:             transfer gap > tau_bad
```

Default:

```text
tau_good = 0.10
tau_bad  = 0.30
```

Nếu transfer gap nằm giữa 0.10 và 0.30, xem là uncertain và không dùng để tính accuracy chính.

---

# 40. Pseudocode: CalibrateTarget chi tiết

## 40.1. Parameter groups được calibrate

Paper 4 không tune toàn bộ framework. Chỉ tune một tập nhỏ tham số production-critical.

> **Ký hiệu thống nhất với mục 13.2/16.1/22** (bản trước dùng `mu_data/nu_execution/psi_resource` — đảo ngược hoàn toàn so với 2 chỗ kia dùng `μ=execution, ν=resource`; đã sửa lại theo số đông và bổ sung `π` cho data weight khớp Paper 3):

```text
Tunable parameters:
- theta_trigger
- lambda_stability        (λ — container-plan stability)
- pi_data                 (π — data confidence weight, mới thêm khớp Paper 3)
- mu_execution            (μ — execution weight)
- nu_resource             (ν — resource weight)
- eta_intervention        (η — intervention complexity weight)
- speed_factor            (khớp Strategy D mục 13.5 / walkthrough mục 25)
- handling_time_factor    (khớp Strategy D mục 13.5 / walkthrough mục 25)
- theta_ood
```

## 40.2. Parameter search space

Local grid quanh tham số source:

```text
theta_trigger:         source * {0.8, 1.0, 1.2}
lambda_stability:      source * {0.8, 1.0, 1.2}
pi_data:               source * {0.8, 1.0, 1.2}
mu_execution:          source * {0.8, 1.0, 1.2}
nu_resource:           source * {0.7, 1.0, 1.3}
eta_intervention:      source * {0.8, 1.0, 1.2}
speed_factor:          source * {0.8, 1.0, 1.2}
handling_time_factor:  source * {0.8, 1.0, 1.2}
theta_ood:             source + {-0.05, 0, +0.05}
```

Để tránh explosion, không grid toàn bộ 7 tham số cùng lúc. Dùng staged grid search.

## 40.3. GenerateLocalParamGrid

```text
Function GenerateLocalParamGrid(source_params, ood_score):
    grid = []

    # Stage 1: trigger and stability
    For theta_trigger in source.theta_trigger * {0.8, 1.0, 1.2}:
        For lambda_stability in source.lambda_stability * {0.8, 1.0, 1.2}:
            params = copy(source_params)
            params.theta_trigger = Clip(theta_trigger, 0.05, 0.90)
            params.lambda_stability = Clip(lambda_stability, 0.10, 10.0)
            grid.append(params)

    # Stage 2: resource and intervention if target has resource shift
    If ood_score.feature_contributions["crane_zone_shift"] > 0.05
       or ood_score.feature_contributions["travel_time_shift"] > 0.10:
        expanded = []
        For params in grid:
            For nu_resource in source.nu_resource * {0.7, 1.0, 1.3}:
                For eta_intervention in source.eta_intervention * {0.8, 1.0, 1.2}:
                    p = copy(params)
                    p.nu_resource = Clip(nu_resource, 0.10, 10.0)
                    p.eta_intervention = Clip(eta_intervention, 0.00, 5.0)
                    expanded.append(p)
        grid = expanded

    # Stage 3: data/execution if target has reliability shift
    If ood_score.feature_contributions["data_reliability_shift"] > 0.05:
        expanded = []
        For params in grid:
            For pi_data in source.pi_data * {0.8, 1.0, 1.2}:
                For mu_execution in source.mu_execution * {0.8, 1.0, 1.2}:
                    p = copy(params)
                    p.pi_data = Clip(pi_data, 0.00, 10.0)
                    p.mu_execution = Clip(mu_execution, 0.00, 10.0)
                    expanded.append(p)
        grid = expanded

    # Stage 4: travel/handling speed factors if target has travel-time shift
    # (khớp Strategy D mục 13.5 và walkthrough mục 25, trước đây bị bỏ sót khỏi grid search)
    If ood_score.feature_contributions["travel_time_shift"] > 0.10:
        expanded = []
        For params in grid:
            For speed_factor in source.speed_factor * {0.8, 1.0, 1.2}:
                For handling_time_factor in source.handling_time_factor * {0.8, 1.0, 1.2}:
                    p = copy(params)
                    p.speed_factor = Clip(speed_factor, 0.10, 3.0)
                    p.handling_time_factor = Clip(handling_time_factor, 0.10, 3.0)
                    expanded.append(p)
        grid = expanded

    # Stage 5: OOD threshold minor calibration
    final_grid = []
    For params in grid:
        For theta_ood in {source.theta_ood - 0.05, source.theta_ood, source.theta_ood + 0.05}:
            p = copy(params)
            p.theta_ood = Clip(theta_ood, 0.05, 0.95)
            final_grid.append(p)

    Return Deduplicate(final_grid)
```

## 40.4. CalibrateTarget

```text
Function CalibrateTarget(source_params, source_port, target_port, calibration_set, validation_set):
    cfg_target = LoadPortConfig(target_port)
    G_target = BuildYardGraph(cfg_target)

    source_features = ExtractPortFeatures(BuildYardGraph(LoadPortConfig(source_port)), LoadPortConfig(source_port))
    target_features = ExtractPortFeatures(G_target, cfg_target)
    source_stats = LoadOrComputeSourceFeatureStats(source_port)   # mean/std per feature qua các source layout đã biết
    ood = ComputeOODScore(source_features, target_features, OOD_WEIGHTS, source_stats)

    candidate_param_sets = GenerateLocalParamGrid(source_params, ood)

    best_params = source_params
    best_score = +INF
    evaluated = 0

    For params in candidate_param_sets:
        If evaluated >= calibration_budget:
            break

        score = 0
        For instance in calibration_set:
            result = RunPortGSAR(instance, cfg_target, G_target, params)
            score += result.total_cost

        score = score / Len(calibration_set)

        # Validate only promising configs
        If score < best_score:
            validation_score = 0
            For instance in validation_set:
                result = RunPortGSAR(instance, cfg_target, G_target, params)
                validation_score += result.total_cost
            validation_score = validation_score / Len(validation_set)

            If validation_score < best_score:
                best_score = validation_score
                best_params = params

        evaluated += 1

    gap_before = ComputeTransferGap(source_params, source_port, target_port, validation_set)
    gap_after  = ComputeTransferGap(best_params, source_port, target_port, validation_set)
    recovery   = ComputeRecoveryRatio(gap_before, gap_after)

    Return CalibrationResult(
        source_port=source_port,
        target_port=target_port,
        calibration_samples=Len(calibration_set),
        params_tuned=ChangedParams(source_params, best_params),
        params_source=source_params,
        params_final=best_params,
        search_method="staged_local_grid_search",
        search_budget=calibration_budget,
        transfer_gap_before=gap_before,
        transfer_gap_after=gap_after,
        recovery_ratio=recovery,
        best_validation_score=best_score,
        status="SUCCESS"
    )
```

## 40.5. Stop condition

Calibration dừng khi một trong các điều kiện sau xảy ra:

```text
1. evaluated >= calibration_budget
2. candidate grid exhausted
3. runtime > calibration_timeout
4. no improvement after patience parameter sets
```

Default:

```text
calibration_budget  = 100 parameter sets
calibration_timeout = xem mục 46.2 (theo K: 120s/300s/600s/1200s cho K=5/10/20/50;
                       300s ở đây là giá trị mặc định khi K không xác định, khớp K=10)
patience            = 20
```

---

# 41. Transfer metrics implementation

## 41.1. ComputeTransferGap

> `RunPortGSAR(instance, cfg_target, G_target, params)` cần graph phản ánh state thật của `instance` (không phải neutral state) để ra quyết định đúng. Trong thực thi, `RunPortGSAR` tự gọi lại `BuildYardGraph(cfg_target, instance.yard_state, instance.crane_state)` bên trong bằng state của chính `instance` đó — `G_target` dựng sẵn ở đây (neutral, dùng chung cho cả target_test_set) chỉ phục vụ so sánh cấu trúc/OOD, không phải input runtime cuối cùng cho mọi instance.

```text
Function ComputeTransferGap(params, source_port, target_port, target_test_set):
    cfg_target = LoadPortConfig(target_port)
    G_target = BuildYardGraph(cfg_target)   # neutral structural graph, dùng cho OOD/so sánh

    transferred_costs = []
    tuned_or_proxy_costs = []

    For instance in target_test_set:
        result_transfer = RunPortGSAR(instance, cfg_target, G_target, params)
        result_proxy = RunPerLayoutTunedOrExtendedSolver(instance, target_port)

        transferred_costs.append(result_transfer.total_cost)
        tuned_or_proxy_costs.append(result_proxy.total_cost)

    J_transfer = Mean(transferred_costs)
    J_proxy    = Mean(tuned_or_proxy_costs)

    transfer_gap = J_transfer - J_proxy
    relative_gap = transfer_gap / Max(abs(J_proxy), epsilon)

    Return {
        "transfer_gap": transfer_gap,
        "relative_transfer_gap": relative_gap,
        "J_transfer": J_transfer,
        "J_proxy": J_proxy
    }
```

## 41.2. ComputeRecoveryRatio

```text
Function ComputeRecoveryRatio(gap_before, gap_after):
    If gap_before <= epsilon:
        return 1.0
    return Max(0.0, Min(1.0, (gap_before - gap_after) / gap_before))
```

## 41.3. EvaluateFewShotCalibration

```text
Function EvaluateFewShotCalibration(source_params, source_port, target_port, K_values, seeds):
    results = []

    For K in K_values:
        For seed in seeds:
            calibration_set = SampleTargetInstances(target_port, K, seed)
            validation_set  = SampleTargetValidationInstances(target_port, seed)
            test_set        = SampleTargetTestInstances(target_port, seed)

            cal_result = CalibrateTarget(
                source_params,
                source_port,
                target_port,
                calibration_set,
                validation_set
            )

            test_gap = ComputeTransferGap(
                cal_result.params_final,
                source_port,
                target_port,
                test_set
            )

            results.append({
                "K": K,
                "seed": seed,
                "calibration_result": cal_result,
                "test_transfer_gap": test_gap.transfer_gap,
                "test_relative_gap": test_gap.relative_transfer_gap,
                "recovery_ratio": cal_result.recovery_ratio
            })

    Return AggregateByK(results)
```

Default:

```text
K_values = {0, 5, 10, 20, 50}
seeds = {0, 1, 2, 3, 4}
```

## 41.4. OODDetectionAccuracy

```text
Function OODDetectionAccuracy(source_ports, target_ports, test_sets):
    y_true = []
    y_pred = []

    For source in source_ports:
        For target in target_ports:
            If source == target:
                continue

            source_features = ExtractPortFeatures(BuildYardGraph(LoadPortConfig(source)), LoadPortConfig(source))
            target_features = ExtractPortFeatures(BuildYardGraph(LoadPortConfig(target)), LoadPortConfig(target))
            source_stats = LoadOrComputeSourceFeatureStats(source)
            ood = ComputeOODScore(source_features, target_features, OOD_WEIGHTS, source_stats)

            gap = ComputeTransferGap(SourceParams(source), source, target, test_sets[target])

            If gap.relative_transfer_gap <= tau_good:
                label = "ID"
            Else if gap.relative_transfer_gap >= tau_bad:
                label = "OOD"
            Else:
                continue  # uncertain region is excluded from strict accuracy

            pred = "OOD" if ood.ood_score > theta_zero_shot else "ID"

            y_true.append(label)
            y_pred.append(pred)

    accuracy  = Accuracy(y_true, y_pred)
    precision = Precision(y_true, y_pred, positive="OOD")
    recall    = Recall(y_true, y_pred, positive="OOD")
    f1        = F1(precision, recall)

    Return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "num_pairs": Len(y_true)
    }
```

---

# 42. Shared decision engine kế thừa từ Paper 3

Paper 4 không viết lại decision engine. Nó kế thừa MISR-Yard từ Paper 3.

## 42.1. Module giữ nguyên từ Paper 3

Các module sau giữ nguyên logic:

```text
Reuse from Paper 3:
- MISR-Yard Decision Orchestrator
- Diagnosis module
- Intervention family definitions
- GenerateContainerRepair
- GenerateResourceReassignment
- GenerateJobResequencing
- GenerateWaitNoOp
- GenerateLimitedHybrid
- ResourceCost
- ResourceStability
- InterventionComplexity
- Safety validation
- Candidate evaluation
- Fallback hierarchy
- Metrics logger
- Baseline runner
- MVP gate protocol
```

## 42.2. Module sửa để đọc PortConfig/YardGraph

Các module sau được adapter hóa:

```text
Modified in Paper 4:
- GetTravelTime: reads PortConfig.travel_time_matrix or YardGraph travel edges
- ResourceCost: uses YardGraph zone/travel/conflict edges
- Safety validation: reads PortConfig.safety_rules and YardGraph conflict edges
- Candidate generation: uses PortConfig constraints instead of hard-coded layout
- Feature extraction: new module for cross-terminal transfer
- OOD detector: new module
- Calibration layer: new module
- Deployment mode selector: new module
```

## 42.3. Module không bị loại bỏ

Không loại bỏ module nào từ Paper 3. Paper 4 chỉ thêm một lớp cấu hình và transfer phía trên:

```text
Paper 4 = Paper 3 MISR-Yard
        + PortConfig adapter
        + YardGraph representation
        + Feature extractor
        + OOD detector
        + Few-shot calibration layer
        + Deployment fallback controller
```

---

# 43. Baseline mapping chi tiết hơn

## B1. Source-only zero-shot transfer

Dùng tham số tune trên source terminal A, áp dụng trực tiếp lên target terminal B/C/D/E.

```text
No target calibration.
No OOD fallback.
```

Mục đích: đo zero-shot transfer thô.

## B2. Per-layout tuned Paper 3 MISR-Yard

Tune riêng Paper 3 MISR-Yard trên từng target layout.

```text
Strong upper reference.
High calibration cost.
Not ideal for production onboarding.
```

Mục đích: biết performance tốt nhất nếu chịu tune riêng từng cảng.

## B3. Rule-based default PortConfig

Dùng rule mặc định:

```text
fixed trigger threshold
fixed stability weight
fixed resource weight
no learned/few-shot calibration
safe fallback when uncertain
```

Mục đích: production fallback đơn giản.

## B4. Few-shot scalar calibration

Baseline calibration đơn giản hơn Port-GSAR.

Chỉ tune một scalar multiplier `s` áp vào các trọng số chính:

```text
lambda_stability' = s * lambda_stability
mu_execution'     = s * mu_execution
nu_resource'      = s * nu_resource
eta_intervention' = s * eta_intervention
```

Grid:

```text
s ∈ {0.5, 0.75, 1.0, 1.25, 1.5}
```

Không tune riêng từng nhóm tham số.

Mục đích: kiểm tra liệu Port-GSAR có thực sự cần staged calibration hay chỉ cần scale đơn giản.

## B5. Train/tune from scratch on target

Tune toàn bộ target từ đầu với nhiều dữ liệu.

```text
Expensive upper bound.
Not few-shot.
```

Mục đích: upper bound nhưng không production-friendly.

## B6. Port-GSAR without YardGraph

Dùng PortConfig dạng tabular/simple feature nhưng không tạo YardGraph.

Mục đích: kiểm tra đóng góp của YardGraph representation.

## B7. No-OOD transfer

Dùng Port-GSAR calibration nhưng tắt OOD detector.

```text
Always deploy if calibration finishes.
No manual review mode.
No safe fallback based on OOD.
```

Rủi ro:

```text
If target terminal is too different, system may still deploy automatically.
```

Mục đích: kiểm tra giá trị của OOD/failure detection đối với production safety.

## B8. Full Port-GSAR

Proposed method:

```text
PortConfig + YardGraph + feature extractor + OOD detection + few-shot calibration + deployment fallback.
```

---

# 44. Benchmark chi tiết cho Paper 4

## 44.1. Layout families

```text
Layout A: Source symmetric small
- 3 blocks
- uniform bay/row
- 2 crane zones
- simple safety rules

Layout B: Scaled medium
- 5 blocks
- larger number of stacks
- same rule family as A

Layout C: Asymmetric
- irregular block sizes
- non-uniform travel matrix
- uneven occupancy

Layout D: Resource-different
- different number of cranes
- different speed factors
- crane zones overlap

Layout E: Rule-different
- stricter safety rules
- different hazardous/locked stack constraints
- lower data reliability
```

## 44.2. Instance count

```text
Source training/tuning:
- Layout A: 300 instances

Target test:
- Layout B: 100 instances
- Layout C: 100 instances
- Layout D: 100 instances
- Layout E: 100 instances

Few-shot calibration:
- K = 0, 5, 10, 20, 50 target instances

Validation during calibration:
- 30 instances per target layout

Random seeds:
- 5 seeds: {0,1,2,3,4}
```

Total held-out target test:

```text
4 target layouts × 100 instances × 5 seeds = 2000 target evaluations per method
```

## 44.3. Event types reused from Paper 1–3

```text
Retrieval events from Paper 1:
- insertion
- deletion/no-show
- rank shift
- priority change

Execution events from Paper 2:
- action delay
- action failure
- state mismatch
- low-confidence update

Intervention/resource events from Paper 3:
- crane slowdown
- crane unavailable
- workload spike
- zone conflict
- safety conflict
```

## 44.4. Synthetic-to-real gap discussion

Paper 4 có thể bắt đầu với synthetic benchmark, nhưng production claim cần thảo luận rõ gap sang dữ liệu thật.

Nếu có real terminal data:

```text
Use real data for:
- travel-time matrix calibration
- occupancy distribution
- crane availability distribution
- delay/failure event distribution
- safety-rule validation
```

Nếu chỉ có synthetic data:

```text
Report explicitly:
- all layouts are synthetic but structurally heterogeneous;
- event distributions are stress-test scenarios, not real terminal logs;
- real-data calibration is required before deployment;
- PortConfig is designed to reduce the gap by allowing terminal-specific travel matrix, safety rules, and reliability factors.
```

Production bridge:

```text
Synthetic benchmark validates algorithmic transfer.
Pilot deployment requires at least 1-2 weeks of real terminal logs to calibrate travel time, handling time, event frequency, and data reliability.
```

---

# 45. Ground truth / proxy cho Paper 4

Paper 4 không có true optimum cho medium/large cross-terminal setting. Vì vậy dùng nhiều proxy theo scale.

## Small instances

```text
Use exhaustive enumeration over:
- candidate intervention family
- local repair choices
- small resource assignment set
- limited resequencing swaps
```

Mục tiêu: approximate oracle for small cases.

## Medium/Large instances

```text
Use extended-time per-layout tuned MISR-Yard or joint solver proxy.
```

Default:

```text
extended_time_budget = 300 seconds per instance
```

## Transfer reference

For transfer gap:

```text
J_proxy(target) = best of:
- per-layout tuned Paper 3 MISR-Yard
- extended-time joint solver
- exhaustive oracle if small
```

---

# 46. Timeout protocol

Paper 4 thêm graph building, feature extraction, OOD scoring và calibration. Vì vậy timeout được tách thành online và offline.

## 46.1. Online decision timeout

Online decision không được chạy calibration. Nó chỉ dùng params đã chọn.

```text
Small:  5 seconds
Medium: 20 seconds
Large:  90 seconds
```

## 46.2. Offline onboarding/calibration timeout

Calibration là bước offline khi onboard terminal mới.

```text
K=5:   120 seconds
K=10:  300 seconds
K=20:  600 seconds
K=50:  1200 seconds
```

## 46.3. Graph/feature/OOD timeout

```text
BuildYardGraph:       <= 5 seconds for large layout
ExtractPortFeatures:  <= 2 seconds
ComputeOODScore:      <= 1 second
SelectDeploymentMode: <= 1 second
```

Nếu timeout:

```text
Fallback to manual review or safe default PortConfig.
```

---

# 47. Production deployment modes

## 47.1. Mode definition

```text
MODE_0: Manual configuration only
MODE_1: Zero-shot recommendation
MODE_2: Few-shot calibrated recommendation
MODE_3: Assisted deployment with human approval
MODE_4: Safe fallback / no autonomous recommendation
```

## 47.2. SelectDeploymentMode

```text
Function SelectDeploymentMode(ood_score, calibration_result, safety_status):
    If safety_status.has_unresolved_hard_rule:
        return MODE_4_SAFE_FALLBACK

    If ood_score.decision == "ZERO_SHOT_ALLOWED":
        return MODE_1_ZERO_SHOT

    If ood_score.decision == "FEW_SHOT_CALIBRATION_REQUIRED":
        If calibration_result.status == "SUCCESS" and calibration_result.recovery_ratio >= rho_min:
            return MODE_2_FEW_SHOT_CALIBRATED
        Else:
            return MODE_3_ASSISTED_HUMAN_APPROVAL

    If ood_score.decision == "MANUAL_REVIEW_OR_SAFE_FALLBACK":
        return MODE_4_SAFE_FALLBACK
```

Default:

```text
rho_min = 0.50
```

---

# 48. Parameter table bổ sung

| Parameter | Default | Ý nghĩa |
|---|---:|---|
| `theta_zero_shot` | 0.30 | OOD dưới ngưỡng này cho phép zero-shot |
| `theta_few_shot` | 0.60 | OOD dưới ngưỡng này cho phép few-shot calibration |
| `tau_good` | 0.10 | Relative transfer gap được xem là tốt |
| `tau_bad` | 0.30 | Relative transfer gap được xem là OOD/fail |
| `calibration_budget` | 100 | Số param set tối đa khi calibration |
| `calibration_patience` | 20 | Dừng nếu không cải thiện sau N config |
| `calibration_timeout_K10` | 300s | Timeout offline với K=10 |
| `rho_min` | 0.50 | Recovery ratio tối thiểu để auto deploy |
| `epsilon` | 1e-6 | Tránh chia 0 (đồng bộ với mục 22) |
| `w_layout_size` | 0.15 | OOD weight |
| `w_stack_height` | 0.10 | OOD weight |
| `w_travel_time` | 0.25 | OOD weight |
| `w_crane_zone` | 0.15 | OOD weight |
| `w_occupancy` | 0.10 | OOD weight |
| `w_safety_rule` | 0.15 | OOD weight |
| `w_data_reliability` | 0.10 | OOD weight |
| `w_block` | 10 | Fallback travel distance block weight |
| `w_bay` | 1 | Fallback travel distance bay weight |
| `w_row` | 1 | Fallback travel distance row weight |

---

# 49. Final coding checklist cho Paper 4

## 49.1. Data schemas

```text
[ ] PortConfig schema
[ ] YardGraph schema
[ ] YardGraphNode schema
[ ] YardGraphEdge schema
[ ] OODScore schema
[ ] CalibrationResult schema
[ ] PortTransferExperiment schema
```

## 49.2. Graph and feature modules

```text
[ ] BuildYardGraph
[ ] GetTravelTime
[ ] ResolveZone
[ ] ResolveCoordinate
[ ] ExtractPortFeatures
[ ] ExtractYardFeatures
[ ] ExtractLayoutFeatures
[ ] ExtractResourceFeatures
[ ] ExtractRiskFeatures
```

## 49.3. OOD and calibration modules

```text
[ ] NormalizeFeatures
[ ] ComputeOODScore
[ ] GenerateLocalParamGrid
[ ] CalibrateTarget
[ ] ComputeTransferGap
[ ] ComputeRecoveryRatio
[ ] EvaluateFewShotCalibration
[ ] OODDetectionAccuracy
[ ] SelectDeploymentMode
```

## 49.4. Paper 3 integration

```text
[ ] Adapter from PortConfig to MISR-Yard config
[ ] Adapter from YardGraph to ResourceCost
[ ] Adapter from YardGraph to SafetyValidation
[ ] Adapter from PortConfig to CandidateGeneration
[ ] Reuse Paper 3 metrics logger
[ ] Reuse Paper 3 baseline runner
```

## 49.5. Baselines

```text
[ ] B1 Source-only zero-shot transfer
[ ] B2 Per-layout tuned Paper 3 MISR-Yard
[ ] B3 Rule-based default PortConfig
[ ] B4 Few-shot scalar calibration
[ ] B5 Train/tune from scratch on target
[ ] B6 Port-GSAR without YardGraph
[ ] B7 No-OOD transfer
[ ] B8 Full Port-GSAR
```

## 49.6. Experiments

```text
[ ] Experiment 1: within-layout upper reference
[ ] Experiment 2: zero-shot transfer
[ ] Experiment 3: few-shot calibration K={0,5,10,20,50}
[ ] Experiment 4: per-layout tuned upper bound
[ ] Experiment 5: OOD detection
[ ] Experiment 6: ablation
[ ] Experiment 7: synthetic-to-real sensitivity if real logs unavailable
```

## 49.7. MVP gate

Before full experiments, run MVP:

```text
MVP setting:
- Source: Layout A
- Target: Layout C
- K = 10 calibration instances
- 20 held-out target test instances
- Baselines: B1, B4, B8
```

MVP pass conditions:

```text
[ ] BuildYardGraph succeeds for both layouts
[ ] OOD score detects A→C as non-trivial shift
[ ] Few-shot calibration reduces transfer gap by at least 30%
[ ] Port-GSAR beats source-only zero-shot on target test
[ ] Runtime within timeout
[ ] No hard safety violation
```

If MVP fails:

```text
Do not scale experiments.
Inspect feature extraction, OOD weights, calibration grid, and target benchmark difficulty.
```

---

# 50. Reviewer-facing clarification

Để tránh reviewer hiểu nhầm rằng Paper 4 chỉ là engineering benchmark, cần viết rõ:

> Paper 4 is not merely a multi-layout evaluation of MISR-Yard. It introduces a port-configurable transfer framework consisting of PortConfig, YardGraph, OOD-based deployment gating, and few-shot calibration. The core research question is how stable adaptive yard decision-making can be transferred across heterogeneous terminals with bounded calibration effort and explicit failure detection.

Tiếng Việt:

> Paper 4 không chỉ là chạy MISR-Yard trên nhiều layout. Paper 4 đề xuất một framework chuyển giao đa cảng gồm PortConfig, YardGraph, OOD-based deployment gating và few-shot calibration. Câu hỏi nghiên cứu chính là làm sao chuyển một hệ thống ra quyết định ổn định sang terminal mới với chi phí calibration hữu hạn và khả năng phát hiện khi nào không nên tự động triển khai.

---

# 51. Final Code-Ready Conclusion

Sau cập nhật này, Paper 4 đạt mức **CODE-READY** giống Paper 1–3.

Câu chuyện 4 paper hoàn chỉnh:

```text
Paper 1 makes replanning stable under evolving retrieval information.
Paper 2 makes replanning robust under imperfect execution.
Paper 3 makes replanning strategic by choosing the right intervention family.
Paper 4 makes replanning deployable across heterogeneous terminals.
```

Câu chốt cho Paper 4:

> **Port-GSAR makes stable adaptive yard decision-making configurable, transferable and deployment-ready across heterogeneous container terminals — bridging the gap between algorithm research and production-ready yard intelligence.**

