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
| T5 | Hiệu lực trở về trước (Điều 152), bỏ "có lợi" | ≤50 | 282 event hồi tố, nhưng chỉ trong **19 văn bản tác động**. Sau khi loại 1 đính chính và 187 event của 6 VB hướng dẫn đồng bộ hiệu lực: **95 event trong 13 VB** | **1,9×**, và chưa lọc theo Điều 152 |
| T6 | Hết hiệu lực một phần ở cấp Khoản/Điểm | 100 **+ phần T5 thiếu** | 2.221 Khoản/Điểm hết hiệu lực không có phiên bản kế, trong VB còn hiệu lực | 22× |

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
| A3 | ✅ 20/09 Chốt lược đồ một dòng dữ liệu (trường bắt buộc, cách truy ngược) | `schema_version: 1` trong `build_question_pool.py`: nhóm, nút, danh sách phiên bản kèm khoảng hiệu lực, `gold` theo từng mốc, `event_ids`, `evidence`, `actor_numbers` |

### Gói B — Sinh ứng viên tự động (NMT) · P4.2, P4.3, P4.6

| Bước | Việc | Xong khi |
|---|---|---|
| B1 | ✅ 20/09 `scripts/pipeline/build_question_pool.py`: đọc `versions.jsonl`, lọc `benchmark_eligible` (P4.6), sinh bộ ba (trước, sau, mốc chuyển) cho mọi nút ≥ 2 phiên bản | `data/derived/vilextime_pool.jsonl` 9.331 dòng; chạy hai lần cho sha256 giống hệt; đọc theo luồng nên không tốn RAM |
| B2 | ✅ 20/09 (trừ T5) Phân tầng ứng viên theo T1–T6 bằng tiêu chí đo được | T1 1.435.086 · T2 10.194 · T3 331 · T4 5.390 · T6 2.218. Mỗi nhóm vẫn ≥ quota; T3 mỏng nhất, chỉ 1,7× |
| B3 | Loại ứng viên rác: text quá ngắn, khác biệt chỉ ở dấu câu hoặc khoảng trắng, nút không có tiêu đề | 🟡 21/09: worksheet dựng lại sau audit (18 cột, `transition_on` của T6 đã có, evidence không còn mask `«Q»`). Lỗi **cấu trúc** đã tự động hoá thành `flags` (ADR 0003 §9): T1 có 97/2.500 dòng (3,9%). Tiêu chí **độ dài** vẫn **chờ CMT kiểm tay 150 dòng** — đo được: ngưỡng 80 ký tự cắt 31,2% mà phần lớn là điều khoản ngắn hợp lệ |
| B4 | ✅ 20/09 (phần nhóm) Chống rò rỉ: mỗi nút chỉ vào một nhóm | Kiểm tự động: 0 nút trùng trên 9.331 dòng. Nhóm hiếm được ưu tiên trước (T3 → T6 → T4 → T2 → T1). Phần chia dev/test vẫn ở Gói E |
| B5 | ✅ 21/09 Chốt schema phát hành và sinh nhóm T1 | [ADR 0003](../../decisions/0003-schema-bo-du-lieu-vilextime.md) Accepted. `scripts/pipeline/build_vilextime.py` → `data/derived/vilextime/T1.jsonl`: **2.500 câu** từ 2.500 điều khoản trong 1.890 văn bản, một bản ghi cho mỗi cặp (điều khoản, `as_of`). 2.500/2.500 có `as_of` nằm trong `[valid_from, valid_to)`. `split` còn null (Gói E). Bản ghi mang `document_title` (2.500/2.500) và `lead_in` — câu dẫn của nút cha tại đúng `as_of` (2.308/2.500, 92,3%) — vì 47,1% điều khoản là mục trong danh sách, vô nghĩa nếu tách khỏi câu dẫn. 8 test trong `tests/test_vilextime.py` |

