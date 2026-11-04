# Chương 6. Thực nghiệm và phân tích

**Câu hỏi của chương:** Các kết quả đã có cho biết gì về giá trị của bộ lọc thời gian, biểu diễn phiên bản và mở rộng đồ thị; những kết luận nào vẫn chưa đủ bằng chứng?

> Bản nháp chỉ sử dụng kết quả đã lưu. Mọi phân tích ngoài họ xác nhận được ghi là **thăm dò**. Test 2 là **nhãn LLM**, được trình bày riêng với v1.0. Không dùng số dev để kết luận trên test.

## 6.1. Thiết kế phép đo và phạm vi kết quả

Các hệ hiện có đầu ra test là `b1`, `b2ctx`, `b5`, `b7`, `b7pp`, `proposed`. Cùng generator Qwen3-4B-Instruct-2507 và cấu hình bị khóa ở ADR được dùng cho hai bộ; lời văn, nhãn và thành phần nhóm của hai bộ khác nhau. Phạm vi hiện có chưa bao gồm đầy đủ mọi hệ trong kế hoạch E2–E6.
<!-- nguồn: runs/README.md -->
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md -->

Bảng chính dùng `giua_khoang`, nhóm all gồm T1, T2, T3, T6 khi nhóm tương ứng có mặt. TV-Recall chấm đúng ID phiên bản hoặc bằng chứng được chấp nhận; Recall có thể chấp nhận điều khoản ở phiên bản khác. Accuracy là phép chấm tương phản trên span ngắn, không phải mức tương đồng ngữ nghĩa do người phán xét. Câu trả lời phải chứa các span gold và tránh các span chỉ thuộc phiên bản khác. Dòng không có đáp án chỉ đúng khi dự đoán khẳng định `answerable=False`.
<!-- nguồn: scripts/eval/score_vilextime.py -->

TVER chỉ có mẫu số ở các dòng có trích dẫn phân giải theo định nghĩa scorer; TVER thấp phải đọc cùng độ phủ và `tver_strict`. VCR cần trích dẫn mang phiên bản; `wrong_version` xét đoạn văn bản khác phiên bản trong nội dung trả lời trên phần có span phân biệt. Không dùng các tỷ lệ có mẫu số khác nhau thay thế lẫn nhau.
<!-- nguồn: scripts/eval/score_vilextime.py -->

Khoảng tin cậy 95% dùng bootstrap theo cụm lineage với 10.000 lần lấy mẫu lại. Họ Holm gồm XN1–XN4, XN8, XN9; ngưỡng 0,05. XN5–XN7 nằm ngoài họ và chỉ thăm dò. Ba phép so sánh tầng truy xuất XN1, XN3, XN4 chỉ dùng dòng có đáp án. Ước lượng và khoảng dưới đây dùng thang tỷ lệ; nhân với 100 sẽ đổi sang điểm phần trăm, không phải phần trăm tăng tương đối.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: scripts/eval/confirm_vilextime.py -->

Theo ADR, kết luận “ủng hộ” cần p sau Holm dưới ngưỡng và ước lượng đúng chiều; “bác” cần p dưới ngưỡng nhưng ngược chiều; các trường hợp còn lại là “không đủ bằng chứng”. Những giá trị p lưu bằng không là kết quả hữu hạn của Monte Carlo trong file, không có nghĩa xác suất lý thuyết bằng không. Với 10.000 lần lấy mẫu, các ô p Holm đó hiển thị `< 0,0001` trong bảng; giá trị gốc trong JSON được giữ nguyên. Không dùng số ngoài họ để tự bổ sung một phán quyết xác nhận.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: scripts/eval/confirm_vilextime.py -->

## 6.2. Kết quả v1.0

Lát giữa khoảng của test v1.0 có 211 dòng thuộc 165 lineage. Các kiểm định truy xuất dùng 196 dòng có đáp án, vẫn thuộc 165 lineage. Đây là bản phát hành final, không phải bảng quy mô ứng viên trước kiểm.
<!-- nguồn: runs/E3_v1/test/confirm.json -->

### 6.2.1. Kết quả tổng thể v1.0 — mô tả thăm dò

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

