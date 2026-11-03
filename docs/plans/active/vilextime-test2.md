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
- [x] 29/10 bước 2, lần 1 (lời dặn v1 `e524774ebc8e2d33…`): `result.tsv` đủ 653 mục. Chấm 31/10:
  loại đúng 0,96 (27/28), loại nhầm **0,42** (17/40) → **chưa đạt** (ngưỡng ≤ 0,30). Theo nhóm, loại nhầm: T2
  0,28; T2 gần giống 3/3; T3 3/4; T6 cấp trên 4/8. Ứng viên giữ 178/585 (T2 72, T2 gần giống 17, T3 71, T6 cấp
  trên 7, T6 đích danh 11).
  Nguyên nhân: 10/17 câu tốt bị loại nhầm mang `transitional_rule`, đều là chuyển tiếp giữ việc phát sinh
  **trước** ngày hiệu lực (hồ sơ đã tiếp nhận, hành vi đã xảy ra). Định nghĩa §1 không loại các ca này; lời
  dặn v1 điều 5 viết quá gọn nên bị đọc rộng. Ở ứng viên: 169 mục loại vì `transitional_rule`, ≥ 133 thuộc kiểu
  này. Chẩn đoán (cùng tập, không phải lần 2): coi mọi `transitional_rule` là giữ thì 0,86 / 0,17. 3 câu T6 tốt
  bị loại vì `relocation_unclear` là đúng chủ ý "không chắc thì loại".
- [x] 31/10: lời dặn v2 `a6b648d6223047c6…` (Claude): chỉ viết lại điều 5 theo định nghĩa §1, có ví dụ. Bản
  v1 giữ trong git (`8cfcd9a`).
- [x] 31/10: CMT chọn chấm lần 2 trên **cùng 68 lineage hiệu chuẩn** (mọi lineage có nhãn người độc lập đã
  dùng ở lần 1; phần còn lại là nhãn một người, nhãn Codex hoặc có phiếu Claude). Khóa luận phải ghi: lần 2
  không có tập giữ riêng; lời dặn chỉ sửa một điều cho khớp định nghĩa, không chỉnh theo điểm.
- [x] 31/10: `test2_packs.py redo --out ~/vilextime_loc/gan2/packs --from ~/vilextime_loc/gan/packs
  ~/vilextime_loc/gan/result.tsv` → 237 mục (68 hiệu chuẩn + 169 ứng viên loại vì `transitional_rule`), 10 gói,
  trộn lại, kèm `HUONG_DAN.md` v2. Ứng viên khác giữ quyết định lần 1 (v2 chỉ nới điều 5). `pytest` 568 qua.
- [x] 02/11 bước 2, lần 2 (lời dặn v2): phiên `claude -p` mới trong `~/vilextime_loc/gan2`, Sonnet 5.5 như lần 1,
  cùng câu lệnh, 22 phút, đủ 237 mục. Log phiên không có đường dẫn tới khóa hay repo. Không tra web (lần 1 cũng
  không), nên T6 không chắc đều rơi vào `relocation_unclear`. Chấm: loại đúng **1,00** (28/28, Wilson 95% [0,88; 1,00]),
  loại nhầm **0,28** (11/40, [0,16; 0,43]) → **đạt**, sát ngưỡng: thêm một câu tốt bị loại là không đạt. Loại nhầm theo
  nhóm: T2 0,12 (3/25); T2 gần giống 3/3; T3 1/4; T6 cấp trên 4/8. Ứng viên giữ 244/585 (T2 93, T2 gần giống 24, T3
  107, T6 cấp trên 7, T6 đích danh 13). Phiên lọc không dùng `transitional_rule` lần nào: 66 mục từng bị loại vì mã này
  được giữ (12 mục có dấu vết thời hạn, đọc tay đều là chuyển tiếp giữ việc cũ), 103 mục chuyển sang mã khác; 7 câu
  hiệu chuẩn đổi quyết định, 6 ở mã này, 1 câu xấu lần 1 bỏ sót.
- [ ] Bước 3, đợt 2: T6 giữ 13% nên chưa đủ. `test2_packs.py build --second --out ~/vilextime_loc/gan3/packs` → 1.012
  mục, 41 gói: 68 hiệu chuẩn + 944 ứng viên (T2 120, T2 gần giống 40, T3 184 là hết kho, T6 mỗi kiểu 300), kiểm tái lập
  đợt 1 qua; rồi lọc bằng phiên mới như lần 2. 68 câu hiệu chuẩn lặp lại để phiên lọc vẫn
  không biết mục nào bị chấm, và cho số đo độ ổn định cùng lời dặn. Cổng của bước 2 chốt ở số lần 2; số này chỉ báo.
  Dở 02/11: phiên lọc `gan3` dừng vì hết hạn mức 5 giờ (mở lại 7:00 UTC), `result.tsv` có 125/1.012 mục, log không chạm khóa
  hay repo. Chạy tiếp: phiên mới trong `gan3`, chỉ làm mục chưa có trong `result.tsv`, Sonnet 5.5. Chấm: `score --out
  ~/vilextime_loc/gan3/packs ~/vilextime_loc/gan/result.tsv ~/vilextime_loc/gan2/result.tsv ~/vilextime_loc/gan3/result.tsv`.
