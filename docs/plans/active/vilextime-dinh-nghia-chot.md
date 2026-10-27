# Execution Plan: Dựng lại ViLexTime theo định nghĩa chốt

Date: 2026-10-20

## Status

Active. Bước 1–5 xong (luật sư đồng ý 21/10). Chờ người kiểm theo lô phiếu
`data/review/kiem_{A,B}.xlsx` (bước 6).

## Outcome

Bản phát hành ViLexTime mà **mọi dòng của tập test** đạt 8 điều kiện ở mục 6 của
`docs/vilextime-dinh-nghia.md`, đã được người kiểm có dẫn chứng; dòng bị loại mang một mã ở mục 7;
cơ cấu đạt sàn ở mục 9; `check_release.py` OK; datasheet không còn mục "chưa xong".

## Context

- Định nghĩa: `docs/vilextime-dinh-nghia.md` (chốt 20/10/2026, CMT).
- Lý do làm lại: D4 sau hòa giải hỏng 22–64% theo lát; nhãn model chỉ gắn `khong_dat` 2–19%, khớp
  người 7/13 dòng (memory, đo 19/10); 7 loại lỗi đồ thị ở `docs/reports/D5_bien_ban.md` §5.
- Mốc: chạy xong đồ án trước 31/10/2026 (A1). Bản dựng lại này phục vụ khóa luận nếu kịp, và chắc
  chắn phục vụ bài báo. Nhóm chọn mốc cho bước 6–8.

## Scope

In scope:

- Hướng dẫn gán nhãn 3.0, bộ lọc máy, sửa lỗi đồ thị, dựng lại, phiếu kiểm, kiểm định người,
  gold độc lập, đóng băng.

Out of scope:

- Thao tác "bổ sung" điều khoản mới; lát "T6 chuyển chỗ" có chấm điểm; chế độ `sau_het_hieu_luc`.

## Approach

1. **Luật sư ký** 7 quy tắc pháp lý (CMT gửi). Không đồng ý điểm nào thì sửa đúng điểm đó trong
   định nghĩa trước bước 6.
2. **Hướng dẫn gán nhãn 3.0** viết lại theo định nghĩa: 8 ô kiểm bắt buộc, mã loại đóng, ví dụ mục
   10; phiếu có cấu trúc (ô "đã kiểm văn bản tác động nào", "nội dung còn ở đâu", "chạm lần sửa nào").
3. **Bộ lọc máy:** R1-i (đã có `cosmetic_change`), R1-ii (danh sách đổi tên cơ quan, đơn vị do sắp
   xếp 2025), R1-iii (điều khoản tự cập nhật dẫn chiếu), R4 (mở rộng bộ dò `cap_huyen` sang bộ, tỉnh),
   R5 (đáp án chỉ là dẫn chiếu), R6 (`pending_events.py`), R7 (đã có); T3 chỉ giữ ứng viên có ≥ 2
   lần chuyển thực chất sau R1; tách T5a/T5b, T6a/T6b; bỏ `sau_het_hieu_luc` khỏi phần chấm.
4. **Sửa lỗi đồ thị** còn lại ở D5 §5 (mục 1 đã sửa ở `5877a5a`): thay toàn bộ điều, khoản bị bỏ sót;
   đích bãi bỏ sai; `valid_to` sai; quy phạm cấp cao thay nội dung (chỉ dò để loại theo R3).
5. **Dựng lại một lần**, giữ nhãn người cũ khi câu hỏi và đáp án không đổi; xuất phiếu kiểm kèm
   đoạn trích văn bản gốc (`crosscheck_evidence.py --ids`).
6. **Người kiểm 100% tập test**; 25% gán đôi; người thứ ba (luật sư) hòa giải; ~100 câu người viết lại.
7. **Gold độc lập** 120 + 30 (đang làm, B6).
8. **Đóng băng:** manifest, tag, datasheet, phụ lục chỗ chuyển đến, silver.

## Risks And Recovery

- T3, T6 thiếu dòng sau khi lọc chặt → lấy từ kho ứng viên (T3 386, T6 2.812), không đạt sàn thì giảm
  quota (đã chốt), không nới điều kiện.
- Giờ người ở bước 6 lớn (ước 100–120 giờ người cho cả bước 5–7) → làm theo lô 30–50 dòng, đo phút
  mỗi dòng sau lô đầu để lập lại kế hoạch.
