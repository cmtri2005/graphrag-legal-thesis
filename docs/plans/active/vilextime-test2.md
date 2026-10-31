# Execution Plan: ViLexTime bộ test 2 (T2, T3, T6; gán theo câu hỏi)

Date: 2026-10-29

## Status

Active. Claude soạn 29/10 theo yêu cầu của CMT. Chạy song song với đợt test v1.0
(`codex-chot-du-lieu-va-thuc-nghiem.md` Phần C); không đụng bản `vilextime-v1.0`.

## Outcome

Một bộ test thứ hai khoảng 300 câu hỏi (T2 ~150, T6 ~100, T3 tối đa kho cho phép), mỗi câu hỏi do
A và B gán độc lập theo thẻ gán nhãn 4.0 (`docs/vilextime-the-gan-nhan.md`), dòng lệch do luật sư
hòa giải, đồng thuận đo trên từng câu Q1–Q4. Bộ này được đăng ký trước bằng amendment ADR 0005, chạy
mỗi cấu hình một lần, để kiểm lại kết luận của v1.0.

## Context

- Định nghĩa: `docs/vilextime-dinh-nghia.md` (luật sư đã ký, không sửa). Thẻ 4.0 chỉ đổi cách hỏi,
  mỗi câu Q ứng với điều kiện ở §6 của định nghĩa.
- Chẩn đoán đo 29/10 trên 246 dòng có cả nhãn A và B theo 3.0: 97/105 dòng lệch là A `dat` / B
  `khong_dat`; luật sư đứng về phía B 87/101. Lý do của bên `khong_dat`: T2 `group_mismatch` 30,
  hình thức hoặc dẫn chiếu tự áp 14, T6 chuyển chỗ 15, câu hỏi mơ hồ hoặc không trả lời được khoảng 22.
  Nghĩa là phần lớn lỗi nằm ở **dòng đưa cho người** (câu hỏi không chạm chỗ đổi, lần sửa không thực
  chất) và ở **cách gán nhanh**, không phải ở định nghĩa.
- Kho ứng viên (`data/derived/vilextime_pool.jsonl`) sau khi bỏ văn bản của split dev (73 văn bản) và
  246 lineage đã có trong v1.0: T2 5.055 (gần giống 1.502), T6 2.622 (cấp trên 1.826, đích danh 796),
  T3 441.

## Scope

In scope:

- Lọc ứng viên bằng Claude (CMT 29/10: luật cứng không giải quyết được), có hiệu chuẩn mù trước.
- Claude viết câu hỏi nhắm đúng chỗ đổi; kiểm trùng chữ tự động.
- Thẻ gán nhãn 4.0, trang gán theo câu hỏi, A và B gán đôi, luật sư hòa giải.
- Amendment ADR 0005 cho bộ test 2, commit trước lần chạy đầu tiên.

Out of scope:

- Sửa `vilextime-v1.0`, sửa định nghĩa, thêm nhóm hay mã loại.
- Cào thêm văn bản: kho hiện có đủ; bộ test 2 dùng chung corpus và đồ thị với v1.0.
- T1, T5 (không có trong bộ test 2).

## Approach

1. **Mẫu ứng viên.** Rút ngẫu nhiên có seed, phân tầng theo nhóm và thẻ (T2 thường, T2 gần giống,
   T6 cấp trên, T6 đích danh), khoảng 850 lineage. Rút ngẫu nhiên để phễu lọc báo được, không chọn tay.
2. **Hiệu chuẩn bộ lọc Claude (mù).** Chạy cùng lời dặn trên các lineage v1.0 đã có nhãn cuối của
   người hoặc luật sư, chỉ với lý do ở cấp lineage (`cosmetic_only`, `rename_only`,
   `auto_reference_update`, `relocated`, `relocation_unclear`, `reference_only`,
   `superseded_by_other_norm`, `gold_wrong`). Phiên lọc chạy trong thư mục ngoài repo, chỉ có gói
   lineage và lời dặn, như A2 của plan Codex. Ngưỡng (CMT 29/10, "càng chất lượng càng tốt"): loại được
   ≥ 80% lineage xấu, loại nhầm ≤ 30% lineage tốt; kho đủ lớn nên chấp nhận mất câu tốt hơn để lọt câu
   xấu. Không đạt thì sửa lời dặn **một lần** trên tập hiệu chuẩn khác, ghi cả hai lần; không đạt nữa
   thì dừng và báo CMT. Lệnh: `scripts/review/test2_packs.py build|score`, lời dặn
   `prompts/vilextime/test2_loc.md`.
3. **Lọc 850 ứng viên.** Mỗi lineage một quyết định `giu` / `loai` kèm mã của định nghĩa §7 và câu
   trích làm căn cứ. T6: Claude tìm dấu vết chuyển chỗ theo bước 7 của hướng dẫn 3.0; không chắc thì
   `loai` (`relocation_unclear`), không đưa cho người. Quyết định lọc là bước xếp loại, không phải nhãn
   kiểm định (hướng dẫn 3.0 §6), và được phát hành cùng phễu.
4. **Viết câu hỏi.** Claude viết một câu hỏi cho mỗi lineage `giu`, nhắm vào phần khác nhau giữa các
   phiên bản (T2, T3) hoặc nội dung bị bãi bỏ (T6), không nêu ngày, số hiệu, Điều, Khoản. Kiểm tự động:
   tỷ lệ tiếng có nghĩa của câu hỏi nằm nguyên văn trong đáp án ≤ 40% (CMT 29/10); quá thì viết lại
   tối đa hai lần rồi loại. Ghi `question_source`.
