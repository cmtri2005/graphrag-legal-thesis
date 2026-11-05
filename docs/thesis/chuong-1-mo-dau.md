# Chương 1. Mở đầu

> Bản nháp cho GVHD xem hướng tại mốc Chủ nhật 08/11/2026. Các kết quả hiện có là kết quả vòng thử; bộ test cuối chưa chạy.
<!-- nguồn: docs/plans/active/master-plan.md -->

**Tên đề tài:** TRUY XUẤT TĂNG CƯỜNG DỰA TRÊN ĐỒ THỊ TRI THỨC CÓ NHẬN BIẾT THỜI GIAN CHO HỎI ĐÁP PHÁP LUẬT VIỆT NAM THEO MỐC HIỆU LỰC.

**Sinh viên:** Cao Minh Trí 23521635; Nguyễn Minh Trí 23521643. **GVHD:** ThS. Đỗ Thị Minh Phụng. MSSV của Nguyễn Minh Trí được ghi theo đính chính của tác giả trong yêu cầu soạn nháp; đề cương có lỗi đánh máy ở trường này.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx; yêu cầu C9 của tác giả ngày 05/11/2026 -->

## 1.1. Bối cảnh và động cơ

Một câu hỏi pháp luật cần được đặt trong thời điểm áp dụng. Cùng một nội dung được hỏi, lời văn của điều khoản có thể đã được sửa đổi, bổ sung, thay thế hoặc bãi bỏ giữa các mốc. Do đó, truy xuất được một đoạn đúng chủ đề chưa đủ: hệ thống còn phải xác định đoạn ấy thuộc phiên bản nào và có thể dùng tại thời điểm người hỏi nêu hay không. Đề cương đặt trọng tâm vào lỗi lấy đúng quy phạm nhưng áp dụng sai phiên bản, thay vì chỉ đánh giá mức liên quan của đoạn văn.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->

Hướng tiếp cận của khóa luận là biểu diễn điều khoản cùng lịch sử lời văn và khoảng hiệu lực, rồi dùng các thông tin đó khi tìm căn cứ và kiểm trích dẫn. Biểu diễn đồ thị hỗ trợ mô tả quan hệ cấu trúc và tác động sửa đổi; tuy nhiên, lợi ích của biểu diễn này phải được phân biệt với lợi ích của một bộ lọc ngày đơn giản. Đó là lý do cần các cấu hình đối chứng giữ chung đường truy xuất và sinh câu trả lời.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Bài toán có tiền lệ gần trong Prior, LawInForce-eCFR và NitiBench+ về lọc luật theo mốc, điều kiện cấp sẵn căn cứ và lỗi đọc phiên bản [@prior2026oldfriend] [@yao2026lawinforce] [@akarajaradwong2026nitibenchplus]. Vì vậy, “lọc thời gian có lợi” và “hai nút thắt tìm–đọc” không được coi là phát hiện riêng. Luận điểm của khóa luận được thu hẹp vào phép đo trên pháp luật Việt Nam, nhận diện bãi bỏ và tách ba nấc thông tin trên cùng dữ liệu: ngày văn bản, khoảng hiệu lực phiên bản và lan truyền từ nút cha. Khảo sát đã có log, nhưng còn nguồn bị chặn và bài chỉ đọc một phần; chưa xác lập thứ tự công bố hay phủ định tiền lệ khác.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md; docs/plans/active/master-plan.md, mục 10 -->

## 1.2. Phát biểu bài toán

Theo đề cương, đầu vào là một câu hỏi pháp lý \(x\) bằng tiếng Việt kèm mốc thời gian áp dụng \(t\), tức thời điểm phát sinh hành vi hoặc quan hệ pháp luật cần tra cứu. Đầu ra là câu trả lời \(a\) và tập bằng chứng \(E\) gồm các đơn vị pháp lý ở cấp Điều/Khoản/Điểm có hiệu lực tại \(t\). Với \(U\) là tập đơn vị pháp lý trong kho, ràng buộc đầu ra được viết:

\[
(x,t)\longmapsto(a,E),\qquad E\subseteq U,\quad \forall u\in E:\operatorname{valid}(u,t).
\]
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->

