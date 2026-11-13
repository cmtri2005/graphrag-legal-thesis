# Chương 6. Thực nghiệm và phân tích

**Câu hỏi của chương:** Các kết quả đã có cho biết gì về giá trị của bộ lọc thời gian, biểu diễn phiên bản và mở rộng đồ thị; những kết luận nào vẫn chưa đủ bằng chứng?

> Bộ test cuối chưa chạy. v1.0 và test 2 được đổi vai thành vòng thử ngày 05/11 sau khi đã thấy kết quả; các bảng dưới giữ kết quả và phán quyết lịch sử, không phải kết luận cuối của khóa luận. Bản nháp chỉ sử dụng kết quả đã lưu. Mọi phân tích ngoài họ xác nhận được ghi là **thăm dò**. Test 2 là **nhãn LLM**, được trình bày riêng với v1.0. Không dùng số dev để kết luận trên test.

## 6.1. Thiết kế phép đo và phạm vi kết quả

Các hệ hiện có đầu ra test là `b1`, `b2ctx`, `b5`, `b7`, `b7pp`, `proposed`. Cùng generator Qwen3-4B-Instruct-2507 và cấu hình bị khóa ở ADR được dùng cho hai bộ; lời văn, nhãn và thành phần nhóm của hai bộ khác nhau. Phạm vi hiện có chưa bao gồm đầy đủ mọi hệ trong kế hoạch E2–E6. `proposed` của hai vòng thử chỉ dùng truy xuất từ vựng; không dùng nó để mô tả kết quả của kiến trúc lai ghép `proposed2`.
<!-- nguồn: runs/README.md -->
<!-- nguồn: docs/plans/active/master-plan.md -->

Bảng chính dùng `giua_khoang`, nhóm all gồm T1, T2, T3, T6 khi nhóm tương ứng có mặt. TV-Recall chấm đúng ID phiên bản hoặc bằng chứng được chấp nhận; Recall có thể chấp nhận điều khoản ở phiên bản khác. Accuracy là phép chấm tương phản trên span ngắn, không phải mức tương đồng ngữ nghĩa do người phán xét. Câu trả lời phải chứa các span gold và tránh các span chỉ thuộc phiên bản khác. Dòng không có đáp án chỉ đúng khi dự đoán khẳng định `answerable=False`.
<!-- nguồn: scripts/eval/score_vilextime.py -->

TVER chỉ có mẫu số ở các dòng có trích dẫn phân giải theo định nghĩa scorer; TVER thấp phải đọc cùng độ phủ và `tver_strict`. VCR cần trích dẫn mang phiên bản; `wrong_version` xét đoạn văn bản khác phiên bản trong nội dung trả lời trên phần có span phân biệt. Không dùng các tỷ lệ có mẫu số khác nhau thay thế lẫn nhau.
<!-- nguồn: scripts/eval/score_vilextime.py -->

Khoảng tin cậy 95% dùng bootstrap theo cụm lineage với 10.000 lần lấy mẫu lại. Họ Holm lịch sử gồm XN1–XN4, XN8, XN9; ngưỡng 0,05. XN5–XN7 nằm ngoài họ và chỉ thăm dò. Ba phép so sánh tầng truy xuất XN1, XN3, XN4 chỉ dùng dòng có đáp án. Ước lượng và khoảng dưới đây dùng thang tỷ lệ; nhân với 100 sẽ đổi sang điểm phần trăm, không phải phần trăm tăng tương đối.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: scripts/eval/confirm_vilextime.py -->

Theo ADR, phán quyết lịch sử giữ quy tắc đúng chiều và p sau Holm dưới ngưỡng. Không dùng số ngoài họ để thêm phán quyết xác nhận.
† Với các ô JSON lưu p bằng 0 sau 10.000 lần bootstrap, bảng dùng quy ước độ phân giải p thô < 0,0002, p Holm ≤ 0,0012 cho họ sáu phép lịch sử. Đây là cách trình bày độ phân giải Monte Carlo, không phải khẳng định p lý thuyết bằng 0 hoặc cận tin cậy của p. Các p khác giữ nguyên; không tính lại họ lịch sử khi bỏ XN2 khỏi thiết kế bộ cuối.
<!-- nguồn: scripts/eval/confirm_vilextime.py, run và holm; runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

V1.0 được khai là bản xác nhận lần 1 trong ADR 0005; amendment 03/11 gọi test 2 là bản lặp lại. Ngày 05/11, sau khi đã thấy kết quả (XN1 được ủng hộ ở v1.0, không đủ bằng chứng ở test 2), kế hoạch mới đổi vai cả hai thành vòng thử và mở bộ cuối. Đây là thay đổi sau quan sát, không phải vai trò được định trước. Giữ cả ba phán quyết cạnh nhau, không gộp điểm hoặc chọn phán quyết thuận lợi. [CHỜ G3: amendment ghi lịch sử các lần nhìn và quy tắc kết luận trước bộ cuối].
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md, §1 và amendment 03/11; runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json; docs/plans/active/master-plan.md, xử lý C3 -->

TVER tự động đọc `effective_intervals` của cùng đồ thị mà bộ lọc và gold sử dụng; gold mù của một dòng chỉ kiểm phiên bản đích, không kiểm mọi trích dẫn hệ trả về. Vì thế không gọi việc chấm lại dòng gold mù là “TVER độc lập”. Theo hướng xử lý đã chấp nhận, XN2 được đưa ra khỏi họ xác nhận của bộ cuối, giữ như kiểm nhất quán nội bộ; giả thuyết đề cương được quyết bằng TV-Recall của XN1 sau amendment. Phán quyết XN2 lịch sử vẫn giữ nguyên nhãn lịch sử.
<!-- nguồn: scripts/eval/score_vilextime.py, row_scores và units_of; runs/x4_verifier_dev/report.json; docs/plans/active/master-plan.md, xử lý C1 -->

TVER theo người là phép đo riêng còn chờ: lấy khoảng 100 đơn vị thực sự được trích từ các hệ, người đọc nguồn gốc và mốc hỏi mà không thấy cửa sổ đồ thị, kết luận còn hiệu lực hay không. Báo mẫu số, tỷ lệ sai, Wilson và phụ thuộc do cùng lineage; không thay bằng gold phiên bản. [CHỜ G4: phiếu, kết quả và khoảng Wilson của TVER theo người].
<!-- nguồn: docs/plans/active/master-plan.md, xử lý C1 và việc người thêm -->

### Bộ test cuối: thiết kế đã khóa

Thiết kế cho bộ test cuối được khóa trong ADR 0006, Accepted ở commit `ac32a89` ngày 12/11/2026, trước lần chạy duy nhất (G4, 12–13/11). ADR ghi rõ các vòng thử đã thấy (v1.0, test 2, dev). Hệ đề xuất P là `proposed2`; generator GPT-4o mini khóa theo ADR 0004.
<!-- nguồn: docs/decisions/0006-*.md, §2, §3, §8 -->

Họ xác nhận gồm bảy kiểm định, Holm α = 0,05, bootstrap theo cụm lineage B = 10.000:

| Mã | Câu hỏi | So sánh | Thước đo | Lát |
|---|---|---|---|---|
| F1 | RQ2, so với RAG phẳng lai ghép | P − `b4` | Accuracy | all |
| F2 | RQ2, so với mở rộng đồ thị phi thời gian | P − `b5` | Accuracy | all |
| F3 | RQ2, lỗi sai phiên bản | P − `b4` | `wrong_version` | all |
| F4 | RQ3, lọc ngày văn bản | `b7` − `b2ctx` | TV-Recall@1 | all_answerable |
| F5 | RQ3, lọc khoảng phiên bản | `b7plus` − `b7` | TV-Recall@1 | all_answerable |
| F6 | Giả thuyết đề cương (H0) | `b7pp` − `b7` | TV-Recall@1 | all_answerable |
| F7 | T6 | P − `b7pp` | Accuracy | t6_unanswerable |
<!-- nguồn: docs/decisions/0006-*.md, §3 -->

`b5` là mở rộng một bước trên cùng đường ống, không phải GraphRAG đầy đủ. TVER nội bộ (F8), RQ1, thành phần, nhóm và miền là mô tả, ngoài Holm (ADR 0006 §4).

Vì GPT-4o mini ở nhiệt độ 0 vẫn đổi câu trả lời giữa các lần gọi, mỗi hệ sinh chạy hai lần độc lập. Lần 1 là kết quả chính, khai trước. Một kiểm định chỉ được gọi là ủng hộ khi cả hai lần cùng phán quyết (ADR 0006 §5b).

Quy tắc cho H0 theo F6, khóa trước khi chạy (ADR 0006 §6). Hai vòng thử cũ không được dùng để đổi phán quyết của bộ cuối:

