# ViLexTime: Bộ đánh giá hỏi đáp pháp luật tiếng Việt theo mốc thời gian và phép đo vai trò của biểu diễn phiên bản

*Tên tiếng Anh tạm: ViLexTime: A Point-in-Time Benchmark for Vietnamese Legal QA and a Controlled Ladder of Temporal Representations*

**Bản nháp ngày 05/11/2026, để xem hiện trạng. Chưa phải bản nộp, chưa có người duyệt.**
<!-- nguồn: docs/plans/active/master-plan.md -->

---

# Phần A. Hiện trạng trong một trang

**Bản nháp theo hướng A: bộ đánh giá và phép đo có đối chứng.** V1.0 và test 2 là hai vòng thử có khai báo; bảng kết luận chính dành cho bộ test cuối chưa chạy. Yêu cầu C9 của tác giả cho phép viết theo hướng này; bản nháp không thay các quyết định phân tích đã Accepted. Hai sinh viên cần đọc và sửa trước khi gửi GVHD.
<!-- nguồn: docs/plans/active/master-plan.md; yêu cầu C9 của tác giả ngày 05/11/2026 -->

| Phần của paper | Hiện trạng | Phần cần hoàn tất |
|---|---|---|
| Câu hỏi và giả thuyết | Có trong đề cương; ADR lưu khai báo lịch sử | Amendment trước bộ cuối, ghi rõ đã thấy các vòng thử |
| Dữ liệu vòng thử | v1.0 nhãn hỗn hợp người/agent; test 2 nhãn LLM | Công bố nguồn nhãn, không dùng làm bộ cuối |
| Chất lượng nhãn | AC1 người 0,377; lời dặn LLM v2 0,530 | Thẻ Q1–Q4, gán mù, ghi thời gian, cổng G1–G2 |
| Gold | Dẫn xuất từ cùng đồ thị với hệ; M2 chưa đạt | Đối chiếu VBHN và gold mù do người kiểm |
| Kiến trúc | `proposed` vòng thử chỉ từ vựng; `proposed2` lai ghép có số truy xuất dev | Sinh dev, khóa hệ; chưa có Accuracy `proposed2` |
| Kết quả chính | [CHỜ G4: bộ test cuối] | Không lấy vòng thử hoặc dev điền vào |
| Baseline / ablation | Chưa đủ hệ theo kế hoạch | Colab đợt bổ sung cho vòng thử, rồi bộ cuối đúng khai báo |
| Phân rã lỗi | Có phân loại máy, thăm dò | E7 người kiểm và giám khảo được hiệu chuẩn |
| Tổng quan | Có nguồn đã đọc và nguồn mới có metadata | Không mô tả chi tiết nguồn chưa đọc; khảo sát trước khi định vị tính mới |
| Nộp bài | Chưa chọn hội nghị, chưa duyệt | Tác giả và GVHD rà nội dung, AI, ẩn danh và nơi nộp |
<!-- nguồn: data/vilextime_dataset/manifest.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md; runs/README.md -->

Bài hướng tới công bố tài nguyên có nguồn gốc rõ và đo phần đóng góp của lọc ngày, chuỗi phiên bản, lan truyền và mở rộng quan hệ một bước. Không đặt điều kiện hệ đề xuất phải thắng. Bảng vòng thử giữ nguyên để giải thích quá trình và khả năng lặp lại; kết luận chính chỉ điền sau G4. `[CHỜ G4: …]` là phần kết quả hoặc hồ sơ bộ cuối chưa có; `[CHỜ COLAB: …]` là đầu ra đang chờ; `[CẦN: …]` là việc cần tác giả kiểm hoặc bổ sung.
<!-- nguồn: docs/plans/active/master-plan.md -->

---

# Phần B. Bản nháp paper

## Tóm tắt

Hỏi đáp pháp luật theo mốc đòi hỏi chọn đúng lời văn có hiệu lực tại thời điểm áp dụng. Bản nháp trình bày ViLexTime và một thang đối chứng để phân biệt vai trò của lọc thời gian, biểu diễn phiên bản và mở rộng quan hệ một bước. Kết luận chính được thiết kế cho bộ test cuối do người kiểm, với gold đối chiếu nguồn độc lập; bộ này chưa chạy. Hai vòng thử có khai báo được báo riêng: v1.0 có 211 dòng thuộc 165 lineage, nhãn hỗn hợp người và agent; test 2 (nhãn LLM) có 227 dòng thuộc 101 lineage. Trong phạm vi các vòng thử, kiểm định về lọc cấp văn bản được ủng hộ ở cả hai bộ; kiểm định về truy xuất phiên bản được ủng hộ ở v1.0 nhưng chưa đủ bằng chứng ở bộ nhãn LLM. Phân rã mô tả chưa cho phép quy toàn bộ chênh lệch cho đồ thị trực tuyến. Gold dùng chung kho với hệ, đồng thuận nhãn thấp và khả năng nhận diện bãi bỏ yếu giới hạn diễn giải. [CHỜ G4: kết quả và kết luận chính trên bộ cuối; chưa khẳng định hệ đề xuất thắng].
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json; docs/plans/active/master-plan.md -->

**Từ khóa:** RAG pháp luật, truy xuất theo thời gian, phiên bản văn bản, bộ đánh giá, tiếng Việt.

## 1. Giới thiệu
<!-- nguồn: docs/plans/active/master-plan.md -->

Văn bản pháp luật thay đổi theo thời gian. Câu hỏi "mức phạt là bao nhiêu" có đáp án khác nhau tùy ngày hỏi. Một hệ RAG thông thường xếp hạng theo mức liên quan, nên có thể trả về lời văn đúng chủ đề nhưng đã hết hiệu lực. FiscalQA Pro đã đặt vấn đề này thành đối tượng đánh giá với luật thuế Pháp [@cymbler2026fiscalqa]. Với pháp luật Việt Nam, các tài nguyên chúng tôi đã đọc tập trung vào truy xuất điều luật và hỏi đáp nhiều bước [@nguyen2025vlqa; @nguyen2026vihermes]; chúng tôi chưa khảo sát đủ để nói không có công trình tương tự. [CẦN: lượt khảo sát có ghi truy vấn, ngày, nguồn đã mở và nguồn không mở được]
<!-- nguồn: docs/plans/active/master-plan.md -->

Một câu hỏi chưa rõ là lợi ích đến từ đâu. Nếu một bộ lọc theo ngày văn bản đã đủ tốt, việc dựng đồ thị phiên bản khó được biện minh. Bài này đo trực tiếp điều đó, qua ba câu hỏi:

- **RQ1.** LLM và RAG hiện có mắc lỗi áp dụng sai phiên bản ở mức nào trên pháp luật Việt Nam?
- **RQ2.** Biểu diễn theo phiên bản có giảm lỗi so với RAG phẳng và đồ thị phi thời gian không?
- **RQ3.** Lợi ích đến từ biểu diễn phiên bản hay chỉ từ lọc theo siêu dữ liệu thời gian?
<!-- nguồn: docs/plans/active/master-plan.md -->

**Các nội dung đóng góp được chuẩn bị theo hướng A:**

1. **Tài nguyên ViLexTime và quy trình kiểm:** bản v1.0 hiện có 769 dòng chính; bộ test cuối được tách riêng và cần người kiểm. Số dòng phát hành không đồng nghĩa số mẫu đã kiểm độc lập về pháp lý.
2. **Phép đo có đối chứng:** thang cấu hình tách các mức thông tin thời gian, giữ hồ sơ hai vòng thử và dành bảng kết luận cho bộ cuối. Chỉ các nấc kề nhau đổi một thành phần; các so sánh xa hơn chưa cô lập tác dụng riêng.
3. **Phân tích giới hạn trên pháp luật Việt Nam:** hai nút thắt tìm và dùng căn cứ đã được báo trên dữ liệu khác [@yao2026lawinforce]; phần riêng ở đây là nhận diện bãi bỏ và chất lượng nhãn. Phân loại máy và so sánh nhãn LLM chỉ là thăm dò; kết luận chính còn chờ người kiểm và G4.
<!-- nguồn: data/vilextime_dataset/manifest.json; docs/plans/active/master-plan.md; docs/reports/e7_phan_ra_loi.md -->

