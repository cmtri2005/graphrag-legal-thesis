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

**Cập nhật 28/09 (CMT duyệt): ViLexTime v1.0 sẵn sàng thực nghiệm, làm nhanh
nhất có thể.** Đề cương đã nộp (`DeCuongKLTN_23521635_23521643_UIT.docx`) đặt GĐ4
ở 24/10–13/11, GĐ5 ở 14/11–04/12 và kết thúc khóa luận 26/12/2026; mốc đó chỉ là
hình thức, việc chạy theo thứ tự phụ thuộc. Master plan còn theo lịch đề cương cũ
(đến 01/02/2027).

### Kế hoạch v1.0 (duyệt 28/09)

Quyết định: (1) **`as_of` ghép cặp**: giữ nguyên dòng sát ranh giới
(`as_of_strategy: ranh_gioi`), thêm dòng anh em giữa khoảng hiệu lực
(`giua_khoang`, `twin_of`) cùng câu hỏi, cùng phiên bản đáp án; bảng kết quả chính
dùng `giua_khoang`, `ranh_gioi` là bài kiểm tra ngày chuyển phiên bản. Căn cứ đo 28/09:
biết mỗi `as_of` là thu 17.091 văn bản đủ điều kiện về trung vị 7 (T1/T3) hoặc 4
(vế sau T2/T4) văn bản có ngày hiệu lực khớp. (2) **Schema 1.1.0** (MINOR, ADR 0003):
`short_answer`, `changed_span`, `evidence_set`, `accepted_evidence`, `op` trên từng
transition, `domain`/`domain_source`, `legal_markers`, `as_of_strategy`, `twin_of`.
(3) **Corpus hai lớp**: lớp "như công bố" cho baseline thông thường và B7, lớp "theo
phiên bản" cho hệ thống đề xuất và B7+; bằng chứng đúng ở lớp nào cũng được chấm
qua `accepted_evidence`. (4) A = CMT, B = NMT. (5) Dev/test 20/80 theo văn bản,
toàn bộ T5 vào test.

| Gói | Việc | Xong khi |
|---|---|---|
| V1 | `scripts/pipeline/enrich_vilextime.py`: `selected.jsonl` → `release.jsonl` (dòng anh em + trường 1.1) | Test; gold dòng anh em tính lại từ chuỗi phiên bản và trùng dòng gốc |
| V2 | `scripts/pipeline/build_corpus.py`: hai lớp + manifest (snapshot id, sha256) | Số đếm, sha256 ghi vào manifest |
| V3 | Nhãn: model gán T2/T3/T4 ngoài bộ κ + `short_answer`; nhóm audit (§6 hướng dẫn) | Mọi nhãn model bắt buộc audit đã audit |
| V4 | D4: dựng lại bộ κ từ `release.jsonl` (chỉ dòng `ranh_gioi`, thêm cột ngữ cảnh), A/B gán mù, κ + AC1 + % đồng thuận | Kết quả `crosscheck.py kappa`, biên bản hòa giải |
| V5 | T5: bản đề xuất cho luật sư → quyết định Điều 152 | Cột `LUẬT SƯ:` điền đủ |
| V6 | Kiểm gold độc lập ~120 dòng (gộp E2 của GĐ3), dư mẫu `giua_khoang` | Tỷ lệ gold sai + Wilson CI; dòng hỏng → `excluded` |
| V7 ✅ | Scorer chính thức + probe (oracle, mới nhất, đầu tiên, ngày gần nhất) | Unit test; kết quả probe trên hai chế độ `as_of` |
| V8 | Sửa/thay dòng không đạt, chia tập, datasheet, đóng băng v1.0 | Tag, sha256, datasheet |