| Phán quyết v1.0 | Phán quyết test 2 (nhãn LLM) | F6 bộ cuối | Kết luận cho H0 |
|---|---|---|---|
| Ủng hộ | Điểm quyết định B7 | **Ủng hộ, cả hai lần** | Ủng hộ, kèm ghi chú lần lặp test 2 không đủ bằng chứng |
<!-- nguồn: runs/E3_v1/test/confirm.log; runs/E3_test2/rescore/confirm.log; runs/final_g4_20261112/compare_runs.json; docs/decisions/0006-*.md §6 -->

Các chỉ số Recall@k, MRR, TV-Recall, Accuracy, EM/F1, TVER, VCR và TCS lấy từ scorer. Giám khảo LLM chưa được hiệu chuẩn với người nên không dùng. Phiếu người chấm 100 câu trả lời đang chờ (REFACTOR_PLAN 1.5).

## 6.2. Vòng thử v1.0 — nhãn hỗn hợp người và agent

Lát giữa khoảng của test v1.0 có 211 dòng thuộc 165 lineage. Các kiểm định truy xuất dùng 196 dòng có đáp án, vẫn thuộc 165 lineage. Đây là bản phát hành v1.0 đã chạy. Tên trường `final` trong manifest chỉ trạng thái bản phát hành lịch sử, không phải bộ test cuối theo kế hoạch mới. Nhãn test gồm nguồn người và agent như Chương 4; không gọi toàn bộ bảng là kết quả trên nhãn người.
<!-- nguồn: runs/E3_v1/test/confirm.json -->

### 6.2.1. Kết quả tổng thể v1.0 — mô tả thăm dò
<!-- nguồn: runs/E3_v1/test/all.score.json -->

| Hệ | Accuracy [KTC 95%] | TV-R@1 [KTC 95%] | TVER [KTC 95%] | Phủ trích dẫn [KTC 95%] | TVER strict [KTC 95%] |
|---|---|---:|---:|---:|---:|
| `b1` | 0,000 [0,000; 0,000] | 0,000 [0,000; 0,000] | — | 0,000 [0,000; 0,000] | 1,000 [1,000; 1,000] |
| `b2ctx` | 0,474 [0,408; 0,543] | 0,289 [0,230; 0,352] | 0,471 [0,401; 0,538] | 0,995 [0,985; 1,000] | 0,474 [0,404; 0,541] |
| `b5` | 0,479 [0,413; 0,547] | 0,289 [0,230; 0,352] | 0,471 [0,401; 0,538] | 0,995 [0,985; 1,000] | 0,474 [0,404; 0,541] |
| `b7` | 0,640 [0,572; 0,706] | 0,417 [0,347; 0,488] | 0,133 [0,090; 0,177] | 0,995 [0,985; 1,000] | 0,137 [0,093; 0,182] |
| `b7pp` | 0,635 [0,564; 0,706] | 0,464 [0,391; 0,537] | 0,000 [0,000; 0,000] | 0,995 [0,985; 1,000] | 0,005 [0,000; 0,015] |
| `proposed` | 0,654 [0,585; 0,721] | 0,464 [0,391; 0,537] | 0,005 [0,000; 0,015] | 0,991 [0,976; 1,000] | 0,014 [0,000; 0,032] |

<!-- nguồn: runs/E3_v1/test/all.score.json -->

### 6.2.2. Accuracy theo nhóm v1.0 — thăm dò
<!-- nguồn: runs/E3_v1/test/all.score.json -->

| Hệ | T1 | T2 | T3 | T6 |
|---|---|---|---|---|
| `b1` | 0,000 [0,000; 0,000] | 0,000 [0,000; 0,000] | 0,000 [0,000; 0,000] | 0,000 [0,000; 0,000] |
| `b2ctx` | 0,626 [0,545; 0,707] | 0,304 [0,196; 0,391] | 0,083 [0,000; 0,250] | 0,267 [0,133; 0,400] |
| `b5` | 0,634 [0,553; 0,715] | 0,304 [0,196; 0,391] | 0,083 [0,000; 0,250] | 0,267 [0,133; 0,400] |
| `b7` | 0,724 [0,642; 0,797] | 0,609 [0,435; 0,761] | 0,583 [0,167; 0,917] | 0,367 [0,233; 0,467] |
| `b7pp` | 0,699 [0,618; 0,780] | 0,674 [0,500; 0,848] | 0,583 [0,167; 0,917] | 0,333 [0,200; 0,433] |
| `proposed` | 0,699 [0,618; 0,780] | 0,761 [0,609; 0,891] | 0,583 [0,167; 0,917] | 0,333 [0,200; 0,433] |

<!-- nguồn: runs/E3_v1/test/all.score.json -->

### 6.2.3. Họ kiểm định xác nhận v1.0
<!-- nguồn: runs/E3_v1/test/confirm.json -->

| XN | So sánh và đại lượng | Ước lượng [KTC 95%] | p Holm | Dòng / lineage | Kết luận |
|---|---|---|---:|---|---|
| XN1 | b7pp − b7, TV-R@1 (E1, có đáp án) | +0,051 [+0,021; +0,088] | 0,0008 | 196/165 | ủng hộ |
| XN2 | b7pp − b7, TVER (E3) | -0,133 [-0,179; -0,090] | ≤ 0,0012† | 211/165 | ủng hộ |
| XN3 | b7 − b2ctx, TV-R@1 (E1, có đáp án) | +0,138 [+0,089; +0,191] | ≤ 0,0012† | 196/165 | ủng hộ |
| XN4 | b7plus − b7, TV-R@1 (E1, có đáp án) | +0,051 [+0,020; +0,087] | 0,0008 | 196/165 | ủng hộ |
| XN8 | proposed − b5, Accuracy | +0,175 [+0,115; +0,234] | ≤ 0,0012† | 211/165 | ủng hộ |
| XN9 | b2ctx − b1, Accuracy | +0,474 [+0,409; +0,542] | ≤ 0,0012† | 211/165 | ủng hộ |

<!-- nguồn: runs/E3_v1/test/confirm.json -->

Trên v1.0, tất cả các kiểm định trong họ đều có phán quyết **ủng hộ**; XN1 và XN2 đều ủng hộ, nên **H0 được ủng hộ theo quy tắc lịch sử** của ADR 0005 §6; đây không phải xác nhận pháp lý vì XN2 phụ thuộc cùng đồ thị. Công cụ cũng ghi “H0: ủng hộ” trong log xác nhận. Phạm vi khẳng định là bộ dữ liệu, generator và cấu hình đã đo. Đây chưa đủ để khẳng định ưu thế chung của suy luận đồ thị, vì các kiểm định không tách hết biểu diễn, lọc ngày và phần trực tuyến; gold độc lập cũng chưa có.
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: runs/E3_v1/test/confirm.log -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## 6.3. Vòng thử test 2 — nhãn LLM

Test 2 dùng nhãn LLM, không phải nhãn người hoặc luật sư. Lát giữa khoảng có 227 dòng, 101 lineage; phần có đáp án gồm 211 dòng. Không gộp bộ này vào v1.0 hoặc xem nó như gold độc lập do người kiểm.
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Lần chấm E3 đầu của test 2 — nhãn LLM — đã sai: release thiếu đáp án ngắn, còn phép kiểm chứa span coi tập rỗng là đúng. Amendment 04/11 công bố lỗi và dùng release `test2_release_v2.jsonl` để chấm lại đúng các đầu ra cũ. Tất cả Accuracy và các kết quả phụ thuộc nó ở mục này lấy từ `runs/E3_test2/rescore/`. Không lấy Accuracy từ `runs/E3_test2/test/` hoặc bảng E1 cũ. Việc chấm lại không phải một lần sinh hay truy xuất test mới.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

### 6.3.1. Kết quả tổng thể test 2 — nhãn LLM, mô tả thăm dò
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

| Hệ | Accuracy [KTC 95%] | TV-R@1 [KTC 95%] | TVER [KTC 95%] | Phủ trích dẫn [KTC 95%] | TVER strict [KTC 95%] |
|---|---|---:|---:|---:|---:|
| `b1` | 0,000 [0,000; 0,000] | 0,000 [0,000; 0,000] | — | 0,000 [0,000; 0,000] | 1,000 [1,000; 1,000] |
| `b2ctx` | 0,150 [0,108; 0,195] | 0,070 [0,040; 0,104] | 0,682 [0,611; 0,748] | 0,982 [0,956; 1,000] | 0,687 [0,618; 0,753] |
| `b5` | 0,150 [0,110; 0,193] | 0,070 [0,040; 0,104] | 0,709 [0,640; 0,774] | 0,982 [0,956; 1,000] | 0,714 [0,646; 0,778] |
| `b7` | 0,308 [0,242; 0,379] | 0,115 [0,073; 0,160] | 0,219 [0,166; 0,273] | 0,987 [0,969; 1,000] | 0,229 [0,176; 0,283] |
| `b7pp` | 0,317 [0,241; 0,396] | 0,141 [0,079; 0,211] | 0,000 [0,000; 0,000] | 0,987 [0,969; 1,000] | 0,013 [0,000; 0,031] |
| `proposed` | 0,335 [0,262; 0,411] | 0,141 [0,079; 0,211] | 0,013 [0,000; 0,031] | 0,987 [0,969; 1,000] | 0,026 [0,009; 0,048] |

