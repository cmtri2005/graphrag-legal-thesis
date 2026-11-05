# Chương 4. Bộ dữ liệu ViLexTime

> v1.0 và test 2 là hai vòng thử có khai báo. Bộ test cuối do người kiểm đang được chuẩn bị, chưa có kết quả.
<!-- nguồn: docs/plans/active/master-plan.md -->

**Câu hỏi của chương:** ViLexTime đo khả năng chọn và sử dụng phiên bản điều khoản như thế nào, và nguồn gốc đáp án, nhãn kiểm tra cùng quy trình chọn mẫu giới hạn độ tin cậy của phép đo ra sao?

## 4.1. Đối tượng và đơn vị đánh giá

ViLexTime đánh giá câu trả lời cho câu hỏi (x) tại một mốc (t) do người hỏi cung cấp. Một dòng là một cặp câu hỏi–mốc, không phải một câu hỏi độc lập. Các dòng cùng `lineage_id` dùng cùng danh tính điều khoản và có thể dùng lại câu hỏi ở nhiều mốc. Vì thế, số dòng thường lớn hơn số câu hỏi khác nhau; không thể thay thế hai đại lượng này khi báo quy mô hoặc độ bất định.
<!-- nguồn: docs/vilextime-dinh-nghia.md -->
<!-- nguồn: scripts/pipeline/enrich_vilextime.py -->

Bộ dữ liệu kiểm tra việc lấy đúng bằng chứng và sử dụng đúng lời văn của phiên bản. Nó không đánh giá đầy đủ việc tư vấn một vụ việc cụ thể, xác định thẩm quyền áp dụng hay giải quyết xung đột giữa mọi văn bản có liên quan. Gold được dựng từ chuỗi phiên bản của kho; “đúng” trong phép chấm trước hết là đúng với gold và các quy tắc đã công bố. Đây là ranh giới cần giữ khi chuyển kết quả benchmark thành nhận định về năng lực pháp lý.
<!-- nguồn: docs/vilextime-dinh-nghia.md -->
<!-- nguồn: scripts/eval/score_vilextime.py -->

## 4.2. Quy trình dựng và chọn câu hỏi

Quy trình bắt đầu từ chuỗi phiên bản và các chuyển tiếp lời văn. Pipeline tạo ứng viên có đích điều khoản, phiên bản, ngày chuyển và câu chứng cứ; model viết câu hỏi dựa trên những phần lời văn cần phân biệt. Các bộ kiểm sau đó loại câu không đủ ngữ cảnh, lộ đáp án, mơ hồ hoặc không chạm nội dung thay đổi. Bước kiểm nhãn có thể loại thêm lineage khi nội dung được hỏi đã chuyển sang văn bản khác, thay đổi chỉ mang tính hình thức hoặc gold không phù hợp với câu hỏi.
<!-- nguồn: scripts/pipeline/build_question_pool.py -->
<!-- nguồn: scripts/pipeline/build_vilextime.py -->
<!-- nguồn: docs/vilextime-dinh-nghia.md -->

Vai trò của AI vượt quá việc diễn đạt câu hỏi. Hồ sơ dữ liệu ghi model tham gia viết câu hỏi, chọn đáp án ngắn, gán nhãn ban đầu, đề xuất loại và hỗ trợ hòa giải. Vì vậy, khóa luận không mô tả ViLexTime là bộ dữ liệu hoàn toàn do người xây dựng, cũng không coi toàn bộ gold là kết quả kiểm định thủ công. Cần tách lời văn gold dẫn xuất từ kho với nhãn đánh giá chất lượng câu hỏi và tính phù hợp của gold.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/reports/D5_bien_ban.md -->

Các nhóm hiện tượng được dùng như sau. Chúng là phân tầng của bộ đánh giá, không phải các miền pháp luật độc lập.