## 2. Công trình liên quan
<!-- nguồn: references.bib; docs/thesis/chuong-2-co-so-ly-thuyet.md -->

**Hỏi đáp pháp luật theo thời gian.** FiscalQA Pro phân biệt chỉ mục chỉ có bản hiện hành với chỉ mục nhiều phiên bản điều kiện theo ngày, và chấm bằng nugget tất định [@cymbler2026fiscalqa]. Điều kiện RAG tĩnh của bài đó được cấp sẵn điều luật gold, khác với bài toán tự tìm trên toàn kho của chúng tôi. Prior và cộng sự dùng 312 cặp hỏi đáp luật Đức, lọc theo mốc ngày như một ràng buộc cứng, và chấm việc áp đúng phiên bản [@prior2026oldfriend]. LawInForce-eCFR dựng 805 cặp sửa đổi có người kiểm trên quy định liên bang Mỹ, với 3.220 câu đúng/sai; Recall@1 tăng từ 2,80% của BM25 có lọc ngày lên 30,90% của bộ truy xuất đề xuất, và bài kết luận có hai nút thắt là tìm đúng luật đang có hiệu lực và áp dụng quy tắc số [@yao2026lawinforce]. NitiBench+ (bản nháp, đang phản biện) cho thấy với luật Thái, đọc văn bản hiện hành thay vì văn bản đúng mốc làm giảm 0,25 điểm ở luật đã sửa và 0,79 điểm ở luật đã bãi bỏ [@akarajaradwong2026nitibenchplus]. Vì vậy giá trị của việc lấy đúng văn bản không còn là điều mới. Bài này tập trung vào phần các công trình đó chưa tách, theo những gì chúng tôi đã đọc: trên cùng dữ liệu, phần đóng góp riêng của lọc theo ngày văn bản, lọc theo khoảng hiệu lực phiên bản và lan truyền hiệu lực từ nút cha, trên pháp luật Việt Nam. [CẦN: đọc phụ lục NitiBench+, LawInForce-eCFR trước khi nộp]
<!-- nguồn: references.bib; docs/thesis/chuong-2-co-so-ly-thuyet.md -->

**Mô hình hóa phiên bản.** Các phần đã đọc của SAT-Graph RAG trình bày cấu trúc và thời gian của quy phạm, chính sách truy vấn tất định và case study định tính [@demartim2025satgraph]. VersionRAG dựng đồ thị phiên bản cho tài liệu kỹ thuật (Node.js, Spark, Bootstrap), không có dữ liệu luật và không xử lý mốc ngày, nên chỉ là đối chứng về biểu diễn [@huwiler2025versionrag]. Một nghiên cứu dùng LLM áp lệnh sửa đổi lên luật Đức cho thấy rủi ro của lời văn hợp nhất tự động [@prior2025consolidation]; cách làm và mẫu số khác nên chúng tôi không đặt số của bài đó cạnh số của mình.
<!-- nguồn: references.bib; docs/thesis/chuong-2-co-so-ly-thuyet.md -->

**Tài nguyên tiếng Việt.** VLQA xây bộ hỏi đáp tư vấn có chuyên gia kiểm và loại điều khoản đã bãi bỏ [@nguyen2025vlqa]. ViHERMES dùng đồ thị cho hỏi đáp nhiều bước về quy định y tế [@nguyen2026vihermes]. VLegal-Bench [@dong2026vietlegal] và ViLegalExpert [@nguyen2026vilegalexpert] là các bộ tiếng Việt quy mô lớn; trong các phần đã xem, chúng tôi chưa thấy gold đến phiên bản điều khoản theo mốc. [CẦN: đọc đầy đủ hai bài này] Chúng tôi không so điểm với các bài này vì tác vụ và mẫu số khác nhau.
<!-- nguồn: references.bib; docs/thesis/chuong-2-co-so-ly-thuyet.md -->

**GraphRAG.** Bài này không chạy GraphRAG [@edge2024graphrag] hay LightRAG [@guo2025lightrag]. Hai hệ đó dựng đồ thị thực thể do LLM trích; mở rộng của chúng tôi đi theo quan hệ sửa đổi tất định có sẵn trong kho, nên kết quả **không phải** phép đánh giá các hệ đó. [CHỜ G4: LightRAG trên tập con sau G3, báo riêng vì khác corpus]

**Khoảng trống, trong phạm vi đã tìm.** Trong các truy vấn ghi ở phụ lục, chạy ngày 05/11/2026 trên arXiv, Crossref, OpenAlex (4/12 truy vấn), danh mục tiêu đề ACL Anthology và tìm kiếm web, chúng tôi không thấy (a) bộ đánh giá nào cho pháp luật Việt Nam gán gold đến phiên bản điều khoản theo mốc và chấm nhầm phiên bản, và (b) công trình nào so sánh có đối chứng, trên cùng dữ liệu, giữa lọc theo ngày văn bản, lọc theo khoảng hiệu lực phiên bản và lan truyền hiệu lực từ nút cha. Semantic Scholar, ACM DL, IEEE Xplore, Google Scholar, SSRN và DBLP không mở được ở lượt này, và một số bài liên quan mới xem đến bản ghi. Chúng tôi không đưa ra tuyên bố nào về thứ tự công bố, cũng không khẳng định chưa có ai làm. [CẦN: chạy lại phần bị chặn trước khi nộp]
<!-- nguồn: references.bib; docs/thesis/chuong-2-co-so-ly-thuyet.md -->

## 3. Dữ liệu
<!-- nguồn: references.bib; docs/thesis/chuong-2-co-so-ly-thuyet.md -->

### 3.1. Kho văn bản và chuỗi phiên bản
<!-- nguồn: data/derived/corpus/manifest.json; docs/thesis/chuong-3-kho-van-ban-va-do-thi.md -->

Dữ liệu thu thập từ vbpl.vn. Pipeline nhận dạng câu lệnh sửa đổi và bãi bỏ, phân giải điều khoản đích, rồi dựng chuỗi phiên bản với khoảng hiệu lực nửa mở. Khoảng hiệu lực thực của một phiên bản là giao của khoảng cục bộ với độ phủ của các nút tổ tiên và văn bản sở hữu. Kho thực nghiệm gồm 17.333 văn bản, 1.455.372 đơn vị lời văn gốc (lớp A), 53.991 đơn vị lệnh (lớp A) và 1.477.089 đơn vị phiên bản (lớp B).
<!-- nguồn: data/derived/corpus/manifest.json; docs/thesis/chuong-3-kho-van-ban-va-do-thi.md -->

Kiểm chất lượng lịch sử ghi 58/60 sự kiện áp đúng (Wilson 95% từ 88,6% đến 99,1%), recall theo `expiryProvisions` 62,2% (5.007/8.046 cặp), và 5.762/7.201 cặp lời văn (80,02%) khớp chính xác với văn bản hợp nhất trên 51 văn bản. Ba số này khác mẫu số, không gộp thành một độ chính xác chung. M2 chưa đạt. Phép thử tải/căn PDF VBHN hiện chỉ là khảo sát kỹ thuật; chưa có báo cáo đối chiếu hoàn chỉnh và gold mù. [CHỜ G4: bằng chứng M2 và gold mù từ nguồn ngoài được kiểm ở G2]
<!-- nguồn: data/derived/corpus/manifest.json; docs/thesis/chuong-3-kho-van-ban-va-do-thi.md -->

### 3.2. Vòng thử ViLexTime v1.0 — nhãn hỗn hợp
<!-- nguồn: data/vilextime_dataset/manifest.json; data/vilextime_dataset/vilextime_meta.jsonl; docs/vilextime-datasheet.md; docs/plans/active/master-plan.md -->

Một dòng là một cặp câu hỏi và mốc. Các dòng cùng lineage dùng chung điều khoản và câu hỏi, nên lineage là đơn vị độc lập khi phân tích. LLM viết câu hỏi, sau đó qua bộ kiểm tự động và bước kiểm nhãn. Dev và test tách theo văn bản đích. Bảng chính dùng mốc giữa khoảng hiệu lực, để ngày hỏi không tự gợi ra văn bản vừa có hiệu lực.

