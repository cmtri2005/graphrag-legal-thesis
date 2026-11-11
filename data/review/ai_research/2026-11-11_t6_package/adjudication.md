# Chốt ca khó T6 dev, VBHN và thuế 2012 (11/11/2026)

**AI-chốt (`legal-adjudicator`), CMT ủy quyền, chưa qua luật sư.** CMT ủy quyền theo quyết định 2026-11-11 trong `docs/plans/active/master-plan.md`. Không có luật sư hay người độc lập nào kiểm các kết luận dưới đây, và paper phải ghi rõ điều đó.

Tôi chỉ áp quy tắc đang có:
- định nghĩa §3 R2/R3/R4, §4 T6, §6 điều 7, §7;
- annotation bước 7 (bảy yếu tố);
- sổ quyết định ngày 24/10, 26/10 và 10/11.

Tôi không dùng proposed2 và không mở `runs/` để lấy câu trả lời của hệ. Có một ngoại lệ: tôi đọc `runs/rebuild_20261110/after/release/vilextime_silver.jsonl` chỉ để lấy id dòng ở mục C.

**Quy ước nguồn.** "vbpl:<ID>" là bản crawl API vbpl lưu ở `data/raw/<ID>.json` (nguồn chính thức, cùng nguồn với `https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/<ID>`). Phiên này **không gọi API trực tiếp**, chỉ đọc bản lưu.

**Quy ước ngày hiệu lực:**
- Ngày ghi "(lời văn)" là ngày tôi tự đọc trong điều hiệu lực.
- Ngày ghi "(phiếu)" lấy từ `kiem_evidence.jsonl` hoặc metadata. Đây là dữ liệu của chính đề tài, không phải bằng chứng độc lập.

---

## 1. Bảng A: 17 dòng T6 dev "không đáp án"

Mã kết luận:
- `giu`: không chuyển chỗ, nhãn "không đáp án" đúng.
- `relocated`, `relocation_unclear`, `superseded_by_other_norm`: loại dòng theo R2 hoặc R3; không đổi đáp án.