Truy vấn là cặp \((x,t)\). Với những câu hỏi có nội dung thay đổi theo lịch sử pháp luật, đổi mốc phải dẫn đến việc lựa chọn lại câu trả lời và bằng chứng tương ứng. Trong đánh giá, cần phân biệt câu trả lời sai nội dung, dùng sai phiên bản và không đưa ra kết luận. Trường hợp không tìm được căn cứ không tự chứng minh quy định đã hết hiệu lực; đây là điểm đặc biệt quan trọng khi đánh giá nhóm bãi bỏ.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->
<!-- nguồn: scripts/eval/score_vilextime.py -->

## 1.3. Câu hỏi nghiên cứu và giả thuyết

Các câu hỏi và giả thuyết dưới đây được giữ nguyên văn đề cương:

> RQ1. Các mô hình ngôn ngữ lớn và các hệ thống RAG hiện có mắc lỗi áp dụng sai phiên bản quy phạm ở mức độ nào trên pháp luật Việt Nam?

> RQ2. Việc biểu diễn văn bản pháp luật dưới dạng đồ thị theo phiên bản có làm giảm tỷ lệ lỗi này so với RAG phẳng và GraphRAG phi thời gian hay không?

> RQ3. Lợi ích thu được đến từ biểu diễn đồ thị, hay chỉ đơn thuần đến từ việc lọc theo siêu dữ liệu thời gian?

> Giả thuyết nghiên cứu: Việc mô hình hóa chuỗi phiên bản và hiệu lực ở cấp cấu trúc pháp lý sẽ cải thiện khả năng truy xuất đúng phiên bản so với chỉ lọc theo ngày hiệu lực ở cấp văn bản.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->

Để trả lời, khóa luận tách ba mức: mô tả lỗi của các hệ đã chạy; so sánh xác nhận theo kế hoạch phân tích đã khai báo; và phân tích thăm dò về các thành phần hoặc nhóm nhỏ. Các phán quyết trong vòng thử chỉ có hiệu lực trong phạm vi dữ liệu, nhãn và cấu hình tương ứng. [CHỜ G4: kết quả bộ test cuối cho các câu hỏi nghiên cứu và giả thuyết].
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: docs/plans/active/master-plan.md -->

## 1.4. Mục tiêu và đóng góp dự kiến

Đề cương cam kết hai sản phẩm nghiên cứu. Thứ nhất là ViLexTime, bộ dữ liệu hỏi đáp pháp luật tiếng Việt theo mốc thời gian, có bằng chứng cấp Điều/Khoản/Điểm, quy mô dự kiến khoảng 1.100–1.300 câu hỏi. Thứ hai là kiến trúc Temporal-Aware KG-RAG, kết hợp đồ thị có thông tin thời gian, truy xuất có ràng buộc hiệu lực, truy xuất lai ghép, mở rộng đồ thị và kiểm chứng trích dẫn. Quy mô dự kiến là mục tiêu của đề cương, chưa phải số mẫu người kiểm đạt.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->

Ở trạng thái hiện tại, đóng góp có thể trình bày là đường ống dẫn xuất phiên bản có truy nguyên, tài nguyên đánh giá công bố nguồn nhãn, và phép so sánh giúp phân biệt các mức thông tin thời gian. Việc hoàn tất hệ theo đề cương và kiểm định trên bộ cuối còn đang chờ. Đóng góp không được định nghĩa bằng yêu cầu hệ đề xuất phải thắng; một kết quả không đủ bằng chứng vẫn trả lời được giới hạn của cách biểu diễn đã thử nếu phép đo đáng tin cậy.
<!-- nguồn: docs/plans/active/master-plan.md -->

Điều kiện X8 sẽ cấp sẵn căn cứ đúng mốc và căn cứ hiện hành cho các nhóm T1, T2, T3, T6 để đo cái giá của việc đọc sai văn bản, tách khỏi lỗi tìm. Phải làm trên dev trước rồi bộ test cuối; oracle dev hiện có không thay được hai điều kiện đó. [CHỜ COLAB: X8 đúng mốc/hiện hành; chưa có kết quả để kết luận].
<!-- nguồn: docs/plans/active/master-plan.md, X8 và mục 10 -->

## 1.5. Phạm vi và giới hạn