**Bảng 1. ViLexTime v1.0, split test, giữa khoảng**
<!-- nguồn: data/vilextime_dataset/manifest.json; data/vilextime_dataset/vilextime_meta.jsonl; docs/vilextime-datasheet.md; docs/plans/active/master-plan.md -->

<!-- nguồn: data/vilextime_dataset/manifest.json; data/vilextime_dataset/vilextime_meta.jsonl; docs/vilextime-datasheet.md; docs/plans/active/master-plan.md -->
| Nhóm | Hiện tượng | Dòng | Lineage |
|---|---|---:|---:|
| T1 | Điều khoản một phiên bản (đối chứng) | 123 | 123 |
| T2 | Hai đáp án khác nhau | 46 | 23 |
| T3 | Từ ba đáp án khác nhau | 12 | 4 |
| T6 | Điều khoản đã bị bãi bỏ | 30 | 15 |
| Tổng | | 211 | 165 |
<!-- nguồn: data/vilextime_dataset/manifest.json; data/vilextime_dataset/vilextime_meta.jsonl; docs/vilextime-datasheet.md; docs/plans/active/master-plan.md -->

**Nguồn nhãn.** Trên 211 dòng ranh giới của test: 88 dòng do A và B cùng nhãn, 33 dòng do luật sư chốt (trong đó 10 dòng có phiếu Claude hỗ trợ), 90 dòng do agent gán. Nhãn agent chỉ được dùng ở T1 và T6; T2 và T3 của test đều có nguồn người.
<!-- nguồn: data/vilextime_dataset/manifest.json; data/vilextime_dataset/vilextime_meta.jsonl; docs/vilextime-datasheet.md; docs/plans/active/master-plan.md -->

**Đồng thuận thấp, và phải nói rõ.** Trên 246 dòng gán đôi theo hướng dẫn hiện hành: AC1 0,377 [0,250; 0,496], κ 0,235, thỏa thuận nhãn âm 0,395. Theo nhóm, AC1 của T1 là 0,878 (n=40), T2 0,269 (n=106), T3 0,378 (n=30), T6 0,216 (n=70). A gán khoảng 5 giây mỗi dòng trong đợt 26/10 theo hồ sơ kế hoạch; do đó chỉ số đồng thuận chưa chứng minh việc đối chiếu được làm đầy đủ. AC1 được chọn sau pilot, không khai báo trước; tài liệu nền đã có bản ghi [@gwet2008ac1], còn chờ đọc gốc. Agent đạt AC1 0,721 và p_neg 0,610 trên 178 dòng hiệu chuẩn, không đạt ngưỡng AC1 0,80. Luật sư kiểm 50 dòng nhãn agent và đồng ý 43.
<!-- nguồn: data/vilextime_dataset/manifest.json; data/vilextime_dataset/vilextime_meta.jsonl; docs/vilextime-datasheet.md; docs/plans/active/master-plan.md -->

**T6 bị thu hẹp mạnh.** Hơn một trăm lineage bị loại vì không chắc nội dung có chuyển sang văn bản khác không (108 lineage `relocation_unclear`, 25 lineage `relocated`). Vì thế T6 không đại diện cho mọi điều khoản từng bị bãi bỏ.
<!-- nguồn: data/vilextime_dataset/manifest.json; data/vilextime_dataset/vilextime_meta.jsonl; docs/vilextime-datasheet.md; docs/plans/active/master-plan.md -->

### 3.3. Test 2 (nhãn LLM)
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->

Test 2 là vòng thử lặp lại có khai báo, gồm T2, T3 và T6, **nhãn do LLM gán, không có người hay luật sư kiểm**. Nó được báo riêng và không gộp với v1.0. Câu hỏi bị giới hạn trùng chữ với lời văn ở mức tối đa 40%.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->

**Bảng 2. Test 2 (nhãn LLM), giữa khoảng**
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->

<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->
| Nhóm | Dòng | Lineage |
|---|---:|---:|
| T2 | 120 | 60 |
| T3 | 75 | 25 |
| T6 | 32 | 16 |
| Tổng | 227 | 101 |
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->

**Quy trình nhãn.** Sonnet 5.5 và Codex gán độc lập 138 câu, lệch ở 53 câu và Opus 5.5 hòa giải; sáu câu phân vân được agent tra luật kiểm lại, trong đó 4 câu đổi nhãn. Giữa hai LLM: AC1 của Q1, Q2, Q3 là 0,907, 0,884, 0,766, nhưng thỏa thuận nhãn âm chỉ 0,476, 0,222, 0,133. Cổng đồng thuận không đạt.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->

**Giới hạn của lời dặn.** Rà soát sau đó cho thấy lời dặn gán nhãn chỉ gồm thẻ viết cho người cộng vài dòng; thiếu các định nghĩa thẻ trỏ tới; có thêm chỉ dẫn "phải khắt khe" (hai model loại 45 và 24 câu); model chỉ đọc đoạn trích nên Q4 = Không phần lớn nghĩa là "không thấy trong phần được đưa". Lời dặn bản 1 không qua bước hiệu chuẩn nào.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->

**Lời dặn bản 2 không đạt cổng.** Chúng tôi viết bản 2 đầy đủ hơn và khai báo trước cổng: so với 68 câu có nhãn người độc lập, nhãn cuối phải đạt AC1 ≥ 0,80 và p_neg ≥ 0,60. Kết quả: AC1 0,530, p_neg 0,758, **không đạt**. Quy trình bắt 25/29 câu xấu và loại nhầm 12/39 câu tốt. Trong 29 câu xấu có 25 câu ở T6, nên cổng gần như không đo được T2 và T3. Theo khai báo, chúng tôi dừng: không gán test 2 (nhãn LLM) bằng bản 2 và không có phân tích độ nhạy. Do đó, **chưa có số đo nào cho biết bộ nhãn LLM này khớp với người đến đâu**. [CẦN: người kiểm một mẫu của bộ này]
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->

**Một lần chấm sai đã công bố.** Lần chấm E3 đầu của bộ này sai vì release thiếu đáp án ngắn, trong khi phép kiểm chứa coi đáp án rỗng là đúng. Lỗi được khai báo, release được sửa, các câu trả lời cũ được chấm lại một lần và không sinh lại. Bộ chấm nay từ chối dòng thiếu đáp án ngắn. Mọi số của bộ này trong bài là số sau khi sửa.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; data/review/test2_llm/agreement.json; data/review/test2_llm_v2/calib_score.json -->

### 3.4. Bộ test cuối đang chuẩn bị
<!-- nguồn: docs/plans/active/master-plan.md -->

Bộ cuối tuyển lineage chưa có hệ nào chạy, không trùng lineage của các vòng thử và không trùng văn bản đích với dev. Quy trình dự kiến gán theo câu hỏi, kiểm Q1 (đúng văn bản/mốc), Q2 (hỏi nội dung thay đổi), Q3 (rõ và không lộ đáp án), Q4 (quy định khác hoặc nơi nội dung chuyển đến). Hai người độc lập, mù với nhãn và gợi ý LLM cũng như kết quả hệ; luật sư chốt lệch không có phiếu AI. Phải trích câu nguồn, trang gán ghi thời gian từng câu. Gold mù đọc văn bản gốc hoặc VBHN, không thấy lời văn phiên bản đồ thị.
<!-- nguồn: docs/plans/active/master-plan.md; docs/vilextime-annotation.md -->

Cỡ mẫu và tầng chất lượng phải báo theo bản khóa, không điền bằng dự báo quota. [CHỜ G4: quy mô thực tế, phân tầng người/LLM, đồng thuận, thời gian và gold mù của bộ cuối]. Mức trùng chữ giữa các vòng thử cần phép đo lưu thành file trước khi công bố số; bản nháp này bỏ các giá trị chỉ từng in ra màn hình. [CẦN: lưu phân tích trùng chữ tái lập trước khi diễn giải nguyên nhân chênh lệch]
<!-- nguồn: docs/plans/active/master-plan.md; scripts/paper/paper_values.py -->