| Nhóm | Hiện tượng được thiết kế để quan sát | Giới hạn khi diễn giải |
|---|---|---|
| T1 | Điều khoản chỉ có một phiên bản trong kho | Không tạo tương phản phiên bản bằng chính lời văn |
| T2 | Cặp lời văn trước và sau thay đổi | Phụ thuộc khả năng xác định cùng một nội dung được hỏi |
| T3 | Chuỗi nhiều phiên bản | Nhiều dòng cùng lineage không độc lập |
| Lát gần giống của T2 | Thay đổi nhỏ giữa các phiên bản | T4 là tên lịch sử, không cộng thêm như nhóm độc lập |
| T5 | Hiện tượng hiệu lực trở về trước | Chỉ chẩn đoán; không nằm trong bảng all |
| T6 | Điều khoản bị bãi bỏ trực tiếp hoặc qua nút cha | Bãi bỏ một vị trí không đủ chứng minh nội dung không còn ở nơi khác |

<!-- nguồn: docs/vilextime-dinh-nghia.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## 4.3. Chọn mốc, split và schema

`ranh_gioi` lấy mốc sát chuyển phiên bản. Bảng chính dùng `giua_khoang` để giảm việc ngày hỏi tự gợi ra văn bản vừa có hiệu lực. Mốc giữa khoảng được lấy bằng seed, ưu tiên cách các đầu khoảng hiệu lực; nếu khoảng quá ngắn thì dùng điểm giữa. `truoc_hieu_luc` giữ đáp án cũ khi văn bản sửa đổi đã ký nhưng quy định mới chưa được áp dụng. Chế độ `sau_het_hieu_luc` từng có trong tài liệu cũ đã bị bỏ khỏi đường enrich hiện tại vì nội dung có thể tiếp tục tồn tại ở văn bản thay thế.
<!-- nguồn: scripts/pipeline/enrich_vilextime.py -->

Việc chia dev/test dựa trên văn bản đích và một hàm băm có seed. Các dòng của cùng văn bản giữ cùng split, tránh việc một câu ở test có phiên bản gần như tương ứng ở dev. Đây là biện pháp chống rò rỉ theo đơn vị văn bản trong thiết kế; nó không loại bỏ mọi dạng gần trùng ngữ nghĩa giữa các văn bản khác nhau. Dev được dùng để lựa chọn cấu hình và kiểm đường ống, không làm bằng chứng kết luận trên test.
<!-- nguồn: scripts/pipeline/enrich_vilextime.py -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Schema công bố tách nội dung đối chiếu `context` khỏi đáp án ngắn `answer`. Ở bản nội bộ, `answer` lại là lời văn gold và `short_answer` là span bắt buộc. Hàm `load_rows` của scorer phục hồi biểu diễn nội bộ khi đọc bản công bố và ghép metadata đi kèm. Sự khác nhau này phải được nêu rõ để tránh đưa nhầm trường vào bộ chấm hoặc mô tả sai loại đầu ra của bộ dữ liệu.
<!-- nguồn: scripts/pipeline/export_release.py -->
<!-- nguồn: scripts/eval/score_vilextime.py -->

| Trường | Vai trò |
|---|---|
| `id`, `lineage_id` | Định danh dòng và cụm phụ thuộc |
| `question`, `as_of` | Đầu vào của hệ trả lời |
| `split`, `group`, `as_of_strategy` | Phân tập và phân tầng đánh giá |
| `version_id` | Phiên bản gold, nếu dòng có đáp án |
| `accepted_evidence` | ID bằng chứng tương đương được chấp nhận |
| `answerable` | Có nội dung hợp lệ theo gold tại mốc hay không |
| `answer`, `context` trong bản công bố | Đáp án ngắn và lời văn đối chiếu |
| `review` trong metadata | Xuất xứ và trạng thái kiểm nhãn |

<!-- nguồn: docs/vilextime-schema-phat-hanh.md -->
<!-- nguồn: scripts/pipeline/export_release.py -->

## 4.4. Vòng thử v1.0: quy mô bản đã chạy

Tên phát hành `vilextime-v1.0` khác với phiên bản schema `2.0.0`; đây là vòng thử đã chạy theo ADR, không phải bộ test cuối của kế hoạch hiện hành. Manifest final ghi 769 dòng chính và 859 dòng silver. Bảng kết quả chính của test dùng 211 dòng giữa khoảng, thuộc 165 lineage; silver không được gộp vào bảng này. Datasheet vẫn có bảng quy mô của một bản dựng cũ, nên chỉ dùng manifest final và file kết quả tương ứng để mô tả bản đã chạy.
<!-- nguồn: data/vilextime_dataset/manifest.json -->
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md @51f36c7 -->

