# Execution Plan: Giai đoạn 4 — Bộ dữ liệu ViLexTime (đến M3)

Date: 2026-09-20

## Status

Active. Kế hoạch chi tiết cho mục 5 của [master plan](master-plan.md); trạng
thái từng việc vẫn cập nhật ở master plan.

## Outcome

**M3 (16/11/2026):** 1.150 câu hỏi theo bảng cấu trúc ViLexTime của đề cương, mỗi câu có nhãn
vàng dẫn xuất từ khác biệt văn bản và truy ngược được về nút, phiên bản và
event sinh ra nó. Cohen κ ≥ 0,6 trên tập kiểm chéo. Tập dev/test chia sẵn,
không rò rỉ giữa hai tập.

## Context

Đề cương giao NMT chủ trì quy trình diff-driven, CMT kiểm định chéo và làm việc
với cố vấn luật; cửa sổ chính thức là 27/10–16/11. Kế hoạch này bắt đầu sớm từ
21/09 vì ba tuần không đủ cho một bộ dữ liệu 1.150 câu có kiểm định chéo.

**Điều kiện tiên quyết đã đủ từ 20/09.** P4.2 (so khớp phiên bản) trước đây chờ
P3.15. Nay `data/derived/versions.jsonl` đã có chuỗi phiên bản toàn corpus dựng
offline ([plan Giai đoạn 3](phase-3-kg-l0-l3.md), C2), nên **ViLexTime không
phải chờ M2 hay Neo4j**: nguồn của nhãn vàng là file dẫn xuất, không phải
database.

### Đo trữ lượng ứng viên (20/09/2026)

Trên 17.091 văn bản `benchmark_eligible` (`data/derived/eligibility.jsonl`,
P2.8), dùng `versions.jsonl` và `event_log.jsonl`:

| Nhóm | Định nghĩa trong đề cương | Số câu | Ứng viên đo được | Dư |
|---|---|---:|---:|---:|
| T1 | Tra cứu một phiên bản, không mơ hồ | 250 | ~1,55 triệu nút một phiên bản | thừa |
| T2 | Cặp tương phản cùng câu, khác mốc | 400 (200 cặp) | 15.070 nút ≥ 2 phiên bản, trong 1.442 VB | 75× |
| T3 | Chuỗi sửa đổi nhiều bước A → B → C | 200 | **321 chuỗi ≥ 3 phiên bản, trong 100 VB** (97 chuỗi mọi bước `verified`) | **1,6×** |
| T4 | Bẫy thời gian, phiên bản cũ rất giống | 150 | 5.149 cặp có độ giống ≥ 0,9 (trung vị toàn bộ 0,78) | 34× |
| T5 | Hiệu lực trở về trước có lợi cho đối tượng | 50 | 282 event hồi tố (`effective_on` < `issueDate` của VB tác động): 236 sửa đổi, 45 bãi bỏ | 5,6× **trước** khi lọc "có lợi" |
| T6 | Hết hiệu lực một phần ở cấp Khoản/Điểm | 100 | 2.221 Khoản/Điểm hết hiệu lực không có phiên bản kế, trong VB còn hiệu lực | 22× |

Hai nhóm chặn tiến độ, phần còn lại thừa trữ lượng:

- **T3 chỉ dư 1,6 lần** và tập trung trong 100 văn bản, nên 200 câu sẽ lặp đi
  lặp lại vài văn bản. Trữ lượng này tăng khi Gói B của Giai đoạn 3 chạy xong
  (sửa đổi mới áp được 41,9%, BỔ SUNG 0%).
- **T5 là 282 ứng viên hồi tố, chưa lọc "có lợi cho đối tượng áp dụng"**. Phần
  "có lợi" là phán đoán pháp lý, không đo được bằng dữ liệu; sau khi cố vấn
  luật lọc có thể còn dưới 50.

### Bản đề cương dùng làm chuẩn

