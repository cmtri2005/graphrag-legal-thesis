# Phản biện độc lập bộ dữ liệu ViLexTime (bản phát hành nháp, 29/09/2026)

Người phản biện: Claude (claude-opus-5-5), phiên độc lập, chỉ đọc. Đối tượng:
`data/derived/vilextime/release.jsonl` (schema 1.1.0, 2.297 dòng), corpus
`data/derived/corpus/`, các file trong `data/vilextime/` và `data/review/`, scorer
`scripts/eval/score_vilextime.py`. Đối chiếu với đề cương đã nộp
(`DeCuongKLTN_23521635_23521643_UIT.docx`) và bản trước trong git (công thức 2–9).

Quy ước: **[Đo]** là số liệu tự đo lại, có lệnh hoặc script ở Phụ lục. **[Suy luận]** là nhận định
chưa kiểm được bằng dữ liệu. Không dòng nào trong 300 id của bộ kiểm chéo κ
(`crosscheck_A.tsv`) được lấy làm mẫu kiểm hay được nhận xét riêng. Mọi id nêu trong báo
cáo đều nằm ngoài các lineage của bộ κ (đã kiểm bằng script). Với T5/T6, vì toàn bộ nằm
trong bộ κ, báo cáo chỉ đưa số gộp.

---

## 1. Kết luận tổng

1. **Đủ để bắt đầu GĐ5 ở mức phát triển** (chạy B7 sớm, chạy thử baseline trên toàn bộ dòng): schema,
   corpus hai lớp, scorer và probe đều chạy và tái hiện được; manifest khớp sha256; gold ở dòng
   ranh giới rất sạch (mẫu tay 0/45; bộ dò tự động chỉ ra 1/850 dòng ngoài κ).
2. **Chưa đủ để báo số chính thức hay trả lời RQ1–RQ3**, vì bốn điều kiện chặn:
   (a) bảng chính (`giua_khoang`) chưa được kiểm hiệu lực tại ngày của dòng anh em: 10/11 lỗi gold xác
   nhận nằm ở đây, và các lỗi đều lệch cùng một chiều (thưởng cho câu trả lời dùng lời văn cũ);
   (b) Accuracy và TCS bị "lách" được: hệ thống in ra mọi phiên bản mà không chọn đạt Accuracy 0,951 và
   TCS 1,000; TVER không tính được cho B1 vì trích dẫn dạng chữ;
   (c) chưa có kiểm định của người: κ 0/300, audit 0/338, T5 chưa có ý kiến luật sư;
   (d) chưa chia dev/test, chưa có datasheet, giấy phép hay manifest cho release.
3. Riêng RQ2/RQ3 còn một rủi ro cấu trúc: gold dẫn xuất từ chính chuỗi phiên bản L2–L3 mà hệ thống
   đề xuất dùng làm lớp B, nên lỗi và bỏ sót của KG không đo được trên bộ này. Cần một tập con có
   gold độc lập.

---

## 2. Đối chiếu với đề cương

| # | Cam kết (nguồn) | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | Bài toán (x, t) → (a, E), E ⊆ {u : valid(u,t)} (CT 1) | **Đạt** | Mỗi dòng có `question`, `as_of`, `answer`/`short_answer`, `version_id` và `accepted_evidence`. `check_release.py` OK: 1.145 đơn vị lớp A và 2.083 phiên bản lớp B đều có trong corpus [Đo] |
| 2 | ~1.100–1.300 câu hỏi (Mục tiêu, ND4) | **Một phần, lệch có chủ đích** | 1.150 dòng ranh giới cộng 1.147 dòng anh em = 2.297 dòng, nhưng chỉ **665 chuỗi câu hỏi khác nhau** (665 lineage). Quota đếm theo dòng QA từ 24/09 (ADR 0003 Follow-Up). Khóa luận phải nói rõ "1.150 câu" nghĩa là 1.150 cặp (câu hỏi, mốc) [Đo] |
| 3 | Bằng chứng cấp Điều/Khoản/Điểm | **Đạt** | Khoản 1.186 · Điểm 1.047 · Điều 64 dòng; 0 dòng có cờ `not_a_provision` [Đo] |
| 4 | Bảng 1: T1 250 · T2 400 (200 cặp) · T3 200 · T4 150 · T5 50 · T6 100 | **Lệch có chủ đích** | T1 250 · T2 400 · T3 200 (65 chuỗi) · T4 150 · **T5 38 · T6 112** (dòng ranh giới). T5 được định nghĩa lại theo Điều 152, bỏ vế "có lợi". Bản UIT đã nộp **vẫn ghi "có lợi cho đối tượng áp dụng"** ở Bảng 1 [Đo] |
| 5 | Vai trò từng nhóm (Bảng 1) | **Một phần** | T4 là bẫy thật (độ giống trung vị 0,957). T3 ranh giới bị probe "ngày gần nhất" giải 100% (mục C). Vai trò H3 của T6 chỉ có 12 lineage `ancestor` [Đo] |
| 6 | Diff-driven: so khớp phiên bản → khác biệt → diễn đạt → kiểm định thủ công (ND4) | **Một phần** | Gold lấy từ `versions.jsonl`; `changed_span` do difflib tính; 0 transition thiếu `event_id`; ngày chuyển = ngày hiệu lực của văn bản tác động ở 100% transition [Đo]. Bước **kiểm định thủ công: chưa có** (mục 7) |
| 7 | "LLM chỉ hỗ trợ diễn đạt câu hỏi" (ND4) | **Lệch** | Cùng một model `claude-opus-5-5` viết 2.273/2.297 câu hỏi, viết lại câu của 56 lineage, viết **1.137/1.137 đáp án ngắn** (thứ mà Accuracy, EM/F1 và TCS chấm), gán 893 nhãn và quyết định loại 20/20 lineage [Đo]. Lời văn gold vẫn do máy trích, nhưng một phần gold của các chỉ số câu trả lời là do model chọn |
| 8 | κ ≥ 0,6 trên 300 câu (đề cương cũ; bản UIT chỉ ghi "đánh giá độ đồng thuận") | **Chưa** | `crosscheck_A/B.tsv` có 0/300 verdict. Thành phần đã đổi so với đề cương cũ (T2/T3/T4 mỗi nhóm 50, toàn bộ T5 38 và T6 112; quyết định Q2) [Đo] |
| 9 | Dev/test không rò rỉ (plan, ADR §7) | **Chưa** | `split` = null ở 2.297/2.297 dòng; scorer đang chấm mọi dòng [Đo] |
| 10 | Khung chỉ số: Recall@k, MRR, TV-Recall@k; Accuracy, EM/F1, LLM-as-judge; TVER, VCR, TCS | **Một phần** | Có đủ, trừ LLM-as-judge (cũ: "hiệu chuẩn trên 100 mẫu"). TV-Recall@k được định nghĩa lại so với CT 9 (mục F) [Đo] |
| 11 | B7 làm sớm; T6 "phá vỡ B7" (cũ) / "hiệu lực cấp điều khoản" (UIT) | **Đạt về dữ liệu** | 42,3% dòng bảng chính là bẫy B7 (mục 5); lớp A và `documents.jsonl` có đủ cho B7 [Đo] |
| 12 | Miền: giao thông, thuế–phí–hải quan, DN–đầu tư, đất đai (ND2) | **Lệch** | Chỉ 212/665 lineage có nhãn miền từ seed; 409 nhãn kế thừa qua quan hệ, và trong mẫu gần như đều sai (mục D). Bộ thực tế đa miền (giáo dục, tòa án, quân đội, lâm nghiệp...) [Đo + Suy luận trên mẫu 25] |
| 13 | Chỉ văn bản QPPL cấp trung ương | **Đạt** | 0 văn bản UBND/HĐND; 11/17 Quyết định là QĐ-TTg, còn lại là QĐ cấp bộ [Đo] |
| 14 | Gold truy vết ngược về nguồn | **Đạt** | `derivation.transitions` có `event_id`, `actor`, `op`; `source_url`; `accepted_evidence` [Đo] |
| 15 | Kiểm chứng snapshot trên 100 truy vấn (L3, đề cương cũ) / V6 kiểm gold ~120 dòng | **Chưa** | Mẫu tay trong báo cáo này (90 dòng) chỉ thay thế được một phần |

