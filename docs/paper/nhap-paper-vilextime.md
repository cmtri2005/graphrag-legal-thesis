# ViLexTime: Bộ đánh giá hỏi đáp pháp luật tiếng Việt theo mốc thời gian và phép đo vai trò của biểu diễn phiên bản

*Tên tiếng Anh tạm: ViLexTime: A Point-in-Time Benchmark for Vietnamese Legal QA and a Controlled Ladder of Temporal Representations*

**Bản nháp ngày 05/11/2026, để xem hiện trạng. Chưa phải bản nộp, chưa có người duyệt.**

---

# Phần A. Hiện trạng trong một trang

**Kết luận: chưa nộp được, nhưng đã có khung bài rõ.** Phần số liệu chính đã có và được khai báo trước. Ba chỗ chặn nộp là: gold phụ thuộc chính kho dữ liệu của hệ, thiếu baseline, và tổng quan tài liệu chưa đọc đủ.

| Phần của paper | Mức sẵn sàng | Còn thiếu |
|---|---|---|
| Câu hỏi nghiên cứu, kế hoạch phân tích | Đủ | Khai báo trong git nội bộ, không phải đăng ký công khai |
| Kiểm định chính (E1, E3) | Đủ trong phạm vi đã chạy | XN5 chưa có; còn thiếu `b7plus`, `b7v` có sinh câu trả lời và các hệ của E2, E4, E5 |
| Kho văn bản, chuỗi phiên bản | Một phần | M2 chưa đạt (100 truy vấn đối chiếu tay); recall sự kiện lịch sử 62,2% |
| ViLexTime v1.0 | Một phần | Đồng thuận người gán thấp; gold độc lập 0/75 |
| Test 2 | Yếu | Nhãn LLM, chưa có người kiểm, chưa có số đo so với người |
| Baseline | Thiếu | `b2 b3 b4 b6` chưa chạy trên test; chưa có GraphRAG bên ngoài |
| Ablation, oracle context | Thiếu | Chờ Colab đợt 2 (v1.0) và lần chạy cuối (G4 của master plan) |
| Phân rã lỗi | Một phần | Mới do máy phân loại; phiếu E7 chưa có người gán |
| Tổng quan tài liệu | Yếu | 14/18 nguồn gần nhất chỉ mới đối chiếu metadata; chưa có lượt khảo sát tính mới |
| Khai báo (dữ liệu, đạo đức, AI, tác giả) | Một phần | Xem cuối Phần B |
| Hội nghị | Chưa chọn | GVHD chọn; quy định ẩn danh ảnh hưởng việc công khai repo |

**Ba hướng paper có thể đi:**

| Hướng | Luận điểm | Số hiện có | Nhận định |
|---|---|---|---|
| **A. Bộ đánh giá và phép đo** (bản nháp này) | Đo được lỗi sai phiên bản; lọc thời gian ở từng cấp đóng góp gì | Đỡ được, có lặp lại một phần | Khả thi nhất. Cần gold độc lập |
| B. Phương pháp đề xuất | Hệ `proposed` tốt hơn hẳn | Yếu: `proposed` − `b7pp` chỉ +0,019 [+0,005; +0,039] trên v1.0 và khoảng chứa 0 trên test 2 (nhãn LLM); Verifier không tác động ở đường chạy batch. Điểm sáng duy nhất là T2 (mục 7), mới ở mức thăm dò | Không khuyên lúc này |
| C. Giới hạn của LLM gán nhãn | Hai LLM cộng hòa giải chưa đạt mức của người | Mẫu nhỏ (68 câu) | Nên là một mục con, chưa đủ thành bài |

Bản nháp giả định hướng A. Đây là giả định để viết, **M4 chưa được nhóm chốt**. Ký hiệu `[CHỜ: …]` là số chưa có, `[CẦN: …]` là việc phải làm trước khi nộp. Bài viết bằng tiếng Việt để dễ đọc, sẽ dịch khi chốt hội nghị.

---

# Phần B. Bản nháp paper

## Tóm tắt

Hệ RAG pháp luật có thể lấy đúng điều khoản nhưng sai phiên bản tại ngày được hỏi. Chúng tôi trình bày ViLexTime, bộ đánh giá hỏi đáp theo cặp câu hỏi và mốc thời gian trên văn bản quy phạm pháp luật Việt Nam, chấm bằng phép tương phản giữa các phiên bản. Trên kho 17.333 văn bản, chúng tôi so sánh một thang cấu hình: không lọc thời gian, lọc theo ngày văn bản, lọc theo phiên bản, lan truyền hiệu lực, và mở rộng quan hệ một bước. Kế hoạch phân tích được khóa trước khi chạy test. Trên v1.0 (211 dòng, 165 lineage), cả sáu kiểm định xác nhận đều được ủng hộ. So với lọc theo ngày văn bản, cấu hình lớp phiên bản có lan truyền hiệu lực chênh -0,133 [-0,179; -0,090] về tỷ lệ trích dẫn vi phạm hiệu lực. Trên bộ lặp lại (227 dòng, 101 lineage, nhãn LLM chưa có người kiểm), bốn kiểm định được ủng hộ, còn hai kiểm định về truy xuất theo phiên bản không đủ bằng chứng. Phân rã mô tả cho thấy phần lớn chênh lệch Accuracy đã xuất hiện ở bước lọc theo ngày văn bản; lớp phiên bản chủ yếu giảm trích dẫn vi phạm hiệu lực; mở rộng một bước thêm rất ít trên toàn tập. Không hệ nào nhận ra đáng tin cậy điều khoản đã bị bãi bỏ. Giới hạn chính là gold dẫn xuất từ cùng kho với hệ được đánh giá, đồng thuận người gán thấp, và chỉ có một generator.

**Từ khóa:** RAG pháp luật, truy xuất theo thời gian, phiên bản văn bản, bộ đánh giá, tiếng Việt.

## 1. Giới thiệu

Văn bản pháp luật thay đổi theo thời gian. Câu hỏi "mức phạt là bao nhiêu" có đáp án khác nhau tùy ngày hỏi. Một hệ RAG thông thường xếp hạng theo mức liên quan, nên có thể trả về lời văn đúng chủ đề nhưng đã hết hiệu lực. FiscalQA Pro đã đặt vấn đề này thành đối tượng đánh giá với luật thuế Pháp [@cymbler2026fiscalqa]. Với pháp luật Việt Nam, các tài nguyên chúng tôi đã đọc tập trung vào truy xuất điều luật và hỏi đáp nhiều bước [@nguyen2025vlqa; @nguyen2026vihermes]; chúng tôi chưa khảo sát đủ để nói không có công trình tương tự. [CẦN: lượt khảo sát có ghi truy vấn, ngày, nguồn đã mở và nguồn không mở được]

