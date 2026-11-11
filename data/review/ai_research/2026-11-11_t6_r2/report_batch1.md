# Rà R2 cho chuỗi T6 bộ test cuối, batch1 (11/11/2026)

AI-chốt (`legal-adjudicator`), CMT ủy quyền, chưa qua luật sư. Ủy quyền theo quyết định CMT 2026-11-11 trong `docs/plans/active/master-plan.md`. Không có luật sư hay người độc lập nào kiểm các kết luận dưới đây.

Tôi chỉ áp quy tắc đang có:
- định nghĩa §3 R2/R3/R4, §4 T6, §6 điều 7, §7;
- annotation bước 7 (bảy yếu tố) và sổ quyết định.

Q1 (`docs/reports/quy-tac-mo-20261111.md`) chưa được chốt, nên tôi áp đúng chữ bước 7. Tôi không mở `runs/` và không dùng câu trả lời của hệ nào.

**Quy ước nguồn.** "vbpl:<ID>" là bản crawl `data/raw/<ID>.json`, cùng nguồn với API `https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/<ID>`. Phiên này không gọi API trực tiếp.

**Quy ước ngày.** "(lời văn)" là ngày tôi tự đọc trong điều hiệu lực, ở bản crawl hoặc Lawgical. "(phiếu)" là ngày lấy từ đoạn trích trong `batch1.jsonl`, tức dữ liệu của chính đề tài.

| lineage | Kết luận | Lệnh bãi bỏ, hiệu lực | Căn cứ | Link | Tin cậy |
|---|---|---|---|---|---|
| 0ba67328 (ve áo) | `relocation_unclear` | NĐ 01/2019 Đ19 k3 bãi bỏ Đ7–10 TT 08/2017; 15/02/2019 (lời văn) | Cùng NĐ, Đ16 k1: đồng phục "theo quy định tại Phụ lục II". Dấu vết, chủ thể, cấp đều đạt. Phụ lục II không có trong API hay Lawgical; theo nguồn phụ thì không có ve áo. Chưa đủ nguồn chính thức, nên áp câu cuối R2 | vbpl:133133; Lawgical; hethongphapluat (phụ) | thấp |
| 0ba67346 (ca vat) | `relocation_unclear` | như trên | Theo nguồn phụ, Phụ lục II không có ca vát; caravat chỉ có ở Phụ lục I của Kiểm lâm. Cùng chỗ thiếu nguồn | như trên | thấp |
| 24019d6a (Karate) | giữ | TT 21/2025 Đ6; hiệu lực từ ngày ký 26/12/2025 (lời văn) | Đợt cắt điều kiện, không có quy định thay | vbpl:186002 | trung bình |
| 285f93c0 (chi nhánh kiểm toán) | giữ | TT 22/2024 Đ2 k2; 01/07/2024 (lời văn) | Không quy định lại. Luật 67/2011 Đ22 k3 là hồ sơ của doanh nghiệp, khác thủ tục | vbpl:166772; vbpl:26750 | trung bình |
| 2fc7a1e0 (xác nhận 3 năm) | giữ | NĐ 151/2018 Đ2 k1; 07/11/2018 (phiếu) | Đ2 chỉ có lệnh bãi bỏ; Luật Kế toán chỉ dẫn chiếu | vbpl:132174; vbpl:95924 | trung bình–cao |
| 2fc83e20 (không bị phạt 12 tháng) | giữ | như trên | như trên | vbpl:132174 | trung bình–cao |
| 2fcd2020 (chứng minh bảo hiểm) | giữ | NĐ 151/2018 Đ2 k2; 07/11/2018 (phiếu) | Đ28 NĐ 174 chỉ đặt nghĩa vụ mua, không phải giấy tờ trong hồ sơ | vbpl:132174; vbpl:118313 | trung bình |
| 3cf170f0 (taxi tải) | giữ | NĐ 336/2025 Đ25 k4; 01/03/2026 (phiếu) | NĐ 336 chỉ phạt taxi chở khách. NĐ 158/2024 là quy định kinh doanh, không phải chế tài | vbpl:185666; vbpl:173412 | trung bình |
| 3eccae18 (lệ phí sửa đổi giấy phép) | giữ | NĐ 114/2016 Đ10 k2; 01/01/2017 (phiếu) | Biểu lệ phí mới chỉ có cấp và gia hạn; sửa đổi do ngân sách chi | vbpl:112160 | cao |
| 4a94f2f0 (giấy ĐKKD) | giữ | TT 11/2022 Đ2 k1; 20/09/2022 (lời văn) | Bỏ giấy tờ, không có quy định thay | vbpl:159014 | trung bình |
| 545c6f32 (chứng chỉ KTV) | giữ | TT 22/2024 Đ1 k2; 01/07/2024 (lời văn) | Không có quy định kế thừa | vbpl:166772; vbpl:30402 | trung bình–cao |
| 5b2570e0 (kiểm tra không định kỳ) | giữ | NĐ 173/2024 Đ1 k2 a (bãi bỏ Đ8); 15/02/2025 (lời văn) | NĐ chỉ bãi bỏ; chưa tra 7d | vbpl:174969 | trung bình |
| 5ba5ec70 (kiểm tra viên điện lực) | giữ | TT 56/2025 Đ12 k3; 28/11/2025 (phiếu) | Bãi bỏ cả chế định; TT mới không có "kiểm tra viên" | vbpl:184154; vbpl:158686 | trung bình |
| 5e4f34b0 (công nhân lò hỏa táng) | giữ | NĐ 14/2026 Đ138 k2; 15/01/2026 (lời văn) | Không có quy định kế thừa | vbpl:186425 | cao |