## 4. Các hệ so sánh
<!-- nguồn: src/vilexgraph/framework/systems.py; src/vilexgraph/framework/graphx.py; runs/README.md -->

Thang chính giữ cố định truy xuất từ vựng (SQLite FTS5, k = 20), prompt và generator. Mỗi nấc kề nhau đổi một thành phần.
<!-- nguồn: src/vilexgraph/framework/systems.py; src/vilexgraph/framework/graphx.py; runs/README.md -->

**Bảng 3. Cấu hình**
<!-- nguồn: src/vilexgraph/framework/systems.py; src/vilexgraph/framework/graphx.py; runs/README.md -->

<!-- nguồn: src/vilexgraph/framework/systems.py; src/vilexgraph/framework/graphx.py; runs/README.md -->
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
<!-- nguồn: src/vilexgraph/framework/systems.py; src/vilexgraph/framework/graphx.py; runs/README.md -->

**Phạm vi của "đồ thị".** Đồ thị phiên bản chủ yếu làm việc ngoại tuyến: dựng chuỗi và tính khoảng hiệu lực. Trong lúc trả lời, mở rộng chỉ là lấy láng giềng một bước bằng truy vấn SQL (5 seed, fanout 3), không tìm đường nhiều bước và không có tóm tắt cộng đồng. Ở đường nhập batch dùng cho E3, Verifier chỉ kiểm ID trích dẫn và không sinh lại, nên chúng tôi không gán tác dụng nào cho nó.
<!-- nguồn: src/vilexgraph/framework/systems.py; src/vilexgraph/framework/graphx.py; runs/README.md -->

**Generator.** Qwen/Qwen3-4B-Instruct-2507, revision `cdbee75`, NF4, greedy, tối đa 512 token mới. Generator nhận mốc, câu hỏi và các đoạn căn cứ, rồi trả lời theo ba dòng: lời văn, hiệu lực (`còn`, `không`, `không rõ`), và nhãn căn cứ. Chỉ `không` được hiểu là khẳng định hết hiệu lực; `không rõ` không được tính là nhận ra bãi bỏ.
<!-- nguồn: src/vilexgraph/framework/systems.py; src/vilexgraph/framework/graphx.py; runs/README.md -->

### Cấu hình đang hoàn thiện theo đề cương

Các tầng L0–L3 ngoại tuyến phân tích cấu trúc, trích tác động, dựng chuỗi và khoảng hiệu lực; L4 kết hợp từ vựng, ngữ nghĩa, mở rộng có ràng buộc thời gian; L5 sinh và kiểm trích dẫn. `proposed` đã chạy các vòng thử chỉ dùng từ vựng. `proposed2` lai ghép thêm `rel_up`: lấy seed trước bộ lọc ngày để tìm lệnh nhắm cả đích và tổ tiên, sau đó xét hiệu lực văn bản ban hành lệnh. Cấu hình mới chỉ có số truy xuất dev, chưa có Accuracy. Khi truy xuất, hệ đọc chỉ mục và cây SQLite cùng vector cục bộ; không gọi Neo4j hoặc Milvus.
<!-- nguồn: docs/DeCuongKLTN_23521635_23521643_UIT.docx; src/vilexgraph/framework/graphx.py; src/vilexgraph/framework/retrieve.py; runs/README.md -->

[CHỜ COLAB: sinh và chấm dev `proposed2`, `p2a2`, `p2a3` và đối chứng lai ghép]. Verifier cũ không bác câu nào trên dev khi bộ lọc cùng tier đã áp; cần đo riêng khi chưa có bộ lọc đủ mạnh trước khi quy tác dụng cho module.
<!-- nguồn: runs/README.md; docs/plans/active/master-plan.md -->

## 5. Thiết kế thực nghiệm
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; scripts/eval/score_vilextime.py -->

**Khai báo các vòng thử.** ADR 0005 khóa giả thuyết, đại lượng, lát dữ liệu, chiều dự đoán và quy tắc kết luận trước khi chạy test. Mỗi cấu hình chỉ chạy một lần trên test. Mọi thay đổi sau đó ghi thành amendment, nói rõ lúc đó đã thấy kết quả nào. Đây là khai báo trong git, không phải đăng ký công khai.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; scripts/eval/score_vilextime.py -->

**Chỉ số.** *Accuracy* là phép chấm tương phản: câu trả lời phải chứa các đoạn gold và tránh đoạn chỉ thuộc phiên bản khác; dòng bãi bỏ chỉ đúng khi hệ khẳng định hết hiệu lực. *TV-Recall@k* cần đúng phiên bản; *Recall@k* chỉ cần đúng điều khoản. *TVER* là tỷ lệ dòng có ít nhất một trích dẫn không có hiệu lực tại mốc, tính trên các dòng có trích dẫn phân giải được, nên luôn đọc cùng độ phủ trích dẫn. *wrong_version* xét nội dung câu trả lời có chứa đoạn chỉ phiên bản khác có, trên các dòng có đoạn phân biệt. Chưa dùng LLM làm giám khảo. [CHỜ G4: hiệu chuẩn LLM-as-judge với người theo kế hoạch; chưa có điểm hợp lệ]
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; scripts/eval/score_vilextime.py -->

**Thống kê.** Bootstrap theo cụm lineage, 10.000 lần lấy mẫu lại, khoảng phân vị 95%. Bootstrap theo cụm vì các dòng của một lineage không độc lập, một vấn đề được nêu mà chưa có lời giải chung [@dror2018hitchhiker]. [CẦN: nguồn đã xác minh cho bootstrap theo cụm] Họ xác nhận gồm sáu kiểm định với hiệu chỉnh Holm, α = 0,05. [CẦN: nguồn đã xác minh cho Holm] "Ủng hộ" cần p sau Holm < 0,05 và đúng chiều dự đoán; ngược chiều là "bác"; còn lại là "không đủ bằng chứng". XN5, XN6, XN7 chỉ thăm dò vì lát quá nhỏ. Mọi so sánh ngoài họ đều là mô tả.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; scripts/eval/score_vilextime.py -->

## 6. Hai vòng thử có khai báo
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/all.score.json; runs/E3_test2/rescore/confirm.json -->

Các bảng dưới là kết quả vòng thử, được báo riêng theo kế hoạch lịch sử và giữ nguyên phán quyết. Bộ test cuối dùng cho kết luận chính chưa chạy. Các kiểm định gọi là xác nhận chỉ trong thiết kế vòng thử tương ứng; không trở thành xác nhận trên bộ cuối. Số trong bảng được dựng từ file, làm tròn theo hàm định dạng.
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; docs/plans/active/master-plan.md; scripts/paper/paper_values.py -->

### 6.1. Truy xuất theo thang (E1)
<!-- nguồn: runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json -->

**Bảng 4. TV-Recall@1 và Recall@1, v1.0**
<!-- nguồn: runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json -->

<!-- nguồn: runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json -->
| Hệ | TV-R@1 | R@1 |
|---|---:|---:|
| `b2ctx` | 0,289 | 0,374 |
| `b7` | 0,417 | 0,483 |
| `b7v` | 0,398 | 0,521 |
| `b7plus` | 0,464 | 0,493 |
| `b7pp` | 0,464 | 0,464 |
<!-- nguồn: runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json -->

**Bảng 5. TV-Recall@1 và Recall@1, test 2 (nhãn LLM)**
<!-- nguồn: runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json -->

<!-- nguồn: runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json -->
| Hệ | TV-R@1 | R@1 |
|---|---:|---:|
| `b2ctx` | 0,070 | 0,154 |
| `b7` | 0,115 | 0,176 |
| `b7v` | 0,070 | 0,159 |
| `b7plus` | 0,141 | 0,141 |
| `b7pp` | 0,141 | 0,141 |
<!-- nguồn: runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json -->

Ba điều lặp lại về chiều trên cả hai bộ (mô tả, ngoài họ):