Tiến độ V1–V2 (28/09): `release.jsonl` 2.297 dòng = 1.150 ranh giới + 1.147
giữa khoảng (3 khoảng mở sau ngày chụp corpus không có dòng anh em). 363 dòng có
đơn vị được dẫn chiếu trong `evidence_set` (329 dẫn chiếu phân giải được, 37
`locator_not_found`). `accepted_evidence` phủ 2.297/2.297: cây điều khoản của văn
bản sửa đổi làm rơi lời văn trong ngoặc kép ở khoảng 1/3 số lần sửa, nên lớp A có
riêng một đơn vị cho mỗi câu lệnh (câu lệnh + lời văn mới). Miền: 721 dòng seed,
1.436 kế thừa qua quan hệ, 140 `khac`. Corpus: 17.307 văn bản; lớp A 1.455.372 điều
khoản + 48.328 câu lệnh; lớp B 1.473.900 phiên bản. `check_release.py` OK. Bộ κ
dựng lại từ `release.jsonl` (đúng 300 dòng cũ, thêm cột câu dẫn/`changed_span`/
khoảng hiệu lực); `crosscheck.py kappa` báo thêm % đồng thuận, AC1, κ theo lineage.
**Phát hiện:** T6 chỉ chứa ca bãi bỏ trực tiếp (điều kiện chọn nhóm đòi
`ended_by_event_id` trên chính nút), nên H3 (mất hiệu lực do nút cha bị bãi bỏ)
chưa có dòng nào để kiểm. **Chốt 28/09 (CMT): tách 12 cặp (24 dòng) vào T6**,
tổng giữ 1.150. `build_question_pool.py` thêm 300 ứng viên `repeal_mode: ancestor`
(trên 10.249 điều khoản đủ điều kiện trong 487 văn bản; mẫu 300/300 truy được về
nút cha bị bãi bỏ cùng ngày — 237 Điều, 32 Khoản, 22 Chương, 9 Mục), không đụng
dòng nào của pool cũ; `sample_vilextime.py` xếp hạng phần này riêng (thứ hạng cũ giữ
nguyên, 24 lineage nối thêm), chọn 24 dòng ancestor + 88 dòng direct. 24 câu hỏi
viết bằng phiên Claude Code, 21 qua C2. Bộ κ đổi đúng 24 dòng T6 (chưa ai gán).

Tiến độ V3 (28/09): model (`claude-opus-5-5`) đã gán mọi dòng ranh giới ngoài bộ κ
của T1–T4 (`data/review/labels.tsv`): T1 228/22, T2 311/39, T3 106/44, T4 74/26
(đạt/không đạt); 319 nhãn bắt buộc audit, phiếu ở `data/review/audit_T{1..4}.xlsx`,
chưa audit dòng nào. `short_answer` phủ 2.185/2.185 dòng có đáp án (1.094 phiên bản,
`data/vilextime/short_answers.jsonl`, mỗi dòng ghi `by`); dòng κ chỉ có đáp án ngắn, không
có nhãn model. Quy tắc T3 áp dụng (§3 hướng dẫn: câu hỏi phải tách được mọi mốc):
lineage mà câu hỏi chỉ có dưới 3 đáp án khác nhau thì mọi dòng `group_mismatch` (ghi chú
cặp mốc có thể chuyển sang T2); lineage đạt thì dòng trùng đáp án với mốc liền trước là
`group_mismatch`. Đồng thuận model–người trên 159 dòng cùng gán: 86,8%.
**Lỗi pipeline tìm ra khi gán T3, đã sửa (4c5a8b7):** phép "thay thế cụm từ" được giải
trên lời văn như công bố, nên nếu điều khoản đã bị sửa trước đó thì lần thay cụm từ âm
thầm quay về lời văn cũ (ví dụ 191/2015/TT-BTC Đ12.2.b năm 2025 mất nội dung sửa năm
2019). `extract_provision_events.py` giờ ghi `phrase_edits`, `build_versions.py` giải lại
trên phiên bản đang có hiệu lực. 59/1.595.391 phiên bản đổi lời văn; pool đổi 56 dòng T3,
release đổi 13 đáp án T3 (6 trong bộ κ, dựng lại: giữ nguyên 300 id và thứ tự). **Lỗi văn
bản nguồn (không sửa được ở pipeline):** 2 đáp án bị cắt ngay trong HTML gốc ở chữ "do"
(59/2011 Đ36.2.b bản 2, 13/2019/TT-BGTVT Đ87.2 bản 1), đã đánh `gold_wrong`/`meta other`.

