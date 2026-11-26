# Execution Plan: Dựng lại bộ test ViLexTime 7.0 theo đề cương

Date: 2026-11-24

## Status

Active. CMT quyết 24/11 dựng lại (đối chiếu đề cương: `docs/reports/doi-chieu-de-cuong-2411.md`).

## Outcome

Bộ test 7.0 cho khóa luận, khớp đề cương ở hai chỗ đang lệch:
1. **Cỡ và cơ cấu** theo định nghĩa §9 (khoảng 1.100–1.150 dòng, đủ T1–T6; T4 là lát của T2).
2. **Mọi dòng do hai người gán độc lập, đọc mù** theo hướng dẫn Q1–Q4. Chỗ lệch do luật sư hòa giải. AI không đứng
   tên nhãn.

Sau đó chạy lại G4 trên bộ 7.0, một lần, theo ADR 0006 cộng amendment.

## Context

- Định nghĩa đã khóa `docs/vilextime-dinh-nghia.md`: §8 (tập test chỉ gồm dòng người kiểm; luật sư hòa giải, không
  dùng AI), §9 (quota), §7 (mã loại). Không đổi định nghĩa.
- Hướng dẫn gán nhãn `docs/vilextime-annotation.md` (Q1–Q4).
- Pipeline có sẵn, dùng lại: `build_question_pool.py` → `sample_vilextime.py` (`sample(..., skip=)`) →
  `generate_questions.py --sample` → `build_vilextime.py` → `sample_vilextime.py --select`.
- Kho ứng viên `data/derived/vilextime_pool.jsonl`: 11.408 lineage; trong khung (bỏ văn bản dev): T1 2.452,
  T2 5.087, T3 446, T5 198, T6 2.616.
- Kiểm tra kho `docs/reports/kiem-tra-kho-2411.md`: kho sót sửa đổi là lỗi chính. Q4 do người gán kiểm bằng nguồn.

## Scope

In scope: khung mẫu, rút mẫu, sinh câu hỏi, kiểm kho trên mẫu, phiếu gán, gán, hòa giải, dựng bản 7.0, chạy lại G4,
evidence-gate.

Out of scope: đổi định nghĩa, thêm nhóm hay mã loại; sửa toàn kho (18.982 lệnh chờ duyệt, ghi ở giới hạn); bộ dev
(giữ nguyên để không phải chọn lại cấu hình).

## Approach

1. **Đăng ký trước** `docs/reports/dang-ky-truoc-v7.md`, commit trước khi rút mẫu.
2. **Khung mẫu:** `data/vilextime_v7/frame_excluded.txt` = mọi lineage của kho ứng viên đã xuất hiện trong
   `data/review/` hoặc một bản phát hành cũ. Không rút lineage nào trong danh sách này.
3. **Rút mẫu** bằng `sample()` có sẵn, seed mới, `skip` = khung loại.
4. **Sinh câu hỏi** bằng `generate_questions.py` như cũ. Câu hỏi đã sinh cho lineage chưa ai thấy được dùng lại.
5. **Kiểm kho miễn phí trên mẫu** (lệnh bị kho từ chối, như `w3/store_check.py`) để đánh dấu lineage nghi lỗi cho
   người gán. Không cho người gán xem đáp án kho.
6. **Phiếu gán** theo Q1–Q4; người gán tự tra nguồn và ghi phút.
7. **Hòa giải:** máy so A với B và với kho; luật sư chốt chỗ lệch.
8. **Dựng 7.0** chỉ từ dòng đạt; `check_release.py`.
9. **G4 trên 7.0:** amendment ADR 0006 (bộ test mới, cùng hệ, cùng cấu hình), CMT duyệt rồi mới chạy.

## Risks And Recovery

- T3 chỉ còn 183 lineage chưa ai thấy; trước đây bị loại 82%. Không đạt sàn 120 dòng thì giảm quota, không nới điều
  kiện (định nghĩa §9); báo T3 là tập chẩn đoán.
- T5 cần luật sư xác nhận từng văn bản. Luật sư không kịp thì T5 báo riêng.
- Kết quả có thể khác G4 cũ: báo đúng số mới.
- Bộ 6.x giữ nguyên làm dự phòng đến khi 7.0 qua evidence-gate.

## Progress