- Riêng đưa lời văn đã hợp nhất vào (`b7v` − `b7`) không tăng TV-R@1: -0,019 [-0,046; +0,005] trên v1.0 và -0,044 [-0,074; -0,017] trên test 2 (nhãn LLM).
- Bước lọc theo phiên bản (`b7plus` − `b7v`) có khoảng không chứa 0: +0,066 [+0,034; +0,101] và +0,070 [+0,036; +0,109].
- Lan truyền hiệu lực (`b7pp` − `b7plus`) không thay đổi TV-R@1 ở cả hai bộ: +0,000 [+0,000; +0,000] và +0,000 [+0,000; +0,000].
<!-- nguồn: runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json -->

### 6.2. Câu trả lời (E3)
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

**Bảng 6. v1.0, 211 dòng**
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->
| Hệ | Accuracy | TVER | wrong_version | Phủ trích dẫn |
|---|---|---|---|---:|
| `b1` | 0,000 [0,000; 0,000] | — | 0,000 [0,000; 0,000] | 0,000 |
| `b2ctx` | 0,474 [0,408; 0,543] | 0,471 [0,401; 0,538] | 0,291 [0,184; 0,400] | 0,995 |
| `b5` | 0,479 [0,413; 0,547] | 0,471 [0,401; 0,538] | 0,291 [0,184; 0,400] | 0,995 |
| `b7` | 0,640 [0,572; 0,706] | 0,133 [0,090; 0,177] | 0,109 [0,037; 0,196] | 0,995 |
| `b7pp` | 0,635 [0,564; 0,706] | 0,000 [0,000; 0,000] | 0,036 [0,000; 0,091] | 0,995 |
| `proposed` | 0,654 [0,585; 0,721] | 0,005 [0,000; 0,015] | 0,036 [0,000; 0,091] | 0,991 |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

**Bảng 7. Test 2 (nhãn LLM), 227 dòng**
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->
| Hệ | Accuracy | TVER | wrong_version | Phủ trích dẫn |
|---|---|---|---|---:|
| `b1` | 0,000 [0,000; 0,000] | — | 0,000 [0,000; 0,000] | 0,000 |
| `b2ctx` | 0,150 [0,108; 0,195] | 0,682 [0,611; 0,748] | 0,210 [0,151; 0,273] | 0,982 |
| `b5` | 0,150 [0,110; 0,193] | 0,709 [0,640; 0,774] | 0,215 [0,157; 0,278] | 0,982 |
| `b7` | 0,308 [0,242; 0,379] | 0,219 [0,166; 0,273] | 0,077 [0,039; 0,119] | 0,987 |
| `b7pp` | 0,317 [0,241; 0,396] | 0,000 [0,000; 0,000] | 0,010 [0,000; 0,026] | 0,987 |
| `proposed` | 0,335 [0,262; 0,411] | 0,013 [0,000; 0,031] | 0,005 [0,000; 0,016] | 0,987 |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

**Bảng 8. Accuracy theo nhóm, v1.0** (T3 chỉ có 4 lineage)
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->
| Hệ | T1 | T2 | T3 | T6 |
|---|---:|---:|---:|---:|
| `b5` | 0,634 | 0,304 | 0,083 | 0,267 |
| `b7` | 0,724 | 0,609 | 0,583 | 0,367 |
| `b7pp` | 0,699 | 0,674 | 0,583 | 0,333 |
| `proposed` | 0,699 | 0,761 | 0,583 | 0,333 |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

**Bảng 9. Accuracy theo nhóm, test 2 (nhãn LLM)**
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->
| Hệ | T2 | T3 | T6 |
|---|---:|---:|---:|
| `b5` | 0,175 | 0,093 | 0,188 |
| `b7` | 0,350 | 0,253 | 0,281 |
| `b7pp` | 0,325 | 0,320 | 0,281 |
| `proposed` | 0,392 | 0,267 | 0,281 |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

### 6.3. Kiểm định xác nhận
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

**Bảng 10. v1.0**
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->
| Mã | So sánh, đại lượng | Ước lượng [KTC 95%] | p Holm | Dòng/lineage | Kết luận |
|---|---|---|---:|---|---|
| XN1 | `b7pp` − `b7`, TV-R@1 | +0,051 [+0,021; +0,088] | 0,0008 | 196/165 | ủng hộ |
| XN2 | `b7pp` − `b7`, TVER | -0,133 [-0,179; -0,090] | < 0,0001 | 211/165 | ủng hộ |
| XN3 | `b7` − `b2ctx`, TV-R@1 | +0,138 [+0,089; +0,191] | < 0,0001 | 196/165 | ủng hộ |
| XN4 | `b7plus` − `b7`, TV-R@1 | +0,051 [+0,020; +0,087] | 0,0008 | 196/165 | ủng hộ |
| XN8 | `proposed` − `b5`, Accuracy | +0,175 [+0,115; +0,234] | < 0,0001 | 211/165 | ủng hộ |
| XN9 | `b2ctx` − `b1`, Accuracy | +0,474 [+0,409; +0,542] | < 0,0001 | 211/165 | ủng hộ |
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

**Bảng 11. Test 2 (nhãn LLM)**
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->
| Mã | So sánh, đại lượng | Ước lượng [KTC 95%] | p Holm | Dòng/lineage | Kết luận |
|---|---|---|---:|---|---|
| XN1 | `b7pp` − `b7`, TV-R@1 | +0,028 [-0,014; +0,072] | 0,4596 | 211/101 | không đủ bằng chứng |
| XN2 | `b7pp` − `b7`, TVER | -0,219 [-0,273; -0,165] | < 0,0001 | 227/101 | ủng hộ |
| XN3 | `b7` − `b2ctx`, TV-R@1 | +0,047 [+0,023; +0,078] | < 0,0001 | 211/101 | ủng hộ |
| XN4 | `b7plus` − `b7`, TV-R@1 | +0,028 [-0,014; +0,072] | 0,4596 | 211/101 | không đủ bằng chứng |
| XN8 | `proposed` − `b5`, Accuracy | +0,185 [+0,127; +0,246] | < 0,0001 | 227/101 | ủng hộ |
| XN9 | `b2ctx` − `b1`, Accuracy | +0,150 [+0,109; +0,195] | < 0,0001 | 227/101 | ủng hộ |
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

Theo quy tắc khai báo: H0 được ủng hộ trên v1.0. Trên test 2 (nhãn LLM), XN1 không được ủng hộ nên đi vào nhánh "điểm quyết định B7", một kết quả đã khai báo trước. XN2, XN3, XN8, XN9 cùng chiều và cùng được ủng hộ ở cả hai bộ. XN1 và XN4 cùng chiều nhưng trên test 2 (nhãn LLM) không đủ bằng chứng, nên **không gọi là đã lặp lại**.
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

XN5 (lan truyền trên T6 có nút cha bị bãi bỏ) chưa có. [CHỜ COLAB: `b7plus` có sinh câu trả lời trên hai vòng thử]
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

### 6.4. Chênh lệch đến từ đâu (mô tả, ngoài họ)
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

**Bảng 12. v1.0**
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->
| Bước | Accuracy | TVER | wrong_version |
|---|---|---|---|
| `b5` − `b2ctx` (thêm mở rộng, không có thời gian) | +0,005 [+0,000; +0,015] | +0,000 [+0,000; +0,000] | +0,000 [+0,000; +0,000] |
| `b7` − `b5` (thêm lọc ngày văn bản, bỏ mở rộng) | +0,161 [+0,104; +0,217] | -0,338 [-0,405; -0,270] | -0,182 [-0,309; -0,053] |
| `b7pp` − `b7` (sang lớp phiên bản, lọc lan truyền) | -0,005 [-0,033; +0,023] | -0,133 [-0,177; -0,090] | -0,073 [-0,167; +0,000] |
| `proposed` − `b7pp` (thêm mở rộng và Verifier) | +0,019 [+0,005; +0,039] | +0,005 [+0,000; +0,015] | +0,000 [+0,000; +0,000] |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