| id@as_of | Kết luận | Mã | Căn cứ (số hiệu, Điều/Khoản, hiệu lực) | Trích | Link | Tin cậy |
|---|---|---|---|---|---|---|
| 41522558@2026-05-18 | loại | `relocation_unclear` | TT 88/2025/TT-BNNMT Đ5 k1 d. Cùng thông tư này "Bãi bỏ Điều 11, 12, 13, 15 TT 10/2025" (có dấu vết, cùng Bộ, cùng cấp). Hiệu lực 01/01/2026 (phiếu). Câu hỏi hỏi cả "ở dạng bản nào", nhưng lời văn mới bỏ chữ "Bản chính" (cũ: "d) Bản chính biên bản họp tổ chức cộng đồng"). Không chắc ở yếu tố 3 (điều kiện về dạng bản). | "d) Biên bản họp tổ chức cộng đồng theo Mẫu số 04 Phụ lục I ban hành kèm theo Thông tư này." | vbpl:186303 | trung bình |
| 8ac0e590@2026-08-08 | giữ | `giu` | TT 32/2026/TT-BXD k2: "Bãi bỏ các điều 2, 3, 4, 5, 6, 7, 8, 9 và 19 TT 10/2021"; thông tư này không có quy định về hồ sơ điện tử. NĐ 207/2026 Đ11 (hiệu lực 01/07/2026, phiếu) chỉ quy định lập hồ sơ theo pháp luật giao dịch điện tử, trách nhiệm về nội dung và in bản giấy khi có yêu cầu. Yêu cầu được hỏi ("ghi nhận các nội dung cần quản lý") không còn, nên yếu tố 1 và 3 rõ ràng không đạt. | NĐ 207 Đ11 k2: "các hồ sơ dưới định dạng tập tin điện tử… phải được trích xuất, in thành bản giấy và được chủ đầu tư xác nhận." | vbpl:58e44110-838c-11f1-a8a6-350e41594052; vbpl:c4911dc0-6e5b-11f1-b871-73e465f01c71 | trung bình. Ghi chú: câu hỏi chép gần hết đáp án của dòng "có" (nguy cơ `question_leaks` ở dòng 2025-10-21). |
| **6cab03a0@2021-10-21** | theo chữ bước 7 là **giữ**, nhưng **cần quy tắc mới** (mục 4) | `giu` (tạm) | NĐ 150/2018 Đ4 k3: "Bãi bỏ Điều 18." (NĐ 47/2011). Hiệu lực "kể từ ngày 24 tháng 12 năm 2018" (lời văn). Đợt bãi bỏ không có câu "Bổ sung" hay "thay thế". Tại as_of, TT 26/2014/TT-BTTTT Đ7 k1 a (hiệu lực 16/02/2015, lời văn; Lawgical ghi "Còn hiệu lực") quy định đúng nội dung được hỏi. Nhưng yếu tố 6 không đạt (Thông tư cấp thấp hơn Nghị định) và yếu tố 7 không có dấu vết, vì TT có trước và không do lệnh bãi bỏ dẫn tới. | TT 26/2014 Đ7 k1: "Hồ sơ… được lập thành một (01) bộ, gồm: a) Đơn đề nghị cấp giấy phép nhập khẩu tem bưu chính theo mẫu tại Phụ lục II của Thông tư này" | vbpl:132170; vbpl:26637; Lawgical `get_document` 26/2014/TT-BTTTT | trung bình |
| 6e3d884a#k1#h@2025-09-06 | loại | `relocated` | TT 36/2024/TT-BGTVT Đ46 k1 h. Cùng thông tư này bãi bỏ "Điều 8 TT 36/2020" (có dấu vết, cùng Bộ, cùng cấp). Hiệu lực 01/01/2025 (phiếu). Cũ (TT 36/2020 Đ8 k1): báo cáo kết quả hoạt động bến xe, do đơn vị kinh doanh vận tải và bến xe khách lập, hằng tháng, chốt từ ngày 01 đến cuối tháng. Mới: báo cáo kết quả hoạt động vận tải, bến xe, cùng chủ thể, hằng tháng. Đạt đủ bảy yếu tố. | "h) Thời gian chốt số liệu báo cáo: từ ngày 01 đến ngày cuối cùng của tháng báo cáo;" | vbpl:173086; vbpl:145902 | cao. Ghi chú: cụm "báo cáo tình hình hoạt động vận tải" trong câu hỏi trùng tên báo cáo năm của Sở ở k2, nên dòng "có" có nguy cơ `question_ambiguous`. |
| 6e30cd9c@2026-06-18 | giữ | `giu` | Luật 72/2025/QH15 bãi bỏ "Điều 7 và Điều 8 của NQ 136/2024/QH15". Từ 01/07/2025 phường "gồm có Hội đồng nhân dân và Ủy ban nhân dân phường". Mô hình chính quyền đô thị Đà Nẵng (phường không có HĐND) đã chấm dứt; Luật Bầu cử 85/2015 là chế độ chung có từ trước, không có dấu vết chuyển. Yếu tố 3 (điều kiện áp dụng) và yếu tố 7 không đạt. Câu hỏi lại ghim khung "chính quyền đô thị… Đà Nẵng". Lô A nói "chuyển chỗ" là không đứng. | "c) Bãi bỏ Điều 7 và Điều 8 của Nghị quyết số 136/2024/QH15…" | vbpl:178340 | trung bình–cao. Chưa mở Luật Bầu cử Đ25. |
| 2cb2c1fa@2020-11-11 | loại | `relocated` | NĐ 59/2017/NĐ-CP Đ12 k1. Cùng NĐ này "Bãi bỏ Điều 18, Điều 19 và Điều 20 NĐ 65/2010" và có điều khoản chuyển tiếp dẫn NĐ 65/2010 (có dấu vết). Cùng Chính phủ. Hiệu lực 01/07/2017 (phiếu). Hành vi "gửi hồ sơ đề nghị cấp giấy phép tới cơ quan có thẩm quyền" giữ nguyên, chỉ thêm cách gửi. | "1. Hồ sơ đề nghị cấp Giấy phép tiếp cận nguồn gen… được gửi tới cơ quan nhà nước có thẩm quyền theo một trong các cách sau: nộp trực tiếp… hoặc gửi qua đường bưu điện." | vbpl:124218 | cao |
| ecff2318@2018-06-10 | giữ | `giu` | NĐ 154/2013 chuyển tiếp: "Các quy định tại Chương III NĐ 71/2007… hết hiệu lực". Hiệu lực 01/01/2014 (phiếu). Mô hình mới khác hẳn: "Tổ chức quản lý khu CNTT tập trung" do Thủ tướng hoặc Chủ tịch UBND tỉnh được ủy quyền quyết định thành lập và ban hành quy chế (Đ19 k1). UBND tỉnh không còn được xác định là "cơ quan quản lý nhà nước khu CNTT tập trung". Yếu tố 2 và 6 rõ ràng không đạt. | Đ19 k1: "Thủ tướng Chính phủ quyết định hoặc ủy quyền cho Chủ tịch Ủy ban nhân dân cấp tỉnh quyết định thành lập Tổ chức quản lý và ban hành quy chế hoạt động." | vbpl:32784 | trung bình. Chưa đọc trọn Đ27 k4. |
| 7dd23e64@2026-08-06 | loại | `relocation_unclear` | NĐ 182/2026 Đ? k6: "Bãi bỏ quy định tại Điều 5 NĐ 61/2006". Hiệu lực 07/07/2026 (phiếu). Cùng NĐ quy định lại phụ cấp ưu đãi trong Đ3 (có dấu vết, cùng Chính phủ), nhưng đổi cấu trúc và mức: chín bậc 20–80%, trường chuyên biệt rải ở nhiều khoản. Không chắc ở yếu tố 4 và 5: mục "mức được đổi" ở yếu tố 5 viết cho chế tài, không rõ có áp cho chế độ phụ cấp (xem mục 4). | Đ3 k9: "Mức phụ cấp ưu đãi 80%… c) Nhà giáo giảng dạy trong… trường chuyên biệt đóng trên địa bàn có điều kiện kinh tế - xã hội đặc biệt khó khăn" | vbpl:d36ee5e0-5d60-11f1-a077-230154264f8d; vbpl:15925 | trung bình |
| c203f3d0@2019-11-05 | loại | `relocated` | TT 15/2018/TT-BTC Đ3 k4. Cùng thông tư này "Bãi bỏ… Điều 40 TT 111/2015" (có dấu vết, cùng Bộ Tài chính). Hiệu lực 01/04/2018 (phiếu). Giữ mức tối đa 0,1% và việc Kho bạc Nhà nước thỏa thuận mức phí. | "Chi phí hoạt động đại lý phát hành (nếu có)… tối đa 0,1% giá trị danh nghĩa… Kho bạc Nhà nước thỏa thuận và thống nhất với đại lý phát hành mức phí…" | vbpl:128189 | cao |
| fe9e225a#k5@2025-11-08 | loại | `relocation_unclear` | TT 80/2021 bãi bỏ "Điều 14…21 Chương IV TT 151/2014". Hiệu lực 01/01/2022 (phiếu). Khoản cũ có hai ý: (i) quyết toán năm theo mẫu 04/TNDN; (ii) không phát sinh thường xuyên thì khai từng lần, không quyết toán. NĐ 126/2020 Đ8 k4 đ (cấp cao hơn, có trước) chỉ phủ ý (ii). Chưa tìm thấy chỗ của ý (i). | NĐ 126/2020 Đ8 k4 "đ) Thuế giá trị gia tăng, thuế thu nhập doanh nghiệp không phát sinh thường xuyên… tỷ lệ trên doanh thu…" | vbpl:37430; vbpl:151086; vbpl:146459 | thấp–trung bình. Câu hỏi "được xác định ra sao" rất mơ hồ. |
| **7dc9e82a@2025-05-18** | loại | `relocation_unclear` | Dòng gốc là khoản 2 Đ8 TT 06/2023, sửa k4 Đ7 TT 90/2014. TT 48/2023 Đ2 bãi bỏ "Điều 7" TT 90/2014 (k1) và "Điều 8 TT 06/2023" (k3), hiệu lực 15/02/2024 (phiếu). TT 48/2023 không quy định lại thủ tục công bố. Chỗ nghi là NĐ 32/2014 Đ11 "Công bố đưa vào khai thác…" (sửa bởi NĐ 25/2023, cấp cao hơn), nhưng tôi chưa mở lời văn và chưa xác định văn bản này còn hiệu lực tại 18/05/2025. Mục lục NĐ 165/2024 (hướng dẫn Luật Đường bộ 2024) không có điều riêng về "công bố đưa vào khai thác"; Đ26 chỉ về phương án tổ chức giao thông. **Không đủ căn cứ** để kết luận chuyển chỗ hay không, nên áp câu cuối R2. | TT 48/2023 Đ2 k1: "Bãi bỏ Điều 2; Điều 5; Điều 7;… của Thông tư số 90/2014/TT-BGTVT" | vbpl:165034; vbpl:161092; Lawgical (2 lượt tìm và mục lục) | thấp. Ghi chú H5: dòng gốc là điều khoản sửa đổi chứ không phải điều khoản đích. |
| 92d51460@2026-03-05 | loại | `relocation_unclear` | NĐ 26/2026 bãi bỏ các Điều 10–15, 17–20 NĐ 33/2024. Hiệu lực 17/01/2026 (phiếu). Cùng NĐ quy định: cơ quan cấp "Giấy phép sản xuất, kinh doanh, xuất khẩu, nhập khẩu hóa chất cần kiểm soát đặc biệt…" "là cơ quan có thẩm quyền thu hồi". Quy tắc "cơ quan cấp thì thu hồi" giữ nguyên, nhưng loại giấy phép "hóa chất Bảng" đã gộp vào nhóm "cần kiểm soát đặc biệt", nên không chắc ở yếu tố 2. Câu hỏi ghim khung "thực hiện Công ước", và có chuyển tiếp cho giấy phép đã cấp. Số Điều (22) lấy theo lô A, tôi chưa tự xác nhận. | "…là cơ quan có thẩm quyền thu hồi Giấy chứng nhận; Giấy phép đã cấp cho tổ chức, cá nhân." | vbpl:186579 | trung bình (chắc chắn phải loại; phân vân giữa `relocated` và `relocation_unclear`) |
| 20ee7b9c@2025-12-04 | giữ | `giu` | Luật 72/2025 bãi bỏ Đ7, Đ8 NQ 136/2024. Cấp quận không còn từ 01/07/2025, nên không có chủ thể kế thừa "UBND quận" (yếu tố 2 không đạt). | như dòng 6e30cd9c | vbpl:178340 | cao |
| **6caa8e70@2021-09-03** | theo chữ bước 7 là **giữ**, nhưng **cần quy tắc mới** (mục 4) | `giu` (tạm) | Cùng tình huống với 6cab03a0: NĐ 150/2018 Đ4 k3 "Bãi bỏ Điều 18." từ 24/12/2018 (lời văn). TT 26/2014 Đ5 k1 (phải xin giấy phép), Đ6 k2 (miễn dưới 500 con), Đ7 (Bộ TTTT cấp) vẫn điều chỉnh. Yếu tố 6 không đạt (cấp thấp hơn), yếu tố 7 không có dấu vết, cấu trúc tách ba điều. Luật Bưu chính 49/2010 Đ37 k2 chỉ dẫn chiếu ("thực hiện theo quy định của cơ quan nhà nước có thẩm quyền về bưu chính"). | TT 26/2014 Đ5 k1: "Tổ chức, cá nhân nhập khẩu tem bưu chính thuộc danh mục quy định tại Phụ lục I… phải thực hiện thủ tục xin cấp giấy phép nhập khẩu tem bưu chính." | vbpl:132170; vbpl:26637; vbpl:25701; Lawgical | trung bình |
| 890e6428@2021-05-28 | giữ | `giu` | NĐ 151/2018: "Bãi bỏ các điểm b, đ, g khoản 1 Điều 11" NĐ 17/2012. Điểm đ cũ: "Có mua bảo hiểm trách nhiệm nghề nghiệp cho các kiểm toán viên hành nghề tại Việt Nam". Hiệu lực 07/11/2018 (phiếu). NĐ 151/2018 không quy định lại. Luật Kiểm toán độc lập 67/2011 chỉ đặt nghĩa vụ bảo hiểm cho "doanh nghiệp kiểm toán" (cho phép thay bằng quỹ dự phòng) và dẫn chiếu "Cung cấp dịch vụ kiểm toán qua biên giới theo quy định của Chính phủ". Chủ thể khác (yếu tố 2), không có dấu vết. | Luật 67/2011: "5. Mua bảo hiểm trách nhiệm nghề nghiệp cho kiểm toán viên hành nghề hoặc trích lập quỹ dự phòng rủi ro nghề nghiệp…" | vbpl:27508; vbpl:132174; vbpl:26750 | trung bình–cao. Chưa mở NĐ 84/2016. |
| 1634ac90@2025-01-31 | loại | `superseded_by_other_norm` (bước 7d) | TT 17/2024 bãi bỏ "khoản 4 Điều 4, … khoản 4 Điều 7 TT 45/2022", hiệu lực 15/07/2024 (phiếu), nhưng chỉ quy định thăng hạng lên hạng I và II, không có hạng IV. Khoản cũ (Đ7 k4) dẫn tới NĐ 115/2020 Đ32. Văn bản cấp cao hơn này vẫn quy định cùng vấn đề cho mọi viên chức tại as_of. | NĐ 115/2020 Đ32 k1: "Viên chức được đăng ký dự thi hoặc xét thăng hạng lên chức danh nghề nghiệp cao hơn liền kề khi có đủ các tiêu chuẩn, điều kiện sau:" | vbpl:167415; vbpl:159051; vbpl:144137 | trung bình. Chưa mở NĐ 85/2023 sửa Đ32. |
| f1fc5a86@2026-08-17 | giữ | `giu` | TT 21/2025/TT-BVHTTDL Đ11: "Bãi bỏ khoản 4 và khoản 7 Điều 3 TT 29/2018". Hiệu lực 26/12/2025 (phiếu). Đây là đợt cắt điều kiện: cùng TT bãi bỏ trọn nhiều thông tư điều kiện của môn khác. Không có quy định thay. | "Điều 11. Bãi bỏ khoản 4 và khoản 7 Điều 3 Thông tư số 29/2018/TT- BVHTTDL…" | vbpl:186002 | trung bình. Chưa tra bước 7d (NĐ điều kiện kinh doanh thể thao). |

