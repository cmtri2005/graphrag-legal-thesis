# Chương 7. Kết luận và hướng phát triển

> Kết luận tạm của bản nháp cho mốc 08/11/2026, dựa trên hồ sơ hiện có. Bộ test cuối chưa chạy; các kết luận chính còn chờ G4.
<!-- nguồn: docs/plans/active/master-plan.md -->

## 7.1. Điều đã có thể nói

Khóa luận đã hình thành đường ống đi từ văn bản nguồn và quan hệ sửa đổi đến chuỗi lời văn có phiên bản, khoảng hiệu lực và corpus truy xuất. Biểu diễn tách danh tính điều khoản khỏi phiên bản, cho phép đặt câu hỏi dưới dạng cặp câu hỏi–mốc và truy nguyên căn cứ đã dùng. Các kiểm tra nội bộ và mẫu kiểm lịch sử là bằng chứng về khả năng tái dựng, kiểm tra nhất quán; chúng chưa chứng minh toàn bộ lịch sử pháp luật được dựng đầy đủ hoặc đúng độc lập với nguồn.
<!-- nguồn: docs/thesis/chuong-3-kho-van-ban-va-do-thi.md -->
<!-- nguồn: scripts/pipeline/build_versions.py; src/vilexgraph/build/temporal/effective_intervals.py -->

ViLexTime hiện cung cấp dữ liệu cho hai vòng thử có khai báo và một cơ chế chấm tương phản theo phiên bản. V1.0 có nhãn hỗn hợp người và agent; test 2 có nhãn LLM, chưa có kiểm người trực tiếp cho bộ nhãn đang dùng. Giá trị có thể trình bày là tài nguyên có xuất xứ và hồ sơ sai sót, cùng phép đánh giá tách đúng điều khoản, đúng phiên bản và đúng câu trả lời. Chưa gọi tài nguyên này là chuẩn vàng pháp lý đã được kiểm độc lập đầy đủ.
<!-- nguồn: data/vilextime_dataset/manifest.json; data/vilextime_dataset/vilextime_meta.jsonl -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Ở mức **xác nhận trong từng vòng thử**, XN3 về lọc ngày cấp văn bản được ủng hộ trên cả hai bộ. XN1 về biểu diễn phiên bản có phán quyết ủng hộ trên v1.0 nhưng không đủ bằng chứng trên test 2, nhãn LLM. Các phán quyết đó được giữ đúng theo ADR và cấu hình lịch sử; không chuyển chúng thành kết luận xác nhận trên bộ cuối. Sự khác biệt giữa hai vòng cho thấy cần một phép đo được người kiểm và có gold độc lập trước khi chốt giả thuyết.
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; docs/plans/active/master-plan.md -->

Ở mức **mô tả**, hệ RAG phẳng còn dùng trích dẫn không hợp lệ theo mốc trong cả hai vòng. Baseline LLM không truy xuất gần như không trả lời nên chưa đủ để mô tả mức sai phiên bản của LLM nói chung. Ở mức **thăm dò**, chênh lệch khi thêm mở rộng quan hệ một bước trên toàn tập nhỏ và chưa nhất quán giữa hai vòng. Kết quả chỉ áp dụng cho cách mở rộng đã đo; nó không cho phép kết luận tổng quát rằng đồ thị không giúp. Các hệ lớp phiên bản còn dựa vào đồ thị khi dựng lịch sử và tính khoảng hiệu lực ngoại tuyến.
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->
<!-- nguồn: runs/README.md; src/vilexgraph/framework/graphx.py -->

Phân rã lỗi máy là **thăm dò**: hệ có thể không tìm được căn cứ hoặc đọc sai khi đã được cấp căn cứ. Nhận diện bãi bỏ vẫn yếu. Việc `b7pp` có TVER bằng không chủ yếu phản ánh bộ lọc và gold dùng chung mô hình hiệu lực; tránh trích phiên bản bị loại không đồng nghĩa nhận ra đúng việc quy định đã hết hiệu lực. Vì thế, không dùng riêng TVER để khẳng định thành công của kiến trúc.
<!-- nguồn: docs/reports/e7_phan_ra_loi.md; docs/plans/active/master-plan.md, D2 -->

## 7.2. Điều chưa thể kết luận

Chưa thể trả lời đầy đủ RQ1 ở vế LLM không truy xuất; cần đo trên phần câu có trả lời và các cấu hình LLM đã định trước. Chưa thể xác nhận RQ2 cho kiến trúc lai ghép đúng đề cương: `proposed` đã chạy vòng thử chỉ dùng từ vựng, còn `proposed2` mới có số truy xuất dev và chưa sinh câu trả lời. Với RQ3, chưa thể chốt lợi ích thêm của chuỗi phiên bản hoặc lan truyền hiệu lực trên bộ cuối. Không đủ bằng chứng cũng chưa phải bằng chứng hiệu ứng bằng không.
<!-- nguồn: docs/plans/active/master-plan.md, mục 3 và 6; runs/README.md -->