| Nhóm v1.0, test, giữa khoảng | Dòng | Lineage |
|---|---:|---:|
| T1 | 123 | 123 |
| T2 | 46 | 23 |
| T3 | 12 | 4 |
| T6 | 30 | 15 |
| All | 211 | 165 |

<!-- nguồn: data/vilextime_dataset/vilextime.jsonl -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Sự nhỏ đi của các lát sau kiểm nhãn là đặc điểm thực của bản v1.0 đã chạy, không phải quy mô bộ test cuối đang chuẩn bị. Không dùng quota dự kiến để mô tả số mẫu đã được xác nhận. Đặc biệt, loại các câu có nội dung chuyển chỗ làm thay đổi mạnh tập bãi bỏ, nên kết quả không đại diện cho mọi trường hợp một điều khoản từng bị bãi bỏ ở vị trí cũ.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: data/vilextime_dataset/manifest.json -->

## 4.5. Độ đồng thuận và nguồn nhãn v1.0

Các số đo đồng thuận và audit là thống kê mô tả về chất lượng nhãn, không phải phán quyết thuộc họ XN. Kế hoạch ngày 05/11 ghi A gán khoảng 5 giây mỗi dòng trong đợt 26/10. Thời gian này không đủ làm cơ sở tin rằng các bước đối chiếu được thực hiện đầy đủ; AC1 không được diễn giải như phép đo đồng thuận pháp lý đáng tin cậy chỉ vì có hai tên người gán.
<!-- nguồn: docs/plans/active/master-plan.md, D1 -->

Biên bản D5 lịch sử báo AC1 0,612, khoảng tin cậy 95% [0,511; 0,697], và κ 0,323 trên 300 dòng của đợt kiểm cũ. Manifest final ghi phép đo theo hướng dẫn hiện hành trên 246 dòng: AC1 0,377, khoảng [0,250; 0,496], κ 0,235, khoảng [0,144; 0,320], và thỏa thuận nhãn âm 0,395. Hai phép đo khác bộ mẫu và phiên bản hướng dẫn; không lấy số thuận lợi hơn để thay số của tập được dùng. Cả hai đều không chứng minh đạt cổng đồng thuận. Việc chọn AC1 diễn ra sau pilot, không được mô tả là đã đăng ký trước.
<!-- nguồn: docs/reports/D5_bien_ban.md -->
<!-- nguồn: data/vilextime_dataset/manifest.json -->

Tại các dòng ranh giới của test v1.0, metadata ghi 88 dòng do A và B cùng nhãn, 33 dòng có nhãn phân xử/kiểm của luật sư và 90 dòng chỉ có nhãn Codex (T1: 75; T6: 15). Trong phần luật sư có 10 dòng ghi đã dùng phiếu Claude hỗ trợ; không đồng nhất việc có chữ “luật sư” với một quy trình hoàn toàn độc lập khỏi AI. Các nhãn này được truyền sang dòng giữa khoảng tương ứng, không phải một lượt người gán mới ở mỗi mốc.
<!-- nguồn: data/vilextime_dataset/vilextime_meta.jsonl -->
<!-- nguồn: docs/vilextime-datasheet.md -->

Agent có AC1 0,721 và thỏa thuận âm 0,610 trên mẫu hiệu chuẩn mù 178 dòng; ngưỡng AC1 0,80 không đạt trên toàn tập. Mẫu luật sư kiểm nhãn agent đồng ý 43/50, khoảng Wilson 95% [0,738; 0,930]. Kết quả này cung cấp thông tin về chất lượng của mẫu kiểm, không xác nhận toàn bộ nhãn agent. Việc code chỉ sử dụng nhãn agent ở T1 và T6 là một quyết định phạm vi, không chứng minh hai nhóm đều đạt mọi ngưỡng hiệu chuẩn.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: scripts/pipeline/export_release.py -->

Quy tắc phát hành v1.0 ưu tiên nhãn luật sư, tiếp đến A/B đồng thuận, rồi nhãn agent đúng phạm vi. Khi A lệch agent trong nhánh được phép, code lấy verdict của agent; test ngoài phạm vi không được coi là đã kiểm chỉ với một nhãn người. Điều này khác mô tả cũ trong tài liệu schema rằng một người là đủ. Vì vậy, nhãn của bản v1.0 phải được giải thích bằng `final_labels` và metadata thực tế.
<!-- nguồn: scripts/pipeline/export_release.py -->
<!-- nguồn: docs/vilextime-schema-phat-hanh.md -->