- Dựng lại làm mất nhãn → `crosscheck.py build` đã lưu bản cũ `*.YYYYMMDD.tsv` và chỉ chuyển nhãn khi
  câu hỏi, đáp án không đổi; giữ nguyên quy tắc đó.

## Progress

- [x] Định nghĩa chốt, ADR 0003 Follow-Up, phiếu luật sư — 20/10
- [x] Bước 1: luật sư đồng ý cả 7 quy tắc pháp lý, không sửa định nghĩa — 21/10 (CMT báo)
- [x] Bước 2: hướng dẫn 3.0 — `docs/vilextime-annotation.md`; `crosscheck.py`, `crosscheck_xlsx.py`,
  `build_vilextime.py` mang GUIDELINE 3.0 và mã loại mới — 20/10
- [x] Bước 3: bộ lọc máy — 20/10. R1 trong `build_question_pool.py` (`transition_kind`, `RENAMES`,
  `_AUTO_UPDATE`; T3/T2 xếp theo số trạng thái pháp lý); R4 `restructuring_2025` và R5 `reference_only`
  trong `check_validity.py` (chỉ để người kiểm, không tự loại); R6 `pending_events.py` xét cả cấp trên;
  `subgroup` T5a/T5b, T6a/T6b; bỏ `sau_het_hieu_luc`. Dựng thử kho (thư mục tạm): R1 bỏ 2.760 ứng viên
  (2.210 chỉ hình thức, 547 chỉ đổi tên, 3 tự cập nhật dẫn chiếu); T3 còn 362 chuỗi, cả 362 có ≥ 2 lần
  sửa thực chất; R5 gắn 20 dòng của bản phát hành cũ.
- [x] Bước 4: sửa lỗi đồ thị — 20/10. Đã sửa ở `extract_provision_events.py`/`provision_ops.py`:
  §5.1 ngày hiệu lực riêng (`5877a5a`); 562 văn bản sửa đổi chỉ nhận ra qua tên (không có quan hệ trên
  cổng, vd NĐ 115/2016) giờ được đọc; nghị định sửa nhiều nghị định ghi tên văn bản bị sửa ở tiêu đề
  Chương (NĐ 14/2026: Điều 59 NĐ 05/2021 bị bãi bỏ từ 15/01/2026, §5.5; sự kiện của văn bản này 6 → 166);
  tiêu đề Điều không có ":" vẫn dẫn danh sách và lời văn mới bên dưới (`wording.py`); câu mở đầu "sửa đổi
  một số khoản của Điều X như sau:" không còn sinh sự kiện giả "sửa cả Điều X" (887 sự kiện chặn oan cả
  Điều qua R6); bãi bỏ một phần ("nội dung sau", "đoạn", "số thứ tự", "tiết", "gạch đầu dòng")
  thành `needs_review/partial_repeal` (§5.4, 41 sự kiện trước đó tự chấp nhận). §5.6 viết lại cả Điều
  khác cấu trúc: không áp tự động, sự kiện `structure_mismatch` để R6 chặn khỏi test. §5.3 (R3) và §5.7:
  người kiểm theo hướng dẫn 3.0, máy không dò. Trích thử vào thư mục tạm: 50.587 → 56.624 sự kiện (tự chấp
  nhận 16.970 → 19.295, đã đối chiếu 3.049 → 3.262, chờ người xem 30.568 → 34.067). `build_versions.py
  --target-document document:146845`: điểm a khoản 5 Điều 59 NĐ 05/2021 hết hiệu lực 15/01/2026 (trước là
  01/07/2026). `pytest` 528 qua. Dữ liệu thật chưa đổi: dựng lại ở bước 5.