Một câu hỏi chưa rõ là lợi ích đến từ đâu. Nếu một bộ lọc theo ngày văn bản đã đủ tốt, việc dựng đồ thị phiên bản khó được biện minh. Bài này đo trực tiếp điều đó, qua ba câu hỏi:

- **RQ1.** LLM và RAG hiện có mắc lỗi áp dụng sai phiên bản ở mức nào trên pháp luật Việt Nam?
- **RQ2.** Biểu diễn theo phiên bản có giảm lỗi so với RAG phẳng và đồ thị phi thời gian không?
- **RQ3.** Lợi ích đến từ biểu diễn phiên bản hay chỉ từ lọc theo siêu dữ liệu thời gian?

**Đóng góp, kèm điều không khẳng định:**

1. **Bộ đánh giá ViLexTime** gồm 769 dòng chính, có danh tính điều khoản, phiên bản gold và đáp án ngắn để chấm tương phản. *Không khẳng định đây là chuẩn vàng pháp lý, hay là bộ đầu tiên.*
2. **Một phép đo có đối chứng** theo thang cấu hình, với kế hoạch khóa trước và một bộ lặp lại. *Chỉ các nấc kề nhau đổi một thành phần; các so sánh xa hơn không tách được hiệu ứng riêng.*
3. **Phân tích thất bại:** nhận diện bãi bỏ gần như không có, và hai điểm nghẽn ở khâu tìm và khâu đọc căn cứ. *Phân loại lỗi hiện do máy, chưa có người kiểm.*
4. **Một số đo về LLM gán nhãn:** quy trình hai LLM cộng hòa giải chưa đạt cổng khi so với nhãn người. *Chỉ trên 68 câu, chủ yếu đo được ở nhóm bãi bỏ.*

## 2. Công trình liên quan

**Hỏi đáp pháp luật theo thời gian.** FiscalQA Pro phân biệt chỉ mục chỉ có bản hiện hành với chỉ mục nhiều phiên bản điều kiện theo ngày, và chấm bằng nugget tất định [@cymbler2026fiscalqa]. Điều kiện RAG tĩnh của bài đó được cấp sẵn điều luật gold, khác với bài toán tự tìm trên toàn kho của chúng tôi. VersionRAG [@huwiler2025versionrag] và công trình về lỗi thời gian trong hỏi đáp luật định [@prior2026oldfriend] là hai ứng viên đối chiếu trực tiếp. [CẦN: đọc bản gốc trước khi mô tả; hiện mới có metadata]

**Mô hình hóa phiên bản.** SAT-Graph RAG mô hình hóa cấu trúc và thời gian của quy phạm, kèm chính sách truy vấn tất định, ở dạng case study định tính [@demartim2025satgraph]. Nghiên cứu về rủi ro của hợp nhất văn bản tự động liên quan trực tiếp đến chất lượng lời văn dẫn xuất của chúng tôi [@prior2025consolidation]. [CẦN: đọc bản gốc]

**Tài nguyên tiếng Việt.** VLQA xây bộ hỏi đáp tư vấn có chuyên gia kiểm và loại điều khoản đã bãi bỏ [@nguyen2025vlqa]. ViHERMES dùng đồ thị cho hỏi đáp nhiều bước về quy định y tế [@nguyen2026vihermes]. Chúng tôi không so điểm với các bài này vì tác vụ và mẫu số khác nhau.

**GraphRAG.** Bài này không chạy GraphRAG [@edge2024graphrag] hay LightRAG [@guo2025lightrag]. Mở rộng của chúng tôi chỉ là lấy láng giềng một bước, nên kết quả **không phải** phép đánh giá các hệ đó. [CẦN: đọc bản gốc trước khi mô tả] [CHỜ: E4 LightRAG trên tập con, nếu chạy]

## 3. Dữ liệu

### 3.1. Kho văn bản và chuỗi phiên bản

Dữ liệu thu thập từ vbpl.vn. Pipeline nhận dạng câu lệnh sửa đổi và bãi bỏ, phân giải điều khoản đích, rồi dựng chuỗi phiên bản với khoảng hiệu lực nửa mở. Khoảng hiệu lực thực của một phiên bản là giao của khoảng cục bộ với độ phủ của các nút tổ tiên và văn bản sở hữu. Kho thực nghiệm gồm 17.333 văn bản, 1.455.372 đơn vị lời văn gốc (lớp A), 53.991 đơn vị lệnh (lớp A) và 1.477.089 đơn vị phiên bản (lớp B).

Kiểm chất lượng lịch sử ghi 58/60 sự kiện áp đúng (Wilson 95% từ 88,6% đến 99,1%), recall theo `expiryProvisions` 62,2%, và 5.762/7.201 cặp lời văn (80,02%) khớp chính xác với văn bản hợp nhất trên 51 văn bản. Ba số này khác mẫu số, không gộp thành một độ chính xác chung. [CẦN: M2, 100 truy vấn đối chiếu tay; đo lại sau các bước mở rộng]

### 3.2. ViLexTime v1.0

Một dòng là một cặp câu hỏi và mốc. Các dòng cùng lineage dùng chung điều khoản và câu hỏi, nên lineage là đơn vị độc lập khi phân tích. LLM viết câu hỏi, sau đó qua bộ kiểm tự động và bước kiểm nhãn. Dev và test tách theo văn bản đích. Bảng chính dùng mốc giữa khoảng hiệu lực, để ngày hỏi không tự gợi ra văn bản vừa có hiệu lực.

**Bảng 1. ViLexTime v1.0, split test, giữa khoảng**

| Nhóm | Hiện tượng | Dòng | Lineage |
|---|---|---:|---:|
| T1 | Điều khoản một phiên bản (đối chứng) | 123 | 123 |
| T2 | Hai đáp án khác nhau | 46 | 23 |
| T3 | Từ ba đáp án khác nhau | 12 | 4 |
| T6 | Điều khoản đã bị bãi bỏ | 30 | 15 |
| Tổng | | 211 | 165 |

