# Errata gold đợt 3 (CMT kiểm 21/11/2026)

## L7AE481 — đáp án gold thiếu ngoại lệ
- lineage: `provision:2353f726-e160-11f0-8c4a-d1ed3dd353c1`, as_of 2025-02-08.
- Đáp án hiện trong `vilextime.jsonl` bị cắt bằng "…" và **thiếu** mệnh đề ngoại lệ của thời hạn giao tài sản.
- CMT bổ sung (duyệt có bổ sung), đáp án hoàn chỉnh theo khoản 7 Điều 1 NĐ 152/2024/NĐ-CP (hiệu lực 01/01/2025):
  > Người mua phải nộp tiền vào tài khoản cơ quan THADS trong tối đa 30 ngày từ ngày đấu giá thành, không gia hạn. Cơ quan THADS tổ chức giao tài sản trong 60 ngày từ ngày người mua nộp đủ tiền, **trừ sự kiện bất khả kháng hoặc trở ngại khách quan**.
- Nguồn chính thức: https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/11/152-cp.signed.pdf
- **Việc cần làm:** sửa trường `answer` của dòng này khi dựng lại release (và kiểm cùng lúc các đáp án khác có "…" nối hai đoạn — có thể là lỗi cắt đoạn diện rộng của pipeline trích đáp án).

## Rà toàn bộ đáp án cắt "…" (21/11)
55 dòng có "…" → **18 lineage riêng** (phần lớn là trùng nhiều as_of). 16 đủ (mẫu "mở đầu khoản … điểm liên quan", hợp lệ). **2 lineage cắt giữa câu, mất nội dung:**

1. **L7AE481** (`…d1ed3dd353c1`, 6 dòng as_of: 2017-12-30, 2020-04-30, 2022-07-06, 2024-12-31, 2025-01-01, 2025-02-08) — **lỗi thật**: đuôi "…người mua nộp đủ tiền" cắt mất "cơ quan THADS tổ chức giao tài sản…, trừ sự kiện bất khả kháng hoặc trở ngại khách quan".
   - ĐÃ SỬA 21/11: 2 dòng phiên NĐ 152/2024 (as_of 2025-01-01, 2025-02-08 — bản CMT duyệt) được nối verbatim từ context trong BASE `runs/posthoc_g4_20261113/t1_fix/release/vilextime.jsonl`, build lại release.
   - CÒN TREO: 4 dòng phiên bản cũ hơn (2017-12-30, 2020-04-30, 2022-07-06, 2024-12-31) cũng cắt "…" tương tự nhưng thuộc phiên bản CMT CHƯA xem → chưa sửa, chờ CMT duyệt rồi nối.
2. **`…01cda9906453`** (two_versions, 4 dòng as_of: 2017-07-18, 2018-12-14, 2018-12-15, 2022-05-12) — **nhẹ**: đuôi "…tương đương với mức đóng bảo hiểm thất nghiệp" cắt trước "theo quy định của pháp luật [và thời gian làm việc đã được…]". Boilerplate; cần CMT xác nhận có cần nối tiếp không.

Kết luận: dấu "…" nhìn chung là ký hiệu bỏ-qua-điểm-anh-em hợp lệ, KHÔNG phải lỗi diện rộng; chỉ 2/18 lineage bị cắt giữa câu, 1 trong đó trọng yếu (L7AE481).

## Nguồn chính thức bổ sung trong đợt này
- L39B446: NĐ 100/2018 Điều 3 khoản 4 (toàn văn).
- LB60578: NĐ 126/2021 Điều 5 khoản 2 (toàn văn).
- L732487: Luật 20/2012 khoản 36 Điều 1 (Công báo/VBHN).
- L7AE481: NĐ 152/2024 bản ký datafiles.chinhphu.vn (CMT cấp).
