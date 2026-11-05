# Execution Plan: Tiếp quản truy xuất lai ghép và tải thử VBHN

Date: 2026-11-05

## Status

Đóng 05/11, phần còn lại chuyển sang master plan: X1, X5

## Outcome

Nhúng đủ lớp `version`, kiểm vector và chạy truy xuất lai ghép trên dev;
lưu kết quả tải thử văn bản hợp nhất (VBHN) cùng giới hạn của phép đối chiếu.

## Context

- CMT duyệt trong phiên Claude ngày 05/11 lúc 00:29 UTC: “oke làm phần lai ghép và thử tải VBHN đi”.
  Lúc 02:11 UTC yêu cầu tiếp tục chạy; phiên dừng do hết hạn mức.
- Claude đã thêm `--hybrid` vào runner và bộ xuất Colab, cùng test truy xuất.
- `scripts/eval/embed_corpus.py` hỗ trợ tiếp tục theo shard; lần trước chưa commit
  shard mới: `unit` rỗng, 1.490.446 lời văn tái sử dụng từ lớp `asis`, chưa có `last_rowid`.
- VBHN đã có file và số đo trong `data/vbhn_files/`; mã thử nghiệm ở `/tmp` của
  phiên Claude không còn. Không coi số đo này là gold đã kiểm định.
- Tham chiếu cấu hình và quy tắc dev/test: ADR 0004, ADR 0005 và `runs/README.md`.

## Scope

In scope:

- Tiếp tục nhúng bằng cùng model, tách từ, độ dài và corpus đã chọn.
- Kiểm vector; chạy dev chỉ truy xuất, so với kết quả từ vựng trên cùng ID.
- Kiểm lại artifact VBHN, lưu báo cáo có thể truy vết.

Out of scope:

- Chạy test, gọi model sinh, đổi gold, corpus gốc hoặc kết quả cũ.
- Cào toàn bộ hoặc mở rộng phạm vi thử tải đã được duyệt.

## Approach

1. Dùng checkpoint nhỏ hơn (`--shard 1000`) để hạn chế mất tiến độ khi ngắt;
   các tham số biểu diễn giữ nguyên.
2. Chạy `verify_embed.py` cho lớp version sau khi nhúng xong.
3. Chạy `b7pp` và `proposed` với `--hybrid --retrieval-only` trên dev,
   `giua_khoang`, k=20; chấm cùng bản từ vựng trên đúng 151 ID của release
   công bố. `proposed` còn kiểm đường mở rộng đồ thị; chỉ truy xuất chưa đo
   chất lượng sinh hoặc Verifier. Ghi rõ đây là kiểm đường ống trên dev.
4. Kiểm file PDF và số đo VBHN, ghi kết quả cùng giới hạn.
5. Chạy kiểm tra repo, cập nhật sổ chạy và kết quả kế hoạch.

## Risks And Recovery

- CPU mất thời gian: theo dõi log, chạy tiếp đúng lệnh sau khi bị ngắt.
- Vector lớp version tái sử dụng shard lớp asis qua symlink; không sửa shard nguồn.
- Không chạy đánh giá khi bản nhúng chưa đầy đủ.
- Số khớp VBHN từ PDF phụ thuộc căn đoạn, chất lượng chữ và chú thích;
  không dùng trực tiếp như bằng chứng gold độc lập đã được xác nhận.
- Test cần amendment được commit trước lần chạy theo ADR 0005; phạm vi hiện tại chỉ dev.

## Progress

- [x] Khôi phục yêu cầu cuối và kiểm trạng thái artifact.
- [x] Toàn bộ 611 test qua; bản từ vựng `b7pp` đủ 151 ID dev, không lỗi.
- [x] `proposed` từ vựng cũng đủ 151 ID dev, không lỗi.
- [x] 05/11, 03:45 UTC: tiếp quản lần nữa; hai terminal session cũ không còn.
  Checkpoint giữ được 595.000/1.477.089 đơn vị (40,28%), 1.501.022 lời văn
  trong bảng `text` (10.576 mới so với nguồn tái sử dụng), 72 shard,
  `last_rowid=2104363`. Chạy tiếp nhúng và quy trình dev; 7 hash đầu vào đều
  còn khớp, `git diff --check` qua. Chưa có điểm lai ghép.
- [x] Nhúng đủ lớp version và kiểm vector (05/11, hai tiến trình chạy lại lúc 05:10 UTC, xong ~06:50).
- [x] Chạy và chấm dev lai ghép: `runs/hybrid_20261105/dev/retrieval.score.json`, log có `DONE`.
  151 ID dev, giua_khoang, k=20, chỉ truy xuất. Từ vựng: MRR 0,528, R@1 0,424, R@5 0,649, R@10 0,722.
  Lai ghép: MRR 0,516, R@1 0,411, R@5 0,682, R@10 0,735. Chênh lệch nằm trong CI 95%
  (R@1 [0,31–0,51] so với [0,33–0,53]); ghép cặp lai ghép − từ vựng: MRR −0,012 [−0,074; +0,043], R@1 −0,013
  [−0,098; +0,065]. Cột sinh câu trả lời là giá trị giữ chỗ.
  `proposed` trùng `b7pp` ở mọi chữ số: mở rộng đồ thị chạy thật (44/151 dòng được thêm 1–5 đơn vị)
  nhưng chỉ nối vào sau vị trí 20, top-10 giống hệt; recall@≤10 không thấy được. Chưa đo tác dụng của đồ thị.