- [x] 02/11 bước 4, chuẩn bị: `test2_packs.py qpack|qcheck`, lời dặn `prompts/vilextime/test2_cau_hoi.md` (ghép với
  `base.md`, `T2/T3/T4/T6.md`). `qcheck` dùng lại `validate()` của `generate_questions.py` và thêm `copy_share` (cùng cách
  đo G7 của DATASET_GAP; bộ câu cũ trung vị 0,71, chỉ 11% đạt ≤ 40%). Thử 25 mục, phiên riêng Opus 5.5. Bản 1 xúi "lời
  thường": trùng chữ quá thấp, ra từ tự chế ("biên lai nhà băng"), hại Q3 và làm BM25 thua giả tạo. Bản 2 giữ thuật ngữ
  chuẩn, coi 40% là trần: trung vị 0,32, 22/25 qua, 2 từ chối, 1 phải viết lại; đọc tay ổn.
- [ ] Bước 4: viết câu hỏi cho mọi ứng viên giữ, ra `data/vilextime/questions_test2.jsonl`.
- [ ] Bước 5: trang gán theo câu hỏi; lô 0; gán đôi; đo AC1 từng Q.
- [ ] Bước 6–7: hòa giải, đóng băng, amendment ADR 0005, chạy.

### Tiếp quản Codex — 02/11/2026

- CMT xác nhận tiếp tục **test2 theo kế hoạch đã duyệt**, Claude Code đang hết usage. Giữ nguyên kết quả Claude
  ở `~/vilextime_loc/gan{,2,3}`. CMT sau đó quyết định: **"Codex làm nốt đi, rồi cứ ghi llm chung là được"**.
  Codex tiếp quản lọc/viết; phần trình bày chung gọi `LLM`, hồ sơ kỹ thuật giữ nguồn thực tế khi biết, nếu chưa
  xác minh được thì ghi rõ chưa biết. Hiệu chuẩn mù Codex riêng, không kế thừa số đo Sonnet 5.5.
- Đã giao ba worker Codex **phiên mới không kế thừa hội thoại**, chỉ đọc thư mục riêng
  `/tmp/vilextime-test2-codex/filter_calibration/worker_{1,2,3}`: 80 mục trộn ngẫu nhiên (68 hiệu chuẩn
  cũ + 12 ứng viên mới; không đưa khóa, vai trò hay kết quả Claude cho worker). Prompt giữ nguyên v2,
  SHA256 `a6b648d6223047c6a4529a2aa906128bc24d435336f7ed08bd9aabd9dcf3227a`.
  Đây là kiểm khả năng của model mới trên tập đã có; không phải tập kiểm định giữ riêng của cả dự án.
- Hiệu chuẩn Codex lần đầu theo prompt v2 **ĐẠT**: bắt đúng 28/28 mục xấu, loại nhầm 12/40 mục tốt
  (0,30, **sát đúng trần**). Theo tầng: T2 thường loại nhầm 3/25, gần giống 2/3, T3 2/4, T6 cấp trên 5/8;
  mẫu xấu T2 thường bằng 0. Không sửa prompt hoặc chạy lại để chọn số tốt hơn. 12 ứng viên trộn kèm giữ 3
  (gần giống 1, T3 2), chỉ là quyết định lọc. Lưu toàn bộ 80 kết quả và receipt ở
  `data/review/test2_filter_codex/calibration.tsv`, `calibration.json` (không phải nhãn A/B).
- Đợt 2 sau khi nối 125 kết quả Claude và 80 kết quả hiệu chuẩn Codex: còn 814 ứng viên chưa lọc; chặn 1
  văn bản dev → **813 mục**, chia 7 gói (6×120 + 93), tại
  `/tmp/vilextime-test2-codex/filter_remaining/batch_{01..07}`. Chỉ chuyển tiếp kết quả đã kiểm cấu trúc;
  lưu riêng nguồn Codex, không ghi đè `~/vilextime_loc/gan3/result.tsv`.
- Viết câu hỏi song song từ 242 ứng viên đợt 1 hợp lệ: 24 đã có kết quả thử (22 đạt, 2 từ chối), còn
  **218 mục** tại `/tmp/vilextime-test2-codex/question_writers/worker_{1,2,3}` (73/73/72). Không dùng lại
  câu bị từ chối để chạy đến khi đạt. `qcheck --provider codex --model 'Codex (model identity unavailable)'`
  ghi đúng nguồn nội bộ, không mặc định nhầm thành Claude. Hai lượt viết lại chỉ dành cho câu bị kiểm tự
  động loại mà không phải `KHONG_DU_NGU_CANH`, giữ đầy đủ lịch sử lượt viết.
- **Ngắt usage Codex, 02/11 lúc trước 08:21 UTC:** ba worker bị chặn, thông báo hẹn mở lại **09:01 UTC**.
  Không đổi model/nhà cung cấp để né hạn mức. Đã phục hồi 89/120 quyết định batch01 và 48/120 batch02,
  kiểm cấu trúc và sao lưu nguyên byte vào `data/review/test2_filter_codex/batch_01_partial.tsv`,
  `batch_02_partial.tsv`. Còn **676/813** ứng viên chưa lọc; mỗi batch đã có `remaining.jsonl` trong thư mục
  tạm để chỉ giao mục thiếu sau khi hạn mức phục hồi. Không tự gán trong phiên điều phối đã biết khóa.