- [x] Đăng ký trước (8fb24e9), S1.
- [x] Khung loại: 609 lineage (73 văn bản dev).
- [x] Rút mẫu seed 20261124: T1 500, T2 550 + T4 150, T3 159 (481 dòng), T5 23, T6a 150, T6b 250 lineage. 1.504
  lineage cần câu hỏi mới.
- [x] Rà pipeline viết câu hỏi, sửa 4 lỗi (ab8e8bf): mục anh em, luật mọi phiên bản, T4.md, ghi ra file riêng
  `data/vilextime_v7/questions.jsonl` (viết lại toàn bộ mẫu bằng một model, một prompt).
- [x] Chạy thử 30 lineage cũ bị loại bằng Qwen3.8-27B (Chutes, seed 20261124): 28/30 qua bộ lọc máy.
- [x] CMT chấm vòng 1 (`pilot/pilot_cham_filled.xlsx`): Qwen + prompt v1 8/28, Opus 10/17.
- [x] Pipeline `qg_v7.py` (thiết kế `docs/reports/thiet-ke-sinh-cau-hoi-v7.md`); kiểm chứng hiệu chuẩn 46/58;
  chế độ `--fast` 22/30 trên tập khó, ~0,004 USD/lineage (CMT: 12–15 USD cho bản đầy đủ là nhiều).
- [x] Sinh câu hỏi cho 1.782 lineage (`qg_v7.py --fast`, Qwen3.8-27B, 4.212 lượt gọi, 6,29 USD): 1.504 lineage có câu
  qua máy. Theo phần (lineage đạt / dòng): T1 476/476, T2 450/900, T4 120/240, T3 78/237, T5 10/20, T6a 143/286,
  T6b 227/454. Bị loại: 46 `no_substantive_change`, 231 `qg_failed`, 1 lỗi. `questions.jsonl` sha256 df44691341db889a…;
  nhật ký lượt gọi `questions.calls.jsonl.xz`.
- [ ] Kiểm kho trên mẫu.
- [x] Phiếu gán Giai đoạn 1: `data/vilextime_v7/phieu/lo00–lo48` (lô thử 20 dòng, lô sau 50 dòng; 2.433 dòng), mỗi lô
  `GD1_A.xlsx`, `GD1_B.xlsx`, `key.tsv` (không giao). S2: loại 93 lineage câu lệnh sửa đổi.
- [x] Script nhập + khóa phiếu (`build.py lock loNN A.xlsx B.xlsx` → GD1.tsv, GD1_lech.tsv, GD1.locked sha256), dựng GD2
  theo lô (`build.py gd2 loNN`).
- [x] Lô thử lo00 về 24/11, khóa: Hiệu lực khớp 20/20; lời văn lệch 2 dòng (00-13 phần hiệu lực 2027, 00-16 chuyển
  tiếp NĐ 23/2026); đáp án ngắn lệch độ dài trích ở 13 dòng; A để trống đáp án 00-20. Hai file lưu bằng openpyxl,
  không phải Excel; phút A có số lẻ 0,1–0,2: hỏi lại công cụ sinh viên dùng. GD2 lo00: 11 câu hỏi.
- [x] GD2 lo00 khóa (`build.py lock GD2 …`): kết luận đạt/không khớp 11/11, đạt 4/11 lineage = 7/20 dòng
  (T6a 0/2, T6b 0/4, T3 0/3); Q1 lệch 2 (00-09, 00-11), mã lý do lệch 4. Lỗi kho do người gán chỉ ra: 00-05 phiên
  bản 3 gộp phần hiệu lực 01/07/2027; 00-11 vbpl 17/01/2026 vs VBHN 01/01/2027; 00-03, 00-08 relocated.
- [x] Sau lô thử (24/11): CMT xác nhận hai sinh viên điền bằng Excel. Hướng dẫn GD1 thêm mục "Cách trích đáp án ngắn"
  (cụm bắt buộc, giữ phần có thể thay đổi, bỏ ký hiệu đầu mục, nối " … ") và quy tắc phút (số nguyên, làm tròn
  lên); GD2 thêm quy tắc phút. Dựng lại phiếu lo01–lo48 (key.tsv không đổi); lo00 đã khóa, giữ nguyên.