**Bảng 13. Test 2 (nhãn LLM)**
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->
| Bước | Accuracy | TVER | wrong_version |
|---|---|---|---|
| `b5` − `b2ctx` | +0,000 [-0,013; +0,013] | +0,027 [+0,005; +0,054] | +0,005 [+0,000; +0,016] |
| `b7` − `b5` | +0,159 [+0,107; +0,212] | -0,490 [-0,563; -0,417] | -0,138 [-0,203; -0,075] |
| `b7pp` − `b7` | +0,009 [-0,036; +0,055] | -0,219 [-0,273; -0,166] | -0,067 [-0,108; -0,031] |
| `proposed` − `b7pp` | +0,018 [-0,026; +0,058] | +0,013 [+0,000; +0,031] | -0,005 [-0,024; +0,011] |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

Trên cả hai bộ, Accuracy tăng chủ yếu ở bước `b7` − `b5`. Bước `b7pp` − `b7` có khoảng Accuracy chứa 0, nhưng TVER giảm rõ. `b7` và `b5` còn khác nhau ở việc mở rộng, nên đây là phân rã mô tả, không phải nhận diện nhân quả của riêng bộ lọc. [CHỜ COLAB: ablation `a1 a2 a3 a4` trên v1.0]
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json -->

### 6.5. Những thất bại cần nêu thẳng
<!-- nguồn: runs/E3_v1/test/b1.jsonl; runs/E3_test2/test/b1.jsonl; scripts/paper/paper_values.py -->

**Nhận diện bãi bỏ.** Trên v1.0, mọi hệ đều đúng 0/15 dòng bãi bỏ. Trên test 2 (nhãn LLM), mỗi hệ đúng 0 đến 1 trên 16 dòng. TVER gần 0 của `b7pp` không mâu thuẫn với điều này: không trích bản hết hiệu lực khác với biết rằng quy định đã hết hiệu lực.
<!-- nguồn: runs/E3_v1/test/b1.jsonl; runs/E3_test2/test/b1.jsonl; scripts/paper/paper_values.py -->

**Baseline không truy xuất.** `b1` để trống 182/196 câu có đáp án trên v1.0 và 208/211 trên test 2 (nhãn LLM). Vì vậy XN9 chủ yếu cho thấy generator này gần như không trả lời khi không có căn cứ, không phải LLM nói chung kém.
<!-- nguồn: runs/E3_v1/test/b1.jsonl; runs/E3_test2/test/b1.jsonl; scripts/paper/paper_values.py -->

### 6.6. Phân rã lỗi do máy (thăm dò)
<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

**Bảng 14. v1.0**
<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->
| Hệ | Có căn cứ đúng trong top 20 | Đúng khi prompt đã có căn cứ | Sai tổng | Bãi bỏ | Thiếu điều khoản | Đọc sai |
|---|---|---|---:|---:|---:|---:|
| `b7` | 178/211 = 0,844 | 135/178 = 0,758 | 76 | 15 | 19 | 39 |
| `b7pp` | 177/211 = 0,839 | 134/177 = 0,757 | 77 | 15 | 19 | 41 |
| `proposed` | 177/211 = 0,839 | 138/177 = 0,780 | 73 | 15 | 19 | 38 |
<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

**Bảng 15. Test 2 (nhãn LLM)**
<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->
| Hệ | Có căn cứ đúng trong top 20 | Đúng khi prompt đã có căn cứ | Sai tổng | Bãi bỏ | Thiếu điều khoản | Đọc sai |
|---|---|---|---:|---:|---:|---:|
| `b7` | 118/227 = 0,520 | 67/118 = 0,568 | 157 | 21 | 72 | 43 |
| `b7pp` | 120/227 = 0,529 | 70/120 = 0,583 | 155 | 20 | 86 | 41 |
| `proposed` | 120/227 = 0,529 | 74/121 = 0,612 | 151 | 19 | 85 | 40 |
<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

Mỗi lỗi chỉ vào một tầng theo thứ tự ưu tiên, nên đây là phân bổ, không phải nguyên nhân duy nhất. Ở v1.0, lỗi lớn nhất là đọc sai khi đã có căn cứ. Ở test 2 (nhãn LLM), lỗi lớn nhất là không tìm được điều khoản. [CHỜ G4: E7 người gán]
<!-- nguồn: docs/reports/e7_phan_ra_loi.md -->

### 6.7. Bảng kết quả chính trên bộ test cuối — chưa chạy
<!-- nguồn: docs/plans/active/master-plan.md -->

Bảng này chỉ được điền sau khóa dữ liệu G2, khóa hệ và amendment G3, rồi chạy G4. Các đầu ra Colab bổ sung cho vòng thử không được dùng để chọn cấu hình cuối. Tầng nhãn người là cơ sở bảng chính; nhãn LLM/agent trình bày riêng.
<!-- nguồn: docs/plans/active/master-plan.md -->

| Câu hỏi / phép đo | Kết quả chính | Loại |
|---|---|---|
| RQ1, RAG và LLM không truy xuất | [CHỜ G4: sai phiên bản, độ phủ, mẫu số và KTC] | Mô tả |
| RQ2, `proposed2` − `b4`, `proposed2` − `b5` | [CHỜ G4: Accuracy, KTC và phán quyết] | Xác nhận sau amendment |
| RQ3 / giả thuyết, thang cấp lọc | [CHỜ G4: TV-Recall và TVER kèm gold mù] | Xác nhận sau amendment |
| T6 lan truyền và thành phần | [CHỜ G4: cỡ lát và kết quả] | Theo điều kiện đã khóa |
| Nhóm, miền, E7 và giám khảo | [CHỜ G4: bảng mô tả và hiệu chuẩn] | Mô tả / thăm dò |
<!-- nguồn: docs/plans/active/master-plan.md, mục 6 -->

## 7. Thảo luận
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

**Phân rã vòng thử gợi ý vai trò của lọc thời gian.** Trên cả hai bộ, đưa ràng buộc thời gian vào truy xuất đi cùng chênh lệch Accuracy lớn nhất. Bản thân bộ lọc cấp văn bản đơn giản đã nằm rất gần đỉnh thang về Accuracy. Đây là mô tả cấu hình đã đo, chưa cô lập nguyên nhân hoặc chứng minh khả năng khái quát sang bộ cuối.

**Biểu diễn phiên bản cần được đọc theo từng chỉ số.** Trên toàn tập, bước `b7pp` − `b7` không tách được về Accuracy, song TVER giảm rõ trên cả hai bộ. TVER gần 0 một phần là **do thiết kế**, vì bộ lọc đã loại bản hết hiệu lực, nên nó không nên là con số chính. wrong_version đo nội dung câu trả lời nên có ý nghĩa hơn. Nó giảm rõ trên test 2 (nhãn LLM), còn trên v1.0 khoảng tin cậy chạm 0, mẫu số chỉ 55 dòng, và chỉ số này nằm ngoài họ kiểm định.
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

**Toàn tập có thể che bớt tác dụng ở nhóm nhạy thời gian.** T1 là nhóm đối chứng, chiếm 123/211 dòng của test v1.0, và lớp phiên bản không có lợi ở đó (`b7` 0,724, `b7pp` 0,699). Riêng ở T2, hiệu `proposed` − `b7pp` có khoảng không chứa 0 trên cả hai bộ: +0,087 [+0,022; +0,174] trên v1.0 và +0,067 [+0,017; +0,117] trên test 2 (nhãn LLM). Đây là dấu hiệu thăm dò cần kiểm trên bộ cuối. Tuy nhiên, đây là so sánh thăm dò, ngoài họ kiểm định, được chọn sau khi thấy số và chưa hiệu chỉnh đa so sánh. Ở T3, hiệu này là +0,000 [+0,000; +0,000] trên v1.0 và -0,053 [-0,147; +0,027] trên test 2 (nhãn LLM). Hiệu `b7pp` − `b7` ở T2 cũng chưa nhất quán: +0,065 [-0,022; +0,152] trên v1.0 và -0,025 [-0,083; +0,042] trên test 2 (nhãn LLM). [CHỜ COLAB: ablation `a2`, tức bỏ riêng phần mở rộng]
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