**Nguồn nhãn.** Trên 211 dòng ranh giới của test: 88 dòng do A và B cùng nhãn, 33 dòng do luật sư chốt (trong đó 10 dòng có phiếu Claude hỗ trợ), 90 dòng do agent gán. Nhãn agent chỉ được dùng ở T1 và T6; T2 và T3 của test đều có nguồn người.

**Đồng thuận thấp, và phải nói rõ.** Trên 246 dòng gán đôi theo hướng dẫn hiện hành: AC1 0,377 [0,250; 0,496], κ 0,235, thỏa thuận nhãn âm 0,395. Theo nhóm, AC1 của T1 là 0,878 (n=40), T2 0,269 (n=106), T3 0,378 (n=30), T6 0,216 (n=70). AC1 được chọn sau pilot, không khai báo trước [@gwet2008ac1]. Agent đạt AC1 0,721 và p_neg 0,610 trên 178 dòng hiệu chuẩn, không đạt ngưỡng AC1 0,80. Luật sư kiểm 50 dòng nhãn agent và đồng ý 43.

**T6 bị thu hẹp mạnh.** Hơn một trăm lineage bị loại vì không chắc nội dung có chuyển sang văn bản khác không (108 lineage `relocation_unclear`, 25 lineage `relocated`). Vì thế T6 không đại diện cho mọi điều khoản từng bị bãi bỏ.

### 3.3. Test 2 (nhãn LLM)

Test 2 là bộ lặp lại, gồm T2, T3 và T6, **nhãn do LLM gán, không có người hay luật sư kiểm**. Nó được báo riêng và không gộp với v1.0. Câu hỏi bị giới hạn trùng chữ với lời văn ở mức tối đa 40%.

**Bảng 2. Test 2 (nhãn LLM), giữa khoảng**

| Nhóm | Dòng | Lineage |
|---|---:|---:|
| T2 | 120 | 60 |
| T3 | 75 | 25 |
| T6 | 32 | 16 |
| Tổng | 227 | 101 |

**Quy trình nhãn.** Sonnet 5.5 và Codex gán độc lập 138 câu, lệch ở 53 câu và Opus 5.5 hòa giải; sáu câu phân vân được agent tra luật kiểm lại, trong đó 4 câu đổi nhãn. Giữa hai LLM: AC1 của Q1, Q2, Q3 là 0,907, 0,884, 0,766, nhưng thỏa thuận nhãn âm chỉ 0,476, 0,222, 0,133. Cổng đồng thuận không đạt.

**Giới hạn của lời dặn.** Rà soát sau đó cho thấy lời dặn gán nhãn chỉ gồm thẻ viết cho người cộng vài dòng; thiếu các định nghĩa thẻ trỏ tới; có thêm chỉ dẫn "phải khắt khe" (hai model loại 45 và 24 câu); model chỉ đọc đoạn trích nên Q4 = Không phần lớn nghĩa là "không thấy trong phần được đưa". Lời dặn bản 1 không qua bước hiệu chuẩn nào.

**Lời dặn bản 2 không đạt cổng.** Chúng tôi viết bản 2 đầy đủ hơn và khai báo trước cổng: so với 68 câu có nhãn người độc lập, nhãn cuối phải đạt AC1 ≥ 0,80 và p_neg ≥ 0,60. Kết quả: AC1 0,530, p_neg 0,758, **không đạt**. Quy trình bắt 25/29 câu xấu và loại nhầm 12/39 câu tốt. Trong 29 câu xấu có 25 câu ở T6, nên cổng gần như không đo được T2 và T3. Theo khai báo, chúng tôi dừng: không gán test 2 (nhãn LLM) bằng bản 2 và không có phân tích độ nhạy. Do đó, **chưa có số đo nào cho biết bộ nhãn LLM này khớp với người đến đâu**. [CẦN: người kiểm một mẫu của bộ này]

**Một lần chấm sai đã công bố.** Lần chấm E3 đầu của bộ này sai vì release thiếu đáp án ngắn, trong khi phép kiểm chứa coi đáp án rỗng là đúng. Lỗi được khai báo, release được sửa, các câu trả lời cũ được chấm lại một lần và không sinh lại. Bộ chấm nay từ chối dòng thiếu đáp án ngắn. Mọi số của bộ này trong bài là số sau khi sửa.

### 3.4. Mức trùng chữ của câu hỏi

Dùng cùng một hàm đo, tỷ lệ tiếng có nghĩa của câu hỏi nằm trong lời văn có trung vị **0,652** ở test v1.0, với 13,9% lineage không quá 40%. Ở test 2 (nhãn LLM), trung vị là **0,321**, 100% lineage không quá 40%. Hai bộ khác nhau rõ về mức câu hỏi giống lời văn.

## 4. Các hệ so sánh

Thang chính giữ cố định truy xuất từ vựng (SQLite FTS5, k = 20), prompt và generator. Mỗi nấc kề nhau đổi một thành phần.

**Bảng 3. Cấu hình**

| Hệ | Lớp | Bộ lọc thời gian | Mở rộng | Verifier | Đo ở |
|---|---|---|---|---|---|
| `b1` | Không truy xuất | Không | Không | Tắt | E3 |
| `b2ctx` | A | Không | Không | Tắt | E1, E3 |
| `b5` | A | Không | Lệnh, một bước | Tắt | E3 |
| `b7` | A | Ngày văn bản | Không | Tắt | E1, E3 |
| `b7v` | B | Ngày văn bản | Không | Tắt | E1 |
| `b7plus` | B | Phiên bản | Không | Tắt | E1 |
| `b7pp` | B | Lan truyền | Không | Tắt | E1, E3 |
| `proposed` | B | Lan truyền | Lệnh, một bước | reject | E3 |

**Phạm vi của "đồ thị".** Đồ thị phiên bản chủ yếu làm việc ngoại tuyến: dựng chuỗi và tính khoảng hiệu lực. Trong lúc trả lời, mở rộng chỉ là lấy láng giềng một bước bằng truy vấn SQL (5 seed, fanout 3), không tìm đường nhiều bước và không có tóm tắt cộng đồng. Ở đường nhập batch dùng cho E3, Verifier chỉ kiểm ID trích dẫn và không sinh lại, nên chúng tôi không gán tác dụng nào cho nó.