Tiến độ V8, phần sửa/thay dòng không đạt (28/09): cả 138 nhãn `khong_dat` (131 của
model trên 73 lineage, 7 của người) đã xử lý, không còn dòng `khong_dat` nào của model
trong release. **Viết lại câu hỏi** 56 lineage (99 dòng): câu mới qua cùng `validate()`, ghi đè
`question` trong `questions.jsonl`, câu model gốc giữ ở `model_question`,
`edited_by: claude-opus-5-5`; nhãn model của mọi dòng lineage đó chấm lại tại chỗ
(ghi chú giữ câu cũ và nhãn cũ), luôn bắt buộc audit. Câu hỏi phạt tiền hỏi "khung
phạt tiền của hành vi" thay vì "mức phạt với tổ chức". Sửa một nhãn sai: 63/2019 Đ51
là lĩnh vực dự trữ quốc gia, câu cũ nói tài sản công mà đã được gán `dat`.
**Loại** 19 lineage không sửa được (không phải quy phạm, văn bản nguồn bị cắt, chỉ 2
đáp án khác nhau ở T3, câu hỏi không thể tách khỏi điểm/khoản anh em) vào
`data/vilextime/dropped.jsonl` (lý do, ghi chú, người loại); `sample_vilextime.py
--select` coi lineage bị loại như câu hỏi không qua, nên lineage xếp hạng kế tiếp vào
thay. Thêm một lineage T3 (hạng 56) loại trước khi sinh câu hỏi vì chỉ có 2 đáp án.
**Thay thế** 43 dòng: 7 lineage dự trữ đã có câu hỏi, 12 câu mới viết bằng phiên
Claude Code theo thứ hạng (T2 hạng 242–246, T3 hạng 70–73, 85, 143 — subset-sum bỏ
qua các lineage 3 dòng ở giữa vì T3 cần đúng 20 dòng); nhãn và đáp án ngắn đủ.
Kiểm: 1.008 dòng không đụng tới giữ nguyên từng trường, 300 id κ không đổi, hạn ngạch
đủ, `check_release.py` OK. `audit-sheet` đọc cả dòng đã loại (từ file nhóm) với cột
`fix` ghi lý do loại, để người audit xác nhận việc loại. 7 nhãn `khong_dat` của người
(human:excel) vẫn giữ: 4 dòng hợp lệ theo quy tắc câu dẫn v1.1 (19/2014, 109/2026
Đ16, 17/2018, 15/2003), 3 dòng câu hỏi đã viết lại. Audit bắt buộc: 338 nhãn.

V7 (28/09): `scripts/eval/score_vilextime.py`, scorer chính thức và 4 probe. Định nghĩa
theo khung đánh giá của đề cương và công thức 6–9 (TVER, VCR, TCS, TV-Recall@k; ảnh
công thức ở bản đề cương trước, `DeCuongKLTN_23521635_23521643.docx` trong git). **Chốt
28/09 (CMT)** ba chỗ công thức để ngỏ: (1) Accuracy và "â = a*" của TCS: câu trả lời
(chuẩn hóa) chứa mọi đoạn của `short_answer`; EM/F1 tính riêng trên âm tiết; (2) E* chỉ
là đơn vị gold (|E*| = 1): Recall@k trúng khi lấy đúng điều khoản, phiên bản nào cũng
được, hoặc `accepted_evidence`; TV-Recall@k chỉ khi đúng phiên bản có hiệu lực tại `as_of`
hoặc `accepted_evidence`; (3) dòng không có đáp án đúng khi bài nộp trả `answerable:
false`, truy xuất trúng khi lấy được lệnh bãi bỏ, không tính EM/F1. TVER, VCR tính trên
dòng có trích dẫn (đề cương); mã đơn vị không có trong corpus tính là không còn hiệu lực.
Bài nộp là JSONL `{id, answer, answerable, citations, retrieved}` với mã đơn vị của
corpus hai lớp; mã lớp A quy về phiên bản (`asis:provision` = bản 1, `asis:event` = bản
lệnh đó viết ra, lệnh bãi bỏ = hiệu lực từ ngày bãi bỏ). 7 unit test trên ví dụ tay.
**Ngày 29/09, CMT thay quyết định (1) và cách chấm trích dẫn**, xem mục "Xử lý phản biện 29/09".

