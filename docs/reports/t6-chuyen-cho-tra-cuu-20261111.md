# Tra cứu 17 dòng T6 "không đáp án" mà proposed2 trả "còn" (dev), 11/11/2026

**AI-đề xuất (`vn-law-verifier`, sonnet, hai lô không trùng), chờ luật sư chốt.** Nguồn: toàn văn vbpl (`data/raw/`, API vbpl), `data/temporal.sqlite` chỉ đọc, Lawgical 5 lượt (lô A 3, lô B 2).
Câu hỏi: nhãn "không đáp án" có đúng theo phán quyết 05/10 (R2: câu hỏi nội dung trả bằng quy phạm đang điều chỉnh), hay nội dung đã chuyển sang quy phạm khác?
Dữ liệu dòng: `docs/reports/chan-doan-t6-dev-20261111.tsv`; câu trả lời: `runs/rebuild_20261110_dev/dev/proposed2.jsonl`.

Cả 17 lệnh bãi bỏ đều đúng và có hiệu lực trước ngày hỏi (gold về bãi bỏ: 0 nghi).

| Dòng (id rút gọn @ as_of) | Nội dung | Nhãn "không đáp án" | proposed2 | Quy phạm điều chỉnh tại as_of (nếu có) |
|---|---|---|---|---|
| 41522558 @2026-05-18 | Biên bản họp tổ chức cộng đồng | chuyển chỗ | đúng phần chính | TT 88/2025/TT-BNNMT Đ5 K1 d (bỏ "bản chính") |
| 8ac0e590 @2026-08-08 | Hồ sơ điện tử thi công | **đúng** | sai | NĐ 207/2026 Đ11 không còn yêu cầu được hỏi |
| 6cab03a0 @2021-10-21 | Hồ sơ nhập khẩu tem bưu chính | chuyển chỗ (cờ) | sai | TT 26/2014/TT-BTTTT Đ7 K1 (cờ: văn bản căn cứ NĐ 187/2013 đã hết hiệu lực) |
| 6e3d884a#k1#h @2025-09-06 | Chốt số liệu báo cáo vận tải | chuyển chỗ | sai | TT 36/2024/TT-BGTVT Đ46 K1 h (giữ nguyên nội dung) |
| 6e30cd9c @2026-06-18 | UBND phường Đà Nẵng, bầu cử | chuyển chỗ (cờ) | đúng một phần | Luật Bầu cử 85/2015 Đ25 K1 (sửa bởi Luật 83/2025) |
| 2cb2c1fa @2020-11-11 | Gửi hồ sơ tiếp cận nguồn gen | chuyển chỗ | **đúng** | NĐ 59/2017 Đ12 K1 |
| ecff2318 @2018-06-10 | Quản lý khu CNTT tập trung | chuyển chỗ (cờ) | đúng một phần | NĐ 154/2013 Đ19, Đ27 (không giữ nguyên từng ý) |
| 7dd23e64 @2026-08-06 | Phụ cấp ưu đãi trường chuyên biệt | chuyển chỗ (cờ: chuyển + sửa mức) | sai | NĐ 182/2026 Đ3 |
| c203f3d0 @2019-11-05 | Phí đại lý trái phiếu Chính phủ | chuyển chỗ | **đúng** | TT 15/2018/TT-BTC Đ3 K4 |
| fe9e225a#k5 @2025-11-08 | Khai thuế TNDN theo tỷ lệ % doanh thu | chuyển chỗ | sai (trích chế độ sổ kế toán) | NĐ 126/2020 Đ8 K4 đ |
| 7dc9e82a @2025-05-18 | Công bố đưa cao tốc vào khai thác | chưa đủ căn cứ về quy phạm thay thế | sai (chép điều đã bãi bỏ) | Chưa mở thông tư hướng dẫn Luật Đường bộ 2024 |
| 92d51460 @2026-03-05 | Thu hồi giấy phép hóa chất Bảng | chuyển chỗ | **đúng** | NĐ 26/2026 Đ22 K1 |
| 20ee7b9c @2025-12-04 | UBND quận Đà Nẵng | **đúng** (cấp quận kết thúc 01/07/2025) | sai | — |
| 6caa8e70 @2021-09-03 | Điều kiện, cơ quan cấp phép nhập khẩu tem | **đúng** (tin cậy trung bình) | sai | Lô B chưa tra TT 26/2014; **lệch với lô A**, luật sư xem cùng dòng 6cab03a0 |
| 890e6428 @2021-05-28 | Bảo hiểm của DN kiểm toán nước ngoài qua biên giới | **đúng** | sai | — |
| 1634ac90 @2025-01-31 | Thăng hạng viên chức đăng kiểm | chuyển chỗ | **đúng** (thiếu trích dẫn) | NĐ 115/2020 Đ32, sửa bởi NĐ 85/2023 |
| f1fc5a86 @2026-08-17 | Nội quy cơ sở Wushu | **đúng** | sai (trích TT môn Đấu kiếm) | — |

## Tổng

| | Số dòng |
|---|---:|
| Nhãn "không đáp án" có vẻ chưa đúng (chuyển chỗ; 5 dòng có cờ cần luật sư) | 11 |
| Nhãn đúng | 5 |
| Chưa đủ căn cứ | 1 |
| proposed2 đúng / đúng một phần (trong 11 dòng chuyển chỗ) | 5 / 2 |

Hệ quả (AI-đề xuất): định nghĩa T6 "không đáp án" hiện không loại trừ trường hợp nội dung đã chuyển sang quy phạm khác,
trái với R2. Ở dev, khoảng 11/21 dòng T6 không đáp án có thể bị chấm sai chiều. Cần luật sư và CMT chốt trước G2, vì bộ test cuối có dòng T6:
(a) dòng chuyển chỗ đổi đáp án theo R2 (quy phạm mới) hay (b) loại theo R3; và quy tắc dựng T6 về sau phải kiểm có quy phạm thay thế không.

Kho lệch nguồn (ghi H5, không sửa): `#k5`, `#k1#h` không có bản ghi riêng trong `versions` (lời văn nằm ở phiên bản Điều cha);
`document:25325` (NQ 725/2009) còn CHL nhưng phạm vi áp dụng thí điểm; TT 26/2014 hướng dẫn NĐ 187/2013 đã hết hiệu lực.
