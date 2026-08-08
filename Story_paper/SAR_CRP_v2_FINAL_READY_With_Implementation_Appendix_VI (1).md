# SAR-CRP v2 FINAL READY Proposal + Implementation Appendix

## Stable Adaptive Replanning for Container Relocation under Imperfect and Evolving Retrieval Information

**Phiên bản:** FINAL READY + Implementation Appendix — updated after ultra-final coding review  
**Mục tiêu:** Đề xuất nghiên cứu Q1 Paper 1, có scope đủ hẹp để triển khai, đủ cụ thể để code, đủ rõ để reviewer tái hiện.  
**Ngôn ngữ:** Tiếng Việt  
**Tên ngắn:** SAR-CRP v2 Core

---

# 1. Tóm tắt ngắn gọn

Bài toán Container Relocation Problem truyền thống giả định rằng thứ tự lấy container đã biết hoặc tương đối ổn định. Trong vận hành cảng thực tế, thông tin retrieval thay đổi liên tục do truck đến sớm/trễ, container bị đổi ưu tiên, no-show, cập nhật xác suất pickup, hoặc dữ liệu trạng thái bị trễ.

Nếu mỗi lần có thông tin mới hệ thống tối ưu lại toàn bộ kế hoạch, plan có thể thay đổi liên tục, gây rối cho operator và thiết bị đang thực thi. Nếu không replan, hệ thống có thể giữ một plan đã lỗi thời và tạo nhiều relocation/delay hơn.

**SAR-CRP v2 Core** đề xuất một lớp stable adaptive replanning nằm phía trên CRP solver hiện có. Framework này quyết định:

1. Khi nào cần replan.
2. Phần nào của kế hoạch cũ phải giữ nguyên.
3. Phần nào có thể sửa.
4. Sửa bằng local repair hay full reoptimization.
5. Plan mới có đáng đổi không khi tính cả operational cost và stability cost.

Paper 1 không cố gắng xây toàn bộ production system. Paper 1 chỉ tập trung vào **core SAR-CRP**:

```text
Event Impact Estimator
+ Replanning Trigger
+ Freeze Horizon
+ Stability-aware Objective
+ Local Search Repair Planner
+ Simple fallback: keep old plan if invalid/timeout/not worth changing
```

Các module mở rộng như full Data Reliability Layer, Execution Feedback Loop, advanced Fallback/Rollback, operator learning, transfer learning sẽ để cho Paper 2 hoặc phần future work.

---

# 2. Định vị nghiên cứu

## 2.1. Không claim sai novelty

SAR-CRP v2 không claim rằng:

- giải CRP tốt hơn mọi solver hiện có;
- phát minh lại DRL cho CRP;
- phát minh lại stochastic CRP;
- phát minh lại truck arrival prediction;
- phát minh lại crane scheduling;
- phát minh lại digital twin.

Các phần đó có thể reuse/adapt từ literature.

## 2.2. Novelty chính

Novelty của SAR-CRP v2 là:

> **Stable adaptive replanning for CRP under evolving and imperfect retrieval information.**

Nói đơn giản:

> Khi thông tin retrieval thay đổi, hệ thống không tối ưu lại toàn bộ một cách mù quáng, mà chỉ replan khi đáng, giữ phần kế hoạch đã cam kết, sửa phần bị ảnh hưởng và chọn plan mới theo trade-off giữa hiệu quả vận hành và độ ổn định.

---

# 3. Base papers và vai trò kế thừa

> **Đã xác minh (2026-08-08, qua WebSearch).** Cả ba base paper dưới đây đều là paper thật, không phải placeholder. Chi tiết:
>
> ```text
> [x] Xác nhận từng paper tồn tại thật (DOI/arXiv ID/venue cụ thể). — Xem BibTeX §3.1–3.3.
> [x] Kiểm tra đúng năm publish/preprint. — Shin et al. là bài thật, published (không phải placeholder), Vol. 183, Feb 2026.
> [x] Kiểm tra nội dung paper khớp với vai trò được gán ở đây. — Khớp cho cả 3 paper, xem nhận xét từng mục.
> [x] Cập nhật bibliography với thông tin đầy đủ (BibTeX) trước khi viết Related Work. — Đã thêm BibTeX vào từng mục con dưới đây.
> ```

## 3.1. Shin et al. 2026 — CRP_RL