- Đã hoàn tất biên soạn và kiểm tự động **242/242** ứng viên đợt 1: giữ 77 câu (T2 43, T3 28, T6 6),
  165 từ chối hoặc hết lượt kiểm. `data/vilextime/questions_test2.jsonl` lưu cả câu đạt và thất bại;
  đây **chỉ** là kết quả biên soạn của đợt 1, chưa phải tập test2 final. 218 câu Codex có đủ lượt gốc và
  tối đa hai lượt viết lại ở `data/vilextime/test2_generation/first_{1,2,3}/answers_{1,2,3}.jsonl`;
  ngưỡng 40% và thuật ngữ chuẩn giữ nguyên, không thêm chữ để vượt kiểm.
- Bổ sung kiểm tương phản trước phiếu A/B theo **định nghĩa §4**: T2 không cho đáp án ngắn nằm trong bản
  kia; T3 cần ít nhất ba đáp án khác nhau. `test2_prepare.py contrast` chỉ là chẩn đoán máy, không phải
  nhãn người. Phiếu thử 22 câu/47 đáp án đã có **22/22** qua kiểm này. Test dương/âm mới chứng minh một
  đoạn trích có thật nhưng cũng nằm trong bản kia bị chặn, không đổi lời luật để tạo khác biệt.
- Phần không cần worker mù đã làm tiếp trong khi chờ usage: trích **129 phiên bản mới** cho 55 câu
  Codex, nối 47 phiên bản thử trước thành `data/vilextime/short_answers_test2.jsonl` (**176 bản ghi**).
  12 bản ghi để `null` ở 6 lineage T2 vì không có đoạn trích riêng giữa hai bản (bản này bao hàm bản kia);
  không viết thêm câu phủ định ngoài lời luật. Mọi lựa chọn là biên soạn LLM, chưa phải nhãn người.
- Sửa hai câu hỏi trước khi giao người: mốc bắt đầu phải là **ngày cơ quan nhận đủ hồ sơ**, không phải
  lúc nộp; trường hợp giới hạn tịch thu phụ thuộc mức phạt thì hỏi **cách xác định giới hạn**, không ép
  nguồn gián tiếp thành một con số chưa có. Cả hai còn lượt viết lại, đã qua `judge_question()`; giữ đầy
  đủ câu cũ/lý do trong `data/vilextime/test2_generation/semantic_revisions_20261102.jsonl`, nguồn sửa
  đi cùng `question_source`. Không sửa lời văn pháp luật hoặc nhãn người.
- Chốt được **71 ứng viên có câu hỏi và đáp án ngắn qua kiểm máy** (T2 37, T3 28, T6 6), **170 mốc**,
  164 đáp án trích không-null. Phiếu: `data/review/test2_candidate_worksheet.jsonl`; receipt ở
  `test2_candidate_worksheet.manifest.json`, SHA256
  `2233b7d3c9b168cbdfbe1ab03784734da69e020a550dcf8e82f5cc4ed71e5783`.
  Có link gốc cho 99 trích văn bản tác động. Phiếu này **chưa phải lô 0**, không có nhãn A/B và không
  phải bản phát hành. Sáu lineage bị chặn ở chẩn đoán `data/review/test2_short_contrast_v2.json`
  (kèm hash câu hỏi/đáp án đầu vào); vẫn giữ trong phễu, chưa ghi vào nhãn `khong_dat` của người.
- Kiểm sau tiếp quản: toàn repo **591 passed**; sau chỉnh kiểm “T2 đúng hai đáp án”, 27 test tập trung
  qua; `git diff --check` qua. v1.0 vẫn đúng hash `7cf51ee6…`. Công việc còn phụ thuộc worker mù: **676**
  ứng viên chưa lọc, rồi viết/trích câu mới từ phần được giữ. Các cổng người, Q4 và amendment chưa đóng.
- **Đối chiếu checkpoint sống lúc 08:57 UTC:** `~/vilextime_loc/gan3/result.tsv` đã có **825** mục,
  không còn 125 của checkpoint trước. File được bổ sung lúc 07:01–07:42 trong phiên Claude
  `7c728d65-5cc5-47bf-96f3-da4b607d72d5`; log báo `claude-sonnet-5-5`, prompt đúng hash v2. Quét tham số
  tool không thấy các đường dẫn khóa/nhãn/repo đã liệt kê; đây là quan sát log, không chứng nhận sandbox.
  Snapshot cố định `data/review/test2_filter_claude_round2_825.tsv`; đối chiếu mô tả ở
  `data/review/test2_filter_overlap.json`: 168 mục trùng Codex, 27 quyết định khác nhau, giữ cả hai bản gốc.
  Thứ tự đọc khi tiếp tục là kết quả Claude rồi các kết quả Codex đã giao tiếp quản; không sửa file gốc và
  không gọi hai model là hai người gán hay coi đây là đồng thuận người.
- Số **676** trên là phần thiếu nếu chỉ đọc checkpoint Claude cũ. Lệnh `pending` đối chiếu snapshot825,
  calibration Codex và 137 mục Codex đã lưu cho ra **138 mục** còn thiếu; prompt sao chép nguyên byte,
  không rút lại mẫu, không sửa kết quả. Gói `/tmp/vilextime-test2-codex/resume_138/worker_{1,2}`,
  mỗi gói 69 mục, chỉ giao sau khi tới mốc phục hồi 09:01 UTC; hai worker đã chạy lại được.
