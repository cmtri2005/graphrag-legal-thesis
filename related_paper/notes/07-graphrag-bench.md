# GraphRAG-Bench: Challenging Domain-Specific Reasoning for Evaluating Graph Retrieval-Augmented Generation

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/_GraphRAG-Bench_ ... .pdf` (12 trang; bản PDF này **không kèm phụ lục** dù bài nhắc "full evaluation protocol in the Appendix", nên prompt chấm LLM và công thức chi tiết không có trong file).

## 0. Thông tin chung

| Mục | Nội dung |
|---|---|
| Tác giả | Yilin Xiao\*, Junnan Dong\*† (đồng tác giả chính), Chuang Zhou, Su Dong, Qian-Wen Zhang, Di Yin, Xing Sun, Xiao Huang. The Hong Kong Polytechnic University; Tencent Youtu Lab |
| Nơi đăng | arXiv:2506.02404v3 [cs.CL], 20/06/2025. "Preprint. Under review." (chưa phải bản bình duyệt xuất bản) |
| Mã nguồn / tài nguyên | https://github.com/jeremycp3/GraphRAG-Bench |
| Miền | **Giáo trình khoa học máy tính cấp đại học** (không phải pháp lý) |
| Quy mô | **1.018** câu hỏi, **5** kiểu câu, **16** chủ đề, kho **~7 triệu từ** từ **20** giáo trình (chọn từ 100+ ấn phẩm thuộc 16 mảng con) |
| Độ gần với ViLexTime | Thấp về nội dung; **cao về phương pháp đánh giá GraphRAG** (đánh giá từng tầng: xây đồ thị, truy hồi, sinh đáp án, sinh lập luận) |

## 1. WHY – Bài toán

- Câu hỏi nghiên cứu: **"Đồ thị hóa tri thức có thực sự nâng khả năng lập luận hơn là truy hồi đơn thuần không?"**
- RAG thường trả các đoạn rời theo độ tương đồng → khó mô hình hóa quan hệ phức tạp giữa khái niệm cho câu hỏi multi-hop hoặc câu hỏi cần hiểu toàn cục. GraphRAG biểu diễn tri thức dạng đồ thị (nút = khái niệm, cạnh = quan hệ) để duyệt/suy luận.
- Ba hướng GraphRAG gần đây: (1) **xây đồ thị phân cấp**: RAPTOR, Microsoft GraphRAG (cây và community detection); (2) **truy hồi đồ thị bằng neural**: GFM-RAG, G-Retriever (bộ mã hóa đồ thị với mục tiêu chuyên biệt); (3) **tích hợp tri thức động**: DALK, ToG (xây và duyệt đồ thị thích ứng, gắn chặt với LLM).
- **Vấn đề của benchmark hiện có** (HotpotQA, 2WikiMultiHopQA, MuSiQue, QuALITY, PopQA): (i) chỉ câu hỏi thường thức, có thể đã nằm trong dữ liệu huấn luyện LLM; (ii) chỉ cần một bước hoặc multi-hop nông qua liên kết tường minh → không kiểm tra ưu thế riêng của tri thức đồ thị; (iii) đáp án ngắn (tên, ngày) hoặc trắc nghiệm → khó phản ánh năng lực lập luận trên đồ thị. Thêm: câu hỏi được dựng nhân tạo bằng luật; kho ngắn, thường chuyển đổi từ thực thể/mô tả của KG; **không có lý giải vàng (gold rationale)**; bỏ qua phân biệt kiểu câu hỏi; DIGIMON chỉ so sánh phương pháp, không dataset mới, không đo lập luận.
- Đóng góp: benchmark GraphRAG chuyên biệt đầu tiên (theo tác giả); giao thức đánh giá toàn pipeline; thực nghiệm chín phương pháp.

## 2. HOW – Thiết kế benchmark và đánh giá

### 2.1 Năm kiểu câu hỏi (Bảng 1)
| Kiểu | Mô tả | Năng lực nhắm tới |
|---|---|---|
| **Fill-in-blank (FB)** | Điền chỗ trống bằng thuật ngữ chính xác theo ngữ cảnh | sinh nội dung mạch lạc nhờ phụ thuộc ngữ nghĩa cục bộ và gắn thực thể |
| **Multi-choice (MC)** | 4 lựa chọn, có phương án nhiễu hợp lý về ngôn ngữ | suy luận phân biệt, tích hợp thông tin thực thể và quan hệ cạnh để loại phương án giống nghĩa nhưng sai sự thật |
| **Multi-select (MS)** | Chọn 2–4 đáp án đúng từ 4 lựa chọn | suy luận trên các khái niệm liên kết, tổng hợp bằng chứng từ đường multi-hop, giải quyết xung đột thuộc tính liên quan nhưng không thiết yếu |
| **True-or-false (TF)** | Xác minh tính đúng của mệnh đề | đánh giá tính thực chứng, suy luận logic trên tri thức |
| **Open-ended (OE)** | Câu trả lời tự do dài | tổng hợp tri thức tổng thể, ghép kiến thức nhiều mảng thành trả lời có cấu trúc, mạch lạc |

Câu hỏi thể hiện ba loại năng lực: **hiểu khái niệm** (ví dụ "cho định lý A và B, chứng minh kết luận C"), **thuật toán/lập trình** (ví dụ viết mã có các lời gọi hàm liên kết), **tính toán toán học** (ví dụ cho Input, Conv1, MaxPool, FC, tính kích thước đầu ra). Mỗi câu gắn **hai nhãn phân cấp**: lĩnh vực rộng (Level 1, ví dụ "Machine Learning") và khái niệm mịn (Level 2, ví dụ "Unsupervised Learning"). 16 chủ đề gồm CV, NLP, cơ sở dữ liệu, mạng máy tính, HCI, đạo đức AI, kiến trúc, hệ điều hành, lập trình, toán, ML, truy xuất thông tin, an ninh mạng, DSA, khoa học dữ liệu, nhập môn AI (theo nhãn biểu đồ).
- Chọn câu: sau sàng lọc và tinh chỉnh bởi **nhiều chuyên gia miền**, chọn 1.018 câu "chất lượng cao, thách thức".

### 2.2 Xử lý kho giáo trình (mục 3.2)
Pipeline nhiều giai đoạn: (a) **tiền xử lý**: phân loại trang văn bản/trang quét (theo mật độ chữ và tỷ lệ diện tích ảnh), trích bằng PyMuPDF hoặc OCR; trích metadata (mục lục, số trang, khoảng trang từng chương/mục); (b) **phân tích nội dung**: bố cục bằng **LayoutLMv3** (tiêu đề, đoạn, hình, bảng, trang trí), nhận diện công thức nội dòng bằng mô hình dựa trên YOLO (PDF-Extract-Kit) để OCR không làm hỏng công thức, **PaddleOCR** cho trang quét; (c) **hậu xử lý** bằng **MinerU** sắp xếp lại thứ tự đọc; (d) **xây phân cấp** 4 tầng: Book Title → Chapter → Section (Subchapter) → Knowledge Content Unit, mỗi nút có metadata ngữ cảnh và vai trò cấu trúc.

### 2.3 Lập luận vàng do chuyên gia soạn (mục 3.3)
Mỗi câu có **rationale** do chuyên gia viết: (i) cô lập khái niệm tiên quyết, (ii) mô tả quan hệ giữa chúng, (iii) nêu các phép suy diễn dùng để giải. Mục đích: đánh giá liệu mô hình **thật sự sinh giải thích có căn cứ** hay chỉ khai thác mẫu bề mặt. Với mỗi chủ đề đo cả độ chính xác đáp án và mức độ rationale sinh ra khớp rationale vàng.

### 2.4 Giao thức đánh giá (mục 4)
- **Xây đồ thị**: Hiệu suất (thời gian), Chi phí (số token tiêu thụ), **Organization** (tỷ lệ nút không cô lập; không áp dụng cho cây vì cây không có nút cô lập).
- **Truy hồi**: thời gian lập chỉ mục (xây CSDL vector); thời gian truy hồi trung bình mỗi truy vấn; liệt kê **toán tử truy hồi** (Node, Relationship, Chunk, Community, Subgraph).
- **Sinh đáp án** — chỉ số **Accuracy** tự đặt (lập luận: *exact match* không phù hợp vì đúng không cần khớp từng chữ): OE và FB → đưa đầu ra và đáp án vàng cho **LLM chấm** theo prompt riêng về tương đồng ngữ nghĩa và đúng đắn; MC và TF → 1 điểm đúng, 0 sai; **MS** → 1 điểm nếu hoàn toàn đúng, **0,5 điểm nếu chọn tập con**, 0 nếu sai.
- **Lập luận (Rationale)**: LLM chấm giữa rationale sinh ra và rationale vàng, cho điểm **R** (tương ứng ngữ nghĩa và nhất quán suy luận). Chỉ số thêm **AR**: điểm lập luận **có điều kiện đã trả lời đúng** — phân biệt "đoán trúng" với "lập luận đúng để ra đáp án".
- **Thiết lập chung**: LLM nền **GPT-4o-mini** cho mọi phương pháp; không giới hạn độ dài token tối đa; top-**k = 5** cho phương pháp cần top-k; chunk size **1.200 token**; các siêu tham số khác theo giá trị tối ưu của bài gốc.
- **Chín phương pháp**: RAPTOR, LightRAG, GraphRAG (Microsoft), G-Retriever, HippoRAG, GFM-RAG, DALK, KGP, ToG. Baseline RAG: **TF-IDF**, **BM25**; và **GPT-4o-mini trơn** (không truy hồi).

## 3. WHAT – Kết quả

### 3.1 Xây đồ thị (Bảng 2)
| Phương pháp | Token xây đồ thị | Thời gian xây | Organization |
|---|---|---|---|
| RAPTOR | 10.142.221 | 20.396,49 s | – (cây) |
| KGP | 15.271.633 | 17.318,07 s | 46,03% |
| LightRAG | 83.909.073 | 12.976,22 s | 69,71% |
| GraphRAG | 79.929.698 | 11.181,24 s | 72,51% |
| G-Retriever | 32.948.161 | 5.315,27 s | 89,95% |
| HippoRAG | 33.006.198 | 5.051,41 s | 89,58% |
| DALK | 33.007.324 | 4.674,30 s | 89,49% |
| ToG | 33.008.230 | 5.235,30 s | 89,95% |
| GFM-RAG | 32.766.094 | 5.631,10 s | 89,97% |

Phân loại bốn cấu trúc: **Tree** (RAPTOR: token thấp nhất vì chỉ gọi LLM để tóm tắt, nhưng chậm nhất do gom cụm lặp); **Passage Graph** (KGP: chunk = nút, cạnh bằng entity linking; token trung bình, chậm thứ hai do entity linking, tỷ lệ nút không cô lập **thấp nhất** vì công cụ liên kết thực thể khó tạo cạnh); **Knowledge Graph** (G-Retriever, HippoRAG, GFM-RAG, DALK, ToG: trích thực thể/quan hệ bằng OpenIE; token trung bình, **nhanh nhất**, organization ~90% **tốt nhất**); **Rich Knowledge Graph** (GraphRAG, LightRAG: thêm mô tả tóm tắt cho nút/cạnh; **token nhiều nhất** do sinh mô tả bằng LLM, organization thấp hơn vì thêm nhiễu).

### 3.2 Truy hồi (Bảng 3)
| Phương pháp | Toán tử truy hồi | Thời gian lập chỉ mục | Thời gian truy hồi TB |
|---|---|---|---|
| KGP | Node | 204,10 s | 89,38 s |
| ToG | Node+Relationship | 1.080,43 s | 70,53 s |
| GraphRAG | Node+Relationship+Chunk+Community | 1.796,65 s | 44,87 s |
| DALK | Node+Subgraph | 407,10 s | 26,80 s |
| G-Retriever | Node+Relationship+Subgraph | 920,39 s | 23,77 s |
| LightRAG | Node+Relationship+Chunk | 1.430,32 s | 13,95 s |
| HippoRAG | Node+Relationship+Chunk | 4.695,29 s | 2,44 s |
| GFM-RAG | Node | 93,55 s | 1,96 s |
| RAPTOR | Node | 451,03 s | 0,02 s |

GFM-RAG lập chỉ mục ngắn nhất (không dựng CSDL vector truyền thống, chỉ lưu thực thể tương ứng câu hỏi khi xây đồ thị); HippoRAG lâu nhất (xây thêm ánh xạ entity↔relationship và relationship↔chunk); GraphRAG thêm thời gian vì lưu báo cáo cộng đồng; RAPTOR truy hồi nhanh nhất nhờ cấu trúc cây; KGP, ToG, DALK chậm vì **phải gọi LLM lúc truy hồi**.

### 3.3 Độ chính xác sinh đáp án (Bảng 4)
| Phương pháp | FB | MC | MS | TF | OE | **Trung bình** |
|---|---|---|---|---|---|---|
| GPT-4o-mini (không truy hồi) | 74,29 | 81,11 | 76,68 | 75,95 | 52,23 | **70,68** |
| TF-IDF | 75,71 | 77,88 | 72,52 | 84,17 | 50,18 | 71,71 ↑ |
| BM-25 | 74,28 | 78,80 | 71,17 | 84,49 | 50,00 | 71,66 ↑ |
| DALK | 70,00 | 78,34 | 71,62 | 77,22 | 51,49 | 69,30 ↓ |
| G-Retriever | 70,95 | 77,42 | 71,62 | 78,80 | 52,04 | 69,84 ↓ |
| LightRAG | 65,24 | 78,80 | 73,42 | 82,59 | 53,16 | 71,22 ↑ |
| ToG | 70,48 | 78,80 | 78,38 | 79,75 | 54,28 | 71,71 ↑ |
| KGP | 74,29 | 79,26 | 74,77 | 82,28 | 51,49 | 71,86 ↑ |
| GFM-RAG | 72,38 | 80,65 | 72,07 | 82,59 | 52,79 | 72,10 ↑ |
| GraphRAG | 75,24 | 81,57 | 77,48 | 80,70 | 52,42 | 72,50 ↑ |
| HippoRAG | 70,48 | 80,18 | 74,32 | 81,65 | 56,13 | 72,64 ↑ |
| **RAPTOR** | 76,67 | 80,65 | 77,48 | 82,28 | 54,83 | **73,58 ↑** |

Diễn giải của tác giả: GPT-4o-mini vốn đã mạnh nên **không phải mọi GraphRAG đều giúp**. **DALK và G-Retriever làm giảm** (quá phụ thuộc cấu trúc, bỏ rơi ngữ nghĩa nội dung → nhiễu khi sinh). LightRAG, ToG, KGP cải thiện nhẹ. **GFM-RAG, GraphRAG, HippoRAG cải thiện đáng kể** nhờ kết hợp cấu trúc đồ thị với ngữ nghĩa mức chunk. **RAPTOR cao nhất** (cây gom cụm lặp khớp với tổ chức phân cấp tự nhiên của giáo trình). Hầu hết GraphRAG vượt baseline BM25/TF-IDF.
- **Lưu ý của người đọc**: mức chênh toàn phần nhỏ (từ 70,68 lên cao nhất 73,58, tức +2,9 điểm); và **BM25/TF-IDF (71,7)** đã đạt gần ngang nhiều GraphRAG (71,2–72,6). Bài không báo khoảng tin cậy hay kiểm định ý nghĩa thống kê. Bài tuyên bố "GraphRAG enhances the reasoning capabilities" nhưng riêng độ chính xác đáp án thì lợi ích khiêm tốn.

### 3.4 Lập luận (Bảng 5; R = điểm rationale, AR = điểm rationale khi đã trả lời đúng; trung bình)
| Phương pháp | R TB | AR TB |
|---|---|---|
| GPT-4o-mini | 55,45 | 39,78 |
| TF-IDF | 57,61 | 42,38 |
| BM-25 | 59,18 | 44,15 |
| DALK | 58,89 | 42,12 |
| KGP | 58,74 | 42,22 |
| GraphRAG | 59,43 | 43,30 |
| G-Retriever | 60,17 | 43,66 |
| LightRAG | 60,46 | 43,81 |
| ToG | 60,17 | 44,01 |
| GFM-RAG | 60,36 | 44,30 |
| HippoRAG | 60,90 | 44,55 |
| **RAPTOR** | 60,81 | **45,53** |

(Chi tiết theo kiểu câu có trong bảng gốc, ví dụ OE: AR của GPT-4o-mini chỉ **9,76**, RAPTOR **13,57**, ToG 12,08, HippoRAG 12,36 — cho thấy ở câu mở, lập luận đúng khi đáp án đúng cực thấp.)
- Phát hiện: điểm lập luận R và AR thấp hơn nhiều điểm accuracy → LLM thường **đoán hoặc khớp mẫu**; ngay cả khi đáp án đúng, lập luận có thể sai (hoặc ngược lại). **Mọi GraphRAG nâng lập luận** (R từ 55,45 lên 58,7–60,9; AR từ 39,78 lên 42,1–45,5) vì truy hồi được cả tài liệu phụ thuộc multi-hop, cho LLM bằng chứng bên ngoài. HippoRAG và RAPTOR tốt nhất; nhìn chung hầu hết GraphRAG vượt BM25/TF-IDF, **nhưng chênh với BM25 nhỏ** (BM25 R 59,18, AR 44,15 so với RAPTOR 60,81 và 45,53).

### 3.5 Phân tích theo chủ đề (mục 4.5)
- GraphRAG nhìn chung cải thiện nhất quán ở đa số chủ đề.
- **Toán học**: mọi GraphRAG **làm giảm** độ chính xác — vì bài toán phụ thuộc thao tác ký hiệu chặt chẽ; tài liệu truy hồi thường mang tính giải thích/khái niệm, ký hiệu và bố cục công thức không khớp yêu cầu, gây mơ hồ hoặc mất bước.
- **Đạo đức**: cả GraphRAG lẫn LLM đều trung bình — vì phán đoán giá trị chủ quan, phụ thuộc bối cảnh động.
- **Độ bền**: RAPTOR tăng đáng kể ở hầu hết chủ đề → hiệu quả xuyên miền.

### 3.6 Quan sát theo kiểu câu hỏi (mục 4.6)
- **MC giảm**: LLM đã nội hóa nhiều kiến thức; truy hồi có thể thêm thông tin dư/ít liên quan → nhiễu quyết định.
- **TF cải thiện** (75,95 → ~82–84): bằng chứng giúp xác minh mệnh đề.
- **OE cải thiện**: bối cảnh/sự kiện bổ sung giúp câu trả lời giàu chi tiết, **giảm ảo giác** nhờ có căn cứ.
- **FB, MS có tác động khác nhau** (thường giảm hoặc ít): FB đòi khớp ngữ cảnh chính xác → kho truy hồi hay không khớp → nhiễu; MS cần chọn tập tổ hợp → nếu truy hồi thiếu hoặc thừa sẽ gây nhầm; các kiểu này **đòi hỏi độ chính xác truy hồi cao**.
- Ví dụ định tính (Hình 3, chủ đề mạng máy tính): hỏi "vì sao server cần ISN đặc biệt trong SYN-ACK?" → cần tổng hợp nhiều bước (ISN đảm bảo nhận dạng kết nối duy nhất và thứ tự gói; ISN khó đoán chống tấn công SYN flood). Rationale vàng thể hiện dưới dạng chuỗi bộ ba <thực thể>→quan hệ→<thực thể>.

## 4. Hạn chế và nhận xét phê phán
- **Miền khác hẳn pháp lý** (giáo trình CS, tiếng Anh): kết luận "RAPTOR tốt nhất" **gắn với giáo trình có phân cấp tự nhiên**; luật cũng phân cấp nên cần kiểm nghiệm lại chứ không suy rộng. Chính tác giả giải thích RAPTOR thắng vì khớp tổ chức giáo trình.
- Chỉ **một LLM nền** (GPT-4o-mini); chưa thử LLM mạnh hơn/yếu hơn; mức cải thiện nhỏ.
- **Chấm bằng LLM** cho FB, OE và lập luận (prompt không có trong bản PDF); không báo mức đồng thuận người–LLM, không báo kiểm định; thiên lệch judge. (Đối lập với tinh thần chấm tất định của bài 01.)
- Không có khoảng tin cậy; chênh lệch giữa nhiều phương pháp rất nhỏ (<1–2 điểm), nên xếp hạng mong manh.
- Chưa có phần "Hạn chế/Đạo đức" trong bản này; chưa có thông tin chi tiết về quy trình chuyên gia (số người, κ) ở mục câu hỏi; rationale do chuyên gia soạn nhưng không nêu quy trình kiểm chứng chéo.
- Đo chi phí xây đồ thị bằng token/thời gian trên cùng một kho, nhưng cấu hình phần cứng/đồng thời không nêu trong bản này.
- Chưa có thí nghiệm theo dõi **cập nhật tăng dần** hay **thời gian**.

## 5. Dùng gì cho khóa luận ViLexTime
1. **Khung đánh giá theo tầng pipeline** (Graph construction → Knowledge retrieval → Generation → Rationale) là mẫu trình bày thí nghiệm GraphRAG: với ViLexTime có thể thêm tầng "**Temporal resolution**" (chọn đúng phiên bản) giữa retrieval và generation.
2. **Chỉ số xây đồ thị**: token, thời gian, Organization (tỷ lệ nút không cô lập) — dùng để báo chi phí và chất lượng đồ thị pháp lý; nút cô lập cao nghĩa là quan hệ sửa đổi/tham chiếu không được nối.
3. **Chỉ số lập luận R và AR**: "AR = rationale tốt khi đã trả lời đúng" phân biệt đoán đúng và lập luận đúng — hữu ích để chứng minh hệ thống chọn đúng phiên bản **vì đúng lý do**; có thể thay judge LLM bằng kiểm tra tất định rằng rationale/citation trỏ đúng phiên bản (kết hợp bài 01).
4. **Chính sách chấm MS** (0,5 điểm cho tập con) áp dụng được cho câu hỏi nhiều đáp án (ví dụ nhiều điều khoản bị ảnh hưởng).
5. **Cấu hình baseline công bằng**: cùng LLM, top-k = 5, chunk 1.200 token, siêu tham số tối ưu theo bài gốc; danh sách chín phương pháp có thể dùng làm tập baseline (ViHERMES đã dùng RAPTOR, MiniRAG, LightRAG, HippoRAG 2).
6. **Quan sát thực nghiệm đáng nhớ**: (a) GraphRAG không phải lúc nào cũng thắng RAG đơn giản; BM25/TF-IDF vẫn mạnh → khóa luận cần so sánh với baseline lexical; (b) GraphRAG giúp OE/TF, hại/hết hiệu ứng với FB/MS/MC → phân tích theo loại câu hỏi; (c) GraphRAG hại khi truy hồi nhiều tài liệu mang tính giải thích nhưng lệch yêu cầu (toán học) → tương tự rủi ro "truy hồi phiên bản sai" trong pháp lý.
7. **Cẩn trọng**: không lấy số liệu domain giáo trình để lập luận cho miền pháp lý; chỉ dùng phương pháp đánh giá.