**Generator.** Qwen/Qwen3-4B-Instruct-2507, revision `cdbee75`, NF4, greedy, tối đa 512 token mới. Generator nhận mốc, câu hỏi và các đoạn căn cứ, rồi trả lời theo ba dòng: lời văn, hiệu lực (`còn`, `không`, `không rõ`), và nhãn căn cứ. Chỉ `không` được hiểu là khẳng định hết hiệu lực; `không rõ` không được tính là nhận ra bãi bỏ.

## 5. Thiết kế thực nghiệm

**Khai báo trước.** ADR 0005 khóa giả thuyết, đại lượng, lát dữ liệu, chiều dự đoán và quy tắc kết luận trước khi chạy test. Mỗi cấu hình chỉ chạy một lần trên test. Mọi thay đổi sau đó ghi thành amendment, nói rõ lúc đó đã thấy kết quả nào. Đây là khai báo trong git, không phải đăng ký công khai.

**Chỉ số.** *Accuracy* là phép chấm tương phản: câu trả lời phải chứa các đoạn gold và tránh đoạn chỉ thuộc phiên bản khác; dòng bãi bỏ chỉ đúng khi hệ khẳng định hết hiệu lực. *TV-Recall@k* cần đúng phiên bản; *Recall@k* chỉ cần đúng điều khoản. *TVER* là tỷ lệ dòng có ít nhất một trích dẫn không có hiệu lực tại mốc, tính trên các dòng có trích dẫn phân giải được, nên luôn đọc cùng độ phủ trích dẫn. *wrong_version* xét nội dung câu trả lời có chứa đoạn chỉ phiên bản khác có, trên các dòng có đoạn phân biệt. Chưa dùng LLM làm giám khảo. [CẦN: quyết định có hiệu chuẩn LLM-as-judge không]

**Thống kê.** Bootstrap theo cụm lineage, 10.000 lần lấy mẫu lại, khoảng phân vị 95%. Họ xác nhận gồm sáu kiểm định với hiệu chỉnh Holm, α = 0,05 [@dror2018hitchhiker]. "Ủng hộ" cần p sau Holm < 0,05 và đúng chiều dự đoán; ngược chiều là "bác"; còn lại là "không đủ bằng chứng". XN5, XN6, XN7 chỉ thăm dò vì lát quá nhỏ. Mọi so sánh ngoài họ đều là mô tả.

## 6. Kết quả

Hai bộ được báo ở hai bảng riêng theo khai báo. Số trong các bảng đã làm tròn ba chữ số.

### 6.1. Truy xuất theo thang (E1)

**Bảng 4. TV-Recall@1 và Recall@1, v1.0**

| Hệ | TV-R@1 | R@1 |
|---|---:|---:|
| `b2ctx` | 0,289 | 0,374 |
| `b7` | 0,417 | 0,483 |
| `b7v` | 0,398 | 0,521 |
| `b7plus` | 0,464 | 0,493 |
| `b7pp` | 0,464 | 0,464 |

**Bảng 5. TV-Recall@1 và Recall@1, test 2 (nhãn LLM)**

| Hệ | TV-R@1 | R@1 |
|---|---:|---:|
| `b2ctx` | 0,070 | 0,154 |
| `b7` | 0,115 | 0,176 |
| `b7v` | 0,070 | 0,159 |
| `b7plus` | 0,141 | 0,141 |
| `b7pp` | 0,141 | 0,141 |

Ba điều lặp lại về chiều trên cả hai bộ (mô tả, ngoài họ):

- Riêng đưa lời văn đã hợp nhất vào (`b7v` − `b7`) không tăng TV-R@1: -0,019 [-0,046; +0,005] trên v1.0 và -0,044 [-0,074; -0,017] trên test 2 (nhãn LLM).
- Bước lọc theo phiên bản (`b7plus` − `b7v`) có khoảng không chứa 0: +0,066 [+0,034; +0,101] và +0,070 [+0,036; +0,109].
- Lan truyền hiệu lực (`b7pp` − `b7plus`) không thay đổi TV-R@1 ở cả hai bộ: +0,000 [+0,000; +0,000] và +0,000 [+0,000; +0,000].

### 6.2. Câu trả lời (E3)

**Bảng 6. v1.0, 211 dòng**

| Hệ | Accuracy | TVER | wrong_version | Phủ trích dẫn |
|---|---|---|---|---:|
| `b1` | 0,000 [0,000; 0,000] | — | 0,000 [0,000; 0,000] | 0,000 |
| `b2ctx` | 0,474 [0,408; 0,543] | 0,471 [0,401; 0,538] | 0,291 [0,184; 0,400] | 0,995 |
| `b5` | 0,479 [0,413; 0,547] | 0,471 [0,401; 0,538] | 0,291 [0,184; 0,400] | 0,995 |
| `b7` | 0,640 [0,572; 0,706] | 0,133 [0,090; 0,177] | 0,109 [0,037; 0,196] | 0,995 |
| `b7pp` | 0,635 [0,564; 0,706] | 0,000 [0,000; 0,000] | 0,036 [0,000; 0,091] | 0,995 |
| `proposed` | 0,654 [0,585; 0,721] | 0,005 [0,000; 0,015] | 0,036 [0,000; 0,091] | 0,991 |

**Bảng 7. Test 2 (nhãn LLM), 227 dòng**

| Hệ | Accuracy | TVER | wrong_version | Phủ trích dẫn |
|---|---|---|---|---:|
| `b1` | 0,000 [0,000; 0,000] | — | 0,000 [0,000; 0,000] | 0,000 |
| `b2ctx` | 0,150 [0,108; 0,195] | 0,682 [0,611; 0,748] | 0,210 [0,151; 0,273] | 0,982 |
| `b5` | 0,150 [0,110; 0,193] | 0,709 [0,640; 0,774] | 0,215 [0,157; 0,278] | 0,982 |
| `b7` | 0,308 [0,242; 0,379] | 0,219 [0,166; 0,273] | 0,077 [0,039; 0,119] | 0,987 |
| `b7pp` | 0,317 [0,241; 0,396] | 0,000 [0,000; 0,000] | 0,010 [0,000; 0,026] | 0,987 |
| `proposed` | 0,335 [0,262; 0,411] | 0,013 [0,000; 0,031] | 0,005 [0,000; 0,016] | 0,987 |

**Bảng 8. Accuracy theo nhóm, v1.0** (T3 chỉ có 4 lineage)