**Về đồ thị, chỉ được nói hẹp.** Trên toàn tập, mở rộng một bước gần như không đổi Accuracy khi không có thời gian (`b5` − `b2ctx`), và thêm rất ít khi có thời gian (`proposed` − `b7pp`). Kết luận này chỉ áp dụng cho kiểu mở rộng đã đo, và ở T2 có dấu hiệu ngược lại như nêu trên. Vai trò ngoại tuyến của đồ thị (dựng chuỗi, tính khoảng hiệu lực) lại là nền của các hệ lớp B. Bài này không đánh giá GraphRAG nói chung.
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

**Nhận diện bãi bỏ là khoảng trống rõ nhất.** Bộ lọc giúp hệ không trích bản cũ, nhưng generator không chuyển điều đó thành câu trả lời "đã hết hiệu lực". Đây là bài toán mở, và benchmark đo được nó.

**Khoảng cách lớn giữa hai bộ chưa được giải thích.** Mức Accuracy của `proposed` trên hai bộ khác nhau nhiều, kể cả khi so cùng nhóm. Một giả thuyết cần kiểm là mức trùng chữ của câu hỏi: truy xuất từ vựng phụ thuộc các từ khớp lời văn. Chưa có phép đo lưu file đủ để đưa số này vào bản nháp. Thành phần nhóm, nguồn nhãn và loại văn bản cũng khác nhau. **Chưa đo độ chính xác theo mức trùng chữ, và chưa có truy xuất dense trên test để đối chứng.** [CẦN: phân tích theo mức trùng chữ, ghi là thăm dò]

**Quy trình nhãn LLM đã thử chưa đạt cổng so với người.** Cả lời dặn bản 2 viết kỹ, gán đôi và hòa giải vẫn chưa đạt cổng. Trên mẫu hiệu chuẩn, hai model có 8 câu cùng sai so với nhãn người, nên hai model đồng ý với nhau chưa có nghĩa là đúng.
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

## 8. Giới hạn và nguy cơ
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

- **Gold và hệ dùng chung kho.** Khi kho bỏ sót một lần sửa đổi, hệ và gold có thể cùng sai mà vẫn khớp nhau. Gold độc lập theo kiểm kê vẫn trống và M2 chưa đạt. TVER bằng không của `b7pp` phần lớn do cách dựng gold và bộ lọc cùng mô hình, chưa chứng minh độ đúng pháp lý. Đây là nguy cơ lớn nhất của cả bài.
- **Chất lượng nhãn.** Đồng thuận người gán thấp ở v1.0, nhãn agent chiếm 90/211 dòng test, test 2 (nhãn LLM) chưa có người kiểm.
- **Mẫu nhỏ ở các nhóm quan trọng.** Trên test v1.0, T3 có 4 lineage và T6 có 15 lineage. T1 chiếm 123/211 dòng.
- **Một generator cỡ nhỏ.** Mọi kết luận gắn với Qwen3-4B. Dao động bằng 0 mới đo trên dev (553/553 dòng), chưa đo khi đổi phần cứng hoặc thư viện.
- **Chỉ truy xuất từ vựng.** Dense và hybrid chưa có số trên test.
- **Chưa đủ điều kiện gọi là "cải thiện".** Theo tiêu chí của dự án còn thiếu: oracle context trên test, gold độc lập, các chế độ `as_of` khác ở tầng sinh, và phép bỏ từng nhóm. Vì vậy bài dùng "chênh lệch" thay cho "cải thiện".
- **Câu hỏi do LLM viết.** Theo `questions.jsonl`, 145/165 câu hỏi test v1.0 do Claude Opus 5.5 viết và 20 câu do DeepSeek viết. Bước chọn lọc cũng có thể thiên về câu dễ diễn đạt.
- **Phép chấm dựa trên đoạn chữ.** Accuracy không phải đánh giá ngữ nghĩa của người, và chưa có giám khảo được hiệu chuẩn.
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

## 9. Kết luận
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

Hai vòng thử cung cấp dấu hiệu về lỗi sai phiên bản và vai trò của lọc thời gian, đồng thời bộc lộ giới hạn của nhãn, gold và nhận diện bãi bỏ. Mở rộng quan hệ được đo chỉ ở một bước; chưa có cơ sở kết luận về mọi kiến trúc đồ thị. Bài đi theo hướng tài nguyên và phép đo có đối chứng; hệ đề xuất không phải thắng mới có thể báo cáo. [CHỜ G4: kết luận chính dựa trên bộ test cuối do người kiểm và gold mù; chưa khẳng định ưu thế phương pháp].
<!-- nguồn: runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json; docs/plans/active/master-plan.md -->

## Khai báo

- **Dữ liệu và mã nguồn:** ViLexTime v1.0 mang giấy phép CC-BY-4.0 (`data/vilextime/LICENSE`). [CẦN: chốt nơi công khai và thời điểm theo quy định ẩn danh của hội nghị]
- **Đạo đức:** không có đối tượng nghiên cứu là người dùng cuối; có người gán nhãn và luật sư. [CẦN: GVHD xác nhận có cần thủ tục không; thống nhất cách nêu tên hay ẩn danh luật sư]
- **Đóng góp tác giả (CRediT):** [CẦN: nhóm điền]
- **Xung đột lợi ích, tài trợ:** [CẦN: nhóm điền]
- **Sử dụng AI:** Claude và DeepSeek viết câu hỏi; Claude chọn đáp án ngắn; Codex gán nhãn agent; Sonnet, Codex và Opus gán và hòa giải nhãn của test 2 (nhãn LLM); Claude và Codex tham gia viết mã, phân tích và soạn tài liệu; Qwen là generator được đánh giá. **Bản nháp ban đầu do Claude Opus 5.5 soạn; Codex cập nhật ngày 05/11 theo C9, dùng file cục bộ, chưa có lượt người duyệt hoặc kiểm Claude độc lập cho bản cập nhật.** [CẦN: đối chiếu quy định AI của hội nghị và của UIT]
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

## Tài liệu tham khảo

*Danh sách lấy từ `references.bib`. Cột mức đọc chỉ để nhóm theo dõi, phải bỏ trước khi nộp.*