**Xác minh:** Có thật. Woo-Jin Shin, Inguk Choi, Sang-Hyun Cho, Hyun-Jung Kim, "Learning to retrieve containers: A scale-diverse deep reinforcement learning approach for the container retrieval problem," *Transportation Research Part C: Emerging Technologies*, vol. 183, article 105496, 2026. DOI: [10.1016/j.trc.2026.105496](https://doi.org/10.1016/j.trc.2026.105496).

Nội dung khớp vai trò gán: DRL solver cho container retrieval problem, kiến trúc size-agnostic + scale-diverse training để generalize qua nhiều yard layout, giải trong vài giây cho instance thực tế — phù hợp để dùng làm CRP solver mạnh / initial planner / full reoptimization baseline / candidate generator như đã gán.

```bibtex
@article{shin2026learning,
  author  = {Shin, Woo-Jin and Choi, Inguk and Cho, Sang-Hyun and Kim, Hyun-Jung},
  title   = {Learning to retrieve containers: A scale-diverse deep reinforcement learning approach for the container retrieval problem},
  journal = {Transportation Research Part C: Emerging Technologies},
  volume  = {183},
  pages   = {105496},
  year    = {2026},
  doi     = {10.1016/j.trc.2026.105496}
}
```


**Vai trò trong SAR-CRP:**

- Base chính.
- Dùng làm CRP solver mạnh.
- Dùng làm initial planner.
- Dùng làm full reoptimization baseline.
- Dùng làm candidate generator cho partial repair.

**Cách kết hợp:**

```text
CRP_RL tạo plan tốt cho trạng thái tĩnh.
SAR-CRP quyết định khi nào dùng lại CRP_RL, dùng trên phần nào của plan, và có chấp nhận plan mới hay không.
```

## 3.2. Zhou & Zhang 2024 — Real-time stochastic CRP

**Vai trò:**

- Base cho evolving retrieval information.
- Dùng làm real-time/stochastic baseline nếu tích hợp được.
- Giúp định vị bài toán dynamic/replanning.

**Xác minh:** Có thật. S. Zhou, Q. Zhang, "Real-Time Batch Optimization for the Stochastic Container Relocation Problem," *Applied Sciences*, vol. 14, no. 6, article 2624, 2024. DOI: [10.3390/app14062624](https://doi.org/10.3390/app14062624).

Nội dung khớp vai trò gán: heuristic (SPFH) xử lý pick-up order thay đổi theo thời gian thực dưới uncertainty về truck arrival time — đúng là real-time/stochastic CRP baseline như đã gán.

```bibtex
@article{zhou2024realtime,
  author  = {Zhou, S. and Zhang, Q.},
  title   = {Real-Time Batch Optimization for the Stochastic Container Relocation Problem},
  journal = {Applied Sciences},
  volume  = {14},
  number  = {6},
  pages   = {2624},
  year    = {2024},
  doi     = {10.3390/app14062624}
}
```

## 3.3. Zhang et al. 2025 — Retrieval probability / data-driven uncertainty

**Vai trò:**

- Base cho xác suất retrieval/pickup.
- SAR-CRP không cần tự phát minh prediction.
- Prediction output được dùng như một dạng thông tin mới trong event stream.

**Xác minh:** Có thật. Zhanluo Zhang, Kok Choon Tan, Wei Qin, Yan Li, Ek Peng Chew, Keyi Xu, "A Data-Driven Approach to Solving the Container Relocation Problem with Uncertainties," *Advanced Engineering Informatics*, vol. 65, article 103112, 2025. DOI: [10.1016/j.aei.2025.103112](https://doi.org/10.1016/j.aei.2025.103112). (Bản preprint từng đăng trên SSRN, tháng 9/2024.)

Nội dung khớp vai trò gán: đề xuất Retrieval Probability Matrix (RPM), model data-driven dự đoán RPM từ terminal operational records, mở rộng CRP thành Probabilistic CRP — đúng là base cho retrieval/pickup probability như đã gán.

```bibtex
@article{zhang2025datadriven,
  author  = {Zhang, Zhanluo and Tan, Kok Choon and Qin, Wei and Li, Yan and Chew, Ek Peng and Xu, Keyi},
  title   = {A Data-Driven Approach to Solving the Container Relocation Problem with Uncertainties},
  journal = {Advanced Engineering Informatics},
  volume  = {65},
  pages   = {103112},
  year    = {2025},
  doi     = {10.1016/j.aei.2025.103112}
}
```

## 3.4. Dynamic scheduling / rescheduling stability literature

**Vai trò:**

- Base lý thuyết cho stability cost.
- SAR-CRP kế thừa ý tưởng stability/rescheduling, nhưng áp dụng vào CRP có cấu trúc stack và blocker đặc thù.

---

# 4. Bài toán nghiên cứu Paper 1

## 4.1. Input

Tại thời điểm replanning \(t\), hệ thống nhận:

```text
s_t      : yard state hiện tại
P_old    : plan cũ đang được thực thi hoặc đã cam kết
I_old    : thông tin retrieval cũ
I_new    : thông tin retrieval mới
H_f      : freeze horizon
lambda   : trọng số stability
tau      : ngưỡng replan
T_max    : timeout runtime
```

## 4.2. Output

Hệ thống trả về một trong hai quyết định:

### Case 1 — Keep old plan

```text
Decision = KEEP
Plan     = P_old
Reason   = event impact nhỏ hoặc plan mới không đủ tốt
```

### Case 2 — Update plan

```text
Decision = UPDATE
Plan     = P_new
Reason   = plan mới có total cost tốt hơn đủ lớn
```

## 4.3. Mục tiêu

Tìm kế hoạch mới \(P\) sao cho:

```text
tốt về vận hành
nhưng không phá vỡ quá nhiều kế hoạch cũ
```

Objective:

\[
\min_P J(P)
=
C_{op}(P)
+
\lambda D(P,P^{old})
+
\mu C_{data}(P)
\]

Trong Paper 1, \(C_{data}\) dùng bản đơn giản. Full Data Reliability để Paper 2.

---

# 5. Kiến trúc SAR-CRP v2 Core

```text
Static / Dynamic CRP Instance
          |
          v
Initial Plan Generator
(CRP_RL or heuristic)
          |
          v
Dynamic Event Stream
          |
          v
Event Impact Estimator
          |
          v
Replanning Trigger
          |
   +------+------+
   |             |
 KEEP        REPLAN
   |             |
   |             v
   |      Freeze Horizon Manager
   |             |
   |             v
   |      Candidate Repair Generator
   |             |
   |             v
   |      Candidate Evaluator
   |             |
   |             v
   |      Stability-aware Selector
   |             |
   |             v
   |      Simple Fallback Check
   |             |
   +-------------+
          |
          v
Final Plan + Metrics
```

---

# 6. Module 1 — Dynamic Event Stream

## 6.1. Mục tiêu

Biến benchmark CRP tĩnh thành benchmark động.

Một instance tĩnh gồm:

```text
initial_yard_state
initial_retrieval_order
```

SAR-CRP bổ sung:

```text
event_stream
updated_retrieval_information
```

## 6.2. Event types dùng trong Paper 1

Paper 1 chỉ dùng 5 loại event, không mở rộng quá nhiều.

### E1 — Order swap

Hai container trong top-k retrieval queue đổi thứ tự.

```text
Before: C1, C2, C3, C4, C5
After : C1, C4, C3, C2, C5
```

### E2 — Urgent insertion

Một container trở thành urgent và được đưa vào top-k.

```text
Before: C1, C2, C3, C4
After : C1, C8, C2, C3, C4
```

### E3 — ETA early / late

Container được dự báo đến sớm hoặc muộn hơn.

SAR-CRP chuyển ETA update thành thay đổi rank hoặc thay đổi retrieval probability.

### E4 — Probability update

Xác suất pickup của một container thay đổi.

Ví dụ:

```text
P(pickup C7 within horizon) tăng từ 0.2 lên 0.8
```

### E5 — Stale information

Thông tin retrieval mới có confidence thấp do dữ liệu cũ/trễ.

Paper 1 dùng confidence đơn giản theo age.

---

# 7. Module 2 — Simple Data Confidence

Paper 1 không xây full Data Reliability Layer.

Chỉ dùng confidence score đơn giản:

\[
Conf(I^{new}) = \exp(-\eta \cdot age(I^{new}))
\]

Trong đó:

- \(age(I^{new})\): thời gian từ lần cập nhật cuối.
- \(\eta\): hệ số decay.

Nếu không có timestamp, dùng preset:

```text
fresh       -> Conf = 1.0
moderate    -> Conf = 0.7
stale       -> Conf = 0.4
very stale  -> Conf = 0.2
```

Confidence được dùng để phạt các plan thay đổi nhiều dựa trên thông tin không chắc chắn.

---

# 8. Module 3 — Event Impact Estimator

## 8.1. Mục tiêu

Đo mức độ ảnh hưởng của thông tin mới lên plan cũ.

Impact tổng:

\[
Impact(e_t)
=
w_o I_{order}
+
w_t I_{target}
+
w_b I_{blocking}
+
w_p I_{plan}
+
w_c I_{conf}
\]

Trong Paper 1, weight dùng heuristic cố định:

```text
w_o = 0.25
w_t = 0.20
w_b = 0.25
w_p = 0.20
w_c = 0.10
```

Ablation sẽ kiểm tra độ nhạy của các weight này.

---

## 8.2. Thành phần 1 — Order impact

Dùng Kendall-tau distance trên top-k retrieval queue.

Gọi:

```text
Q_old^k = top-k retrieval queue trước event
Q_new^k = top-k retrieval queue sau event
```

\[
I_{order}
=
\frac{
KT(Q_{old}^k,Q_{new}^k)
}{
|U|(|U|-1)/2
}
\]

Trong đó:

- \(U = Q_{old}^k \cup Q_{new}^k\) (hợp của top-k cũ và top-k mới; nếu không có container nào mới xuất hiện thì \(|U|=k\) và mẫu số trở về \(k(k-1)/2\)).
- \(KT\): số cặp container trong \(U\) bị đảo thứ tự tương đối.
- Giá trị nằm trong \([0,1]\).

Nếu container mới xuất hiện trong top-k (tức nằm trong \(Q_{new}^k\) nhưng không nằm trong \(Q_{old}^k\), hoặc ngược lại), gán vị trí cũ/mới bằng \(k+1\) trước khi tính Kendall-tau mở rộng. Công thức này khớp chính xác với pseudocode ở mục 44.1 (biến `total_pairs` = số cặp trong `items = union(...)`).

---

## 8.3. Thành phần 2 — Target impact

\[
I_{target}
=
\begin{cases}
1, & \text{nếu target retrieval hiện tại thay đổi}\\
0, & \text{nếu target không thay đổi}
\end{cases}
\]

Có thể dùng phiên bản mềm hơn:

\[
I_{target}
=
1 - \frac{1}{1 + |rank_{new}(c^*) - rank_{old}(c^*)|}
\]

Nhưng Paper 1 dùng binary để đơn giản và dễ tái hiện.

---

## 8.4. Thành phần 3 — Blocking impact

Bản cũ dùng ratio và clamp, có thể mất thông tin khi blocker pressure thay đổi mạnh. Bản refined dùng trung bình thay đổi tuyệt đối có saturation nhẹ.

Gọi:

- \(B_{old}(c)\): số blocker của container \(c\) trước event.
- \(B_{new}(c)\): số blocker của container \(c\) sau event.
- \(TopK\): tập container quan trọng trong top-k retrieval queue mới.

Trước hết tính:

\[
\Delta B
=
\frac{1}{|TopK|}
\sum_{c\in TopK}
|B_{new}(c)-B_{old}(c)|
\]

Sau đó dùng saturation function:

\[
I_{blocking}
=
1 - \exp(-\Delta B / \sigma_b)
\]

Trong đó:

- \(\sigma_b\) là hệ số scale.
- Paper 1 chọn \(\sigma_b=2\).

Ưu điểm:

- Không bị mất thông tin vì clamp cứng.
- Vẫn giữ giá trị trong \([0,1]\).
- Blocking thay đổi càng lớn thì impact càng tăng nhưng bão hòa dần.

---

## 8.4.1. Sensitivity analysis cho \(I_{blocking}\)

Để tránh phụ thuộc vào một giá trị cố định của \(\sigma_b\), Paper 1 báo cáo sensitivity analysis:

```text
sigma_b ∈ {1, 2, 3}
default sigma_b = 2
```

Trong đó:

- \(\sigma_b=1\): blocking impact tăng nhanh, nhạy với thay đổi nhỏ.
- \(\sigma_b=2\): setting mặc định, cân bằng giữa sensitivity và saturation.
- \(\sigma_b=3\): blocking impact tăng chậm hơn, bảo thủ hơn.

Khi viết paper, \(\sigma_b=2\) được dùng làm default, còn \(\sigma_b\in\{1,2,3\}\) được dùng để kiểm tra robustness.

---

## 8.5. Thành phần 4 — Plan impact

Reviewer yêu cầu định nghĩa rõ "affected action".

Một action \(a_i \in P^{old}\) được xem là affected nếu thỏa một trong các điều kiện sau:

### A1 — Container removed/cancelled

Container của action không còn trong retrieval queue do no-show/cancellation.

### A2 — Rank shift lớn

Container của action có retrieval rank thay đổi hơn ngưỡng \(r_{shift}\).

\[
|rank_{new}(c)-rank_{old}(c)| > r_{shift}
\]

Paper 1 chọn:

```text
r_shift = 5
```

Để tránh phụ thuộc vào một ngưỡng cứng duy nhất, Paper 1 báo cáo sensitivity analysis:

```text
r_shift ∈ {3, 5, 7}
default r_shift = 5
```

Trong đó:

- \(r_{shift}=3\): nhạy hơn, nhiều action bị xem là affected.
- \(r_{shift}=5\): setting mặc định.
- \(r_{shift}=7\): bảo thủ hơn, chỉ các thay đổi rank lớn mới bị xem là affected.

### A3 — Destination invalid

Destination stack của relocation action không còn hợp lệ.

Ví dụ:

```text
stack full
stack locked
stack violates height limit
```

### A4 — Stack affected

Action liên quan đến stack chứa target mới hoặc stack có blocker structure thay đổi.

Cụ thể, stack \(s\) là affected nếu:

\[
\exists c \in TopK:
location(c)=s
\quad \text{and} \quad
B_{new}(c)\neq B_{old}(c)
\]

### A5 — Urgent conflict

Action làm trì hoãn một urgent container.

Cụ thể:

```text
action nằm trước urgent container trong plan
và action không trực tiếp phục vụ urgent container
```

Sau đó:

\[
I_{plan}
=
\frac{
|\{a_i \in P^{old}: affected(a_i)=1\}|
}{
|P^{old}|
}
\]

---

## 8.6. Thành phần 5 — Confidence impact

\[
I_{conf}
=
1 - Conf(I^{new})
\]

Nếu thông tin mới không đáng tin, hệ thống nên cẩn trọng hơn với replan mạnh.

---

# 9. Module 4 — Replanning Trigger

SAR-CRP chỉ replan nếu event đủ quan trọng.

Điều kiện 1:

\[
Impact(e_t) \ge \theta_{impact}
\]

Điều kiện 2:

\[
EstimatedGain > SwitchingCost + \tau
\]

Trong Paper 1, để đơn giản:

\[
EstimatedGain
=
J(P^{old}) - J(P^{minimal})
\]

Trong đó \(P^{minimal}\) là plan sau minimal repair nhanh.

Nếu không có \(P^{minimal}\), dùng impact threshold làm trigger.

Recommended setting:

```text
theta_impact = 0.30
tau          = 0.01 * J(P_old)
```

(Xem Bảng tham số mặc định — mục 48 — để biết khoảng sensitivity `{0.2, 0.3, 0.4}`.)

Nếu không vượt trigger:

```text
return KEEP(P_old)
```

---

# 10. Module 5 — Freeze Horizon

## 10.1. Mục tiêu

Không đổi các action sắp thực hiện hoặc đã cam kết.

Hai kiểu freeze:

### Freeze by action count

```text
freeze first H_f actions
```

Ví dụ:

```text
H_f = 3
```

(Dùng ký hiệu `H_f` thống nhất với mục 4.1 và bảng tham số mặc định mục 48, không dùng `K` — `K` đã được dùng riêng cho kích thước top-k retrieval queue ở mục 8.2.)

### Freeze by execution time

```text
freeze all actions scheduled in next H_f minutes
```

Paper 1 dùng freeze by action count để đơn giản.

## 10.2. Split plan

\[
P^{old} = [P^{frozen}, P^{tail}]
\]

Trong đó:

- \(P^{frozen}\): không được thay đổi.
- \(P^{tail}\): có thể repair.

Nếu candidate plan vi phạm frozen prefix:

```text
reject candidate
```

hoặc penalty vô hạn:

\[
D = \infty
\]

---

# 11. Module 6 — Operational Cost

Paper 1 không mô phỏng thời gian thật phức tạp. Dùng proxy dễ tái hiện.

\[
C_{op}(P)
=
\alpha R(P)
+
\beta RetrievalDelay(P)
+
\gamma InvalidPenalty(P)
\]

Trong đó:

## 11.1. Relocation count

\[
R(P)=\text{số relocation action trong plan}
\]

## 11.2. Retrieval delay proxy

Reviewer yêu cầu làm rõ phần này.

Dùng rank-based proxy:

\[
RetrievalDelay(P)
=
\sum_{c\in Urgent}
pos(c,P)
\]

Trong đó:

- \(Urgent\): tập container có priority cao theo \(I^{new}\).
- \(pos(c,P)\): vị trí retrieval của container \(c\) trong plan \(P\).

Nếu container không được retrieve trong plan:

\[
pos(c,P)=|P|+1
\]

Chuẩn hóa:

\[
RetrievalDelayNorm(P)
=
\frac{
RetrievalDelay(P)
}{
|Urgent|(|P|+1)
}
\]

## 11.3. Invalid penalty

Nếu plan invalid:

\[
InvalidPenalty(P)=M_{inf}
\]

với \(M_{inf}\) rất lớn.

Nếu valid:

\[
InvalidPenalty(P)=0
\]

Paper 1 đặt:

```text
M_inf = 10^6
```

(Đặt tên `M_inf` để tránh trùng với `M` = số neighbor tối đa mỗi vòng lặp trong Local Search Repair — mục 15.2/46.3.)

## 11.4. Default weights

```text
alpha = 1.0
beta  = 0.5
gamma = 1.0
```

`gamma` nhân với `InvalidPenalty(P)` ở mục 11.3 (đã bằng `M_inf = 10^6` khi invalid, `0` khi valid) — không dùng `gamma = 1000` như bản nháp trước, để tránh nhân đôi độ lớn (`gamma × M_inf`) một cách không cần thiết. Đây là bộ trọng số duy nhất, khớp với mục 45.1 và bảng tham số mặc định mục 48.

Weights được kiểm tra trong sensitivity analysis.

---

# 12. Module 7 — Time-weighted Stability Cost

## 12.1. Mục tiêu

Đo mức độ plan mới phá vỡ plan cũ.

Thay đổi action gần hiện tại nghiêm trọng hơn thay đổi action ở tương lai xa.

\[
D(P,P^{old})
=
\sum_{i=1}^{L}
\omega(i)
\cdot
d_i(P,P^{old})
\]

Trong đó:

\[
\omega(i)=\exp(-\rho i)
\]

- \(i\): vị trí action trong plan.
- \(\rho\): tốc độ giảm penalty theo thời gian.
- Paper 1 dùng \(\rho=0.05\) (đồng bộ với mục 45.3 và bảng tham số mặc định — mục 48; sensitivity `{0.01, 0.05, 0.1}`).

## 12.2. Action-level difference

\[
d_i =
p_c \cdot \mathbf{1}[container_i \neq container_i^{old}]
+
p_a \cdot \mathbf{1}[actionType_i \neq actionType_i^{old}]
+
p_d \cdot \mathbf{1}[destination_i \neq destination_i^{old}]
+
p_o \cdot \mathbf{1}[orderChanged_i]
+
p_m \cdot \mathbf{1}[committedChanged_i]
+
p_f \cdot \mathbf{1}[frozenViolation_i]
\]

Trong đó `committedChanged_i` = true nếu action đó có `commit_status = "committed"` (đã giao nhưng chưa frozen theo mục 10) và bị thay đổi bất kỳ thành phần nào ở trên; `frozenViolation_i` = true nếu action nằm trong `P_frozen` và bị thay đổi (vi phạm cứng, không được phép).

Default penalties:

```text
p_c = 2    # changed container
p_a = 2    # changed action type
p_d = 1    # changed destination
p_o = 1    # changed ordering
p_m = 10   # changed action đã committed (chưa frozen)
p_f = INF  # changed frozen action (invalid, bị loại)
```

Đây là công thức d_i duy nhất dùng trong toàn bộ tài liệu (thay cho bản case-table đơn giản hoá trước đây ở mục 45.3, nay đã gộp về đây).

Nếu action ở plan mới và plan cũ có độ dài khác nhau, phần thiếu/thừa được tính là inserted/deleted action với penalty:

```text
p_insert = 1.5
p_delete = 1.5
```

---

# 13. Module 8 — Data Confidence Penalty

Paper 1 dùng bản đơn giản, nhưng refined theo review bằng confidence-weighted changes.

\[
C_{data}(P)
=
\sum_{a\in Changes(P,P^{old})}
importance(a)
\cdot
(1-Conf(a))
\]

Trong Paper 1 có thể đơn giản hóa:

\[
C_{data}(P)
=
Changes(P,P^{old})
\times
(1-Conf(I^{new}))
\]

Khuyến nghị implementation:

- Bản chính: simple form.
- Appendix hoặc ablation: action-weighted form.

Mục đích:

> Nếu thông tin mới có confidence thấp, hệ thống sẽ ít thay đổi plan hơn.

---

# 14. Module 9 — Candidate Repair Generator

Paper 1 giảm số candidate để dễ triển khai và tái hiện.

## 14.1. Candidate C0 — Keep old plan

```text
P0 = P_old
```

Luôn có candidate này.

## 14.2. Candidate C1 — Minimal Feasibility Repair

Chỉ sửa action invalid hoặc affected.

Procedure:

```text
For each affected action in P_tail:
    if action invalid:
        replace destination by nearest valid destination
    if action obsolete:
        remove action
    if urgent container is delayed:
        try insert retrieval-supporting relocation earlier
Return repaired plan
```

## 14.3. Candidate C2 — Local Search Repair

Dùng stochastic hill climbing.

## 14.4. Candidate C3 — Constrained CRP_RL / Full Reoptimization on Tail

Giữ frozen prefix, gọi CRP_RL hoặc heuristic solver cho phần tail.

```text
P3 = P_frozen + CRP_RL(s_after_frozen, updated_retrieval_info)
```

Nếu không tích hợp được CRP_RL trong repair phase, dùng heuristic CRP solver.

---

# 15. Local Search Repair cụ thể

## 15.1. Neighborhood operations

Từ plan hiện tại \(P\), sinh neighbor bằng một trong 5 operation:

### N1 — Change relocation destination

Chọn một relocation action và đổi destination sang một stack hợp lệ khác.

### N2 — Swap two non-frozen actions

Đổi vị trí hai action trong tail nếu vẫn feasible.

### N3 — Insert urgent-support action

Thêm một relocation action để unblock urgent target.

### N4 — Remove obsolete action

Xóa một relocation action không còn cần thiết.

### N5 — Replace action by CRP_RL suggested action

Thay một action trong tail bằng action do CRP_RL/heuristic đề xuất ở state tương ứng.

## 15.2. Search strategy

Dùng stochastic hill climbing.

Parameters:

```text
T = 100        # số vòng lặp tối đa
M = 50         # số neighbor tối đa mỗi vòng
epsilon = 0.05 # xác suất chấp nhận neighbor tệ hơn nhẹ để tránh local optimum
```

Algorithm:

```text
Input: P_start, P_old, s_t, I_new

P_best = P_start
score_best = J(P_best)

for iter in 1..T:
    Generate up to M valid neighbors of P_best
    Evaluate J(neighbor)
    Let P_candidate be best neighbor

    if J(P_candidate) < J(P_best):
        P_best = P_candidate
    else if random() < epsilon:
        P_best = P_candidate

return P_best
```

Termination:

```text
stop if iter = T
or no valid neighbor found for 10 consecutive iterations
or runtime > T_max
```

---

# 16. Simple Fallback / Rollback for Paper 1

Không làm rollback phức tạp.

Sau khi có \(P_{best}\):

Nếu:

```text
P_best invalid
runtime timeout
P_best violates frozen prefix
J(P_old) - J(P_best) <= tau
```

thì:

```text
return KEEP(P_old)
```

Ngược lại:

```text
return UPDATE(P_best)
```

---

# 17. Timeout setting

Theo review, cần đặt timeout rõ.

Default timeout:

```text
Small instance  : 1 second
Medium instance : 5 seconds
Large instance  : 30 seconds
```

Nếu vượt timeout:

```text
fallback to Minimal Repair
if Minimal Repair invalid:
    keep old plan
```

Metrics ghi:

```text
mean runtime
P95 runtime
timeout rate
fallback rate
```

## 17.1. Hardware reporting

Tất cả kết quả runtime phải ghi rõ hardware:

```text
CPU model
RAM
GPU used or not
Python version
solver/library version nếu có
```

Default experimental setup nên ưu tiên CPU-only để phản ánh điều kiện triển khai thực tế:

```text
All runtime results are reported on CPU-only execution unless explicitly stated otherwise.
```

Nếu dùng GPU cho CRP_RL inference, phải báo cáo riêng runtime có GPU và không GPU.

---

# 18. Algorithm SAR-CRP Core

```text
Algorithm: SAR-CRP v2 Core

Input:
    s_t, P_old, I_old, I_new
    freeze size H_f
    lambda, mu, tau
    timeout T_max

1. Compute confidence:
       Conf = exp(-eta * age(I_new))

2. Estimate event impact:
       I_order    = top-k Kendall-tau distance
       I_target   = target changed indicator
       I_blocking = saturated mean blocker change
       I_plan     = affected-action ratio
       I_conf     = 1 - Conf

       Impact = weighted sum

3. If Impact < theta_impact:
       return KEEP(P_old)

4. Split plan:
       P_frozen = first H_f actions of P_old
       P_tail   = remaining actions

5. Generate candidates:
       C0 = P_old
       C1 = MinimalFeasibilityRepair(P_old)
       C2 = LocalSearchRepair(C1)
       C3 = P_frozen + CRP_RL/heuristic repair on tail

6. For each candidate P:
       if violates frozen prefix:
            discard
       if invalid:
            assign high penalty
       compute:
            C_op(P)
            D(P, P_old)
            C_data(P)
            J(P) = C_op + lambda*D + mu*C_data

7. Select:
       P_best = argmin J(P)

8. Fallback check:
       if timeout or invalid(P_best):
            return KEEP(P_old)

       if J(P_old) - J(P_best) <= tau:
            return KEEP(P_old)

9. Return UPDATE(P_best)
```

---

# 19. Benchmark v2 Final

## 19.1. Source

Tạo benchmark từ:

```text
CRP_RL benchmark
+ classical CRP instances
+ synthetic dynamic event stream
```

## 19.2. Instance schema

```json
{
  "instance_id": "...",
  "layout": {
    "num_stacks": 10,
    "max_tier": 5
  },
  "initial_state": "...",
  "initial_retrieval_order": ["C1", "C2", "..."],
  "initial_plan": ["a1", "a2", "..."],
  "event_stream": [
    {
      "time": 5,
      "type": "urgent_insertion",
      "container": "C8",
      "confidence": 0.9
    }
  ],
  "freeze_size": 3,
  "cost_parameters": {
    "lambda": 0.5,
    "mu": 0.2
  }
}
```

---

# 20. Sanity Check cho benchmark động

Vì benchmark dynamic là synthetic, cần kiểm tra độ hợp lý trước khi dùng cho paper.

## SC1 — Benchmark không quá dễ

Chạy Static Plan trên dynamic benchmark.

Nếu Static Plan vẫn gần bằng Full Reoptimization:

```text
benchmark quá dễ
cần tăng event severity
```

## SC2 — Benchmark không quá khó

Nếu Static Plan luôn invalid hoặc cost cực lớn:

```text
benchmark quá khó
event stream phi thực tế
```

## SC3 — Event distribution hợp lý

Kiểm tra:

```text
tỷ lệ urgent insertion
tỷ lệ order swap
tỷ lệ stale information
số event trung bình / instance
mức thay đổi top-k rank
mức thay đổi blocker pressure
```

## SC4 — Impact distribution

Impact score không nên toàn gần 0 hoặc toàn gần 1.

Nên có phân bố:

```text
low impact
medium impact
high impact
```

---

# 21. Ground truth / proxy

## 21.1. Small instances

Dùng exhaustive search hoặc branch-and-bound để tìm near-optimal solution.

Mục đích:

```text
kiểm tra chất lượng thuật toán
đo optimality gap
```

## 21.2. Medium / large instances

Dùng Full Reoptimization with extended time limit làm proxy upper bound.

Ví dụ:

```text
normal timeout: 5s
offline upper bound: 300s
```

Không claim đây là true optimum.

Chỉ gọi là:

```text
offline high-quality proxy
```

---

# 22. Baselines Final

Theo review, giảm từ 9 baseline xuống 6 baseline chính.

## B1 — Static Plan

Không replan khi event xảy ra.

## B2 — Full Reoptimization

Mỗi event gọi CRP solver tối ưu lại toàn bộ.

## B3 — Periodic Replanning

Replan mỗi fixed interval.

Ví dụ:

```text
every 10 events
or every T simulated steps
```

## B4 — Event-triggered Replanning without Stability

Có trigger nhưng objective không có stability cost.

## B5 — MPC-style Receding Horizon

Tại mỗi event hoặc horizon, tối ưu lại window ngắn phía trước.

## B6 — SAR-CRP Core

Proposed method.

## Optional baseline — RL with Stability Penalty

Không bắt buộc Paper 1.

Nếu không làm, giải thích:

```text
RL cần nhiều training data
khó đảm bảo safety
khó explain
khó transfer sang layout/cảng mới
và mục tiêu Paper 1 là deployable stable repair framework
```

Câu nên đưa vào paper:

> RL with stability penalty is considered an optional exploratory baseline. It is not included in the main comparison because training a safe and transferable replanning policy requires substantial interaction data and is less explainable than the proposed repair-based approach.

Nếu có thêm thời gian, có thể cài một baseline PPO đơn giản với reward:

\[
r_t = -C_{op}(P_t) - \lambda D(P_t,P^{old})
\]

nhưng baseline này không phải điều kiện bắt buộc của Paper 1.

---

# 23. Experiments Final

Theo review, gộp experiment để tránh loãng.

## Experiment 1 — Main Factorial Experiment

Mục tiêu:

Đánh giá SAR-CRP dưới nhiều điều kiện.

Factors:

```text
uncertainty level: low / medium / high
freeze size      : 0 / 3 / 5
lambda           : 0 / 0.5 / 1.0
```

Lưu ý: khoảng `lambda` dùng trong factorial experiment này (`{0, 0.5, 1.0}`) khác có chủ đích với khoảng sensitivity ở bảng tham số mặc định mục 48 (`{0.5, 1, 2}`, quét quanh default `λ=1.0`). Ở đây `λ=0` được giữ lại vì nó tương đương ablation A3 — No Stability Cost (mục 25) và cần thiết để đo trade-off operational/stability trong cùng một thiết kế factorial. Không hợp nhất hai khoảng này thành một.

So sánh 6 baseline chính.

Metrics:

```text
operational cost
stability cost
total cost
runtime
fallback rate
```

## Experiment 2 — Benchmark Sanity + Ground Truth Small

Mục tiêu:

- kiểm tra benchmark không quá dễ/quá khó;
- so với exhaustive search trên instance nhỏ;
- đo optimality gap.

## Experiment 3 — Cross-layout Validation

Ít nhất 3 layout:

```text
small layout
medium layout
large layout
```

Hoặc:

```text
layout A: train/tune parameters
layout B/C: test
```

Quy tắc bắt buộc:

```text
Tune hyperparameters only on Layout A.
Evaluate Layouts B and C using the same tuned hyperparameters.
Do not retune on Layouts B/C.
```

Câu nên đưa thẳng vào paper:

> We tune hyperparameters on Layout A only. Layouts B and C are evaluated with the same hyperparameters without further tuning, in order to measure cross-layout generalization.

Metrics:

```text
performance drop
stability preservation
runtime scaling
```

## Experiment 4 — Data Confidence Sensitivity

Kiểm tra:

```text
Conf = 1.0 / 0.7 / 0.4 / 0.2
```

Mục tiêu:

SAR-CRP có giảm mức thay đổi plan khi confidence thấp không?

## Experiment 5 — Optional Operator Acceptance Proxy/User Study

### Option A — Proxy only

Dùng metrics:

```text
changed actions
changed frozen actions
plan churn
explanation simplicity
```

### Option B — Small user study nếu làm được

Đối tượng:

```text
5-10 người hiểu logistics / vận hành / optimization
```

Task:

```text
So sánh Full Reoptimization vs SAR-CRP plan
Chọn plan dễ chấp nhận hơn
Đo thời gian hiểu plan
Đo preference
```

**Ràng buộc bắt buộc khi báo cáo Option B (n=5-10 là quá nhỏ để có ý nghĩa thống kê):**

```text
- Gọi rõ đây là "exploratory qualitative pilot", không dùng p-value/CI
  để claim significance với n nhỏ như vậy.
- Không dùng kết quả Option B làm evidence chính cho contribution claims
  (mục 29) — chỉ dùng làm minh hoạ bổ trợ cho Option A (proxy metrics).
- Báo cáo đầy đủ: số người, background, và toàn bộ câu trả lời/quan sát
  định tính, không chỉ con số tổng hợp.
- Nếu muốn claim định lượng về operator acceptance, phải tăng n hoặc
  chuyển hẳn sang thiết kế HCI/khảo sát chuyên biệt — nằm ngoài phạm vi Paper 1.
```

Nếu không làm user study, đưa vào future work.

---

## 23.6. Statistical Protocol (bắt buộc cho Experiment 1, 3, 4)

Reviewer thực nghiệm Q1 sẽ hỏi ngay: chạy bao nhiêu lần, có ý nghĩa thống kê không. Paper 1 cần cố định trước:

```text
Số lần lặp:
    Mỗi (instance, uncertainty level, baseline) chạy với >= 20 random
    seed khác nhau (seed kiểm soát: event stream generation + bất kỳ
    randomness nào trong CRP_RL/local search).
    Instance nhỏ (Experiment 2, ground truth) có thể dùng ít seed hơn
    nếu đã exhaustive/branch-and-bound (không có randomness).

Báo cáo:
    Mean +/- 95% CI (bootstrap hoặc t-distribution) cho mọi metric
    chính trong mục 24 (operational cost, stability cost, total cost,
    runtime, fallback rate).

Kiểm định ý nghĩa (so sánh SAR-CRP vs từng baseline B1-B5):
    Dùng Wilcoxon signed-rank test (paired, vì cùng chạy trên cùng bộ
    instance/seed) trên total cost và stability cost.
    Không dùng t-test trừ khi đã kiểm tra phân phối gần chuẩn.

Hiệu chỉnh multiple comparison:
    So sánh với 5 baseline chính (B1-B5) => dùng Holm-Bonferroni
    correction để tránh false positive khi báo cáo "SAR-CRP tốt hơn
    có ý nghĩa" trên nhiều baseline cùng lúc.

Effect size:
    Báo cáo thêm effect size (vd. rank-biserial correlation hoặc
    Cliff's delta) bên cạnh p-value — p-value nhỏ với cỡ mẫu lớn
    (nhiều seed) không tự động nghĩa là khác biệt có ý nghĩa thực tế.

Ablation (mục 25):
    Áp dụng cùng protocol trên (mỗi ablation vs SAR-CRP Core đầy đủ).
```

Thêm vào Metrics Final (mục 24) một dòng "Statistical reporting" trỏ về mục này, không lặp lại nội dung.

---

# 24. Metrics Final

## 24.1. Operational metrics

```text
relocation count
retrieval delay proxy
invalid plan rate
operational cost
```

## 24.2. Stability metrics

```text
changed actions
changed destinations
changed action order
changed frozen actions
plan churn rate
stability cost
```

## 24.3. Trade-off metric

```text
total cost = operational cost + lambda * stability cost + mu * data cost
```

## 24.4. Runtime metrics

```text
mean runtime
P95 runtime
timeout rate
fallback rate
```

## 24.5. Robustness metrics

```text
performance under high uncertainty
performance under low confidence
cross-layout performance drop
```

## 24.6. Statistical reporting

Mọi metric ở 24.1–24.5 khi dùng để so sánh SAR-CRP với baseline phải báo cáo theo protocol ở mục 23.6 (mean ± 95% CI, Wilcoxon signed-rank test, Holm-Bonferroni correction, effect size) — không lặp lại chi tiết ở đây.

---

# 25. Ablation Study

Giữ 6 ablation chính.

## A1 — No Trigger

Always replan.

## A2 — No Freeze Horizon

Cho phép sửa toàn bộ plan.

## A3 — No Stability Cost

Chỉ optimize operational cost.

## A4 — No Local Search

Chỉ dùng minimal repair hoặc full reoptimization.

## A5 — No Data Confidence Penalty

Không xét confidence.

## A6 — No Blocking Impact

Impact không dùng \(I_{blocking}\).

Mục tiêu:

Chứng minh từng module có đóng góp.

---

# 26. Expected Results

Kỳ vọng hợp lý:

## SAR-CRP không nhất thiết ít relocation nhất

Full Reoptimization có thể ít relocation hơn.

Nhưng SAR-CRP nên tốt hơn ở:

```text
total cost
stability cost
changed actions
runtime
operator acceptance proxy
```

## Khi uncertainty thấp

SAR-CRP gần với Full Reoptimization về operational cost nhưng ít thay đổi plan hơn.

## Khi uncertainty cao

SAR-CRP tránh replan quá mạnh, nên stability tốt hơn.

## Khi confidence thấp

SAR-CRP nên ít thay đổi plan hơn baseline không xét confidence.

## Khi layout thay đổi

SAR-CRP nên giảm hiệu suất vừa phải, không collapse.

---

# 27. Implementation Roadmap

## Phase 0 — Reproduce CRP_RL

Mục tiêu:

```text
run baseline
extract action sequence
log state/action/relocation
```

Output:

```text
working CRP solver wrapper
```

## Phase 1 — Dynamic Event Generator

Implement:

```text
order swap
urgent insertion
ETA early/late
probability update
stale information
```

Output:

```text
dynamic CRP benchmark v1
```

## Phase 2 — Cost and Impact Functions

Implement:

```text
I_order
I_target
I_blocking
I_plan
I_conf
C_op
D_stability
C_data
```

Output:

```text
scoring library
```

## Phase 3 — SAR-CRP Core

Implement:

```text
trigger
freeze horizon
minimal repair
local search repair
candidate selector
fallback
```

Output:

```text
SAR-CRP runnable method
```

## Phase 4 — Baselines

Implement:

```text
static
full reoptimization
periodic replanning
event-triggered without stability
MPC-style receding horizon
```

Output:

```text
baseline suite
```

## Phase 5 — Small MVP Experiment

Chỉ chạy:

```text
1 layout nhỏ
3 baselines: static, full reoptimization, SAR-CRP
low/medium/high uncertainty
```

Decision gate:

```text
Nếu SAR-CRP không có trade-off tốt:
    sửa objective/trigger
Nếu có:
    mở rộng experiment
```

## Phase 6 — Full Experiment

Chạy 5 experiments final.

## Phase 7 — Paper Writing

Viết theo structure:

```text
Introduction
Literature Review
Problem Formulation
Method
Benchmark
Experiments
Results
Discussion
Limitations
Conclusion
```

---

# 28. Paper Structure đề xuất

## 1. Introduction

- CRP quan trọng.
- Thông tin retrieval thay đổi trong thực tế.
- Full reoptimization gây plan churn.
- Need stable adaptive replanning.
- Contributions.

## 2. Related Work

- CRP and DRL CRP.
- Stochastic/real-time CRP.
- Dynamic scheduling stability.
- MPC/receding horizon.
- Gap.

## 3. Problem Formulation

- State.
- Plan.
- Event.
- Cost.
- Stability.
- Objective.

## 4. SAR-CRP Method

- Impact estimator.
- Trigger.
- Freeze.
- Repair.
- Candidate selection.
- Fallback.

## 5. Dynamic Benchmark

- Event generator.
- Confidence.
- Sanity check.
- Ground truth/proxy.

## 6. Experiments

- Baselines.
- Metrics.
- Setup.
- Ablation.

## 7. Results

- Main results.
- Trade-off.
- Ablation.
- Runtime.
- Cross-layout.

## 8. Discussion

- Why not always full reoptimization.
- Why not direct RL.
- Product relevance.
- Operator implications.

## 9. Limitations

- Synthetic benchmark — tham số event generator (mục 39.1.1) là heuristic, chưa hiệu chỉnh từ log cảng thật; kết luận cần đọc với điều kiện "dưới giả định phân bố event này".
- Limited operator validation — user study (Experiment 5, Option B) chỉ 5-10 người, mang tính exploratory/qualitative, không đủ lực thống kê để generalize (mục 23, Option B).
- Simplified confidence.
- CRP-only scope.
- Nhiều ngưỡng heuristic cố định (θ_impact, r_shift, σ_b, H_f...) được chọn thủ công và chỉ kiểm tra bằng sensitivity analysis cục bộ quanh default, không phải học/tối ưu từ dữ liệu — nêu rõ đây là thiết kế có chủ đích để dễ tái hiện, không phải giới hạn có thể khắc phục dễ dàng trong Paper 1.
- Base papers tham chiếu (mục 3) cần được xác minh tồn tại/đúng thông tin trước khi công bố — nếu đến lúc submit vẫn chưa xác minh được, phải thay bằng nguồn khác tương đương.

## 10. Conclusion

- Stable adaptive replanning is necessary.
- SAR-CRP improves trade-off between operational efficiency and plan stability.

---

# 29. Q1 Contribution Claims

Nên claim vừa đủ:

## C1

A stable adaptive replanning formulation for CRP under imperfect and evolving retrieval information.

## C2

A concrete event impact estimator combining retrieval-order change, target change, blocking-pressure change, plan impact and information confidence.

## C3

A time-weighted plan stability cost that penalizes changes to near-term and committed actions more heavily.

## C4

A local-search repair planner that revises only affected parts of the plan while respecting a freeze horizon.

## C5

A dynamic CRP benchmark with event streams, sanity checks, ground-truth/proxy evaluation and cross-layout validation.

## C6

An empirical study showing the trade-off between operational efficiency, stability, robustness and runtime.

---

# 30. Những gì không làm trong Paper 1

Để tránh scope quá rộng, Paper 1 không làm sâu:

```text
full Data Reliability Layer
full Execution Feedback Loop
advanced Rollback Manager
multi-crane scheduling
truck appointment control
real TOS integration
full operator-in-the-loop deployment
transfer learning/few-shot calibration
deep RL replanning policy
```

Các phần này đưa vào:

```text
future work
appendix architecture
Paper 2 roadmap
```

---

# 31. Chốt chiến lược

Bản final sau review nên tập trung vào câu sau:

> **We do not propose another CRP solver. We propose a stable adaptive replanning layer that decides when and how to revise an existing CRP plan under evolving and imperfect retrieval information, while explicitly trading off operational efficiency against plan stability.**

Tiếng Việt:

> **Chúng tôi không đề xuất thêm một CRP solver mới. Chúng tôi đề xuất một lớp stable adaptive replanning quyết định khi nào và cách nào nên sửa kế hoạch CRP hiện có khi thông tin retrieval thay đổi và không hoàn hảo, đồng thời tối ưu đồng thời hiệu quả vận hành và độ ổn định của kế hoạch.**

Đây là định vị gọn, đúng novelty, không bị lan man, và phù hợp cho Paper Q1 đầu tiên.

---

# 32. Checklist trước khi code

Trước khi code lớn, cần hoàn thành:

```text
[ ] Reproduce CRP_RL baseline
[ ] Extract plan/action sequence
[ ] Define dynamic event schema
[ ] Implement 5 event types
[ ] Implement I_order
[ ] Implement I_target
[ ] Implement I_blocking refined
[ ] Implement I_plan with affected action definition
[ ] Implement I_conf
[ ] Implement C_op with retrieval delay proxy
[ ] Implement time-weighted stability cost
[ ] Implement simple data cost
[ ] Implement freeze horizon
[ ] Implement minimal repair
[ ] Implement local search repair
[ ] Implement fallback keep-old-plan
[ ] Implement 3 MVP baselines
[ ] Run MVP experiment on small layout
[ ] Check if SAR-CRP has better total cost trade-off
```

Nếu MVP fail, không chạy full experiment. Sửa objective/trigger trước.

---

# 33. Final MVP để bắt đầu ngay

MVP đầu tiên chỉ cần:

```text
Methods:
1. Static
2. Full Reoptimization
3. SAR-CRP Core

Layout:
1 small layout

Events:
order swap
urgent insertion
ETA early/late

Metrics:
relocation count
changed actions
total cost
runtime
```

Mục tiêu MVP:

```text
Chứng minh SAR-CRP giảm plan churn đáng kể
trong khi không làm operational cost tăng quá nhiều.
```

Nếu MVP đạt:

```text
SAR-CRP total cost < Static
SAR-CRP stability cost < Full Reoptimization
SAR-CRP operational cost close to Full Reoptimization
```

thì mới mở rộng thành full Q1 experiment.

---

# 34. Kết luận

SAR-CRP v2 sau second review cần được viết lại theo hướng:

```text
ít module hơn
ít baseline hơn
ít experiment hơn
nhưng công thức rõ hơn
local search rõ hơn
benchmark sanity rõ hơn
timeout rõ hơn
affected action rõ hơn
retrieval delay proxy rõ hơn
```

Như vậy paper sẽ không bị xem là một system proposal quá rộng, mà trở thành một nghiên cứu có core contribution rõ:

> **Stable adaptive replanning for CRP with explicit operational-stability trade-off.**
---

# 35. Implementation Appendix — bổ sung để lập trình viên có thể code ngay

Phần này được bổ sung theo nhận xét ultra-final: proposal trước đã đủ về mặt nghiên cứu, nhưng cần thêm **schema dữ liệu, mapping baseline với paper, flow dữ liệu, wrapper CRP_RL, event generator, hàm blocker, confidence, local search và bảng tham số mặc định** để lập trình viên không phải tự đoán.

---

# 36. Phạm vi code cho Paper 1

Paper 1 chỉ code SAR-CRP Core. Không tích hợp đa cần cẩu, không làm TOS thật, không làm scheduling phức tạp.

## 36.1. Code trong Paper 1

```text
1. CRP_RL wrapper
2. Dynamic event generator
3. Yard state schema
4. Plan/action schema
5. Event schema
6. Event Impact Estimator
7. Replanning Trigger
8. Freeze Horizon
9. Candidate Repair Generator
10. Stability-aware Candidate Selector
11. Fallback: Minimal Repair -> Keep Old Plan
12. Benchmark runner
13. Baseline runner
14. Metrics logger
```

## 36.2. Không code trong Paper 1

```text
1. Multi-crane scheduling
2. TOS/TAS/ECS integration thật
3. Operator feedback learning
4. Full data reliability layer
5. Full execution feedback loop
6. Transfer learning / few-shot calibration
7. Production dashboard
```

Giả định trong Paper 1:

> We assume a single relocation resource or that crane scheduling is handled separately. The focus of this paper is not crane assignment, but stable replanning of the relocation plan under evolving retrieval information.

---

# 37. Data Schema chuẩn

## 37.1. YardState schema

```json
{
  "instance_id": "inst_0001",
  "time_step": 0,
  "layout": {
    "num_stacks": 6,
    "max_tier": 5
  },
  "stacks": [
    {
      "id": "S1",
      "containers": ["C10", "C07", "C03"],
      "max_tier": 5
    },
    {
      "id": "S2",
      "containers": ["C09", "C04"],
      "max_tier": 5
    }
  ],
  "container_attributes": {
    "C03": {
      "size": "40ft",
      "weight_class": "medium",
      "status": "available"
    }
  },
  "retrieval_queue": ["C01", "C02", "C03", "C04", "C05"],
  "pickup_prob": {
    "C01": 0.95,
    "C02": 0.80,
    "C03": 0.60
  },
  "data_timestamp": 0,
  "state_confidence": 1.0
}
```

Quy ước stack:

```text
containers[0]  = đáy stack
containers[-1] = đỉnh stack
```

Ví dụ:

```json
{"containers": ["C10", "C07", "C03"]}
```

thì `C03` nằm trên cùng, `C10` nằm dưới cùng.

---

## 37.2. Plan schema

Một plan là list các action.

```json
{
  "plan_id": "plan_0001",
  "created_at": 0,
  "source": "CRP_RL",
  "actions": [
    {
      "action_id": "a001",
      "step_index": 0,
      "type": "RELOCATE",
      "container": "C03",
      "source_stack": "S1",
      "dest_stack": "S3",
      "commit_status": "committed",
      "planned_time": 1
    },
    {
      "action_id": "a002",
      "step_index": 1,
      "type": "RETRIEVE",
      "container": "C01",
      "source_stack": "S4",
      "dest_stack": null,
      "commit_status": "planned",
      "planned_time": 2
    }
  ]
}
```

`type` gồm:

```text
RELOCATE
RETRIEVE
NOOP
```

`commit_status` gồm:

```text
executed    : đã làm, không được sửa
committed   : đã giao/sắp làm, không nên sửa
planned     : chưa giao, có thể sửa
cancelled   : đã hủy
```

---

## 37.3. RetrievalInformation schema

```json
{
  "info_id": "info_0001",
  "timestamp": 10,
  "retrieval_queue": ["C01", "C04", "C02", "C03", "C05"],
  "pickup_prob": {
    "C01": 0.95,
    "C04": 0.88,
    "C02": 0.65,
    "C03": 0.55
  },
  "urgent_containers": ["C04"],
  "confidence": 0.85,
  "source": "synthetic_event_generator"
}
```

---

## 37.4. Event schema

```json
{
  "event_id": "e001",
  "time_step": 10,
  "type": "ORDER_SWAP",
  "severity": "medium",
  "affected_containers": ["C02", "C04"],
  "old_queue": ["C01", "C02", "C03", "C04", "C05"],
  "new_queue": ["C01", "C04", "C03", "C02", "C05"],
  "confidence": 0.85,
  "timestamp_generated": 10,
  "timestamp_observed": 10,
  "metadata": {
    "swap_distance": 2
  }
}
```

Các event type trong Paper 1:

```text
ORDER_SWAP
URGENT_INSERTION
ETA_EARLY
ETA_LATE
PROBABILITY_UPDATE
STALE_INFORMATION
```

---

# 38. Các hàm dữ liệu cốt lõi

## 38.1. Hàm tìm stack chứa container

```text
Function find_stack(state, container_id):
    for stack in state.stacks:
        if container_id in stack.containers:
            return stack.id
    return None
```

---

## 38.2. Hàm tính blocker count B(c)

`B(c)` là số container nằm phía trên container `c` trong cùng stack.

```text
Function blocker_count(state, c):
    stack = find_stack(state, c)
    if stack is None:
        return 0

    containers = stack.containers
    index = position of c in containers
    return len(containers) - index - 1
```

Ví dụ:

```text
Stack S1 = [C10, C07, C03]
B(C10) = 2
B(C07) = 1
B(C03) = 0
```

---

## 38.3. Hàm tính blocker pressure cho Top-K

```text
Function blocker_pressure(state, retrieval_queue, K):
    topK = first K containers in retrieval_queue
    total = 0
    for c in topK:
        total += blocker_count(state, c)
    return total
```

---

## 38.4. Hàm confidence theo age

Age của thông tin:

```text
age(I) = current_time - I.timestamp_observed
```

Confidence đơn giản:

```text
Conf(I) = base_confidence * exp(-age(I) / tau_age)
```

Trong đó:

```text
base_confidence = confidence gốc của event
age(I)          = độ trễ thông tin
τ_age           = tham số decay, mặc định 10 steps
```

Nếu không có timestamp thực, trong benchmark synthetic dùng:

```text
age = timestamp_observed - timestamp_generated
```

---

# 39. Event Stream Generator

## 39.1. Tham số mặc định

```text
p_event  = 0.30
p_swap   = 0.40
p_urgent = 0.25
p_eta    = 0.20
p_prob   = 0.10
p_stale  = 0.05
```

Tổng bằng 1 trong nhóm event khi event xảy ra.

Severity:

```text
low    : rank shift 1-2
medium : rank shift 3-5
high   : rank shift >5
```

Confidence:

```text
low uncertainty    : Uniform(0.80, 1.00)
medium uncertainty : Uniform(0.50, 0.90)
high uncertainty   : Uniform(0.20, 0.80)
```

## 39.1.1. Căn cứ và giới hạn của các tham số trên

Các giá trị `p_event, p_swap, p_urgent, p_eta, p_prob, p_stale` và các ngưỡng severity/confidence ở trên là **giả định heuristic của nhóm nghiên cứu**, không được hiệu chỉnh (calibrate) từ log vận hành cảng thật. Đây là một điểm reviewer thực nghiệm rất dễ chất vấn ("tại sao đúng những con số này?"). Cách xử lý cho Paper 1:

```text
1. Nếu có log thật (dù chỉ một phần, ví dụ tỷ lệ container đổi ưu tiên/no-show
   trong vài ca trực), dùng nó để ước lượng lại p_swap/p_urgent/p_stale
   thay vì heuristic, và ghi rõ nguồn dữ liệu.
2. Nếu không có log thật, giữ nguyên các giá trị này nhưng:
   a. Nêu rõ trong paper đây là "assumed synthetic distribution", không
      claim phản ánh phân bố thật của một cảng cụ thể.
   b. Bắt buộc chạy sanity check SC1-SC4 (mục 20/49) và báo cáo kết quả
      như bằng chứng gián tiếp cho việc benchmark "đủ khó, đủ hợp lý".
   c. Đưa "calibration against real port logs" vào Limitations (mục 28,
      phần 9. Limitations) và Future Work — không âm thầm bỏ qua.
3. Bắt buộc chạy Experiment 1 (Main Factorial) với ít nhất 2 mức
   uncertainty khác severity/confidence range để chứng minh kết luận
   không chỉ đúng với một bộ tham số sinh event cụ thể.
```

Nói ngắn gọn: các con số này **được phép** dùng làm default để code và chạy MVP, nhưng **không được** trình bày trong paper như thể chúng có căn cứ thực nghiệm nếu chưa thực sự hiệu chỉnh từ dữ liệu thật.

---

## 39.2. Event generator pseudocode

```text
Function generate_event_stream(initial_queue, T, uncertainty_level):
    queue = copy(initial_queue)
    events = []

    for t in 1..T:
        if random() > p_event:
            continue

        event_type = sample_from({
            ORDER_SWAP: p_swap,
            URGENT_INSERTION: p_urgent,
            ETA_EARLY_OR_LATE: p_eta,
            PROBABILITY_UPDATE: p_prob,
            STALE_INFORMATION: p_stale
        })

        severity = sample_severity(uncertainty_level)
        confidence = sample_confidence(uncertainty_level)

        if event_type == ORDER_SWAP:
            queue_new = apply_order_swap(queue, severity)
        elif event_type == URGENT_INSERTION:
            queue_new = apply_urgent_insertion(queue, severity)
        elif event_type == ETA_EARLY_OR_LATE:
            queue_new = apply_eta_shift(queue, severity)
        elif event_type == PROBABILITY_UPDATE:
            queue_new = queue
            update pickup_prob
        elif event_type == STALE_INFORMATION:
            queue_new = queue
            delay timestamp_observed

        event = build_event(t, event_type, queue, queue_new, confidence)
        events.append(event)
        queue = queue_new

    return events
```

---

# 40. Mapping baseline với paper tham chiếu

| Baseline | Paper / nguồn tham chiếu | Mô tả | Khác biệt với SAR-CRP |
|---|---|---|---|
| B1 Static Plan | Heuristic baseline | Tạo plan ban đầu rồi không replan | Không thích ứng với thông tin mới |
| B2 Full Reoptimization | Shin et al. 2026 / CRP_RL | Mỗi event gọi CRP_RL tối ưu lại toàn bộ phần còn lại | Không có stability cost, dễ đổi plan nhiều |
| B3 Periodic Replanning | Heuristic / rolling update practice | Replan mỗi K step | Không dựa trên event impact |
| B4 Event-triggered without Stability | Zhou & Zhang 2024 real-time stochastic CRP inspired | Có trigger khi thông tin thay đổi nhưng objective chỉ tối ưu operational cost | Không phạt plan instability |
| B5 MPC-style Receding Horizon | MPC / dynamic scheduling literature | Tối ưu trong rolling horizon | Không có affected-action repair và time-weighted stability cost riêng cho CRP |
| B6 SAR-CRP Core | Proposed | Trigger + freeze + local repair + stability objective | Đề xuất chính |
| Optional RL-Stability | Optional exploratory baseline | PPO/DQN reward = -operational cost - stability penalty | Không bắt buộc vì tốn training, khó safety/explainability |

Ghi chú:

- `Full Reoptimization` nên implement bằng wrapper CRP_RL nếu dùng repo Shin et al.
- `Event-triggered without Stability` có thể implement bằng cùng trigger với SAR-CRP nhưng đặt `λ = 0`.
- `MPC-style` có thể implement bằng periodic receding horizon với horizon cố định và không dùng local repair.

---

# 41. Nguồn gốc các thành phần của SAR-CRP

| Thành phần | Nguồn gốc / cảm hứng | Điều chỉnh trong SAR-CRP |
|---|---|---|
| CRP solver | Shin et al. 2026 CRP_RL | Dùng làm solver/candidate generator, không claim novelty |
| Evolving retrieval information | Stochastic/real-time CRP literature, Zhou & Zhang 2024 | Chuyển thành event stream cho benchmark động |
| Retrieval probability | Zhang et al. 2025 probabilistic retrieval | Dùng pickup probability/confidence, không claim prediction novelty |
| Event Impact Estimator | Dynamic scheduling impact analysis | Thiết kế riêng cho CRP bằng order/target/blocker/plan/confidence impact |
| Freeze Horizon | Commitment/frozen horizon trong production scheduling | Khóa các action đã committed hoặc gần execution |
| Stability Cost | Schedule stability/rescheduling literature | Time-weighted plan distance cho relocation plan |
| Local Search Repair | Repair-based planning, local search | Neighborhood riêng cho CRP: đổi destination, swap order, insert urgent, remove obsolete |
| Fallback | Production-safe optimization | Minimal Repair -> Keep Old Plan nếu invalid/timeout |
| Cross-layout validation | Generalization evaluation | Tune layout A, test B/C không retune |

---

# 42. Flow dữ liệu chi tiết

```text
Initial CRP instance
    |
    v
YardState S0 + RetrievalInfo I0
    |
    v
CRP_RL Wrapper
    |
    v
Initial Plan P_old
    |
    v
Simulator executes first actions
    |
    v
State S_t + Plan P_old_remaining
    |
    v
Dynamic Event Generator emits event e_t
    |
    v
Update RetrievalInfo: I_old -> I_new
    |
    v
Compute confidence Conf(I_new)
    |
    v
Event Impact Estimator
    |
    v
Impact score
    |
    +-- if impact < θ_impact --> Keep P_old
    |
    v
Freeze Horizon Manager
    |
    v
Frozen prefix + Repairable tail
    |
    v
Candidate Repair Generator
    |
    v
Candidate plans {P1, P2, ..., Pm}
    |
    v
Candidate Evaluator computes J(P)
    |
    v
Choose best candidate
    |
    +-- if invalid/timeout/gain <= τ --> Keep P_old
    |
    v
Return P_new
```

---

# 43. CRP_RL Wrapper interface

## 43.1. Input

```python
solve_crp(
    yard_state: YardState,
    retrieval_queue: list[str],
    constraints: dict | None = None,
    time_limit_sec: float | None = None,
) -> Plan
```

## 43.2. Output

```json
{
  "plan_id": "plan_crprl_001",
  "source": "CRP_RL",
  "actions": [
    {
      "type": "RELOCATE",
      "container": "C03",
      "source_stack": "S1",
      "dest_stack": "S4"
    },
    {
      "type": "RETRIEVE",
      "container": "C01",
      "source_stack": "S2",
      "dest_stack": null
    }
  ]
}
```

## 43.3. Wrapper constraints cho Partial Repair

```json
{
  "frozen_actions": ["a001", "a002"],
  "forbidden_moves": [
    {"container": "C03", "dest_stack": "S5"}
  ],
  "preferred_old_actions": true,
  "max_changed_actions": 5
}
```

Nếu CRP_RL gốc không hỗ trợ constraints trực tiếp, implement bằng cách:

```text
1. Apply frozen actions vào state trước.
2. Tạo state mới sau frozen prefix.
3. Gọi CRP_RL trên state mới và retrieval queue mới.
4. Ghép frozen prefix + tail plan.
5. Tính stability cost để phạt tail khác plan cũ.
```

---

# 44. Impact Estimator reference implementation

Tổng impact:

```text
Impact = w_order I_order
       + w_target I_target
       + w_blocking I_blocking
       + w_plan I_plan
       + w_conf I_conf
```

Default weights:

```text
w_order    = 0.25
w_target   = 0.20
w_blocking = 0.25
w_plan     = 0.20
w_conf     = 0.10
```

---

## 44.1. I_order — Kendall-tau top-k

```text
I_order = normalized Kendall-tau distance between old_topK and new_topK
```

Nếu container mới xuất hiện trong top-k, gán rank cũ bằng `K+1`.

Pseudocode:

```text
Function I_order(old_queue, new_queue, K):
    items = union(first K of old_queue, first K of new_queue)
    inversions = 0
    total_pairs = 0

    for each pair (a,b) in items:
        old_rank_a = rank(a, old_queue, default=K+1)
        old_rank_b = rank(b, old_queue, default=K+1)
        new_rank_a = rank(a, new_queue, default=K+1)
        new_rank_b = rank(b, new_queue, default=K+1)

        if sign(old_rank_a - old_rank_b) != sign(new_rank_a - new_rank_b):
            inversions += 1
        total_pairs += 1

    return inversions / max(1, total_pairs)
```

---

## 44.2. I_target

```text
I_target = 1 if old_queue[0] != new_queue[0] else 0
```

---

## 44.3. I_blocking

```text
ΔB = average absolute blocker-count change over top-k containers
I_blocking = 1 - exp(-ΔB / σ_b)
```

Pseudocode:

```text
Function I_blocking(state_old, state_new, old_queue, new_queue, K, sigma_b):
    items = union(first K of old_queue, first K of new_queue)
    delta = 0
    for c in items:
        B_old = blocker_count(state_old, c)
        B_new = blocker_count(state_new, c)
        delta += abs(B_new - B_old)
    delta = delta / max(1, len(items))
    return 1 - exp(-delta / sigma_b)
```

Default:

```text
σ_b = 2
sensitivity: σ_b ∈ {1,2,3}
```

---

## 44.4. I_plan — affected action ratio

```text
I_plan = number of affected planned actions / number of remaining planned actions
```

Một action được xem là affected nếu thỏa ít nhất một điều kiện:

```text
A1. action.container không còn nằm trong retrieval queue mới.
A2. |rank_new(container) - rank_old(container)| > r_shift.
A3. action.dest_stack hiện đã full hoặc invalid sau state update.
A4. action.container nằm trong stack chứa một target mới thuộc top-k.
A5. action đang phục vụ target bị thay đổi khỏi top-k mới.
```

Default:

```text
r_shift = 5
sensitivity: r_shift ∈ {3,5,7}
```

---

## 44.5. I_conf

```text
I_conf = 1 - Conf(I_new)
```

---

# 45. Objective J(P)

Mỗi candidate plan được chấm điểm bằng:

```text
J(P) = C_op(P) + λ D(P, P_old) + μ C_data(P)
```

Default:

```text
λ = 1.0
μ = 0.5
```

---

## 45.1. Operational cost

```text
C_op(P) = α Relocations(P) + β RetrievalDelay(P) + γ InfeasiblePenalty(P)
```

Default (đồng bộ với mục 11.4):

```text
α = 1.0
β = 0.5
γ = 1.0
```

`InfeasiblePenalty(P)` = `M_inf = 10^6` nếu plan invalid, `0` nếu valid (mục 11.3) — `γ` chỉ là hệ số nhân thêm, mặc định giữ nguyên `1.0` để không làm thay đổi độ lớn `M_inf` đã chọn.

---

## 45.2. RetrievalDelay proxy

Không cần mô phỏng thời gian thật.

```text
RetrievalDelay(P) = sum_{c in Urgent} position(c, P)
```

Normalized:

```text
RetrievalDelay_norm(P) = RetrievalDelay(P) / (|Urgent| * (|P| + 1))
```

Nếu không có urgent container:

```text
RetrievalDelay_norm(P) = 0
```

---

## 45.3. Stability cost

```text
D(P, P_old) = sum_i ω(i) * d_i
ω(i) = exp(-ρ i)
```

Default:

```text
ρ = 0.05
```

Action distance `d_i`: dùng đúng công thức cộng dồn ở mục 12.2 (không dùng bản case-table rời rạc), gồm các thành phần `p_c, p_a, p_d, p_o, p_m, p_f` với default:

```text
p_c = 2    # changed container
p_a = 2    # changed action type
p_d = 1    # changed destination
p_o = 1    # changed ordering
p_m = 10   # changed committed action (chưa frozen)
p_f = INF  # changed frozen action (invalid)
```

Insert/delete khi độ dài plan khác nhau: `p_insert = 1.5`, `p_delete = 1.5` (xem mục 12.2).

---

## 45.4. Data confidence cost

Paper 1 dùng bản đơn giản:

```text
C_data(P) = Changes(P, P_old) * (1 - Conf(I_new))
```

Bản nâng cao để future work:

```text
C_data(P) = sum_{a in Changes} importance(a) * (1 - Conf(a))
```

---

# 46. Local Search Repair — reference procedure

## 46.1. Candidate ban đầu

Nhãn candidate thống nhất theo mục 14 và Algorithm mục 18 (không dùng nhãn khác ở bản nháp trước):

```text
C0 Keep old plan                                   (mục 14.1)
C1 Minimal feasibility repair                      (mục 14.2)
C2 Local Search Repair (stochastic hill climbing)  (mục 14.3, chạy trên C1)
C3 Constrained CRP_RL / Full Reoptimization on Tail (mục 14.4, giữ frozen prefix)
```

---

## 46.2. Neighborhood operations

```text
N1 ChangeDestination(a): đổi dest_stack của một relocation action.
N2 SwapActions(a_i, a_j): đổi thứ tự hai action chưa frozen.
N3 InsertUrgentRetrieval(c): đưa urgent container lên sớm hơn nếu feasible.
N4 RemoveObsoleteMove(a): xóa relocation không còn cần thiết.
N5 ReplaceTailWithCRPRL(k): giữ prefix dài k, thay tail bằng CRP_RL.
```

---

## 46.3. Stochastic hill climbing

Default parameters:

```text
T = 100 iterations
M = 50 neighbors per iteration
epsilon = 0.05
```

Pseudocode:

```text
Function local_search_repair(P_start, P_old, state, info_new):
    P_best = P_start
    score_best = J(P_best)

    for iter in 1..T:
        candidates = []
        for m in 1..M:
            op = sample_neighborhood_operation()
            P_candidate = apply(op, P_best)

            if not valid(P_candidate):
                continue

            candidates.append(P_candidate)

        if candidates is empty:
            continue

        P_min = argmin_{P in candidates} J(P)

        if J(P_min) < score_best:
            P_best = P_min
            score_best = J(P_min)
        else if random() < epsilon:
            P_best = P_min
            score_best = J(P_min)

        if runtime_exceeds_timeout:
            break

    return P_best
```

---

# 47. Fallback và timeout

Timeout:

```text
Small instance  : 1 second
Medium instance : 5 seconds
Large instance  : 30 seconds
```

Fallback chain:

```text
Local Search Repair timeout/invalid
        ↓
Minimal Feasibility Repair
        ↓
Keep Old Plan
```

Quy tắc chọn plan:

```text
If P_new invalid:
    keep P_old
If runtime timeout and no valid candidate:
    keep P_old
If J(P_old) - J(P_new) <= τ:
    keep P_old
Else:
    accept P_new
```

Default:

```text
τ = 0.01 * J(P_old)
```

---

# 48. Bảng tham số mặc định

| Tham số | Ý nghĩa | Default | Sensitivity |
|---|---|---:|---|
| K | top-k retrieval queue | 10 | {5,10,20} |
| θ_impact | ngưỡng impact để xét replan | 0.30 | {0.2,0.3,0.4} |
| τ | minimum gain threshold | 1% J(P_old) | {0,1%,5%} |
| λ | stability weight | 1.0 | {0.5,1,2} |
| μ | data confidence weight | 0.5 | {0,0.5,1} |
| α | trọng số relocation count trong C_op | 1.0 | fixed |
| β | trọng số retrieval delay proxy trong C_op | 0.5 | fixed |
| γ | trọng số InvalidPenalty trong C_op | 1.0 | fixed |
| M_inf | hằng số phạt plan invalid | 10^6 | fixed |
| ρ | time decay in stability cost | 0.05 | {0.01,0.05,0.1} |
| σ_b | blocking saturation parameter | 2 | {1,2,3} |
| r_shift | affected rank-shift threshold | 5 | {3,5,7} |
| H_f | freeze horizon | 3 actions | {0,3,5} |
| T | local search iterations | 100 | runtime-based |
| M | neighbors per iteration | 50 | runtime-based |
| ε | exploration prob | 0.05 | {0,0.05,0.1} |
| timeout small | runtime limit | 1s | fixed |
| timeout medium | runtime limit | 5s | fixed |
| timeout large | runtime limit | 30s | fixed |
| τ_age | confidence decay | 10 steps | {5,10,20} |

---

# 49. Benchmark sanity check

Trước khi chạy full experiment, phải kiểm tra benchmark synthetic.

## SC1 — Không quá dễ

Chạy Static Plan. Nếu dynamic events không làm tăng cost so với no-event baseline, benchmark quá dễ.

```text
StaticCost_dynamic > StaticCost_no_event
```

## SC2 — Không quá khó

Nếu mọi method đều fail hoặc timeout quá nhiều, benchmark quá khó.

```text
fallback_rate < 50%
```

## SC3 — Distribution hợp lý

Báo cáo distribution:

```text
number of events per instance
event type frequency
confidence distribution
impact score distribution
```

## SC4 — Impact phân bố đều

Impact không nên toàn gần 0 hoặc toàn gần 1.

```text
mean impact in [0.2, 0.8]
```

---

# 50. Cross-layout protocol

```text
Layout A: tune hyperparameters only.
Layout B: test with same hyperparameters, no retuning.
Layout C: test with same hyperparameters, no retuning.
```

Câu cần đưa vào paper:

> We tune hyperparameters on Layout A only. Layouts B and C are evaluated with the same hyperparameters without further tuning, in order to measure cross-layout generalization.

---

# 51. Runtime reporting

Tất cả runtime experiment phải báo cáo hardware.

Template:

```text
CPU: [model]
RAM: [GB]
GPU: not used / used only for CRP_RL inference
OS: [version]
Python: [version]
```

Khuyến nghị Paper 1:

> SAR-CRP core should be evaluated on CPU-only execution when possible to reflect deployable decision-support constraints.

Metrics:

```text
mean runtime
P95 runtime
timeout rate
fallback rate
runtime by instance size
runtime by layout
```

---

# 52. Ví dụ chạy tay nhỏ

State:

```text
S1 = [C5, C2]
S2 = [C4]
S3 = [C3, C1]
max_tier = 3
old_queue = [C1, C2, C3, C4, C5]
```

Plan cũ:

```text
a1: RELOCATE C1 from S3 to S2
a2: RETRIEVE C3
a3: RELOCATE C2 from S1 to S3
a4: RETRIEVE C5
```

Event:

```text
ORDER_SWAP: C2 becomes urgent
new_queue = [C2, C1, C3, C4, C5]
confidence = 0.8
```

Blocker count:

```text
B_old(C1) = 0 because C1 is top of S3
B_old(C2) = 0 because C2 is top of S1
B_old(C3) = 1 because C1 is above C3
```

Impact:

```text
I_target = 1 because old target C1 changes to C2
I_conf = 0.2
I_order > 0 because top-k order changes
I_plan high because actions serving C1/C3 may conflict with urgent C2
```

Decision:

```text
Impact > θ_impact -> consider replan
Freeze first action if committed
Generate candidates
Score by J(P)
Accept new plan only if gain > τ
```

Possible SAR-CRP output:

```text
Keep frozen: a1 if committed
Repair tail: retrieve C2 earlier if feasible
Changed actions: 2
Expected benefit: lower urgent retrieval delay
Stability cost: moderate
```

---

# 53. Có cần đa cần cẩu hoặc lập lịch không?

Không cần cho Paper 1.

Lý do:

```text
1. CRP là bài toán nền tảng về relocation plan.
2. Thêm multi-crane scheduling sẽ làm scope quá rộng.
3. Novelty của Paper 1 nằm ở stable replanning, không phải resource scheduling.
4. Crane scheduling có thể được xử lý riêng hoặc xem là future work.
```

Giả định đưa vào paper:

> We assume a single relocation resource or that crane scheduling is handled by a separate system. This paper focuses on stable replanning of the relocation sequence, while multi-crane scheduling and resource assignment are left for future work.

Paper 2 có thể mở rộng:

```text
SAR-CRP + multi-crane scheduling
SAR-CRP + execution feedback
SAR-CRP + TOS/TAS integration
SAR-CRP + operator feedback learning
```

---

# 54. Implementation checklist cuối cùng

```text
[ ] Define YardState dataclass/schema
[ ] Define Plan and Action schema
[ ] Define RetrievalInformation schema
[ ] Define Event schema
[ ] Implement find_stack
[ ] Implement blocker_count
[ ] Implement blocker_pressure
[ ] Implement confidence decay
[ ] Implement event stream generator
[ ] Implement CRP_RL wrapper
[ ] Implement I_order
[ ] Implement I_target
[ ] Implement I_blocking
[ ] Implement I_plan
[ ] Implement I_conf
[ ] Implement C_op
[ ] Implement RetrievalDelay proxy
[ ] Implement Stability Cost D
[ ] Implement C_data
[ ] Implement Impact score
[ ] Implement Replanning Trigger
[ ] Implement Freeze Horizon
[ ] Implement candidate C0-C3
[ ] Implement local search N1-N5
[ ] Implement fallback and timeout
[ ] Implement baseline B1-B5
[ ] Implement SAR-CRP B6
[ ] Implement benchmark sanity checks SC1-SC4
[ ] Implement metrics logger
[ ] Run MVP: 1 layout + 3 baselines
[ ] Decision gate before scaling
[ ] Verify base papers (Shin et al. 2026, Zhou & Zhang 2024, Zhang et al. 2025)
    thực sự tồn tại, đúng DOI/venue (mục 3)
[ ] Implement statistical protocol: >= 20 seeds, mean +/- 95% CI,
    Wilcoxon signed-rank test, Holm-Bonferroni correction (mục 23.6)
[ ] Run benchmark sanity checks SC1-SC4 và ghi rõ trong paper rằng
    tham số event generator (mục 39.1.1) chưa hiệu chỉnh từ dữ liệu thật
[ ] Nếu chạy Experiment 5 Option B, ghi rõ đây là exploratory/qualitative,
    không dùng để claim significance với n nhỏ
```

---

# 55. Kết luận cập nhật sau Implementation Appendix

Bản trước đã đủ mạnh về mặt research proposal. Bản cập nhật này bổ sung lớp cần thiết để lập trình viên có thể triển khai:

```text
schema dữ liệu
hàm tính blocker
hàm confidence
hàm tạo event
mapping baseline-paper
nguồn gốc từng module
flow dữ liệu
CRP_RL wrapper
local search cụ thể
tham số mặc định
benchmark sanity
runtime protocol
multi-crane assumption
```

Do đó, tài liệu hiện tại có thể dùng làm:

```text
1. Research proposal cho Q1
2. Implementation specification cho lập trình viên
3. Checklist Phase 0/Phase 1
4. Cơ sở để viết Introduction, Method và Experiment Setup
```