### Gói C — Diễn đạt thành câu hỏi (NMT) · P4.4

| Bước | Việc | Xong khi |
|---|---|---|
| C1 | ✅ 21/09 Prompt sinh câu hỏi từ bộ ba, cấm model tự thêm số liệu hoặc mốc thời gian không có trong bộ ba | `prompts/vilextime/base.md` + một file mỗi nhóm (T1, T2, T3, T4, T6). `question_source` ghi provider/model/temperature/prompt_sha trên từng dòng. Client đa nhà cung cấp `src/legal_crawler/llm.py` (Groq trước), không thêm dependency |
| C2 | ✅ 21/09 Kiểm tra tự động sau sinh: mọi số và mốc trong câu hỏi phải có trong bộ ba gốc | `generate_questions.validate()`, 9 mã lý do (ADR 0003 §10). Chặt hơn plan: thêm `copies_the_answer` (trùng 8-gram với đáp án), `cites_a_provision`, `conversational_filler`. Câu bị loại ghi kèm nguyên văn, không thử lại ngầm. 9 test |
| C3 | ✅ 21/09 (phần cơ chế) Cặp tương phản T2 dùng chung một câu hỏi, chỉ khác mốc t | Sinh theo **lineage**, không theo dòng: một câu cho mọi `as_of`. `lineage_id` giữ vai trò `question_id`. Mốc thời gian không nằm trong câu hỏi, nên một câu phục vụ được mọi mốc. Chờ T2 tồn tại mới chạy thật được |

### Gói D — Đủ quota và kiểm định (CMT chủ trì, NMT phối hợp) · P4.5, P4.7, P4.8

| Bước | Việc | Xong khi |
|---|---|---|
| D1 | Liên hệ và chốt lịch cố vấn luật cho T5, T6 | Có người nhận và lịch làm việc |
| D2 | Cố vấn luật xác nhận 95 ca hồi tố trong 13 VB có thuộc Điều 152 không, và duyệt mẫu T6 | Số T5 chốt được, phần thiếu chuyển sang T6 |
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
| Q3 | T5 định nghĩa hẹp ("có lợi cho đối tượng") hay rộng (mọi hồi tố) | **Cố vấn luật 20/09 bác cách đặt vấn đề:** "có lợi" là ngôn ngữ của Bộ luật Hình sự, không phải phép thử của Điều 152. Không có dấu hiệu câu chữ nào lọc tự động được. Trữ lượng thật sau khi loại đính chính và ca đồng bộ hiệu lực: **95 sự kiện trong 13 văn bản**, cho quota 50. **Chốt 20/09 (CMT): lấy định nghĩa đúng luật, thiếu bao nhiêu bù sang T6** — xem Decisions | D2, D3 |
| Q4 | T3 chỉ có 321 chuỗi trong 100 VB cho 200 câu | Sinh T3 sau khi Gói B của Giai đoạn 3 xong (trữ lượng sẽ tăng). Nếu tới tuần 6 vẫn dưới 300 chuỗi thì hạ T3 xuống 150 và chuyển 50 câu sang T2 | B2, D3 |
| Q5 | Model sinh câu hỏi (P4.4) trước khi P5.1 chốt | Dùng bất kỳ model nào sẵn có, vì nhãn vàng không phụ thuộc model; ghi tên model và tham số vào từng dòng để tái lập | C1 |
| Q6 | Chia dev/test theo câu hay theo văn bản | **Chốt 20/09 (CMT): theo văn bản.** Cùng một Điều sửa nhiều lần sẽ sinh nhiều câu, chia theo câu là rò rỉ | ~~E~~ |

## Decisions đã chốt

- 2026-09-24 (CMT, Follow-Up ADR 0003): **quota đếm theo dòng QA**, tổng 1.150
  dòng. T2 400 dòng = 200 điều khoản, T3 200 dòng ≈ 55–65 chuỗi. Không cắt một
  lineage giữa các mốc.
