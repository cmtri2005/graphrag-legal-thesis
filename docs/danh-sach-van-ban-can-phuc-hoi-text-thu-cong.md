# Danh sách văn bản cần phục hồi text thủ công

**Ngày lập:** 14/09/2026

**Mốc corpus:** 12/09/2026

**Tổng số:** 152 văn bản có body hiển thị rỗng trong snapshot hiện tại.

**Mục đích:** dùng số hiệu và tiêu đề để tìm lại toàn văn trên Thư Viện Pháp Luật hoặc nguồn đối chiếu khác, sau đó lưu dưới dạng manual backfill có provenance.

> Danh sách này chỉ là danh sách công việc. Nội dung tìm được từ nguồn khác
> không được ghi đè vào raw response của vbpl.vn và không tự động trở thành
> ground truth pháp lý.

---

## 1. Tiêu chí lập danh sách

Một văn bản được đưa vào danh sách khi thỏa một trong các điều kiện:

| Trường hợp | Số lượng |
|---|---:|
| Thiếu tree và body hiển thị rỗng | 1 |
| Có tree nhưng body rỗng, chưa có provision artifact | 17 |
| Có provision artifact 0 node và body hiển thị rỗng | 134 |
| **Tổng** | **152** |

Việc xác định body rỗng đã bỏ qua nội dung trong `head`, `style` và
`script`, đồng thời giải mã HTML entity. Vì vậy các trang chỉ có vỏ HTML hoặc
`&nbsp;` cũng được xem là không có nội dung pháp lý.

Có thêm **153 văn bản** đang có text nhìn thấy trong HTML nhưng provision
artifact vẫn 0 node. Nhóm đó là lỗi parser/căn chỉnh và **không nằm trong danh
sách tìm thủ công này**.

---

## 2. Thứ tự ưu tiên

| Mức | Số lượng | Cách xử lý |
|---|---:|---|
| P0 | 10 | Tìm và nhập trước vì là seed trực tiếp của bốn miền, đồng thời được metadata đánh dấu Trung ương và QPPL |
| P1 | 13 | Tìm tiếp vì là QPPL Trung ương hỗ trợ chuỗi phả hệ |
| P2 | 129 | Rà soát phạm vi trước; chỉ nhập nếu cần cho graph hoặc benchmark |

Tìm bằng **số hiệu trong dấu ngoặc kép** trước. Nếu có nhiều kết quả, đối chiếu
thêm tiêu đề, cơ quan ban hành và ngày ban hành.

## 3.1. P0 — Seed trực tiếp, Trung ương và QPPL

| STT | Số hiệu để tìm | Tiêu đề đầy đủ | Cơ quan | Ngày ban hành | ID vbpl | Miền seed | Lý do | Trạng thái |
|---:|---|---|---|---|---|---|---|---|
| 1 | `06/2026/TT-BCT` | Thông tư số 06/2026/TT-BCT Quy định về hạn ngạch thuế quan nhập khẩu để thực hiện Bản Thỏa thuận thúc đẩy thương mại song phương giữa Chính phủ nước Cộng hòa Xã hội Chủ nghĩa Việt Nam và Chính phủ Vương quốc Campuchia giai đoạn 2025 - 2026 | Bộ Công Thương | 2026-02-12 | `186996` | Thuế | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 2 | `101/2025/TT-BTC` | Thông tư số 101/2025/TT-BTC Hướng dẫn nguyên tắc kế toán áp dụng đối với doanh nghiệp môi giới bảo hiểm | Bộ Tài chính | 2025-10-29 | `187768` | Doanh nghiệp–đầu tư | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 3 | `12/LĐTBXH-TT` | Thông tư số 12/LĐTBXH-TT Hướng dẫn việc kiến nghị điều chỉnh Danh mục các doanh nghiệp không được đình công | Bộ Lao động - Thương binh và Xã hội | 1997-04-08 | `8653` | Doanh nghiệp–đầu tư | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 4 | `158/2025/TT-BTC` | Thông tư số 158/2025/TT-BTC Quy định chi tiết một số điều của Nghị định số 360/2025/NĐ-CP ngày 31 tháng 12 năm 2025 của Chính phủ quy định chi tiết thi hành một số điều của Luật Thuế tiêu thụ đặc biệt | Bộ Tài chính | 2025-12-31 | `187020` | Thuế | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 5 | `19/2026/TT-BCT` | Thông tư số 19/2026/TT-BCT Quy định về tạm ứng cho Quỹ bình ổn giá xăng dầu từ nguồn ngân sách nhà nước, trích lập Quỹ bình ổn giá xăng dầu và hoàn trả tạm ứng ngân sách nhà nước | Bộ Công Thương | 2026-04-03 | `187743` | Doanh nghiệp–đầu tư | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 6 | `312/2025/NĐ-CP` | Nghị định số 312/2025/NĐ-CP Quy định cơ chế quản lý tài chính dự án đầu tư theo phương thức đối tác công tư và cơ chế thanh toán, quyết toán đối với dự án áp dụng loại hợp đồng BT | Chính phủ | 2025-12-06 | `187840` | Doanh nghiệp–đầu tư | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 7 | `366/2025/NĐ-CP` | Nghị định số 366/2025/NĐ-CP Về quản lý và đầu tư vốn nhà nước tại doanh nghiệp | Chính phủ | 2025-12-31 | `187734` | Doanh nghiệp–đầu tư | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 8 | `40/2026/TT-BTC` | Thông tư số 40/2026/TT-BTC Quy định miễn một số khoản phí, lệ phí nhằm hỗ trợ sản xuất, kinh doanh trong lĩnh vực giao thông vận tải | Bộ Tài chính | 2026-04-06 | `187729` | Giao thông | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 9 | `81/2026/NĐ-CP` | Nghị định số 81/2026/NĐ-CP Quy định xử phạt vi phạm hành chính trong lĩnh vực giao thông đường sắt | Chính phủ | 2026-03-19 | `187551` | Giao thông | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 10 | `84 TC/QÐ/TCT` | Quyết định số 84 TC/QÐ/TCT Về việc giảm thuế và khoản thu sử dụng vốn năm 1992 | Bộ Tài chính | 1995-02-08 | `109506` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |

## 3.2. P1 — Văn bản Trung ương/QPPL hỗ trợ phả hệ

| STT | Số hiệu để tìm | Tiêu đề đầy đủ | Cơ quan | Ngày ban hành | ID vbpl | Miền seed | Lý do | Trạng thái |
|---:|---|---|---|---|---|---|---|---|
| 11 | `05/2026/TT-BNNMT` | Thông tư số 05/2026/TT-BNNMT Sửa đổi, bổ sung một số điều của Thông tư số 38/2025/TT-BNNMT ngày 02 tháng 7 năm 2025 của Bộ Nông nghiệp và Môi trường quy định về phương pháp xác định chi phí đánh giá tiềm năng khoáng sản, thăm dò khoáng sản phải hoàn trả; mẫu văn bản trong hồ sơ xác định, phê duyệt chi phí đánh giá tiềm năng khoáng sản, thăm dò khoáng sản phải hoàn trả; mẫu văn bản trong hồ sơ xác định, phê duyệt, quyết toán tiền cấp quyền khai thác khoáng sản; mẫu văn bản trong đấu giá quyền khai thác khoáng sản | Bộ Nông nghiệp và Môi trường | 2026-01-16 | `187685` | — | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 12 | `07/2009/TT-BCT` | Thông tư số 07/2009/TT-BCT Về việc cấp Giấy chứng nhận xuất xứ hàng dệt may đối với một số chủng loại hàng xuất khẩu sang Hoa Kỳ | Bộ Công Thương | 2009-04-09 | `11987` | — | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 13 | `07/2025/TT-BNNMT` | Thông tư số 07/2025/TT-BNNMT Quy định phân cấp, phân định thẩm quyền quản lý nhà nước trong lĩnh vực môi trường và biến đổi khí hậu | Bộ Nông nghiệp và Môi trường | 2025-06-16 | `178650` | — | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 14 | `102/2025/TT-BNNMT` | Thông tư số 102/2025/TT-BNNMT Sửa đổi, bổ sung một số điều của Thông tư số 21/2024/TT-BTNMT ngày 21 tháng 12 năm 2024 của Bộ trưởng Bộ Tài nguyên và Môi trường quy định kỹ thuật điều tra, đánh giá tài nguyên và thăm dò khoáng sản đất hiếm | Bộ Nông nghiệp và Môi trường | 2025-12-31 | `186725` | — | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 15 | `105/2025/QH15` | Luật Giám định tư pháp số 105/2025/QH15 | Quốc hội | 2025-12-05 | `187758` | — | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 16 | `108/2025/TT-BTC` | Thông tư số 108/2025/TT-BTC Hướng dẫn lập báo cáo tài chính hợp nhất của đơn vị kế toán hành chính, sự nghiệp | Bộ Tài chính | 2025-11-14 | `187793` | — | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 17 | `14/2025/TT-BNNMT` | Thông tư số 14/2025/TT-BNNMT Quy định phân quyền, phân cấp, phân định thẩm quyền và sửa đổi, bổ sung một số điều của các Thông tư trong lĩnh vực tài nguyên nước | Bộ Nông nghiệp và Môi trường | 2025-06-19 | `178658` | — | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 18 | `141/2025/QH15` | Luật Sửa đổi, bổ sung một số điều của Luật Quản lý nợ công số 141/2025/QH15 | Quốc hội | 2025-12-10 | `187763` | — | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 19 | `28/2017/TT-BTC` | Thông tư số 28/2017/TT-BTC Sửa đổi, bổ sung một số điều của Thông tư số 45/2013/TT-BTC ngày 25 tháng 4 năm 2013 và Thông tư số 147/2016/TT-BTC ngày 13 tháng 10 năm 2016 của Bộ Tàỉ chính hướng dẫn chế độ quản lý, sử dụng và trích khấu hao tài sản cố định | Bộ Tài chính | 2017-04-12 | `121053` | — | Thiếu tree và body rỗng | Chưa tìm |
| 20 | `30/2014/TT-BCT` | Thông tư số 30/2014/TT-BCT Quy định về vận hành thị trường phát điện cạnh tranh | Bộ Công Thương | 2014-10-02 | `37520` | — | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 21 | `343/2016/TT-BTC` | Thông tư số 343/2016/TT-BTC Hướng dẫn thực hiện công khai ngân sách nhà nước đối với các cấp ngân sách | Bộ Tài chính | 2016-12-30 | `121272` | — | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 22 | `63/2025/TT-BTC` | Thông tư số 63/2025/TT-BTC Sửa đổi, bổ sung một số điều của Thông tư số 96/2021/TT-BTC ngày 11 tháng 11 năm 2021 của Bộ trưởng Bộ Tài chính quy định về hệ thống mẫu biểu sử dụng trong công tác quyết toán | Bộ Tài chính | 2025-06-30 | `179084` | — | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 23 | `71/2007/TTLT/BTC-BNV` | Thông tư liên tịch số 71/2007/TTLT/BTC-BNV Hướng dẫn sửa đổi Thông tư liên tịch số 03/2006/TTLT-BTC-BNV ngày 17/01/2006 của Liên Bộ Tài chính - Bộ Nội vụ hướng dẫn thực hiện Nghị định số 130/2005/NĐ-CP ngày 17/10/2005 của Chính phủ quy định chế độ tự chủ, tự chịu trách nhiệm về sử dụng biên chế và kinh phí quản lý hành chính đối với các cơ quan nhà nước | Bộ Tài chính | 2007-06-26 | `13902` | — | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |

## 3.3. P2 — Cần rà soát phạm vi trước khi nhập tay

| STT | Số hiệu để tìm | Tiêu đề đầy đủ | Cơ quan | Ngày ban hành | ID vbpl | Miền seed | Lý do | Trạng thái |
|---:|---|---|---|---|---|---|---|---|
| 24 | `02/2026/NQ-HĐND` | Nghị quyết số 02/2026/NQ-HĐND Quy định chính sách hỗ trợ đối với học sinh đang học bán trú, học sinh thuộc hộ nghèo không thuộc đối tượng hưởng theo Nghị định số 66/2025/NĐ-CP ngày 12 tháng 3 năm 2025 của Chính phủ tại các cơ sở giáo dục phổ thông công lập trên địa bàn tỉnh Tuyên Quang | HĐND Tỉnh Tuyên Quang | 2026-03-28 | `187639` | — | Có tree, body rỗng, chưa có provision artifact | Chưa tìm |
| 25 | `06/TC/TCT` | Công văn số 06/TC/TCT Công văn về việc xác nhận hoàn thuế giá trị gia tăng cho nhà thầu chính thực hiện dự án ODA | Bộ Tài chính | 2004-01-02 | `108178` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 26 | `10061/TC/TCT` | Công văn số 10061/TC/TCT Công văn về việc xử lý chứng từ thanh toán hàng xuất khẩu để xét hoàn thuế nhập khẩu | Bộ Tài chính | 2003-09-29 | `110470` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 27 | `102/2001/TT-BTC` | Công văn số 102/2001/TT-BTC Thông tư hướng dẫn thực hiện vay vốn tín dụng đầu tư phát triển của Nhà nước đối với các dự án đầu tư sản xuất động cơ xe hai bánh gắn máy ở trong nước | Bộ Tài chính | 2001-12-19 | `108939` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 28 | `10216/TC/TCT` | Công văn số 10216/TC/TCT Công văn về việc thủ tục, hồ sơ đối với hàng hoá xuất khẩu được áp dụng thuế suất thuế giá trị gia tăng 0% | Bộ Tài chính | 2001-10-25 | `109013` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 29 | `1033-TC/TCT` | Công văn số 1033-TC/TCT Công văn về việc quản lý thu thuế đối với hoạt động kinh doanh của các nhà khách, nhà nghỉ | Bộ Tài chính | 1991-08-05 | `107943` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 30 | `10479/TC-TCT` | Công văn số 10479/TC-TCT Công văn về việc thuế thu nhập doanh nghiệp kinh doanh SXKT | Bộ Tài chính | 2001-10-31 | `109082` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 31 | `10506/TC/TCT` | Công văn số 10506/TC/TCT Công văn về việc thuế nhập khẩu xe ô tô sát hạch lái xe | Bộ Tài chính | 2002-09-26 | `110018` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 32 | `10592/TC/TCT` | Công văn số 10592/TC/TCT Công văn về việc quản lý thuế thu nhập đối với người có thu nhập cao | Bộ Tài chính | 2002-09-30 | `110017` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 33 | `10945/BTC-TCT` | Công văn số 10945/BTC-TCT Công văn về việc xoá nợ thuế và các khoản phải nộp ngân sách nhà nước | Bộ Tài chính | 2005-08-31 | `110674` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 34 | `10950/TC/TCT` | Công văn số 10950/TC/TCT Công văn về việc miễn, giảm tiền thuê đất | Bộ Tài chính | 2004-09-28 | `110639` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 35 | `11-TC/TCT` | Công văn số 11-TC/TCT Công văn về khai báo đăng ký kinh doanh và kê khai nộp thuế | Bộ Tài chính | 1991-01-02 | `107823` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 36 | `1102-TCT/NV3` | Công văn số 1102-TCT/NV3 Công văn về việc miễn thuế nhập khẩu và thuế giá trị gia tăng đối với thiết bị nhập khẩu tạo tài sản cố định | Bộ Tài chính | 2001-04-03 | `109225` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 37 | `1110/TC/ÐT` | Công văn số 1110/TC/ÐT Công văn về việc xử lý thanh toán vốn đầu tư kế hoạch năm 2001 | Bộ Tài chính | 2002-01-31 | `109237` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 38 | `11218/TC/TCT` | Công văn số 11218/TC/TCT cv về việc tăng cường biện pháp quản lý, sử dụng hoá đơn | Bộ Tài chính | 2001-11-21 | `109244` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 39 | `11448/TC/TCT` | Công văn số 11448/TC/TCT Công văn về việc thuế giá trị gia tăng đối với hoạt động xây dựng lắp đặt công trình ở nước ngoài và cho doanh nghiệp chế xuất | Bộ Tài chính | 2001-11-28 | `109319` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 40 | `11571/TC/ÐT` | Công văn số 11571/TC/ÐT Công văn về việc thời hạn thanh toán vốn đầu tư năm 2002 | Bộ Tài chính | 2002-11-27 | `110044` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 41 | `11597/TC/ÐT` | Công văn số 11597/TC/ÐT Công văn về việc ứng trước kế hoạch vốn đầu tư xây dựng cơ bản 2003 | Bộ Tài chính | 2002-10-27 | `110043` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 42 | `11684/BTC-TCT` | Công văn số 11684/BTC-TCT Công văn về việc hướng dẫn về thuế thu nhập doanh nghiệp | Bộ Tài chính | 2005-09-16 | `110688` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 43 | `11712/TC/TCDN` | Công văn số 11712/TC/TCDN Công văn về việc hướng dẫn Quy trình cổ phần hoá doanh nghiệp nhà nước | Bộ Tài chính | 2003-11-10 | `110538` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 44 | `1182-TC/TCT` | Công văn số 1182-TC/TCT Công văn về việc danh mục hàng hoá được giảm 50% thuế giá trị gia tăng | Bộ Tài chính | 1999-03-15 | `107935` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 45 | `12401/TC/TCT` | Công văn số 12401/TC/TCT Công văn về việc khấu trừ, hoàn thuế giá trị gia tăng đối với mặt hàng nông, lâm, thuỷ sản | Bộ Tài chính | 2004-10-29 | `110546` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 46 | `1261-TC/TCT` | Công văn số 1261-TC/TCT Công văn về việc thuế suất thuế nhập khẩu nguyên liệu sản xuất thuốc paracetamol | Bộ Tài chính | 2001-02-18 | `109017` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 47 | `1266-TC/CTN` | Công văn số 1266-TC/CTN Công văn về việc hướng dẫn thu phí giao thông | Bộ Tài chính | 1988-12-18 | `108836` | Giao thông | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 48 | `1269-TC/TCT` | Công văn số 1269-TC/TCT Công văn về việc xử lý miễn thuế nhập khẩu hàng hóa nhập khẩu bằng nguồn tiền ODA của Chính phủ Pháp theo Nghị định thư Tài chính năm 1996 | Bộ Tài chính | 1997-04-21 | `110165` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 49 | `12725/TC/TCT` | Công văn số 12725/TC/TCT Công văn về việc phân loại mã số, thuế xuất thuế nhập khẩu | Bộ Tài chính | 2002-11-20 | `109797` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 50 | `13393/BTC-ĐT` | Công văn số 13393/BTC-ĐT Công văn về việc quyết toán vốn đầu tư dự án hoàn thành để giải quyết dứt điểm nợ đọng vốn đầu tư xây dựng cơ bản | Bộ Tài chính | 2005-10-24 | `110734` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 51 | `1346-TC/TCT` | Công văn số 1346-TC/TCT Công văn về việc thuế TTÐB đối với mặt hàng rượu sản xuất trong nước | Bộ Tài chính | 1997-04-25 | `108054` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 52 | `13587TC/TCT` | Công văn số 13587TC/TCT Công văn về thuế thu nhập doanh nghiệp của các doanh nghiệp kinh doanh sân golf | Bộ Tài chính | 2004-11-12 | `110563` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 53 | `1361-TC/TCT` | Công văn số 1361-TC/TCT Công văn hướng dẫn thu thuế lợi tức đối với hoạt động bảo hiểm Nhà nước | Bộ Tài chính | 1991-09-26 | `108029` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 54 | `13610/TC/CST` | Công văn số 13610/TC/CST Công văn về việc thuế giá trị gia tăng và thuế thu nhập doanh nghiệp đối với doanh nghiệp di chuyển địa điểm kinh doanh theo quy hoạch | Bộ Tài chính | 2004-11-22 | `110564` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 55 | `1366-TC/TCT` | Công văn số 1366-TC/TCT Công văn về việc thuế đối với các nhà nghỉ công đoàn | Bộ Tài chính | 1991-09-26 | `110223` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 56 | `13897/TC/ÐT` | Công văn số 13897/TC/ÐT Công văn về việc cấp vốn đầu tư xây dựng cơ bản bổ sung kế hoạch năm 2003 | Bộ Tài chính | 2002-12-18 | `109933` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 57 | `14290/TC/TCT` | Công văn số 14290/TC/TCT Công văn về thuế đối với giao dịch quyền chọn mua/bán ngoại tệ | Bộ Tài chính | 2004-12-06 | `110601` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 58 | `1482-TC/TCT` | Công văn số 1482-TC/TCT Công văn về việc thuế giá trị gia tăng đối với xây nhà để bán, xây dựng cơ sở hạ tầng để chuyển nhượng hoặc cho thuê | Bộ Tài chính | 2000-04-18 | `108384` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 59 | `1500/TC/ĐT` | Công văn số 1500/TC/ĐT Công văn về việc triển khai kế hoạch và cấp vốn đầu tư xây dựng cơ bản kế hoạch năm 2004 | Bộ Tài chính | 2004-02-17 | `110540` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 60 | `1515-TC/TCT` | Công văn số 1515-TC/TCT Công văn về việc xử lý thuế đối với xe ôtô nhập khẩu chuyển đổi công năng | Bộ Tài chính | 2001-02-26 | `109094` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 61 | `15242/TC/TCT` | Công văn số 15242/TC/TCT Công văn về việc hướng dẫn xử phạt vi phạm hành chính về thuế | Bộ Tài chính | 2004-12-24 | `110624` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 62 | `15350/BTC-CST` | Công văn số 15350/BTC-CST Công văn về việc hướng dẫn phân loại một số mặt hàng nhập khẩu trong danh mục biểu thuế nhập khẩu ban hành kèm theo Quyết định 39/2006/QĐ-BTC | Bộ Tài chính | 2006-12-06 | `107419` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 63 | `1546-TC/TCT` | Công văn số 1546-TC/TCT Công văn về việc khai thu tiền thuê đất của các tổ chức trong nước | Bộ Tài chính | 1996-05-12 | `107761` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 64 | `1570-ÐTPT/CP` | Công văn số 1570-ÐTPT/CP Công văn về việc đẩy mạnh tiến độ cấp phát vốn đầu tư những tháng cuối năm 1997 | Bộ Tài chính | 1997-10-07 | `108706` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 65 | `1681/TCT/TCDN` | Công văn số 1681/TCT/TCDN Công văn về việc thu sử dụng vốn ở doanh nghiệp nhà nước thực hiện cổ phần hoá | Bộ Tài chính | 2002-02-26 | `109328` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 66 | `2007-TC/TCT` | Công văn số 2007-TC/TCT Công văn về chế độ thuế đối với hoạt động sản xuất dịch vụ của các trường học | Bộ Tài chính | 1990-12-25 | `107946` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 67 | `2037-TC/TCT` | Công văn số 2037-TC/TCT Công văn về việc tiền thuê đất của các doanh nghiệp có vốn đầu tư nước ngoài | Bộ Tài chính | 1998-06-04 | `108193` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 68 | `244-TC/TCT` | Công văn số 244-TC/TCT Công văn về việc nộp thuế doanh thu và thuế lợi tức đối với ngành ngân hàng | Bộ Tài chính | 1991-02-27 | `109785` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 69 | `2454-TC/CÐKT` | Công văn số 2454-TC/CÐKT Công văn về việc tổng kết đánh giá hệ thống chế độ kế toán doanh nghiệp sau hơn 1 năm triển khai thực hiện | Bộ Tài chính | 1997-07-21 | `109957` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 70 | `253-TC/TCT` | Công văn số 253-TC/TCT Công văn về việc thủ tục kê khai nộp thuế đối với các xí nghiệp quốc doanh | Bộ Tài chính | 1991-02-28 | `110211` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 71 | `274-TC/TCT` | Công văn số 274-TC/TCT Công văn hướng dẫn thu thuế tiêu thụ đặc biệt đối với rượu | Bộ Tài chính | 1991-03-04 | `108602` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 72 | `2749/TC/TCT` | Công văn số 2749/TC/TCT Công văn về việc xử lý thuế nhập khẩu nguyên liệu, vật tư, linh kiện cho sản xuất lắp ráp | Bộ Tài chính | 2002-03-21 | `109449` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 73 | `2852/TC/TCT` | Công văn số 2852/TC/TCT Công văn về việc chống thất thu thuế đối với hoạt động kinh doanh xe ôtô, xe hai bánh gắn máy | Bộ Tài chính | 2002-03-25 | `109462` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 74 | `2865/TC/TCT` | Công văn số 2865/TC/TCT Công văn về việc quyết toán thuế theo tỷ lệ nội địa hoá các sản phẩm, phụ tùng ngành cơ khí-điện-điện tử | Bộ Tài chính | 2003-03-27 | `109674` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 75 | `2868/TC/TCT` | Công văn số 2868/TC/TCT Công văn về việc thuế tiêu thụ đặc biệt đối với điều hoà nhiệt độ để lắp ráp xe ôtô chở khách | Bộ Tài chính | 2003-03-27 | `110031` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 76 | `2925/TC/TCT` | Công văn số 2925/TC/TCT Công văn về thuế đối với hoạt động báo chí | Bộ Tài chính | 2005-03-14 | `110667` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 77 | `3052/TC/TCT` | Công văn số 3052/TC/TCT Công văn về việc thuế tiêu thụ đặc biệt xe ôtô chở khách | Bộ Tài chính | 2002-03-28 | `109185` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 78 | `3090/TC/TCT` | Công văn số 3090/TC/TCT Công văn về việc đăng ký sử dụng hoá đơn tự in | Bộ Tài chính | 2002-03-31 | `109598` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 79 | `3114-TC/ÐT` | Công văn số 3114-TC/ÐT Công văn về việc cấp vốn đầu tư XDCB bổ sung kế hoạch năm 2000 | Bộ Tài chính | 2000-07-31 | `109977` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 80 | `326-TC/TCT` | Công văn số 326-TC/TCT Công văn về việc cấp vốn đầu tư XDCB kế hoạch năm 2000 | Bộ Tài chính | 2000-01-25 | `109827` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 81 | `3260-TC/TCT` | Công văn số 3260-TC/TCT Công văn về thuế thu nhập đối với hoạt động kiều hối | Bộ Tài chính | 1996-09-18 | `109569` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 82 | `338` | Công văn số 338 Công văn về việc bổ sung vốn lưu động và tạm ứng vốn đầu tư | Bộ Tài chính | 1997-09-14 | `110067` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 83 | `360-TC/TCT` | Công văn số 360-TC/TCT Công văn về việc sử dụng hoá đơn | Bộ Tài chính | 1991-03-24 | `107460` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 84 | `3655-TC/TCT` | Công văn số 3655-TC/TCT Công văn về việc xử lý thuế tiêu thụ đặc biệt đối với hàng nhập khẩu | Bộ Tài chính | 1996-10-15 | `107422` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 85 | `3663/TC/TCT` | Công văn số 3663/TC/TCT Công văn về việc phân loại mặt hàng ôtô chuyên dùng theo Biểu thuế nhập khẩu | Bộ Tài chính | 2002-04-15 | `109678` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 86 | `3805-TC/TCT` | Công văn số 3805-TC/TCT Công văn về việc kiểm tra thu học phí đào tạo Luật giao thông và lệ phí thi, cấp bằng lái xe cơ giới đường bộ | Bộ Tài chính | 1996-10-24 | `107643` | Giao thông | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 87 | `39-TC/TCT` | Công văn số 39-TC/TCT Công văn về việc đăng ký về thuế | Bộ Tài chính | 1991-01-07 | `108457` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 88 | `3945/TC/TCT` | Công văn số 3945/TC/TCT Công văn về việc thu thuế theo tỷ lệ nội địa hoá sản xuất, lắp ráp xe gắn máy | Bộ Tài chính | 2001-04-26 | `109005` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 89 | `4066/TC/TCT` | Công văn số 4066/TC/TCT Công văn về việc chính sách ưu đãi thuế đối với ngư dân khai thác hải sản | Bộ Tài chính | 2002-04-24 | `109735` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 90 | `4082-TC/TCT` | Công văn số 4082-TC/TCT Công văn về việc "Thuế đối với nhà thầu nước ngoài" | Bộ Tài chính | 1997-11-14 | `107692` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 91 | `4102-TC/TCT` | Công văn số 4102-TC/TCT Công văn về việc ghi thu, ghi chi thuế nhập khẩu, thuế TTÐB hàng hoá nhập khẩu cho dự án | Bộ Tài chính | 1999-08-18 | `107752` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 92 | `4125/BTC-TCT` | Công văn số 4125/BTC-TCT V/v thu thuế thu nhập đối với hoạt động chuyển quyền thuê đất trong KCN, KCX. | Bộ Tài chính | 2009-03-23 | `107886` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 93 | `4126/TC/TCDN` | Công văn số 4126/TC/TCDN Công văn về việc hướng dẫn bổ sung một số vấn đề về tài chính khi thực hiện cổ phần hoá | Bộ Tài chính | 2005-04-08 | `110723` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 94 | `4129/TC/TCT` | Công văn số 4129/TC/TCT Công văn về việc điều chỉnh hạng đất tính thuế sử dụng đất nông nghiệp | Bộ Tài chính | 2002-04-28 | `109722` | Đất đai, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 95 | `4200-TC/ÐTPT` | Công văn số 4200-TC/ÐTPT Công văn về việc cấp phát, thanh toán vốn đầu tư xây dựng cơ bản thuộc kế hoạch năm 1997 | Bộ Tài chính | 1997-11-24 | `110188` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 96 | `4321/TC/TCT` | Công văn số 4321/TC/TCT Công văn về việc chính sách thuế đối với tổ chức cá nhân nước ngoài dầu tư chứng khoán tại Việt Nam | Bộ Tài chính | 2002-05-06 | `109737` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 97 | `439/TC/ÐTPT` | Công văn số 439/TC/ÐTPT Công văn về việc cấp phát vốn đầu tư xây dựng cơ bản năm 1998. | Bộ Tài chính | 1998-02-20 | `107553` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 98 | `4390-TC/TCT` | Công văn số 4390-TC/TCT Công văn về việc hướng dẫn nộp thuế nhập khẩu | Bộ Tài chính | 1999-08-31 | `108604` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 99 | `466-TC/TCT` | Công văn số 466-TC/TCT Công văn về việc thuế thu nhập quà biếu, quà tặng bằng tiền từ nước ngoài chuyển về | Bộ Tài chính | 2000-02-02 | `109358` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 100 | `48-TC/CTN` | Công văn số 48-TC/CTN Công văn về việc quản lý và sử dụng chống tự thu nộp phí giao thông | Bộ Tài chính | 1990-01-30 | `107370` | Giao thông | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 101 | `4904-TC/TCT` | Công văn số 4904-TC/TCT Công văn hướng dẫn một số điểm về hoàn thuế GTGT | Bộ Tài chính | 1999-09-27 | `109564` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 102 | `4938/TC/TCT` | Công văn số 4938/TC/TCT Công văn về việc thuế nhập khẩu bộ linh kiện để sản xuất, lắp ráp ô tô | Bộ Tài chính | 2002-05-21 | `109948` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 103 | `5249/TC-CST` | Công văn số 5249/TC-CST Công văn về việc khấu trừ, hoàn thuế giá trị gia tăng đã nộp thừa, nộp nhầm ở khâu nhập khẩu | Bộ Tài chính | 2005-04-29 | `110739` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 104 | `525-TC/ÐT` | Công văn số 525-TC/ÐT Công văn về việc cấp vốn đầu tư XDCB kế hoạch năm 2001 | Bộ Tài chính | 2001-01-16 | `108483` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 105 | `5524/TC-TCHQ` | Công văn số 5524/TC-TCHQ Thủ tục, hồ sơ xử lý hàng nhập khẩu không thuộc đối tượng chịu thuế GTGT | Bộ Tài chính | 2004-05-24 | `110615` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 106 | `5524/TC-TCHQ` | Công văn số 5524/TC-TCHQ Công văn về việc thủ tục hồ sơ xử lý hàng nhập khẩu không thuộc đối tượng chịu thuế giá trị gia tăng | Bộ Tài chính | 2004-05-04 | `110637` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 107 | `575-TC/TCT` | Công văn số 575-TC/TCT Công văn về việc thu thuế doanh thu đối với hoạt động thi công xây lắp | Bộ Tài chính | 1991-04-22 | `109714` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 108 | `58/TC/TCT` | Công văn số 58/TC/TCT Công văn về việc thuế giá trị gia tăng máy vi tính và cụm linh kiện máy vi tính | Bộ Tài chính | 2003-06-04 | `110468` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 109 | `5933/TC/TCHQ` | Công văn số 5933/TC/TCHQ Công văn về việc miễn thuế nhập khẩu, không thu thuế giá trị gia tăng đối với vật tư, thiết bị nhỏ lẻ thuộc tập hợp dây chuyền máy móc, thiết bị đồng bộ nhập khẩu tạo tài sản cố định của dự án đầu tư | Bộ Tài chính | 2004-06-01 | `110638` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 110 | `594/TC-TCNH` | Công văn số 594/TC-TCNH Về việc thu thuế TNDN đối với đại lý bán vé xổ số | Bộ Tài chính | 2005-01-17 | `110652` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 111 | `6002/TC/TCDN` | Công văn số 6002/TC/TCDN Công văn về việc quyết toán thuế đối với doanh nghiệp thực hiện cổ phần hoá, đa dạng hoá sở hữu | Bộ Tài chính | 2003-06-10 | `110119` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 112 | `6078/TC/TCT` | Công văn số 6078/TC/TCT Công văn về việc giải quyết vướng mắc về thuế giá trị gia tăng | Bộ Tài chính | 2003-06-12 | `110118` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 113 | `6083/TC/TCT` | Công văn số 6083/TC/TCT Công văn về việc báo cáo hồ sơ để xem xét xử lý xoá nợ thuế phải truy thu do nguyên nhân khách quan | Bộ Tài chính | 2002-06-18 | `110041` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 114 | `675/TC/ÐT` | Công văn số 675/TC/ÐT Công văn về việc cấp vốn đầu tư xây dựng cơ bản kế hoạch năm 2002 | Bộ Tài chính | 2002-01-20 | `108941` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 115 | `687-TCT/NV2` | Công văn số 687-TCT/NV2 Công văn về việc quyết toán thuế năm 2000 | Bộ Tài chính | 2001-03-05 | `109477` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 116 | `6873/TC/TCT` | Công văn số 6873/TC/TCT về việc hướng dẫn giải quyết các hồ sơ tồn đọng về xin miễn giảm thuế cước theo Hiệp định tránh đánh thuế hai lần | Bộ Tài chính | 2004-06-22 | `110508` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 117 | `6905 /TC-TCHQ` | Công văn số 6905 /TC-TCHQ V/v: Thuế đối với xe ô tô ngoại giao chuyển nhượng | Bộ Tài chính | 2005-06-08 | `110712` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 118 | `6905/TC-TCHQ` | Công văn số 6905/TC-TCHQ Công văn về việc thuế đối với xe ô tô ngoại giao chuyển nhượng | Bộ Tài chính | 2005-06-08 | `110673` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 119 | `7071/TC/TCT` | Công văn số 7071/TC/TCT Công văn về việc Ưu đãi đầu tư tại khu thương mại Lao Bảo | Bộ Tài chính | 2002-06-25 | `109516` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 120 | `713/TC/TCT` | Công văn số 713/TC/TCT Công văn về việc áp dụng Hiệp định tránh đánh thuế hai lần trong hoạt động vận tải quốc tế | Bộ Tài chính | 2002-01-21 | `108942` | Giao thông, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 121 | `732-TC/TCT` | Công văn số 732-TC/TCT Công văn về việc hoàn thuế nhập vật liệu, nhập khẩu để sản xuất hàng xuất khẩu, hàng tái nhập, tái xuất, tái nhập | Bộ Tài chính | 1994-03-31 | `108297` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 122 | `7333/TC/TCT` | Công văn số 7333/TC/TCT Công văn về việc thuế thu nhập doanh nghiệp và thuế thu nhập cá nhân đối với dự án ODA không hoàn lại | Bộ Tài chính | 2004-07-02 | `110527` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 123 | `736-TC/CÐTC` | Công văn số 736-TC/CÐTC Công văn về việc xử lý thuế nhà đất đối với nhà ở thuộc sở hữu Nhà nước cho thuê | Bộ Tài chính | 1993-04-28 | `110236` | Đất đai, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 124 | `7430/TC-TCT` | Công văn số 7430/TC-TCT Công văn về việc thuế nhập khẩu, giá trị gia tăng mặt hàng máy may, mô tơ máy may | Bộ Tài chính | 2001-08-05 | `109387` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 125 | `7483/TC/CST` | Công văn số 7483/TC/CST Công văn về việc truy thu thuế nhập khẩu | Bộ Tài chính | 2004-07-07 | `110529` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 126 | `75-TC/TCT` | Công văn số 75-TC/TCT Công văn về việc phân loại, xử lý nợ thuế nông nghiệp từ năm 1993 trở về trước | Bộ Tài chính | 1997-01-07 | `109351` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 127 | `757/TC/TCT` | Công văn số 757/TC/TCT Công văn về việc thuế giá trị gia tăng đối với hàng bán cho doanh nghiệp chế xuất | Bộ Tài chính | 2002-01-22 | `109459` | Doanh nghiệp–đầu tư, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 128 | `7601/TC/TCT` | Công văn số 7601/TC/TCT Công văn về việc thuế xuất khẩu mặt hàng quặng kẽm đã được làm giàu | Bộ Tài chính | 2002-07-10 | `109580` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 129 | `766-TC/TCT` | Công văn số 766-TC/TCT Công văn hướng dẫn thu thuế tài nguyên nước sản xuất thuỷ điện | Bộ Tài chính | 1991-06-10 | `107936` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 130 | `7711/TC/TCT` | Công văn số 7711/TC/TCT Công văn về việc tăng cường quản lý thuế và quản lý tài chính đối với dự án sử dụng vốn ODA | Bộ Tài chính | 2004-07-13 | `110535` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 131 | `7760/TC-QLCS` | Công văn số 7760/TC-QLCS Công văn về việc thực hiện Luật Đất đai năm 2003 | Bộ Tài chính | 2004-07-14 | `110534` | Đất đai | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 132 | `7802/TC/TCT` | Công văn số 7802/TC/TCT Công văn về việc thực hiện thuế giá trị gia tăng đối với hàng tồn kho của đại lý; cho thuê cơ sở hạ tầng | Bộ Tài chính | 2004-07-14 | `110530` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 133 | `789-TC/TCT` | Công văn số 789-TC/TCT Công văn về việc tính chi phí hợp lý, hợp lệ để tìm lợi tức chịu thuế | Bộ Tài chính | 1991-06-13 | `108428` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 134 | `794/TC/TCT` | Công văn số 794/TC/TCT Công văn về việc thuế đối với đại lý bưu điện | Bộ Tài chính | 2003-01-21 | `109945` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 135 | `833-TC/TCT` | Công văn số 833-TC/TCT Công văn về việc thuế nhập khẩu xe cứu thương phục vụ cho y tế và xe cứu thương cải tạo thành xe phục vụ cho mục đích khác | Bộ Tài chính | 1995-04-11 | `109621` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 136 | `836-TC/TCT` | Công văn số 836-TC/TCT Công văn về các biện pháp tăng cường quản lý thu thuế đôi với kinh tế | Bộ Tài chính | 1991-06-24 | `110280` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 137 | `8545/TC/TCT` | Công văn số 8545/TC/TCT Công văn về việc thuế khấu trừ tại nguồn đối với lãi tiền gửi | Bộ Tài chính | 2001-09-09 | `109460` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 138 | `8570/TC/TCT` | Công văn số 8570/TC/TCT Công văn về việc thuế suất thuế nhập khẩu đá trường thạch feldspar | Bộ Tài chính | 2001-09-10 | `109015` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 139 | `861-TC/CTN` | Công văn số 861-TC/CTN Công văn về việc hướng dẫn thu nộp phí giao thông đường bộ và đường sông | Bộ Tài chính | 1987-12-03 | `107671` | Giao thông | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 140 | `874-TC/TCT` | Công văn số 874-TC/TCT Công văn hướng dẫn nộp thuế doanh thu đối với ngành hàng không Việt Nam | Bộ Tài chính | 1991-06-30 | `109695` | Giao thông, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 141 | `8800/TC/TCT` | Công văn số 8800/TC/TCT Công văn về việc miễn thuế hàng quà tặng | Bộ Tài chính | 2003-08-22 | `110421` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 142 | `8842/BTC-TCT` | Công văn số 8842/BTC-TCT Công văn về việc thời gian bắt đầu ưu đãi miễn, giảm thuế | Bộ Tài chính | 2005-07-13 | `110698` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 143 | `8952/TC/TCT` | Công văn số 8952/TC/TCT Công văn về việc miễn nộp tiền sử dụng đất đối với xây dựng nhà chung cư cao tầng | Bộ Tài chính | 2002-08-14 | `109804` | Đất đai | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 144 | `8953/TC/TCT` | Công văn số 8953/TC/TCT Công văn về việc vướng mắc về thu thuế đối với việc xử lý tài sản đảm bảo tiền vay | Bộ Tài chính | 2002-08-14 | `109803` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 145 | `9031/TC-QLCS` | Công văn số 9031/TC-QLCS Công văn về việc hướng dẫn việc quản lý phát hành hoá đơn bán tài sản thanh lý | Bộ Tài chính | 2001-09-23 | `108948` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 146 | `9124TC/TCT` | Công văn số 9124TC/TCT Công văn về thu tiền sử dụng đất trong thời gian chưa có Nghị định về thu tiền sử dụng đất theo Luật Đất đai năm 2003 | Bộ Tài chính | 2004-08-17 | `110596` | Đất đai | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 147 | `9142/TC/TCT` | Công văn số 9142/TC/TCT Công văn về việc chính sách thuế đối với hàng hoá cung cấp cho "Dự án bữa trưa học đường" | Bộ Tài chính | 2003-09-03 | `110429` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 148 | `9151/TC/TCT` | Công văn số 9151/TC/TCT Công văn về việc Ưu đãi đầu tư | Bộ Tài chính | 2002-08-20 | `110035` | Doanh nghiệp–đầu tư | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 149 | `9273/TC/TCT` | Công văn số 9273/TC/TCT Công văn về việc tạm thời chưa thu thuế giá trị gia tăng đối với hoạt động rà phá bom mìn | Bộ Tài chính | 2001-09-30 | `108905` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 150 | `9339/BTC-CST` | Công văn số 9339/BTC-CST Công văn về việc miễn thuế sử dụng đất nông nghiệp | Bộ Tài chính | 2005-07-25 | `110728` | Đất đai, Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 151 | `9342/TC/TCT` | Công văn số 9342/TC/TCT Công văn về việc thuế nhập khẩu mặt hàng hương liệu và mặt hàng phụ gia dùng trong công nghiệp chế biến thực phẩm | Bộ Tài chính | 2001-10-01 | `108900` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |
| 152 | `9933/TC/TCT` | Công văn số 9933/TC/TCT Công văn về việc xử lý thuế giá trị gia tăng hàng hoá xuất nhập khẩu | Bộ Tài chính | 2001-10-18 | `109172` | Thuế | Có tree/provision artifact nhưng body hiển thị rỗng | Chưa tìm |