<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

### 6.3.2. Accuracy theo nhóm test 2 — nhãn LLM, thăm dò
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

| Hệ | T2 | T3 | T6 |
|---|---|---|---|
| `b1` | 0,000 [0,000; 0,000] | 0,000 [0,000; 0,000] | 0,000 [0,000; 0,000] |
| `b2ctx` | 0,167 [0,108; 0,225] | 0,093 [0,040; 0,147] | 0,219 [0,094; 0,375] |
| `b5` | 0,175 [0,117; 0,233] | 0,093 [0,040; 0,147] | 0,188 [0,062; 0,312] |
| `b7` | 0,350 [0,258; 0,442] | 0,253 [0,147; 0,373] | 0,281 [0,125; 0,438] |
| `b7pp` | 0,325 [0,225; 0,433] | 0,320 [0,187; 0,467] | 0,281 [0,125; 0,438] |
| `proposed` | 0,392 [0,292; 0,492] | 0,267 [0,133; 0,400] | 0,281 [0,125; 0,438] |

<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

### 6.3.3. Họ kiểm định xác nhận test 2 — nhãn LLM
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

| XN | So sánh và đại lượng | Ước lượng [KTC 95%] | p Holm | Dòng / lineage | Kết luận |
|---|---|---|---:|---|---|
| XN1 | b7pp − b7, TV-R@1 (E1, có đáp án) | +0,028 [-0,014; +0,072] | 0,4596 | 211/101 | không đủ bằng chứng |
| XN2 | b7pp − b7, TVER (E3) | -0,219 [-0,273; -0,165] | ≤ 0,0012† | 227/101 | ủng hộ |
| XN3 | b7 − b2ctx, TV-R@1 (E1, có đáp án) | +0,047 [+0,023; +0,078] | ≤ 0,0012† | 211/101 | ủng hộ |
| XN4 | b7plus − b7, TV-R@1 (E1, có đáp án) | +0,028 [-0,014; +0,072] | 0,4596 | 211/101 | không đủ bằng chứng |
| XN8 | proposed − b5, Accuracy | +0,185 [+0,127; +0,246] | ≤ 0,0012† | 227/101 | ủng hộ |
| XN9 | b2ctx − b1, Accuracy | +0,150 [+0,109; +0,195] | ≤ 0,0012† | 227/101 | ủng hộ |

<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

Trên test 2 — nhãn LLM — XN2, XN3, XN8 và XN9 **ủng hộ**, còn XN1 và XN4 **không đủ bằng chứng**. Các khoảng của XN1 và XN4 chứa không; không được đổi lời kết luận thành “bác” hay coi ước lượng điểm dương là bằng chứng đủ. XN2 ủng hộ nhưng XN1 không được ủng hộ, nên theo đúng ADR 0005 §6, H0 của bộ này đi vào nhánh **“điểm quyết định B7”**. Log xác nhận in cùng kết luận. ADR xác định đây là kết quả đã khai báo trước, không phải thất bại. Đó là vai trò bảng chính và bảng lặp lại trong thiết kế lịch sử của ADR. Theo kế hoạch hiện hành, cả hai là vòng thử; hai kết quả H0 khác nhau không thay thế kết luận chính còn chờ G4.
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/confirm.log -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## 6.4. So sánh hai vòng thử

### 6.4.1. Mức lặp lại của các phán quyết lịch sử

Amendment 03/11 yêu cầu xét cùng chiều khi mô tả sự lặp lại và cấm gộp hai bộ thành một bảng. XN2 đều có ước lượng âm; XN3, XN8 và XN9 đều dương. Các phép so sánh này cùng chiều và đều có phán quyết **ủng hộ** trên cả v1.0 lẫn test 2 — nhãn LLM. Nhận định chỉ áp dụng cho các phép đo tương ứng và không loại được sai lệch gold chung.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

XN1 và XN4 cũng cùng chiều dương, đáp ứng phần điều kiện về chiều, nhưng test 2 — nhãn LLM — có phán quyết **không đủ bằng chứng** ở cả hai. Vì vậy, không gọi bằng chứng xác nhận của hai phép này là đã lặp lại đầy đủ. Trên từng bộ, XN1 và XN4 có cùng ước lượng điểm sau làm tròn vì b7pp và b7plus có cùng TV-Recall@1 trong thang E1. Các bảng E1 giữa khoảng ghi cặp b7pp/b7plus cùng đạt 0,464 trên v1.0 và cùng đạt 0,141 trên test 2 — nhãn LLM. Các file confirm dùng lát có đáp án và cũng ghi ước lượng điểm bằng nhau; chúng vẫn là các kiểm định riêng với seed và khoảng tin cậy riêng, không phải một kết quả bị sao chép.
<!-- nguồn: runs/E1/test/ladder.score.json -->
<!-- nguồn: runs/E1_test2/test/ladder.score.json -->
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: scripts/eval/confirm_vilextime.py -->

Về độ lớn, XN9 trên v1.0 là +0,474 còn trên test 2 — nhãn LLM — là +0,150; XN3 lần lượt là +0,138 và +0,047. Đây là đối chiếu mô tả thăm dò giữa hai mẫu, không phải kiểm định hiệu số giữa các bộ. V1.0 có T1, còn test 2 — nhãn LLM — không có T1; thành phần mẫu, câu hỏi và nguồn nhãn cũng khác. Chưa có thiết kế cho phép quy toàn bộ chênh lệch độ lớn cho riêng việc thiếu T1.
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: data/vilextime_dataset/manifest.json -->
<!-- nguồn: data/vilextime/test2_release_v2.jsonl -->

### 6.4.2. Phân rã chênh lệch — mô tả

**Vòng thử v1.0 — thăm dò.**

Chênh lệch `b7 − b5` là +0,161, KTC 95% [+0,104; +0,217], trong khi `proposed − b7pp` chỉ +0,019 [+0,005; +0,039]. XN8 đo cả khoảng cách giữa một cấu hình phi thời gian và hệ đề xuất, nên không thể dùng nó như ước lượng riêng của đóng góp đồ thị trực tuyến. Đối chiếu các mốc cấu hình cho thấy phần lớn mức tăng quan sát được xuất hiện trước phần mở rộng trực tuyến, tại các hệ có lọc ngày. Tuy nhiên, b7 và b5 còn khác việc mở rộng, nên đây là phân rã mô tả, không phải phép nhận diện nhân quả sạch của riêng bộ lọc.
<!-- nguồn: runs/E3_v1/test/all.score.json -->
<!-- nguồn: src/vilexgraph/framework/systems.py -->

**Vòng thử test 2 — nhãn LLM, thăm dò.**

Chênh lệch `b7 − b5` là +0,159, KTC 95% [+0,107; +0,212], còn `proposed − b7pp` là +0,018 [−0,026; +0,058]. Khoảng của phần trực tuyến chứa không. Không kết luận phần trực tuyến có lợi ích đã xác nhận và không quy mức tăng XN8 cho đồ thị. Các số này gợi ý giá trị thực dụng của bộ lọc ngày và biểu diễn hơn là một hiệu ứng trực tuyến lớn đã được chứng minh.
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

### 6.4.3. Những thất bại cần nêu trực tiếp

Ở v1.0, tất cả các hệ đã chạy đều đúng 0/15 dòng bãi bỏ. Ở test 2 — nhãn LLM — mỗi hệ chỉ đúng từ 0 đến 1 trên 16 dòng bãi bỏ; `b2ctx`, `b7`, `b7pp`, `proposed` đúng 1 dòng, `b1` và `b5` không có dòng đúng. Vì vậy, chưa có hệ nào thể hiện khả năng nhận ra bãi bỏ một cách đáng tin cậy. TVER bằng không ở b7pp không phủ nhận thất bại này: tránh trích dẫn hết hiệu lực khác với kết luận đúng rằng nội dung đã không còn hiệu lực tại mốc hỏi.
<!-- nguồn: runs/E3_v1/test/b1.jsonl -->
<!-- nguồn: runs/E3_v1/test/b2ctx.jsonl -->
<!-- nguồn: runs/E3_v1/test/b5.jsonl -->
<!-- nguồn: runs/E3_v1/test/b7.jsonl -->
<!-- nguồn: runs/E3_v1/test/b7pp.jsonl -->
<!-- nguồn: runs/E3_v1/test/proposed.jsonl -->
<!-- nguồn: runs/E3_test2/test/b1.jsonl -->
<!-- nguồn: runs/E3_test2/test/b2ctx.jsonl -->
<!-- nguồn: runs/E3_test2/test/b5.jsonl -->
<!-- nguồn: runs/E3_test2/test/b7.jsonl -->
<!-- nguồn: runs/E3_test2/test/b7pp.jsonl -->
<!-- nguồn: runs/E3_test2/test/proposed.jsonl -->