- 2026-09-24 (CMT, E1 với T2/T4): **không chặn T2/T4 chờ E1.** Sinh và lấy mẫu
  T2/T4 ngay; trước D4 kiểm tay vế "trước sửa đổi" trên mẫu, ghi tỷ lệ sai vào
  Risks. Đổi lại, gold T2/T4 chưa đóng băng cho tới khi có con số này.
- 2026-09-24 (CMT, C1): nhà cung cấp LLM sinh câu hỏi là **Groq** (mặc định của
  `src/legal_crawler/llm.py`). Chỉ gửi text văn bản luật công khai.
  Model `openai/gpt-oss-120b` (Groq không có model mặc định, Q5). Chạy thử
  10 lineage T1: 5/10 qua C2 (loại: 2 `cites_a_provision`, 2
  `copies_the_answer`, 1 `insufficient_context`). Lượt đầu 1/5 vì
  `max_tokens=512` bị phần suy luận ẩn của gpt-oss ăn hết và câu bị cắt ghi
  thành lỗi model; `llm.complete()` nay báo lỗi khi `finish_reason=length`.
- 2026-09-24 (CMT): **sửa prompt sau khi đọc 31 câu đầu.** Cả 31 mở bằng
  "Trong …", 10 kết bằng "…như thế nào?", và T2–T4 không chắc hỏi trúng chỗ
  sửa. Sửa: dạng *tình huống* / *tra cứu* 50/50 gán theo hash lineage (theo
  định nghĩa đầu vào "thời điểm phát sinh hành vi" của đề cương), câu mở đầu
  gán sẵn, khác biệt tính bằng difflib đưa vào prompt, ký hiệu mục "c)" bị C2
  loại. 35 câu sinh bằng prompt cũ đã xoá. Lấy mẫu: `sample_vilextime.py`
  (2× quota, T3 3× vì chỉ qua 9/22, tối đa 2 lineage mỗi văn bản, seed
  20260924); T3 chạm trần 571/600 dòng do chỉ có 121 văn bản.
- 2026-09-24: **`copies_the_answer` thu hẹp lại.** Luật cũ (bất kỳ 8-gram trùng
  đáp án) loại phần lớn câu tình huống, vì mô tả tình huống buộc phải gọi đúng
  tên hành vi. Luật mới chỉ loại khi (a) phần chép phủ ≥ 1/2 một phiên bản, hoặc
  có chép trong câu có/không; (b) với nhiều phiên bản, phần chép chứa từ chỉ một
  phiên bản có — câu hỏi lộ mốc. Luật (b) bắt đúng các câu T2 nhắc "cho vay bằng
  phương tiện điện tử" hay "công nghệ thông tin cơ bản" — chính là phần mới thêm.
  Chấm lại offline bằng `--revalidate`, không gọi lại API. Giới hạn Groq miễn phí
  (1.000 request/ngày, 8.000 token/phút) làm tốc độ ~1 câu/phút.
- 2026-09-24: **Groq miễn phí bị chặn ở 200.000 token/ngày** (~75 câu/ngày với
  gpt-oss-120b). CMT chốt: câu hỏi do phiên Claude Code viết (`--answers`,
  `provider: claude-code`, `model: claude-opus-5-5`), cùng prompt và cùng
  `validate()`. Khoá luận phải ghi rõ, vì nếu một đường cơ sở dùng Claude thì
  nó trả lời câu do chính Claude viết.