Kết quả probe (hệ thống được cho sẵn điều khoản gold, chỉ chọn phiên bản; toàn release):

| Probe | as_of | TV-Recall@1 | Accuracy | TVER = VCR | TCS |
|---|---|---|---|---|---|
| oracle | cả hai | 1,000 | 1,000 | 0,000 | 1,000 |
| mới nhất | giữa khoảng / ranh giới | 0,577 / 0,578 | 0,606 / 0,607 | 0,423 / 0,422 | 0,101 / 0,100 |
| đầu tiên | giữa khoảng / ranh giới | 0,577 / 0,576 | 0,586 / 0,584 | 0,423 / 0,424 | 0,015 / 0,015 |
| ngày gần nhất | giữa khoảng / ranh giới | 0,762 / 0,696 | 0,774 / 0,717 | 0,238 / 0,304 | 0,530 / 0,100 |

Oracle đạt trần ở mọi chỉ số (kể cả dòng bị bãi bỏ: từ chối và trích lệnh bãi bỏ), nên
scorer nhất quán từ đầu tới cuối. Accuracy cao hơn TV-Recall@1 ở probe sai phiên bản
(0,606 so với 0,577): có dòng mà phiên bản sai vẫn chứa đáp án ngắn, nên Accuracy một
mình đánh giá cao hệ thống. Bẫy ngày gần nhất chỉ tác dụng ở chế độ ranh giới (TCS 0,53
→ 0,10). **Phát hiện:** 200/200 dòng ranh giới T3 nằm đúng 1 ngày sau ngày bắt đầu phiên
bản của nó, không dòng nào ở ngày trước lần sửa như T2/T4/T5, nên probe ngày gần nhất
đạt 1,000 trên T3 ranh giới; muốn T3 ranh giới thử bẫy này thì phải đổi cách đặt `as_of`
(chưa đổi, chờ quyết định).

### Xử lý phản biện 29/09 (`docs/reports/JUDGE_DATASET.md`)

Phản biện độc lập kết luận release đủ để phát triển GĐ5 nhưng chưa đủ để báo số chính thức. Có năm điểm chặn:

| # | Điểm chặn |
|---|---|
| C1 | Gold sai ở bảng `giua_khoang`, vì chuỗi phiên bản bỏ sót sửa đổi hoặc bãi bỏ |
| C2 | Accuracy và TCS bị lách bằng câu trả lời rào đón |
| C3 | TVER của B1 bằng 100% do cách chấm, không do hành vi của model |
| C4 | Chưa có người kiểm |
| C5 | Chưa có split, datasheet, giấy phép, manifest |

**Chốt 29/09 (CMT):**

1. **Chỉ số chính đổi**, thay quyết định (1) của V7:
   - Accuracy và TCS dùng bản *tương phản*: câu trả lời phải chứa mọi đoạn gold, và không được chứa đoạn nào
     chỉ đáp án ngắn của phiên bản khác cùng lineage có. Bản 28/09 giữ lại, đặt tên `accuracy_lenient` và
     `tcs_lenient`.
   - Trích dẫn dạng chữ được quy về điều khoản.
   - Trích dẫn không phân giải được thì không tính vào TVER chính, nhưng tính là lỗi ở `tver_strict`.
   - Báo thêm độ phủ trích dẫn.
2. **Dòng mà sửa chuỗi không cứu được:**
   - chỉ dòng anh em sai: dời `as_of` về trước event bị bỏ sót (quyết định ghi trong
     `data/review/validity_queue.tsv`);
   - dòng ranh giới sai: loại cả lineage qua `dropped.jsonl`, lấy lineage kế tiếp theo thứ hạng.
