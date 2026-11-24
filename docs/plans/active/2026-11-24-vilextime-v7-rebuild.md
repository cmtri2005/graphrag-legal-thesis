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
- [ ] Script nhập + khóa phiếu (làm khi lô thử về), dựng GD2 theo lô (`build.py gd2 loNN`).
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
