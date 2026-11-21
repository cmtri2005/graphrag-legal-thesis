# Rà sót sửa đổi, 21/11/2026 (xong)
Script `scripts/check/audit_missed_amendments.py`: offline, dùng cache vbpl (data/diagrams = "Lược đồ", data/raw = toàn văn).
Tự kiểm: chạy trên bản chưa sửa `runs/posthoc_g4_20261113/t1_fix/release` phải bắt F016.

Kết quả trên 199 lineage: 60 ứng viên / 46 lineage (`candidates.tsv`), đọc hết, phán quyết ở `verdicts.tsv`:
- 5 lỗi kho, đã sửa (bản DiB 5.0.0): F016, F060 (người đọc mù tìm ra) và 3 lỗi mới: NĐ 33/2010 Đ7 k1 đ (NĐ 53/2012),
  NĐ 05/2015 Đ14 k3 b (NĐ 145/2020 thay cả nghị định), NĐ 135/2004 Đ61 k3 (NĐ 221/2013 bãi bỏ Chương IV).
- 1 đổi chữ không thực chất (TT 48/2015 Đ8 k6 a, TT 16/2023; R1). 54 báo nhầm (Điều/khoản khác, văn bản khác trùng số).
Cách sửa (`STORE_FIXES`, `F060` trong build_dib_release.py): phiên bản bị giữ quá hạn nhận ngày hết đúng; dòng nằm sau
ngày đó dời vào giữa khoảng hiệu lực thật của phiên bản (đáp án, nhãn giữ nguyên). F016 KHÔNG thêm phiên bản 3
(sẽ thành nội dung chưa ai gán nhãn); dataset hết dòng sau 25/09/2017.
Giới hạn: chỉ thấy văn bản tác động mà Lược đồ vbpl có ghi; corpus (bản chụp 17/09) không sửa, lệch ghi ở corpus/README.md.