Bản `.docx` trong repo là bản 12/09 và **đã cũ**. Bản mới (ảnh chụp 20/09) đánh
số bảng cấu trúc là **Bảng 1** thay vì Bảng 2, và đổi vai trò của T6 từ "Phá vỡ
đường cơ sở B7" thành "Đánh giá hiệu lực ở cấp điều khoản". Sáu nhóm, phần mô
tả và toàn bộ quota (250 · 400 · 200 · 150 · 50 · 100 = 1.150) giữ nguyên. Kế
hoạch này không trích số bảng, để khỏi lệch giữa hai bản. Cần đưa bản mới vào
repo để `data/` và `docs/` cùng trỏ về một nguồn.

### Hai mâu thuẫn trong đề cương (đã chốt 20/09, xem Decisions)

1. **T6/T7** (master plan §12): đề cương viết "gồm bảy nhóm" nhưng bảng cấu
   trúc chỉ có T1–T6; giả thuyết nhắc T1–T7; `docs/graph_justification.md` gọi
   nhóm hết hiệu lực một phần là T7, còn bảng gọi là T6. → Chốt: **T6**,
   đối chiếu lại với bản đề cương mới ngày 20/09.
2. **Phạm vi kiểm định chéo** (phát hiện 20/09): đề cương viết "300 câu (toàn
   bộ T3, T4, T5, T6 và mẫu ngẫu nhiên từ T2)", nhưng T3+T4+T5+T6 = 500 câu,
   đã vượt 300. → Chốt: **300 câu**, "toàn bộ" chỉ áp cho T5 và T6.

Cả hai đều còn phải sửa vào file `.docx` của đề cương, thuộc P1.2.

## Scope

In scope: P4.1–P4.9 của master plan.

Out of scope:

- Chạy đường cơ sở B1–B7 trên bộ dữ liệu (Giai đoạn 5).
- Chỉ số đánh giá TVER, VCR, TCS (P5.4, P5.5) — ViLexTime chỉ cung cấp cặp
  tương phản mà TCS cần.
- Văn bản ngoài `benchmark_eligible`, phụ lục, biểu mẫu, văn bản địa phương.
- Huấn luyện hay tinh chỉnh model sinh câu hỏi.

## Approach

Nguyên tắc: **nhãn vàng sinh từ dữ liệu, LLM chỉ diễn đạt.** Mỗi câu hỏi mang
theo `provision_id`, hai `version_id`, ngày chuyển phiên bản và `event_id`, nên
mọi câu đều truy ngược được về `data/`. Nếu bỏ hết câu chữ tiếng Việt thì nhãn
vàng vẫn dựng lại được bằng script.

```text
versions.jsonl + event_log.jsonl ─► build_question_pool.py ─► data/derived/vilextime_pool.jsonl
  (bộ ba: trước, sau, mốc chuyển)          │  lọc benchmark_eligible, phân tầng T1–T6
                                           ▼
                            phrase_questions.py (LLM chỉ diễn đạt)
                                           ▼
                     data/vilextime/{dev,test}.jsonl  +  hàng đợi kiểm tay
```

### Gói A — Chốt định nghĩa và hướng dẫn gán nhãn (CMT, NMT) · P4.1

Không có gói nào khác bắt đầu đúng trước khi T1–T6 có định nghĩa vận hành
được, vì định nghĩa quyết định cách lọc ứng viên.

| Bước | Việc | Xong khi |
|---|---|---|
| A1 | ✅ 20/09 Chốt Q1 (T6) và Q2 (κ trên 300 câu) | Quyết định ghi ở mục Decisions; `graph_justification.md` đã khớp; còn sửa `.docx` ở P1.2 |
| A2 | Viết hướng dẫn gán nhãn: định nghĩa vận hành từng nhóm, tiêu chí loại câu, ví dụ đúng và sai | `docs/vilextime-annotation.md`; hai người đọc hiểu giống nhau trên 20 ví dụ thử |
| A3 | Chốt lược đồ một dòng dữ liệu (trường bắt buộc, cách truy ngược) | Có ví dụ JSON; script Gói B ghi đúng lược đồ |

