# Người đọc thứ hai (luật sư), 30 dòng chung — 16/11/2026
Phiếu: `gold_B.xlsx` (bản luật sư trả, sha256 c1fb469f…), nhập bằng `independent_gold.py import B` rồi `reveal B --release data/vilextime_final/internal/derived/vilextime/release.jsonl`. 30/30 dòng có `hieu_luc`; 17 dòng có nội dung và văn bản áp dụng; cột `phut` trống.

**Đồng thuận `hieu_luc` (còn/không), 30 dòng chung với NMT:** khớp 29/30 (0,967); Cohen κ = 0,932; Gwet AC1 = 0,935. Luật sư khớp kho 29/30; NMT khớp kho 30/30 trên 30 dòng này. Chưa so cột nội dung (chữ tự do).

**Dòng lệch duy nhất: F019** (`vilextime:T2:provision:4cee6a60-eb71-11f0-ac45-154b0d915a56:2026-08-06`, Thông tư 11/2021/TT-BXD, Điểm a Khoản 5 Điều 10, ngày hỏi 06/08/2026). Kho và NMT: còn. Luật sư: không, vì bị bãi bỏ.
Đã kiểm văn bản gốc: Thông tư 36/2026/TT-BXD (Bộ Xây dựng, 26/06/2026), Điều 16: "1. Thông tư này có hiệu lực thi hành từ ngày 01 tháng 7 năm 2026. 2. Thông tư này bãi bỏ Thông tư số 11/2021/TT-BXD ngày 31 tháng 8 năm 2021 …". Ngày hỏi sau 01/07/2026, nên **luật sư đúng, kho và NMT sai** (kho thiếu văn bản bãi bỏ; mã gần nhất `kg_wrong_repeal`/`kg_missed_amendment`).
Phạm vi: lineage này có 4 dòng trong bộ cuối (2022-05-21, 2025-03-07, 2025-03-08, 2026-08-06); chỉ dòng 2026-08-06 sau ngày bãi bỏ.

**Chưa làm, chờ CMT:** theo ADR 0006 §7, dòng gold mù cho thấy gold sai thì giữ trong bộ cuối với gold đã sửa. Chưa sửa gold, chưa chấm lại. Kho đúng trên phần có gold người giảm từ 79/81 xuống 78/81 lineage NMT.