`b1` để trống 182/196 câu có đáp án ở v1.0. Với test 2 — nhãn LLM — con số tương ứng là 208/211. XN9 vì thế là phép so với một generator gần như không đưa ra câu trả lời trong điều kiện không căn cứ và prompt đã dùng. Dù phán quyết XN9 là ủng hộ, không suy ra rằng mọi LLM không truy xuất đều kém như cấu hình này hoặc rằng khoảng cách sẽ giữ nguyên với một model mạnh hơn.
<!-- nguồn: runs/E3_v1/test/b1.jsonl -->
<!-- nguồn: data/vilextime_dataset/vilextime.jsonl -->
<!-- nguồn: runs/E3_test2/test/b1.jsonl -->
<!-- nguồn: data/vilextime/test2_release_v2.jsonl -->

### 6.4.4. E7 do máy — thăm dò

Các bảng sau phân loại toàn bộ dòng sai theo thứ tự ưu tiên đã công bố. ABST dùng cờ khẳng định hiệu lực trong dự đoán; RET-UNIT kiểm sự hiện diện của điều khoản; RET-VER phân biệt hướng cũ/mới khi thiếu gold; GEN-BLANK và GEN-MISREAD chỉ xét sau khi căn cứ đúng đã có trong prompt. Một lỗi chỉ thuộc một tầng, nên đây là cách phân bổ ưu tiên, không chứng minh nguyên nhân nhân quả duy nhất. Cột “chứa bản khác” là tập con của MISREAD, không cộng thêm vào tổng.
<!-- nguồn: scripts/review/e7_error_analysis.py -->

**Vòng thử v1.0 — thăm dò, do máy phân loại.**

| Hệ | ABST | RET-UNIT | RET-VER-OLD | RET-VER-NEW | GEN-BLANK | GEN-MISREAD | Chứa bản khác | Tổng sai |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| b7 | 15 | 19 | 2 | 0 | 1 | 39 | 5 | 76 |
| b7pp | 15 | 19 | 0 | 0 | 2 | 41 | 2 | 77 |
| proposed | 15 | 19 | 0 | 0 | 1 | 38 | 2 | 73 |

<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

| Hệ | TV-R@20, chỉ dòng có đáp án | Đúng khi prompt có căn cứ, chỉ dòng có đáp án |
|---|---|---|
| b7 | 175/196 = 0,893 | 135/175 = 0,771 |
| b7pp | 177/196 = 0,903 | 134/177 = 0,757 |
| proposed | 177/196 = 0,903 | 138/177 = 0,780 |
<!-- nguồn: docs/reports/e7_phan_ra_loi.md, cột "Chỉ dòng có đáp án"; data/vilextime_dataset/vilextime.jsonl; runs/E3_v1/test/{b7,b7pp,proposed}.jsonl; scripts/paper/paper_values.py -->

**Vòng thử test 2 — nhãn LLM, thăm dò, do máy phân loại.**

| Hệ | ABST | RET-UNIT | RET-VER-OLD | RET-VER-NEW | GEN-BLANK | GEN-MISREAD | Chứa bản khác | Tổng sai |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| b7 | 21 | 72 | 14 | 0 | 7 | 43 | 8 | 157 |
| b7pp | 20 | 86 | 0 | 0 | 8 | 41 | 2 | 155 |
| proposed | 19 | 85 | 0 | 0 | 7 | 40 | 1 | 151 |

<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

| Hệ | TV-R@20, chỉ dòng có đáp án | Đúng khi prompt có căn cứ, chỉ dòng có đáp án |
|---|---|---|
| b7 | 118/211 = 0,559 | 67/118 = 0,568 |
| b7pp | 120/211 = 0,569 | 70/120 = 0,583 |
| proposed | 120/211 = 0,569 | 74/121 = 0,612 |
<!-- nguồn: docs/reports/e7_phan_ra_loi.md, cột "Chỉ dòng có đáp án"; data/vilextime/test2_release_v2.jsonl; runs/E3_test2/test/{b7,b7pp,proposed}.jsonl; scripts/paper/paper_values.py -->

Hai tỷ lệ dùng mẫu số khác nhau: top-20 chỉ xét danh sách đầu, còn prompt gồm mọi căn cứ mở rộng. Với `proposed` test 2 (nhãn LLM), 120 dòng có căn cứ ở top-20 nhưng 121 trong toàn prompt. Không bỏ căn cứ ngoài top-20 hoặc gộp hai định nghĩa. Dòng không có đáp án không vào mẫu số truy xuất này; các tần suất lỗi phía trên vẫn dùng toàn bộ dòng sai. Tỷ lệ có điều kiện chỉ mô tả, chưa có KTC.
<!-- nguồn: docs/reports/e7_phan_ra_loi.md; scripts/review/e7_error_analysis.py -->

Phân tích máy cho thấy hai chỗ nghẽn có thể cùng tồn tại: thiếu căn cứ và dùng sai căn cứ đã có. Nó chưa tách được lỗi gold, câu hỏi mơ hồ, đọc sai ngữ nghĩa hay rào đón theo đánh giá của người. Phiếu người gán đã được lấy mẫu có seed; cột hệ và tầng máy được giữ ngoài phiếu người, nối với file máy bằng `stt`. Việc tạo phiếu không đồng nghĩa đã có kết quả E7 do người kiểm.
<!-- nguồn: scripts/review/e7_error_analysis.py -->
<!-- nguồn: data/review/e7/phieu_v1.tsv -->
<!-- nguồn: data/review/e7/phieu_test2.tsv -->

### 6.4.5. Các phân tích bổ sung

### XN5–XN7 và đầy đủ các nhóm — thăm dò

XN5 là Accuracy `b7pp − b7plus` trên bãi bỏ qua tổ tiên; XN6 là VCR `b2ctx` giữa T2 gần giống và thường; XN7 là chênh lệch của hiệu Accuracy `proposed − b7` giữa T6 và T2/T3. p dưới đây là p thô, không Holm; XN7 v1.0 ngược chiều dự đoán H2, nhưng vẫn chỉ là thăm dò.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md, §4; scripts/eval/confirm_vilextime.py -->

**V1.0**

| Mã | Ước lượng [KTC 95%] | p thô | Dòng / lineage theo lát |
|---|---|---:|---|
| XN5 | [CHỜ: đầu ra sinh `b7plus`] | — | — |
| XN6 | -0,059 [-0,263; +0,191] | 0,5738 | 8/4 và 38/19 |
| XN7 | -0,154 [-0,274; -0,051] | 0,0042 | 30/15 và 58/27 |
<!-- nguồn: runs/E3_v1/test/confirm.json -->

**Test 2 (nhãn LLM)**

| Mã | Ước lượng [KTC 95%] | p thô | Dòng / lineage theo lát |
|---|---|---:|---|
| XN5 | [CHỜ: đầu ra sinh `b7plus`] | — | — |
| XN6 | +0,100 [-0,067; +0,278] | 0,2706 | 30/15 và 90/45 |
| XN7 | -0,031 [-0,078; +0,015] | 0,2314 | 32/16 và 195/85 |
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

Hiệu Accuracy [KTC 95%] theo đủ nhóm có mặt; đây là phân tích sau quan sát, ngoài họ kiểm định và chưa hiệu chỉnh đa so sánh. Bảng gồm cả chiều âm, không chỉ chọn T2 thuận lợi.

**V1.0**

| Nhóm | `b7pp − b7`, Accuracy [KTC] | `proposed − b7pp`, Accuracy [KTC] |
|---|---|---|
| T1 | -0,024 [-0,057; +0,000] | +0,000 [+0,000; +0,000] |
| T2 | +0,065 [-0,022; +0,152] | +0,087 [+0,022; +0,174] |
| T3 | +0,000 [+0,000; +0,000] | +0,000 [+0,000; +0,000] |
| T6 | -0,033 [-0,100; +0,000] | +0,000 [+0,000; +0,000] |
<!-- nguồn: runs/E3_v1/test/all.score.json -->

**Test 2 (nhãn LLM)**

| Nhóm | `b7pp − b7`, Accuracy [KTC] | `proposed − b7pp`, Accuracy [KTC] |
|---|---|---|
| T2 | -0,025 [-0,083; +0,042] | +0,067 [+0,017; +0,117] |
| T3 | +0,067 [-0,013; +0,160] | -0,053 [-0,147; +0,027] |
| T6 | +0,000 [+0,000; +0,000] | +0,000 [+0,000; +0,000] |
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