**Tổng A:**

| Kết luận | Số dòng |
|---|---:|
| giữ | 6 |
| `relocated` | 3 |
| `relocation_unclear` | 5 |
| `superseded_by_other_norm` | 1 |
| giữ tạm, cần quy tắc mới | 2 (tem) |

So với tra trước:
- Năm dòng tôi kết luận khác lô A: 6e30cd9c, ecff2318 (A nói chuyển chỗ có cờ, tôi giữ); 1634ac90 (thành R3); và hai dòng tem.

**Hai dòng tem.** Lô A kết luận "chuyển chỗ" là sai theo bảy yếu tố: yếu tố 6 không đạt và yếu tố 7 không có dấu vết. Lô B kết luận "đúng" là khớp chữ bước 7, nhưng lô B chưa tra TT 26/2014, nên lý lẽ chưa đủ. Cả hai dòng xử lý như nhau.

**Dòng 7dc9e82a** vẫn chưa đủ căn cứ, nên tôi loại theo câu cuối R2, không kết luận "giữ".

## 2. Bảng B: VBHN, tín hiệu bãi bỏ, H021

| Ca | Đề xuất cũ (CMT xác nhận tạm) | Chốt | Lý do / tra lại |
|---|---|---|---|
| 1 (NĐ 124/2008 Đ13), các mốc 2010-03-26, 2012-03-01, 2013-03-30 | đúng | **giữ, kèm cờ cho mốc 2012-03-01** | NĐ 122/2011 k9 Đ1 sửa Đ13. Mốc 2010 và 2013 không vướng. Mốc 2012-03-01 cũng có thể vướng như mục C: doanh nghiệp chọn năm tài chính có thể vẫn ở kỳ trước năm 2012. Mốc này nằm ngoài phần được giao nên tôi chỉ báo, không chốt. |
| 1, các mốc 2012-01-31, 2012-02-29 | để mở | xem mục C | — |
| 2, 3 (NĐ 11/2013 Đ2 k9/k10), mốc v1 | đúng | **giữ** | Lời văn gốc khớp (vbpl:28073). |
| 2, 3, mốc 2026-01-22 và 2026-06-15 (không đáp án) | đúng | **giữ ngày bãi bỏ**; dùng làm dòng T6 thì phải kiểm tiếp | Tra lại vì căn cứ yếu. NĐ 35/2026 (vbpl:186907) có điều bãi bỏ "a) Khoản 9, 10 Điều 2… của NĐ 11/2013", hiệu lực 22/01/2026 (API; chưa đọc điều hiệu lực). Đ3 NĐ 35/2026 không định nghĩa lại hai thuật ngữ. Luật Xây dựng 135/2025 (vbpl:185659) có "7. Dự án đầu tư xây dựng khu đô thị là…" với lời văn khác, và "có hiệu lực thi hành từ ngày 01 tháng 7 năm 2026" (lời văn). Vậy câu hỏi lộ ra trong đề xuất cũ đã có lời đáp: luật này không thay ở hai mốc trên. Chưa kiểm Luật Xây dựng 50/2014 (sửa 2020) Đ3 và Luật Quy hoạch đô thị và nông thôn 47/2024 theo bước 7d, nên nếu đưa vào T6 thì chưa đủ căn cứ. |
| 4, 5 (TT 15/2019 Đ2 k1) | đúng v1/v2 | **giữ** | TT 24/2024 có hiệu lực 27/01/2025 (đề xuất cũ và phiên chính đều đã kiểm lời văn). Không tra lại. |
| 6 (NĐ 100/2024 Đ5 k1) | đúng v1/v2 | **giữ** | NĐ 178/2025 Đ28 k3 a, hiệu lực 01/07/2025. VBHN lệch, đồ thị đúng. Không tra lại. |
| 7 (NĐ 209/2013 Đ3 k11) | đúng | **giữ** | Có lỗi thiếu câu (H5 mục 1), nhưng đó không phải lỗi chọn phiên bản. Không tra lại. |
| 8, 9 (NĐ 156/2020 Đ4) | đúng | **giữ** | Không tra lại. |
| Tín hiệu 1 (TT 23/2018 Đ5 k1 d), tín hiệu 2 (Đ7 k1 a) | tín hiệu giả | **giữ** | Tôi đã kiểm lại vbpl:152678: "16. Bãi bỏ các điểm b, c và đ khoản 1 Điều 5; điểm b và điểm c khoản 1 Điều 6; điểm b và điểm c khoản 1 Điều 7." Điểm d Đ5 và điểm a Đ7 không bị bãi bỏ. |
| H021 (Pháp lệnh 17/2004 Đ2, mốc 2016-09-25) | loại, `superseded_by_other_norm` | **giữ** | Tra lại chỗ hở cũ trong Luật Dự trữ quốc gia 22/2012/QH13 (vbpl:28029): điều hiệu lực chỉ ghi "Luật này có hiệu lực thi hành từ ngày 01 tháng 7 năm 2013", không có câu bãi bỏ Pháp lệnh. Pháp lệnh không hết hiệu lực do suy diễn (định nghĩa §2). Luật của Quốc hội cao hơn và quy định cùng vấn đề, nên áp R3. Chưa tìm thêm văn bản bãi bỏ Pháp lệnh trong giai đoạn 2013–2016 ngoài một lượt tìm của phiên trước. |