- Phần đã có kết quả lọc hiện giữ **378 ứng viên hợp lệ** sau chặn văn bản dev. Đợt1 đã xử lý242;
  136 mới nằm ở `/tmp/vilextime-test2-codex/questions_second_known`. Lượt đầu đã đủ136:33 qua,
  9 từ chối,94 cần viết lại theo cùng cổng40%, lịch sử ở
  `data/vilextime/test2_generation/second_known/`. Chưa cộng các câu này vào phiếu71 cho đến khi đủ đáp án.
- Bổ sung `test2_packs.py pending` để phục hồi sau usage bằng đối chiếu ID thực tế. Test cho phép giữ
  ứng viên mới, bỏ mục đã làm/hiệu chuẩn/dev, giữ nguyên thứ tự và byte prompt, từ chối ghi đè thư mục;
  **28 test tập trung qua**. Lệnh hồi phục từ snapshot825, calibration.tsv và hai partial.tsv đã được chạy
  thực tế, ra138mục. Không dùng số trong plan thay cho kiểm file sống khi nối phiên.
- Phát hiện rò văn bản dev: `build()` lấy danh sách dev từ riêng các lineage T2/T3/T6, bỏ sót văn bản chỉ
  có T1 ở dev. Đối chiếu **toàn bộ** v1.0 + metadata: dev có 73 văn bản; ứng viên đợt 1 vi phạm 2,
  đợt 2 vi phạm 1. `published_scope()` nay lấy văn bản từ metadata v1.0 của mọi nhóm. Không dựng lại hay sửa
  khóa/kết quả các đợt lịch sử (thứ tự rút sẽ đổi); chặn các mục này tại `qpack` và `test2_prepare.py`.
  Căn cứ: Decisions 29/10 và Context của chính plan này, bỏ văn bản dev và lineage v1.0.
- `qpack` trên kết quả hoàn chỉnh đợt 1 + lượt sửa v2: 244 giữ → **242 mục / 10 gói** ở
  `/tmp/vilextime-test2-codex/cau_hoi/packs`; 2 mục bị chặn ghi trong `../excluded_scope.jsonl`.
  Đây là gói tạm, có thể dựng lại; **không** phải toàn bộ ứng viên cuối cùng (gan3 còn thiếu 887 mục).
- Bổ sung bước nối còn thiếu giữa viết câu hỏi và Q1: `test2_prepare.py shortpack` dùng **câu hỏi mới**
  để giao trích đáp án ngắn cho mọi phiên bản; `worksheet` chỉ nhận đoạn nằm trong lời văn/câu dẫn, có
  `by`/`at`, đủ trích nguồn, không mang nhãn/model nguồn cũ sang. Không tự dùng đáp án của câu hỏi v1.0.
  Gói thử từ 22 câu Claude đã qua `qcheck`: **47 phiên bản**, tại
  `/tmp/vilextime-test2-codex/dap_an_ngan_thu/tasks.jsonl`. Đáp án ngắn của Codex, nếu có, chỉ là đầu vào
  biên soạn, ghi nguồn riêng, **không** thay nhãn của A/B hay luật sư.
- Công cụ bước 5: `scripts/review/test2_labels.py`, `test2_label_ui.html`: mọi mốc của cùng câu hỏi;
  tô thay đổi và đáp án ngắn; Q1–Q4, mã loại theo thẻ 4.0, câu trích bắt buộc; T6 Q4 Không cần nhật ký tìm
  chuyển chỗ. Từng tiến trình A/B chỉ đọc và ghi phiếu của chính mình. Nhãn gắn hash câu hỏi/đáp án/nguồn;
  thay phiếu thì nhãn cũ bị từ chối, không bị tái dùng. Chưa tạo hoặc sửa nhãn người.
- **Chưa chọn thay CMT:** Q4 có ba mức (`Không`, `Có`, `Không chắc`) nhưng kế hoạch chưa định nghĩa cách
  tính `p_neg` cho ba mức. `report` báo AC1 ba mức, thỏa thuận từng mức và chẩn đoán nhị phân gộp hai đáp án
  bất lợi; cổng Q4 để `unresolved_q4_categories`, không tự cho qua. Cần chốt trước cổng 50 câu.
- Gói thử đã dựng xuyên suốt: giữ nguyên 24 kết quả `qcheck` thử của Claude (22 câu đạt, 2 từ chối) ở
  `data/vilextime/questions_test2_trial.jsonl`; 47 đáp án ngắn do Codex trích ở
  `data/vilextime/short_answers_test2_trial.jsonl` (`by: Codex (model identity unavailable)` vì worker không
  có tên model được xác minh). Cả 47 đều qua phép kiểm trích đoạn, **chưa được người kiểm nghĩa**.
  Phiếu thử `/tmp/vilextime-test2-codex/worksheet_thu_v2.jsonl`: 22 câu / 50 mốc (T2 13, T3 6, T6 3),
  có đủ link gốc cho 28 trích văn bản tác động, lấy từ `temporal.sqlite` mở read-only.
  SHA256 `752b48b50466204cf26088650986b28af374c4475dd0e19acd0627eb113c32b1`.
  Đây chưa là lô 0 và không phải bản release; chưa có nhãn A/B. Có thể dựng lại bằng `worksheet` từ hai
  file `*_trial.jsonl` đã lưu và hai file evidence gốc, không cần gọi model lại.
