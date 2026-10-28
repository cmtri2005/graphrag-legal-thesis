# Execution Plan: Agent kiểm phần tập test còn thiếu người kiểm

Date: 2026-10-26

## Status

Active. Bước 1 (hiệu chuẩn mù) đang chạy. Từ 27/10 việc còn lại theo dõi ở [`codex-chot-du-lieu-va-thuc-nghiem.md`](codex-chot-du-lieu-va-thuc-nghiem.md) (Phần A).

## Outcome

Mọi dòng `ranh_gioi` của split `test` có nhãn kiểm theo 8 ô ở mục 6 định nghĩa: nhãn người (A, B,
hòa giải) hoặc nhãn agent `vn-law-verifier` đã qua kiểm chứng. Nhãn agent ở
`data/review/kiem_agent.tsv`, có `labeler`.

## Context

- Quyết định: CMT chọn hướng 1 ngày 26/10/2026 (agent kiểm, có kiểm chứng). Sửa mục 6 và mục 11 của
  `docs/vilextime-dinh-nghia.md`, mục 6 của `docs/vilextime-annotation.md`.
- Người kiểm đủ chuẩn 3.0 chỉ được 152 dòng `dat` (123 khi giữ đủ lineage); AC1 A–B 0,377.
- Hạn chạy xong: 31/10/2026.

## Scope

In scope: hiệu chuẩn mù 178 dòng; gán 714 dòng test chưa có người kiểm; mẫu 50 dòng cho luật sư.

Out of scope: dòng `dev` (139), T5b `truoc_hieu_luc`, gold độc lập, sửa lỗi kho (làm riêng).

## Approach

1. Hiệu chuẩn mù: 178 dòng có nhãn người độc lập (A=B theo 3.0: 166; lô 0 luật sư tự chốt: 12),
   agent không thấy nhãn hay ghi chú người. Ngưỡng AC1 ≥ 0,80 và p_neg ≥ 0,60 (cùng ngưỡng của người).
   Loại khỏi hiệu chuẩn 89 dòng hòa giải 26/10 vì luật sư đã xem phiếu agent.
2. Đạt ngưỡng: gán 714 dòng test còn thiếu, cùng prompt, cùng định dạng.
3. Luật sư kiểm 50 dòng ngẫu nhiên (seed ghi trong plan) từ nhãn agent.
4. Ghi `kiem_agent.tsv`; cập nhật plan dựng lại để lấy nhãn agent khi dựng split.

## Risks And Recovery

- Không đạt ngưỡng: dừng, báo số đo, quay lại hướng 2 hoặc 3 (CMT chọn). Không đổi ngưỡng.
- Chi phí: khoảng 200 nghìn token cho 15 dòng; 714 dòng khoảng 48 agent.
- Lawgical 20 lượt/ngày: agent không dùng; đọc `data/raw`, regai, web.

## Progress

- [ ] Hiệu chuẩn mù 178 dòng
- [ ] Gán 714 dòng test
- [ ] Luật sư kiểm 50 dòng
- [ ] Ghi `kiem_agent.tsv`, nối vào bước dựng split

## Validation

- AC1, p_neg agent so với nhãn người trên 178 dòng (`crosscheck.gwet_ac1`, `specific_agreement`).
- Luật sư: số dòng đồng ý trên 50.

## Result

(Điền khi xong.)