**Tổng:**

| Kết luận | Số lineage |
|---|---:|
| giữ | 12 |
| `relocation_unclear` | 2 |
| `relocated` | 0 |
| `superseded_by_other_norm` | 0 |
| `q1_case` | 0 |

**Ghi chú dòng có đáp án:**
- 3eccae18 và 5e4f34b0: short_answer còn ký hiệu mục ("c)", "b)").
- 0ba67346: tiền đề câu hỏi lạ ("chủ rừng lựa chọn ca vat"), có nguy cơ nhẹ `question_ambiguous`.
- Không tự đổi đáp án nào.

## Quy tắc còn mở

Không có quy tắc mới. Có một ca cần CMT xác nhận cách áp: dấu vết chuyển (yếu tố 7) có đủ, nhưng nội dung chỗ mới nằm ở phụ lục không đọc được từ nguồn chính thức (0ba67328, 0ba67346). Tôi áp câu cuối R2 cùng quy tắc nguồn của skill: kết luận "không có quy phạm thay thế" chỉ dựa nguồn phụ thì chưa đủ căn cứ. Có bản Công báo hay PDF Phụ lục II NĐ 01/2019 thì hai dòng này nhiều khả năng chuyển thành giữ.

## Nguồn đã dùng

- **Bản crawl `data/raw`:** 133133, 186002, 166772, 26750, 27508, 30402, 132174, 118313, 95924, 185666, 173412, 140152, 112160, 159014, 174969, 184154, 158686, 160787, 186425.
- **Lawgical:** 1 lượt (`get_document` 01/2019/NĐ-CP; bản này không có phụ lục). `get_account_status` lúc đầu phiên báo 14/20 đã dùng.
- **WebSearch:** 1 lượt. **WebFetch:** hethongphapluat có kết quả (nguồn phụ, đọc qua bản tóm của model nhỏ). Các URL khác lỗi: thuvienphapluat 403; vbpl.moj.gov.vn không phân giải được tên miền; tệp đính kèm vbpl.vn 133133 và 177746 trả 404.
- **Chưa mở:**
  - Phụ lục II NĐ 01/2019 bản chính thức;
  - mẫu Phụ lục II của TT 11/2022;
  - toàn văn Luật Điện lực 61/2024 (chưa xác định được nó là văn bản nào trong data/raw) và nghị định hướng dẫn luật này;
  - NĐ 36/2019;
  - Luật Đầu tư 2020;
  - toàn bộ các khoản phạt vận tải hàng hóa của NĐ 336/2025.

Nguồn web đã dùng:
- [hethongphapluat: NĐ 01/2019/NĐ-CP](https://hethongphapluat.com/nghi-dinh-01-2019-nd-cp-ve-kiem-lam-va-luc-luong-chuyen-trach-bao-ve-rung.html)
- [luatvietnam: VBHN 02/VBHN-BNNPTNT 2025](https://luatvietnam.vn/nong-nghiep/van-ban-hop-nhat-02-vbhn-bnnptnt-nam-2025-do-bo-nong-nghiep-va-phat-trien-nong-thon-ban-hanh-hop-nhat-nghi-dinh-ve-kiem-lam-va-luc-luong-chuyen-trach-bao-ve-rung-384995-d5.html) (chỉ thấy trong kết quả tìm kiếm, chưa mở)

## Model

Claude Opus 5.5 (`claude-opus-5-5`), vai `legal-adjudicator`, phiên batch1 ngày 11/11/2026. Không đụng batch2. Phiên không có công cụ ghi file; nội dung này do phiên điều phối ghi ra đĩa.