- Kiểm đã chạy: 24 test tập trung (gói lọc/chuẩn bị/nhãn) qua; toàn repo **588 passed**. `git diff --check`
  qua. Test dương/âm chứng minh văn bản dev chỉ có T1 bị loại, ứng viên hợp lệ vẫn được giữ; v1.0 và kết quả
  lọc gốc không bị đổi. `node --check` JavaScript qua; smoke-test HTTP thật trên loopback qua mở trang,
  đọc trạng thái, lưu và đọc lại nhãn A, không tạo nhãn B; chỉ dùng dữ liệu giả trong thư mục tạm và đã dừng
  server/xóa dữ liệu giả. Chưa kiểm giao diện bằng trình duyệt. Hash v1.0 vẫn `7cf51ee6…`.
  Chưa thấy cấu hình CI/pre-commit gọi kiểm này trong repo; hook cục bộ và branch protection chưa xác minh.

#### Lệnh tiếp tục phần chuẩn bị và gán nhãn

Chạy từ repo bằng `.venv/bin/python`. Dùng thư mục đầu ra mới để không ghi đè phiếu đã có nhãn.
Gói `/tmp` là tạm; đầu vào gốc vẫn ở `~/vilextime_loc` và dữ liệu repo.

```bash
# Chốt câu hỏi bằng qcheck trước; câu hỏi mới cần đáp án ngắn riêng.
.venv/bin/python scripts/review/test2_prepare.py shortpack --questions QUESTIONS.jsonl --out NEW_SHORT_TASK_DIR
.venv/bin/python scripts/review/test2_prepare.py worksheet --questions QUESTIONS.jsonl --shorts SHORT_ANSWERS.jsonl --evidence ~/vilextime_loc/evidence.jsonl ~/vilextime_loc/evidence_2.jsonl --out NEW_WORKSHEET.jsonl
# Sau khi chọn lô 0 và luật sư xem thẻ: hai phiên riêng, cùng phiếu, hai tệp nhãn riêng.
.venv/bin/python scripts/review/test2_labels.py serve --worksheet PILOT_WORKSHEET.jsonl --labels-dir data/review/test2 --who A
.venv/bin/python scripts/review/test2_labels.py serve --worksheet PILOT_WORKSHEET.jsonl --labels-dir data/review/test2 --who B
.venv/bin/python scripts/review/test2_labels.py report --worksheet PILOT_WORKSHEET.jsonl --a data/review/test2/test2_A.tsv --b data/review/test2/test2_B.tsv
```

Server chỉ lắng nghe loopback, cổng mặc định A 8775/B 8776; mở đúng link của người gán, Ctrl-C dừng đúng
tiến trình đã khởi chạy. Không chạy trực tiếp trên phiếu thật khi đang smoke-test: dùng phiếu và thư mục
nhãn giả trong `/tmp`, cổng tạm riêng. Chưa mở ra mạng ngoài. Lô 0 cần `batch: 0`; lô sản xuất `batch >= 1`.
Chuẩn bị phiếu **chưa** tự chọn 20 câu lô 0, chưa cho phép vượt cổng luật sư hoặc cổng đồng thuận.

### Bàn giao lại cho Codex — 02/11/2026 (Claude, sau khi hết usage lần 1)

Đã làm (Claude, Sonnet 5.5):
- **Lọc xong 100% ứng viên.** 138 mục còn thiếu lọc bằng phiên mù mới (thư mục không có khóa/repo), lưu
  `data/review/test2_filter_codex_resume138_by_claude.tsv` (38 giữ, 100 loại). Tên file nói "codex" chỉ vì đó là
  phần Codex đang dở; **nguồn là Claude Sonnet 5.5**. Kiểm `pending` ra 0 mục thiếu. `/tmp/vilextime-test2-codex/`
  đã mất (khởi động lại WSL): đừng tìm lại, dựng lại bằng lệnh dưới.
- `qpack` trên toàn bộ kết quả lọc → **174 mục giữ chưa nằm trong 242 mục đợt 1**: 136 đã có lượt viết đầu
  (`test2_generation/second_known/`, 33 qua, 9 từ chối, 94 cần viết lại) + **38 mục mới chưa có câu hỏi**.
  Một phiên Claude đang viết 38 câu này ở thư mục tạm; nếu `/tmp` còn, kết quả ở `.../scratchpad/q/w/answers.jsonl`.

Việc Codex làm tiếp, theo thứ tự (mỗi việc dùng thư mục đầu ra mới, không ghi đè):
1. Dựng lại gói: `test2_packs.py qpack --out DIR/packs --key ~/vilextime_loc/key_loc.tsv` + các file kết quả lọc theo thứ
   tự: `test2_filter_claude_round2_825.tsv`, `test2_filter_codex/{calibration,batch_01_partial,batch_02_partial}.tsv`,
   `test2_filter_codex_resume138_by_claude.tsv`. Bỏ mục đã có trong `questions_test2.jsonl` hoặc `second_known/answers_1.jsonl`.
2. Viết câu hỏi cho 38 mục mới (nếu chưa có `answers.jsonl` của Claude); viết lại 94 mục của `second_known` (tối đa hai
   lượt, cùng cổng 40%). Chạy `qcheck` rồi ghi vào `questions_test2.jsonl`. Không chạy lại để chọn câu đẹp hơn.
3. `test2_prepare.py shortpack` → trích đáp án ngắn → `worksheet`. Thêm vào phiếu71 để thành phiếu đầy đủ.
4. `pytest -q`, `git diff --check`, kiểm hash v1.0 `7cf51ee6…`. Dừng ở diff, CMT commit.