| Tài liệu | Mức đọc hiện tại |
|---|---|
| [akarajaradwong2026nitibenchplus] Akarajaradwong, Pawitsapak; Nutanong, Sarana; Chaksangchaichot, Chompakorn (2026). NitiBench+: A Temporal Thai Legal Question Answering Benchmark Across 17 Domains. arXiv:2611.03576. | Hồ sơ AI 05/11: arXiv v2; một phần: p.1-7, p.10-14, p.27; chưa xác nhận phản biện |
| [cymbler2026fiscalqa] Cymbler, Rose; Guez, Daniel; Fabre, Laurent (2026). Temporal Misgrounding in Legal RAG: A Versioned-Corpus Benchmark for French Tax Law. arXiv:2608.09393. | Đã đọc một số mục của PDF: Introduction, Nugget-Based Scoring, Experimental Design, phụ lục artifact. Chưa đọc toàn văn |
| [demartim2025satgraph] de Martim, Hudson (2025). An Ontology-Driven Graph RAG for Legal Norms: A Hierarchical, Temporal, and Deterministic Approach. Legal Knowledge and Information Systems. | Đã đọc một số mục của bản arXiv v5: Proposed Framework, Case Study, Discussion; chưa đối soát bản kỷ yếu |
| [dong2026vietlegal] Dong, Nguyen Tien; Nguyen, Minh-Anh; Hoang, Thanh Dat và cộng sự (2026). Benchmarking Vietnamese Legal Knowledge of Large Language Models. arXiv:2512.14554. | Hồ sơ AI 05/11: tìm từ khóa và đọc đoạn arXiv v5, v7; repo giữ v5; chưa đọc đầy đủ |
| [dror2018hitchhiker] Dror, Rotem; Baumer, Gili; Shlomov, Segev và cộng sự (2018). The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing. Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). | Hồ sơ AI 05/11: ACL Anthology; đọc thân bài, chưa đọc phụ lục; không bàn Holm hay bootstrap theo cụm |
| [edge2024graphrag] Edge, Darren; Trinh, Ha; Cheng, Newman và cộng sự (2025). From Local to Global: A GraphRAG Approach to Query-Focused Summarization. arXiv:2404.16130. | Hồ sơ AI 05/11: arXiv v2 (2025-02-19); một phần: tóm tắt, p.3, p.8-9, tìm từ khóa; tiêu đề theo v2 |
| [guo2025lightrag] Guo, Zirui; Xia, Lianghao; Yu, Yanhua và cộng sự (2025). LightRAG: Simple and Fast Retrieval-Augmented Generation. Findings of the Association for Computational Linguistics: EMNLP 2025. | Hồ sơ AI 05/11: ACL Anthology; một phần: tóm tắt, p.4-6, p.9 |
| [gwet2008ac1] Gwet, Kilem Li (2008). Computing Inter-Rater Reliability and Its Variance in the Presence of High Agreement. British Journal of Mathematical and Statistical Psychology. | Hồ sơ AI 05/11: PubMed; chỉ tóm tắt; PDF tác giả trả HTTP 404, chưa đọc toàn văn |
| [huwiler2025versionrag] Huwiler, Daniel; Stockinger, Kurt; Fürst, Jonathan (2025). VersionRAG: Version-Aware Retrieval-Augmented Generation for Evolving Documents. arXiv:2510.08109. | Hồ sơ AI 05/11: arXiv v1; đọc thân bài, chưa đọc phụ lục; tài liệu kỹ thuật, chưa ánh xạ ngày lịch |
| [nguyen2025vlqa] Nguyen, Tan-Minh; Nguyen, Hoang-Trung; Dao, Trong-Khoi và cộng sự (2025). VLQA: The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering. arXiv:2507.19995. | Đã đọc một số mục của PDF: Dataset Construction, Expert Annotation; cần xác nhận nơi công bố |
| [nguyen2026vihermes] Nguyen, Long S. T.; Bui, Quan M.; Ngo, Tin T. và cộng sự (2026). ViHERMES: A Graph-Grounded Multihop Question Answering Benchmark and System for Vietnamese Healthcare Regulations. Intelligent Information and Database Systems. | Đã đọc một số mục của PDF arXiv: SRKG, Seeded Retrieval and Propagation, Conclusion; metadata LNCS theo Crossref, chưa đối soát toàn văn bản LNCS |
| [nguyen2026vilegalexpert] Nguyen, Dat Tien; Nguyen, Nghia Hieu; Nguyen, Anh Thi-Hoang và cộng sự (2026). ViLegalExpert: A Large-Scale Benchmark for Vietnamese Legal Retrieval and Question Answering from Real-World Consultations. arXiv:2609.39189. | Hồ sơ AI 05/11: arXiv v1, đọc p.1-6 và tìm từ khóa; chưa đọc đầy đủ |
| [prior2025consolidation] Prior, Max; Hof, Adrian; Wais, Niklas và cộng sự (2025). Risks and Limits of Automatic Consolidation of Statutes. Proceedings of the Natural Legal Language Processing Workshop 2025. | Hồ sơ AI 05/11: ACL Anthology; đọc thân bài, chưa đọc phụ lục |
| [prior2026oldfriend] Prior, Max; Schultz, Andreas; Grabmair, Matthias (2026). Asking For An Old Friend: Diagnosing and Mitigating Temporal Failure Modes in LLM-based Statutory Question Answering. arXiv:2605.23497. | Hồ sơ AI 05/11: arXiv v2 (2026-09-25); đọc thân bài, chưa đọc phụ lục; arXiv ghi accepted as full paper at ICAIL 2026, nominated for Best Paper Award; ACM DL bị chặn, chưa xác minh bản kỷ yếu, giữ misc |
| [yao2026lawinforce] Yao, Yuchen; Hu, Yiran; Zhang, Kaixiang và cộng sự (2026). When the Correct Law Still Fails: A Diagnostic Benchmark for Law-in-Force Retrieval in Versioned Legal RAG. Proceedings of IJCNLP-AACL 2026 (Volume 1: Long Papers). | Hồ sơ AI 05/11: đọc thân bài; chưa đọc phụ lục |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

---

# Phần C. Reviewer sẽ hỏi gì

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->
| # | Câu hỏi | Hiện trả lời được gì | Cần làm |
|---|---|---|---|
| 1 | Gold lấy từ chính kho của hệ, vậy kết quả có vòng lặp không? | Có khai báo, chưa có đối chứng độc lập | E6 khoảng 120 dòng, M2 |
| 2 | Nhãn test 2 đáng tin đến đâu? | Chưa có số đo; lời dặn v2 không đạt cổng | Người kiểm một mẫu test 2 |
| 3 | Đồng thuận AC1 0,377 thì v1.0 có dùng được không? | Có quy tắc chọn nhãn và mẫu luật sư 43/50; số vẫn thấp | Trình bày thẳng; cân nhắc báo riêng theo nguồn nhãn |
| 4 | Sao không so với GraphRAG hay LightRAG? | Không có | Chạy E4 trên tập con, hoặc thu hẹp kết luận (bản nháp đã thu hẹp) |
| 5 | Dense ở đâu? BM25 có phải baseline quá yếu? | Chưa có số test | Colab đợt bổ sung; bộ cuối sau G3 |
| 6 | TVER gần 0 có phải hiển nhiên do bộ lọc? | Đúng một phần | Không để TVER làm số chính; báo cùng wrong_version và kết quả theo nhóm |
| 7 | Generator 4B có quá nhỏ không? | Chưa có model thứ hai | Thêm một generator, viết amendment trước |
| 8 | Có chắc là đóng góp mới? | Khảo sát có log 05/11 (`related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md`); LawInForce-eCFR và NitiBench+ rất gần; nhiều chỉ mục bị chặn | Chạy lại phần bị chặn, đọc các bài chưa mở |
| 9 | Vì sao hai bộ chênh nhau nhiều vậy? | Mới có giả thuyết | Phân tích theo mức trùng chữ |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

# Phần D. Việc cần làm để nộp được

**Chặn nộp:**

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->
| Việc | Ai làm | Phụ thuộc |
|---|---|---|
| Gold độc lập (E6) và kiểm mẫu test 2 | Luật sư, người trong nhóm | Mình soạn phiếu |
| Colab đợt 2 (v1.0, test 2) và lần chạy cuối ở G4 | Nhóm | Đợt 2 chạy được ngay; lần cuối chờ G1–G3 của `docs/plans/active/master-plan.md` |
| Đọc nguồn còn thiếu; khảo sát có log | Nhóm, mình hỗ trợ | Cần tác giả tự đọc |
| M2 hoặc khai báo chưa đạt | Nhóm | Truy vấn đối chiếu tay |
| Rà hướng A và chốt hội nghị | Nhóm, GVHD | Bản nháp C9 theo hướng A, chưa phải quyết định nộp |
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

**Nên có:** E7 do người gán; phân tích theo mức trùng chữ; bỏ từng nhóm và các chế độ `as_of`; LightRAG trên tập con; generator thứ hai; hiệu chuẩn LLM-as-judge.
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

# Phần E. Nguồn số liệu

Mọi số trong bảng và phần lớn số trong câu do `scripts/paper/paper_build.py` đọc trực tiếp từ các file dưới đây. `scripts/paper/paper_check.py` đối chiếu Bảng 6, 7, 10, 11 và quy mô kho với chương 3, 6, quét câu chữ cấm, và phải bắt được ba lỗi cấy sẵn. Chạy từ thư mục gốc của repo. Chưa có lượt phản biện độc lập.
<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->
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
| Mức trùng chữ | [CẦN: lưu phép đo thành file; đã bỏ số chỉ từng in màn hình khỏi bài] |
| Kiểm chất lượng kho, agent, luật sư | `docs/thesis/chuong-3…`, `chuong-4…`; nguồn gốc ghi trong chú thích của từng chương |

<!-- nguồn: runs/E3_v1/test/all.score.json; runs/E3_test2/rescore/all.score.json; data/review/test2_llm_v2/calib_score.json; docs/plans/active/master-plan.md -->