### Chỉ số bổ sung — mô tả, không thêm kiểm định

TCS yêu cầu cả cặp T2 đúng; VCR đo sai phiên bản của trích dẫn theo scorer. MRR tính trên toàn lát, EM/F1 chỉ trên dòng có đáp án; EM đòi khớp lời đáp ngắn nên khác Accuracy chứa span. Không dùng các mẫu số này thay cho nhau.
<!-- nguồn: scripts/eval/score_vilextime.py, row_scores và score -->

**V1.0**

| Hệ | TCS (cặp T2) | VCR | MRR | EM | F1 |
|---|---:|---:|---:|---:|---:|
| `b1` | 0,000 (23) | — | 0,000 | 0,000 | 0,020 |
| `b2ctx` | 0,000 (23) | 0,095 | 0,509 | 0,138 | 0,594 |
| `b5` | 0,000 (23) | 0,095 | 0,509 | 0,133 | 0,589 |
| `b7` | 0,435 (23) | 0,052 | 0,602 | 0,189 | 0,633 |
| `b7pp` | 0,609 (23) | 0,000 | 0,573 | 0,189 | 0,630 |
| `proposed` | 0,652 (23) | 0,005 | 0,573 | 0,184 | 0,633 |
<!-- nguồn: runs/E3_v1/test/all.score.json; scripts/paper/paper_values.py -->

**Test 2 (nhãn LLM)**

| Hệ | TCS (cặp T2) | VCR | MRR | EM | F1 |
|---|---:|---:|---:|---:|---:|
| `b1` | 0,000 (60) | — | 0,000 | 0,000 | 0,002 |
| `b2ctx` | 0,000 (60) | 0,197 | 0,242 | 0,081 | 0,410 |
| `b5` | 0,000 (60) | 0,188 | 0,242 | 0,081 | 0,405 |
| `b7` | 0,167 (60) | 0,121 | 0,270 | 0,161 | 0,448 |
| `b7pp` | 0,233 (60) | 0,000 | 0,224 | 0,185 | 0,428 |
| `proposed` | 0,233 (60) | 0,004 | 0,224 | 0,190 | 0,450 |
<!-- nguồn: runs/E3_test2/rescore/all.score.json; scripts/paper/paper_values.py -->

### Precision và recall khẳng định hết hiệu lực — mô tả

Dự đoán dương là cờ `answerable=False`, không phải mọi câu bỏ trống hay “không rõ”. Recall = đúng trên tổng dòng không có đáp án; precision = đúng trên mọi khẳng định đó, bao gồm khẳng định sai ở dòng có đáp án.
<!-- nguồn: src/vilexgraph/framework/generate.py; scripts/eval/score_vilextime.py -->

**V1.0**

| Hệ | Đúng / dòng bãi bỏ (recall) | Sai trên dòng có đáp án | Precision |
|---|---|---:|---|
| `b1` | 0/15 = 0,000 | 0 | — (không khẳng định) |
| `b2ctx` | 0/15 = 0,000 | 2 | 0/2 = 0,000 |
| `b5` | 0/15 = 0,000 | 2 | 0/2 = 0,000 |
| `b7` | 0/15 = 0,000 | 0 | — (không khẳng định) |
| `b7pp` | 0/15 = 0,000 | 0 | — (không khẳng định) |
| `proposed` | 0/15 = 0,000 | 0 | — (không khẳng định) |
<!-- nguồn: data/vilextime_dataset/vilextime.jsonl; runs/E3_v1/test/{b1,b2ctx,b5,b7,b7pp,proposed}.jsonl; scripts/paper/paper_values.py -->

**Test 2 (nhãn LLM)**

| Hệ | Đúng / dòng bãi bỏ (recall) | Sai trên dòng có đáp án | Precision |
|---|---|---:|---|
| `b1` | 0/16 = 0,000 | 0 | — (không khẳng định) |
| `b2ctx` | 1/16 = 0,062 | 12 | 1/13 = 0,077 |
| `b5` | 0/16 = 0,000 | 7 | 0/7 = 0,000 |
| `b7` | 1/16 = 0,062 | 6 | 1/7 = 0,143 |
| `b7pp` | 1/16 = 0,062 | 5 | 1/6 = 0,167 |
| `proposed` | 1/16 = 0,062 | 4 | 1/5 = 0,200 |
<!-- nguồn: data/vilextime/test2_release_v2.jsonl; runs/E3_test2/test/{b1,b2ctx,b5,b7,b7pp,proposed}.jsonl; scripts/paper/paper_values.py -->

Bộ cuối (thăm dò hậu nghiệm, lần 1): `proposed2` khẳng định "hết hiệu lực" 11 lần, 7 đúng, 4 sai. Precision 0,64, recall 7/23. Lệnh bãi bỏ có trong prompt ở 12/23 dòng, trong đó đúng 5. `oracle` 22/23 khi được cấp sẵn căn cứ. Số lần 2 ở `attribution.json`. T6 bộ cuối chưa có gold mù người. `proposed3` không chạy trên bộ cuối. Không suy các số này từ TVER hoặc từ việc đã có thông báo bãi bỏ.
<!-- nguồn: docs/plans/active/master-plan.md, xử lý C2, N8 và V5 -->

### Đóng góp XN1 theo nhóm và độ nhạy cỡ mẫu — thăm dò

Bảng chỉ đếm TV-hit@1 trên dòng có đáp án E1; tăng/mất là chuyển trạng thái theo từng dòng, không phải số dòng độc lập.

**V1.0**

| Nhóm | Dòng có đáp án / lineage | Tăng hit / mất hit | Chênh lệch số hit |
|---|---|---|---:|
| T1 | 123/123 | 0/0 | +0 |
| T2 | 46/23 | 6/0 | +6 |
| T3 | 12/4 | 4/0 | +4 |
| T6 | 15/15 | 0/0 | +0 |
<!-- nguồn: runs/E1/test/b7.jsonl; runs/E1/test/b7pp.jsonl; data/vilextime_dataset/vilextime.jsonl; scripts/paper/paper_values.py -->

**Test 2 (nhãn LLM)**

| Nhóm | Dòng có đáp án / lineage | Tăng hit / mất hit | Chênh lệch số hit |
|---|---|---|---:|
| T2 | 120/60 | 10/5 | +5 |
| T3 | 75/25 | 3/2 | +1 |
| T6 | 16/16 | 0/0 | +0 |
<!-- nguồn: runs/E1_test2/test/b7.jsonl; runs/E1_test2/test/b7pp.jsonl; data/vilextime/test2_release_v2.jsonl; scripts/paper/paper_values.py -->

Ở v1.0, chênh lệch đến từ 10 dòng của T2/T3, T1 đóng góp 0. Lát bỏ T1 có 10/73 = +0,137; không đối chiếu độ lớn toàn tập v1.0 với bộ cuối không có T1. Silver theo quy trình viết của v1.0, còn test 2 (nhãn LLM) có cổng trùng chữ; “lặp lại” chưa độc lập với cách sinh câu hỏi. [CHỜ G4: phân tầng kết quả bộ cuối theo nguồn silver/T2 mới/T3 mới/T6 mới và quy trình sinh].
<!-- nguồn: data/vilextime_dataset/vilextime.jsonl; data/vilextime/test2_release_v2.jsonl; scripts/review/test2_packs.py; scripts/paper/paper_values.py; docs/plans/active/master-plan.md, mục 10 -->

Xấp xỉ chuẩn hai phía lấy hiệu +0,028 và phương sai theo cụm lineage từ E1 test 2 (nhãn LLM): SE 0,022; nếu giữ phân bố đó và có 150 lineage thì SE dự phóng 0,018, power tại α = 0,05 là 0,346. Nếu phải vượt ngay ngưỡng Holm bảo thủ α/6 của họ sáu phép lịch sử, power còn 0,141; các bậc Holm muộn hơn có thể cao hơn. Không có một power sau Holm duy nhất khi chưa khóa họ và chưa biết thứ tự p. Đây là phân tích độ nhạy sau quan sát, không phải power đo được của bộ cuối. [CHỜ G3: họ cuối và giả định cỡ mẫu đã khóa].
<!-- nguồn: runs/E1_test2/test/b7.jsonl; runs/E1_test2/test/b7pp.jsonl; data/vilextime/test2_release_v2.jsonl; runs/E3_test2/rescore/confirm.json; scripts/paper/paper_values.py, phương sai tỷ số theo cụm và NormalDist; docs/plans/active/master-plan.md, dự báo mục 10 -->

## 6.5. Thử nghiệm `proposed2` trên dev — mô tả để phát triển hệ