Không thuộc Codex, chờ người: luật sư xem thẻ 4.0; chọn 20 câu lô 0; A/B gán đôi; CMT chốt cách tính `p_neg`
Q4 ba mức; amendment ADR 0005. Cỡ đợt: giữ ~520 câu, sức người 430, cắt ở bước 5.

#### Checkpoint Codex — 02/11/2026 (chưa hoàn tất bước 4)

- Dựng lại `qpack` từ đúng năm file lọc theo thứ tự bàn giao tại
  `data/vilextime/test2_generation/second_new/qpack_rebuilt_20261102/`: 174 ứng viên giữ sau chặn scope.
  Đối chiếu ID xác nhận 136 mục đúng bằng `second_known/answers_1.jsonl`, 38 mục đúng bằng
  `second_new/answers_1.jsonl`, không trùng 242 câu đã có. Bản gói chỉ 38 mục mới để kiểm nằm ở
  `data/vilextime/test2_generation/second_new/qcheck_20261102_r2/packs/`.
- `qcheck` một lượt trên 38 câu Claude có sẵn, provenance `claude-code` / `Claude Sonnet 5.5`, cho
  8 đạt, 2 `insufficient_context`, 27 `copy_share`, 1 `copies_the_answer`; 10 kết quả chốt (gồm từ chối)
  ở `.../checked_1.jsonl`, 28 mục cần viết lại ở `.../viet_lai.jsonl`. Theo bàn giao, **không viết lại
  38 câu này**; chưa nối chúng vào `questions_test2.jsonl` khi chưa có cách ghi các mục không đạt mà vẫn
  giữ đúng nghĩa một lượt qcheck.
- `qcheck` lượt đầu của 136 mục `second_known` tái lập: 33 đạt, 9 `insufficient_context`, 94
  `copy_share`; gói và receipt tại `data/vilextime/test2_generation/second_known/qcheck_20261102/`.
  Codex (CLI báo model thực tế `gpt-5.6-terra`, còn hồ sơ qcheck phải ghi theo nhãn được duyệt
  `codex` / `Codex (model identity unavailable)`) đã viết lại được 16/94 ở
  `rewrite_chunk_01/answers_2.jsonl`. Các phiên sau đọc gói nhưng kết thúc trước khi ghi file;
  không có kết quả một phần và không được tính là lượt viết lại.
- **Dừng do phiên viết Codex không còn trả file đầu ra sau gói đầu**, chưa chạy qcheck lượt 2, chưa
  ghi `questions_test2.jsonl`, shortpack/đáp án ngắn/worksheet mới, hoặc pytest/hash cuối. Không commit,
  tag hay push.
- Lệnh tiếp tục sau khi khôi phục khả năng viết của Codex: dùng từng thư mục
  `data/vilextime/test2_generation/second_known/qcheck_20261102/rewrite_small_{01..10}/` (8 mục/gói,
  riêng gói 10 là 6), chỉ đọc `HUONG_DAN.md` và `tasks.json`, ghi `answers_2.jsonl`; gói 01 chưa có
  đầu ra nên vẫn làm đủ 78 mục. Sau khi đủ 94, gom các `answers_2.jsonl` (và 16 dòng
  `rewrite_chunk_01/answers_2.jsonl`, không dùng các thư mục `rewrite_chunk_02..06` không có output)
  rồi chạy:

  ```bash
  .venv/bin/python scripts/review/test2_packs.py qcheck \
    --out data/vilextime/test2_generation/second_known/qcheck_20261102/packs \
    --provider codex --model 'Codex (model identity unavailable)' \
    --dest NEW_QUESTIONS.jsonl \
    data/vilextime/test2_generation/second_known/answers_1.jsonl ANSWERS_2.jsonl
  ```

  Chỉ sau đó mới hợp nhất duy nhất các kết quả qcheck hợp lệ vào `questions_test2.jsonl`, rồi tiếp tục
  shortpack → trích đáp án ngắn → worksheet trong các đường dẫn mới như lệnh bàn giao quy định.

#### Checkpoint tiếp tục — 02/11/2026 (Codex, dừng do lượt viết lại cuối không có đầu ra)

- Dựng lại `qpack` bằng đúng năm file lọc theo thứ tự bàn giao tại
  `data/vilextime/test2_generation/second_new/qpack_rebuilt_20261102_r3/`: 174 mục giữ; sau khi bỏ 136
  mục đã có `second_known/answers_1.jsonl` (và 0 mục đã có trong `questions_test2.jsonl`) còn đúng **38**
  mục mới, giữ nguyên thứ tự, ở `new_only/packs/`.
- Đã chạy lại `qcheck` trên 38 câu có sẵn của Claude Sonnet 5.5, ghi nguồn `claude-code` / `Claude Sonnet
  5.5`, tại `second_new/qcheck_20261102_r3/`: 8 đạt, 2 `insufficient_context`, 27 `copy_share`, 1
  `copies_the_answer`; 28 còn lượt nhưng **không viết lại** theo bàn giao. Kết quả chốt 10 dòng là
  `checked_1.jsonl`, danh sách không chốt là `viet_lai.jsonl`.
- Đã kiểm 94 dòng `answers_2.jsonl` khớp chính xác 94 mục cần viết lại ở lượt một, rồi qcheck bằng nguồn
  `codex` / `Codex (model identity unavailable)` trong thư mục đầu ra mới
  `second_known/qcheck_20261102_r3/`: tổng 136 mục cho 35 đạt, 9 `insufficient_context`, 92 `copy_share`;
  44 mục đã chốt, 92 mục còn **một lượt viết lại cuối** (giới hạn `MAX_WRITES=3`, tức câu gốc + tối đa hai
  lượt viết lại).