| Hệ | T1 | T2 | T3 | T6 |
|---|---:|---:|---:|---:|
| `b5` | 0,634 | 0,304 | 0,083 | 0,267 |
| `b7` | 0,724 | 0,609 | 0,583 | 0,367 |
| `b7pp` | 0,699 | 0,674 | 0,583 | 0,333 |
| `proposed` | 0,699 | 0,761 | 0,583 | 0,333 |

**Bảng 9. Accuracy theo nhóm, test 2 (nhãn LLM)**

| Hệ | T2 | T3 | T6 |
|---|---:|---:|---:|
| `b5` | 0,175 | 0,093 | 0,188 |
| `b7` | 0,350 | 0,253 | 0,281 |
| `b7pp` | 0,325 | 0,320 | 0,281 |
| `proposed` | 0,392 | 0,267 | 0,281 |

### 6.3. Kiểm định xác nhận

**Bảng 10. v1.0**

| Mã | So sánh, đại lượng | Ước lượng [KTC 95%] | p Holm | Dòng/lineage | Kết luận |
|---|---|---|---:|---|---|
| XN1 | `b7pp` − `b7`, TV-R@1 | +0,051 [+0,021; +0,088] | 0,0008 | 196/165 | ủng hộ |
| XN2 | `b7pp` − `b7`, TVER | -0,133 [-0,179; -0,090] | < 0,0001 | 211/165 | ủng hộ |
| XN3 | `b7` − `b2ctx`, TV-R@1 | +0,138 [+0,089; +0,191] | < 0,0001 | 196/165 | ủng hộ |
| XN4 | `b7plus` − `b7`, TV-R@1 | +0,051 [+0,020; +0,087] | 0,0008 | 196/165 | ủng hộ |
| XN8 | `proposed` − `b5`, Accuracy | +0,175 [+0,115; +0,234] | < 0,0001 | 211/165 | ủng hộ |
| XN9 | `b2ctx` − `b1`, Accuracy | +0,474 [+0,409; +0,542] | < 0,0001 | 211/165 | ủng hộ |

**Bảng 11. Test 2 (nhãn LLM)**

| Mã | So sánh, đại lượng | Ước lượng [KTC 95%] | p Holm | Dòng/lineage | Kết luận |
|---|---|---|---:|---|---|
| XN1 | `b7pp` − `b7`, TV-R@1 | +0,028 [-0,014; +0,072] | 0,4596 | 211/101 | không đủ bằng chứng |
| XN2 | `b7pp` − `b7`, TVER | -0,219 [-0,273; -0,165] | < 0,0001 | 227/101 | ủng hộ |
| XN3 | `b7` − `b2ctx`, TV-R@1 | +0,047 [+0,023; +0,078] | < 0,0001 | 211/101 | ủng hộ |
| XN4 | `b7plus` − `b7`, TV-R@1 | +0,028 [-0,014; +0,072] | 0,4596 | 211/101 | không đủ bằng chứng |
| XN8 | `proposed` − `b5`, Accuracy | +0,185 [+0,127; +0,246] | < 0,0001 | 227/101 | ủng hộ |
| XN9 | `b2ctx` − `b1`, Accuracy | +0,150 [+0,109; +0,195] | < 0,0001 | 227/101 | ủng hộ |

Theo quy tắc khai báo: H0 được ủng hộ trên v1.0. Trên test 2 (nhãn LLM), XN1 không được ủng hộ nên đi vào nhánh "điểm quyết định B7", một kết quả đã khai báo trước. XN2, XN3, XN8, XN9 cùng chiều và cùng được ủng hộ ở cả hai bộ. XN1 và XN4 cùng chiều nhưng trên test 2 (nhãn LLM) không đủ bằng chứng, nên **không gọi là đã lặp lại**.

XN5 (lan truyền trên T6 có nút cha bị bãi bỏ) chưa có. [CHỜ: `b7plus` có sinh câu trả lời trên hai bộ]

### 6.4. Chênh lệch đến từ đâu (mô tả, ngoài họ)

**Bảng 12. v1.0**

| Bước | Accuracy | TVER | wrong_version |
|---|---|---|---|
| `b5` − `b2ctx` (thêm mở rộng, không có thời gian) | +0,005 [+0,000; +0,015] | +0,000 [+0,000; +0,000] | +0,000 [+0,000; +0,000] |
| `b7` − `b5` (thêm lọc ngày văn bản, bỏ mở rộng) | +0,161 [+0,104; +0,217] | -0,338 [-0,405; -0,270] | -0,182 [-0,309; -0,053] |
| `b7pp` − `b7` (sang lớp phiên bản, lọc lan truyền) | -0,005 [-0,033; +0,023] | -0,133 [-0,177; -0,090] | -0,073 [-0,167; +0,000] |
| `proposed` − `b7pp` (thêm mở rộng và Verifier) | +0,019 [+0,005; +0,039] | +0,005 [+0,000; +0,015] | +0,000 [+0,000; +0,000] |

**Bảng 13. Test 2 (nhãn LLM)**

| Bước | Accuracy | TVER | wrong_version |
|---|---|---|---|
| `b5` − `b2ctx` | +0,000 [-0,013; +0,013] | +0,027 [+0,005; +0,054] | +0,005 [+0,000; +0,016] |
| `b7` − `b5` | +0,159 [+0,107; +0,212] | -0,490 [-0,563; -0,417] | -0,138 [-0,203; -0,075] |
| `b7pp` − `b7` | +0,009 [-0,036; +0,055] | -0,219 [-0,273; -0,166] | -0,067 [-0,108; -0,031] |
| `proposed` − `b7pp` | +0,018 [-0,026; +0,058] | +0,013 [+0,000; +0,031] | -0,005 [-0,024; +0,011] |

Trên cả hai bộ, Accuracy tăng chủ yếu ở bước `b7` − `b5`. Bước `b7pp` − `b7` có khoảng Accuracy chứa 0, nhưng TVER giảm rõ. `b7` và `b5` còn khác nhau ở việc mở rộng, nên đây là phân rã mô tả, không phải nhận diện nhân quả của riêng bộ lọc. [CHỜ: ablation `a1 a2 a3 a4`]

### 6.5. Những thất bại cần nêu thẳng

**Nhận diện bãi bỏ.** Trên v1.0, mọi hệ đều đúng 0/15 dòng bãi bỏ. Trên test 2 (nhãn LLM), mỗi hệ đúng 0 đến 1 trên 16 dòng. TVER gần 0 của `b7pp` không mâu thuẫn với điều này: không trích bản hết hiệu lực khác với biết rằng quy định đã hết hiệu lực.