## 4.6. Vòng thử test 2 — nhãn LLM

Test 2 là vòng thử lặp lại có khai báo dùng **nhãn LLM**, không phải nhãn người hoặc luật sư. Sau khi loại các lineage thuộc văn bản dev, release có 101 lineage và 492 dòng ở mọi chế độ. Lát giữa khoảng dùng trong E3 có quy mô dưới đây. Bộ này được báo riêng, không cộng vào v1.0 để tăng cỡ mẫu hay tạo một bảng kết quả chung.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

| Nhóm test 2 — nhãn LLM, giữa khoảng | Dòng | Lineage |
|---|---:|---:|
| T2 | 120 | 60 |
| T3 | 75 | 25 |
| T6 | 32 | 16 |
| All | 227 | 101 |

<!-- nguồn: data/vilextime/test2_release_v2.jsonl -->
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

Hai LLM gán độc lập, các trường hợp lệch được hòa giải bằng model và một số ca phân vân được agent hỗ trợ tra cứu. Báo cáo đồng thuận ghi AC1 của Q1, Q2, Q3 lần lượt 0,907; 0,884; 0,766, nhưng thỏa thuận nhãn âm tương ứng chỉ 0,476; 0,222; 0,133. AC1 tương đối cao ở vài câu hỏi kiểm không đủ để kết luận nhãn đáng tin cậy khi cổng nhãn âm không đạt. Amendment cũng ghi rõ chưa có người hoặc luật sư kiểm bộ này.
<!-- nguồn: data/review/test2_llm/agreement.json -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: data/review/test2_llm_v2/calib_score.json -->

Lời dặn dùng khi gán nhãn test 2 cũng có giới hạn, được phát hiện khi rà ngày 04/11. Model chỉ nhận thẻ gán nhãn viết cho người và vài dòng dặn thêm, không có các định nghĩa mà thẻ trỏ tới và không có bước hiệu chuẩn. Model không được tra cứu ngoài các đoạn trích, nên Q4 = Không phần lớn chỉ có nghĩa là không thấy quy định khác trong phần được đưa; chỉ sáu câu phân vân được agent tra luật kiểm lại. Lời dặn còn yêu cầu "phải khắt khe" ngoài nội dung của thẻ, và với cùng lời dặn, hai model loại 45 và 24 trên 138 câu. Nguyên văn lời dặn được lưu ở `prompts/vilextime/test2_gan_v1.md`. Nhóm đã viết lời dặn bản 2 đầy đủ hơn và khai báo trước một cổng hiệu chuẩn (amendment 04/11 (b)): so với 68 câu có nhãn người độc lập, nhãn cuối phải đạt AC1 ≥ 0,80 và p_neg ≥ 0,60. Kết quả không đạt: AC1 0,530 và p_neg 0,758. Trong 29 câu người gán xấu, quy trình bắt 25; trong 39 câu người gán tốt, quy trình loại nhầm 12. Mẫu này có 25/29 câu xấu ở T6, nên gần như không đo được khả năng bắt câu xấu ở T2 và T3. Theo khai báo trước, nhóm dừng lại: không gán test 2 bằng bản 2, không sửa lời dặn và không có phân tích độ nhạy. Kết quả này đo lời dặn bản 2, không đo trực tiếp nhãn test 2 đang dùng, vì lời dặn bản 1 chưa từng được hiệu chuẩn. Do đó chưa có số đo nào cho biết nhãn test 2 khớp với người đến đâu.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Có một lần chấm E3 test 2 — nhãn LLM — sai do release thiếu đáp án ngắn và phép kiểm chứa span coi tập span rỗng là thỏa. Amendment ngày 04/11 khai báo sửa trường đáp án ngắn và chấm lại các dự đoán đã có, không sinh hoặc truy xuất lại. Mọi Accuracy của test 2 trong khóa luận chỉ lấy từ `runs/E3_test2/rescore/`; bản kết quả cũ được giữ làm hồ sơ sai sót, không được trích như số hợp lệ. Bộ chấm hiện từ chối dòng có đáp án nhưng thiếu span vàng trong phần đang chấm.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: scripts/eval/score_vilextime.py -->