---

## 3. Phát hiện

Thang mức: **Chặn** là phải xử lý trước khi báo số chính hoặc đóng băng v1.0; **Nặng** làm lệch
kết luận của một RQ nếu không xử lý hoặc không công bố; **Vừa** là khuyết điểm chất lượng
hoặc tài liệu; **Gợi ý** là cải tiến.

### Chặn

**C1. Bảng chính (`giua_khoang`) chưa được kiểm hiệu lực tại ngày của dòng anh em, và lỗi gold tập trung ở đây.**
- *Mô tả.* Hướng dẫn §5.1 cho dòng anh em dùng chung nhãn với dòng ranh giới vì "cùng câu hỏi, cùng
  phiên bản". Giả định này sai ở một điểm: dòng anh em hỏi ở ngày muộn hơn nhiều, nên mọi lần sửa đổi
  hay bãi bỏ mà chuỗi phiên bản bỏ sót trong khoảng đó đều làm gold sai. Dòng ranh giới (ngày bắt đầu + 1)
  gần như miễn nhiễm với loại lỗi này.
- *Bằng chứng [Đo].* Bộ dò `s04_missed.py` tìm event cùng văn bản, có locator trùng điều khoản đích hoặc nút cha,
  có hiệu lực trong (valid_from, as_of] nhưng không nằm trong chuỗi. Bộ dò gắn cờ 98 dòng; 35 dòng ngoài κ
  được phân xử tay bằng toàn văn nguồn: **11 lỗi xác nhận, 2 có thể sai, 22 báo động giả**
  (danh sách ở mục 4.2). Trong 11 lỗi, **10 là dòng anh em**: 10/848 = 1,18% [0,64; 2,16] dòng giữa khoảng
  ngoài κ, so với 1/850 = 0,12% [0,02; 0,66] dòng ranh giới. Ví dụ:
  `vilextime:T1:provision:2f5ea3c0-2c85-11f1-b760-79130d885196:2025-01-13` hỏi Nghị định 176/2013/NĐ-CP
  ở năm 2025, trong khi khoản 3 Điều 115 Nghị định 117/2020/NĐ-CP ghi "Nghị định số 176/2013/NĐ-CP ...
  hết hiệu lực toàn bộ kể từ ngày 15 tháng 11 năm 2020"; cổng vẫn để "Còn hiệu lực", `effective_to` = null.
- *Nguyên nhân gốc [Đo].* (1) Siêu dữ liệu cấp văn bản thiếu ngày hết hiệu lực: 176/2013/NĐ-CP, 147/2014/TT-BTC; thêm
  62/2014/QH13 (Điều 151 Luật 34/2024/QH15) và 81/CP-1995 (Nghị định 05/2020/NĐ-CP ghi "81-CP") chỉ sai siêu dữ liệu, chưa
  làm sai dòng nào. 298/521 văn bản của release có `effective_to` = null. (2) Event kẹt ở `needs_review`
  (`structure_mismatch`, `missing_resulting_text`, `document_scope`): kho có ~21,9 nghìn event `needs_review`.
  (3) Phép thay cụm từ không được áp: trong 779 event `phrase_not_found` tách được cụm từ cũ, có
  **274 cặp khớp nguyên văn và 332 cặp chỉ khớp khi bỏ phân biệt hoa/thường** trên lời văn đang có hiệu lực
  (ví dụ "Trong giai đoạn chuyển tiếp..." so với lệnh bãi bỏ "trong giai đoạn chuyển tiếp...").
- *Tác động.* Cả RQ1–RQ3 báo trên bảng chính. Lỗi lệch cùng một chiều: gold giữ lời văn cũ, nên thưởng cho
  hệ thống trả lời bằng bản cũ (B7, LLM không truy xuất) và phạt hệ thống trả lời đúng luật.
  Con số 1,18% là **cận dưới**: bộ dò không thấy được các lần sửa đổi mà L2 không trích ra event nào
  (recall L2 62,2% theo báo cáo tiến độ).
- *Đề xuất.* Chạy bộ dò và bộ quét chấm dứt toàn văn bản trên cả 2.297 dòng; lineage κ để sau D4 hoặc giao người thứ ba
  phân xử. Sửa chuỗi (sửa lỗi hoa/thường ở `build_versions.py`, áp các event đã kiểm) hoặc chuyển dòng sang
  `excluded`. Bổ sung vào quy trình audit một bước kiểm hiệu lực tại ngày dòng anh em.

**C2. Accuracy và TCS thưởng cho câu trả lời không chọn phiên bản.**
- *Bằng chứng [Đo].* Trong `s14_scorer.py`, một bài nộp tổng hợp in câu dẫn cùng **mọi phiên bản** của điều
  khoản đạt trên bảng chính: Accuracy 0,951, **TCS 1,000**, Accuracy T2 = T3 = 1,000. Nó chỉ sai ở
  56 dòng không có đáp án. Thêm hai điểm: ở 100/1.685 dòng nhiều phiên bản (5,9%; T3 21/200), đáp án
  ngắn đúng cũng nằm trong một phiên bản sai; và 50/547 cặp T2/T4 có đáp án ngắn vế này chứa trong vế kia.
- *Tác động.* TCS là chỉ số của "nhóm cốt lõi" T2 (RQ1, RQ2). Câu trả lời của LLM hay rào đón kiểu
  "trước ngày X thì A, sau đó thì B", nên nhiễu này là thật chứ không chỉ là lý thuyết [Suy luận].