**Baseline không truy xuất.** `b1` để trống 182/196 câu có đáp án trên v1.0 và 208/211 trên test 2 (nhãn LLM). Vì vậy XN9 chủ yếu cho thấy generator này gần như không trả lời khi không có căn cứ, không phải LLM nói chung kém.

### 6.6. Phân rã lỗi do máy (thăm dò)

**Bảng 14. v1.0**

| Hệ | Có căn cứ đúng trong top 20 | Đúng khi prompt đã có căn cứ | Sai tổng | Bãi bỏ | Thiếu điều khoản | Đọc sai |
|---|---|---|---:|---:|---:|---:|
| `b7` | 178/211 = 0,844 | 135/178 = 0,758 | 76 | 15 | 19 | 39 |
| `b7pp` | 177/211 = 0,839 | 134/177 = 0,757 | 77 | 15 | 19 | 41 |
| `proposed` | 177/211 = 0,839 | 138/177 = 0,780 | 73 | 15 | 19 | 38 |

**Bảng 15. Test 2 (nhãn LLM)**

| Hệ | Có căn cứ đúng trong top 20 | Đúng khi prompt đã có căn cứ | Sai tổng | Bãi bỏ | Thiếu điều khoản | Đọc sai |
|---|---|---|---:|---:|---:|---:|
| `b7` | 118/227 = 0,520 | 67/118 = 0,568 | 157 | 21 | 72 | 43 |
| `b7pp` | 120/227 = 0,529 | 70/120 = 0,583 | 155 | 20 | 86 | 41 |
| `proposed` | 120/227 = 0,529 | 74/121 = 0,612 | 151 | 19 | 85 | 40 |

Mỗi lỗi chỉ vào một tầng theo thứ tự ưu tiên, nên đây là phân bổ, không phải nguyên nhân duy nhất. Ở v1.0, lỗi lớn nhất là đọc sai khi đã có căn cứ. Ở test 2 (nhãn LLM), lỗi lớn nhất là không tìm được điều khoản. [CHỜ: E7 người gán]

## 7. Thảo luận

**Lọc theo thời gian là phần đáng giá nhất đã đo được.** Trên cả hai bộ, đưa ràng buộc thời gian vào truy xuất đi cùng chênh lệch Accuracy lớn nhất. Bản thân bộ lọc cấp văn bản đơn giản đã nằm rất gần đỉnh thang về Accuracy. Về thực dụng, đây là bước rẻ nên làm trước.

**Biểu diễn phiên bản có giá trị riêng, nhưng ở chỉ số khác.** Trên toàn tập, bước `b7pp` − `b7` không tách được về Accuracy, song TVER giảm rõ trên cả hai bộ. TVER gần 0 một phần là **do thiết kế**, vì bộ lọc đã loại bản hết hiệu lực, nên nó không nên là con số chính. wrong_version đo nội dung câu trả lời nên có ý nghĩa hơn. Nó giảm rõ trên test 2 (nhãn LLM), còn trên v1.0 khoảng tin cậy chạm 0, mẫu số chỉ 55 dòng, và chỉ số này nằm ngoài họ kiểm định.

**Toàn tập có thể che bớt tác dụng ở nhóm nhạy thời gian.** T1 là nhóm đối chứng, chiếm 123/211 dòng của test v1.0, và lớp phiên bản không có lợi ở đó (`b7` 0,724, `b7pp` 0,699). Riêng ở T2, hiệu `proposed` − `b7pp` có khoảng không chứa 0 trên cả hai bộ: +0,087 [+0,022; +0,174] trên v1.0 và +0,067 [+0,017; +0,117] trên test 2 (nhãn LLM). Đây là **dấu hiệu có lợi duy nhất cho mở rộng một bước**, và là hướng đáng đo tiếp nhất. Tuy nhiên, đây là so sánh thăm dò, ngoài họ kiểm định, được chọn sau khi thấy số và chưa hiệu chỉnh đa so sánh. Ở T3, hiệu này là +0,000 [+0,000; +0,000] trên v1.0 và -0,053 [-0,147; +0,027] trên test 2 (nhãn LLM). Hiệu `b7pp` − `b7` ở T2 cũng chưa nhất quán: +0,065 [-0,022; +0,152] trên v1.0 và -0,025 [-0,083; +0,042] trên test 2 (nhãn LLM). [CHỜ: ablation `a2`, tức bỏ riêng phần mở rộng]

**Về đồ thị, chỉ được nói hẹp.** Trên toàn tập, mở rộng một bước gần như không đổi Accuracy khi không có thời gian (`b5` − `b2ctx`), và thêm rất ít khi có thời gian (`proposed` − `b7pp`). Kết luận này chỉ áp dụng cho kiểu mở rộng đã đo, và ở T2 có dấu hiệu ngược lại như nêu trên. Vai trò ngoại tuyến của đồ thị (dựng chuỗi, tính khoảng hiệu lực) lại là nền của các hệ lớp B. Bài này không đánh giá GraphRAG nói chung.

**Nhận diện bãi bỏ là khoảng trống rõ nhất.** Bộ lọc giúp hệ không trích bản cũ, nhưng generator không chuyển điều đó thành câu trả lời "đã hết hiệu lực". Đây là bài toán mở, và benchmark đo được nó.

**Khoảng cách lớn giữa hai bộ chưa được giải thích.** Mức Accuracy của `proposed` trên hai bộ khác nhau nhiều, kể cả khi so cùng nhóm. Một giả thuyết là mức trùng chữ của câu hỏi (mục 3.4): truy xuất từ vựng dựa nhiều vào việc câu hỏi giống lời văn. Thành phần nhóm, nguồn nhãn và loại văn bản cũng khác nhau. **Chưa đo độ chính xác theo mức trùng chữ, và chưa có truy xuất dense trên test để đối chứng.** [CẦN: phân tích theo mức trùng chữ, ghi là thăm dò]

**LLM chưa thay được người trong khâu gán nhãn.** Cả lời dặn bản 2 viết kỹ, gán đôi và hòa giải vẫn chưa đạt cổng. Trên mẫu hiệu chuẩn, hai model có 8 câu cùng sai so với nhãn người, nên hai model đồng ý với nhau chưa có nghĩa là đúng.