- [x] Phiếu hòa giải lo00 (`build.py hoa_giai lo00` → `lo00/hoa_giai.xlsx`): 7 dòng giữ, A/B/kho khớp hiệu lực và
  lời văn, chỉ chốt đáp án ngắn; 4 mã lý do lệch (câu đã loại). Mọi lệch lời văn GD1 (00-13, 00-16, 00-20) thuộc câu
  đã loại. Chờ luật sư. (00-12, T4: đáp án ngắn nằm trọn trong lời văn bản trước, nhưng scorer đã loại câu trả lời
  chứa cụm riêng của phiên bản khác (`score_vilextime.distractors`), nên không cần amendment; cần giữ cả hai ngày
  của lineage T2/T4 trong bộ test để cụm đối chứng tồn tại.)
- [x] lo00 chốt (`build.py chot lo00 …` → `lo00/final.jsonl`, `hoa_giai.locked`): giữ 7 dòng (T1 1, T2 2, T4 2, T5 2),
  loại 13. Luật sư chọn bản dài ở 00-15, 00-19 (giữ "trong nội dung của quy hoạch chung đô thị được phê duyệt"), khác
  quy tắc "ngắn nhất": theo dõi Accuracy chứa-cụm trên các dòng đáp án dài.
- [x] lo01, lo02 GD1 khóa (hiệu lực khớp 50/50, 46/50), GD2 khóa 25/11 (kết luận khớp 21/27, 20/27). Phiếu hòa
  giải thêm trang "Kết luận" cho câu một người đạt, một người không (luật sư chốt, theo đăng ký trước §dòng 17).
  Lỗi hướng dẫn GD2: "có phiên bản không trả lời được" làm loại mọi câu T6 (lo01 0/16, lo02 0/14 dòng); đã sửa
  hướng dẫn cho lô sau. CMT duyệt S4 (25/11): giao lại GD2 riêng câu T6 (`build.py gd2b`): lo01 8 câu, lo02 7
  câu. Hòa giải lo01, lo02 chờ GD2b khóa. Phiếu hòa giải thêm cột "Hiệu lực cuối" khi A, B lệch; dòng T6 mốc sau
  (cả hai ghi Hết) không cần đáp án ngắn.
- [x] lo03–lo12 GD1 khóa 26/11 (506 dòng; hiệu lực A–B khớp 490/505, khớp kho A 500, B 490; 13/16 chỗ lệch là T6,
  phần lớn B ghi Còn). GD2 lo03–lo12 đã dựng, chờ gửi. Phút KHÔNG tin được: A 252 dòng ghi 1 phút, lo11 ghi 850
  phút/dòng; B ghi ~280 phút/lô nhưng giờ lưu file cách nhau 25–35 phút. File cả hai lưu bằng openpyxl. CMT xác
  nhận hai bạn tự gán; giữ nguyên phút đã ghi, không sửa. Khi báo cáo phút trung vị (đăng ký trước §70) phải ghi
  rõ giới hạn này hoặc bỏ chỉ số. Lỗi phiếu: 09-39 cột Điều khoản thiếu số điều; 03-39, 06-22, 07-02, 08-12 A ghi
  Còn nhưng để trống đáp án (lý do ở báo cáo của A), chuyển luật sư. So `van_ban_ap_dung` đang so cả chữ "Nghị
  định"/"Thông tư" nên báo lệch giả (cùng số hiệu 461/490).
- [ ] Gán (A, B).
- [ ] Hòa giải (luật sư).
- [ ] Dựng 7.0.
- [ ] Amendment ADR 0006, G4 trên 7.0.
- [ ] Evidence-gate.

## Decisions

- 2026-11-24 (CMT): dựng lại bộ test; cỡ mẫu theo đề cương/định nghĩa §9, không giới hạn theo giờ gán ("team gán được").
- 2026-11-24 (CMT): giữ LLM sinh câu hỏi; bỏ AI gán nhãn, thay bằng hai người.
- 2026-11-24 (CMT, S1): người gán là hai sinh viên luật chưa xem dữ liệu; CMT, NMT chỉ phân xử ca máy móc. Khung chỉ
  loại văn bản của tập dev (609 lineage).
- Còn mở: nộp DiB bằng 6.x hay chờ 7.0.

## Validation

- Đếm bằng script: 0 lineage của mẫu nằm trong khung loại; quota từng nhóm theo §9 hoặc ghi lý do thiếu.
- Mọi dòng của 7.0 có nhãn của cả A và B, có phút, có kết quả hòa giải nếu lệch.
- `check_release.py` đạt; evidence-gate đạt cho mọi con số.

## Result

Điền sau khi xong.