3. **Giấy phép CC BY 4.0** cho câu hỏi, đáp án ngắn và nhãn.
4. **Làm thêm:**
   - dòng `document_repealed` (chế độ `sau_het_hieu_luc`);
   - dời ranh giới T3 về ngày trước mỗi lần chuyển;
   - loại lineage mà lời văn là điều khoản hiệu lực;
   - gán miền theo trường của cổng.

Thứ tự khác §7 của báo cáo. D4 đi **sau** J1–J5, vì hai lý do: 0/300 dòng κ đã gán, và J3–J4 đổi một số dòng κ.
Riêng việc liên hệ luật sư làm song song ngay từ đầu.

| Gói | Việc | Xong khi |
|---|---|---|
| J0 | Ghi quyết định vào plan này và ADR 0003 (schema 1.2.0) | ✅ 29/09 |
| J1 | Scorer:<br>• Accuracy/TCS tương phản<br>• bộ phân giải trích dẫn chữ<br>• `tver_strict`, độ phủ trích dẫn<br>• probe `hedge` · `no_cite` · `text_cite`<br>• `--ids` | ✅ 29/09 |
| J2 | `scripts/check/check_validity.py` → `data/review/validity_queue.tsv`. Các loại cờ:<br>• event bị bỏ sót<br>• văn bản đã hết hiệu lực<br>• điều khoản hiệu lực<br>• sau ngày chụp<br>• cấp huyện | ✅ 29/09; mọi cờ ngoài κ đã phân xử |
| J3 | Sửa gốc:<br>• thay cụm từ lệch hoa/thường, giải lại trên lời văn đang có hiệu lực<br>• nhận `effective_to` đã duyệt<br>• giữ pool ổn định<br>Sau đó dựng lại | ✅ 29/09; precision 29/30 |
| J4 | Ranh giới T3, dời dòng anh em, loại/thay lineage, dòng `sau_het_hieu_luc`, miền theo cổng, `retrieved_at`, `split` | ✅ 29/09 |
| J5 | Hướng dẫn v1.2, luật audit mới, dựng lại bộ κ, đóng băng bộ κ | ✅ 29/09, bộ κ đã đóng băng |
| J6 | Người làm: D4/D5, audit, luật sư, phân xử cờ κ | κ ≥ 0,6; audit đủ |
| J7 | Gold độc lập khoảng 120 dòng (gộp V6) | Tỷ lệ sai kèm Wilson CI; hai cột điểm |
| J8 | Manifest, datasheet, LICENSE, master plan, tag | Tag `vilextime-v1.0` (hỏi trước khi đẩy ra ngoài) |

#### Tiến độ 29/09

**J1 ✅.** Kết quả probe trên release trước khi dựng lại:
- `hedge` đạt Accuracy 0,293 theo bản tương phản, 0,951 theo bản lỏng; TCS = 0.
- `text_cite` cho TVER 0,049, đúng bằng tỷ lệ dòng bị bãi bỏ (trước đây 1,000).
- Oracle giữ trần.
- 21/665 trích dẫn chữ không phân giải được. Nguyên nhân: `citation` thiếu Điều ở các văn bản cũ đánh số theo mục, và số hiệu cũ trùng mà không có năm.
- Cổng lưu một số văn bản hai lần (cùng số hiệu, cùng ngày ký). Trích dẫn tới những văn bản này đứng cho điều khoản ở mọi bản.

**J2 ✅.** `check_validity.py` bắt được cả 12 dòng lỗi mà phản biện đã nêu. Đã siết để giảm báo động giả:
- chỉ giữ cạnh genealogy loại 12 ("thay thế"); loại 1 bị cổng dùng cả cho bãi bỏ một điều;
- câu chấm dứt phải có dạng "thay thế/bãi bỏ + loại văn bản + số", hoặc "số … hết hiệu lực", và không có dấu hiệu chấm dứt một phần (Điều/Khoản, phụ lục, mẫu, cụm từ, "một số").