- [x] Bước 5: dựng lại, xuất phiếu — 20/10. Trích sự kiện, chuỗi phiên bản, kho, corpus (BM25 + embed bù
  6.340 đoạn PhoBERT trên CPU, `verify_embed.py` OK) dựng lại trên dữ liệu thật; bản cũ lưu ở thư mục tạm.
  R1 thêm đổi tên NHNN chi nhánh, Tổng cục TĐC, Cục Thuế địa phương, Cục Hàng hải / Đường thủy nội địa,
  đổi tên một phần, chữ cái đầu dòng (948 + 2.503 ứng viên bỏ). 53 lineage D4 `khong_dat` vào `dropped.jsonl`
  (`adjudicate.py drop`); R6 chặn ngay khi xếp hạng và chọn. Quota mục 9 (`sample_vilextime.RELEASE`): T1 150,
  T2 450 (T4 150), T3 150, T5a 20 (10 lineage luật sư xác nhận, còn lại sau R6 và D4), T6a 100, T6b 250 →
  1.120 dòng ranh giới, 2.383 dòng cả dòng giữa khoảng và trước hiệu lực; `check_release.py` OK. Câu hỏi mới
  do DeepSeek viết (hết số dư ở T2 205/401, T1 0/179: chỉ thiếu câu dự trữ sau dòng chọn cuối, tập chọn
  không đổi); 123 đáp án ngắn mới do Claude viết (`short_answers.jsonl`). Phiếu `data/review/kiem_{A,B}.xlsx`
  (`crosscheck.py kiem`): A 700, B 698 dòng, 278 dòng (25%) gán đôi ngoài D4, 139 dòng mang nhãn D4,
  1.120/1.120 dòng có trích văn bản gốc, 18 lô 40 dòng; gợi ý máy ở 74 dòng của A (cờ validity, R6, đáp án
  ngắn nằm trong bản khác). Sửa kèm: `transitions_of` đọc sự kiện của phiên bản; đáp án ngắn lệch lời văn
  sau dựng lại thành "hết hạn" thay vì dừng; khóa cache truy xuất theo corpus và bộ vector.
- [x] Câu hỏi dự trữ còn thiếu (21/10, người dùng giao Claude viết thay DeepSeek): 389 lineage trong
  `sample.jsonl` (T1 179, T2 209, T3 1) do claude-opus-5-5 viết qua `generate_questions.py --answers`, cùng
  `validate()`. Giữ 316 (T1 152, T2 163, T3 1), từ chối 73: T1 27 (câu lệnh sửa đổi, mục trơn, điều khoản thủ
  tục chung), T2 46 ghi lý do ở `data/review/t2_khong_viet.tsv` (đổi tên/sắp xếp 2025 mà R1 chưa bắt, chỉnh
  câu chữ, chỉ đổi dẫn chiếu, nghi chuyển chỗ, phiên bản chỉ là tiêu đề). 5 cụm mở đầu chiếm 17,8% (T1),
  12,9% (T2). Dựng lại T1–T3 và `--select`: `selected.jsonl` trùng từng byte, bản phát hành không đổi. Dự trữ
  có câu hỏi: T1 255, T2 379, T3 119 lineage. Không còn lineage nào trong mẫu chưa có câu hỏi.