## 8. Giới hạn và nguy cơ

- **Gold và hệ dùng chung kho.** Khi kho bỏ sót một lần sửa đổi, hệ và gold có thể cùng sai mà vẫn khớp nhau. Gold độc lập là 0/75 và M2 chưa đạt. Đây là nguy cơ lớn nhất của cả bài.
- **Chất lượng nhãn.** Đồng thuận người gán thấp ở v1.0, nhãn agent chiếm 90/211 dòng test, test 2 (nhãn LLM) chưa có người kiểm.
- **Mẫu nhỏ ở các nhóm quan trọng.** Trên test v1.0, T3 có 4 lineage và T6 có 15 lineage. T1 chiếm 123/211 dòng.
- **Một generator cỡ nhỏ.** Mọi kết luận gắn với Qwen3-4B. Dao động bằng 0 mới đo trên dev (553/553 dòng), chưa đo khi đổi phần cứng hoặc thư viện.
- **Chỉ truy xuất từ vựng.** Dense và hybrid chưa có số trên test.
- **Chưa đủ điều kiện gọi là "cải thiện".** Theo tiêu chí của dự án còn thiếu: oracle context trên test, gold độc lập, các chế độ `as_of` khác ở tầng sinh, và phép bỏ từng nhóm. Vì vậy bài dùng "chênh lệch" thay cho "cải thiện".
- **Câu hỏi do LLM viết.** Theo `questions.jsonl`, 145/165 câu hỏi test v1.0 do Claude Opus 5.5 viết và 20 câu do DeepSeek viết. Bước chọn lọc cũng có thể thiên về câu dễ diễn đạt.
- **Phép chấm dựa trên đoạn chữ.** Accuracy không phải đánh giá ngữ nghĩa của người, và chưa có giám khảo được hiệu chuẩn.

## 9. Kết luận

Trên pháp luật Việt Nam, trong phạm vi hai bộ đã đo và một generator, ràng buộc thời gian đi cùng chênh lệch lớn nhất về Accuracy; lớp phiên bản giảm thêm lỗi trích dẫn vi phạm hiệu lực; mở rộng quan hệ một bước thêm rất ít trên toàn tập. Các hệ vẫn chưa nhận ra được điều khoản đã bãi bỏ. Bước tiếp theo cần thiết nhất là gold độc lập với kho, tiếp đó là baseline dense và oracle.

## Khai báo

- **Dữ liệu và mã nguồn:** ViLexTime v1.0 mang giấy phép CC-BY-4.0 (`data/vilextime/LICENSE`). [CẦN: chốt nơi công khai và thời điểm theo quy định ẩn danh của hội nghị]
- **Đạo đức:** không có đối tượng nghiên cứu là người dùng cuối; có người gán nhãn và luật sư. [CẦN: GVHD xác nhận có cần thủ tục không; thống nhất cách nêu tên hay ẩn danh luật sư]
- **Đóng góp tác giả (CRediT):** [CẦN: nhóm điền]
- **Xung đột lợi ích, tài trợ:** [CẦN: nhóm điền]
- **Sử dụng AI:** Claude và DeepSeek viết câu hỏi; Claude chọn đáp án ngắn; Codex gán nhãn agent; Sonnet, Codex và Opus gán và hòa giải nhãn của test 2 (nhãn LLM); Claude và Codex tham gia viết mã, phân tích và soạn tài liệu; Qwen là generator được đánh giá. **Bản nháp này do Claude Opus 5.5 soạn từ hồ sơ trong repo, chưa có người duyệt.** [CẦN: đối chiếu quy định AI của hội nghị và của UIT]

## Tài liệu tham khảo

*Danh sách lấy từ `references.bib`. Cột mức đọc chỉ để nhóm theo dõi, phải bỏ trước khi nộp.*

| Tài liệu | Mức đọc hiện tại |
|---|---|
| [cymbler2026fiscalqa] Cymbler, Rose; Guez, Daniel; Fabre, Laurent (2026). Temporal Misgrounding in Legal RAG: A Versioned-Corpus Benchmark for French Tax Law. arXiv:2608.09393. | Đã đọc một số mục của PDF: Introduction, Nugget-Based Scoring, Experimental Design, phụ lục artifact. Chưa đọc toàn văn |
| [demartim2025satgraph] de Martim, Hudson (2025). An Ontology-Driven Graph RAG for Legal Norms: A Hierarchical, Temporal, and Deterministic Approach. Legal Knowledge and Information Systems. | Đã đọc một số mục của bản arXiv v5: Proposed Framework, Case Study, Discussion; chưa đối soát bản kỷ yếu |
| [dror2018hitchhiker] Dror, Rotem; Baumer, Gili; Shlomov, Segev và cộng sự (2018). The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing. Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). | Mới đối chiếu metadata. Ghi trong references.bib: 2026-10-11; ACL Anthology; tóm tắt |
| [edge2024graphrag] Edge, Darren; Trinh, Ha; Cheng, Newman và cộng sự (2024). From Local to Global: A Graph RAG Approach to Query-Focused Summarization. arXiv:2404.16130. | Mới đối chiếu metadata. Ghi trong references.bib: 2026-10-11; arXiv (năm của bản v1; bản ghi arXiv hiện ghi 2025 theo phiên bản mới nhất); tóm tắt |
| [guo2025lightrag] Guo, Zirui; Xia, Lianghao; Yu, Yanhua và cộng sự (2025). LightRAG: Simple and Fast Retrieval-Augmented Generation. Findings of the Association for Computational Linguistics: EMNLP 2025. | Mới đối chiếu metadata. Ghi trong references.bib: 2026-10-11; ACL Anthology; tóm tắt (arXiv 2410.05779) |
| [gwet2008ac1] Gwet, Kilem Li (2008). Computing Inter-Rater Reliability and Its Variance in the Presence of High Agreement. British Journal of Mathematical and Statistical Psychology. | Mới đối chiếu metadata. Ghi trong references.bib: 2026-10-11; doi.org (Wiley); tóm tắt (bản PDF của tác giả) |
| [huwiler2025versionrag] Huwiler, Daniel; Stockinger, Kurt; Fürst, Jonathan (2025). VersionRAG: Version-Aware Retrieval-Augmented Generation for Evolving Documents. arXiv:2510.08109. | Mới đối chiếu metadata. Ghi trong references.bib: 2026-10-11; arXiv; tóm tắt |
| [nguyen2025vlqa] Nguyen, Tan-Minh; Nguyen, Hoang-Trung; Dao, Trong-Khoi và cộng sự (2025). VLQA: The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering. arXiv:2507.19995. | Đã đọc một số mục của PDF: Dataset Construction, Expert Annotation; cần xác nhận nơi công bố |
| [nguyen2026vihermes] Nguyen, Long S. T.; Bui, Quan M.; Ngo, Tin T. và cộng sự (2026). ViHERMES: A Graph-Grounded Multihop Question Answering Benchmark and System for Vietnamese Healthcare Regulations. arXiv:2602.07361. | Đã đọc một số mục của PDF: SRKG, Seeded Retrieval and Propagation, Conclusion |
| [prior2025consolidation] Prior, Max; Hof, Adrian; Wais, Niklas và cộng sự (2025). Risks and Limits of Automatic Consolidation of Statutes. Proceedings of the Natural Legal Language Processing Workshop 2025. | Mới đối chiếu metadata. Ghi trong references.bib: 2026-10-11; ACL Anthology; tóm tắt |
| [prior2026oldfriend] Prior, Max; Schultz, Andreas; Grabmair, Matthias (2026). Asking For An Old Friend: Diagnosing and Mitigating Temporal Failure Modes in LLM-based Statutory Question Answering. arXiv:2605.23497. | Mới đối chiếu metadata. Ghi trong references.bib: 2026-10-11; arXiv (bài ICAIL 2026 theo MASTER_RESEARCH_GUIDE; chưa thấy bản kỷ yếu); tóm tắt |