5. **Gán nhãn.** Trang gán theo câu hỏi (mọi mốc của một câu hỏi trên một màn hình, tô chỗ khác nhau),
   phiếu Q1–Q4 và ô dẫn chứng bắt buộc. Lô 0: 20 câu, A và B độc lập, luật sư xem chỗ lệch, kết luận vào
   §7 của thẻ. Đo AC1 từng câu Q sau 50 câu đầu; dưới ngưỡng (AC1 ≥ 0,80 và p_neg ≥ 0,60) thì dừng,
   hiệu chuẩn lại trên câu mới, không sửa nhãn đã gán.
6. **Hòa giải và đóng băng.** Luật sư chốt mọi câu lệch. Câu `khong_dat` sau hòa giải bị loại với mã.
   Xuất split `test2` cùng corpus, tag riêng.
7. **Đăng ký trước và chạy.** Amendment ADR 0005: cùng XN1–XN9, Holm, bootstrap theo lineage; ghi cỡ
   thật của `test2`. CMT commit trước lần chạy đầu tiên; mỗi cấu hình chạy một lần.

## Risks And Recovery

- Bộ lọc Claude dễ dãi (đo 19/10: model gắn `khong_dat` 2–3% ở T1/T2). Phòng: hiệu chuẩn mù ở bước 2;
  người vẫn gán mọi câu được giữ, nên lọc dễ dãi chỉ làm tốn công người, không làm bẩn test.
- Bộ lọc loại nhầm câu tốt, tạo thiên lệch chọn. Phòng: ngưỡng loại nhầm ở bước 2; phát hành phễu và
  quyết định lọc.
- Câu hỏi do Claude viết, generator là Qwen (ADR 0004 §3): không cùng họ. Báo theo `question_source`.
- Gán nhanh như v1.0. Phòng: ô dẫn chứng bắt buộc, lô 0 với luật sư, dừng khi AC1 thấp.
- Thiếu người: mỗi người khoảng 430 câu hỏi × 3 phút, khoảng 21 giờ. Thiếu thời gian thì giảm quota
  theo nhóm, không nới điều kiện (định nghĩa §9).

## Progress

- [x] 29/10: chẩn đoán lệch A–B, đếm kho ứng viên, soạn plan và thẻ 4.0 (Claude).
- [x] 29/10: CMT duyệt thẻ 4.0 và hai ngưỡng; luật sư rảnh, A và B gán đôi 100%.
- [ ] Luật sư xem thẻ 4.0 trước lô 0.
- [x] 29/10 bước 1: `test2_packs.py build --out ~/vilextime_loc/gan/packs` → 653 mục (68 hiệu chuẩn,
  585 ứng viên), 27 gói, 5,1 triệu ký tự; khóa `~/vilextime_loc/key_loc.tsv` (ngoài thư mục gán). Hiệu
  chuẩn: tốt 40 (T2 28, T3 4, T6 8), xấu 28 (T2 gần giống 2, T3 1, T6 25). **Giới hạn:** T2 chỉ có 2 mục
  xấu, nên tỷ lệ loại đúng thực chất là số đo của T6; ở T2 chỉ đo được loại nhầm. Người vẫn gán mọi câu
  được giữ, nên lọc lỏng ở T2 chỉ tốn công người. Lời dặn sha256 `e524774ebc8e2d33…`; `pytest` 567 qua.
- [ ] Bước 2: CMT mở phiên Claude Code mới trong `~/vilextime_loc/gan` (thư mục chỉ có gói, lời dặn,
  `CLAUDE.md`), lọc 27 gói ra `result.tsv`; kiểm log phiên không có đường dẫn tới repo; chấm `score`.
- [ ] Bước 3–4: lọc 850, viết câu hỏi, kiểm trùng chữ.
- [ ] Bước 5: trang gán theo câu hỏi; lô 0; gán đôi; đo AC1 từng Q.
- [ ] Bước 6–7: hòa giải, đóng băng, amendment ADR 0005, chạy.

## Decisions

- 2026-10-29 (CMT): lọc ứng viên bằng Claude thay cho luật cứng; phiếu Q1–Q4, nhãn do máy suy ra,
  gán theo câu hỏi; luật làm việc (dẫn chứng bắt buộc, lô 0 với luật sư, dừng khi AC1 thấp).
- 2026-10-29 (Claude, mặc định, CMT có thể đổi): bỏ văn bản của split dev và lineage đã có trong v1.0;
  dùng lại lineage silver nhưng viết lại câu hỏi; T6 không chắc chuyển chỗ thì loại ở bước lọc.

- 2026-10-29 (CMT): ngưỡng lọc ≥ 80% / ≤ 30%; ngưỡng trùng chữ ≤ 40%; thẻ 4.0 duyệt; luật sư rảnh;
  A và B gán đôi 100%.
- 2026-10-29 (Claude): rút đợt 1 khoảng nửa số cần (T2 150, T2 gần giống 65, T3 220, T6 mỗi kiểu 75), seed
  `vilextime-test2-2910`; thiếu thì rút đợt 2 tiếp theo cùng thứ tự. Hiệu chuẩn bỏ nhãn một người và 101 dòng
  luật sư hòa giải có phiếu Claude hỗ trợ (không mù với Claude).

Câu hỏi còn mở: mốc cuối tháng 11 đã chắc chưa.

## Validation

- Focused proof: bảng hiệu chuẩn bộ lọc (tỷ lệ loại đúng, loại nhầm theo nhóm); kiểm trùng chữ chạy
  trên mọi câu hỏi; AC1 và p_neg theo từng Q.
- Integration or end-to-end proof: `export_release.py` ra split `test2`; `run_vilextime.py` →
  `score_vilextime.py` → `confirm_vilextime.py` chạy trọn trên `test2`.
- Repository-required checks: `.venv/bin/python -m pytest -q`.

## Result

(Điền khi xong.)