### Gói B — Sinh ứng viên tự động (NMT) · P4.2, P4.3, P4.6

| Bước | Việc | Xong khi |
|---|---|---|
| B1 | `scripts/pipeline/build_question_pool.py`: đọc `versions.jsonl`, lọc `benchmark_eligible` (P4.6), sinh bộ ba (trước, sau, mốc chuyển) cho mọi nút ≥ 2 phiên bản | `data/derived/vilextime_pool.jsonl`; chạy hai lần cho file giống hệt |
| B2 | Phân tầng ứng viên theo T1–T6 bằng tiêu chí đo được: T3 theo độ dài chuỗi, T4 theo độ giống văn bản, T5 theo hồi tố, T6 theo nút hết hiệu lực trong VB còn hiệu lực | Số ứng viên mỗi nhóm ≥ quota; bảng trữ lượng in ra được |
| B3 | Loại ứng viên rác: text quá ngắn, khác biệt chỉ ở dấu câu hoặc khoảng trắng, nút không có tiêu đề | Kiểm tay 30 ứng viên mỗi nhóm, ghi tỷ lệ dùng được |
| B4 | Chống rò rỉ: mỗi nút chỉ vào một nhóm và một tập | Kiểm tra tự động, không có `provision_id` xuất hiện ở hai tập |

### Gói C — Diễn đạt thành câu hỏi (NMT) · P4.4

| Bước | Việc | Xong khi |
|---|---|---|
| C1 | Prompt sinh câu hỏi từ bộ ba, cấm model tự thêm số liệu hoặc mốc thời gian không có trong bộ ba | Prompt lưu trong repo; ghi model và tham số vào mỗi dòng |
| C2 | Kiểm tra tự động sau sinh: mọi số và mốc trong câu hỏi phải có trong bộ ba gốc | Câu vi phạm bị loại tự động, có đếm |
| C3 | Cặp tương phản T2 dùng chung một câu hỏi, chỉ khác mốc t | Mỗi cặp có cùng `question_id`, khác `as_of` |

### Gói D — Đủ quota và kiểm định (CMT chủ trì, NMT phối hợp) · P4.5, P4.7, P4.8

| Bước | Việc | Xong khi |
|---|---|---|
| D1 | Liên hệ và chốt lịch cố vấn luật cho T5, T6 | Có người nhận và lịch làm việc |
| D2 | Cố vấn luật lọc T5 ("có lợi cho đối tượng áp dụng") và duyệt mẫu T6 | Đủ 50 câu T5 hoặc có văn bản ghi lý do giảm quota |
| D3 | Sinh đủ quota T1 250 · T2 400 · T3 200 · T4 150 · T5 50 · T6 100 | Tổng 1.150; mỗi câu truy ngược được |
| D4 | Kiểm chéo độc lập theo phạm vi đã chốt ở A1, tính Cohen κ | κ ≥ 0,6; nếu thấp hơn thì viết lại hướng dẫn và kiểm lại |
| D5 | Biên bản kiểm định: ai kiểm, câu nào lệch, xử lý thế nào | Bảng kết quả trong plan |

### Gói E — Chia tập và công bố (NMT) · P4.9

Chia dev/test theo **văn bản**, không theo câu, để một văn bản không nằm ở cả
hai tập (Q6). λ và μ của Giai đoạn 6 chỉ được tinh chỉnh trên dev.

### Lịch 8 tuần

Hai người vẫn đang chạy Giai đoạn 3 tới M2 (26/10), nên bốn tuần đầu chỉ nhận
phần việc script và giấy tờ, không nhận phần cần ngồi kiểm tay hàng trăm câu.

