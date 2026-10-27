# ViHERMES: A Graph-Grounded Multihop Question Answering Benchmark and System for Vietnamese Healthcare Regulations

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/ViHERMES.pdf` (15 trang).

## 0. Thông tin chung

| Mục | Nội dung |
|---|---|
| Tác giả | Long S. T. Nguyen\*, Quan M. Bui\* (đồng tác giả chính), Tin T. Ngo, Quynh T. N. Vo, Dung N. H. Le, Tho T. Quan. Nhóm URA, Khoa KH&KT Máy tính, ĐH Bách khoa TP.HCM (HCMUT), ĐHQG-HCM |
| Nơi đăng | arXiv:2602.07361v1 [cs.CL], 07/02/2026 |
| Mã nguồn / dữ liệu | https://github.com/ura-hcmut/ViHERMES |
| Miền | Quy định y tế Việt Nam (nguồn: cổng Bộ Y tế moh.gov.vn) |
| Đóng góp | (1) Benchmark multihop QA đầu tiên cho quy định y tế tiếng Việt; (2) quy trình sinh dữ liệu "graph-inspired" có kiểm soát; (3) hệ thống QA đa agent nhận biết đồ thị (SRKG) |
| Độ gần với ViLexTime | Cao về **bối cảnh tiếng Việt, chuỗi sửa đổi, kỹ thuật xây benchmark và baseline GraphRAG**; **thấp về thời gian**: chỉ nói "bản hiệu lực mới nhất" bằng cách đi theo chuỗi sửa đổi, chưa có mô hình hiệu lực theo ngày |

## 1. WHY – Bài toán

- Hỏi đáp trên văn bản quy phạm vốn là **bài toán nhiều bước (multihop)**, không phải hiểu một tài liệu: đáp án đúng có thể phụ thuộc vào (i) xác định **quy định có hiệu lực mới nhất**, (ii) **lần theo chuỗi sửa đổi** qua nhiều văn bản, (iii) ghép **định nghĩa/quy tắc thủ tục** được viện dẫn từ các văn bản khác. Truy hồi một lượt hay so khớp đoạn đơn lẻ là không đủ.
- Y tế khó hơn các bài báo y khoa/hướng dẫn lâm sàng (mô tả, khép kín): quy định y tế là văn bản pháp lý có cấu trúc hành chính chặt (điều, khoản) và phụ thuộc chéo văn bản dày đặc (sửa đổi, thay thế, bổ sung, tham chiếu).
- RAG ngây thơ coi kho là tập đoạn văn phẳng, thiếu nhận thức về cấu trúc pháp lý và quan hệ giữa văn bản → câu trả lời "trôi chảy nhưng **không đầy đủ hoặc lỗi thời** về pháp lý".
- Graph RAG tổng quát (GraphRAG, HippoRAG, LightRAG, MiniRAG) có đồ thị **tự học, thiên thực thể**, khó bám cấu trúc hình thức và phân cấp của luật; câu hỏi về chuỗi sửa đổi hay hiệu lực cần quan hệ **chính xác, có quy tắc** mà trích xuất thực thể–quan hệ chung chung không phục hồi được.
- Khoảng trống dữ liệu tiếng Việt: dataset hiện có hoặc là pháp luật chung hay miền khác (giáo dục), thiết kế cho **hiểu một văn bản hoặc QA nông** (ALQAC 2024, ViRHE4QA/R2GQA đào tạo đại học, ViBidLQA đấu thầu, ViLawQA lao động, dữ liệu quản lý giáo dục); còn dataset y tế (ViMedAQA, UIT-ViNewsQA, ViHealthQA) lại là lâm sàng/tin tức/website hỏi đáp, **không** phải quy định. Chưa có bộ nào kết hợp y tế + quy phạm + multihop.

## 2. HOW – Phương pháp

### 2.1 Quy trình xây dữ liệu (5 bước, Hình 1)
1. **Tuyển annotator + thiết kế guideline**: nhóm nhỏ annotator cùng **một chuyên gia miền**; guideline chung xác định tiêu chí multihop, cách dùng bằng chứng, ràng buộc hiệu lực pháp lý. Chuyên gia hướng dẫn tổng quát bảo đảm multihop hợp lệ và nhất quán pháp lý.
2. **Thu thập + tiền xử lý**: crawl tự động từ cổng công khai của Bộ Y tế; chuẩn hóa nội dung, loại nhiễu, **phân đoạn theo phân cấp pháp lý**. Mỗi đơn vị ngữ cảnh (điều hoặc khoản) là một bộ ba **⟨id, title, text⟩**.
3. **Gom cụm ngữ nghĩa + đồ thị tương đồng ngầm**:
   - Mỗi ngữ cảnh được mã hóa thành vector e_i ∈ R^d, **chuẩn hóa ℓ2** (ẽ_i = e_i/‖e_i‖₂) để nhấn hướng ngữ nghĩa thay vì độ lớn → K-Means trên vector chuẩn hóa = **Spherical K-Means** trên thực tế.
   - Tâm cụm c_k = trung bình các ẽ_i trong cụm; xếp hạng ngữ cảnh theo khoảng cách Euclid tới tâm d(ẽ_i, c_k) = ‖ẽ_i − c_k‖₂; chọn những ngữ cảnh gần nhất làm **ngữ cảnh đại diện**.
   - Cấu trúc cụm–tâm tạo **đồ thị tương đồng ngữ nghĩa ngầm**, bảo toàn tính liên kết chủ đề mà **không** dựa vào trích xuất quan hệ pháp lý tự động (có thể nhiễu). Tác giả nhấn mạnh đây *không* phải đồ thị pháp lý tường minh.
4. **Sinh QA multihop + kiểm tra cấu trúc**:
   - Với mức số bước h (hop), lấy mẫu bộ ngữ cảnh T = {c₁,…,c_h} từ nhóm đại diện, với hai ràng buộc: (a) các ngữ cảnh trong bộ phải thuộc **các tiêu đề văn bản khác nhau** (∀i≠j, title(c_i) ≠ title(c_j)) để bảo đảm suy luận **xuyên văn bản**; (b) giới hạn trùng lặp giữa hai bộ |T_a ∩ T_b| / |T_a| ≤ τ để đa dạng.
   - Mỗi bộ đưa cho LLM bằng prompt có cấu trúc để sinh cặp hỏi–đáp mà **câu trả lời phải dựa vào cả h ngữ cảnh**; mỗi "hop" ứng một bước phụ thuộc pháp lý (lần theo sửa đổi, tra định nghĩa, ghép thủ tục liên văn bản).
   - **Kiểm tra cấu trúc**: đúng định dạng, nhất quán giữa mức hop và việc dùng bằng chứng, có suy luận tường minh. Ca mơ hồ/biên được annotator rà dưới giám sát chuyên gia.
5. **Tổng hợp và chia tập**: xuất định dạng có cấu trúc, chia **train/test** có kiểm soát phân phối theo mức hop.

### 2.2 Cấu trúc một mẫu (Bảng 1)
Trường: Query, Answer, Number of hops, Context IDs, Evidence (đoạn trích nguyên văn từ từng ngữ cảnh), Reasoning (giải thích tường minh cách ghép). Reasoning và Evidence được **sinh ở bước 4 rồi annotator xác minh**.
Ví dụ trong bài (3 hop, ID ngữ cảnh dạng `4814-7506-4302`): câu hỏi về nghĩa vụ của cơ sở khám chữa bệnh gồm (i) áp dụng giá dịch vụ trong **giai đoạn chuyển tiếp**, (ii) duy trì chất lượng cơ bản, (iii) điều kiện pháp lý để hoạt động. Đáp án tổng hợp: cấp phép hoạt động + chứng chỉ hành nghề; triển khai tiêu chuẩn chất lượng, rà soát, tự đánh giá, báo cáo; khi có giá mới, người bệnh đang điều trị trước đó tiếp tục áp **mức giá cũ** đến khi ra viện hoặc kết thúc đợt ngoại trú. (Ví dụ này minh họa tổng hợp thủ tục và quy tắc chuyển tiếp, chưa phải truy vết sửa đổi.)

### 2.3 Thống kê tập test (Bảng 2; độ dài tính theo min / mean / max, đơn vị ký tự/token như bài ghi)
| NoH | Số mẫu | Từ vựng | Độ dài câu hỏi | Độ dài đáp án | Độ dài ngữ cảnh |
|---|---|---|---|---|---|
| 1 | 312 | 2.232 | 48 / 113,2 / 215 | 58 / 181,8 / 504 | 195 / 1.185,1 / 4.257 |
| 2 | 312 | 2.949 | 120 / 249,4 / 446 | 89 / 399,1 / 810 | 734 / 2.729,4 / 10.075 |
| 3 | 312 | 3.178 | 168 / 325,7 / 688 | 135 / 524,0 / 1.100 | 743 / 3.739,8 / 14.767 |
| 4 | 312 | 3.545 | 179 / 386,4 / 813 | 175 / 748,0 / 1.696 | 1.461 / 5.677,5 / 16.556 |
| 5 | 312 | 3.707 | 194 / 445,9 / 977 | 101 / 889,9 / 1.938 | 1.115 / 6.451,6 / 18.878 |
| **Tất cả** | **1.560** | **5.703** | 48 / 304,2 / 977 | 58 / 548,8 / 1.938 | 195 / 3.953,9 / 18.878 |

Test được **cân bằng**: 312 mẫu mỗi mức hop 1–5 (tổng 1.560). Hop tăng → câu hỏi/đáp án dài hơn nhiều, ngữ cảnh dài nhanh. Bài **không báo kích thước tập train** và không nêu kích thước kho văn bản hay số văn bản (đáng chú ý khi trích dẫn).

### 2.4 Hệ thống QA nhận biết đồ thị (mục 4)
**Structure-driven Regulatory Knowledge Graph (SRKG)** G = (V, E), E ⊆ V × R × V với R = R_struct ∪ R_legal.
- **Nút**: ba cấp khái niệm — *Document* (văn bản), *Clause* (đơn vị pháp lý có nghĩa độc lập), *Article* (đơn vị mịn hơn khi có). Mỗi nút v = ⟨id(v), text(v), meta(v)⟩; meta gồm mã văn bản, **ngày ban hành**, cơ quan ban hành, **tình trạng pháp lý**. ID tất định theo lược đồ chặt (ví dụ `DocID::UnitID`) → tham chiếu ổn định, **truy vết chuỗi sửa đổi**, nạp tăng dần. Đồ thị tổ chức như **lớp nền phẳng** (các nút đơn vị pháp lý cùng mặt phẳng, truy hồi trực tiếp) chứ không phải pipeline từ trên xuống.
- **Quan hệ cấu trúc** R_struct = {Has_Article, Has_Clause}: giữ phân cấp và provenance.
- **Quan hệ ngữ nghĩa pháp lý** R_legal = {Amends, Replaces, Supplements, Refers_To}: phụ thuộc liên văn bản ảnh hưởng diễn giải và hiệu lực.
- Mọi quan hệ rút ra bằng **mẫu quy tắc (rule-based pattern matching)** trên cách diễn đạt pháp lý chuẩn, ví dụ "sửa đổi Điều X", "bổ sung Khoản Y", "căn cứ Điều Z" → độ chính xác cao, tránh liên kết giả.
- **Nút giữ chỗ (placeholder)**: khi nút tham chiếu đơn vị chưa có trong kho thì tạo nút nhẹ giữ chỗ; tự phân giải khi văn bản đó được nạp sau → đồ thị đầy đủ dần mà không phá truy hồi.

**Truy hồi hạt giống + lan truyền (seeded retrieval + propagation)**
- *Seeded retrieval*: trên lớp nền đơn vị pháp lý, chọn K nút hạt giống S_K(q) bằng điểm lai **s(v,q) = λ·s_dense(v,q) + (1−λ)·s_sparse(v,q)** (dày = tương đồng embedding; thưa = từ vựng, ví dụ BM25).
- *Propagation* — ba luồng có nguyên tắc, theo cạnh chuyên biệt N_r(v) = {u | (v,r,u) ∈ E}:
  1. **Validity tracing** (r ∈ {Amends, Replaces, Supplements}): duyệt đệ quy chuỗi sửa đổi đến khi gặp **nút cuối (terminal)**: u là terminal nếu với mọi quan hệ r′ trong tập đó N_r′(u) = ∅; **nút terminal được ưu tiên làm bằng chứng áp dụng được**.
  2. **Contextual supplementation** (Refers_To): chỉ mở rộng **láng giềng trực tiếp**, cho ngữ cảnh pháp lý cần thiết, ngăn trôi ngữ cảnh.
  3. **Provenance retrieval**: dùng quan hệ cấu trúc để lấy metadata văn bản cấp trên, bảo đảm dùng bằng chứng có nguồn gốc.
- *Context assembly*: C(q) = S_K(q) ∪ P(q) có biên; độ sâu lan truyền và loại quan hệ bị ràng buộc rõ ràng trước khi đưa cho agent phía sau.

**Hệ đa agent (MAS) nhẹ, 4 agent**
- **Interpreter**: phân tích ý định và định tuyến; xác định có phải câu hỏi quy định không, trích tín hiệu như mã văn bản, quyết định có cần truy hồi đồ thị không (tránh truy hồi thừa).
- **Pathfinder**: lõi truy hồi nhận biết đồ thị (seeded retrieval + validity tracing + mở rộng tham chiếu có biên); trả tập ngữ cảnh nhất quán pháp lý, cập nhật.
- **Auditor**: kiểm chứng bằng chứng và đầu ra trung gian (nhất quán giữa nút, quan hệ, mệnh đề sinh ra); kiểm tra grounding và an toàn, phát hiện nội dung không có căn cứ/ảo giác.
- **Conductor**: điều phối; gọi LLM sinh câu trả lời cuối từ ngữ cảnh đã kiểm; khi Auditor báo thiếu căn cứ thì ép hành vi thận trọng (từ chối trả lời hoặc yêu cầu làm rõ).

## 3. WHAT – Thực nghiệm và kết quả

### 3.1 Thiết lập
- Đánh giá trên tập test ViHERMES (1.560 mẫu): các mẫu hình suy luận gồm lần sửa đổi, giải quyết phụ thuộc xuyên văn bản, và ghép điều khoản có xét hiệu lực.
- **Baseline** (3 họ): Naive RAG (BM25 / dense / hybrid nội suy có trọng số); **IRCoT** (xen kẽ truy hồi với chain-of-thought); graph-based: **RAPTOR** (cây tóm tắt đệ quy), **MiniRAG** (SLM + chỉ mục đồ thị dị thể), **LightRAG**, **HippoRAG 2**.
- **Chỉ số**: token-level **F1**; **LLM-as-a-Judge** (đúng, đầy đủ, nhất quán với bằng chứng); **Recall@k** = |E_gold ∩ E_retrieved^(k)| / |E_gold| (tỷ lệ ngữ cảnh vàng được phục hồi trong top-k).
- Cùng backbone cho mọi hệ: **GPT-4o-mini** sinh câu trả lời; embedding **OpenAI text-embedding-3-small**; judge **GPT-4o** với rubric chuẩn; hyperparameter mặc định cho baseline (hiệu năng "out-of-the-box").

### 3.2 Bảng 3 – Chất lượng QA (test)
| Phương pháp | F1 | LLM Judge | Recall@5 |
|---|---|---|---|
| Naive RAG (BM25) | 0,3076 | 0,2027 | 0,2617 |
| Naive RAG (Dense) | 0,3289 | 0,2433 | 0,3241 |
| Naive RAG (Hybrid) | 0,4127 | 0,3324 | 0,3989 |
| IRCoT | 0,4835 | 0,3751 | 0,4254 |
| MiniRAG | 0,5429 | 0,4856 | 0,5083 |
| RAPTOR | 0,5941 | 0,5783 | 0,5563 |
| LightRAG | 0,7855 | 0,6756 | 0,7256 |
| HippoRAG 2 | 0,8023 | 0,7332 | 0,8032 |
| **Ours (SRKG + MAS)** | **0,8334** | **0,7554** | **0,8461** |
| − Auditor | 0,8150 | 0,6823 | 0,8267 |
| − Interpreter | 0,6540 | 0,5434 | 0,6134 |
| − Pathfinder (thay bằng truy hồi dày–thưa trên đơn vị phẳng) | 0,7734 | 0,6927 | 0,7955 |

Nhận xét của tác giả: tiến trình rõ từ RAG phẳng → multihop → graph; hybrid > dense > BM25; IRCoT cải thiện nhưng vẫn không có nhận thức cấu trúc; graph-based tốt hơn hẳn, LightRAG/HippoRAG 2 cao nhất trong nhóm; hệ đề xuất **hơn HippoRAG 2 +3,1 điểm F1** (0,8334 vs 0,8023) và cao nhất trên cả ba chỉ số.
- **Ablation**: bỏ Interpreter làm giảm mạnh nhất (F1 0,8334 → 0,6540, −18,0 điểm: định tuyến ý định quan trọng nhất); bỏ Auditor làm giảm độ tin cậy suy luận (LLM Judge 0,7554 → 0,6823); thay Pathfinder bằng truy hồi phẳng cũng giảm (F1 0,7734, LLM Judge 0,6927).

### 3.3 Bảng 4 – Hiệu quả suy luận và xây đồ thị
| Phương pháp | Độ trễ TB (s) | Token TB | Nút | Cạnh | Token đồ thị |
|---|---|---|---|---|---|
| BM25 | 4,1139 | 3.009,8 | – | – | – |
| Dense | 6,1139 | 3.043,3 | – | – | – |
| Hybrid | 9,2348 | 3.289,3 | – | – | – |
| IRCoT | 11,8312 | 4.457,5 | – | – | – |
| MiniRAG | 13,1923 | 4.224,7 | 2.988 | 4.323 | 3.270.523 |
| RAPTOR | 14,2325 | 4.320,5 | 3.352 | 7.234 | 3.436.236 |
| LightRAG | 17,3236 | 4.558,3 | 3.569 | 9.332 | 3.684.343 |
| HippoRAG 2 | 22,0278 | 4.859,4 | 2.988 | 11.183 | 3.966.963 |
| **Ours** | 14,7415 | 4.236,5 | 3.727 | 12.540 | 3.397.126 |

- Hệ đề xuất có đồ thị **lớn nhất** (3.727 nút, 12.540 cạnh) nhưng **ít token đồ thị hơn** LightRAG và HippoRAG 2 (3,40M vs 3,68M / 3,97M); độ trễ 14,74 s ≈ RAPTOR (14,23 s), nhanh hơn HippoRAG 2 (22,03 s) và LightRAG (17,32 s).
- Số nút ≈ 3.727 cho thấy kho thực tế nhỏ (cỡ vài nghìn đơn vị), điều này suy ra từ bảng, không được bài mô tả riêng.

## 4. Kết luận và hạn chế do tác giả nêu
- Cấu trúc hình thức hóa pháp lý + lan truyền theo quan hệ + xác minh cho kết quả vượt baseline mạnh với độ trễ cạnh tranh.
- Công thức "structure-driven" áp dụng được cho miền quy định khác có tổ chức phân cấp và phụ thuộc liên văn bản.
- **Hướng tương lai (là hạn chế thừa nhận)**: (a) **kiểm soát khối lượng lan truyền (constraining propagation volume)**; (b) **làm giàu hiệu lực thời gian (enriching temporal validity)** cho triển khai thực tế → tức là bài *chưa* mô hình hiệu lực thời gian đầy đủ.

## 5. Nhận xét phê phán (của người đọc, không phải của tác giả)
- Dữ liệu **sinh bằng LLM** (GPT-style) rồi người xác minh; không báo tỷ lệ chấp nhận/loại, kappa liên annotator, số annotator, hay chuyên gia kiểm bao nhiêu mẫu. Chất lượng gold chưa lượng hóa → rủi ro đối với khóa luận khi trích làm mẫu quy trình.
- Đánh giá dùng **LLM-judge (GPT-4o)** và F1 token mức bề mặt; backbone sinh là GPT-4o-mini. Đây là điểm đối lập trực tiếp với tinh thần chấm tất định của FiscalQA Pro (bài 1).
- Quan hệ pháp lý (Amends/Replaces/Supplements/Refers_To) trích bằng **regex mẫu câu**: tin được cho cách viết chuẩn; chưa báo độ chính xác/độ phủ của việc trích quan hệ; phụ thuộc cách diễn đạt chuẩn của văn bản VN.
- Không nêu rõ cách "nút terminal" xử lý khi một điều bị nhiều văn bản sửa với **hiệu lực chồng lấn/khác ngày**, hoặc câu hỏi cần bản **tại một ngày trong quá khứ** (validity tracing luôn ưu tiên bản mới nhất). Đây chính là khoảng trống mà ViLexTime lấp (point-in-time).
- Mô tả có ví dụ nhưng ví dụ Bảng 1 là tổng hợp thủ tục, **không** minh họa chuỗi sửa đổi dù tác giả nói bộ dữ liệu có mẫu hình đó; không nêu tỷ lệ các mẫu hình (amendment tracing / cross-document comparison / procedural synthesis).
- Hop ở đây = số ngữ cảnh từ **tiêu đề văn bản khác nhau** ghép lại, nên "hop" thiên về **tổng hợp** hơn là chuỗi suy diễn có thứ tự.

## 6. Dùng gì cho khóa luận ViLexTime
1. **Baseline GraphRAG tiếng Việt có sẵn**: cùng nhóm baseline (BM25/Dense/Hybrid, IRCoT, RAPTOR, MiniRAG, LightRAG, HippoRAG 2) và cùng chỉ số (F1, LLM-judge, Recall@k) → khóa luận có thể chạy lại trên ViLexTime để so sánh và để đối chiếu với con số ViHERMES (F1 0,80 của HippoRAG 2 trên tập multihop không có thời gian).
2. **Mẫu quy trình xây dữ liệu**: spherical K-Means → ngữ cảnh đại diện → bộ ngữ cảnh khác văn bản + giới hạn chồng lấn τ → LLM sinh → kiểm cấu trúc → chuyên gia rà. Có thể thay "bước lấy mẫu" bằng lấy mẫu theo **cặp phiên bản/điểm trôi giá trị** (xem bài 1) để sinh câu hỏi theo thời gian.
3. **Lược đồ SRKG**: nút Document/Clause/Article + `meta` (ngày ban hành, cơ quan, tình trạng pháp lý) + ID tất định `DocID::UnitID` + nút placeholder cho tham chiếu chưa có → rất hợp với văn bản quy phạm VN; cần **bổ sung** `valid_from/valid_to` (hiệu lực) và nút phiên bản theo kiểu SAT-Graph RAG (bài 2).
4. **Validity tracing** (đi theo Amends/Replaces/Supplements đến nút cuối) là phiên bản "hiện tại" của bài toán; khóa luận cần tổng quát thành **tracing có điều kiện ngày** (dừng ở nút mà `valid_from ≤ t < valid_to`).
5. **Regex trích quan hệ** từ cụm "sửa đổi Điều X / bổ sung Khoản Y / căn cứ Điều Z" là điểm khởi đầu thực tế cho việc dựng cạnh sửa đổi; cần đo precision/recall của việc này (bài chưa làm).
6. **Ablation theo agent** (Interpreter/Auditor/Pathfinder) là cách trình bày đóng góp từng thành phần; hành vi từ chối/làm rõ của Conductor hợp với yêu cầu chống ảo giác.
7. **Khoảng trống để trích dẫn**: tự bài nói cần "enriching temporal validity" trong hướng tương lai → có thể dùng làm luận cứ cho động lực ViLexTime.