Các số dưới chỉ đánh giá truy xuất trên dev. Việc thay `rel` bằng `rel_up` được chọn sau khi xem lỗi dev; không phải kiểm định xác nhận, chưa có sinh câu trả lời. Tên file `proposed-hyb` của lượt đồ thị đi lên cha tương ứng cấu hình được gọi là `proposed2` trong kế hoạch hiện tại.
<!-- nguồn: runs/README.md; src/vilexgraph/framework/systems.py -->

Trước khi thay mở rộng, phép thử lai ghép trên 151 dòng dev ghi R@1 của `b7pp` và `proposed` từ 0,424 xuống 0,411, trong khi R@10 từ 0,722 lên 0,735. Không có cơ sở nói lai ghép đã làm tốt hơn trên mọi vị trí. Cấu hình được kiểm tiếp để hoàn thiện L4 của đề cương; kết quả này không dùng để chọn dựa trên test.
<!-- nguồn: runs/hybrid_20261105/dev/retrieval.score.json; runs/README.md -->

Sau khi tìm lệnh tác động ở chuỗi cha, R@30 trên dòng T6 không có đáp án từ 0/21 lên 15/21; trên toàn dev từ 122/151 = 0,808 lên 137/151 = 0,907. R@1 vẫn 62/151 và R@10 vẫn 111/151. Đây là Recall theo danh sách truy xuất mở rộng, không phải Accuracy và không phải bằng chứng generator đã nhận ra bãi bỏ. Mức R@30 trước sửa dùng số đã chấm lại từ file, không dùng số ghi nhầm trong kế hoạch cũ.
<!-- nguồn: runs/hybrid_20261105/dev_graph2/proposed-hyb.jsonl; runs/hybrid_20261105/dev/proposed-hyb.jsonl; runs/README.md -->

[CHỜ COLAB: đầu ra sinh và chấm dev cho `b7pp --hybrid`, `proposed2`, `p2a2`, `p2a3`]. Cần đo tác dụng Verifier khi chưa có bộ lọc mạnh; trên dev cũ, Verifier không bác câu nào và ablation tắt nó trùng đầu ra. Thông báo bãi bỏ có cấu trúc và kiểm độ bền generator còn là công việc theo kế hoạch, không điền số giả định.
<!-- nguồn: docs/plans/active/master-plan.md; runs/README.md -->

### 6.5.1. `proposed3` và điều kiện cấp sẵn căn cứ X8 — còn chờ

`proposed3` kế thừa `proposed2` và bật `repeal_note`, đưa thông báo bãi bỏ có cấu trúc từ đồ thị vào prompt; đây là phần việc trong A7. Chương chưa có đầu ra sinh đã chấm để kết luận tác dụng của cấu hình này. Không mang số `proposed` hay số truy xuất `proposed2` sang nhãn mới. [CHỜ COLAB: đầu ra dev, provenance và điểm `proposed3`; xác nhận cấu hình được khóa trước khi chạy bộ cuối].
<!-- nguồn: docs/plans/active/master-plan.md, A7; src/vilexgraph/framework/systems.py; src/vilexgraph/framework/generate.py; runs/README.md -->

`proposed3` đưa `repeal_note` từ sự kiện `repeal` đã phân giải vào prompt; gold “không có đáp án” của T6 cũng dẫn từ nguồn sự kiện đó. Accuracy T6 vì vậy là cận trên có điều kiện khi đồ thị đúng, chưa phải bằng chứng pháp lý độc lập. Chỉ kết luận trên T6 đã qua gold mù; phải báo cả recall, precision và số khẳng định sai trên dòng có đáp án. Các lượt bổ sung trên T6 của v1.0 và test 2 phải gắn nhãn “đã thấy”, báo riêng từng bộ, không gộp với nhau hay với bộ cuối vì cấu hình được thiết kế sau khi xem lỗi của chúng.
<!-- nguồn: src/vilexgraph/framework/graphx.py, _repeals và repeal_notes; docs/plans/active/master-plan.md, xử lý C2 và N8 -->

Trên dev T6 không có đáp án, Qwen3-4B đúng 6/21 ở `oracle` và 3/21 ở `oracle_v2` dù được cấp ngữ cảnh; các lượt khác prompt nên không gộp. Nhận định “nhận diện bãi bỏ yếu” chỉ nói về Qwen3-4B trong điều kiện này. [CHỜ COLAB: X3 với generator khác, tối thiểu ngữ cảnh đúng của T6; chưa thực hiện và không suy giới hạn chung của LLM].
<!-- nguồn: data/vilextime_dataset/vilextime.jsonl; runs/B2_dev/dev/oracle.jsonl; runs/B2_dev/dev/oracle_v2.jsonl; docs/plans/active/master-plan.md, X3 -->

X8 phải so hai điều kiện **cấp sẵn căn cứ đúng mốc** và **cấp sẵn căn cứ hiện hành**, theo T1 (đối chứng), T2, T3, T6. Mục đích là đo sai lệch do đọc bản hiện hành, tách khỏi lỗi tìm trên toàn kho. Phải chạy dev trước, rồi bộ test cuối sau các cổng khóa. Oracle dev đã có chỉ cho biết kết quả trong điều kiện căn cứ của lượt đó; chưa phải kết quả X8 hay oracle trên test.
<!-- nguồn: docs/plans/active/master-plan.md, X8 và mục 10 -->

| Điều kiện X8 | Kết quả |
|---|---|
| Dev: đúng mốc so với hiện hành, từng nhóm | [CHỜ COLAB: điểm, mẫu số và chênh lệch ghép cặp X8 dev] |
| Bộ cuối: đúng mốc so với hiện hành, từng nhóm | Lần 1, `oracle` / `oracle_now`: all 0,956 / 0,456; T2 0,969 / 0,476; T3 1,000 / 0,278; T6 0,870 / 0,413 (`runs/final_g4_20261112/r1/results.md`) |
<!-- nguồn: docs/plans/active/master-plan.md, X8 -->

Lọc thời gian có lợi và hai nút thắt tìm–đọc đã có tiền lệ [@prior2026oldfriend] [@yao2026lawinforce] [@akarajaradwong2026nitibenchplus]. Phân rã E7 hiện tại là mô tả/thăm dò trên pháp luật Việt Nam; không tuyên bố phát hiện riêng hai nút thắt. Phần có thể kiểm là hai nấc ngày văn bản và khoảng phiên bản; lan truyền chưa có lợi ích đo được. Nhóm bãi bỏ đã có ở NitiBench+, nên chỉ giữ đặc thù lệnh nằm ở văn bản khác và bãi bỏ qua nút cha của Việt Nam. Không đưa số nghiên cứu khác vào bảng điểm chung khi khác tác vụ, gold hoặc mẫu số.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md; docs/plans/active/master-plan.md, mục 10 -->

## 6.6. Bộ test cuối (G4)

**Dữ liệu.** 199 lineage, 361 dòng `giua_khoang`. Lát `all` gồm T2, T3, T6: 156 lineage, 318 dòng. T1 có 43 lineage, là đối chứng ngoài `all`. Cơ cấu: T2 127 lineage, T3 6, T6 23, không có T5. Nhãn thuộc tầng "AI-A/AI-B gán mù, CMT duyệt", chưa luật sư hay người độc lập kiểm (`review.source = "ai_cmt"`).
<!-- nguồn: data/vilextime_final/README.md; data/vilextime_final/STATUS.md -->

### 6.6.1. Họ xác nhận F1–F7

| F | So sánh | Lần 1 (chính) | Lần 2 | Phán quyết |
|---|---|---|---|---|
| F1 | P − `b4`, Accuracy | +0,343 [+0,283; +0,401] | +0,368 [+0,312; +0,422] | ủng hộ, ổn định |
| F2 | P − `b5`, Accuracy | +0,355 [+0,297; +0,414] | +0,352 [+0,297; +0,409] | ủng hộ, ổn định |
| F3 | P − `b4`, `wrong_version` | −0,283 [−0,330; −0,237] | −0,287 [−0,334; −0,239] | ủng hộ, ổn định |
| F4 | `b7` − `b2ctx`, TV-R@1 | +0,078 [+0,049; +0,110] | như lần 1 | ủng hộ |
| F5 | `b7plus` − `b7`, TV-R@1 | +0,115 [+0,076; +0,156] | như lần 1 | ủng hộ |
| F6 | `b7pp` − `b7`, TV-R@1 | +0,115 [+0,076; +0,156] | như lần 1 | ủng hộ |
| F7 | P − `b7pp`, Accuracy, T6 không đáp án | +0,087 [0,000; +0,217] | +0,043 [0,000; +0,130] | không đủ bằng chứng, cả hai lần |
<!-- nguồn: runs/final_g4_20261112/r1/confirm.json; runs/final_g4_20261112/r2/results.md; runs/final_g4_20261112/compare_runs.json -->