- 2026-09-24: **hai lỗi dữ liệu phát hiện khi viết T1.** (1) Cờ mới
  `answer_in_children` (ADR 0003 §9, v1.1.0): text là tiêu đề/câu dẫn, nội dung
  ở nút con — T1 617, T2 588, T4 332, T6 145, T3 38 dòng; `heading_only` chỉ bắt
  trùng khít nên bỏ sót. (2) **`lead_in` rỗng trên toàn bộ 16.513 dòng** từ khi
  `versions.jsonl` chuyển sang JSON gọn (22/09): bộ lọc chuỗi
  `'"provision_id": "'` bỏ qua mọi dòng. Sửa bằng regex; lead_in về 92–99%.
  Mọi câu đã sinh (158) được viết khi prompt thiếu câu dẫn nên đã bỏ; giữ 11
  câu của lineage vốn không có câu dẫn. Mẫu lấy lại sau cờ mới.
- 2026-09-24: **T1 đủ quota.** 255 câu qua C2 trên 342 lineage đã viết (câu
  dẫn có sẵn: ~80% giữ được; loại 64 `insufficient_context` do chính người viết
  đánh — dẫn chiếu trần, cụm danh từ, câu lệnh sửa đổi; 12 `copies_the_answer`).
  `sample_vilextime.py --select` → 250 dòng T1 trong `selected.jsonl`, 244 văn
  bản, 0 cờ, 250/250 `as_of` trong `[valid_from, valid_to)`, mở đầu phân bố đều
  (Trường 38 · Trong 37 · Theo 34 · Pháp 28 · Nếu 28 · Một 26 · Khi 26).
  **Chưa có:** kiểm tay T1 (B3), và `questions.jsonl` vẫn nằm dưới `data/*`
  bị gitignore — câu chữ LLM chưa được commit (xem Risks). *(Đã xử lý 24/09:
  chuyển sang `data/vilextime/questions.jsonl`, whitelist trong `.gitignore`.)*
- 2026-09-24: **T2 đủ quota.** 202 lineage qua C2 trên 247 đã viết → 400 dòng
  (200 cặp) trong `selected.jsonl`, 175 văn bản, 0 cờ, 400/400 `as_of` trong
  khoảng hiệu lực; mọi cặp dùng chung một câu hỏi và có hai đáp án khác nhau.
  **Phát hiện mới về dữ liệu L2:** khoảng 1/20 cặp T2 không phải hai phiên bản
  của cùng một quy định mà là hai quy định khác chủ đề chung số thứ tự (vd.
  "10. Nghiệm thu xe cơ giới cải tạo là…" → "10. Cơ quan nghiệm thu là…";
  "c) Kinh doanh bảo hiểm … 500 tỷ" → "c) Thu hoa hồng tái bảo hiểm…"), tức
  lineage bị nối nhầm khi khoản/điểm được thay thế hoặc đánh số lại. Không câu
  hỏi nào phục vụ được cả hai mốc, nên các cặp này được đánh
  `insufficient_context`; chưa có cờ cấu trúc cho chúng. Cần đo tỷ lệ trên toàn
  T2/T4 và báo lại cho Giai đoạn 3 (L2).
- 2026-09-24: **đo xong, không thêm cờ tự động.** Trên 247 lineage T2 đã đọc
  tay, 18 (7,3%) có hai phiên bản khác chủ đề. Không dấu hiệu máy nào tách được:
  Jaccard từ vựng < 0,2 bắt 8/18 nhưng đã cắt 2/202 cặp tốt, < 0,3 bắt 14/18
  và cắt 15/202 — sửa đổi hợp lệ cũng viết lại gần hết câu; `method`/`locator`
  của event phân bố như nhau ở hai nhóm. 18 ca gồm hai loại: (a) **lỗi L2 thật**,
  câu lệnh không nêu Điều ("Sửa đổi, bổ sung điểm c khoản 2 như sau") và Điều bị
  suy sai — vd. 46/2023/NĐ-CP Điều 35 nhận nội dung về doanh thu tái bảo hiểm;
  (b) **cả Điều bị thay**, khoản mới ghép với khoản cũ theo số thứ tự: vị trí đúng
  về pháp lý nhưng nội dung đổi chủ đề. Cả hai đều không hợp với câu hỏi nội
  dung dùng chung hai mốc. Xử lý: tiếp tục sàng tay khi viết (`insufficient_context`),
  T4 ít bị vì đã lọc similarity ≥ 0,9. Loại (a) cần chuyển Giai đoạn 3 như mẫu
  cho đo precision L2 (P3.13).