Kết quả phân xử (`validity_queue.tsv`, reviewer `claude-opus-5-5`, người audit xác nhận ở J6):
- `document_ended`: 38 cặp văn bản. 9 văn bản đã hết hiệu lực mà siêu dữ liệu cổng bỏ sót: 176/2013/NĐ-CP, 147/2014/TT-BTC, 47/2020/NĐ-CP, 09/2017/TT-BLĐTBXH, 28/2018/TT-BNNPTNT, 135/2004/NĐ-CP, 62/2014/QH13, 81/CP (1995), 50/2016/TT-BGTVT. Tất cả đã ghi thành quyết định `effective_to` có trích câu nguồn trong `temporal_candidates.jsonl`. Các cặp còn lại là báo động giả.
- `missed_event` ngoài bộ κ: 32 cờ, 13 cờ đúng (10 lineage), 19 cờ giả. Có 2 lỗi mới ngoài danh sách của phản biện:
  - 102/2024/NĐ-CP Điều 32 hết hiệu lực theo NĐ 49/2026 (lệnh bãi bỏ dạng liệt kê mà L2 bỏ sót);
  - 16/2013/TT-BGTVT Điều 3 bị 10/2024 viết lại toàn bộ.

  Ngoài ra có một nhóm cờ giả do hai văn bản trùng số hiệu 01/2014/TT-NHNN: event của văn bản này bị gán sang văn bản kia.
- 18 cờ `missed_event` và 8 cờ `document_ended` thuộc lineage κ giữ `sau_D4`.

**J3 ✅ (code và dựng lại).**
- Thay cụm từ lệch hoa/thường; lệnh `phrase_not_found` được giải lại trên lời văn đang có hiệu lực.
- Event được áp: 18.840 → 19.182. Mẫu 30 event mới được áp có 29/30 đúng nội dung (Wilson 95% [83,3; 99,4]). Lỗi còn lại là cụm từ lặp ("05 ngày làm việc làm việc"), loại lỗi đã có từ trước (74 chỗ lặp trong bản cũ).
- **Phát hiện khi dựng lại:** khi lệnh thay cụm từ không còn trượt, 15 lệnh sửa cả điều khoản hoặc lệnh bãi bỏ **cùng ngày, cùng văn bản** bị chúng chiếm chỗ. Bộ áp event chỉ nhận một thay đổi mỗi ngày cho một nút. Sửa: trong một ngày, lệnh thay cụm từ của cùng văn bản áp sau cùng (`application_sort_key`). Không đổi bất biến của bộ áp event.
- **Lỗi của bản sửa pool, đã sửa:** thứ hạng giữ lại phải theo từng nhóm. Nếu không, 12 lineage T6 "ancestor" (cũng là ứng viên T1) bị giữ ở T1.
- Ingest áp thêm 375 quyết định `effective_to` (367 cũ + mới). `tests/test_real_version_chains.py` cập nhật theo: 03/2014/TT-NHNN nay kết thúc 01/07/2024.

**J4.** Đã loại 12 lineage (`dropped.jsonl`):
- 5 lineage là điều khoản hiệu lực thi hành;
- 3 cặp hỏi sau ngày chụp corpus;
- 4 lineage có dòng ranh giới sai.

Lineage thay thế:
- Câu hỏi mới viết bằng phiên Claude Code qua `validate()`: T1 8/8, T2 7/8 (1 `insufficient_context`: lineage 40/2014/TT-BCT bị nối nhầm), T3 5/5.
- Hai chuỗi 4 phiên bản kế tiếp không dùng được: hạng 84 bị nối nhầm, hạng 129 là điều khoản hiệu lực thi hành.
- **Chốt 29/09 (CMT): T3 199 + T1 251**, tổng vẫn 1.150. Sau khi loại, mọi chuỗi T3 còn dùng được dài 3 dòng, nên T3 chỉ ra 199 hoặc 202.

**Lưu ý:** `sample_vilextime.py` (không kèm `--select`) giữ thứ tự cũ nhưng **đánh số hạng lại** khi có lineage rời nhóm. Đợt này không dùng nó; `sample.jsonl` giữ nguyên bản đã commit.