- Đã tạo gói mới chỉ gồm 92 mục cuối tại `.../qcheck_20261102_r3/rewrite_2/`, rồi thử Codex CLI với gói
  92 mục và tiếp tục với `chunks/chunk_01` (8 mục). Cả hai phiên chỉ đọc đầu vào rồi kết thúc mà không tạo
  `answers_3.jsonl`; không có dòng đầu ra hợp lệ để tính là lượt viết lại, và không đổi model/nhà cung cấp
  để né lỗi/usage. Vì vậy **chưa** hợp nhất vào `questions_test2.jsonl`, chưa chạy `shortpack`, chưa trích
  đáp án ngắn hay dựng worksheet mới; cũng chưa chạy pytest/hash cuối.

  Lệnh tiếp tục sau khi Codex có thể ghi đầu ra trở lại (chạy từng `chunk_01` … `chunk_12`, 8 mục/chunk,
  chunk_12 4 mục; chỉ đọc `HUONG_DAN.md`, `tasks.jsonl`, ghi `answers_3.jsonl`):

  ```bash
  codex exec --ephemeral --sandbox workspace-write \
    -C data/vilextime/test2_generation/second_known/qcheck_20261102_r3/rewrite_2/chunks/chunk_01 \
    -o agent_last_message.txt \
    'Read only HUONG_DAN.md and tasks.jsonl. For every JSONL record, write one replacement Vietnamese legal question that obeys HUONG_DAN.md and repairs ly_do. Write exactly one JSON object per line to answers_3.jsonl with schema {"item": ..., "question": ...}; no prose.'
  ```

  Khi đủ 92 dòng, ghép duy nhất các `answers_3.jsonl` theo ID (không chọn câu), chạy:

  ```bash
  .venv/bin/python scripts/review/test2_packs.py qcheck \
    --out data/vilextime/test2_generation/second_known/qcheck_20261102_r3/packs \
    --provider codex --model 'Codex (model identity unavailable)' \
    --dest NEW_SECOND_KNOWN_FINAL.jsonl \
    data/vilextime/test2_generation/second_known/answers_1.jsonl \
    data/vilextime/test2_generation/second_known/qcheck_20261102/answers_2.jsonl \
    ANSWERS_3.jsonl
  ```

  Chỉ sau đó nối kết quả 136 mục đầy đủ vào `data/vilextime/questions_test2.jsonl`, tiếp tục `shortpack`
  → đáp án ngắn → `worksheet` bằng đường dẫn mới, rồi chạy `.venv/bin/python -m pytest -q`, `git diff
  --check` và kiểm hash v1.0 `7cf51ee6…`.

#### Chốt biên soạn câu hỏi — 02/11/2026 (Claude)

- Lượt viết lại cuối 92 mục `second_known`: Claude Sonnet 5.5, phiên chỉ đọc `HUONG_DAN.md` + `tasks.jsonl`
  (Codex CLI không ghi được `answers_3.jsonl`); `qcheck` → `second_known/qcheck_20261102_r4/final.jsonl`: 39 đạt
  (33 lượt 1 + 2 lượt 2 do Codex, 4 lượt 3 do Claude), 9 thiếu ngữ cảnh, 87 trùng chữ, 1 chép đáp án. Độ trùng điển hình
  0,6–0,9 so với trần 0,40: viết lại thêm không cứu được; **không** thêm lượt cho câu sát ngưỡng, **không** nới cổng.
- Nhập vào `questions_test2.jsonl`: 136 mục `second_known` (sửa `provider/model` thành Codex cho lượt 1–2, Claude cho lượt 3
  vì `qcheck` gắn một nguồn cho cả cụm) + 10 mục chốt của 38 câu mới. 28 câu mới còn lượt nhưng không viết lại, nằm ở
  `second_new/qcheck_20261102_r3/viet_lai.jsonl`. Tổng 388 mục, **124 câu hợp lệ: T2 72, T3 33, T6 19**.
- Kho đã giữ (378) cạn; thêm câu phải rút/lọc đợt 3. Test2 hiện nhỏ hơn mục tiêu 300: CMT chọn giữa test2 nhỏ (T6
  ghi rõ không đủ mẫu) và đợt 3. Còn lại cho Codex: `shortpack` → đáp án ngắn → `worksheet`, `pytest`.

#### Checkpoint đợt 3 — 02/11/2026 (phiên Claude Code Sonnet tại `~/vilextime_loc/gan4`)

- Gói đợt 3 có 468 lineage T2. Phiên lọc dừng lúc 14:39 UTC vì hết hạn mức 5 giờ; CLI báo mở lại lúc 17:30 UTC.
  Không có `result.tsv` hoàn chỉnh; kết quả từng phần nằm ở `gan4/.work/r01a.tsv` … `r14a.tsv`.
- Kiểm cấu trúc độc lập: 338 dòng có đủ năm cột và không lặp, nhưng **5 `item` không có trong các gói hiện hành**;
  vì vậy chỉ 333 quyết định khớp gói, còn 135 lineage phải được lọc. Năm ID sai phải bị thay bằng quyết định cho
  các mục còn thiếu, không được đưa vào kết quả chấm. Chưa chạy `score`, `qpack`, hay hợp nhất vào dữ liệu repo.