- [x] Chuẩn bị phiếu cho bước 6 theo cách làm giảm lệch (21/10, CMT: "chuẩn bị tươm tất, best practice để
  gán nhãn không bị mismatch"). Nhắm vào nguyên nhân lệch D5 §2: `scripts/review/kiem_hints.py` ghi
  `data/review/kiem_goi_y.jsonl` — cột `cac_phien_ban` (mọi phiên bản, văn bản sửa, chỗ đổi) cho 970 dòng
  nhiều phiên bản, cột `goi_y_cho_moi` cho 350 dòng T6 (văn bản bãi bỏ cũng sửa gì vào văn bản gốc; đoạn có
  hiệu lực giống nội dung bị bãi bỏ, tách nhóm mới hiệu lực quanh ngày bãi bỏ). Phiếu: lô 0 hiệu chuẩn 21
  dòng cả hai cùng làm rồi thảo luận với luật sư, không tính vào AC1 (`kappa` báo riêng); dòng gán đôi cùng
  số lô ở hai phiếu, rải đều 18 lô, để đo đồng thuận sau lô 3, 6, 9…; chữ đổi tô đỏ trong `answer`; trang
  "Cách quyết" (8 điều kiện §6 → mã). Hướng dẫn 3.0 thêm mục 5 bước 3 và mục 7 Hỏi đáp; quy tắc gán nhãn
  không đổi. Máy không điền nhãn nào. Phiếu mới: A 715, B 704 dòng (lô 0: 21 dòng chung; 278 dòng gán đôi,
  12–18 dòng mỗi lô). Sửa kèm: nạp phiếu không còn tự đổi `guideline_version` của nhãn D4 mang sang chỉ vì
  dấu cách cuối ô `note` (Excel bỏ dấu cách đó); `pytest` 537 qua.
- [ ] Bước 6: kiểm định người. Lệnh hòa giải đã có (21/10): `adjudicate.py export|import --set kiem`
  → `hoa_giai_kiem.xlsx/.tsv` + cột `adjudicated` ở `kiem_A.tsv` (nhãn thô A/B không đổi); danh sách
  gồm cả dòng lệch lô 0 (nhãn "lô 0 hiệu chuẩn"), còn `kappa` vẫn loại lô 0 khỏi AC1. `pytest` 538 qua.
  Trang gán nhãn thay Excel (21/10): `scripts/review/label_ui.py` + `label_ui.html` (`--who A|B`; 4 họ lỗi, chip điền bằng chứng, tab Tổng quan) (localhost, phím tắt, tự đo phút,
  lưu thẳng `kiem_X.tsv`, kiểm nhãn như `crosscheck_xlsx.py import`); `pytest` 539 qua.
  Chưa làm: `drop` cho phiếu `kiem` (khi đóng băng). Còn chờ người gán nhãn lô 0.
- [x] Xuất bản phát hành (21/10): `scripts/pipeline/export_release.py` theo `docs/vilextime-schema-phat-hanh.md`
  (file chính 13 cột, silver, meta, `manifest.json`; `--final` từ chối khi còn dòng chưa có nhãn cuối);
  `score_vilextime.py --release` chấm trên file công bố, trùng báo cáo nội bộ 2.383/2.383 dòng. Nhãn D4 mang sang
  (139: A 70, B 69, hướng dẫn 1.2/2.0) chỉ tính khi xác nhận lại theo 3.0 (định nghĩa §8: có dẫn chứng); trang
  gán nhãn hiện lại chúng. Bản ứng viên hôm nay: 0 dòng chính, 2.383 silver (A lô 0 xong, B chưa). `pytest` 540 qua.
- [x] Một người kiểm, sửa câu chữ ngay khi kiểm (21/10, CMT: "thời gian gấp, label chéo để sau; cần ngay bộ
  đầy đủ, tự đọc từng dòng và sửa"). `kiem_A.tsv` gộp thêm 405 dòng chỉ có ở B → đủ 1.120 dòng ranh giới (bản trước
  ở `kiem_A.20261021.tsv`). `export_release.py`: một người gán theo 3.0 là đủ, hai người lệch thì chờ hòa giải;
  `--draft` → `data/vilextime_dataset/vilextime.jsonl` đủ 2.383 dòng để đọc ngay. `label_ui.py`: sửa câu hỏi (cả lineage) và đáp
  án ngắn (cả phiên bản; phải là đoạn trích của đáp án hoặc câu dẫn), ghi vào `questions.jsonl`,
  `short_answers.jsonl` (giữ bản model, `edited_by`, `edited_at`) và phiếu TSV. Dựng lại (`build_vilextime.py` →
  `sample_vilextime.py --select` → `enrich_vilextime.py`, ~1 phút) đã thử trọn vòng trên dữ liệu thật: câu sửa tới
  cả 4 dòng của lineage, id không đổi, trả về thì trùng từng byte. `pytest` 542 qua. Còn: 1.099 dòng (139 nhãn D4
  xác nhận lại); 149 dòng ẩn vì thuộc 75 lineage gold của A.
- [x] Mẫu gán chéo thu nhỏ (21/10, CMT "ok"): `data/review/kiem_cheo.txt` 106 dòng, 60 lineage — các dòng gán đôi
  đã thiết kế (có ở phiếu A trước khi gộp) thuộc lô 1–9, trừ lô 0 và lineage của gold; T2 48, T6 28, T1 18, T3 12.
  B mở `label_ui.py --who B --ids data/review/kiem_cheo.txt`. `kappa --set kiem` và `adjudicate.py --set kiem` chỉ
  tính dòng cả hai gán theo 3.0 (69 nhãn D4 của B đã chép sang phiếu A khi gộp, không phải hai lần phán).
  `pytest` 542 qua.
- [x] Trang gán nhãn cho hai người cùng làm (23/10): `label_ui.py` thêm dòng thời gian phiên bản (một ô mỗi phiên
  bản, ghim ở mốc hỏi) và so sánh hai phiên bản cạnh nhau (T2, T4, T3, T5a). Mã phiên bản đọc từ ◀ của
  `cac_phien_ban`, khớp `release.jsonl` 1.120/1.120 dòng A và 704/704 dòng B, nên trang không còn cần
  `release.jsonl` (gitignore): partner `git pull` là chạy được. Trên dữ liệu thật: 0 dòng phiên bản đọc sót, 0 ghim
  lệch ô đáp án. `pytest` 544 qua.
- [ ] Bước 7: gold độc lập. 21/10: mẫu cũ rút trước khi dựng lại (17/120 dòng không còn trong bản phát hành,
  chưa ai gán) → rút lại 120 dòng trên bản dựng lại (`independent_gold.py build`, xuất lại `gold_{A,B}.xlsx`;
  bản cũ lưu ở thư mục tạm của phiên). Lineage đã lộ đáp án máy qua phiếu `kiem` (dòng đã gán, lô 0) bị loại
  khỏi mẫu; `label_ui.py` ẩn lineage trong phiếu gold của mỗi người tới khi phiếu gold điền xong (A: ẩn 83 dòng),
  để gold vẫn mù khi hai việc làm song song. `pytest` 541 qua.
- [ ] Bước 8: đóng băng

## Decisions

- 2026-10-20: một bản định nghĩa duy nhất, không chia phiên bản v1.0/v1.1 (CMT).
- 2026-10-20: thêm R6 (dòng có sự kiện chưa áp chưa vào test); CMT trả lời "ok" cho câu hỏi giữ R6 cùng
  lúc cho commit bước 2–4.
- 2026-10-21: người thứ ba hòa giải dòng lệch của phiếu kiểm (A/B) là **luật sư** (CMT); cột `adjudicator`
  ghi tên luật sư. Câu hỏi dự trữ còn thiếu do Claude viết thay DeepSeek (CMT).

- 2026-10-21: gán chéo giữ lại nhưng thu nhỏ: B gán độc lập 106 dòng (thay 25% = 278 dòng của định nghĩa §8),
  luật sư hòa giải dòng lệch, báo AC1/κ (CMT đồng ý). Đề cương chỉ ghi "kiểm định chéo dữ liệu và đánh giá độ đồng
  thuận", không ghi tỷ lệ, nên vẫn khớp đề cương; chỗ lệch là với định nghĩa §8, ghi vào datasheet khi đóng băng.
  Gold độc lập 75 dòng của A: làm nếu kịp.
- 2026-10-21: một người kiểm toàn bộ trước, gán chéo 25% + AC1 làm sau (CMT). Chưa làm thì paper ghi "một người
  kiểm, chưa đo đồng thuận" — lệch định nghĩa §8. Người kiểm sửa thẳng câu hỏi và đáp án ngắn (trước là chỉ đề
  xuất ở `suggestion`); lời văn luật, ngày, phiên bản không sửa tay, sai thì khong_dat (CMT đồng ý hướng này khi giao
  "đọc từng dòng rồi chỉnh sửa").
