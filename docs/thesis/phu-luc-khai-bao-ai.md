# Phụ lục. Khai báo sử dụng AI

**Câu hỏi của phụ lục:** AI đã tham gia vào những phần nào của công trình, ai đã kiểm các phần đó và bằng chứng nào cho thấy việc kiểm đã thực sự diễn ra?

## A.1. Phạm vi khai báo

Công trình sử dụng AI trong lập trình, chuẩn bị dữ liệu, hỗ trợ kiểm nhãn, viết tài liệu và sinh câu trả lời thực nghiệm. Các vai trò này phải được khai riêng. Việc một model là đối tượng đánh giá không biến các nội dung do model khác hỗ trợ tạo thành dữ liệu hoàn toàn do người xây dựng. Ngược lại, việc có người duyệt một artifact cũng không đồng nghĩa mọi nội dung trong artifact đã được người đó kiểm độc lập với nguồn gốc.
<!-- nguồn: MASTER_RESEARCH_GUIDE.md @51f36c7 -->
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md @51f36c7 -->

Phụ lục chỉ xác nhận những hoạt động có hồ sơ trong kho. A/B là hai tác giả Cao Minh Trí (CMT) và Nguyễn Minh Trí (NMT), đồng thời tham gia dựng hệ, gold mù và E7; không phải hai chuyên gia pháp lý độc lập bên ngoài. Không công bố danh tính luật sư vượt quá vai trò mà hồ sơ cho phép. Các khẳng định chưa có biên bản kiểm được ghi là đang chờ, không được chuyển thành “đã xác nhận” khi biên tập.
<!-- nguồn: docs/plans/active/master-plan.md -->
<!-- nguồn: docs/reports/D5_bien_ban.md -->

## A.2. Bảng vai trò, kiểm tra và giới hạn

| Hạng mục | AI đã làm gì theo hồ sơ | Người kiểm và cách kiểm được ghi nhận | Giới hạn cần công bố |
|---|---|---|---|
| Mã nguồn và script | Claude/Codex tham gia cài đặt, sửa lỗi, tạo test và báo cáo | Kế hoạch có các checkpoint kiểm pytest, diff và các quyết định CMT/NMT | Test chứng minh hành vi được kiểm; không chứng minh toàn mã đúng hoặc mọi quy tắc pháp lý đã được chuyên gia duyệt |
| Câu hỏi ViLexTime v1.0 | Model thuộc họ Claude/DeepSeek viết và viết lại câu hỏi; có phần người sửa | Metadata xuất xứ, bộ kiểm tự động, nhãn A/B và hòa giải ở phần được ghi | Không mô tả AI chỉ sửa văn phong; kiểm theo mẫu không thành kiểm toàn bộ |
| Đáp án ngắn v1.0 | Claude chọn các span từ lời văn gold hoặc câu dẫn | Kiểm span bằng code, kết hợp quy trình nhãn của dòng | Hợp lệ về span không chứng minh đủ và đúng nghĩa pháp lý |
| Nhãn và đề xuất loại v1.0 | Model gán trước hoặc đề xuất; Codex cung cấp nhãn agent ở phạm vi được phép | Hiệu chuẩn với nhãn người, mẫu luật sư kiểm, quy tắc ưu tiên trong `final_labels` | Cổng đồng thuận toàn tập không đạt; nhãn agent không được gọi là nhãn người |
| Hòa giải D4 | AI soạn bản nháp và đối chiếu kho gốc theo biên bản | A xác nhận bản được ghi trong biên bản | Chưa phải lượt hòa giải độc lập hoàn toàn do người; một số nháp tự ghi chưa đối chiếu nguồn |
| Silver T2–T3 và tiếp xúc trước của A | Phiếu A chứa đáp án và chuỗi phiên bản đồ thị; AI không chỉ hỗ trợ diễn đạt | Đo lại từ phiếu có verdict và silver: A đã gán 131/168 lineage, 283 dòng, 280 `dat` trong vòng 25/10 | A đã thấy đáp án đồ thị ở phần này; nhãn gán lại không được khai là một lượt mù mới; gold1 chia theo người, còn trống |
| Test 2 — nhãn LLM | Hai LLM gán độc lập, model hòa giải và agent hỗ trợ các ca phân vân | Chưa có người hoặc luật sư xác nhận nhãn theo amendment | Luôn gọi là nhãn LLM; không coi là gold độc lập của người |
| Generator thực nghiệm | Qwen sinh câu trả lời từ prompt đã khóa | Cổng định dạng, kiểm hash, parser và scorer; hồ sơ có CMT đọc mẫu dev | Chỉ một generator, chưa có kiểm độ bền khác họ; điểm scorer không thay thế đánh giá người |
| E7 lượt máy | Script phân loại lỗi theo quy tắc ưu tiên, tạo thống kê và phiếu | Assert tổng, test hành vi và đối chiếu với score đã lưu | Chưa có người mã hóa; tầng máy là phân tích thăm dò |
| Tài liệu và bản nháp khóa luận | AI hỗ trợ tổng hợp code, ADR, số đo và soạn văn bản | Bản nháp hiện chờ tác giả và người hướng dẫn rà nội dung, số liệu, cách diễn giải | Không khai rằng đã được GVHD hoặc UIT phê duyệt |