| XN | So sánh và đại lượng | Ước lượng [KTC 95%] | p Holm | Dòng / lineage | Kết luận |
|---|---|---|---:|---|---|
| XN1 | b7pp − b7, TV-R@1 (E1, có đáp án) | +0,051 [+0,021; +0,088] | 0,0008 | 196/165 | ủng hộ |
| XN2 | b7pp − b7, TVER (E3) | -0,133 [-0,179; -0,090] | < 0,0001 | 211/165 | ủng hộ |
| XN3 | b7 − b2ctx, TV-R@1 (E1, có đáp án) | +0,138 [+0,089; +0,191] | < 0,0001 | 196/165 | ủng hộ |
| XN4 | b7plus − b7, TV-R@1 (E1, có đáp án) | +0,051 [+0,020; +0,087] | 0,0008 | 196/165 | ủng hộ |
| XN8 | proposed − b5, Accuracy | +0,175 [+0,115; +0,234] | < 0,0001 | 211/165 | ủng hộ |
| XN9 | b2ctx − b1, Accuracy | +0,474 [+0,409; +0,542] | < 0,0001 | 211/165 | ủng hộ |

<!-- nguồn: runs/E3_v1/test/confirm.json -->

Trên v1.0, tất cả các kiểm định trong họ đều có phán quyết **ủng hộ**; XN1 và XN2 đều ủng hộ, nên **H0 được ủng hộ** theo đúng ADR 0005 §6. Công cụ cũng ghi “H0: ủng hộ” trong log xác nhận. Phạm vi khẳng định là bộ dữ liệu, generator và cấu hình đã đo. Đây chưa đủ để khẳng định ưu thế chung của suy luận đồ thị, vì các kiểm định không tách hết biểu diễn, lọc ngày và phần trực tuyến; gold độc lập cũng chưa có.
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: runs/E3_v1/test/confirm.log -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

## 6.3. Kết quả test 2 — nhãn LLM

Test 2 dùng nhãn LLM, không phải nhãn người hoặc luật sư. Lát giữa khoảng có 227 dòng, 101 lineage; phần có đáp án gồm 211 dòng. Không gộp bộ này vào v1.0 hoặc xem nó như gold độc lập do người kiểm.
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Lần chấm E3 đầu của test 2 — nhãn LLM — đã sai: release thiếu đáp án ngắn, còn phép kiểm chứa span coi tập rỗng là đúng. Amendment 04/11 công bố lỗi và dùng release `test2_release_v2.jsonl` để chấm lại đúng các đầu ra cũ. Tất cả Accuracy và các kết quả phụ thuộc nó ở mục này lấy từ `runs/E3_test2/rescore/`. Không lấy Accuracy từ `runs/E3_test2/test/` hoặc bảng E1 cũ. Việc chấm lại không phải một lần sinh hay truy xuất test mới.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

### 6.3.1. Kết quả tổng thể test 2 — nhãn LLM, mô tả thăm dò

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

| XN | So sánh và đại lượng | Ước lượng [KTC 95%] | p Holm | Dòng / lineage | Kết luận |
|---|---|---|---:|---|---|
| XN1 | b7pp − b7, TV-R@1 (E1, có đáp án) | +0,028 [-0,014; +0,072] | 0,4596 | 211/101 | không đủ bằng chứng |
| XN2 | b7pp − b7, TVER (E3) | -0,219 [-0,273; -0,165] | < 0,0001 | 227/101 | ủng hộ |
| XN3 | b7 − b2ctx, TV-R@1 (E1, có đáp án) | +0,047 [+0,023; +0,078] | < 0,0001 | 211/101 | ủng hộ |
| XN4 | b7plus − b7, TV-R@1 (E1, có đáp án) | +0,028 [-0,014; +0,072] | 0,4596 | 211/101 | không đủ bằng chứng |
| XN8 | proposed − b5, Accuracy | +0,185 [+0,127; +0,246] | < 0,0001 | 227/101 | ủng hộ |
| XN9 | b2ctx − b1, Accuracy | +0,150 [+0,109; +0,195] | < 0,0001 | 227/101 | ủng hộ |

<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

Trên test 2 — nhãn LLM — XN2, XN3, XN8 và XN9 **ủng hộ**, còn XN1 và XN4 **không đủ bằng chứng**. Các khoảng của XN1 và XN4 chứa không; không được đổi lời kết luận thành “bác” hay coi ước lượng điểm dương là bằng chứng đủ. XN2 ủng hộ nhưng XN1 không được ủng hộ, nên theo đúng ADR 0005 §6, H0 của bộ này đi vào nhánh **“điểm quyết định B7”**. Log xác nhận in cùng kết luận. ADR xác định đây là kết quả đã khai báo trước, không phải thất bại. Kết luận theo từng bộ không thay thế quyết định M4 của nhóm: v1.0 là bảng chính, còn test 2 — nhãn LLM — là bản lặp lại và hai bộ cho hai kết quả H0 khác nhau.
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/confirm.log -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