- 2026-10-21: nhãn D4 mang sang phải xác nhận lại theo 3.0 mới vào bản phát hành (Claude, theo định nghĩa §8;
  dòng T2 mốc 14/01/2026 đáp án "cấp huyện" mang nhãn D4 `dat`). CMT bác thì đổi một dòng ở `final_labels`.
- 2026-10-21: chốt schema phát hành `docs/vilextime-schema-phat-hanh.md` (2 file, 12 cột chính, `2.0.0`, không công bố dòng bị loại); 5 quyết
  định mở dùng mặc định Claude đề xuất (CMT: "chốt schema cuối cùng đi").
- 2026-10-23: không host lên Vercel; mỗi người chạy `label_ui.py` trên máy mình, nhãn đồng bộ qua git (CMT chọn).
  Lý do: Vercel cần thêm database, đăng nhập, chia nhỏ dữ liệu (trang tải 7,6 MB, giới hạn 4,5 MB mỗi phản hồi) và
  đưa bộ test chưa công bố lên internet.
- 2026-10-24: lô 0 hiệu chuẩn xong. 12/21 dòng lệch; luật sư tự chốt (không dùng AI, CMT xác nhận) cả 12 là
  `khong_dat`; sáu kết luận ghi ở hướng dẫn §7 (`docs/hoa_giai_lo0_chot.xlsx`). B gán lô 1–9 trước buổi hiệu chuẩn,
  trái hướng dẫn §5 mục 3; nhãn thô vẫn giữ.
- 2026-10-24: bốn ô dẫn chứng (`da_xem_van_ban_tac_dong`, `cham_lan_sua`, `noi_dung_con_o_dau`, `phut`) chỉ bắt
  buộc với A; B chỉ đo đồng thuận nên chỉ cần `verdict` (CMT). `missing_fields(..., who)`. Phiếu B nạp 381 nhãn;
  một mã gõ sai `question_ambiguou` → `question_ambiguous` sửa khi nạp (Claude). Hệ quả: không có `phut` của B.
