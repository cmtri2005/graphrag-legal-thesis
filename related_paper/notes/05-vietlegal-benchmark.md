# Benchmarking Vietnamese Legal Knowledge of Large Language Models (VietLegal / VLegal-Bench)

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/2512.14554v5.pdf` (31 trang, kể cả phụ lục). Bảng số liệu lấy từ văn bản trích xuất PDF; số trong bảng chi tiết theo từng mô hình ở các phụ lục (Bảng 5–11) chỉ được tóm tắt, không chép hết.

## 0. Thông tin chung

| Mục | Nội dung |
|---|---|
| Tác giả | Nguyen Tien Dong\*, Minh-Anh Nguyen\* (đồng tác giả chính), Thanh Dat Hoang, Nguyen Tuan Ngoc, Dao Xuan Quang Minh, Phan Phi Hai, Nguyen Thi Ngoc Anh†, Binh Vu† (đồng tác giả cuối). CMC OpenAI, VinUniversity, HUST, SRH University Heidelberg |
| Nơi đăng | arXiv:2512.14554v5 [cs.CL], 17/04/2026 (bản v5, nhiều lần chỉnh sửa; ACL-style) |
| Mã nguồn | github.com/CMC-OPENAI/VLegal-Bench (kho ẩn danh khi nộp) |
| Quy mô | **10.450 mẫu** do chuyên gia chú giải, **22 tác vụ**, **5 cấp nhận thức**, đánh giá **23 LLM** |
| Độ gần với ViLexTime | Trung bình: là benchmark tiếng Việt lớn nhất về kiến thức pháp luật; có tác vụ thời gian/sửa đổi (Task 1.5) và phân tích lỗi "mù thời điểm" (recency blindness), nhưng **không** mô hình hóa hiệu lực theo ngày |

## 1. WHY – Bài toán

- Benchmark pháp lý hiện có chủ yếu cho **common law, tiếng Anh**, thiên về lập luận theo án lệ (LexGLUE, LegalBench, CaseHOLD). **Civil law** (cai quản hơn 60% khu vực tài phán, nguồn thẩm quyền là các đạo luật có thứ bậc) chưa được phục vụ tốt: cần diễn giải đạo luật phức tạp và **theo dõi hiệu lực theo thời gian qua các lần sửa đổi thường xuyên**.
- Luật Việt Nam khó vì phụ thuộc vào các tham chiếu chồng chéo giữa Điều, Khoản, Điểm → cần đánh giá chuyên biệt để bảo đảm trung thành pháp lý. Pháp luật Trung Quốc đã có LawBench, LexEval, LAiW; các nền luật thành văn khác (Việt Nam) còn thiếu.
- NLP pháp lý tiếng Việt đến nay do cộng đồng/shared task dẫn dắt (VLSP) với các bộ dữ liệu cho truy hồi, kéo theo văn bản (entailment), QA; mô hình tiền huấn luyện (PhoBERT, ViT5). Tài nguyên **rời rạc, thiên truy hồi/trích xuất**; ít đánh giá sinh văn bản, suy luận nhiều bước hay **theo dõi sửa đổi lập pháp**. Chưa có chuẩn đánh giá thống nhất cho hệ trợ lý pháp lý thực tế.
- Đóng góp: (1) benchmark VietLegal có thiết kế có thể tái lập cho các nền civil law khác; (2) phương pháp đánh giá "cognitively grounded" theo **Bloom's taxonomy**; (3) 10.450 mẫu xác minh bởi chuyên gia + thực nghiệm 23 LLM.

## 2. HOW – Thiết kế benchmark

### 2.1 Khung năm cấp nhận thức (Bloom) – 22 tác vụ (Bảng 1)
Năm loại mẫu câu hỏi: MCQ (trắc nghiệm), MLC (phân loại đa nhãn), BC (phân loại nhị phân), NER, Generation.

**Cấp 1 – Nhận biết & Ghi nhớ** (kiến thức nền, thực thể/khái niệm/điều luật):
| ID | Tác vụ | Dạng | Chỉ số | Số mẫu test |
|---|---|---|---|---|
| 1.1 | Nhận dạng thực thể pháp lý (người, tổ chức, số tiền...) | MCQ, NER | Accuracy, EM | 750 |
| 1.2 | Phân loại chủ đề pháp lý | MCQ, MLC | Accuracy, Macro-F1 | 700 |
| 1.3 | Nhớ khái niệm/định nghĩa pháp lý | MCQ | Accuracy | 300 |
| 1.4 | Nhớ điều luật (trích đúng điều tương ứng thuật ngữ/khái niệm/câu hỏi) | MCQ | Accuracy | 1.000 |
| **1.5** | **Nhớ lược đồ pháp lý: nhận ra quan hệ phân cấp và thời gian giữa các văn bản (sửa đổi, thay thế...)** | MCQ | Accuracy | **800** |

**Cấp 2 – Hiểu & Cấu trúc hóa**: 2.1 Trích xuất quan hệ (chủ thể, đối tượng, nội dung) – MCQ – 253; 2.2 Nhận dạng thành phần quy phạm (giả định, quy định, chế tài) – MCQ – 300; 2.3 Cấu trúc đồ thị pháp lý (chuyển văn bản thành KG có thực thể, quan hệ, tham chiếu liên điều) – Generation, MLQ – ROUGE-L, Node-F1, Edge-F1 – 296; 2.4 Thẩm định phán quyết – BC – 600; 2.5 Hiểu ý định người dùng – MLC – macro-F1 – 1.359.

**Cấp 3 – Suy luận & Suy diễn**: 3.1 Dự đoán điều/khoản áp dụng từ câu hỏi ngắn (không phải tình huống dài) – MCQ – 600; 3.2 Dự đoán phán quyết – MCQ – 600; 3.3 Lập luận nhiều điều – MCQ – 292; 3.4 Phát hiện mâu thuẫn/chồng chéo giữa các quy định – BC, Binary F1 – 161; 3.5 Ước lượng chế tài/biện pháp khắc phục – MCQ – 358.

**Cấp 4 – Diễn giải & Sinh văn bản**: 4.1 Tóm tắt văn bản pháp lý (ROUGE-L, 384); 4.2 Sinh lập luận tư pháp theo mẫu **IRAC** (Issue–Rule–Application–Conclusion) (ROUGE-L, 299); 4.3 Sinh ý kiến pháp lý khách quan (ROUGE-L, 498).

**Cấp 5 – Đạo đức, Công bằng, Thiên lệch**: 5.1 Phát hiện thiên lệch (giới, chủng tộc, chính trị, tôn giáo) – 250; 5.2 Quyền riêng tư và bảo vệ dữ liệu – 216; 5.3 Nhất quán đạo đức nghề nghiệp – 200; 5.4 Phát hiện điều khoản bất công trong hợp đồng – 234.

Cấp 3 và 4 nhắm các hiện tượng đặc thù civil law: phụ thuộc nhiều điều, diễn giải phân cấp giữa các văn bản, **phân tích nhất quán khi quy định chồng chéo hoặc đã sửa đổi**. Cơ sở lý thuyết: tam đoạn luận pháp lý và lý thuyết subsumption (Alexy 1989).

### 2.2 Thu thập và xử lý dữ liệu (mục 3.2, Hình 1)
- Nguồn: cổng thông tin chính phủ và kho hỏi đáp của văn phòng luật; khoảng **55.000 văn bản do trung ương ban hành, đang có hiệu lực** (HTML parsing + OCR). Sau khử trùng và trích metadata dựng hai tài nguyên: (1) **Knowledge Graph Database** mã hóa phân cấp Điều–Khoản–Điểm; (2) **Legal Corpus Database** cho truy hồi quy mô lớn. Quy trình: Legal Resources → Preprocess (HTML parse, OCR, legal schema extraction, deduplicate, normalize, tokenization, extract metadata) → Corpus DB + KG DB → post-process & feature extraction (topic classification, citation extraction, precedent graph feature) → xuất dữ liệu có cấu trúc.
- Công cụ tìm kiếm văn bản pháp lý để chuyên gia định vị Điều/Khoản/Điểm/chủ đề; công cụ chú giải tự xây (Hình 4–5) cho junior gắn điều luật do senior chọn.
- Ví dụ mẫu (Hình 1): tình huống K say rượu định đánh nhưng không trúng rồi rủ bạn đập phá cửa hàng → đáp án dựa vào **Điều 134 Bộ luật Hình sự 2015** ("cố gắng đánh nhưng không gây thương tích không phải tội; xúi giục hoặc rủ người khác gây rối trật tự công cộng thì bị xử lý").

### 2.3 Quy trình chú giải (mục 3.2 và Phụ lục B, E)
- **Nhân sự**: 3 senior (luật sư có giấy phép ≥5 năm, chuyên ít nhất một lĩnh vực dân sự/hình sự/hành chính/thương mại, có kinh nghiệm giảng dạy) + 8 junior (luật sư hoặc sinh viên luật năm cuối đã đỗ kỳ thi luật sư, 1–3 năm kinh nghiệm), tuyển qua 2 văn phòng luật và 1 khoa luật.
- **Đào tạo hai ngày**: tổng quan khung nhận thức và định nghĩa tác vụ; thực hành 50 mẫu/tác vụ có phản hồi tức thì; hiệu chuẩn các ca biên; hướng dẫn quy tắc quyết định cho ca mơ hồ (ví dụ điều đã bãi bỏ nhưng còn được tham chiếu; điều khoản có nhiều cách hiểu hợp lệ). Yêu cầu ≥85% đồng thuận với nhãn vàng thí điểm trước khi vào chính thức.
- **Quy trình**: senior xác định chủ đề và nguồn thẩm quyền; hạn mức mẫu chia đều cho **hai junior độc lập (A, B)** tự dựng tình huống và đáp án (MCQ hoặc mở). **Kiểm chéo mù theo lô**: cứ 100 mẫu thì A và B đổi lô và tự trả lời câu hỏi của nhau.
- **Phương án sai (distractors)** của MCQ do luật sư có giấy phép thiết kế tay, hợp lý về pháp lý và giống bề mặt đáp án đúng.
- **Độ nhất quán**: trên 10.450 mẫu, đồng thuận ban đầu **92,39%** (9.656/10.450), **Cohen's κ = 0,89** (tính trên nhãn trước khi thảo luận). Phần bất đồng **7,61% (794 mẫu)**: 683 mẫu được hai junior giải quyết bằng đồng thuận có cấu trúc sau khi xem lại nguồn; 111 mẫu chuyển senior phân xử; tập trung ở Task 3.4 (31), Task 3.3 (27), Task 5.4 (22).
- **Công sức**: ~1.400 giờ-người trong 14 tuần, phiên tối đa 4 giờ có nghỉ, luân phiên tác vụ hàng tuần chống chuyên môn hóa quá mức; trả 150.000 VND/giờ (~6 USD), senior có thêm phụ cấp giám sát; có đồng ý tham gia cho nghiên cứu.
- Truy vấn công dân được ẩn danh (thay tên, địa chỉ, số định danh); văn bản nguồn là văn bản nhà nước công khai.

## 3. Thiết lập thí nghiệm
- **Zero-shot** (chỉ chỉ dẫn + đầu vào), **few-shot 1 ví dụ** (từ tập dev tách riêng), mỗi loại **có/không** suy luận tường minh (CoT); nhiệt độ giải mã **0**; cắt giữa (middle truncation) khi vượt cửa sổ ngữ cảnh (theo các benchmark LexEval, LAiW, LawBench).
- **Chỉ số lai**: trích xuất (Accuracy, F1, EM) cho cấp thấp; sinh (ROUGE-L) cho cấp cao; thêm đánh giá người mù đôi cho tác vụ sinh.
- **23 LLM**: đa ngôn ngữ đóng (GPT-4o, GPT-4o-mini, Claude Sonnet 4.5, Gemini 2.5 Flash), mã nguồn mở (gpt-oss-20b, Qwen2.5 72B/32B/14B/7B/3B, Llama-3.1 70B/8B, Llama-2 13B/7B, gemma-2 27B/9B, InternLM3-8B, InternLM-chat-20b) và nhóm tiếng Việt (SeaLLMs-v3 7B/1.5B, BloomVN-8B-chat, Qwen3-4b-legal-pretrain, **CMC-Legal-32B**, mô hình của nhóm tác giả).

## 4. WHAT – Kết quả chính (zero-shot, Bảng 2–3)

### 4.1 Suy giảm theo cấp nhận thức
- Cấp 1: mô hình tốt nhất đạt 80–90% trên nhận biết cơ bản. Task 1.4 (Article Recall) tốt nhất **87,91%** (CMC-Legal-32B).
- **Task 3.1 (Dự đoán điều/khoản) khó nhất**: tốt nhất chỉ **43,83%** (Qwen3-4b-legal-pretrain); Claude Sonnet 4.5 bảng ghi 59,83% ở cột Acc của Bảng 3 (số liệu của bài trong bảng; văn bản nêu 43,83% là mức tốt nhất, hai chỗ không khớp, cần kiểm khi trích). Chênh hơn 40 điểm so với nhớ điều (1.4). Nghĩa là mô hình có thể nhớ điều khi được nhắc tường minh nhưng **áp dụng để tìm điều từ truy vấn mới** thì rất khó.
- **Task 1.5 (Legal Schema Recall) là nút thắt phổ quát**: mọi mô hình **<28%** (cao nhất ~27,75%, gần mức ngẫu nhiên với 4 phương án), nêu rõ khó "mô hình hóa phân cấp pháp luật Việt Nam, sửa đổi và quan hệ thời gian".
- **Task 3.4 (Phát hiện mâu thuẫn) thất bại hệ thống**: trong 23 mô hình, **16 đạt 0,00 Y-F1**; chúng thiên lệch mạnh sang "không mâu thuẫn" (N-F1 39–46%). Chỉ ba mô hình có khả năng: CMC-Legal-32B (Y-F1 86,41), Llama-3.1-8B-Instruct (37,66), GPT-4o (27,21). (Bảng cũng ghi vài mô hình có Y-F1 cao bất thường như Llama-2-13b 85,91 với N-F1 0,00 – tức là dự đoán toàn "có", không phải năng lực.)

### 4.2 Chuyên hóa miền thắng quy mô
- CMC-Legal-32B đạt SOTA ở dự đoán phán quyết (**90,67%**), lập luận nhiều điều (**76,71%**), phát hiện mâu thuẫn (**86,41**), phát hiện điều khoản bất công (**73,50%**; hơn GPT-4o 6,17 và 15,39 điểm ở hai tác vụ sau).
- Qwen3-4b-legal-pretrain (4B tham số) tốt nhất ở dự đoán điều (43,83%) và tóm tắt (0,4361 ROUGE-L), vượt mô hình lớn gấp tới 18 lần.
- Mô hình độc quyền (GPT-4o, Claude Sonnet 4.5, Gemini 2.5 Flash) trội ở cấp 1–2, nhưng lợi thế giảm mạnh ở cấp 3–5. GPT-4o chỉ tốt nhất ở 2 tác vụ cấp cao: ước lượng chế tài (67,97%) và sinh ý kiến pháp lý (0,4975 ROUGE-L). Chênh lớn nhất so với GPT-4o: phát hiện mâu thuẫn (+59,20 điểm), dự đoán phán quyết (+6,17).
- Claude Sonnet 4.5 nổi bật ở cấu trúc hóa: 0,808 ROUGE-L trên Legal Graph Structuring (2.3) và 87,81% ở thẩm định phán quyết (2.4).
- Đạo đức: nhất quán đạo đức (5.3) thường >85%, nhưng **phát hiện thiên lệch (5.1) chỉ 15–58%**; Qwen2.5-14B tốt nhất (57,79%).
- Dự đoán phán quyết 82–90% (có mẫu hình, tình huống tự chứa thông tin).

### 4.3 Phân tích theo họ mô hình
- Qwen2.5: nhất quán theo kích cỡ; 32B tốt nhất phân loại chủ đề (85,50%); **mọi biến thể đều 0,00 Y-F1 ở phát hiện mâu thuẫn**.
- Llama-3.1: 70B cao nhất nhất quán đạo đức (93,99%); 8B là biến thể duy nhất có phát hiện mâu thuẫn đáng kể. Llama-2 yếu ở cấp cao (accuracy thường <30%, ROUGE-L <0,10).
- Nhóm tiếng Việt: BloomVN-8B tương đương mô hình đa ngôn ngữ; CMC-Legal-32B thống trị suy luận, SOTA ở 4/5 benchmark (theo tác giả) → lộ trình "từ tiếng Việt tổng quát đến chuyên hóa pháp lý".

### 4.4 Bốn kết luận chính (mục 4.3.4)
1. LLM hiện tại gặp thách thức nền tảng ở lập luận pháp lý nâng cao: dự đoán điều và phát hiện mâu thuẫn **gần như chưa giải quyết**.
2. Tiền huấn luyện miền có lợi hơn mở rộng tham số (mô hình nhỏ chuyên hóa vượt mô hình lớn 10–18 lần).
3. Ưu thế mô hình độc quyền giảm ở lập luận bậc cao.
4. Phát hiện thiên lệch và hiểu lược đồ pháp lý (bao gồm thời gian/sửa đổi) vẫn khó với mọi mô hình.

## 5. Phân tích lỗi (error analysis, sáu tác vụ đại diện) – **rất liên quan thời gian**
- **Task 1.5 (Legal Schema Recall)**: (1) *hierarchical document-type bias* – mặc định chọn văn bản cấp cao hơn (Luật thay vì Thông tư đúng) do giả định cứng về thứ bậc; (2) ***temporal-direction confusion*** – hiểu sai chiều quan hệ sửa đổi khi văn bản sửa đổi có ngày ban hành "bất ngờ theo ngữ cảnh"; (3) ***consolidation confusion*** – lẫn Hợp nhất với thay thế hay bãi bỏ, không phân biệt vai trò thủ tục của Văn bản hợp nhất.
- **Task 3.1**: (1) ***recency blindness*** (mù tính mới) – chọn văn bản cũ thay vì văn bản đúng 2024–2025; các câu về **Luật Trật tự, an toàn giao thông đường bộ 2024**, **Luật Tổ chức Tòa án nhân dân 2024**, **Nghị định 37/2025/NĐ-CP** bị **tất cả** mô hình trả lời sai; (2) *subarticle granularity failure* – chọn nhầm Điều/Khoản trong số các lựa chọn đánh số gần nhau dù đã nhận đúng đạo luật.
- **Task 3.4**: hai thiên lệch đối xứng: mô hình tổng quát có *no-conflict bias* (âm tính giả với mâu thuẫn thật giữa quyết định cấp tỉnh và luật quốc gia); CMC-Legal-32B có *over-detection bias* (dự đoán mâu thuẫn hầu như mọi ca, kể cả cặp nhất quán). Kết luận: lập luận chéo văn bản trên thứ bậc quy phạm và hiệu lực thời gian vẫn chưa giải quyết ở cả 23 mô hình.
- **Cấp 4**: sai định dạng, thiếu căn cứ luật; tóm tắt sao chép cấu trúc nguồn và bị cắt giữa câu; IRAC sai ở thành phần Rule (bịa luật không tồn tại; nhầm ngưỡng: mặc định dưới 18 tuổi của Công ước LHQ thay vì dưới 16 theo Luật Trẻ em 2016); ý kiến pháp lý đưa tham chiếu ngoài văn bản và vi phạm ràng buộc định dạng.
- **Task 5.1**: *single-answer truncation* (chỉ nêu lựa chọn nổi bật nhất dù cần chọn nhiều); CMC-Legal-32B hay xuất rỗng.

## 6. Các thí nghiệm bổ sung
**Chiến lược prompt (Hình 2)**: few-shot không suy luận cho kết quả **cao và ổn định hơn** zero-shot có suy luận; suy luận tường minh thường **làm giảm** và tăng phương sai ở Level 2; ở Level 3 tác dụng hỗn hợp (giúp xác định điều, không ổn định ở phát hiện mâu thuẫn); few-shot giảm phương sai và nâng trung vị. Ở phát hiện mâu thuẫn, few-shot làm GPT-4o và Gemini-2.5-Flash chuyển từ gần như toàn "không mâu thuẫn" sang dự đoán lớp thiểu số.

**Agentic RAG (Phụ lục, Bảng 11)** – gần với đề tài của khóa luận:
- Cấu hình: công cụ tìm kiếm trên Legal Corpus DB (>55.000 văn bản), chunk **1024 token, chồng 100**; truy hồi lai: dense (PhoBERT tinh chỉnh miền pháp lý + FAISS) + BM25 (token hóa pháp lý giữ số điều/tham chiếu) + khớp chính xác qua Elasticsearch; hợp nhất **RRF trọng số 0,4 dense / 0,3 sparse / 0,3 exact** tối ưu trên tập validation; top-5 chunk/truy vấn. Khác RAG một lượt: mô hình tự sinh truy vấn ngôn ngữ tự nhiên, nhận chunk **kèm metadata (tên văn bản, số điều/khoản, ngày ban hành, tình trạng sửa đổi)**, phân tích rồi viết lại truy vấn hay tìm tiếp, **tối đa 5 vòng**.
- **Xử lý phiên bản**: "temporal filtering" **ưu tiên văn bản có hiệu lực tại thời điểm tham chiếu của truy vấn** (bài không mô tả chi tiết cách chọn).
- Kết quả: Task 3.1 **tăng +10,66 đến +22,00 điểm** cho mọi mô hình (lớn nhất GPT-4o) vì không ai nhớ được số điều/khoản của 55.000+ văn bản. Task 3.2 (dự đoán phán quyết): giảm nhẹ ở mọi mô hình (câu hỏi tự chứa, truy hồi làm nhiễu). **Task 3.3 (nhiều điều): giảm nhẹ** — mô hình không phân rã câu hỏi thành nhiều truy vấn và chỉ lấy một phần quy định cần; chunk có thể cắt vụn các điều liên quan logic. Task 3.4: Y-F1 cải thiện cho nhiều mô hình tổng quát nhờ truy hồi đúng điều được viện dẫn; mô hình chuyên hóa giảm (nhiễu từ điều khoản gần giống).
- Kết luận: truy hồi **phụ thuộc tác vụ**; cần chiến lược truy hồi nhận biết tác vụ, phân rã câu hỏi và phân đoạn nhận biết cấu trúc; gọi truy hồi có chọn lọc.

**Đánh giá người cho tác vụ sinh (Bảng 4)**: 20 mẫu × 3 tác vụ × 5 hệ (gồm đáp án người) = 300 mẫu; hai junior chấm độc lập, mù đôi, thang 1–5 về **Legal Accuracy** và **Completeness**; mean κ = 0,92; ~40 giờ. Người: Legal Accuracy 4,76–4,82; Completeness 4,78–4,88. Mô hình thua người trung bình 1,2–1,5 điểm (lớn nhất ở completeness); Task 4.2 (IRAC) tất cả mô hình rất thấp (2,36–2,62). CMC-Legal-32B dẫn đầu mô hình ở 4.1 và 4.3 (Legal Accuracy 3,79 và 3,57), GPT-4o thứ hai.

**Đánh giá bổ sung dạng khác (Phụ lục A)**: NER cho Task 1.1: Exact Match gần 0 (nhận được thực thể lẻ nhưng không phục hồi đủ tập); Task 1.2 dạng Macro-F1 cho thấy nhiều mô hình mặc định lớp đa số; Task 2.3: Node-F1 và Edge-F1 — mô hình dự đoán **cạnh tốt hơn nút** (nắm quan hệ nhưng sai tham chiếu điều/khoản cụ thể).

## 7. Nghiên cứu nhiễm bẩn dữ liệu (mục 5, Phụ lục)
- Phân tầng 1.000 mẫu; lấy tối đa 20 cụm 13-gram từ mỗi câu hỏi (bỏ chỉ dẫn, lựa chọn, nhãn); tìm Google khớp chính xác; đánh dấu nghi ngờ nếu ≥2 cụm trùng cùng trang trong top-5 ngoài tham chiếu luật chuẩn. Bổ sung: tìm trên cổng pháp luật (thuvienphapluat.vn, chinhphu.vn) với khớp chính xác và mờ (ngưỡng 0,85); tra Common Crawl 2020–2024 (n-gram chính xác + tương đồng ngữ nghĩa). Phân loại khớp: văn bản luật bắt buộc / mẫu pháp lý chuẩn / nội dung vụ việc thực chất (chỉ loại cuối mới tính nhiễm).
- Kết quả: **1,8%** mẫu có khả năng chồng lấn, đều do điều luật hay mẫu chuẩn lặp tự nhiên; không nhiễm ở tác vụ vụ việc, suy luận, sinh văn bản.

## 8. Hạn chế do tác giả nêu
- **Hiệu lực thời gian**: benchmark **tĩnh**; dù KG ghi quan hệ lập pháp và lịch sử phiên bản tại thời điểm xây, các luật mới (ví dụ Luật Đất đai 2024) làm một số câu lỗi thời theo thời gian → hạn chế giá trị dài hạn của câu hỏi cố định.
- Tập trung văn bản thành văn; bỏ sót vùng xám diễn giải của thông tư hướng dẫn, quy tắc ngầm.
- Corpus chỉ **văn bản trung ương đang hiệu lực** (~55.000), nên không có kho phiên bản lịch sử.

## 9. Nhận xét phê phán (người đọc)
- Tập test chủ yếu **MCQ** với distractor do chuyên gia thiết kế; phần lớn tác vụ đo kiến thức/nhận biết, chấm Accuracy; chỉ số sinh dùng ROUGE-L (tác giả tự nhận ROUGE tương quan kém với đúng đắn).
- Task 1.5 là MCQ; nếu có 4 phương án như ví dụ minh họa trong Hình 1 (A–D) thì mức ngẫu nhiên là 25% và kết quả <28% ≈ ngẫu nhiên (bài không nêu số phương án riêng cho Task 1.5, đây là suy đoán của người đọc); chưa có phân tích chi tiết về đề và nhãn.
- Bài không nêu cách tạo nhãn "thời gian" cho Task 1.5 nằm ở mức "quan hệ giữa văn bản" chứ không phải "bản có hiệu lực tại ngày X".
- Chỉ số κ = 0,89 là đồng thuận **giữa hai junior trả lời câu hỏi của nhau**, không phải kiểm tra độc lập chất lượng nhãn gốc (cái đã được dựng bởi chính chuyên gia).
- Bản v5 có số liệu chênh giữa văn bản và bảng (ví dụ Task 3.1) → khi trích dẫn nên lấy từ bảng trong PDF.

## 10. Dùng gì cho khóa luận ViLexTime
1. **Số liệu động lực** (trích có điều kiện, dùng đúng bảng PDF): Task 1.5 (quan hệ phân cấp/thời gian) mọi LLM đều <28%; "recency blindness" khiến các câu về luật 2024–2025 bị tất cả mô hình trả lời sai; "temporal-direction confusion" và "consolidation confusion" là các lỗi cụ thể đáng đưa vào taxonomy lỗi của ViLexTime (liên hệ taxonomy 4 kiểu của bài FiscalQA Pro).
2. **Baseline và related work**: VietLegal là benchmark kiến thức pháp luật tiếng Việt quy mô lớn; khóa luận nên chỉ ra rằng nó **tĩnh, chỉ văn bản đang hiệu lực, không có kho phiên bản**, nên không đo được point-in-time — đúng khoảng trống ViLexTime.
3. **Cấu hình Agentic RAG** có thể tái dùng làm baseline: chunk 1024/100, hybrid dense (PhoBERT miền luật) + BM25 + Elasticsearch exact, RRF 0,4/0,3/0,3, top-5, tối đa 5 vòng, metadata gồm ngày ban hành và tình trạng sửa đổi, temporal filtering ưu tiên văn bản có hiệu lực tại thời điểm tham chiếu. Phát hiện "RAG chunk hại lập luận nhiều điều" ủng hộ luận điểm cần truy hồi nhận biết cấu trúc/đồ thị.
4. **Quy trình chú giải mẫu**: senior + hai junior độc lập, kiểm chéo mù theo lô 100, κ trước thảo luận, quy tắc cho điều đã bãi bỏ nhưng còn được tham chiếu, đào tạo hai ngày + ngưỡng 85% trên mẫu vàng thí điểm, công khai mức thù lao và giờ công. Đối chiếu với tiêu chuẩn kiểm chất lượng của ViLexTime.
5. **Nghiên cứu nhiễm bẩn 13-gram** (Google, cổng pháp luật, Common Crawl; phân loại khớp vào luật bắt buộc/mẫu/nội dung thực chất) là quy trình dùng lại được.
6. **Phát hiện về prompt**: few-shot không CoT ổn hơn zero-shot có CoT cho tác vụ cấu trúc; nên cố định cấu hình prompt khi đánh giá.
7. **Cẩn trọng**: không dùng VietLegal làm "bằng chứng thời gian" mạnh; dùng như bằng chứng gián tiếp. Kiểm số liệu từ bảng PDF trước khi trích (có điểm chưa nhất quán giữa văn bản và bảng).
