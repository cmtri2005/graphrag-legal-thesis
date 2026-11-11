# Rà R2 (chuyển chỗ) cho T6 bộ test cuối, batch 2 (11/11/2026)

AI-chốt (`legal-adjudicator`), CMT ủy quyền, chưa qua luật sư.

Ủy quyền: quyết định CMT 2026-11-11 trong `docs/plans/active/master-plan.md`. Không có luật sư hay người độc lập kiểm.

Quy tắc áp: định nghĩa §3 R2/R3/R4, §4 T6, §6 điều 7, §7; annotation bước 7 (bảy yếu tố); sổ quyết định 24/10, 26/10, 10/11. Q1 (`docs/reports/quy-tac-mo-20261111.md`) chưa chốt: áp đúng chữ bước 7 và gắn cờ `q1_case`. Không mở `runs/`, không dùng câu trả lời của hệ nào.

**Quy ước nguồn.** "vbpl:<ID>" là bản crawl `data/raw/<ID>.json`. Phiên này không gọi API trực tiếp.
**Quy ước ngày.** "(lời văn)" là ngày tôi đọc trong điều hiệu lực, ở bản crawl hoặc ở đoạn `in_force` của `batch2.jsonl` (đoạn này trích từ bản crawl). Không dùng ngày "(phiếu)".

## Bảng

| lineage (8 ký tự đầu) @ mốc không đáp án | Kết luận | Mã | Căn cứ (số hiệu, Điều/Khoản, hiệu lực) | Trích | Link | Tin cậy |
|---|---|---|---|---|---|---|
| 834d699a@2016-07-01 | giữ | `giu` | TT 14/2016/TT-NHNN Đ1 k2 "Bãi bỏ Điều 8" TT 30/2014; 01/07/2016 (lời văn). Không có câu bổ sung; cụm "cơ sở vật chất…" chỉ có ở Đ8 k4. | "2. Bãi bỏ Điều 8." | vbpl:111884; vbpl:37568 | trung bình. Chưa mở Luật TCTD 2010. |
| 913092a4@2018-12-01 | giữ | `giu` | TT 30/2018/TT-BVHTTDL Đ2 k3; 01/12/2018 (lời văn). QĐ 308/2005/QĐ-TTg Đ2 k6 chỉ cấm cán bộ, công chức mời/dự tiệc cưới trong giờ làm việc: khác chủ thể, không có nơi tổ chức, phạm vi khách. Không dấu vết. | QĐ 308 Đ2 k6: "…không mời, không dự tiệc cưới trong giờ làm việc…" | vbpl:131594; vbpl:17135 | trung bình. Giáp ranh Q1, không gắn cờ. |
| 9784e330@2024-05-24 | giữ | `giu` | TT 08/2024/TT-BYT Đ1 k1; 24/05/2024 (lời văn: hiệu lực từ ngày ký). NĐ 146/2018 Đ34 không có điều kiện địa lý; NĐ 75/2023 không sửa Đ34. | "1. Khoản 3 Điều 5, Khoản 3 Điều 8 Thông tư số 30/2020/TT-BYT ngày 31 tháng 01 năm 2020…" | vbpl:169585; vbpl:132188; vbpl:166456 | trung bình. Ngày ký TT 30/2020 bị chép lệch trong lệnh bãi bỏ. |
| 9ed890ee@2008-07-01 | giữ | `giu` | Luật 19/2008/QH12 Điều 2; 01/07/2008 (lời văn). Đ13 và Đ38 viết lại, bỏ phân hạng dự bị. | Đ38 mới: "Hạn tuổi cao nhất của sĩ quan dự bị quy định như sau: Cấp Úy: 51;…" | vbpl:12805 | cao |
| b3ab65f0@2018-11-15 | giữ | `giu` | TT 24/2018/TT-NHNN, khoản 4: bãi bỏ chính báo cáo định kỳ năm; 15/11/2018 (lời văn). Còn Đ20 k2 (báo cáo đột xuất). | "4. Bãi bỏ báo cáo định kỳ hàng năm về thực hiện các yêu cầu kỹ thuật về an toàn bảo mật…" | vbpl:131436; vbpl:46996 | cao |
| b7dde3d0@2026-04-08 | giữ | `giu` | NĐ 116/2026 Đ28; 08/04/2026 (lời văn). Chương VIII chỉ bãi bỏ; NĐ 148/2024 không chạm Đ4 k3. | "Điều 28. Bãi bỏ khoản 3 Điều 4." | vbpl:187830; vbpl:171628 | trung bình. Chưa tra 7c. |
| b7ee85a0@2026-04-08 | giữ | `giu` | NĐ 116/2026 Đ30; 08/04/2026 (lời văn). Không có thành phần hồ sơ thay. | "Điều 30. Bãi bỏ khoản 2 Điều 10." | vbpl:187830 | trung bình. Đ31 k2 chuyển tiếp chỉ cho hồ sơ đã nộp. |
| c87f45e0@2018-09-15 | giữ | `giu` | NĐ 100/2018, khoản 4 bãi bỏ Đ16 NĐ 11/2013; 15/09/2018 (lời văn). Không có quy định thay; Lawgical 1 lượt không ra. | "4. Bãi bỏ Điều 16 Nghị định số 11/2013/NĐ-CP…" | vbpl:130011; vbpl:28073 | trung bình. NĐ 11/2013 còn dẫn chiếu treo về Đ16. |
| **d88e3c54@2013-07-01** | loại | `relocation_unclear` | Luật 20/2012 k36 bãi bỏ Đ52; 01/07/2013 (lời văn). Cùng đợt, Đ49 k2 mới: luật sư cá nhân (nay là luật sư làm theo hợp đồng lao động) phải mua bảo hiểm khi hợp đồng có thỏa thuận. Yếu tố 6, 7 đạt; yếu tố 2, 3 không chắc. Chuyển tiếp hai năm chuyển đổi. | Đ49 k2: "Trường hợp hợp đồng lao động có thỏa thuận thì luật sư hành nghề với tư cách cá nhân phải mua bảo hiểm trách nhiệm cho hoạt động hành nghề…" | vbpl:28019 | trung bình. Chỗ nghi: Đ49 k2. |
| d88e3ee8@2013-07-01 | giữ | `giu` | Luật 20/2012 k36 bãi bỏ Đ63; 01/07/2013 (lời văn). Đoàn luật sư dùng Điều lệ Liên đoàn; Đ67 k3 là thủ tục khác (Bộ Tư pháp phê duyệt Điều lệ Liên đoàn). Yếu tố 2 không đạt. | Đ67 k1: "…được áp dụng thống nhất đối với Liên đoàn luật sư Việt Nam và các Đoàn luật sư." | vbpl:28019 | cao |
| e782e8ce@2022-01-01 | giữ | `giu` | NĐ 126/2021, khoản 2 bãi bỏ Điều 28 NĐ 119/2017 (cấp trên); 01/01/2022 (lời văn). Không có quy định mới nào về mũ bảo hiểm. | "2. Bãi bỏ … Điều 28; … Nghị định số 119/2017/NĐ-CP." | vbpl:154199 | trung bình |
| e9ffd3da@2017-01-20 | giữ | `giu` | TT 27/2016/TT-BCT Đ1 k2; 20/01/2017 (lời văn). Cùng đợt k1 bỏ luôn Điều 4 TT 14/2013 (điều kiện kinh doanh than). | "1. Bãi bỏ Điều 4 Thông tư số 14/2013/TT-BCT…; 2. Bãi bỏ khoản 1 Điều 4 Thông tư số 15/2013/TT-BCT…" | vbpl:116451; vbpl:46689 | trung bình. Dòng có đáp án có nguy cơ `reference_only`. |
| f01b7674@2019-02-18 | giữ | `giu` | TT 54/2018/TT-BCT bãi bỏ Đ7 TT 44/2015 (cấp trên); 18/02/2019 (lời văn). QĐ 24/2014 Đ15 k2 không có ý kiến UBND tỉnh trong hồ sơ. | QĐ 24/2014 Đ15 k2: "Chủ đầu tư xây dựng đề án giá điện… trình Bộ Công Thương thẩm định…" | vbpl:134865; vbpl:33792 | trung bình |

