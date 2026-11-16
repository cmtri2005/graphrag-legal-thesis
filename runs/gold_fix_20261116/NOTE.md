# Sửa gold F019 theo ADR 0006 §7 — 16/11/2026
CMT duyệt trong hội thoại ("sửa luôn"). Dòng `vilextime:T2:provision:4cee6a60-eb71-11f0-ac45-154b0d915a56:2026-08-06` (F019) chuyển thành **không có đáp án** (`provision_repealed`, `valid_to` 2026-07-01): Thông tư 36/2026/TT-BXD, Điều 16 khoản 2, bãi bỏ Thông tư 11/2021/TT-BXD, hiệu lực 01/07/2026; ngày hỏi 06/08/2026. Phát hiện bởi người đọc thứ hai (luật sư, `data/review/gold_final/DONG_THUAN_B_20261116.md`).
Bản release đã sửa nằm ở thư mục này (`make_release.py`); **không sửa** `data/vilextime_final` (kho và bản phát hành gốc giữ nguyên, có thể tái lập). Chỉ chấm lại dự đoán đã lưu (`run.sh`), không gọi model.

Kết quả (F1–F7, Holm, bộ cuối 318 dòng): phán quyết không đổi ở cả GPT-4o mini và Qwen, cả hai lần chạy.
| | GPT r1 | GPT r2 | Qwen r1 | Qwen r2 |
|---|---|---|---|---|
| F1 | +0,343 [+0,283; +0,401] | +0,368 | +0,324 | +0,330 |
| F3 | −0,284 | −0,288 | −0,307 | −0,307 |
| F5 | +0,116 [+0,076; +0,156] (294 dòng có đáp án) | | | |
| F7 | +0,087 [0; 0,217] | +0,043 | +0,087 | +0,087 |
Trước khi sửa (G4 r1): F3 −0,283, F5 +0,115 trên 295 dòng; các số khác như trên. Oracle GPT r1 0,956 → 0,953.

Phần có gold mù người (103 lineage, 211 dòng; `subset/`): F1 +0,289 [+0,211; +0,364] / +0,322; F5 +0,075 [+0,032; +0,122]; F1–F6 ủng hộ, F7 không đủ bằng chứng, cả hai lần.

Chưa làm: 2 lineage T2 mà NMT thấy kho sai (`kg_missed_amendment`, 15/11) vẫn **bị loại** khỏi phần gold mù thay vì sửa gold như §7 nói; cần đáp án đúng để sửa. Số chính của paper (bảng, F1–F7) vẫn theo gold gốc; chênh ở chữ số thứ ba.
