# Rà R2 cho 4 lineage T6 dev còn lại (11/11/2026)

AI-chốt (`legal-adjudicator`), CMT ủy quyền, chưa qua luật sư. Ủy quyền theo quyết định CMT 2026-11-11 trong `docs/plans/active/master-plan.md`. Không có luật sư hay người độc lập nào kiểm các kết luận dưới đây.

Tôi chỉ áp quy tắc đang có:
- định nghĩa §3 R2/R3/R4, §4 T6, §6 điều 7, §7;
- annotation bước 7 (bảy yếu tố) và sổ quyết định.

Q1 (`docs/reports/quy-tac-mo-20261111.md`) chưa được chốt, nên tôi áp đúng chữ bước 7 và gắn `q1_case: true` cho ca kiểu Q1. Tôi không mở `runs/` và không dùng câu trả lời của hệ nào.

**Quy ước nguồn.** "vbpl:<ID>" là bản crawl `data/raw/<ID>.json`, cùng nguồn với API `https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/<ID>`. Phiên này không gọi API trực tiếp.

**Quy ước ngày.** "(lời văn)" là ngày tôi tự đọc trong điều hiệu lực của bản crawl. "(phiếu)" là ngày lấy từ metadata hoặc dữ liệu của đề tài.

| lineage | Kết luận | Lệnh bãi bỏ, hiệu lực | Căn cứ | Link | Tin cậy |
|---|---|---|---|---|---|
| fe9e707a#k2#c (thông báo kiểm toán độc lập kiểm tra quyết toán) | giữ | TT 80/2021 Đ87 k4 b bãi bỏ Đ14–21 TT 151/2014 (Đ18 = Đ12b TT 156/2013); 01/01/2022 (lời văn) | TT 80/2021 không quy định lại. NĐ 91/2014 chỉ giao BTC hướng dẫn cơ chế đặt hàng, không có nghĩa vụ thông báo | vbpl:151086; vbpl:37430; vbpl:37143 | trung bình |
| 1a267400 (công đoàn trong Hội đồng xét bồi thường) | giữ, `q1_case` | NĐ 18/2010 Đ30 k2 bãi bỏ Chương III NĐ 54/2005; 01/05/2010 (lời văn) | TT 03/2011/TT-BNV Đ28 k2 b vẫn có "đại diện tổ chức công đoàn" trong Hội đồng xét đền bù, còn áp dụng ở mốc 2017-06-07. Yếu tố 6 không đạt (thông tư thấp hơn nghị định), yếu tố 2 và 4 đổi, yếu tố 7 chỉ gián tiếp. Đúng chữ bước 7 thì giữ; nếu Q1 được chốt thì thành `relocation_unclear` | vbpl:18430; vbpl:25059; vbpl:26227 | thấp |
| 982d3ea0 (Quyền anh: khu thay đồ) | giữ | TT 21/2025 Đ9; hiệu lực từ ngày ký 26/12/2025 (lời văn) | Đợt cắt điều kiện, không có quy định thay; cùng mô thức ca Karate ở batch1. NĐ 36/2019 chỉ yêu cầu chung, chưa có QCVN Quyền anh | vbpl:186002; vbpl:129643; vbpl:135173; Lawgical | trung bình |
| 939488a2 (QCVN 01-108 Anastrepha) | giữ | TT 15/2023 Đ2 k5 bãi bỏ k1–7, 14, 15 Đ1 TT 63/2012; 05/02/2024 (lời văn) | Thông tư chỉ bãi bỏ; chuyển tiếp không gồm TT 63/2012; không có QCVN mới | vbpl:164265; vbpl:30338; Lawgical | trung bình–cao |

**Tổng:**

| Kết luận | Số lineage |
|---|---:|
| giữ | 4 |
| `relocation_unclear` | 0 |
| `relocated` | 0 |
| `superseded_by_other_norm` | 0 |
| `q1_case` | 1 |

**Ghi chú dòng có đáp án:**
- 1a267400: phạm vi NĐ 54/2005 là "công chức, viên chức", câu hỏi viết "cán bộ, công chức". Chưa kiểm sửa đổi Điều 14 trước mốc 2007-09-28.
- 939488a2: câu hỏi hỏi tên và ký hiệu QCVN, là nội dung kiểu siêu dữ liệu; chỉ ghi lại.
- Không tự đổi đáp án nào.

## Quy tắc còn mở

Không có quy tắc mới. 1a267400 là ca Q1, đúng loại với các ca tem bưu chính 6cab03a0, 6caa8e70: thông tư Bộ Nội vụ (cấp thấp hơn) vẫn quy định đại diện công đoàn trong hội đồng ở mốc của dòng không đáp án. Đúng chữ bước 7 thì giữ dòng. Nếu CMT chốt Q1 theo khuyến nghị của phiên điều phối ("trả quy phạm đang điều chỉnh") thì lineage này phải loại với `relocation_unclear`. Ca này làm Q1 có tác động trên T6 dev; trước đây rà R2 bộ test cuối không gặp ca Q1 nào.

## Nguồn đã dùng

- **Bản crawl `data/raw`:** 37430, 151086, 37143, 18430, 25059, 113590, 26227, 124688, 129643, 186002, 135173, 129523, 30338, 164265, 178655.
- **Lawgical:** `get_account_status` lúc đầu phiên báo đã dùng 16/20. Đã gọi 2 lượt `search_legal_docs`: "quy chuẩn kỹ thuật quốc gia cơ sở vật chất trang thiết bị môn Quyền anh" và "quy trình giám định ruồi đục quả Anastrepha". Cả hai không ra quy phạm kế thừa; chỉ đọc đoạn trích, không gọi `get_document`.
- **Không dùng:** WebSearch, WebFetch, API vbpl trực tiếp.
- **Chưa mở:**
  - toàn văn Luật QLT 38/2019 và NĐ 126/2020 bằng nguồn ngoài;
  - điều hiệu lực NĐ 101/2017;
  - điều hiệu lực TT 13/2018 (Điều 8);
  - TCVN về giám định ruồi đục quả (nếu có);
  - toàn văn QĐ 1616/QĐ-TTg.

## Model

Claude Opus 5.5 (`claude-opus-5-5`), vai `legal-adjudicator`, phiên t6_dev4 ngày 11/11/2026. Phiên không có công cụ ghi file; nội dung này do phiên điều phối ghi ra đĩa.