---

# Phần C. Reviewer sẽ hỏi gì

| # | Câu hỏi | Hiện trả lời được gì | Cần làm |
|---|---|---|---|
| 1 | Gold lấy từ chính kho của hệ, vậy kết quả có vòng lặp không? | Có khai báo, chưa có đối chứng độc lập | E6 khoảng 120 dòng, M2 |
| 2 | Nhãn test 2 đáng tin đến đâu? | Chưa có số đo; lời dặn v2 không đạt cổng | Người kiểm một mẫu test 2 |
| 3 | Đồng thuận AC1 0,377 thì v1.0 có dùng được không? | Có quy tắc chọn nhãn và mẫu luật sư 43/50; số vẫn thấp | Trình bày thẳng; cân nhắc báo riêng theo nguồn nhãn |
| 4 | Sao không so với GraphRAG hay LightRAG? | Không có | Chạy E4 trên tập con, hoặc thu hẹp kết luận (bản nháp đã thu hẹp) |
| 5 | Dense ở đâu? BM25 có phải baseline quá yếu? | Chưa có số test | Colab phiên 3 |
| 6 | TVER gần 0 có phải hiển nhiên do bộ lọc? | Đúng một phần | Không để TVER làm số chính; báo cùng wrong_version và kết quả theo nhóm |
| 7 | Generator 4B có quá nhỏ không? | Chưa có model thứ hai | Thêm một generator, viết amendment trước |
| 8 | Có chắc là đóng góp mới? | Chưa khảo sát có hệ thống | Đọc 14 nguồn, ghi log tìm kiếm |
| 9 | Vì sao hai bộ chênh nhau nhiều vậy? | Mới có giả thuyết | Phân tích theo mức trùng chữ |

# Phần D. Việc cần làm để nộp được

**Chặn nộp:**

| Việc | Ai làm | Phụ thuộc |
|---|---|---|
| Gold độc lập (E6) và kiểm mẫu test 2 | Luật sư, người trong nhóm | Mình soạn phiếu |
| Colab đợt 2 (v1.0, test 2) và lần chạy cuối ở G4 | Nhóm | Đợt 2 chạy được ngay; lần cuối chờ G1–G3 của `docs/plans/active/master-plan.md` |
| Đọc 14 nguồn gần nhất; khảo sát có log | Nhóm, mình hỗ trợ | Cần tác giả tự đọc |
| M2 hoặc khai báo chưa đạt | Nhóm | Truy vấn đối chiếu tay |
| Chốt M4 và hội nghị | Nhóm, GVHD | Quyết định mọi phần còn lại |

**Nên có:** E7 do người gán; phân tích theo mức trùng chữ; bỏ từng nhóm và các chế độ `as_of`; LightRAG trên tập con; generator thứ hai; hiệu chuẩn LLM-as-judge.

# Phần E. Nguồn số liệu

Mọi số trong bảng và phần lớn số trong câu do `scripts/paper/paper_build.py` đọc trực tiếp từ các file dưới đây. `scripts/paper/paper_check.py` đối chiếu Bảng 6, 7, 10, 11 và quy mô kho với chương 3, 6, quét câu chữ cấm, và phải bắt được ba lỗi cấy sẵn. Chạy từ thư mục gốc của repo. Chưa có lượt phản biện độc lập.

| Số liệu | File |
|---|---|
| E3 v1.0, kiểm định | `runs/E3_v1/test/all.score.json`, `confirm.json` |
| E3 test 2 (chỉ dùng bản chấm lại) | `runs/E3_test2/rescore/all.score.json`, `confirm.json` |
| E1 | `runs/E1/test/ladder.score.json`, `runs/E1_test2/test/ladder.score.json` (chỉ lấy cột truy xuất) |
| Bãi bỏ, `b1` để trống | Các file `.jsonl` trong `runs/E3_v1/test`, `runs/E3_test2/test` |
| Phân rã lỗi | `docs/reports/e7_phan_ra_loi.md` |
| Quy mô, đồng thuận, nguồn nhãn v1.0 | `data/vilextime_dataset/manifest.json`, `vilextime_meta.jsonl` |
| Quy mô kho | `data/derived/corpus/manifest.json` |
| Nhãn test 2 | `data/review/test2_llm/agreement.json`, các file TSV cùng thư mục |
| Hiệu chuẩn lời dặn bản 2 | `data/review/test2_llm_v2/calib_score.json`, `calib_key.tsv`, `calib_silver.tsv` |
| Mức trùng chữ | `test2_packs.copy_share` chạy 05/11 trên `data/derived/corpus`; **in ra màn hình, chưa lưu file** |
| Kiểm chất lượng kho, agent, luật sư | `docs/thesis/chuong-3…`, `chuong-4…`; nguồn gốc ghi trong chú thích của từng chương |