<!-- nguồn: data/review/kiem_A.tsv; data/vilextime_dataset/vilextime_silver.jsonl; data/review/the4/gold1/gold_sample.tsv; data/review/the4/gold1/gold_A.tsv; data/review/the4/gold1/gold_B.tsv; yêu cầu C9b của tác giả -->
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/reports/D5_bien_ban.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md @51f36c7 -->
<!-- nguồn: scripts/pipeline/export_release.py -->
<!-- nguồn: scripts/review/e7_error_analysis.py -->

## A.3. Những giới hạn kiểm tra không được lược bỏ

Metadata v1.0 của phần test ranh giới ghi 88 dòng nhãn A+B, 33 dòng luật sư và 90 dòng nhãn agent. Trong phần luật sư có các phiếu hỗ trợ bởi Claude. Đây là nguồn gốc nhãn, không phải tỷ lệ độ đúng của từng loại người hoặc model. Việc mang nhãn theo lineage sang mốc giữa khoảng không tạo thêm một lượt người kiểm độc lập.
<!-- nguồn: data/vilextime_dataset/vilextime_meta.jsonl -->

Manifest final ghi AC1 giữa người gán là 0,377 trên 246 dòng, κ 0,235. Hiệu chuẩn agent được datasheet ghi AC1 0,721 trên 178 dòng và không đạt cổng toàn tập. Các giá trị này phải được giữ khi công bố vai trò AI; không chỉ nêu rằng “nhãn đã được kiểm”. Bộ gold độc lập vẫn chưa hoàn tất.
<!-- nguồn: data/vilextime_dataset/manifest.json -->
<!-- nguồn: docs/vilextime-datasheet.md -->

Test 2 — nhãn LLM — có một lần chấm sai được khai báo ở amendment 04/11. Việc sửa đáp án ngắn và chấm lại đầu ra có sẵn là một sửa lỗi sau quan sát kết quả, không phải khai báo trước. Accuracy hợp lệ được lưu riêng ở `runs/E3_test2/rescore/`. Sự minh bạch về sai sót là một phần hồ sơ tái lập, không phải bằng chứng rằng các lỗi chưa biết đã được loại hết.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Các phiếu E7 người gán không chứa cột hệ hoặc tầng máy. File máy giữ hệ và tầng, liên kết qua `stt`; thứ tự mẫu giữ nguyên khi bỏ cột hệ. Biện pháp này giảm lộ trực tiếp danh tính hệ, nhưng không bảo đảm người gán không thể đoán hệ từ phong cách câu trả lời hoặc loại bằng chứng. Chưa có kết quả kiểm độ mù hoặc độ đồng thuận E7 của người.
<!-- nguồn: scripts/review/e7_error_analysis.py -->
<!-- nguồn: tests/test_e7_error_analysis.py -->

### Khai báo bổ sung về đợt gán và hòa giải 26/10

Ước tính 5 giây/dòng trong kế hoạch chưa có log thực để xác minh, nên không dùng làm số đo. Phiếu A có 971 dòng điền `phut` trên 1.120 dòng tổng, trung vị 1,0 phút và tổng 990 phút; đây là thời lượng khai trong phiếu, không phải timestamp tự động. AC1 0,377 trên 246 dòng vẫn là phép đo người–người có đồng thuận thấp, không tự xác nhận chất lượng pháp lý.
<!-- nguồn: data/review/kiem_A.tsv; data/vilextime_dataset/manifest.json -->
<!-- nguồn: docs/plans/active/master-plan.md, D1 -->