## 3. Mục C: hai dòng thuế 2012

Hai dòng:
- `vilextime:T2:provision:1089c3ac-df56-11f0-8679-ff3f54843828:2012-01-31` (chế độ `truoc_hieu_luc`)
- `vilextime:T2:provision:1089c3ac-df56-11f0-8679-ff3f54843828:2012-02-29` (chế độ `ranh_gioi`)

**Chốt: `q3=khong/question_ambiguous` cho cả hai dòng, verdict `khong_dat`, loại.** Căn cứ là sổ quyết định 10/11 mục 4. Không chọn đáp án theo ngày hiệu lực, cũng không chọn đáp án theo kỳ tính thuế.

- NĐ 122/2011 Đ2 k1 (vbpl:27261; lời văn): "có hiệu lực thi hành từ ngày 01 tháng 3 năm 2012 và áp dụng cho kỳ tính thuế từ năm 2012 trở đi."
- NĐ 124/2008 (vbpl:11606; lời văn): "Doanh nghiệp được lựa chọn kỳ tính thuế theo năm dương lịch hoặc năm tài chính nhưng phải đăng ký với cơ quan thuế trước khi thực hiện."
- Doanh nghiệp tính thuế theo năm dương lịch thì từ 01/01/2012 đã ở kỳ 2012, nên hai mốc nhận Đ13 mới. Doanh nghiệp tính theo năm tài chính khác năm dương lịch thì có thể vẫn ở kỳ trước, nên nhận Đ13 cũ. Câu hỏi ("Một doanh nghiệp có thu nhập từ bất động sản…") không nêu dữ kiện này. Đây đúng là trường hợp "hai doanh nghiệp thuộc hai kỳ tính thuế" mà mục 4 ngày 10/11 nêu.
- Không áp phán quyết 26/10 mục 3. Năm ngân sách thống nhất theo năm dương lịch (Luật 01/2002 Đ14), còn kỳ tính thuế thì do doanh nghiệp chọn.