Chất lượng thước đo là giới hạn cần giải quyết trước. Đồng thuận người gán thấp đi kèm tốc độ gán rất nhanh của A; một phần test v1.0 chỉ có nhãn Codex; lời dặn LLM bản mới không qua hiệu chuẩn. Gold từ cùng đồ thị với hệ còn tạo nguy cơ hệ và đáp án cùng sai. M2 chưa đạt và thử căn VBHN hiện mới là khảo sát kỹ thuật, chưa thay được việc người kiểm nguồn độc lập.
<!-- nguồn: docs/plans/active/master-plan.md, D1–D2 -->
<!-- nguồn: data/review/test2_llm_v2/calib_score.json; docs/reports/thu-tai-vbhn-20261105.md -->

Log khảo sát và báo cáo đọc hiện đã xác nhận các tiền lệ gần về lợi ích lọc theo mốc và hai nút thắt tìm–đọc, gồm Prior, LawInForce-eCFR và NitiBench+ [@prior2026oldfriend] [@yao2026lawinforce] [@akarajaradwong2026nitibenchplus]. Khóa luận chỉ giữ luận điểm hẹp: phép đo pháp luật Việt Nam, nhận diện bãi bỏ và đối chứng cùng dữ liệu giữa ngày văn bản, khoảng phiên bản và lan truyền từ cha. Chưa có bằng chứng cho thứ tự công bố hoặc ưu thế chung; các nguồn bị chặn và phần chưa đọc vẫn có thể đổi cách định vị. [CẦN: đọc đủ các phần và phiên bản còn thiếu đã nêu trong chương tổng quan].
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md; docs/plans/active/master-plan.md, mục 10 -->

## 7.3. Phần kết luận chờ bộ test cuối

Bảng dưới là vị trí kết luận sau khi có bằng chứng G4, không phải danh sách kết quả được dự đoán. Phải điền cả trường hợp không đủ bằng chứng hoặc khác chiều giả thuyết.
<!-- nguồn: docs/plans/active/master-plan.md, mục 6, 7 và 10 -->

| Nội dung | Kết luận chính |
|---|---|
| RQ1, RAG và LLM không truy xuất | [CHỜ G4: mức sai phiên bản, mẫu số và giới hạn độ phủ] |
| RQ2, hệ lai ghép so với các đối chứng | [CHỜ G4: ước lượng, KTC và phán quyết theo amendment] |
| RQ3 và giả thuyết đề cương | [CHỜ G4: nguồn gốc chênh lệch qua thang lọc và phiên bản] |
| Bãi bỏ ở nút cha, tác dụng thành phần | [CHỜ G4: kết quả và phân loại xác nhận/thăm dò/mô tả] |
| Độ bền khi dùng gold mù | [CHỜ G4: mức khớp nguồn độc lập và ảnh hưởng đến kết luận] |
<!-- nguồn: docs/plans/active/master-plan.md -->

## 7.4. Hướng phát triển

Ưu tiên trước mắt là kiểm nhãn theo câu hỏi, bắt buộc dẫn chứng và ghi thời gian, để người gán độc lập với nhãn hoặc gợi ý AI. Dòng lệch do luật sư phân xử không có phiếu AI. Gold mù từ văn bản gốc và VBHN cần giúp phát hiện lỗi của đồ thị, đồng thời tách lỗi trích/căn PDF khỏi lỗi dựng phiên bản. Chất lượng của bước này quyết định mức độ có thể bảo vệ các kết luận sau cùng.
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 và 7 -->

Về hệ thống, cần hoàn thiện truy xuất lai ghép và `rel_up` trên dev, đo khả năng generator hiểu thông báo bãi bỏ, và kiểm Verifier trong điều kiện bộ lọc chưa loại hết trích dẫn sai. Các baseline còn thiếu, kiểm độ bền generator và E7 người kiểm phải được báo theo kế hoạch. X8 phải so căn cứ được cấp sẵn đúng mốc với căn cứ hiện hành ở T1 (đối chứng), T2, T3, T6, trên dev trước rồi bộ cuối; oracle dev chưa thay được phép so này. [CHỜ COLAB: X8 đúng mốc/hiện hành và phân rã lỗi tìm–đọc]. Chỉ sau khi khóa dữ liệu, hệ và phân tích mới chạy bộ test cuối; kết quả vòng thử không được dùng để tiếp tục chọn cấu hình.
<!-- nguồn: docs/plans/active/master-plan.md, mục 6, 7 và 10 -->

Về phạm vi dài hạn, xử lý đầy đủ ngoại lệ theo đối tượng, không gian và xung đột quy phạm cần một thiết kế và bằng chứng riêng. Những nội dung này nằm ngoài giới hạn đề cương hiện tại, không được hứa là kết quả của lần chạy sắp tới. [CẦN: tác giả và GVHD rà cách trình bày đóng góp, phạm vi và các phần chưa hoàn tất trước khi nộp].
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->