---

## 4. Metadata cần ghi khi tìm được văn bản

Không dán text tìm được vào `data/raw/{id}.json`. Nên lưu một artifact riêng,
ví dụ `data/manual_text/{id}.json`, với cấu trúc tối thiểu:

```json
{
  "schema_version": 1,
  "document_id": "187020",
  "document_number": "158/2025/TT-BTC",
  "title": "...",
  "source_name": "thuvienphapluat.vn",
  "source_url": "...",
  "retrieved_at": "2026-09-14",
  "content_sha256": "...",
  "text": "...",
  "method": "manual_backfill",
  "review_status": "needs_review",
  "reviewer": null,
  "notes": null
}
```

Nếu tải file PDF hoặc DOC, cần giữ cả tên file, checksum và đường dẫn nguồn.

---

## 5. Checklist đối chiếu trước khi đánh dấu đã tìm

- [ ] Số hiệu trùng hoàn toàn.
- [ ] Tiêu đề trùng hoặc giải thích được khác biệt trình bày.
- [ ] Cơ quan ban hành trùng.
- [ ] Ngày ban hành trùng.
- [ ] Không phải dự thảo.
- [ ] Không lấy nhầm văn bản hợp nhất thay cho văn bản gốc.
- [ ] Có đầy đủ nội dung chính, Điều/Khoản/Điểm cần thiết.
- [ ] Đã lưu URL nguồn và ngày truy cập.
- [ ] Đã tính checksum cho nội dung/file tải về.
- [ ] Đã căn chỉnh thử với provision tree.
- [ ] Có người thứ hai kiểm tra trước khi chuyển sang `verified`.

---

## 6. Quy tắc nhập vào dataset

- Dữ liệu mới bắt đầu ở trạng thái `needs_review`.
- Text lấy trực tiếp từ trang nguồn ghi method `manual_backfill`.
- Text trích từ PDF ghi method `pdf_text`.
- Text qua OCR ghi method `ocr` và không được tự động nâng lên `verified`.
- Không sửa chính tả, dấu, số hiệu hoặc nội dung bằng LLM.
- Exact source text phải được giữ nguyên; bản chuẩn hóa phục vụ tìm kiếm nếu có
  phải lưu ở trường dẫn xuất khác.
- Chỉ artifact `verified` mới được dùng trong strict dataset và benchmark
  chính.