| Tuần | Việc | Kết thúc tuần phải có |
|---|---|---|
| 1 · 21–27/09 | ~~A1~~ (xong 20/09), A2; D1 (liên hệ cố vấn luật ngay, đây là việc có thời gian chờ dài nhất) | Q1, Q2 chốt; nháp hướng dẫn gán nhãn; đã liên hệ cố vấn |
| 2 · 28/09–04/10 | A3; B1 | `vilextime_pool.jsonl` chạy được trên toàn corpus |
| 3 · 05–11/10 | B2, B3 | Bảng trữ lượng thật theo T1–T6; tỷ lệ dùng được trên mẫu 30 |
| 4 · 12–18/10 | B4; C1, C2 | 50 câu mẫu sinh thử, qua kiểm tra tự động |
| 5 · 19–26/10 | *(M2 của Giai đoạn 3 — tuần này ưu tiên cho M2)* C3 | Cặp tương phản T2 chạy được |
| 6 · 27/10–02/11 | D3 (sinh đủ quota); D2 | 1.150 câu sinh xong; T5 đã qua cố vấn |
| 7 · 03–09/11 | D4 (kiểm chéo), D5 | κ tính xong |
| 8 · 10–16/11 | Sửa theo D4; E | **M3**; dev/test chia xong |

Nếu trễ, cắt theo thứ tự: giảm T3 xuống mức trữ lượng cho phép (Q4) → giảm T4
→ **không cắt** T2 (nhóm cốt lõi, TCS phụ thuộc nó) và **không cắt** D4 (κ là
điều kiện của M3).

## Decisions

Cần chốt ở tuần 1. Ý kiến đề xuất chưa phải quyết định.

| # | Câu hỏi | Đề xuất | Chặn |
|---|---|---|---|
| Q1 | T6 hay T7 cho nhóm hết hiệu lực một phần | **Chốt 20/09 (CMT): T6.** Sáu nhóm T1–T6 theo Bảng 2; `graph_justification.md` đã sửa T7 → T6 (3 chỗ, gồm H2). Còn lại: sửa đề cương (P1.2) | ~~A1, A2~~ |
| Q2 | Phạm vi kiểm định chéo: "300 câu" mâu thuẫn "toàn bộ T3–T6" (= 500) | **Chốt 20/09 (CMT): giữ 300 câu** = toàn bộ T5 (50) và T6 (100), cộng mẫu ngẫu nhiên 50 mỗi nhóm T2, T3, T4. Lý do: T5, T6 cần chuyên môn luật nên kiểm toàn bộ; T2–T4 sinh máy móc hơn nên lấy mẫu. Còn lại: sửa đề cương (P1.2) | ~~A1~~, D4 |
| Q3 | T5 định nghĩa hẹp ("có lợi cho đối tượng") hay rộng (mọi hồi tố) | Giữ hẹp theo đề cương, nhưng nếu sau khi cố vấn lọc mà dưới 50 câu thì hạ quota và ghi lý do, không nới định nghĩa để lấp số | D2, D3 |
| Q4 | T3 chỉ có 321 chuỗi trong 100 VB cho 200 câu | Sinh T3 sau khi Gói B của Giai đoạn 3 xong (trữ lượng sẽ tăng). Nếu tới tuần 6 vẫn dưới 300 chuỗi thì hạ T3 xuống 150 và chuyển 50 câu sang T2 | B2, D3 |
| Q5 | Model sinh câu hỏi (P4.4) trước khi P5.1 chốt | Dùng bất kỳ model nào sẵn có, vì nhãn vàng không phụ thuộc model; ghi tên model và tham số vào từng dòng để tái lập | C1 |
| Q6 | Chia dev/test theo câu hay theo văn bản | Theo văn bản: cùng một Điều sửa nhiều lần sẽ sinh nhiều câu, chia theo câu là rò rỉ | E |