Object hòa giải cho lineage có nhãn thô khóa (silver lượt 3):

```json
{"lineage_id":"provision:1089c3ac-df56-11f0-8679-ff3f54843828","raw_a_sha256":"a51d23cf1dff4079cf985878b69604287cd64e413bb61a792f137dbfc741a4d6","raw_b_sha256":"a79a5e034bf5fffba8d39b0d2cdb228bffd37ec5e03aa2e56e7c09c48622e7bb","disputed_fields":["q2","q2_reason"],"proposed_label":{"q1":"sai","q1_reason":"gold_wrong","q2":"khong","q2_reason":"group_mismatch","q3":"khong","q3_reason":"question_ambiguous","q4":"khong","q4_reason":"","verdict":"khong_dat","note":"[phân vân] q1, q2 phụ thuộc kỳ tính thuế (năm dương lịch: hai mốc 29/02 và 01/03 đều bản mới; năm tài chính: có thể đều bản cũ). Q1 giữ như A, B (không tranh chấp). Lý do loại quyết định là q3 theo 10/11 mục 4."},"disposition":"both_wrong","reasoning":"A, B đúng về nội dung NĐ 122/2011 k9 Đ1 và Đ2 k1. Cả hai cùng bỏ sót Q3: câu hỏi thiếu kỳ tính thuế, mà NĐ 124/2008 cho doanh nghiệp chọn năm dương lịch hoặc năm tài chính. B đúng hơn A ở Q2 chỉ khi giả định năm dương lịch.","evidence":["vbpl:27261 Đ2 k1","vbpl:11606 câu về kỳ tính thuế"],"open_questions":["Mốc 2012-03-01 cùng lineage có thể vướng cùng lý do"],"labeler":"ai-adjudicator","label_origin":"ai","verification_status":"not_verified","human_adjudication_required":true}
```