Trong vòng theo hướng dẫn 3.0 có 101 dòng lệch, 97 dòng là A đạt và B không đạt; luật sư đứng về phía B ở 87/101 dòng, nhưng đã có phiếu Claude hỗ trợ. Metadata test v1.0 ghi 10 dòng luật sư có hỗ trợ Claude. Hai phạm vi này khác nhau: không dùng số ở test thay số của toàn vòng hòa giải 26/10. Cần gọi ghi chú Claude là **bản nháp hỗ trợ**, không phải nhận định độc lập của người hoặc bằng chứng luật sư đã tự kiểm không có gợi ý.
<!-- nguồn: docs/plans/active/master-plan.md, D1; data/vilextime_dataset/vilextime_meta.jsonl -->

## A.4. Bản nháp hiện tại và trách nhiệm tác giả

Các chương trong thư mục `docs/thesis/` là bản nháp do trợ lý Codex hỗ trợ soạn từ các artifact của dự án, chưa phải bản tác giả đã xác nhận để nộp. Nguồn được đặt cạnh đoạn có số liệu hoặc mô tả cơ chế; các khoảng trống được đánh dấu để tác giả kiểm tiếp. Đây là mô tả về lần soạn hiện tại, không phải chứng nhận độc lập về chất lượng bản thảo.
<!-- nguồn: docs/thesis/chuong-3-kho-van-ban-va-do-thi.md -->
<!-- nguồn: docs/thesis/chuong-4-vilextime.md -->
<!-- nguồn: docs/thesis/chuong-5-phuong-phap.md -->
<!-- nguồn: docs/thesis/chuong-6-thuc-nghiem.md -->

Trước khi nhận bản nháp làm nội dung của khóa luận, tác giả cần tự giải thích cơ chế, kiểm được nguồn của từng số và quyết định cách trình bày đóng góp. Hướng A của paper được dùng cho đợt nháp này theo yêu cầu tác giả; các kết luận chính vẫn chờ bộ cuối và phải do tác giả kiểm, quyết định cách trình bày. Việc AI tạo đoạn văn, test hoặc bảng không chuyển trách nhiệm học thuật và trách nhiệm nộp bài sang công cụ.
<!-- nguồn: MASTER_RESEARCH_GUIDE.md @51f36c7 -->
<!-- nguồn: docs/plans/active/master-plan.md -->

Tài liệu tham khảo có trong `references.bib` chưa đồng nghĩa đã được đọc toàn văn. Những khóa được dùng trong bản nháp chỉ trỏ đến bản ghi hiện có; các mục mới kiểm tóm tắt hoặc chưa đọc gốc còn được đánh dấu. Không tạo thêm tên bài, tác giả, DOI hay khóa trích dẫn từ trí nhớ để lấp phần thiếu.
<!-- nguồn: references.bib -->

### Đợt agent ngày 05/11 và bản nháp mốc 08/11

Claude đã soạn bản nháp paper ban đầu; Codex cập nhật các chương mở đầu, dữ liệu, phương pháp, thực nghiệm, kết luận, phụ lục và template paper theo hợp đồng C9 của tác giả. Bản paper được dựng bằng `paper_build.py`, đối chiếu với chương bằng `paper_check.py`. Script kiểm số chỉ kiểm được các bảng và chuỗi nó được thiết kế để kiểm, không chứng nhận toàn bộ lập luận hoặc nội dung pháp lý.
<!-- nguồn: scripts/paper/paper_template.md; scripts/paper/paper_build.py; scripts/paper/paper_check.py -->

Ở đợt này, agent tổng hợp và biên tập từ file cục bộ; không gọi mạng, không gửi bản thảo cho LLM ngoài, không tạo nhãn người hoặc điền kết quả còn thiếu. Không có lượt kiểm độc lập mới của Claude trong chính phiên soạn này. Quy trình dự kiến “Codex làm, Claude kiểm” trong kế hoạch chưa được khai thành việc đã xảy ra. Hai sinh viên vẫn phải đọc, sửa và kiểm từng kết luận trước khi gửi GVHD.
<!-- nguồn: docs/plans/active/master-plan.md; yêu cầu C9 của tác giả ngày 05/11/2026 -->

Theo quy trình bộ cuối, AI có thể hỗ trợ mã, chuẩn bị phiếu và diễn đạt ứng viên; AI không gợi ý nhãn, nháp ghi chú hay hòa giải cho người gán bộ cuối. Khi mô tả dữ liệu cũ, phải giữ nguyên khai báo rằng các vòng trước đã có các can thiệp đó. [CHỜ G4: hồ sơ kiểm người và khai báo công cụ của các lượt tiếp theo].
<!-- nguồn: docs/plans/active/master-plan.md, mục 9 -->