- *Đề xuất.* Dùng Accuracy tương phản: đúng khi chứa đoạn gold **và không chứa** đoạn chỉ có ở phiên bản khác
  (dựa trên `changed_span` hoặc đáp án ngắn của vế kia). Hoặc bắt buộc một trường đáp án ngắn có giới hạn độ dài.
  Đưa probe "rào đón" vào `--probes` làm kiểm tra hợp lệ; hiệu chuẩn LLM-as-judge như đề cương cũ.

**C3. Chỉ số dựa trên trích dẫn chưa dùng được cho B1, và có thể né bằng cách không trích dẫn.**
- *Bằng chứng [Đo].* Bài nộp có đáp án đúng tuyệt đối nhưng trích dẫn dạng chữ ("Điểm s Khoản 3 Điều 16
  Nghị định 109/2026/NĐ-CP") bị chấm **TVER = 1,000**, vì scorer coi mã không có trong corpus là
  "không còn hiệu lực". Bài nộp không trích dẫn gì thì TVER và VCR = "—" (`cited_rows` = 0).
- *Tác động.* RQ1 hỏi đúng mức lỗi của LLM không truy xuất (B1); với scorer hiện tại, TVER của B1 là 100%
  theo cấu trúc chấm chứ không phải do hành vi của model.
- *Đề xuất.* Viết bộ phân giải trích dẫn chữ → `provision_id` (số hiệu, Điều/Khoản/Điểm). Bộ này phải xử lý
  số hiệu kiểu cũ trùng nhau (40/CP năm 1994 và 1996; 81/CP năm 1993 và 1995) và biến thể "81-CP". Báo tỷ lệ
  phủ trích dẫn cạnh TVER/VCR, thêm biến thể "nghiêm" coi thiếu trích dẫn là lỗi, và ghi rõ trích dẫn chữ
  không mang phiên bản nên VCR không xác định được cho B1.

**C4. Chưa có kiểm định của người; vòng kiểm hiện tại khép kín trong một model.**
- *Bằng chứng [Đo].* κ: A và B đều 0/300. Audit: 338 nhãn bắt buộc, 0 đã audit, cột `auditor` trống. T5: cột
  `LUẬT SƯ:` chưa điền. Mọi dòng ranh giới ngoài κ (850) mang nhãn `dat` của model sau đợt viết lại.
  Hai dòng ranh giới có gold sai mà tôi tìm được đều được model gán `dat`, và một dòng không nằm trong diện
  bắt buộc audit (mục 4.2). Mã `transitional_rule` chưa được dùng lần nào trong 893 nhãn model, dù
  190 dòng ranh giới ngoài κ có dấu hiệu `actor_has_transitional`. **8/300 dòng κ đã có nhãn người
  (`human:excel`) từ bản Excel xem trước D4**, tức không còn mù hoàn toàn với người đã gán bản đó.
- *Tác động.* Lời hứa "kiểm định thủ công" và κ ≥ 0,6 là điều kiện của M3. Nhãn model là cận trên
  (hướng dẫn §6.4 tự thừa nhận).
- *Đề xuất.* Làm D4 trước mọi việc khác; ghi chú 8 dòng tiền-D4 trong biên bản κ. Audit phải có bước đối chiếu
  lịch sử văn bản (không chỉ đọc cột gold). Rà điều khoản chuyển tiếp trên 190 dòng kể trên.

**C5. Chưa có split, datasheet, giấy phép, và release không có trong manifest.**
- *Bằng chứng [Đo].* `split` null; không có LICENSE hay datasheet trong repo; `manifest.json` chỉ phủ corpus
  (sha256 khớp 7/7 file) và ghi commit `0326d3c` (HEAD là `351bd5f`). `release.jsonl`, `questions.jsonl`,
  `short_answers.jsonl` và `labels.tsv` không có sha256 ở đâu cả.
- *Đề xuất.* Xem mục 7.

### Nặng

**N1. Gold và hệ thống đề xuất dùng chung một nguồn (vòng tròn).**
- *[Đo]* Lớp B của corpus chính là đầu ra L2–L3 (`build_corpus.py`); gold `version_id` lấy từ cùng
  `versions.jsonl`. Nhóm T2–T6 chỉ gồm những thay đổi mà L2 đã phát hiện. Người viết câu hỏi đã tự loại 145
  lineage `insufficient_context`, trong đó có 18/247 lineage T2 bị nối nhầm (plan 24/09).
- *[Suy luận]* Hệ thống đề xuất sẽ "đúng theo gold" cả khi KG sai, nên một phần lợi thế ở RQ2/RQ3 là do cấu trúc
  bộ dữ liệu. Tỷ lệ lỗi thật của KG (recall L2 62,2%) không hiện ra trên ViLexTime.
- *Đề xuất.* Tách một tập con có gold độc lập (VBHN, danh mục điều khoản hết hiệu lực trên cổng, người đọc
  văn bản gốc) và báo kết quả hai cột: "gold theo KG" và "gold độc lập". Ghi đây là giới hạn trong khóa luận.

**N2. RQ3: B7 vẫn lấy được bằng chứng đúng qua đơn vị câu lệnh, và TV-Recall@k với k ≥ 5 không phân biệt.**
- *[Đo]* 485/1.147 dòng bảng chính (42,3%) là bẫy B7: văn bản còn hiệu lực nhưng lời văn như công bố không còn đúng
  (429 dòng đã sửa đổi, 56 dòng đã bãi bỏ). Nhưng ở 482/485 dòng, văn bản chứa câu lệnh sửa đổi hoặc bãi bỏ
  (đơn vị `asis:event`, nằm trong `accepted_evidence`) cũng còn hiệu lực theo ngày cấp văn bản. Bài nộp xếp lời
  văn cũ lên đầu, câu lệnh thứ hai và trích dẫn lời văn cũ đạt **TV-Recall@5 = 1,000** (TV-Recall@1 0,577,
  TVER 0,423). 0 dòng thuộc loại `document_repealed` hay `not_yet_in_force`, nên siêu dữ liệu cấp văn bản
  không bao giờ bị thử thách trực tiếp; lại có những văn bản mà siêu dữ liệu sai, khi đó B7 và gold cùng sai (C1).
- *Đề xuất.* Trả lời RQ3 bằng TVER, VCR và TV-Recall@1; chạy B7+ (lọc theo phiên bản, không dùng đồ thị) như
  phép đối chứng chính. Bổ sung dòng `document_repealed` từ các văn bản bị thay thế toàn bộ.

**N3. Ngày ranh giới để lộ thông tin.**
- *[Đo]* Dòng ranh giới: T1 250/250 và T3 200/200 đặt đúng ngày bắt đầu phiên bản + 1 (xác nhận phát hiện của plan,
  và mở rộng sang T1). Probe "ngày gần nhất" đạt 1,000 trên T3 ranh giới, 0,500 trên T2/T4.
  T5 ở chế độ giữa khoảng không thật sự nằm giữa khoảng: 10/38 dòng cách ngày bắt đầu 1 ngày, 19/38 cách một
  lần chuyển dưới 30 ngày (10 lineage có cửa sổ hồi tố 2 ngày). Có 19 dòng ranh giới mà lời văn là câu
  "có hiệu lực ..." (điều khoản thi hành); với loại này đáp án suy ra được từ `as_of`.
- *Đề xuất.* Báo T3 và T5 riêng theo chế độ `as_of`; loại hoặc gắn cờ điều khoản thi hành.

**N4. Độ phủ hiện tượng hẹp hơn Bảng 1 gợi ý.**
- *[Đo]* 100% transition là `amend` (kho event có 5.095 `supplement` và 2.211 `replace`); không dòng nào kiểm bổ sung
  hay thay thế điều khoản. H3 (mất hiệu lực vì nút cha bị bãi bỏ) chỉ có 12 lineage, tức 12 dòng không có
  đáp án mỗi chế độ; với n = 12, khoảng tin cậy rộng khoảng ±25 điểm phần trăm. T5 gồm 19 lineage từ **3 văn bản tác động (10/7/2)**;
  văn bản phủ 7 lineage không ghi ngày hồi tố trong câu hiệu lực.
- *Tác động.* Kết luận về T5 và H3 chỉ ở mức minh họa, không kiểm định được.

**N5. Nhãn miền không dùng được cho phân tích theo miền hay A7.**
- *[Đo]* Nguồn nhãn: seed 212, `quan_he_1/2/3` 409, `khong_ro` 44 lineage. *[Kiểm tay trên 25 lineage mẫu]* 7/7 nhãn seed hợp lý;
  gần như cả 17 nhãn kế thừa đều sai (ví dụ Luật Tổ chức TAND 62/2014/QH13 bị gán `dat_dai, doanh_nghiep_dau_tu`;
  Nghị định 75/2006/NĐ-CP về giáo dục bị gán `giao_thong`).
- *Đề xuất.* Gán lại miền (theo cơ quan ban hành hoặc lĩnh vực trên cổng) hoặc bỏ trường này khỏi phân tích;
  không mô tả bộ dữ liệu là "4 miền".

**N6. Các chỗ lệch với đề cương phải công bố.**
- Số câu hỏi (665 chuỗi, 1.150 dòng ranh giới); vai trò rộng của LLM (C4, dòng 7 của bảng A); định nghĩa T5 và cặp
  số T5 38 / T6 112; thành phần bộ κ; công thức 9 được định nghĩa lại (mục F). Mọi chỗ này đã có quyết định trong
  repo, nhưng đề cương đã nộp vẫn ghi bản cũ.

### Vừa

- **V1.** Release thiếu `retrieved_at`, trục thời gian thứ hai mà ADR 0003 §6 đã chốt [Đo]. Cần trường này vì
  siêu dữ liệu cổng thay đổi và từng sai (C1). `review.guideline_version` trong release vẫn là 1.0, còn nhãn là 1.1.
- **V2.** 6 dòng ranh giới hỏi ở ngày sau ngày chụp corpus 17/09, xa nhất là 01/03/2027 (3 cặp; 3 dòng thiếu dòng anh em) [Đo].
  Mốc tương lai có thể bị sửa trước khi đến ngày.
- **V3.** 22 dòng ranh giới có đáp án ngắn **không** nằm trong lời văn của đơn vị gold mà nằm ở câu dẫn (T1 14, T2 2, T6 6).
  Recall@k không tính đơn vị câu dẫn [Đo]. Có đáp án ngắn "đòi thừa" so với câu hỏi, ví dụ vế sau của
  `vilextime:T2:provision:02077f40-4b62-11f1-8e5a-3794b48af277:2025-09-11` đòi cả đoạn "đồng thời là hồ sơ đăng ký dự thi" dù câu hỏi chỉ hỏi về hồ sơ sau khi nộp.
- **V4.** Khuôn câu hỏi lặp: 5 cụm mở đầu ("Trong lĩnh vực", "Trường hợp", "Theo quy định", "Pháp luật", "Nếu một")
  chiếm 367/665 (55%). Nguyên nhân là câu mở đầu được gán theo hash (ADR §10). Không có câu trùng hay gần trùng (Jaccard ≥ 0,8) [Đo].
- **V5.** Điều khoản chuyển tiếp: trong mẫu, 1/15 lineage nhiều phiên bản có điều khoản chuyển tiếp có thể giữ quy
  định cũ cho vế sau (Nghị định 22/2024/NĐ-CP về lễ phục: "chưa bảo đảm trang phục dự lễ mới ... tiếp tục thực hiện" theo quy định cũ;
  lineage `provision:ec121e20-29f6-11f1-86b5-0d550726534d`) [Kiểm tay; phán đoán pháp lý chưa kiểm được].
- **V6.** Việc bỏ cấp huyện từ 01/07/2025 được xử lý bằng các văn bản chuyển tiếp liên ngành, không phải lệnh sửa từng điều.
  Có 10 dòng hỏi sau mốc này mà câu hỏi hoặc đáp án còn nhắc "cấp huyện" [Đo]. Việc gold có còn đúng ở các dòng đó chưa kiểm được,
  vì văn bản chuyển tiếp có thể nằm ngoài corpus.

### Gợi ý

- **G1.** Thêm vào `--probes` ba probe kiểm tra hợp lệ của scorer: "rào đón", "không trích dẫn", "trích dẫn dạng chữ".
- **G2.** Trong datasheet, báo phễu chọn dòng: 930 lineage được viết câu → 179 bị C2 loại (145 `insufficient_context` do chính người viết
  đánh, 34 `copies_the_answer`) → 20 bị loại sau gán nhãn → 665 lineage. Đây là thiên lệch chọn về phía điều khoản dễ diễn đạt.
- **G3.** Công bố số liệu probe theo nhóm, không chỉ số tổng (bảng ở mục 5).

---

## 4. Kiểm gold theo mẫu

### 4.1 Mẫu phân tầng ngẫu nhiên (seed 20260929, ngoài mọi lineage κ)

Cách lấy: với mỗi nhóm, `random.Random(f"20260929:{g}").sample()` trên danh sách lineage ngoài κ đã sắp xếp;
T1 10 lineage, T2/T3/T4 mỗi nhóm 5 lineage. Kiểm cả dòng ranh giới lẫn dòng anh em.
Với từng lineage, tôi kiểm: (1) mỗi phiên bản gold có nguyên văn trong văn bản gốc hoặc trong văn bản sửa đổi;
(2) ngày chuyển khớp câu hiệu lực của văn bản tác động; (3) các văn bản sửa đổi hoặc bãi bỏ khác của văn bản đích
không chạm tới Điều đích trước `as_of` (đọc toàn văn); (4) câu hỏi, đáp án ngắn, và chức năng nhóm.
T5/T6: **chưa kiểm được theo dòng**, vì 100% lineage T5 (19) và T6 (56) nằm trong bộ κ.

| Nhóm | Chế độ | n | Gold sai | Tỷ lệ | Wilson 95% |
|---|---|---:|---:|---:|---|
| T1 | ranh giới | 10 | 0 | 0% | [0; 27,8] |
| T2 | ranh giới | 10 | 0 | 0% | [0; 27,8] |
| T3 | ranh giới | 15 | 0 | 0% | [0; 20,4] |
| T4 | ranh giới | 10 | 0 | 0% | [0; 27,8] |
| **T1–T4** | **ranh giới** | **45** | **0** | **0%** | **[0; 7,9]** |
| T1 | giữa khoảng | 10 | 0 | 0% | [0; 27,8] |
| T2 | giữa khoảng | 10 | 1 | 10% | [1,8; 40,4] |
| T3 | giữa khoảng | 15 | 0 | 0% | [0; 20,4] |
| T4 | giữa khoảng | 10 | 0 | 0% | [0; 27,8] |
| **T1–T4** | **giữa khoảng** | **45** | **1** | **2,2%** | **[0,4; 11,6]** |
| T5 | cả hai | – | – | – | chưa kiểm được (toàn bộ thuộc κ) |
| T6 | cả hai | – | – | – | chưa kiểm được (toàn bộ thuộc κ) |

Chất lượng câu hỏi trong mẫu (25 lineage): 25/25 trả lời được, không có câu nêu số hiệu hay Điều/Khoản.
Ở 15/15 lineage T2–T4, câu hỏi chạm tới chỗ thay đổi; riêng 155/2020/NĐ-CP chỉ chạm một phần. Lưu ý chất lượng: câu 68/2024/NĐ-CP
(đã được model viết lại) gần như nhắc lại đáp án; câu 136/2024/NĐ-CP hỏi ngày hiệu lực của chính nghị định (N3);
câu 160/2006/NĐ-CP có rủi ro mơ hồ giữa các văn bản. Kiểm cơ học gộp T6 [Đo]: 56/56 dòng bãi bỏ có lệnh bãi bỏ, ngày bãi bỏ bằng
ngày hiệu lực của văn bản tác động, 43/44 locator trực tiếp khớp đường dẫn, không có ngoại lệ "trừ". T5 [Đo]: 19/19 lineage có ngày
hiệu lực trước ngày ký, và mốc sau nằm trong cửa sổ hồi tố.

Id đã kiểm (lineage, mỗi lineage gồm mọi dòng ranh giới và dòng anh em của nó):
- T1: `provision:62e2f75c-eb83-11f0-88fe-cb9e4fcd2761`, `provision:6f64a95a-2d44-11f1-b0d7-d1b0e48cb3c1`,
  `provision:a305de90-df4d-11f0-b252-c3d03b9f6995#k4`, `provision:6c729f40-27ae-11f1-946b-a90cf85afed7`,
  `provision:189cfcfa-e175-11f0-a20b-737ea331ff00#k1#a`, `provision:c1bc2cca-ec3d-11f0-b841-c1c5abf336c8#k3`,
  `provision:b063dc28-e181-11f0-99cf-1f4f4f29cdc1#k2`, `provision:a82e7fd0-2f43-11f1-845f-b378206c5594`,
  `provision:b16882e6-df4b-11f0-9108-bfc3409d5817#k2#e`, `provision:680053d0-2768-11f1-bfbd-efc08bd225d4`
- T2: `provision:02077f40-4b62-11f1-8e5a-3794b48af277`, `provision:58b0b660-2d47-11f1-9aad-bd005c4d14c4`,
  `provision:ec121e20-29f6-11f1-86b5-0d550726534d`, `provision:0540eb90-3188-11f1-aecf-fff3b527cb22`,
  `provision:fd70d0b0-208e-11f1-934f-4d2a85a46aa6`
- T3: `provision:387a3620-2c82-11f1-8d74-79a15475fa71`, `provision:db5da940-2d53-11f1-b8ea-772cb5c62cab`,
  `provision:46a6c1a8-e157-11f0-86e8-7f18fb7d374c#k1`, `provision:fc52f300-eb84-11f0-ab2c-4f4961cea41c`,
  `provision:406c63b0-2c7f-11f1-9540-7d73c403d1d2`
- T4: `provision:3376be48-df46-11f0-9e9d-a330b920f907`, `provision:55ac5bec-df4d-11f0-b470-a3516d537d9d#k1#b`,
  `provision:0b910900-210a-11f1-b748-c1eb115306ea`, `provision:36298684-273f-11f1-b504-7138bb4f333a`,
  `provision:9d44166a-2e81-11f1-8975-ef6a7728f53c`

Lỗi siêu dữ liệu gặp trong mẫu nhưng không làm sai dòng nào: Luật 62/2014/QH13 lẽ ra có `valid_to` = 01/01/2025.

### 4.2 Sàng lọc có chủ đích (cận dưới, ngoài κ)

Bộ dò `s04_missed.py` cùng hai bộ quét chấm dứt toàn văn bản (`s06`, `s09`–`s12`) chạy trên cả 2.297 dòng.
Dòng thuộc lineage κ chỉ được đếm: 63 dòng bị gắn cờ (phần lớn T6), **chưa phân xử** theo đúng ràng buộc. Ngoài κ,
35 dòng được phân xử tay: 11 lỗi xác nhận, 2 có thể sai, 22 báo động giả (precision bộ dò khoảng 31–37%).

| # | Id dòng (ngoài κ) | Chế độ | Lỗi | Căn cứ trong nguồn |
|---|---|---|---|---|
| 1 | `vilextime:T1:provision:2f5ea3c0-2c85-11f1-b760-79130d885196:2025-01-13` | giữa khoảng | Văn bản hết hiệu lực toàn bộ | K3 Đ115 NĐ 117/2020: 176/2013/NĐ-CP hết hiệu lực từ 15/11/2020 |
| 2 | `vilextime:T1:provision:886734ba-eae9-11f0-bfb6-1b525bfe6ee3:2021-08-22` | giữa khoảng | Văn bản bị thay thế | TT 15/2019/TT-BTC "thay thế Thông tư số 147/2014/TT-BTC", HL 01/06/2019 |
| 3 | `vilextime:T1:provision:f0af9e70-1dea-11f1-be02-15fcb9b1bea7:2025-08-30` | giữa khoảng | Khoản bị viết lại | NĐ 63/2025 sửa toàn bộ K1 Đ24 NĐ 78/2021 từ 19/04/2025 |
| 4 | `vilextime:T1:provision:b3bcbe30-21be-11f1-af12-01dc2ecd3981:2025-08-07` | giữa khoảng | Khoản bị viết lại | NĐ 119/2025 sửa K1 Đ29 NĐ 06/2022 từ 01/08/2025 |
| 5 | `vilextime:T1:provision:0ad14760-3261-11f1-803c-c1123978731e:2026-03-22` | giữa khoảng | Điều bị viết lại | NĐ 119/2026 sửa toàn bộ Đ23 NĐ 242/2025 từ 01/01/2026 |
| 6 | `vilextime:T2:provision:0540eb90-3188-11f1-aecf-fff3b527cb22:2026-04-05` | giữa khoảng | Thiếu phiên bản thứ 3 | NĐ 50/2026 sửa Đ41 NĐ 103/2024 từ 31/01/2026 ("cho cả thời gian thuê") |
| 7 | `vilextime:T2:provision:cf4ee8a0-1e2e-11f1-bb92-f7181c000d19:2021-08-15` | **ranh giới (vế trước)** | Vế trước đã bị sửa từ 2019 | TT 37/2018/TT-NHNN sửa K2 Đ12 từ 15/02/2019, lời văn trùng v2; cặp tương phản 15/16-08-2021 không có thật |
| 8 | `vilextime:T2:provision:ec4b5dbe-df43-11f0-980f-9505879c1a66#k1#b:2019-09-05` | giữa khoảng | Điều bị viết lại | TT 10/2018/TT-BXD sửa Đ7 TT 10/2015 từ 16/02/2019 |
| 9 | `vilextime:T3:provision:4720fefe-eb8f-11f0-a786-237da4d41ad5#k4:2024-04-18` | giữa khoảng | Thay cụm từ chưa áp (đáp án ngắn không đổi) | TT 05/2023/TT-BGTVT: "Tổng cục Đường bộ" → "Cục Đường bộ" tại K4 Đ30 |
| 10 | `vilextime:T3:provision:d9ace170-2d52-11f1-a3cd-6fe9242b4f5e:2023-12-22` | giữa khoảng | Bãi bỏ cụm từ chưa áp, lệch hoa/thường (đáp án ngắn không đổi) | NĐ 104/2022 bãi bỏ "trong giai đoạn chuyển tiếp..." tại K1 Đ2 NĐ 123/2015 |
| 11 | `vilextime:T4:provision:9395fe30-eabb-11f0-b95f-553220e945dc#k3#b:2018-05-02` | giữa khoảng | Điều bị thay thế/bãi bỏ | K3 Đ12 TT 32/2017/TT-BCT "thay thế, bãi bỏ ... Điều 10" TT 42/2013 từ 28/12/2017 |
| 12–13 | `vilextime:T2:provision:a1f103aa-ec3a-11f0-a4a7-9fc8904c5daf#k1#c:2011-07-19` và `...:2011-03-30` | ranh giới + giữa khoảng | *Có thể sai*: thay cụm từ lệch hoa/thường, làm hỏng một đoạn của đáp án ngắn | NĐ 88/2009 thay "Giấy chứng nhận quyền sử dụng đất" tại Đ123 NĐ 181/2004 |

---

## 5. Số liệu (mục C, D)

### C1. Vị trí `as_of` [Đo, `s02_temporal.py`]

| Nhóm | Ranh giới: vị trí | Giữa khoảng: khoảng cách tới lần chuyển gần nhất (trung vị) | Giữa khoảng: số dòng < 30 ngày |
|---|---|---:|---:|
| T1 | 250/250 = ngày bắt đầu + 1 | 482 ngày | 1/250 |
| T2 | 200 dòng ngày trước, 200 dòng đúng ngày chuyển | 336 | 2/398 |
| T3 | **200/200 = ngày bắt đầu + 1** | 180 | 2/200 |
| T4 | 75 trước / 75 đúng ngày chuyển | 258 | 3/149 |
| T5 | 19 trước / 19 đúng ngày hồi tố | **31** | **19/38** (10 dòng cách 1 ngày) |
| T6 | 56 ngày trước bãi bỏ / 56 đúng ngày bãi bỏ | 265 | 2/112 |

Khoảng `as_of`: 1981-02-25 → 2027-03-01; 6 dòng sau ngày chụp 17/09/2026. Có 12/1.147 dòng anh em đặt theo luật điểm giữa (cửa sổ ≤ 60 ngày).

### C2. Tỷ lệ bẫy B7 [Đo, `s03_b7.py`]

Mọi văn bản đích đều còn hiệu lực tại `as_of` theo `documents.jsonl` (0 dòng ngoại lệ).

| Nhóm (bảng chính) | Lời văn như công bố = gold | Bẫy: đã sửa đổi | Bẫy: đã bãi bỏ | Tỷ lệ bẫy |
|---|---:|---:|---:|---:|
| T1 | 250 | 0 | 0 | 0% |
| T2 | 200 | 198 | 0 | 49,7% |
| T3 | 65 | 135 | 0 | 67,5% |
| T4 | 75 | 74 | 0 | 49,7% |
| T5 | 17 | 21 | 0 | 55,3% |
| T6 | 55 | 1 | 56 | 50,9% |
| **Tổng** | **662** | **429** | **56** | **42,3%** |

### C3. Độ phân biệt [Đo]

Probe theo nhóm, bảng chính, chỉ số TV-Recall@1 (`score_vilextime.py --probes --out`, tái hiện đúng bảng trong plan):

| Probe | T1 | T2 | T3 | T4 | T5 | T6 | TCS (giữa khoảng / ranh giới) |
|---|---:|---:|---:|---:|---:|---:|---|
| mới nhất | 1,000 | 0,497 | 0,325 | 0,497 | 0,500 | 0,500 | 0,101 / 0,100 |
| đầu tiên | 1,000 | 0,503 | 0,325 | 0,503 | 0,447 | 0,491 | 0,015 / 0,015 |
| ngày gần nhất | 1,000 | 0,749 | 0,645 | 0,745 | 0,789 | 0,500 | 0,530 / 0,100 |
| ngày gần nhất, ranh giới | 1,000 | 0,500 | **1,000** | 0,500 | 0,500 | 0,500 | – |

- T4: độ giống giữa hai phiên bản từ 0,901 đến 0,997, trung vị 0,957.
- Dòng mà phiên bản sai vẫn chứa đáp án ngắn đúng: 100/1.685 (T2 22/400, T3 21/200, T4 6/150, T5 1/38, T6 0/56 mỗi chế độ).
- Cặp T2/T4 có đáp án ngắn lồng nhau: 50/547 (trùng hẳn: 0).
- Đoán được mà không cần truy xuất: tôi chưa chạy LLM, nên chỉ có chỉ số thay thế theo từ vựng. Ở 57/1.094 dòng ranh giới có đáp án (5,2%; T4 17/150),
  ≥ 80% token của đáp án ngắn đã có trong câu hỏi. Kiểm tay cho thấy đây là cận trên: token then chốt thường không có trong câu hỏi.
- Kiểm tra hợp lệ của scorer bằng bài nộp tổng hợp (`s14_scorer.py`, bảng chính):

| Bài nộp tổng hợp | Accuracy | TCS | TV-R@1 | TV-R@5 | TVER | Dòng có trích dẫn |
|---|---:|---:|---:|---:|---:|---:|
| In mọi phiên bản, không chọn | 0,951 | 1,000 | 0 | 0 | — | 0 |
| Đáp án oracle + trích dẫn dạng chữ | 1,000 | 1,000 | 0 | 0 | **1,000** | 1.147 |
| Lời văn cũ trước, câu lệnh sau, trích dẫn lời văn cũ | 0 | 0 | 0,577 | **1,000** | 0,423 | 1.147 |
| Đáp án oracle, không trích dẫn | 1,000 | 1,000 | 0 | 0 | — | 0 |
| Luôn từ chối trả lời | 0,049 | 0 | 0 | 0 | — | 0 |

### D. Phân bố [Đo, `s01_overview.py`, `s13_stats.py`]

| Thuộc tính | Giá trị |
|---|---|
| Dòng / lineage / văn bản | 2.297 / 665 / 521 |
| Cấp nút (mọi dòng) | Khoản 1.186 · Điểm 1.047 · Điều 64 |
| Loại văn bản (lineage) | Nghị định 319 · Thông tư 278 · Luật 36 · Quyết định 17 · TTLT 5 · Bộ luật 4 · Nghị quyết 3 · Pháp lệnh 3 |
| Miền (lineage, đa nhãn) | DN-ĐT 311 · Giao thông 178 · Thuế 148 · Đất đai 47 · Khác 44; nguồn: seed 212, kế thừa 409, không rõ 44 |
| Năm `as_of` (bảng chính) | < 2000: 7 · 2000–09: 46 · 2010–14: 89 · 2015–19: 228 · 2020–24: 422 · 2025–27: 355 |
| Mức tập trung | Tối đa 5 lineage/văn bản (TB 1,28); 26 văn bản có ≥ 3 lineage; 10 văn bản lớn nhất chiếm 6,2% lineage; tối đa 24 dòng/văn bản; 62 văn bản trải trên > 1 nhóm |
| Độ dài (âm tiết, dòng ranh giới) | Câu hỏi: trung vị 33 (p10 26, p90 41) · Lời văn gold: trung vị 56 (p90 141, max 841) · Đáp án ngắn: trung vị 32 (p90 70, max 245), bằng khoảng 0,60 lời văn gold |
| Lặp khuôn | 171 cụm mở đầu 2 âm tiết khác nhau trên 665 câu; 5 cụm đầu chiếm 55%; 0 câu trùng, 0 câu gần trùng |
| Câu hỏi về xử phạt | 60/665 lineage (9,0%); 27 câu hỏi mức phạt tiền; 24 dòng ranh giới có đáp án ngắn là khung phạt |
| Dòng không có đáp án | 112/2.297 (4,9%); bảng chính 56/1.147. **Toàn bộ** là `provision_repealed` |
| Nguồn câu hỏi | claude-opus-5-5 2.075 dòng (không sửa) + 198 (model tự sửa) · human:excel sửa 18 · groq gpt-oss-120b 6 |
| Đáp án ngắn / nhãn / quyết định loại | 1.137/1.137 do model viết · nhãn: model 893, human:excel 210 · loại: 20/20 do model |

---

## 6. Rủi ro với từng RQ và cách giảm

| RQ | Rủi ro chính | Cách giảm |
|---|---|---|
| RQ1: mức lỗi dùng sai phiên bản của LLM/RAG | TVER của B1 = 100% theo cấu trúc chấm (C3); Accuracy và TCS thưởng cho câu rào đón (C2); gold sai lệch về phía lời văn cũ làm **hạ thấp** mức lỗi đo được (C1). Câu hỏi và đáp án ngắn do Claude viết: nếu một baseline dùng model họ Claude, có rủi ro "tự chấm" [Suy luận] | Bộ phân giải trích dẫn, Accuracy tương phản, sửa hoặc loại các dòng gold sai; báo baseline không dùng Claude làm cột chính; ghi rõ trong datasheet |
| RQ2: đồ thị có giảm lỗi so với RAG phẳng và GraphRAG phi thời gian? | Vòng tròn gold–KG (N1); T3 ranh giới bị giải bằng ngày (N3); T3 chỉ có 65 chuỗi | Tập con gold độc lập; báo T3 theo chế độ `as_of`; báo khoảng tin cậy bootstrap theo lineage |
| RQ3: lợi ích từ đồ thị hay chỉ từ lọc thời gian? | B7 lấy được câu lệnh đúng từ lớp A, nên TV-R@k với k ≥ 5 không phân biệt (N2); siêu dữ liệu văn bản sai làm B7 và gold cùng sai; không có dòng `document_repealed`; H3 n = 12 | Kết luận RQ3 bằng TVER, VCR, TV-R@1; chạy B7+ (lọc theo phiên bản, không đồ thị) làm phép đối chứng chính; bổ sung dòng văn bản bị thay thế toàn bộ; gọi H3 là minh họa |

---

## 7. Việc cần làm trước khi đóng băng v1.0 (theo thứ tự ưu tiên)

1. **D4 và audit** (C4): A/B gán 300 dòng κ → κ, AC1, hòa giải; audit 338 nhãn; luật sư chốt T5, gồm cả 7 lineage của văn bản không ghi
   ngày hồi tố. Thêm vào audit bước kiểm hiệu lực tại ngày dòng anh em và kiểm điều khoản chuyển tiếp (190 dòng có dấu hiệu, ngoài κ).
2. **Làm sạch gold ở bảng chính** (C1): sửa lỗi hoa/thường của phép thay cụm từ; áp hoặc loại các event `needs_review` chạm tới dòng
   release; chạy lại bộ dò trên cả 2.297 dòng (lineage κ sau D4); dòng không sửa được thì đưa vào `excluded` kèm cờ.
   Dựng lại theo chuỗi `build_versions` → pool → `build_vilextime` → `--select` → `enrich` → `build_corpus`.
3. **Sửa scorer** (C2, C3): Accuracy và TCS tương phản; bộ phân giải trích dẫn dạng chữ; báo độ phủ trích dẫn; thêm ba probe kiểm
   tra hợp lệ; ghi định nghĩa TV-Recall@k và mẫu số của TVER/VCR vào docstring và khóa luận (mục F).
4. **Chia split** (C5): 20/80 theo văn bản, cùng lineage phải cùng split, T5 vào test, dòng hỏng vào `excluded`. Lưu ý 50/117 văn bản
   chứa lineage κ cũng chứa lineage ngoài κ.
5. **Đóng gói**: thêm `retrieved_at`; manifest cho release (sha256 của `release.jsonl`, `questions.jsonl`, `short_answers.jsonl`,
   `labels.tsv`, `dropped.jsonl`, `sample.jsonl`, commit, ngày chụp); datasheet (động cơ, phễu chọn, vai trò của LLM, lỗi đã biết,
   phân bố, giới hạn: chỉ có `amend`/`repeal`, T5 3 văn bản, H3 12 lineage); giấy phép. [Suy luận, cần xác nhận] Văn bản QPPL
   không thuộc đối tượng bảo hộ quyền tác giả theo Điều 15 Luật SHTT, nhưng phần câu hỏi và đáp án ngắn do model viết cần một giấy phép chọn riêng.
6. **Công bố các chỗ lệch với đề cương** (N6) và gán lại hoặc bỏ nhãn miền (N5) trước khi dùng cho A7.
7. Tùy chọn: dời `as_of` ranh giới của T3 sang ngày trước lần sửa, hoặc chỉ báo riêng; gắn cờ điều khoản thi hành; bổ sung một ít dòng `supplement`/`replace` nếu L3 áp được.

---

## 8. Phụ lục

### Lệnh trong repo (chỉ đọc)

```bash
sha256sum data/derived/corpus/{asis,documents,versions}.jsonl data/derived/versions.jsonl \
  data/derived/provision_events.jsonl data/derived/eligibility.jsonl data/temporal.sqlite   # khớp manifest.json 7/7
python3 scripts/check/check_release.py                     # OK: 2.297 dòng; 1.145 đơn vị A, 2.083 phiên bản B
python3 scripts/eval/score_vilextime.py --probes           # tái hiện bảng probe của plan
python3 scripts/eval/score_vilextime.py --probes --out <scratchpad>/probes_full.json   # số theo nhóm
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_crosscheck.py \
  tests/test_enrich_vilextime.py tests/test_generate_questions.py tests/test_labels.py \
  tests/test_question_pool.py tests/test_score_vilextime.py tests/test_vilextime.py        # 55 passed
```

### Script tạm (ngoài repo)

Thư mục: `/tmp/claude-1000/-home-trica-UIT-Thesis-graphrag-legal-thesis/8b1c39d6-d080-49f1-9cd8-116d3defd79a/scratchpad/`.
Thư mục này là tạm và gắn với phiên làm việc; nếu cần giữ lại để tái hiện, hãy chép script sang nơi khác.

| Script | Việc |
|---|---|
| `common.py` | Nạp release; tập loại trừ κ = 300 id + mọi dòng cùng lineage và dòng anh em (599 dòng) |
| `src.py`, `ctx.py` | Tra `data/raw/<id>.json` (siêu dữ liệu cổng, toàn văn đã bỏ thẻ); in văn bản ngay sau câu lệnh sửa đổi |
| `s01_overview.py` | Đếm theo nhóm, chế độ, nguồn câu hỏi; trạng thái κ (chỉ đếm verdict) |
| `s02_temporal.py` | Vị trí `as_of`, dòng sau ngày chụp |
| `s03_b7.py` | Tỷ lệ bẫy B7; hiệu lực của văn bản chứa câu lệnh |
| `s04_missed.py` | Bộ dò event chưa áp (mục 4.2) |
| `s05`, `s06`, `s09`–`s12` | Quét chấm dứt toàn văn bản qua cạnh `genealogy` và toàn văn 23.139 văn bản |
| `s07_phrase.py` | Đo event `phrase_not_found` có thể áp được (khớp nguyên văn hoặc chỉ khác hoa/thường) |
| `s08_sample.py`, `dossier.py` | Lấy mẫu (seed 20260929) và dựng hồ sơ đối chiếu nguồn cho từng lineage |
| `s13_stats.py` | Số liệu mục C3 và D |
| `s14_scorer.py` | Bài nộp tổng hợp cho scorer (ca biên) |
| `s15_t5t6.py` | Kiểm cơ học gộp T5/T6 (chỉ in số đếm) |

Trước khi làm, tôi lưu sha256 và mtime của mọi file trong `data/derived/vilextime`, `data/vilextime`, `data/review`, cùng manifest và
`documents.jsonl` của corpus, rồi so lại sau khi làm (mục cuối).

### Mục F: định nghĩa trong scorer so với công thức 6–9

- **CT 9 (TV-Recall@k)** viết u ∈ E\*_q ∧ valid(u, t_q). Vì mọi đơn vị gold đều có hiệu lực tại t_q theo định nghĩa, công thức như viết
  **trùng với Recall@k**. Scorer định nghĩa lại: trúng khi lấy đúng `version_id` hoặc một đơn vị trong `accepted_evidence`. Định nghĩa này hợp lý,
  nhưng khóa luận phải ghi đó là định nghĩa chính thức. Recall@k thường tính trúng ở mọi phiên bản của điều khoản. |E\*| = 1: đơn vị
  câu dẫn không được tính (V3).
- **CT 6, 7 (TVER, VCR)**: công thức lấy trung bình trên Q; scorer chỉ tính trên dòng có trích dẫn, khớp câu "được đánh giá trên các câu
  trả lời có trích dẫn" của đề cương cũ. Hệ quả: không trích dẫn thì né được chỉ số (C3). VCR = 0 nếu trong các trích dẫn có
  phiên bản đúng, kể cả khi đồng thời trích một phiên bản sai. Mã không có trong corpus bị coi là hết hiệu lực.
- **CT 8 (TCS)**: tính trên các cặp T2 cùng chế độ (200 cặp ranh giới, 199 cặp giữa khoảng); T4 không được tính dù cũng là cặp tương phản.
  "â = a\*" được hiện thực bằng phép chứa đoạn, nên bị lách được (C2).
- **EM**: so với đáp án ngắn đã nối các đoạn. Oracle đạt EM 0,000 và F1 0,589, nên EM gần như vô nghĩa với hệ thống sinh câu dài;
  cần báo F1, hoặc một biến thể trích đoạn.
- **Dòng không có đáp án**: đúng khi `answerable: false`; truy xuất trúng khi lấy được lệnh bãi bỏ. Hệ thống luôn từ chối đạt 0,049.

### Chưa kiểm được và lý do

- Gold theo từng dòng của T5 và T6: 100% lineage thuộc bộ κ đang gán mù; chỉ có kiểm cơ học gộp.
- 63 dòng thuộc lineage κ bị bộ dò gắn cờ: chưa phân xử, theo đúng ràng buộc.
- Những lần sửa đổi mà L2 không trích ra event nào (bộ dò không nhìn thấy): tỷ lệ lỗi ở mục 4.2 là cận dưới.
- Phán đoán pháp lý (Điều 152, điều khoản chuyển tiếp, văn bản chuyển tiếp sau khi bỏ cấp huyện): cần luật sư; văn bản liên quan có thể nằm ngoài corpus.
- Đối chiếu với văn bản hợp nhất (VBHN) ngoài phần E1 mà plan đã làm.
- Khả năng đoán đáp án không cần truy xuất bằng LLM: tôi không chạy model nào, chỉ có chỉ số thay thế theo từ vựng.
- Độ đúng của nhãn miền trên toàn bộ: chỉ kiểm trên 25 lineage mẫu.

### Kiểm tính chỉ đọc

So sánh sha256 và mtime trước/sau của 27 file dữ liệu: không đổi. `git status` chỉ khác trạng thái ban đầu ở file mới
`docs/reports/JUDGE_DATASET.md`. Không ghi vào `labels.tsv` hay `crosscheck_*.tsv`, không tạo `__pycache__` hay `.pytest_cache`
trong repo (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`).