`human_adjudication_required` giữ `true` theo schema; theo ủy quyền ngày 11/11, CMT duyệt thay luật sư.

## 4. Ca "cần quy tắc mới" (chưa áp, chờ CMT)

1. **Quy phạm cấp thấp hơn hoặc có từ trước vẫn quy định đúng nội dung được hỏi, nhưng không phải chỗ chuyển đến** (6cab03a0, 6caa8e70).
   - Theo chữ bước 7, yếu tố 6 không đạt, nên "bước này đạt" và giữ nhãn "không đáp án".
   - Theo câu đầu R2 ("câu hỏi về nội dung được trả lời bằng quy phạm đang điều chỉnh nội dung đó"), đáp án đúng tại as_of lại là TT 26/2014. Hai câu mâu thuẫn nhau.
   - Đề xuất: thêm vào bước 7 một nhánh "có quy phạm khác (kể cả cấp thấp hơn hoặc có từ trước) đang điều chỉnh đúng phần được hỏi tại as_of thì loại với `relocation_unclear` (hoặc mã mới)". Trước khi CMT quyết, không đưa hai dòng này vào bộ test.
2. **Yếu tố 5 "mức được đổi" có áp cho chế độ quyền lợi (phụ cấp, mức chi) hay không**, hay chỉ cho chế tài (7dd23e64). Tôi đã dùng `relocation_unclear`. Đề xuất ghi rõ phạm vi của yếu tố 5.
3. **Dòng T6 lấy điều khoản sửa đổi làm đích** (7dc9e82a: Đ8 TT 06/2023 sửa TT 90/2014). Quy tắc chưa nói lệnh bãi bỏ chính điều sửa đổi có hệ quả gì. Đề xuất ghi vào H5 và quy tắc dựng T6: chỉ lấy điều khoản đích.
4. Mục C: mục 4 ngày 10/11 đã đủ để chốt, nên không cần quy tắc mới. Chỉ cần quyết có rà mốc 2012-03-01 hay không.