### Cập nhật C9b

Codex sửa chương tổng quan theo báo cáo đọc nguồn của AI ngày 05/11, cập nhật mức đọc trong bibliography và bảng tham khảo sinh tự động; đo lại tiếp xúc trước của A, rà nguồn số và đối chiếu một mẫu có seed từ file. Script kiểm số của lượt này đặt ngoài repo; bộ kiểm paper được giữ nguyên. Báo cáo đọc cũ là bằng chứng về phạm vi AI đã truy cập, không thay việc hai tác giả tự đọc tài liệu gốc. Lượt C9b không chạy bộ test cuối và chưa có lượt người duyệt hoặc phản biện độc lập mới.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md; scripts/paper/paper_refs.py; scripts/paper/paper_build.py; scripts/paper/paper_check.py; yêu cầu C9b của tác giả -->

Lượt C12 sửa theo phản biện 05/11 chỉ đọc artifact cục bộ, tính thêm bảng TCS/VCR/MRR/EM/F1, precision/recall, đóng góp XN1 và độ nhạy power; dựng lại paper từ template. Không gọi mạng, generator hay giám khảo LLM; không chạy bộ test cuối. Phản biện do AI trong dự án làm, không phải phản biện ngoài. Các góp ý về power và mẫu số thời gian được kiểm lại thay vì chép nguyên con số.
<!-- nguồn: docs/reports/phan-bien-ban-nhap-20261105.md; scripts/paper/paper_values.py; yêu cầu C12 của tác giả -->

### Đối chiếu lại các con số phản biện C12

Không chép số power sau Holm 0,25 ở V2: với cùng hiệu và phương sai theo cụm từ file, xấp xỉ chuẩn cho 150 lineage cho 0,346 ở α = 0,05, và 0,141 ở ngưỡng α/6; kết quả phụ thuộc bậc Holm, không có một số cố định trước khóa họ. L2 nói 971/971 nhưng đó là phần có verdict/thời gian, còn toàn phiếu có 1.120 dòng; giữ 971/1.120 và phân biệt số tự khai với log thực. Các ý cảnh báo của V2/L2 vẫn được tiếp thu, chỉ không nhận các con số chưa đúng phạm vi.
<!-- nguồn: scripts/paper/paper_values.py; runs/E1_test2/test/b7.jsonl; runs/E1_test2/test/b7pp.jsonl; data/vilextime/test2_release_v2.jsonl; data/review/kiem_A.tsv; docs/reports/phan-bien-ban-nhap-20261105.md, V2 và L2 -->

## A.5. Quy định cơ sở đào tạo

Quy định cụ thể của UIT về sử dụng và khai báo AI trong khóa luận **chưa được xác minh**. Hồ sơ hướng dẫn nghiên cứu của dự án cũng ghi tình trạng này là chưa biết. Phụ lục này là bản khai báo theo bằng chứng dự án, không phải kết luận rằng cách dùng AI hiện tại phù hợp quy định của trường. [CẦN: quy định hiện hành của UIT, yêu cầu của khoa và hướng dẫn của GVHD về phạm vi sử dụng, hình thức khai báo AI trước khi nộp].
<!-- nguồn: MASTER_RESEARCH_GUIDE.md @51f36c7 -->

## A.6. Câu trả lời có thể rút ra

AI tham gia đáng kể vào dữ liệu, mã và tài liệu, bên cạnh vai trò generator được đánh giá. Kho có cơ chế lưu xuất xứ, kiểm hành vi và các lượt xác nhận của người ở những phần cụ thể. Tuy nhiên, nhãn LLM, nhãn agent không đạt cổng toàn tập, các hòa giải có AI hỗ trợ và phần người kiểm chưa hoàn tất phải được công bố nguyên trạng. Chỉ những lần kiểm có hồ sơ mới được khai là đã thực hiện.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/reports/D5_bien_ban.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## Việc còn thiếu trước khi nộp

- Tác giả và GVHD rà bản khai báo, xác nhận phần nào đã kiểm và lưu bằng chứng tương ứng.
- Xác minh quy định UIT; điều chỉnh hình thức phụ lục theo yêu cầu chính thức, không tự suy tính tuân thủ.
- Hoàn thiện lịch sử sử dụng công cụ/model từ receipt có sẵn nếu cần khai chi tiết; không suy model cụ thể chỉ từ tên sản phẩm.
- Kiểm rằng bản nộp cuối vẫn công bố nhãn LLM, sự tham gia của AI trong hòa giải và lần chấm sai đã sửa.