- [x] 05/11, sửa đồ thị cho tier `propagated` (`graphx.py`, `retrieve.py`): mở rộng bắt đầu từ
  5 kết quả từ vựng **trước** bộ lọc ngày, và tìm lệnh bãi bỏ trên cả chuỗi tổ tiên của điều khoản.
  Lý do: 21/42 dòng T6 dev không có đáp án, đáp án là lệnh bãi bỏ nhắm vào điều khoản cha; điều khoản
  bị loại khỏi `hits` nên đồ thị không có điểm xuất phát. Sửa lần đầu đổi `proposed` tại chỗ, trái khóa ADR 0005 §2;
  đang tách thành hệ `proposed2`, xem `docs/plans/active/rerank-va-do-thi-t6.md`.
  Kết quả dev (hybrid, `runs/hybrid_20261105/dev_graph2/`): T6 không đáp án R@30 0,000 → 0,714 (15/21);
  toàn bộ R@30 0,808 (`proposed` cũ) → 0,907; T1, T2, T3, T6 có đáp án và R@1, R@10 không đổi (lệnh nối sau vị trí 20).
  Điều chỉnh này chọn sau khi thấy lỗi trên dev; chỉ đo trên dev, chưa chạm test.
- Thử chỉnh trộn RRF (độ sâu 50–100, trọng số từ vựng ×2): MRR 0,516 → 0,539, CI 95% ghép cặp
  [−0,004; +0,052], không vượt nhiễu nên **không** đưa vào `fuse_rrf` dùng chung.
- [x] Báo cáo tải thử VBHN: `docs/reports/thu-tai-vbhn-20261105.md`;
  đủ 40 PDF, kích thước khớp; khôi phục mã thử trong `data/vbhn_files/source/`.
  Phép so PDF chạy lại khớp từng byte với kết quả Claude.
- [ ] Kiểm tra repo và ghi kết quả.

## Decisions

- 2026-11-05: Giữ `dangvantuan/vietnamese-embedding`, pyvi, max_seq_length=256,
  RRF hiện có, k=20; chỉ giảm kích thước shard lưu, không tinh chỉnh theo điểm.

## Tiếp tục khi bị ngắt

Lúc 02:21 UTC: checkpoint đầu `rowid=1574363`, 65.000 đơn vị,
1.009 lời văn mới, tốc độ khoảng 2,9 lời văn/giây. Chưa đủ để đánh giá lai ghép.

Hai tiến trình được khởi chạy lại lúc 03:45 UTC qua terminal session của Codex:

1. Nhúng (session `84432`), log `runs/hybrid_20261105/embedding.log`.
   Log cũ ở `/tmp` không còn sau lần đổi phiên; từ lần này lưu trong `runs/`:

   ```bash
   HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
     .venv/bin/python -u scripts/eval/embed_corpus.py --layer version \
     --max-seq-length 256 --model dangvantuan/vietnamese-embedding --shard 1000 \
     --out data/derived/embed/version-vietnamese-embedding
   ```

2. Quy trình dev (session `18408`), log `runs/hybrid_20261105/pipeline.log`
   (nối thêm, giữ log từ phiên trước):

   ```bash
   HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
     .venv/bin/python -u runs/hybrid_20261105/continue_dev.py
   ```

Quy trình kiểm hash đầu vào, chờ đủ đơn vị và checkpoint cuối, kiểm vector
(gồm 100 mẫu nhúng lại), rồi chạy `b7pp`/`proposed` lai ghép và chấm cùng bản
từ vựng trên đúng 151 ID. Nó không chọn dòng test và không gọi generator.
File cuối khi thành công là `runs/hybrid_20261105/dev/retrieval.score.json`;
log phải có `DONE`. Chưa có file đó thì không báo hoàn tất.

Sau khi ngắt phiên, kiểm tiến trình còn sống và checkpoint trước khi khởi chạy
lại; mỗi đầu ra chỉ có một writer. Hai lệnh đều hỗ trợ tiếp tục nhưng không
được chạy hai bản đồng thời. Nếu log báo input đổi, cần đối chiếu thay đổi trước
khi quyết định tạo lượt chạy mới; không tự cập nhật hash để bỏ qua lỗi.

Sau khi có điểm, cập nhật báo cáo/sổ chạy, ghi Result rồi mới chuyển kế hoạch
sang completed. Các chỉ số câu trả lời từ lượt retrieval-only không dùng được.

## Validation

- Focused proof: `verify_embed.py --layer version --model dangvantuan/vietnamese-embedding`.
- Integration proof: dự đoán dev đủ ID, chấm bằng `score_vilextime.py`.
- Repository checks: `.venv/bin/python -m pytest -q`, `git diff --check`.

## Result

Đóng 05/11, phần còn lại chuyển sang master plan: X1, X5
