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
   - ĐÃ SỬA 21/11 (toàn bộ 6 dòng answerable): nối verbatim từ context của chính dòng trong BASE, trung thành theo từng phiên bản. Phiên NĐ 152/2024 (2025-01-01, 2025-02-08) kết "…trừ sự kiện bất khả kháng hoặc trở ngại khách quan"; phiên cũ hơn (2017-12-30, 2020-04-30, 2022-07-06, 2024-12-31) kết "…trừ trường hợp có sự kiện bất khả kháng" (phiên đó chưa có "trở ngại khách quan").
2. **`…01cda9906453`** (two_versions) — **nhẹ**, ĐÃ SỬA 21/11: 2 dòng bản ngắn (as_of 2017-07-18, 2018-12-14) nối verbatim " theo quy định của pháp luật" cho khớp context. 2 dòng bản dài (2018-12-15, 2022-05-12) vốn đã đủ, không đụng.

Kết luận: dấu "…" nhìn chung là ký hiệu bỏ-qua-điểm-anh-em hợp lệ, KHÔNG phải lỗi diện rộng; chỉ 2/18 lineage bị cắt giữa câu. **Đã sửa hết 21/11** — rà lại còn 0 chỗ cắt giữa câu.

## Nguồn chính thức bổ sung trong đợt này
- L39B446: NĐ 100/2018 Điều 3 khoản 4 (toàn văn).
- LB60578: NĐ 126/2021 Điều 5 khoản 2 (toàn văn).
- L732487: Luật 20/2012 khoản 36 Điều 1 (Công báo/VBHN).
- L7AE481: NĐ 152/2024 bản ký datafiles.chinhphu.vn (CMT cấp).