## Decisions đã chốt

- 2026-09-20 (Q1, CMT): nhóm hết hiệu lực một phần ở cấp Khoản/Điểm là **T6**;
  bộ dữ liệu có đúng sáu nhóm T1–T6 theo bảng cấu trúc. `graph_justification.md` đã
  sửa T7 → T6 ở ba chỗ, gồm cả giả thuyết H2 — H2 giờ đọc là "khoảng cách giữa
  phương pháp đề xuất và B7 lớn nhất trên T6". Đề cương (`.docx`) vẫn còn nhắc
  T1–T7; sửa ở P1.2.
- 2026-09-20 (Q2, CMT): kiểm định chéo **300 câu**, gồm toàn bộ T5 (50) và T6
  (100) vì hai nhóm này cần chuyên môn luật, cộng mẫu ngẫu nhiên 50 câu mỗi
  nhóm T2, T3, T4. Thay cho câu "toàn bộ T3, T4, T5, T6" của đề cương, vốn cộng
  lại thành 500 câu chứ không phải 300. Cohen κ tính trên đúng 300 câu này.

## Risks And Recovery

- **T3 không đủ trữ lượng** (rủi ro lớn nhất): phụ thuộc Gói B của Giai đoạn 3.
  Giảm thiểu bằng Q4, quyết ở tuần 6 chứ không để tới tuần 8.
- **T5 hụt sau khi cố vấn luật lọc:** 282 ứng viên là cận trên, chưa xét "có
  lợi". Liên hệ cố vấn từ tuần 1 để biết sớm.
- **Lỗi L2 chui vào nhãn vàng:** precision L2 đang là 96,7% trên mẫu kiểm tay,
  nên khoảng 3 trong 100 câu có thể sai gốc. Giảm thiểu: ưu tiên chuỗi mọi bước
  `verified` (97 chuỗi cho T3), và mọi câu vào tập kiểm chéo đều xem lại gốc.
- **LLM bịa số khi diễn đạt:** C2 kiểm tra tự động mọi số và mốc phải có trong
  bộ ba gốc.
- **Rò rỉ dev/test:** Q6 chia theo văn bản; B4 kiểm tra tự động.
- **Phục hồi:** toàn bộ pool là file dẫn xuất từ `data/`; xóa và chạy lại
  script. Chỉ phần câu chữ do LLM sinh và phần người duyệt là không tái tạo
  được, nên hai phần đó phải nằm trong `data/vilextime/` và được commit.

## Progress

- [ ] Gói A — chốt Q1, Q2 và hướng dẫn gán nhãn (P4.1). A1 xong 20/09; còn A2 (hướng dẫn gán nhãn), A3 (lược đồ dòng dữ liệu)
- [ ] Gói B — sinh ứng viên tự động (P4.2, P4.3, P4.6)
- [ ] Gói C — diễn đạt thành câu hỏi (P4.4)
- [ ] Gói D — đủ quota, cố vấn luật, Cohen κ (P4.5, P4.7, P4.8)
- [ ] Gói E — chia dev/test (P4.9)

## Validation

| Tiêu chí M3 | Bằng chứng |
|---|---|
| Đủ 1.150 câu theo quota của đề cương | Đếm theo nhóm từ `data/vilextime/` |
| Nhãn vàng không phụ thuộc LLM | Mỗi dòng có `provision_id`, hai `version_id`, `event_id`; xóa trường câu hỏi vẫn dựng lại được nhãn |
| Cohen κ ≥ 0,6 | Bảng kiểm chéo theo phạm vi Q2, có tên người kiểm |
| Không rò rỉ dev/test | Kiểm tra tự động: giao của tập `document_id` hai bên là rỗng |
| Tái lập được | `build_question_pool.py` chạy hai lần cho file giống hệt (sha256) |

Kiểm tra chung của repository: `python -m pytest -q`.

## Result

(chưa có)
