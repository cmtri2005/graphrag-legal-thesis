# Chương 4. Bộ dữ liệu ViLexTime

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

## 4.4. Quy mô bản v1.0 được dùng trong thực nghiệm

Tên phát hành `vilextime-v1.0` khác với phiên bản schema `2.0.0`. Manifest final ghi 769 dòng chính và 859 dòng silver. Bảng kết quả chính của test dùng 211 dòng giữa khoảng, thuộc 165 lineage; silver không được gộp vào bảng này. Datasheet vẫn có bảng quy mô của một bản dựng cũ, nên chỉ dùng manifest final và file kết quả tương ứng để mô tả bản đã chạy.
<!-- nguồn: data/vilextime_dataset/manifest.json -->
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md -->

| Nhóm v1.0, test, giữa khoảng | Dòng | Lineage |
|---|---:|---:|
| T1 | 123 | 123 |
| T2 | 46 | 23 |
| T3 | 12 | 4 |
| T6 | 30 | 15 |
| All | 211 | 165 |

<!-- nguồn: data/vilextime_dataset/vilextime.jsonl -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Sự nhỏ đi của các lát sau kiểm nhãn là đặc điểm thực của tập cuối. Không dùng quota dự kiến để mô tả số mẫu đã được xác nhận. Đặc biệt, loại các câu có nội dung chuyển chỗ làm thay đổi mạnh tập bãi bỏ, nên kết quả không đại diện cho mọi trường hợp một điều khoản từng bị bãi bỏ ở vị trí cũ.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: data/vilextime_dataset/manifest.json -->

## 4.5. Độ đồng thuận và nguồn nhãn v1.0

Các số đo đồng thuận và audit là thống kê mô tả thăm dò về chất lượng nhãn, không phải phán quyết thuộc họ XN.

Biên bản D5 lịch sử báo AC1 0,612, khoảng tin cậy 95% [0,511; 0,697], và κ 0,323 trên 300 dòng của đợt kiểm cũ. Manifest final ghi phép đo theo hướng dẫn hiện hành trên 246 dòng: AC1 0,377, khoảng [0,250; 0,496], κ 0,235, khoảng [0,144; 0,320], và thỏa thuận nhãn âm 0,395. Hai phép đo khác bộ mẫu và phiên bản hướng dẫn; không lấy số thuận lợi hơn để thay số của tập được dùng. Cả hai đều không chứng minh đạt cổng đồng thuận. Việc chọn AC1 diễn ra sau pilot, không được mô tả là đã đăng ký trước.
<!-- nguồn: docs/reports/D5_bien_ban.md -->
<!-- nguồn: data/vilextime_dataset/manifest.json -->

Tại các dòng ranh giới của test v1.0, metadata ghi 88 dòng do A và B cùng nhãn, 33 dòng có nhãn phân xử/kiểm của luật sư và 90 dòng dùng nhãn agent. Trong phần luật sư có 10 dòng ghi đã dùng phiếu Claude hỗ trợ; không đồng nhất việc có chữ “luật sư” với một quy trình hoàn toàn độc lập khỏi AI. Các nhãn này được truyền sang dòng giữa khoảng tương ứng, không phải một lượt người gán mới ở mỗi mốc.
<!-- nguồn: data/vilextime_dataset/vilextime_meta.jsonl -->
<!-- nguồn: docs/vilextime-datasheet.md -->

Agent có AC1 0,721 và thỏa thuận âm 0,610 trên mẫu hiệu chuẩn mù 178 dòng; ngưỡng AC1 0,80 không đạt trên toàn tập. Mẫu luật sư kiểm nhãn agent đồng ý 43/50, khoảng Wilson 95% [0,738; 0,930]. Kết quả này cung cấp thông tin về chất lượng của mẫu kiểm, không xác nhận toàn bộ nhãn agent. Việc code chỉ sử dụng nhãn agent ở T1 và T6 là một quyết định phạm vi, không chứng minh hai nhóm đều đạt mọi ngưỡng hiệu chuẩn.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: scripts/pipeline/export_release.py -->