**Tổng:**

| Kết luận | Số lineage |
|---|---:|
| `giu` | 12 |
| `relocation_unclear` | 1 |
| `relocated` | 0 |
| `superseded_by_other_norm` | 0 |
| `q1_case` = true | 0 |

**Ghi chú về dòng có đáp án (không đổi đáp án):**
- **e9ffd3da@2017-01-19:** nửa đáp án là dẫn chiếu TT 14/2013, có nguy cơ `reference_only` hoặc `unanswerable_as_asked`.
- **d88e3c54@2013-06-30:** không thấy lỗi.
- **9784e330:** lệnh bãi bỏ chép sai ngày ký văn bản gốc. Đây không phải lỗi đáp án.

## Quy tắc còn mở
- **N1. T6 có điều khoản chuyển tiếp cho chủ thể theo chế độ cũ tồn tại thêm** (d88e3c54: hai năm chuyển đổi luật sư cá nhân). Bước 7 chỉ hỏi "chuyển tiếp có giữ khoản cũ không" ở phần khoảng trống. Chưa có quy tắc khi chuyển tiếp chỉ giữ tư cách chủ thể, không nói giữ nghĩa vụ cũ. Tôi đã dùng `relocation_unclear`; nếu CMT muốn, có thể ghi thêm `transitional_rule`.
- **N2. Đáp án T6 nửa nội dung, nửa dẫn chiếu** (e9ffd3da). R5 chỉ nói đáp án "chỉ có dẫn chiếu". Cần CMT nói rõ có loại trường hợp hỗn hợp khi câu hỏi hỏi đúng phần dẫn chiếu không.
- **Q1:** batch này không có ca nào đúng loại Q1. 913092a4 chỉ giáp ranh và đã ghi lý do.

## Nguồn đã dùng
- **Bản crawl** `data/raw/`: 111884, 37568, 131594, 26159, 17135, 169585, 147385, 132188, 166456, 12805, 6153, 131436, 46996, 187830, 171628, 135886, 130011, 28073, 28019, 15076, 154199, 125654, 116451, 46691, 46689, 134865, 94337, 33792.
- **Lawgical:** 1 lượt, `search_legal_docs` "chủ đầu tư dự án đầu tư phát triển đô thị tổ chức chính trị xã hội có chức năng phù hợp…". Không ra văn bản thay. `get_account_status` đầu phiên: 15/20 đã dùng.
- **Không dùng:** WebFetch, WebSearch, API trực tiếp. Không có lỗi truy cập.
- **Giới hạn:**
  - Ngày hiệu lực của nhiều văn bản lấy từ đoạn `in_force` trong batch (trích từ bản crawl), không mở lại riêng.
  - Bước 7d chưa tra hết ở các dòng ghi "trung bình".

## Model
Claude Opus 5.5 (`claude-opus-5-5`), vai `legal-adjudicator`, ngày 11/11/2026. Phiên không có công cụ ghi file; nội dung này do phiên điều phối ghi ra đĩa.