- Khi hạn mức mở lại, tiếp tục chỉ trong `gan4`: kiểm chính xác tập ID của `packs/*.jsonl`, giữ nguyên 333 quyết định
  khớp gói, lọc 135 mục thiếu, và xuất đúng một `result.tsv` 468 dòng (header một lần) theo `HUONG_DAN.md`.
  Sau đó mới chạy `test2_packs.py score` với khóa và dựng gói câu hỏi theo kết quả đã chấm.

#### Checkpoint thay thế phần còn thiếu bằng Codex — 02/11/2026

- CMT yêu cầu dùng Codex thay cho phiên Sonnet đang chờ quota. Các phiên Codex mới, không kế thừa hội thoại,
  chỉ được giao `HUONG_DAN.md`, `packs/*.jsonl`, và các TSV phần việc trong `gan4/.work`; không được đọc repo,
  khóa, nhãn, hay thư mục cha. Chỉ dùng chứng cứ đã đóng trong pack (không gọi web) do CLI web dừng trước khi ghi file.
- Các lô hợp lệ: `codex_b01.tsv` 15 mục, `codex_b02.tsv` 5 mục, `codex_b03.tsv` 5 mục, `codex_b04.tsv` 15 mục.
  Các lô ban đầu có xuống dòng trong ô đã được chuẩn hóa lại cùng nội dung quyết định trước khi nhận. Đối chiếu mới
  nhất: **373/468** ID gói có đúng một hàng năm cột; 5 ID lạc từ phần Sonnet cũ vẫn tách riêng; **95** mục còn thiếu.
  Chưa có `result.tsv`, chưa chấm hiệu chuẩn, chưa dựng qpack.
- CLI chỉ hoàn tất được một phiên lọc trước khi runner kết thúc vòng lặp tuần tự; tiếp tục bằng các phiên Codex nhỏ,
  mỗi phiên lấy các ID còn thiếu đầu tiên, ghi `.work/codex_bNN.tsv`, rồi kiểm đủ năm cột, không trùng, và ID thuộc pack
  trước khi nhận. Khi đủ 468, chỉ ghép các hàng hợp lệ thành `result.tsv` rồi mới chạy score.

## Decisions

- 2026-11-03 (CMT): giữ test2 nhỏ, không mở đợt 3. Phiếu gán nhãn
  `data/review/test2_candidate_worksheet_v3.jsonl` (sha256 `c0925d5b…`): 138 câu / 321 mốc (T2 86, T3 33,
  T6 19). T6 không đủ mẫu, khóa luận phải ghi rõ. 6 câu loại sau rà Codex + rà tay ở
  `data/review/test2_worksheet_v2_loai.json` (lọc, không phải nhãn người). Rà mới chạm 13 + 73 câu, Codex dễ dãi.

- 2026-11-02 (CMT): Codex làm tiếp phần còn lại của test2; gọi chung `LLM` trong phần trình bày. Gán đôi
  A/B, luật sư hòa giải và các ngưỡng đã duyệt giữ nguyên. Kết quả model không thay nhãn người.

- 2026-10-29 (CMT): lọc ứng viên bằng Claude thay cho luật cứng; phiếu Q1–Q4, nhãn do máy suy ra,
  gán theo câu hỏi; luật làm việc (dẫn chứng bắt buộc, lô 0 với luật sư, dừng khi AC1 thấp).
- 2026-10-29 (Claude, mặc định, CMT có thể đổi): bỏ văn bản của split dev và lineage đã có trong v1.0;
  dùng lại lineage silver nhưng viết lại câu hỏi; T6 không chắc chuyển chỗ thì loại ở bước lọc.

- 2026-10-29 (CMT): ngưỡng lọc ≥ 80% / ≤ 30%; ngưỡng trùng chữ ≤ 40%; thẻ 4.0 duyệt; luật sư rảnh;
  A và B gán đôi 100%.
- 2026-10-29 (Claude): rút đợt 1 khoảng nửa số cần (T2 150, T2 gần giống 65, T3 220, T6 mỗi kiểu 75), seed
  `vilextime-test2-2910`; thiếu thì rút đợt 2 tiếp theo cùng thứ tự. Hiệu chuẩn bỏ nhãn một người và 101 dòng
  luật sư hòa giải có phiếu Claude hỗ trợ (không mù với Claude).
- 2026-11-02 (Claude, mặc định, CMT có thể đổi): cỡ đợt 2 theo tỉ lệ giữ đo được, tổng rút 1.529 ứng viên thay vì 850 của
  bước 1; dự kiến giữ khoảng 520 câu, nhiều hơn sức người (430), phần dư cắt theo nhóm ở bước 5.

Câu hỏi còn mở: mốc cuối tháng 11 đã chắc chưa.

## Validation

- Focused proof: bảng hiệu chuẩn bộ lọc (tỷ lệ loại đúng, loại nhầm theo nhóm); kiểm trùng chữ chạy
  trên mọi câu hỏi; AC1 và p_neg theo từng Q.
- Integration or end-to-end proof: `export_release.py` ra split `test2`; `run_vilextime.py` →
  `score_vilextime.py` → `confirm_vilextime.py` chạy trọn trên `test2`.
- Repository-required checks: `.venv/bin/python -m pytest -q`.

## Result

(Điền khi xong.)