- 2026-09-24: **T3 đủ quota.** 71 chuỗi qua C2 trên 72 đã viết (chuỗi dài nên
  ngữ cảnh đủ, gần như không phải bỏ). `select()` chọn tham lam thì kẹt ở
  198/200 vì chuỗi 3–5 dòng; nay chỉ nhận lineage nếu phần quota còn lại vẫn
  lấp đúng được bằng các lineage sau (tổng tập con), giữ thứ tự rank. Kết quả:
  200 dòng, 66 chuỗi (64 × 3 dòng, 2 × 4), 52 văn bản, 0 cờ, mọi mốc có đáp án
  khác nhau. 3 dòng dùng câu của lượt thử Groq `gpt-oss-120b` (lineage không có
  câu dẫn nên không bị bỏ), còn lại `claude-opus-5-5`. Chuỗi quay về nguyên văn
  bản cũ: 1/331 — không đáng xử lý riêng.
- 2026-09-24: **T4 đủ quota.** 77 lineage qua C2 trên 100 đã viết → 150 dòng
  (75 cặp), 63 văn bản, 0 cờ. Phần lớn cặp T4 là **đổi tên cơ quan** (Bộ Tài
  nguyên và Môi trường → Bộ Nông nghiệp và Môi trường, Tổng cục → Ủy ban, Chi cục
  Hải quan → Hải quan cửa khẩu, thị trấn → đặc khu) — đúng loại bẫy T4 nhắm tới.
  **Cờ mới `cosmetic_change`** (ADR 0003 flags v1.2.0): hai phiên bản liền nhau
  chỉ khác chữ hoa/dấu câu — T4 70/1.500, T3 7, T6 3. Đo được chính xác, khác lỗi
  nối nhầm lineage. Cờ bắt được 1 chuỗi T3 đã chọn (v2→v3 chỉ "đất," → "đất;"),
  nay được thay bằng chuỗi kế tiếp; phép kiểm "mỗi mốc có đáp án khác nhau" trước
  đó so nguyên văn nên đã bỏ sót.
- 2026-09-25: **T6 đủ quota** (100 dòng, 50 cặp, 40 văn bản; 76 lineage đã có
  câu, đủ cho 150 dòng nếu T5 thiếu). Tổng 1.100/1.150.
- 2026-09-25 (CMT): **sửa `effFrom` lệch năm ở nguồn** (chi tiết: plan Giai đoạn 3,
  "Sửa effFrom lệch năm"). 31 văn bản được sửa theo câu hiệu lực của chính văn
  bản. Trong bộ đã chọn chỉ 2 cặp T2 đổi mốc (vd. 61/2024/TT-BGTVT: hỏi ở
  2024-02-14/15 — trước khi văn bản được ký — nay 2025-02-14/15); câu hỏi giữ
  nguyên vì không chứa ngày; thứ tự mẫu và 1.100 lineage đã chọn không đổi.
  **T5:** ứng viên hồi tố còn 10 văn bản (240 event): 119/2026/NĐ-CP,
  65/2025/TT-BQP, 97/2026/NĐ-CP, 80/2025/TT-NHNN, 96/2002/QĐ-BTC,
  123/2003/QĐ-BTC; 12/2015/NĐ-CP, 26/2015/TT-BTC, 130/2016/TT-BTC (khả năng là
  hướng dẫn đồng bộ hiệu lực — cố vấn đã nói loại); 2714/QĐ-BTC (đính chính,
  loại). Con số "95 ca trong 13 văn bản" ở trên đã lỗi thời. T5 vẫn chờ cố vấn.