### 6.3.4. Mức lặp lại giữa hai bộ

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

## 6.4. Mức tăng đến từ đâu?

### 6.4.1. Phân rã mô tả v1.0 — thăm dò

Chênh lệch `b7 − b5` là +0,161, KTC 95% [+0,104; +0,217], trong khi `proposed − b7pp` chỉ +0,019 [+0,005; +0,039]. XN8 đo cả khoảng cách giữa một cấu hình phi thời gian và hệ đề xuất, nên không thể dùng nó như ước lượng riêng của đóng góp đồ thị trực tuyến. Đối chiếu các mốc cấu hình cho thấy phần lớn mức tăng quan sát được xuất hiện trước phần mở rộng trực tuyến, tại các hệ có lọc ngày. Tuy nhiên, b7 và b5 còn khác việc mở rộng, nên đây là phân rã mô tả, không phải phép nhận diện nhân quả sạch của riêng bộ lọc.
<!-- nguồn: runs/E3_v1/test/all.score.json -->
<!-- nguồn: src/vilexgraph/framework/systems.py -->

### 6.4.2. Phân rã mô tả test 2 — nhãn LLM, thăm dò

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

## 6.5. E7 do máy — thăm dò

Các bảng sau phân loại toàn bộ dòng sai theo thứ tự ưu tiên đã công bố. ABST dùng cờ khẳng định hiệu lực trong dự đoán; RET-UNIT kiểm sự hiện diện của điều khoản; RET-VER phân biệt hướng cũ/mới khi thiếu gold; GEN-BLANK và GEN-MISREAD chỉ xét sau khi căn cứ đúng đã có trong prompt. Một lỗi chỉ thuộc một tầng, nên đây là cách phân bổ ưu tiên, không chứng minh nguyên nhân nhân quả duy nhất. Cột “chứa bản khác” là tập con của MISREAD, không cộng thêm vào tổng.
<!-- nguồn: scripts/review/e7_error_analysis.py -->

### 6.5.1. v1.0 — thăm dò, do máy phân loại

| Hệ | ABST | RET-UNIT | RET-VER-OLD | RET-VER-NEW | GEN-BLANK | GEN-MISREAD | Chứa bản khác | Tổng sai |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| b7 | 15 | 19 | 2 | 0 | 1 | 39 | 5 | 76 |
| b7pp | 15 | 19 | 0 | 0 | 2 | 41 | 2 | 77 |
| proposed | 15 | 19 | 0 | 0 | 1 | 38 | 2 | 73 |

<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

| Hệ | TV-R@20 | Đúng khi có căn cứ trong prompt |
|---|---|---|
| b7 | 178/211 = 0,844 | 135/178 = 0,758 |
| b7pp | 177/211 = 0,839 | 134/177 = 0,757 |
| proposed | 177/211 = 0,839 | 138/177 = 0,780 |

<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

### 6.5.2. Test 2 — nhãn LLM, thăm dò, do máy phân loại

| Hệ | ABST | RET-UNIT | RET-VER-OLD | RET-VER-NEW | GEN-BLANK | GEN-MISREAD | Chứa bản khác | Tổng sai |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| b7 | 21 | 72 | 14 | 0 | 7 | 43 | 8 | 157 |
| b7pp | 20 | 86 | 0 | 0 | 8 | 41 | 2 | 155 |
| proposed | 19 | 85 | 0 | 0 | 7 | 40 | 1 | 151 |

<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

| Hệ | TV-R@20 | Đúng khi có căn cứ trong prompt |
|---|---|---|
| b7 | 118/227 = 0,520 | 67/118 = 0,568 |
| b7pp | 120/227 = 0,529 | 70/120 = 0,583 |
| proposed | 120/227 = 0,529 | 74/121 = 0,612 |

<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

Trong phân tích thăm dò trên test 2 — nhãn LLM — căn cứ đúng ở top-20 chỉ đạt khoảng 52–53%; khi đã có căn cứ trong prompt, tỷ lệ trả lời đúng vẫn chỉ khoảng 57–61%. Trên v1.0, tỷ lệ có điều kiện tương ứng khoảng 76–78%. Oracle context dev đạt 0,854 (129/151), nhưng khác split, phân bố và điều kiện căn cứ; không dùng các tỷ lệ này để kiểm định chênh lệch với oracle hoặc lấy dev làm cận trên test đã đo. Các tỷ lệ có điều kiện chưa có KTC trong báo cáo E7 hiện tại, nên chỉ là thống kê mô tả.
<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->
<!-- nguồn: runs/B2_dev/dev/all.score.json -->