Nguồn thu thập theo đề cương là vbpl.vn; các miền tiêu biểu gồm giao thông đường bộ, thuế–phí–hải quan, doanh nghiệp–đầu tư và đất đai. Các nội dung thực hiện bao gồm khảo sát tài liệu, thu thập và phân tích cấu trúc, dựng đồ thị có phiên bản, xây ViLexTime, phát triển truy xuất và sinh, thực nghiệm và phân tích. ViLexTime theo thiết kế diff-driven đi từ so khớp phiên bản, trích khác biệt, diễn đạt câu hỏi đến kiểm định thủ công; vai trò LLM được đề cương giới hạn ở hỗ trợ diễn đạt câu hỏi.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->

Khóa luận tập trung vào hiệu lực theo thời gian của văn bản quy phạm pháp luật cấp trung ương; chưa xử lý đầy đủ hiệu lực theo không gian, đối tượng áp dụng và xung đột quy phạm. Dữ liệu chỉ là văn bản dạng chữ, chưa hỗ trợ đa phương thức. Hợp nhất tự động có thể sai; hệ thống không huấn luyện lại LLM và không thay thế tư vấn pháp lý chuyên nghiệp. Kho thực tế có thể rộng hơn các miền đánh giá để giữ các quan hệ tác động cần thiết.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->
<!-- nguồn: docs/plans/active/master-plan.md -->

## 1.6. Chỗ lệch so với đề cương

Bảng sau ghi các lệch đã được kế hoạch chính yêu cầu giải trình. Đây là khai báo về cách thực hiện, không sửa nội dung cam kết ban đầu.

| Lệch | Lý do | Xử lý trong khóa luận |
|---|---|---|
| Nhãn LLM ở v1.0 và test 2 | Thiếu giờ người khi chạy theo mốc 31/10 | Báo thành vòng thử; bộ cuối do người gán, phân biệt tầng chất lượng |
| “Chuyển miền” đổi thành phân rã theo miền | Hệ không huấn luyện lại, miền đa nhãn | Thực hiện theo C5; không gọi là phép chuyển miền đã chạy |
| GraphRAG là bản xấp xỉ trong cùng đường ống | Cần so sánh chỉ đổi một yếu tố; dựng GraphRAG đầy đủ trên kho lớn có chi phí cao | Gọi rõ đối chứng mở rộng một bước; nêu giới hạn; LightRAG trên tập con báo riêng khi có |
| T5 thiếu, T4 có thể dưới 150 | Điều kiện pháp lý hẹp | Báo số thật, không nới định nghĩa để đủ quota |
| Kho rộng hơn bốn miền | Cần đóng kín quan hệ sửa đổi | Giải thích trong phần dữ liệu và datasheet |
<!-- nguồn: docs/plans/active/master-plan.md, mục 4 -->

Ngoài các lệch trên, trạng thái chưa hoàn tất cũng phải được công bố: M2 kiểm chứng snapshot chưa đạt; cấu hình `proposed` đã chạy dùng từ vựng; `proposed2` lai ghép mới có số truy xuất trên dev; Verifier chưa cho thấy tác dụng khi bộ lọc đã loại căn cứ không hợp lệ. Chương phương pháp phân biệt kiến trúc cam kết với cấu hình đã đo, còn chương thực nghiệm để trống kết quả bộ cuối.
<!-- nguồn: docs/plans/active/master-plan.md -->
<!-- nguồn: runs/README.md -->

## 1.7. Cấu trúc khóa luận

Chương mở đầu xác định bài toán, mục tiêu và phạm vi. Chương cơ sở lý thuyết tổng hợp các khái niệm và công trình đã đọc. Chương kho văn bản trình bày cấu trúc, sự kiện và chuỗi phiên bản cùng bằng chứng kiểm chứng. Chương ViLexTime mô tả quy trình dữ liệu, nguồn nhãn và thiết kế bộ test cuối. Chương phương pháp trình bày các tầng kiến trúc và đối chứng. Chương thực nghiệm tách hai vòng thử, thử nghiệm dev và phần kết quả cuối còn chờ. Chương kết luận phân biệt điều đã quan sát với điều chưa thể khẳng định; phụ lục khai báo sự tham gia của AI.
<!-- nguồn: docs/thesis/chuong-2-co-so-ly-thuyet.md; docs/thesis/chuong-3-kho-van-ban-va-do-thi.md; docs/thesis/chuong-4-vilextime.md; docs/thesis/chuong-5-phuong-phap.md; docs/thesis/chuong-6-thuc-nghiem.md; docs/thesis/chuong-7-ket-luan.md -->