## 4.7. Đối chiếu Bảng 1 của đề cương và kế hoạch dữ liệu

Bảng dưới đếm cặp (câu hỏi, mốc) ở chế độ ranh giới trên các phần dữ liệu, khác bảng test giữa khoảng của vòng thử. T4 là lát của T2 và T3 nên không cộng lần nữa vào tổng. “Đang có” bao gồm silver chưa kiểm và nhãn LLM; không phải tổng mẫu đã được người xác nhận.
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 -->

<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx; docs/plans/active/master-plan.md, mục 5 -->
| Nhóm | Đề cương | v1.0 | Silver chưa kiểm | Test 2, nhãn LLM | Đang có | Dự báo sau kiểm |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 250 | 141 | 0 | 0 | 141 | 251 (thêm 110) |
| T2 | 400 | 118 | 274 | 120 | 512 | ~490 |
| T3 | 200 | 31 | 95 | 75 | 201 | ~200 |
| T4 (lát) | 150 | 24 | 102 | 30 | 156 | ~130 |
| T5 | 50 | 0 | 20 | 0 | 20 | ~12 |
| T6 | 100 | 72 | 0 | 32 | 104 | ~155 |
| Tổng, không trùng T4 | 1.150 | 362 | 389 | 227 | 978 | ~1.100 |
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 -->

Cột cuối là **dự báo của kế hoạch**, giả định 60% câu qua kiểm và hoàn tất phần bổ sung; không phải kết quả quan sát. Tổng theo Bảng 1 của đề cương cũng cần giải thích lại khi T4 được tính như lát chồng lắp theo quyết định A2. Số phát hành thực tế phải thay bằng kết quả G2, phân biệt tầng người gán đôi và luật sư với tầng LLM/agent, không gộp hai tầng trong bảng chính.
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 -->
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx -->

## 4.8. Thiết kế bộ test cuối và quy trình người gán

Bộ test cuối chỉ dùng lineage chưa có hệ nào chạy. Theo kiểm kê trong kế hoạch, nguồn silver chưa có dự đoán trong `runs/`, không trùng lineage của v1.0 và test 2, không trùng văn bản đích với dev. Đây là điều kiện tuyển chọn, chưa phải tuyên bố bộ cuối đã khóa. T1 bổ sung làm đối chứng và đối chiếu quy mô; không vào bộ tương phản cuối vì không có thay đổi lời văn cần phân biệt.
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 -->

Các nguồn đưa cho người kiểm dưới đây là kế hoạch, chưa phải mẫu đạt. Dự báo được giữ nguyên từ master plan để tránh biến mong muốn về cỡ mẫu thành dữ liệu đã có.

<!-- nguồn: docs/plans/active/master-plan.md, mục 5 -->
| Nguồn | Câu đưa cho người | Dự báo qua kiểm |
|---|---:|---:|
| Silver T2, gồm phần gần giống | 137 | ~82 |
| Silver T3 | 31 | ~19 |
| Silver T5, báo riêng | 10 | ~6 |
| T6 mới, LLM lọc trước | 60 | ~25 |
| T3 mới | 20 | ~12 |
| T2 mới nếu đủ giờ | 60 | ~45 |
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 -->

Kế hoạch đặt cổng G2 tối thiểu 130 lineage người kiểm, mục tiêu khoảng 180; nếu thiếu giờ thì cắt nguồn ưu tiên thấp, không hạ tiêu chuẩn nhãn hoặc bỏ kiểm gold mù. Lô thử G1 lấy 30 câu từ test 2, không lấy silver để giữ nguyên nguồn bộ cuối. Những con số này là ngưỡng và mục tiêu có sẵn trong kế hoạch, chưa phải cỡ mẫu đã thu được.
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 và 7 -->

Thẻ gán theo câu hỏi gồm các câu kiểm sau; phải đối chiếu mọi mốc được đưa, không gán độc lập một nhãn mới cho mỗi bản sao mốc.