## 5. Nguồn đã dùng

- **Lawgical: 4 lượt** trong phiên (đúng ngân sách):
  - `get_document` 26/2014/TT-BTTTT;
  - `search_legal_docs` hai lần (thủ tục công bố đưa cao tốc vào khai thác);
  - `get_summary` 165/2024/NĐ-CP.
  - `get_account_status`: đầu phiên 6/20, cuối phiên 14/20 (các phiên song song dùng thêm 4).
- **API vbpl:** không gọi trực tiếp. Tôi đọc bản crawl `data/raw/<ID>.json` các ID 26637, 132170, 25701, 186303, 58e44110-…, c4911dc0-…, 173086, 145902, 178340, 124218, 32784, 15925, d36ee5e0-…, 128189, 37430, 151086, 146459, 161092, 165034, 186579, 27508, 132174, 26750, 167415, 159051, 144137, 186002, 186907, 28073, 185659, 28029, 19465, 152678, 11606, và 27261 (qua file input của lượt hòa giải 08/11).
- **Dữ liệu dòng:**
  - `docs/reports/chan-doan-t6-dev-20261111.tsv` (không có cột câu hỏi);
  - câu hỏi lấy từ `data/vilextime/questions.jsonl`;
  - văn bản gốc và văn bản tác động lấy từ `data/review/kiem_evidence.jsonl`;
  - id dòng mục C lấy từ `runs/rebuild_20261110/after/release/vilextime_silver.jsonl` (chỉ lấy id).
- **Không dùng:** WebFetch, WebSearch, proposed2. Không có lỗi truy cập.
- **Giới hạn:**
  - Nhiều ngày hiệu lực lấy từ phiếu hoặc API, chưa đọc lời văn điều hiệu lực (đã đánh dấu "(phiếu)").
  - Tình trạng "Còn hiệu lực" của TT 26/2014 là trạng thái hôm nay theo Lawgical. Suy ra văn bản còn hiệu lực năm 2021 là suy luận.
  - Chưa mở: NĐ 32/2014 Đ11 (sửa 2023), NĐ 85/2023, Luật Bầu cử Đ25, NĐ 84/2016, NĐ 69/2018 (Phụ lục tem bưu chính).

## 6. Model

Claude Opus 5.5 (`claude-opus-5-5`), vai `legal-adjudicator`, phiên mới ngày 11/11/2026. Phiên không mù: đã đọc báo cáo tra trước của `vn-law-verifier` và nhãn A/B ở mục C. Tôi không ghi file nào.