- 2026-09-25 (CMT): **T5 dựng đủ dưới dạng ứng viên, chờ luật sư.** Pool có 249
  điều khoản bị một văn bản hồi tố sửa (HL trước ngày ký); T5 được ưu tiên như
  nhóm hiếm nhất nhưng tách ra **sau** khi các nhóm khác đã lấy mẫu, và
  `sample_vilextime.py` giữ thứ tự xếp hạng đã có (`data/vilextime/sample.jsonl`,
  nay commit) — chỉ 8 điều khoản rời T2/T3/T4, thứ tự còn lại không đổi. Mỗi
  bản ghi T5 có `retroactive` (văn bản tác động, ngày HL, ngày ký, số ngày hồi
  tố, loại); mốc sau luôn nằm trong khoảng hồi tố [HL, ký). Loại đo bằng dữ
  liệu, không đoán từ chữ: `guidance_in_sync` khi văn bản mà tên nó nêu số hiệu
  có cùng ngày HL (26/2015/TT-BTC, 130/2016/TT-BTC), `correction` khi là đính
  chính — hai loại cố vấn đã loại, không vào bản phát hành nhưng vẫn trong bảng
  audit. **Giới hạn:** 12/2015/NĐ-CP hướng dẫn Luật thuế sửa đổi mà tên không
  nêu số hiệu, nên máy không nhận ra là đồng bộ — luật sư xét. 80/2025/TT-NHNN
  thực ra lệch năm (văn bản: 25/01/2026) nhưng nêu hai ngày nên không tự sửa.
  Bản phát hành: T5 44 dòng (22 cặp, trần 2 điều khoản/văn bản), **T6 tự nhận
  phần thiếu** (106 dòng) → **tổng 1.150**. Bảng cho luật sư:
  `data/review/t5_documents.tsv` (10 văn bản, câu hiệu lực trích từ văn bản,
  cột quyết định) và `data/review/t5_items.tsv` (38 điều khoản có câu hỏi, 22
  trong bản phát hành, cột ý kiến). Sinh lại: `scripts/review/t5_worksheet.py`.
  Kèm theo: `build_question_pool.py` nay đọc `versions.jsonl` theo luồng (bị
  kill khi RAM trống ~1 GB).

- 2026-09-20 (CMT, Q3 — chốt sau khi cố vấn luật trả lời): **T5 định nghĩa lại theo
  Điều 152**, là "văn bản quy định hiệu lực trở về trước", bỏ mệnh đề "có lợi cho đối
  tượng áp dụng". Số câu T5 là số ca cố vấn xác nhận được, không đặt trước. **Phần
  thiếu so với 50 chuyển sang T6**, vì T6 dư trữ lượng (2.221) và phục vụ trực tiếp
  giả thuyết H2 — phép thử quyết định với đường cơ sở B7. Tổng vẫn giữ 1.150.
  Không nới định nghĩa T5 để lấp cho đủ số, và không lấy ca đồng bộ hiệu lực vào T5.
  Khóa luận phải ghi rõ: T5 nhỏ vì hồi tố là hiện tượng hiếm và tập trung trong 13
  văn bản của corpus này, đó là một quan sát về thực tiễn lập pháp, không phải thiếu
  sót của bộ dữ liệu. Đề cương sửa mô tả T5 ở P1.2.