| Câu kiểm | Nội dung thẻ | Dẫn chứng cần đọc |
|---|---|---|
| Q1 | Đáp án ở mỗi mốc có đúng văn bản không? | Văn bản tác động, câu sửa/bãi bỏ, điều hiệu lực; cả lời văn đầy đủ và span ngắn |
| Q2 | Câu hỏi có hỏi vào đúng phần tô màu không? | Nội dung thay đổi phải làm đổi đáp án; T6 hỏi nội dung |
| Q3 | Câu hỏi có rõ không? | Một điều khoản trả lời được, không mơ hồ và không lộ đáp án |
| Q4 | Có quy định nào khác đang thay cho đáp án này không? | Quy định cấp cao hơn, quy định ban hành sau, chuyển tiếp và nơi nội dung chuyển đến |
<!-- nguồn: docs/vilextime-annotation.md, mục 2 -->

Nhãn đạt được suy ra khi Q1 Đúng, Q2 Có, Q3 Có và Q4 Không. Q4 Không chắc không vào bảng chính. Người gán phải dán một câu trích nguyên văn từ văn bản tác động đã đọc; với T6 và Q4 Không, phải ghi nơi đã tìm. Hai người gán độc lập, không thấy nhãn, gợi ý hoặc ghi chú LLM và không thấy kết quả hệ. Luật sư chốt dòng lệch mà không có phiếu AI hỗ trợ. Đây là quy trình bộ cuối, khác thực hành của các vòng thử.
<!-- nguồn: docs/vilextime-annotation.md -->
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 -->

Trang gán phải ghi thời gian từng câu. Cổng G1 yêu cầu AC1 ≥ 0,80 và p_neg ≥ 0,60 trên từng Q1–Q4 cùng trung vị thời gian ≥ 90 giây/câu; dưới mức thời gian đó phải dừng và xem lại. Thời gian là dấu hiệu tuân thủ quy trình, không phải bảo đảm người gán đúng. [CHỜ G2: số thực tế của lô thử, nhãn bộ cuối, AC1/p_neg và phân bố thời gian được khóa ở G1–G2].
<!-- nguồn: docs/plans/active/master-plan.md, mục 5 và 7 -->

### Tiếp xúc trước với đáp án đồ thị và gold mù theo người

Đối chiếu lại `lineage_id` của silver T2–T3 với các dòng **có verdict không rỗng** trong phiếu A cho thấy: ở vòng 25/10 theo hồ sơ tác giả, A đã gán **131/168 lineage**, tương ứng **283 dòng**, trong đó **280 `dat`** và **3 `khong_dat`**. Các dòng này có trường `answer` và `cac_phien_ban`: A đã được cho thấy đáp án cùng lịch sử phiên bản do đồ thị dựng. Không đếm các dòng phiếu còn trống là đã gán, cũng không coi đây là bằng chứng A đã đọc đủ nguồn pháp lý.
<!-- nguồn: data/review/kiem_A.tsv; data/vilextime_dataset/vilextime_silver.jsonl; phép đo: lấy lineage T2/T3 silver, giao phiếu A có verdict khác rỗng, đếm dòng/lineage/verdict; ngày vòng theo yêu cầu C9b của tác giả -->

Điều kiện “hệ chưa chạy” của silver vẫn khác điều kiện “người chưa thấy đáp án”. Khi thu nhãn mới, cần khai lần tiếp xúc này; một lượt A gán lại trên cùng lineage không trở thành một quan sát mù mới. Quy trình bộ cuối yêu cầu không thấy gợi ý hoặc nhãn LLM và kết quả hệ; gold độc lập còn đòi không thấy lời văn do đồ thị dựng. Vì vậy phải xác định độ mù theo từng người và từng lineage, không chỉ gọi chung cả silver là mới.
<!-- nguồn: data/review/kiem_A.tsv; docs/plans/active/master-plan.md, mục 5 và A6 -->

Gói hiện có ở `data/review/the4/gold1/` chia câu theo người. `gold_sample.tsv` có **60 dòng mẫu**: **22 chỉ A**, **23 chỉ B**, **15 cả hai**; từ đó `gold_A.tsv` có **37 phiếu**, `gold_B.tsv` có **38 phiếu**. Đối chiếu với các lineage A đã gán cho thấy **0** lineage đó được giao A ở gold1; phần chỉ B có **23** lineage A đã gán. Với B, giao giữa lineage B đã gán trong `kiem_B.tsv` và phần giao B cũng bằng **0**. Đây là kiểm tra cấu trúc phân công, chưa chứng minh người không xem ngoài phiếu hoặc đã hoàn thành gold. Các cột `hieu_luc`, `noi_dung`, `van_ban_ap_dung` của cả hai phiếu đều trống. Không nhầm lô chuẩn bị hiện có với mục tiêu gold mù của kế hoạch.
<!-- nguồn: data/review/the4/gold1/gold_sample.tsv; data/review/the4/gold1/gold_A.tsv; data/review/the4/gold1/gold_B.tsv; data/review/kiem_A.tsv; data/review/kiem_B.tsv -->