**J4 ✅.** Bản phát hành mới có 2.481 dòng:
- 1.150 dòng ranh giới: T1 251 · T2 400 · T3 199 · T4 150 · T5 38 · T6 112;
- 1.150 dòng anh em;
- 181 dòng `sau_het_hieu_luc` (91 lineage không có dòng này vì không tìm được câu chấm dứt).

Tổng cộng 666 lineage trên 517 văn bản. Split theo văn bản: 131 lineage dev, 535 lineage test.
- Miền: `seed` 215 · `portal_field` 223 · `portal_major` 135 · `khong_ro` 93 lineage.
- 17 lineage mới vào bản chọn: 13 dùng câu hỏi vừa viết, 4 lấy từ dự phòng. Đã bổ sung 31 đáp án ngắn và 30 nhãn model (đều bắt buộc audit). Lineage T6 mới rơi vào bộ κ nên không có nhãn model.
- `check_release.py`: OK. Không lineage nào ở hai split, không văn bản nào ở hai split, T5 không có trong dev.
- `check_validity.py`: mọi cờ ngoài κ đã có quyết định, trừ `cap_huyen` (chờ người audit).

**J5 ✅ (phần của agent).**
- Hướng dẫn v1.2 và `GUIDELINE = "1.2"` (một nguồn, ở `crosscheck.py`).
- `labels.py`:
  - thêm luật audit bắt buộc cho dòng có điều khoản chuyển tiếp và dòng nói "cấp huyện";
  - thêm `mark-audit`;
  - người audit phải là `human:*`;
  - phiếu audit thêm cột ngày hỏi lại, văn bản tác động và cờ hiệu lực.
- 140 nhãn T3 chuyển sang id mới (cùng lineage, câu hỏi và gold), có ghi chú id cũ.
- 490 nhãn bắt buộc audit (trước đây 338). Phiếu audit T1–T4 đã dựng lại.
- **Bộ κ dựng lại có giữ lượt bốc cũ** (`crosscheck.py pick(prior)`). Nếu bốc lại từ đầu thì seed xáo 35/141 lineage, và các lineage mới vào sẽ mang sẵn nhãn model. Kết quả: giữ 138 lineage; 3 lineage đã rời bản phát hành được thay. Id của 50 dòng T3 đổi theo ngày ranh giới mới.
- `kappa` liệt kê 13 dòng κ đã có nhãn ngoài D4 (8 `human:excel`, 5 nhãn model gán khi dòng chưa thuộc κ), để ghi vào biên bản D5.
- Bảng luật sư T5 dựng lại, có đánh dấu văn bản mà câu hiệu lực không nêu ngày hồi tố.
- **Bộ κ đã đóng băng, sẵn sàng cho D4.**

**J8 (một phần).**
- `data/vilextime/LICENSE` (CC BY 4.0).
- `docs/vilextime-datasheet.md` đã có số liệu 29/09.
- `check_release.py --manifest` ghi `data/vilextime/manifest.json`. Lần ghi hiện tại có `uncommitted_changes: true`, phải ghi lại sau khi commit.
- Master plan có thêm B7+ (P5.13b), ghi chú P5.1 và P5.6; P5.4, P5.5 ✅.
- Còn lại: tag `vilextime-v1.0` và đẩy release lên GCS. Hai việc này làm sau J6/J7 và cần hỏi CMT trước.

**Scorer, chỉnh cuối.** Đơn vị thuộc `accepted_evidence` của dòng không bao giờ bị tính là lỗi TVER, kể cả khi câu chấm dứt nằm trong một văn bản về sau cũng hết hiệu lực. Nhờ đó oracle đạt trần ở cả ba chế độ.

Probe trên split test:
- "ngày gần nhất" ở T3 ranh giới: 1,000 → 0,325;
- `hedge`, Accuracy tương phản trên bảng chính: T2 0,057 · T3 0,000 · T4 0,028; TCS 0.

**Kiểm chứng:** `python -m pytest -q` cho 385 passed, không test nào bị bỏ qua.