F1–F3 đều có p Holm < 0,0002 ở cả hai lần. F4–F6 là hệ chỉ truy xuất nên không chịu dao động của generator. F7 có 23 lineage. MDE ước trước khi chạy là 0,185, nên chỉ phát hiện được hiệu rất lớn. F7 "không đủ bằng chứng" nghĩa là KTC không loại trừ 0 và không loại trừ hiệu ≥ MDE, không có nghĩa là không có hiệu ứng.

**F5 và F6 bằng nhau.** `b7pp` và `b7plus` có cùng TV-R@1 (0,336). Lan truyền trên đồ thị không đổi căn cứ đứng đầu ở dòng nào có đáp án. Vì vậy F6 ủng hộ H0 hoàn toàn nhờ bước lọc khoảng phiên bản, đúng phần F5 đo. Không được đọc F6 là bằng chứng cho phần duyệt đồ thị lúc truy vấn.

### 6.6.2. Bảng mô tả, lần 1

| Hệ | Accuracy [KTC 95%] | TV-R@1 | TVER | Sai phiên bản |
|---|---|---|---|---|
| `b1` | 0,006 [0,000; 0,016] | 0,000 | — | 0,008 |
| `b2ctx` | 0,302 [0,256; 0,348] | 0,151 | 0,535 | 0,253 |
| `b4` | 0,324 [0,277; 0,369] | 0,164 | 0,544 | 0,291 |
| `b5` | 0,311 [0,265; 0,356] | 0,164 | 0,566 | 0,294 |
| `b6` | 0,340 [0,293; 0,386] | 0,164 | 0,553 | 0,283 |
| `b7` | 0,487 [0,428; 0,547] | 0,242 | 0,248 | 0,177 |
| `b7plus` | 0,654 [0,585; 0,722] | 0,336 | 0,022 | 0,008 |
| `b7pp` | 0,660 [0,593; 0,726] | 0,336 | 0,000 | 0,008 |
| `proposed2` | 0,667 [0,598; 0,733] | 0,336 | 0,013 | 0,008 |
| `oracle` | 0,956 [0,927; 0,981] | 1,000 | 0,000 | 0,000 |
| `oracle_now` | 0,456 [0,432; 0,478] | 0,484 | 0,516 | 0,502 |
<!-- nguồn: runs/final_g4_20261112/r1/results.md (all.score.json, 318 dòng) -->

- **RQ1, vế RAG:** RAG phẳng (`b2ctx`, `b4`) trích sai phiên bản ở khoảng một phần tư đến gần một phần ba số dòng (0,253; 0,291).
- **RQ1, vế LLM không truy xuất:** `b1` gần 0 vì thước đo đòi chép đúng lời văn. Bộ cuối chưa đo được tỷ lệ sai phiên bản của LLM không truy xuất (REFACTOR_PLAN 3.1).
- **Đọc bản hiện hành thay bản đúng mốc:** Accuracy rơi từ 0,956 (`oracle`) xuống 0,456 (`oracle_now`), cùng generator. Đây là cỡ của bài toán thời gian khi căn cứ đã có sẵn.
- **Dao động generator:** số câu trả lời đổi giữa hai lần trên `all`: `b4` 49 (12 từ đúng sang sai, 1 ngược lại), `b5` 58, `b7pp` 58, `proposed2` 39, `oracle` 12.
- **T1:** đáp án ngắn của 43 dòng T1 là nguyên lời văn còn ký hiệu liệt kê, `oracle` chỉ đúng 2/43. Cột T1 chưa dùng được, chờ amendment (REFACTOR_PLAN 3.2).
<!-- nguồn: runs/final_g4_20261112/compare_runs.json; runs/final_g4_20261112/r1/results.md -->

### 6.6.3. Quy kết sau khi chạy (thăm dò hậu nghiệm)

Mọi số trong mục này được tính **sau khi đã thấy kết quả G4**, nên chỉ là thăm dò, không thuộc họ xác nhận. Script `scripts/eval/posthoc_g4.py`, kết quả `runs/posthoc_g4_20261113/attribution.json`. Evidence-gate (một phiên AI tách riêng, không phải duyệt của người) ngày 13/11 đã tái chạy và nhận kết quả trùng từng byte.

**Đồ thị lúc truy vấn.** Trên `all` (318 dòng):
- `proposed2 − b7pp`: +0,006 [−0,016; +0,028] lần 1; 0,000 [−0,016; +0,016] lần 2.
- `proposed2 − b7plus`: +0,013 [−0,009; +0,035] lần 1; +0,016 [−0,006; +0,038] lần 2.

KTC chứa 0 ở cả hai lần. Không thấy lợi ích lớn hơn khoảng 4 điểm. Không được viết "bằng nhau".

Ngoại lệ ở T6 không đáp án (23 dòng): `proposed2 − b7plus` +0,174 [+0,043; +0,348] ở cả hai lần. `proposed2 − b7pp` có KTC chạm 0.

**Tách bước kho phiên bản và bước lọc khoảng.** Hệ `b7v` (kho phiên bản, không lọc khoảng) chỉ chạy phần truy xuất, sau khi đã thấy test, theo thang đã khai ở ADR 0006 §2. Kết quả TV-R@1:
- `b7v − b7`: −0,044 [−0,072; −0,019].
- `b7plus − b7v`: +0,159 [+0,120; +0,199].

Kho phiên bản không có bộ lọc khoảng còn kém lớp lời văn gốc. Lợi ích của F5 cần cả kho phiên bản lẫn bộ lọc khoảng.

**Lọc cứng hay chỉ báo khoảng hiệu lực.** Có hai baseline thêm theo amendment ADR 0006 ngày 13/11, được CMT duyệt trước khi chạy trên bộ cuối:
- `bvnone`: kho phiên bản, không lọc.
- `bvdate`: như `bvnone` nhưng in khoảng hiệu lực vào prompt.

Kết quả:
- Accuracy `b7plus − bvdate`: +0,245 lần 1, +0,230 lần 2.
- `bvdate` giảm tỷ lệ trích sai phiên bản (0,317 → 0,064 lần 1; 0,328 → 0,060 lần 2), nhưng vẫn kém lọc cứng xa.

Lọc theo khoảng trước khi xếp hạng có giá trị riêng. Trên dev cùng chiều.

**Nút thắt là xếp hạng.** Khi gold đứng hạng 1, `proposed2` đúng 96%. Nhưng gold chỉ đứng hạng 1 ở 107/295 dòng có đáp án.
<!-- nguồn: runs/posthoc_g4_20261113/attribution.json; runs/posthoc_g4_20261113/test/; docs/plans/active/REFACTOR_PLAN.md, "Kết quả Nhóm 2"; docs/reports/research-audit-20261113.md §8.2 -->

### 6.6.4. Gold mù trên phần bộ cuối nó phủ

Gold mù đợt 1 do người đọc nguồn: khớp thô 148/150, 119/120 sau phân xử do AI đề xuất, CMT xác nhận. Gold này chỉ phủ 24/156 lineage chính của bộ cuối (T2 19, T3 5, không có T6, T1). Tập con vẫn chấm bằng gold của đồ thị.

Trên 53 dòng này, F1–F6 đều ủng hộ ở cả hai lần, cùng chiều với toàn bộ cuối. Ví dụ: F4 +0,075 [+0,018; +0,154]; F5 +0,189 [+0,071; +0,315]. Đây là mô tả trên tập con nhỏ, không thay cho gold độc lập trên cả bộ.
<!-- nguồn: runs/posthoc_g4_20261113/gold_subset/confirm_r1.txt, confirm_r2.txt -->

### 6.6.5. Còn chờ

| Hạng mục | Tình trạng |
|---|---|
| Người chấm 100 câu trả lời (`b1`, `b4`, `proposed2`), độ khớp scorer–người | Phiếu đã dựng, chờ người chấm |
| Đáp án ngắn T1 | Nháp amendment chờ duyệt |
| Gold mù người cho T6 và 132 lineage còn lại | Chưa có người làm |
| TVER theo người, E7 mã hóa lỗi bằng người | Chưa làm |
| LightRAG (GraphRAG phi thời gian thật) | Đang dựng đồ thị trên Colab; chạy bộ cuối cần amendment riêng |
| Generator thứ hai khác họ | Chưa chạy |

Các lượt Colab đợt 2 cho vòng thử cũ (v1.0, test 2) không chạy nữa: kết luận đã lấy từ bộ cuối.

## 6.7. Mối đe dọa tính hợp lệ

**Gold tự chấm và TVER do cách dựng.** Gold phiên bản lấy từ cùng đồ thị mà bộ lọc `b7pp` sử dụng; khi sự kiện bị bỏ sót, cả hai có thể cùng sai. TVER = 0 của `b7pp` phần lớn do cách dựng: bộ lọc đã loại phiên bản không hợp lệ theo chính khoảng hiệu lực mà scorer tham chiếu. Nó kiểm được tính nhất quán trong mô hình, chưa xác nhận độc lập độ đúng pháp lý. Bảng TVER phải đọc cùng gold mù, độ phủ trích dẫn và khả năng trả lời dòng bãi bỏ. [CHỜ G4: TVER theo người trên các đơn vị được trích, không đồng nhất với gold mù phiên bản].
<!-- nguồn: docs/plans/active/master-plan.md, D2; src/vilexgraph/framework/temporal.py; scripts/eval/score_vilextime.py -->