Quy tắc phát hành hiện hành ưu tiên nhãn luật sư, tiếp đến A/B đồng thuận, rồi nhãn agent đúng phạm vi. Khi A lệch agent trong nhánh được phép, code lấy verdict của agent; test ngoài phạm vi không được coi là đã kiểm chỉ với một nhãn người. Điều này khác mô tả cũ trong tài liệu schema rằng một người là đủ. Vì vậy, nhãn của tập cuối phải được giải thích bằng `final_labels` và metadata thực tế.
<!-- nguồn: scripts/pipeline/export_release.py -->
<!-- nguồn: docs/vilextime-schema-phat-hanh.md -->

## 4.6. Test 2 — nhãn LLM

Test 2 là bản lặp lại dùng **nhãn LLM**, không phải nhãn người hoặc luật sư. Sau khi loại các lineage thuộc văn bản dev, release có 101 lineage và 492 dòng ở mọi chế độ. Lát giữa khoảng dùng trong E3 có quy mô dưới đây. Bộ này được báo riêng, không cộng vào v1.0 để tăng cỡ mẫu hay tạo một bảng kết quả chung.
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

## 4.7. Độ tin cậy, giới hạn và tài liệu hóa

Gold và hệ đề xuất cùng dựa vào kho sự kiện và phiên bản. Khi kho bỏ sót một lần sửa đổi, hệ thống và bộ đánh giá có thể cùng sử dụng lời văn sai mà vẫn đồng ý với nhau. Gold độc lập vẫn chưa hoàn tất; không thể dùng độ chính xác trên ViLexTime để suy ra trực tiếp độ đúng pháp lý ngoài kho. Khả năng phát hiện lỗi gold qua kiểm câu hỏi cũng phụ thuộc năng lực và thời gian người kiểm.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md -->

Datasheet của dự án tự khai được tổ chức theo hướng tài liệu hóa bộ dữ liệu [@gebru2021datasheets]. Tuy nhiên, tài liệu hiện chứa cả trạng thái và số liệu lịch sử lẫn cập nhật cuối; sự tồn tại của datasheet không chứng minh dữ liệu đã đạt chất lượng yêu cầu. [CẦN XÁC MINH: đọc bản gốc tài liệu Datasheets for Datasets trước khi hoàn tất trích dẫn; references.bib hiện ghi mới kiểm tóm tắt].
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: references.bib -->

Các nguy cơ còn lại gồm thiên lệch chọn câu dễ diễn đạt, quan hệ giữa model viết câu hỏi với nhóm hiện tượng, phụ thuộc nguồn vbpl.vn và việc chuyển tiếp pháp luật có thể nằm ngoài corpus. Việc chọn generator khác họ model viết dữ liệu chỉ giảm một nguy cơ xung đột, không loại bỏ mọi thiên lệch do dữ liệu sinh bằng AI. Không được gọi test 2 — nhãn LLM — là gold độc lập do người xây dựng.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## 4.8. Câu trả lời có thể rút ra

ViLexTime cung cấp phép đo theo câu hỏi–mốc với truy nguyên phiên bản và một cơ chế kiểm tra tương phản giữa các lời văn. Các bước loại và hòa giải giúp nhận diện những trường hợp không thể đơn giản coi là “hết hiệu lực nên không có đáp án”. Tuy nhiên, đồng thuận thấp, sự tham gia rộng của LLM và thiếu gold độc lập giới hạn mức khẳng định về chất lượng. Giá trị hiện có của bộ dữ liệu là một tài nguyên đánh giá có công bố xuất xứ và sai sót; chưa phải chuẩn vàng pháp lý đã được kiểm độc lập đầy đủ.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/reports/D5_bien_ban.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## Việc còn thiếu trước khi nộp

- Hoàn tất hoặc công bố chưa hoàn tất gold độc lập và các lượt audit người còn thiếu.
- [CẦN XÁC MINH: đối soát phễu chọn ứng viên, phân bố năm và loại văn bản trên bản final, không dùng bảng lịch sử thay thế].
- Chuẩn hóa số câu hỏi khác nhau, số lineage và số dòng theo yêu cầu của khoa; trình bày rõ chỗ lệch với đề cương.
- Kiểm tài liệu gốc cho trích dẫn phương pháp tài liệu hóa dữ liệu; giữ nguyên nhãn LLM của test 2 trong mọi lần biên tập.