- 2026-10-24: hướng dẫn 3.0 viết gọn lại theo tám bước, không đổi quy tắc; AC1 ghi "chọn sau pilot 07/10" thay
  "đăng ký trước" ở hướng dẫn, D5, datasheet, `*_result.json` (khóa `gate`), lệnh `kappa` (G6).
- 2026-10-24: quét `effect_split_scan.py` (21 văn bản, 29 lineage hiệu lực tách phần) và `diacritic_scan.py`
  (91 chỗ, 14 lineage); phiếu luật sư `data/review/gui_luat_su_2410.xlsx` gồm 21 lineage sắp xếp 2025 (G8)
  và 29 lineage hiệu lực tách phần. Kết luận theo từng lineage không đưa cho A/B trước khi họ gán các dòng đó.
- 2026-10-25: gán trên một link cố định thay cho mỗi người tự chạy (CMT, đổi quyết định 23/10): Artifact riêng tư trên
  claude.ai https://claude.ai/artifact/Q6ckAyZ3ULLPpXV64MdbrB, chỉ người được chia sẻ mở được. `label_ui.py --web`
  dựng trang (phiếu A cả phiếu, B dòng gán chéo; dòng gold vẫn ẩn), nhãn lưu ở database của trang (`kiem_A`,
  `kiem_B`); kéo về bằng ArtifactData `query` theo `lo` với `out_dir` rồi `label_ui.py --who X --pull <dir>`, đi qua
  đúng `save()`. Phiếu kiểm chưa công bố vì vậy nằm trên claude.ai (CMT chấp nhận). Khi gold của A điền xong, hoặc khi
  nhãn ở TSV đổi ngoài trang, phải dựng và đăng lại trang. Chế độ chạy máy cục bộ giữ nguyên, thêm mật khẩu tùy chọn
  (`LABEL_UI_PASSWORD`).
- 2026-10-26: kéo 950 nhãn A (lô 1–18, gán 25/10 trên trang) về `kiem_A.tsv`. CMT xác nhận A tự gán, Claude chỉ
  viết nháp ghi chú (288 note có "[Claude nháp]"). Ghi lại cho biên bản D5: cả 950 nhãn lưu trong 4 giờ 45 phút,
  trung vị khoảng 5 giây giữa hai lần lưu (491 lần dưới 5 giây), `phut` = 1 ở 946 dòng, 92,5% `dat`. 12 dòng đổi từ
  `dat` sang `khong_dat` so với nhãn cũ trong phiếu. 149 dòng thuộc lineage gold vẫn ẩn vì `gold_A` còn 0/75.
- 2026-10-26: đo `kiem` sau khi kéo nhãn: 246 dòng chung, AC1 0,377 (T1 0,88; T2 0,27; T3 0,38; T6 0,22), chưa đạt;
  89 dòng lệch ngoài lô 0 xuất ra `hoa_giai_kiem.xlsx` (cùng 12 dòng lô 0). CMT yêu cầu agent `vn-law-verifier` kiểm
  trước 89 dòng: kết quả ở `data/review/hoa_giai_kiem_claude.tsv` (nghiêng B 72, A 14, chưa rõ 2, cả hai sai mã 1;
  21 dòng phân vân). Đây là phiếu tham khảo của model, không điền vào `chot_*`. §8 hướng dẫn nói hòa giải không dùng
  AI; nếu đưa file này cho luật sư thì biên bản D5 và cột `adjudicator` phải ghi luật sư có Claude hỗ trợ.
  Luật sư đọc phiếu và đồng ý, chốt thêm ba quy tắc (§7 hướng dẫn); nạp `hoa_giai_kiem.tsv` 101 dòng (12 lô 0 +
  89; 83 `khong_dat`, 18 `dat`), `adjudicator` = "luật sư Nguyễn Văn A (bí danh), có phiếu Claude hỗ trợ" vì luật
  sư không muốn nêu tên. AC1 đo trên nhãn thô nên không đổi (0,377, chưa đạt).
- 2026-10-24: dọn 30 file lỗi thời (bản cuối ở git `e023e55`); đề cương KLTN không bao giờ xóa (CMT).

## Validation

- Focused proof: test cho từng bộ lọc (một ca dương, một ca âm lấy từ ví dụ mục 10 của định nghĩa).
- Integration: `check_release.py` OK; bảng cơ cấu so với mục 9; đếm dòng theo mã loại.
- Repository-required checks: `pytest` toàn bộ.

## Result

(Điền khi xong.)