**Còn lại cho người (J6, J7):**
- D4/D5 trên bộ κ mới;
- audit 490 nhãn;
- luật sư chốt T5;
- phân xử 26 cờ `sau_D4`;
- cờ `cap_huyen`;
- khoảng 120 dòng gold độc lập.

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
| C1 | ✅ 21/09 Prompt sinh câu hỏi từ bộ ba, cấm model tự thêm số liệu hoặc mốc thời gian không có trong bộ ba | `prompts/vilextime/base.md` + một file mỗi nhóm (T1, T2, T3, T4, T6). `question_source` ghi provider/model/temperature/prompt_sha trên từng dòng. Client đa nhà cung cấp `src/vilexgraph/llm.py` (Groq trước), không thêm dependency |
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
  `src/vilexgraph/llm.py`). Chỉ gửi text văn bản luật công khai.
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

- 2026-09-28 (CMT): **model gán nhãn trước, nhóm audit cuốn chiếu** (hướng dẫn
  v1.1 §6). Nhãn ngoài D4 nằm ở `data/review/labels.tsv`, một dòng cho mỗi
  (dòng QA, người gán), chỉ ghi qua `scripts/review/labels.py` (kiểm từ vựng
  đóng; từ chối nhãn model trên dòng D4 khi A, B chưa gán xong). κ vẫn chỉ giữa
  hai người. Nhãn tay T1 gõ trong file Excel preview được nhập nguyên văn
  (`human:excel`, 184 dòng T1 + 26 dòng T2 `CHECKED`; 10 câu hỏi bị sửa trong
  Excel giữ ở `note`, chưa áp vào `questions.jsonl`). Hướng dẫn v1.1: câu dẫn là
  một phần của đáp án, mã `transitional_rule`, lớp `meta_issues`.
  **T1 do model gán đủ 250:** 222 `dat`, 28 `khong_dat` (20 `question_ambiguous`,
  3 `unanswerable_as_asked`, 3 `other` — điều khoản thi hành dính khối chữ ký,
  2 `question_leaks`), 33 dòng có `meta_issues` (16 `valid_to_wrong`: valid_to
  rỗng dù có cạnh 'Văn bản được thay thế' hoặc văn bản đã bị thay thế; 15
  `citation_path_wrong`: citation thiếu cấp cha). 7 dòng `dat` là điều khoản hiệu
  lực/thi hành, ghi chú "cân nhắc loại khỏi T1".
  So với 141 dòng người có verdict: đồng ý 83,0%; 6 dòng lệch do quy tắc câu dẫn
  mới, 6 dòng người đã sửa câu hỏi (tức câu gốc có lỗi). Ba mẫu lỗi lặp: văn bản
  chức danh nghề nghiệp/ngạch có một Điều cho mỗi hạng mà câu hỏi không nêu hạng;
  cùng mục có ở nhiều Điều cho nhiều loại đồ án/nghề; câu hỏi về "một tổ chức"
  trong nghị định xử phạt mà mức ghi trong khoản là mức cho cá nhân (tổ chức gấp
  02 lần). 96 nhãn cần audit: `labels.py audit-sheet` → điền → `import-audit`.
  **Cập nhật cùng ngày (CMT):** `CHECKED` ở 26 dòng T2 và `verified` ở T1 nghĩa
  là đạt. 10 câu hỏi sửa trong Excel được áp vào `questions.jsonl`
  (`edited_by: human:excel`, câu gốc giữ ở `model_question`; ADR 0003 Follow-Up),
  cả 10 qua C2 sau khi sửa lỗi `presumes_the_present` bắt nhầm "thực hiện hành vi"
  (0 câu từng bị loại oan). Dựng lại T1 + `--select`: bản phát hành chỉ đổi đúng
  10 dòng ở `question`, `question_source`. Model chấm lại 10 câu: 9 đạt, 1 vẫn mơ
  hồ (63/2007 điểm b khoản 5 Điều 18). T1 của model nay 228 `dat` / 22
  `khong_dat`, đồng ý với người 86,5% (141 dòng), 91 nhãn cần audit.

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