Phân tích máy cho thấy hai chỗ nghẽn có thể cùng tồn tại: thiếu căn cứ và dùng sai căn cứ đã có. Nó chưa tách được lỗi gold, câu hỏi mơ hồ, đọc sai ngữ nghĩa hay rào đón theo đánh giá của người. Phiếu người gán đã được lấy mẫu có seed; cột hệ và tầng máy được giữ ngoài phiếu người, nối với file máy bằng `stt`. Việc tạo phiếu không đồng nghĩa đã có kết quả E7 do người kiểm.
<!-- nguồn: scripts/review/e7_error_analysis.py -->
<!-- nguồn: data/review/e7/phieu_v1.tsv -->
<!-- nguồn: data/review/e7/phieu_test2.tsv -->

## 6.6. Các phân tích thăm dò khác đã có số

### 6.6.1. v1.0 — thăm dò

XN6 có ước lượng −0,059, KTC 95% [−0,263; +0,191], trên các lát gần giống và thường của T2. XN7 có ước lượng −0,154 [−0,274; −0,051]. Dù khoảng XN7 nằm về một phía, ADR xếp phép đo này là thăm dò; không dùng nó để tự đưa ra phán quyết ủng hộ hoặc bác giả thuyết xác nhận. XN5 chưa có vì thiếu đầu ra sinh của hệ cần so sánh.
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

### 6.6.2. Test 2 — nhãn LLM, thăm dò

XN6 có ước lượng +0,100, KTC 95% [−0,067; +0,278]; XN7 là −0,031 [−0,078; +0,015]. Hai khoảng đều rộng và chứa không. Chúng chỉ mô tả mẫu hiện có, không khẳng định hiệu ứng của độ gần giống hoặc lợi ích riêng ở nhóm bãi bỏ. XN5 vẫn chưa có đầu ra sinh cần thiết.
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

## 6.7. Các phần đang chờ kết quả

### E2: các baseline phẳng còn thiếu

[CHỜ KẾT QUẢ: E2 b2 b3 b4 trên test]

### E4: mở rộng cấu trúc và đối chứng đồ thị bổ sung

[CHỜ KẾT QUẢ: E4 b6 trên test]

[CHỜ KẾT QUẢ: E4 LightRAG trên tập con nếu được thực hiện]

### E5: ablation

[CHỜ KẾT QUẢ: E5 a1 a2 a3 a4 trên test]

### E6: gold độc lập

[CHỜ KẾT QUẢ: E6 trên gold độc lập do người kiểm]

### E7: phân tích người gán

[CHỜ KẾT QUẢ: E7 người gán, độ đồng thuận và ví dụ lỗi đã kiểm]

### Cận trên bằng ngữ cảnh đúng

[CHỜ KẾT QUẢ: oracle context trên test; không thay bằng oracle dev]

## 6.8. Các nguy cơ đối với độ tin cậy

Nhãn v1.0 gồm nguồn người và agent, các cổng đồng thuận không đạt như trình bày ở Chương 4. Test 2 — nhãn LLM — không có lượt xác nhận độc lập của người. Hai bộ cùng dẫn xuất từ một kho phiên bản, còn gold độc lập chưa có và M2 kiểm tay vẫn mở. Vì thế, sự lặp lại của một chiều hiệu ứng trên hai bộ không tự loại được sai lệch chung của nguồn gold và hệ đề xuất.
<!-- nguồn: docs/vilextime-datasheet.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: docs/plans/active/phase-3-kg-l0-l3.md -->

Kết quả chỉ dùng một generator và các cấu hình từ vựng hiện có. Sổ chạy dev ghi 553/553 đầu ra giống nhau ở các prompt trùng giữa các biến thể chạy; điều này không chứng minh mọi phần cứng và thư viện đều cho kết quả giống nhau. Chi phí Colab chưa được đối soát đầy đủ. [CẦN XÁC MINH: cấu hình GPU, phiên bản thư viện và chi phí thực tế của từng lượt từ provenance và biên nhận; không suy từ ước tính trước chạy].
<!-- nguồn: runs/README.md -->
<!-- nguồn: docs/decisions/0004-framework-truy-xuat-va-sinh.md -->
<!-- nguồn: runs/E3_v1/test/proposed.run.json -->