**Giới hạn thành phần.** Các so sánh `proposed` trong vòng thử chỉ đo mở rộng quan hệ một bước cùng Verifier trên đường từ vựng; không suy ra “đồ thị không giúp” cho mọi GraphRAG. `proposed2` chưa được đánh giá câu trả lời. Chuyển từ kết quả một bước sang kết luận về suy luận đồ thị nhiều bước sẽ vượt phạm vi thực nghiệm.
<!-- nguồn: src/vilexgraph/framework/graphx.py; runs/README.md -->

Nhãn v1.0 gồm nguồn người và agent, các cổng đồng thuận không đạt như trình bày ở Chương 4. Test 2 — nhãn LLM — không có lượt xác nhận độc lập của người. Hai bộ cùng dẫn xuất từ một kho phiên bản, còn gold độc lập chưa có và M2 kiểm tay vẫn mở. Vì thế, sự lặp lại của một chiều hiệu ứng trên hai bộ không tự loại được sai lệch chung của nguồn gold và hệ đề xuất.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: docs/plans/active/phase-3-kg-l0-l3.md @51f36c7 -->

Kết quả chỉ dùng một generator và các cấu hình từ vựng hiện có. Sổ chạy dev ghi 553/553 đầu ra giống nhau ở các prompt trùng giữa các biến thể chạy; điều này không chứng minh mọi phần cứng và thư viện đều cho kết quả giống nhau. Chi phí Colab chưa được đối soát đầy đủ. [CẦN: cấu hình GPU, phiên bản thư viện và chi phí thực tế của từng lượt từ provenance và biên nhận; không suy từ ước tính trước chạy].
<!-- nguồn: runs/README.md -->
<!-- nguồn: docs/decisions/0004-framework-truy-xuat-va-sinh.md -->
<!-- nguồn: runs/E3_v1/test/proposed.run.json -->

Các cảnh báo ID `asis:event:` không phân giải được phản ánh phạm vi resolver dựa trên lịch sử phiên bản, không trực tiếp đếm thiếu đích vàng. Không biến số cảnh báo thành trần recall hoặc tự thay metric để xử lý một số ít trích dẫn. Bản nháp giữ số chấm hợp lệ đã lưu và công bố giới hạn phân giải.
<!-- nguồn: scripts/eval/score_vilextime.py -->
<!-- nguồn: runs/README.md -->

### 6.7.1. Đối chiếu điều kiện diễn giải chênh lệch

ADR 0005 §6 yêu cầu thêm các điều kiện của MASTER_RESEARCH_GUIDE §8.6 (tài liệu nội bộ, commit `51f36c7`) ngoài phán quyết thống kê. Bản nháp vì thế dùng “chênh lệch”, “ước lượng” hoặc phán quyết XN, không gọi một chênh lệch quan sát được là cải thiện đã đáp ứng đầy đủ các điều kiện. Các điều kiện đã kiểm được và phần còn thiếu được phân biệt dưới đây.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: MASTER_RESEARCH_GUIDE.md @51f36c7 -->

Về khoảng tin cậy, các hiệu số thuộc họ trên v1.0 có khoảng không chứa không. Trên test 2 — nhãn LLM — điều này được xác nhận ở XN2, XN3, XN8, XN9; không đạt ở XN1 và XN4. Phần trực tuyến proposed − b7pp trên test 2 — nhãn LLM — cũng có khoảng chứa không. Đây là kiểm tra điều kiện thống kê, chưa thay thế các điều kiện còn lại.
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

Về dao động, sổ chạy ghi 553/553 đầu ra giống nhau trên các prompt dev trùng byte giữa các lượt và biến thể attention. Nhóm đã chấp nhận phép đối chiếu này thay lượt lặp dev dự kiến; mức dao động quan sát trên phần đó bằng không. Điều kiện đã được kiểm trong phạm vi dev và các prompt trùng có hồ sơ, không phải phép đo lặp đầy đủ trên test, cũng không chứng minh không có dao động khi thay phần cứng hoặc thư viện.
<!-- nguồn: runs/README.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Về kiểm soát thành phần, code và test cấu hình xác nhận các nấc kề nhau của thang đổi một trường cấu hình. Tuy nhiên, các cặp ghép nhiều nấc và proposed so với b5 không cô lập một thành phần; proposed so với b7pp còn thêm cả mở rộng lẫn Verifier. Vì vậy, chưa thể coi mọi kiểm định có ý nghĩa là hiệu ứng riêng của một cơ chế đồ thị.
<!-- nguồn: src/vilexgraph/framework/systems.py -->
<!-- nguồn: tests/test_rag_systems.py -->

Về độ phủ trích dẫn, b7 và b7pp có cùng độ phủ tổng thể trong từng bộ: 0,995 trên v1.0 và 0,987 trên test 2 — nhãn LLM. Như vậy, mức giảm TVER ở XN2 không đi cùng giảm độ phủ tổng thể. Các cặp khác chưa đồng nhất hoàn toàn: proposed có độ phủ 0,991 trên v1.0; b5 có độ phủ 0,982 trên test 2 — nhãn LLM — trong khi proposed là 0,987. Việc đối chiếu này kiểm được độ phủ tổng thể; chưa phải kiểm soát toàn bộ thay đổi ở từng dòng hay một bảo đảm chung cho mọi cặp.
<!-- nguồn: runs/E3_v1/test/all.score.json -->
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

Điều kiện cùng chiều trên các chế độ as_of và gold độc lập chưa được xác nhận đầy đủ: tầng sinh hiện chỉ có lát giữa khoảng và E6 chưa có. Điều kiện không bị một nhóm hoặc vài văn bản chi phối cũng chưa được kiểm bằng phân tích bỏ lần lượt nhóm/văn bản đã lưu. Các bảng theo nhóm giúp quan sát khác biệt nhưng không thay thế phép kiểm độ bền này.
<!-- nguồn: docs/plans/active/master-plan.md -->
<!-- nguồn: runs/E3_v1/test/all.score.json -->
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

Điều kiện không hệ nào vượt oracle trên cùng test **chưa kiểm được**, vì oracle context test chưa có. Oracle context dev chỉ là đối chiếu mô tả; oracle probe tất định của scorer kiểm đường chấm, không phải generator nhận căn cứ gold trên test. Các điều kiện của §8.6 vì thế chưa đồng thời hoàn tất, dù các phán quyết ủng hộ đã báo trong họ XN vẫn giữ nguyên.
<!-- nguồn: docs/plans/active/master-plan.md -->
<!-- nguồn: runs/README.md -->
<!-- nguồn: scripts/eval/score_vilextime.py -->

## 6.8. Điều có thể diễn giải ở bản nháp

Ở mức **xác nhận trong vòng thử**, các phán quyết lịch sử của XN được giữ nguyên; chúng không trở thành xác nhận trên bộ test cuối. Ở mức **mô tả**, RAG phẳng còn trích sai phiên bản, trong khi baseline LLM không truy xuất gần như không trả lời, nên vế LLM của RQ1 chưa đo được đủ. Ở mức **thăm dò**, lợi ích mở rộng một bước trên toàn tập nhỏ và chưa nhất quán giữa hai vòng; phân rã lỗi máy gợi ý cả nút thắt tìm và đọc căn cứ. Nguồn nhãn hỗn hợp của v1.0 và nhãn LLM của test 2 giới hạn các diễn giải này.
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json; docs/reports/e7_phan_ra_loi.md -->

Bản nháp đi theo hướng tài nguyên và phép đo có đối chứng của master plan: sửa thước đo, hoàn thiện hệ trên dev rồi chạy bộ cuối. Chưa kết luận hệ đề xuất thắng, cũng chưa bác giả thuyết đề cương từ việc một khoảng tin cậy chứa không. [CHỜ G4: kết luận chính của khóa luận, kể cả kết quả không đủ bằng chứng hoặc ngược chiều dự kiến].
<!-- nguồn: docs/plans/active/master-plan.md -->

## Việc còn thiếu trước khi nộp

- Hoàn tất nguồn nhãn người, gold mù và đối chiếu VBHN; giữ nguồn LLM ở bảng riêng.
- Nhập và chấm lượt Colab đã khai báo, không dùng vòng thử để tinh chỉnh.
- Khóa amendment, chạy và báo bộ test cuối; điền đúng các bảng đang chờ.
- Hoàn tất E7 người kiểm, kiểm giám khảo, chi phí và độ bền; phần không có bằng chứng tiếp tục ghi chờ.