- 2026-09-20 (cố vấn luật, Q3): **cách đặt vấn đề của đề cương cho T5 chưa đúng
  khung pháp lý.** "Hiệu lực trở về trước có lợi cho đối tượng áp dụng" dùng chuẩn
  "có lợi" của Bộ luật Hình sự. Điều 152 Luật BHVBQPPL 80/2015/QH13 dùng hai chuẩn
  khác: khoản 1 là điều kiện cho phép ("thật cần thiết để bảo đảm lợi ích chung của
  xã hội, thực hiện các quyền, lợi ích của tổ chức, cá nhân"), khoản 2 là phép loại
  trừ (không được quy định trách nhiệm pháp lý mới hoặc nặng hơn cho hành vi xảy ra
  trước). Khoản 2 nói "không được bất lợi hơn", **không** khẳng định phần còn lại là
  có lợi. Hệ quả: không lọc tự động được, vì "có lợi" phụ thuộc vào đối tượng áp dụng
  nào và phải so nội dung mới với nội dung cũ. Đề cương cần sửa ở P1.2.
- 2026-09-20 (cố vấn luật, Q3): mốc so sánh **ngày hiệu lực ghi trong văn bản với
  ngày ký/thông qua**, không phải ngày đăng Công báo, không phải mốc 45 ngày của Điều
  151. Cách đo hiện tại (`effective_from` với `issued_on`) khớp. Hai lớp nhiễu phải
  loại: **đính chính** (cơ chế khác, ngoài Điều 152) và **văn bản hướng dẫn có hiệu
  lực đồng bộ với văn bản được hướng dẫn** (về số học trông như hồi tố, bản chất là
  đồng bộ hóa).

- 2026-09-20 (Q1, CMT): nhóm hết hiệu lực một phần ở cấp Khoản/Điểm là **T6**;
  bộ dữ liệu có đúng sáu nhóm T1–T6 theo bảng cấu trúc. `graph_justification.md` đã
  sửa T7 → T6 ở ba chỗ, gồm cả giả thuyết H2 — H2 giờ đọc là "khoảng cách giữa
  phương pháp đề xuất và B7 lớn nhất trên T6". Đề cương (`.docx`) vẫn còn nhắc
  T1–T7; sửa ở P1.2.
- 2026-09-20 (Q2, CMT): kiểm định chéo **300 câu**, gồm toàn bộ T5 (50) và T6
  (100) vì hai nhóm này cần chuyên môn luật, cộng mẫu ngẫu nhiên 50 câu mỗi
  nhóm T2, T3, T4. Thay cho câu "toàn bộ T3, T4, T5, T6" của đề cương, vốn cộng
  lại thành 500 câu chứ không phải 300. Cohen κ tính trên đúng 300 câu này.

- 2026-09-25 (CMT, trước D4): **kiểm hai lỗi ngày còn mở trên bản phát hành.**
  (1) 367 quyết định `effective_to` đã duyệt nhưng ingest chưa áp: **0 dòng
  phát hành bị ảnh hưởng** — văn bản bị bãi bỏ mà cổng thiếu `effTo` đã bị loại
  khỏi benchmark từ `build_eligibility.py` (`benchmark_eligible: false`), nên
  khoảng hở này chỉ còn ảnh hưởng KG, không ảnh hưởng ViLexTime. (2) 5 candidate
  `effective_from` chờ người: chỉ 97/2026/NĐ-CP chạm bản phát hành (2 cặp T5).
  Đọc câu hiệu lực: 97/2026/NĐ-CP "có hiệu lực kể từ ngày ký ban hành" (31/03/2026;
  cổng 13/03; candidate 01/07 chỉ là ngoại lệ Điều 25, 26, khoản 4 Điều 31) và
  80/2025/TT-NHNN lệch năm (25/01/2026; cổng 2025) — **cả hai không hồi tố**, 3 cặp
  T5 mang gold sai. Sửa ở nguồn: 2 quyết định `human_reviewed` trong
  `data/review/temporal_candidates.jsonl`, dựng lại `build_store --with-subtrees`
  → `build_versions` (1.565.078 versions, 18.840 event, khớp lần trước; queue
  review đổi đúng 1 dòng của 80/2025) → pool → records → chọn lại. Bản phát hành
  chỉ đổi 6 dòng T5 → 6 dòng T6; không dòng nào khác đổi đáp án/phiên bản/câu
  hỏi. **T5 38, T6 112, tổng 1.150.** Bảng luật sư còn 8 văn bản; cột câu hiệu
  lực nay trích cả câu "kể từ ngày ký" (trước chỉ trích câu có ngày nên che mất
  ngày thật của 97/2026). 4 candidate còn lại (02/2018/TT-BGTVT, 24/2001/TT-BTC,
  113/2011/TT-BTC, 20/2026/TT-BTC) không chạm bản phát hành, vẫn chờ người.
  **Giới hạn:** hiệu lực riêng từng Điều (ngoại lệ trong câu hiệu lực) chưa mô
  hình hóa; event của các Điều đó mang ngày chung của văn bản.

## Risks And Recovery

- **11,1% cặp phiên bản liền nhau có chữ giống hệt nhau** (2.132/19.192, đo
  20/09). Sửa đổi mà không đổi một ký tự nào: hoặc cổng đã cập nhật sẵn lời văn
  vào bản gốc, hoặc khối trích xuất chính là lời văn đang có. `build_question_pool.py`
  loại chúng (1.947 ca T4, 69 ca T3), nhưng câu hỏi nền vẫn mở: **lời văn trong
  `data/provisions/` là bản gốc lúc ban hành hay bản hiện hành?** Nếu là bản hiện
  hành thì vế "trước khi sửa" của mọi cặp T2/T4 sai. Chỉ E1 (đối chiếu 356 văn bản
  hợp nhất) trả lời được, nên E1 cần làm trước khi chốt nhãn vàng T2/T4.
  **Đóng 25/09 (E1):** (1) đối chiếu văn bản hợp nhất chỉ phủ 9/1.150 dòng
  phát hành (51/356 VBHN so được); 7 dòng lệch đều là vế sau và đều do định dạng
  VBHN (chú thích [3], [12], [146], khối chữ ký, mục danh sách gộp vào khoản),
  không lệch nội dung. (2) Vế trước không VBHN nào kiểm được, nên kiểm trực tiếp
  cả 275 cặp T2/T4 phát hành (`scripts/check/check_before_side.py`): 275/275 vế
  trước là phiên bản 1 và có nguyên văn trong văn bản gốc; 272/275 cặp có cụm
  từ mới tìm thấy trong văn bản sửa đổi; 2 cặp có lời văn vế sau xuất hiện trong
  văn bản gốc, xem tay đều là lời của khoản/điểm khác cùng văn bản. **Tỷ lệ sai
  vế trước đo được: 0/275.** Gold T2/T4 chờ D4 để đóng băng.

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

- [ ] Gói A — chốt Q1, Q2 và hướng dẫn gán nhãn (P4.1). A1 xong 20/09; A2 nháp v1.0 xong 25/09 (`docs/vilextime-annotation.md`, chưa thử 20 ví dụ với hai người); còn A3 (lược đồ dòng dữ liệu)
- [ ] Gói B — sinh ứng viên tự động (P4.2, P4.3, P4.6). B1, B2, B4 xong 20/09; B5 (schema + T1) xong 21/09; còn B3 (tiêu chí độ dài, chờ kiểm tay); quota chốt 24/09 là đếm theo dòng QA
- [ ] Gói C — diễn đạt thành câu hỏi (P4.4). C1, C2, C3 (cơ chế) xong 21/09; **chưa chạy thật**: cần API key và quyết định gửi text luật ra dịch vụ ngoài
- [ ] Gói D — đủ quota, cố vấn luật, Cohen κ (P4.5, P4.7, P4.8). Bản phát hành đủ 1.150 dòng (T5 38 chờ luật sư, T6 112). D4: bảng kiểm chéo 300 dòng dựng 25/09 (`scripts/review/crosscheck.py build` → `data/review/crosscheck_A.tsv`, `_B.tsv`: T2 50, T3 50, T4 50, T5 38, T6 112, theo lineage); chờ hai người gán nhãn rồi `crosscheck.py kappa`. Nếu luật sư loại dòng T5, dựng lại bảng trước khi gán
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