Các cảnh báo ID `asis:event:` không phân giải được phản ánh phạm vi resolver dựa trên lịch sử phiên bản, không trực tiếp đếm thiếu đích vàng. Không biến số cảnh báo thành trần recall hoặc tự thay metric để xử lý một số ít trích dẫn. Bản nháp giữ số chấm hợp lệ đã lưu và công bố giới hạn phân giải.
<!-- nguồn: scripts/eval/score_vilextime.py -->
<!-- nguồn: runs/README.md -->

### 6.8.1. Đối chiếu điều kiện sử dụng từ “cải thiện”

ADR 0005 §6 yêu cầu thêm các điều kiện của MASTER_RESEARCH_GUIDE §8.6 ngoài phán quyết thống kê. Bản nháp vì thế dùng “chênh lệch”, “ước lượng” hoặc phán quyết XN, không gọi một chênh lệch quan sát được là cải thiện đã đáp ứng đầy đủ các điều kiện. Các điều kiện đã kiểm được và phần còn thiếu được phân biệt dưới đây.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: MASTER_RESEARCH_GUIDE.md -->

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
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md -->
<!-- nguồn: runs/E3_v1/test/all.score.json -->
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

Điều kiện không hệ nào vượt oracle trên cùng test **chưa kiểm được**, vì oracle context test chưa có. Oracle context dev chỉ là đối chiếu mô tả; oracle probe tất định của scorer kiểm đường chấm, không phải generator nhận căn cứ gold trên test. Các điều kiện của §8.6 vì thế chưa đồng thời hoàn tất, dù các phán quyết ủng hộ đã báo trong họ XN vẫn giữ nguyên.
<!-- nguồn: docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md -->
<!-- nguồn: runs/README.md -->
<!-- nguồn: scripts/eval/score_vilextime.py -->

## 6.9. Câu trả lời có bằng chứng và hai nhánh M4

Đối với RQ1, XN9 ủng hộ giá trị của truy xuất trong cấu hình hiện tại, nhưng baseline không truy xuất hầu như không trả lời; đây là giới hạn trực tiếp của sức khái quát. Đối với RQ2, XN8 ủng hộ chênh lệch giữa hệ đề xuất và đối chứng phi thời gian, nhưng phân rã thăm dò không cho phép quy toàn bộ mức tăng cho đồ thị. Đối với RQ3, XN3 ủng hộ giá trị bộ lọc cấp văn bản; bằng chứng bổ sung của chuỗi phiên bản có trên v1.0 nhưng chưa được xác nhận lại đầy đủ trên test 2 — nhãn LLM.
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->
<!-- nguồn: runs/E3_v1/test/all.score.json -->
<!-- nguồn: runs/E3_test2/rescore/all.score.json -->

M4 chưa được nhóm chốt. Trên bảng chính v1.0, H0 được ủng hộ; trên bản lặp lại test 2 — nhãn LLM — ADR dẫn đến nhánh “điểm quyết định B7”, một kết quả đã khai báo trước, không phải thất bại. Nhánh đóng góp phương pháp có thể dựa vào kết quả XN1 cùng XN2 ủng hộ trên v1.0, nhưng phải công bố giới hạn gold và sự không lặp lại đầy đủ ở test 2 — nhãn LLM. Nhánh tài nguyên–phân tích có căn cứ từ XN1 không đủ bằng chứng trên test 2 — nhãn LLM — và từ vai trò lớn của phép đối chứng lọc ngày. Bản nháp trình bày cả hai nhánh; không lựa chọn thay nhóm, không đổi lời kết luận thống kê để làm phù hợp một nhánh mong muốn.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: docs/plans/active/master-plan.md -->
<!-- nguồn: runs/E3_v1/test/confirm.json -->
<!-- nguồn: runs/E3_test2/rescore/confirm.json -->

## Việc còn thiếu trước khi nộp

- Bổ sung đúng các phần đánh dấu chờ khi có kết quả, giữ nguyên khoảng tin cậy và trạng thái thăm dò.
- Hoàn tất E7 người gán và E6, hoặc nêu rõ chưa hoàn tất trong giới hạn của khóa luận.
- Nhóm quyết định M4 và sửa phần đóng góp sau quyết định đó; không sửa kết quả đã quan sát.
- Đối soát chi phí, topology GPU và phần mềm; chưa tự suy chi phí từ thời gian chạy.
- Kiểm liên kết nguồn sau khi chuyển sang mẫu trình bày chính thức, bảo đảm mọi bảng test 2 đều ghi nhãn LLM.
