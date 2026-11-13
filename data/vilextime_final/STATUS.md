# Trạng thái bộ test cuối (cập nhật 13/11/2026)

`README.md` và `manifest.json` ở thư mục này ghi "NHÁP, chưa Accepted, chưa hệ nào chạy". Đó là trạng thái lúc dựng (12/11). Hai file đó nằm trong `SHA256SUMS` nên **không sửa**; trạng thái hiện hành ghi ở đây.

- **ADR 0006 Accepted** ở commit `ac32a89` (12/11/2026, CMT duyệt; NMT chưa có xác nhận riêng trong repo).
- **Đã chạy G4** (12–13/11/2026), một lần, mỗi hệ sinh gọi API hai lần: `runs/final_g4_20261112/`. Dòng sổ chạy ở `runs/README.md`.
- **Hậu nghiệm, thăm dò:** `runs/posthoc_g4_20261113/` (quy kết, `b7v`, `bvnone`, `bvdate`); amendment ADR 0006 ngày 13/11.
- **Lỗi biết sau khi chạy:** đáp án ngắn của 43 dòng T1 là nguyên lời văn có ký hiệu liệt kê, nên cột T1 và `t1_no_harm` chưa dùng được. Nháp sửa ở `docs/plans/active/REFACTOR_PLAN.md` (việc 3.2), chờ duyệt.
- Kiểm hash các file đã khóa: `cd data/vilextime_final && sha256sum -c SHA256SUMS`.