Theo A6, câu gold của mỗi người phải được giữ khỏi lô gán của chính người đó cho đến khi họ điền xong gold. Việc gán lại nhãn câu hỏi và việc tự tìm đáp án từ văn bản gốc/VBHN là hai loại bằng chứng; phải lưu riêng. [CHỜ G2: gold1 được người điền và đối soát độ mù theo người; khai báo tiếp xúc cũ khi thu nhãn mới].
<!-- nguồn: docs/plans/active/master-plan.md, A6 và quy tắc sau mục 11; data/review/the4/gold1/ -->

## 4.9. Độ tin cậy, giới hạn và tài liệu hóa

Gold và hệ đề xuất cùng dựa vào kho sự kiện và phiên bản. Khi kho bỏ sót một lần sửa đổi, hệ thống và bộ đánh giá có thể cùng sử dụng lời văn sai mà vẫn đồng ý với nhau. Gold độc lập vẫn chưa hoàn tất; không thể dùng độ chính xác trên ViLexTime để suy ra trực tiếp độ đúng pháp lý ngoài kho. Khả năng phát hiện lỗi gold qua kiểm câu hỏi cũng phụ thuộc năng lực và thời gian người kiểm.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md @51f36c7 -->

Datasheet của dự án tự khai được tổ chức theo hướng tài liệu hóa bộ dữ liệu [@gebru2021datasheets]. Tuy nhiên, tài liệu hiện chứa cả trạng thái và số liệu lịch sử lẫn cập nhật cuối; sự tồn tại của datasheet không chứng minh dữ liệu đã đạt chất lượng yêu cầu. [CẦN: đọc bản gốc tài liệu Datasheets for Datasets trước khi hoàn tất trích dẫn; references.bib hiện ghi mới kiểm tóm tắt].
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: references.bib -->

Các nguy cơ còn lại gồm thiên lệch chọn câu dễ diễn đạt, quan hệ giữa model viết câu hỏi với nhóm hiện tượng, phụ thuộc nguồn vbpl.vn và việc chuyển tiếp pháp luật có thể nằm ngoài corpus. Việc chọn generator khác họ model viết dữ liệu chỉ giảm một nguy cơ xung đột, không loại bỏ mọi thiên lệch do dữ liệu sinh bằng AI. Không được gọi test 2 — nhãn LLM — là gold độc lập do người xây dựng.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## 4.10. Câu trả lời có thể rút ra

ViLexTime cung cấp phép đo theo câu hỏi–mốc với truy nguyên phiên bản và một cơ chế kiểm tra tương phản giữa các lời văn. Các bước loại và hòa giải giúp nhận diện những trường hợp không thể đơn giản coi là “hết hiệu lực nên không có đáp án”. Tuy nhiên, đồng thuận thấp, sự tham gia rộng của LLM và thiếu gold độc lập giới hạn mức khẳng định về chất lượng. Giá trị hiện có của bộ dữ liệu là một tài nguyên đánh giá có công bố xuất xứ và sai sót; chưa phải chuẩn vàng pháp lý đã được kiểm độc lập đầy đủ.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/reports/D5_bien_ban.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## Việc còn thiếu trước khi nộp

- Hoàn tất hoặc công bố chưa hoàn tất gold độc lập và các lượt audit người còn thiếu.
- [CẦN: đối soát phễu chọn ứng viên, phân bố năm và loại văn bản trên bản final, không dùng bảng lịch sử thay thế].
- Chuẩn hóa số câu hỏi khác nhau, số lineage và số dòng theo yêu cầu của khoa; trình bày rõ chỗ lệch với đề cương.
- Kiểm tài liệu gốc cho trích dẫn phương pháp tài liệu hóa dữ liệu; giữ nguyên nhãn LLM của test 2 trong mọi lần biên tập.
