# An Ontology-Driven Graph RAG for Legal Norms: A Structural, Temporal, and Deterministic Approach (SAT-Graph RAG)

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf`.

## 0. Thông tin chung

| Mục | Nội dung |
|---|---|
| Tác giả | Hudson de Martim (Thượng viện Liên bang Brazil) |
| Nơi đăng | arXiv:2505.00039v5 [cs.CL], 11/09/2025. Bản đăng JURIX 2025 (Frontiers in AI and Applications, IOS Press, tr. 282–287, theo trích dẫn của bài FiscalQA Pro) |
| Loại bài | Đề xuất khung kiến trúc + **case study định tính** (không có thực nghiệm định lượng, không có benchmark) |
| Dữ liệu minh họa | Hiến pháp Liên bang Brazil 1988 và các Tu chính án đến đầu 2024 (hơn 100 tu chính án) |
| Công trình nền | [2] De Martim, *Modeling the Diachronic Evolution of Legal Norms: an LRMoo-based, component-level, event-centric approach to legal KGs* (arXiv:2506.07853) |
| Độ gần với ViLexTime | Cao về **mô hình đồ thị thời gian**; thấp về đánh giá (chưa có số liệu) |

## 1. WHY – Bài toán và khoảng trống

- RAG phẳng ("flat-text") mù trước ba tính chất của luật: **cấu trúc phân cấp** (phần, chương, điều, khoản), **mạng tham chiếu chéo dày đặc**, và **tiến hóa theo thời gian** (sửa đổi, bãi bỏ, hợp nhất). Hệ "temporally-naïve" không truy hồi tất định được bản luật có hiệu lực tại một ngày lịch sử → câu trả lời **lỗi thời thời điểm (anachronistic)**, không chấp nhận được ở lĩnh vực rủi ro cao cần chính xác và kiểm toán được.
- Ba khoảng trống tác giả nêu:
  1. Hầu hết RAG pháp lý coi văn bản là các chunk phẳng, hiếm khi tích hợp tường minh cấu trúc quy phạm.
  2. Nghiên cứu Temporal KG (TKG) tập trung biểu diễn và dự đoán liên kết; ít công trình kết hợp (ở quy mô lớn, có provenance) **tiến hóa quy phạm** (phiên bản điều/luật) với cơ chế RAG.
  3. Thiếu benchmark/dataset kết hợp truy hồi pháp lý với yêu cầu thời gian và phân cấp. (Bài chỉ đặt nền móng cho khoảng trống này bằng đề xuất bộ chỉ số.)
- Vì sao không dùng Graph RAG chuẩn (Edge et al. 2024, entity-centric): (a) mô hình thực thể–khái niệm **mù cấu trúc hình thức** của văn bản (vị trí của một quy định trong chương/phần quyết định phạm vi và ý nghĩa); (b) NER tối ưu cho danh từ riêng (người, tổ chức, nơi chốn), vốn **thưa thớt** trong văn bản quy phạm trừu tượng, vô nhân xưng; "mạng ngữ nghĩa" của luật được dệt từ **khái niệm pháp lý** (hành vi hành chính, thủ tục tố tụng...) mà NER chuẩn không bắt được → đồ thị thưa và nghèo ngữ nghĩa. Do đó chuyển sang cách **top-down**, dùng cấu trúc hình thức làm xương sống thay vì bottom-up trích thực thể.

## 2. HOW – Khung SAT-Graph RAG

Tên gọi: **S**tructure-**A**ware **T**emporal Graph RAG = (góc nhìn cấu trúc: dùng phân cấp nội tại làm xương sống) + (góc nhìn thời gian: mô hình hóa tiến hóa của từng thành phần cấu trúc).

### 2.1 Nền ontology: LRMoo (IFLA)
- Chọn **LRMoo** (hướng đối tượng của IFLA LRM) thay vì Akoma Ntoso. Lý do: Akoma Ntoso mã hóa các tầng Work/Expression/Manifestation như **định danh metadata** trong khối `<meta>`; còn khung này nâng chúng thành **thực thể bản thể hạng nhất**, cho phép xây chuỗi phiên bản có thể duyệt ngay trong đồ thị.

### 2.2 Bốn kiểu nút chính
| Nút | Vai trò | Ánh xạ LRMoo |
|---|---|---|
| **Norm (Work)** | Một văn bản quy phạm như một sáng tạo trí tuệ trừu tượng (ví dụ "Hiến pháp Liên bang 1988"); danh tính độc lập với lời văn/tu chính cụ thể | F1 Work |
| **Component (Work)** | Phần tử phân cấp (phần/chương/điều/khoản...) như khái niệm trừu tượng; giữ danh tính dù văn bản đổi | Component Work |
| **Temporal Version (TV/CTV)** | "Ảnh chụp thời gian" không phụ thuộc ngôn ngữ của Norm/Component tại một thời điểm; CTV = TV của một Component. Nắm nội dung ngữ nghĩa + cấu trúc logic | F2 Expression |
| **Language Version (LV/CLV)** | Hiện thực hóa văn bản của một TV bằng một ngôn ngữ (ví dụ văn bản tiếng Bồ Đào Nha của phiên bản 1988-10-05 của điều đó); CLV = LV của một CTV | F2 Expression suy từ một TV |

Phân tách "cái gì" (Work) / "khi nào" (TV) / "thế nào" (LV).

### 2.3 Xây đồ thị từ văn bản
- Bước đầu **không phải chunking ngây thơ** mà là **phân đoạn ngữ nghĩa nhận biết cấu trúc**: tách văn bản thô thành đoạn ứng với phần tử phân cấp (title, chapter, article, paragraph) bằng parser chuyên dụng hoặc LLM tinh chỉnh, lý tưởng có người duyệt.
- Tạo một nút Norm và nhiều nút Component (xương sống phân cấp).
- Với mỗi Component và mỗi thời điểm văn bản được ban hành/sửa: tạo một **CTV** (nội dung ngữ nghĩa tại ngày đó) và một **CLV** (lời văn trong một ngôn ngữ).
- **Text Unit** (đoạn văn bản dùng để nhúng/truy hồi) chỉ liên kết với tầng cụ thể nhất là **CLV**. Liên kết thẳng chunk vào Component (Work) vô thời gian là sai khái niệm. Mọi nội dung truy hồi được đều gắn rõ với một trạng thái ngữ nghĩa (CTV) và một biểu đạt ngôn ngữ (CLV).
- Hiệu quả đa ngôn ngữ: thêm bản dịch tiếng Anh chỉ cần tạo thêm LV/CLV mới trỏ về CTV sẵn có; cấu trúc trừu tượng và thời gian **không bị đụng**.

### 2.4 Phiên bản thời gian là **Aggregation**, không phải Composition
- Khi một thành phần được sửa ngày D: tạo CTV mới cho nó; các tổ tiên (lên đến Norm) cần CTV mới phản ánh trạng thái hợp nhất mới.
- Cách ngây thơ (**Composition**): CTV cha mới gồm các CTV mới của *mọi* con, kể cả con không đổi → dư thừa dữ liệu khổng lồ và che mất cái gì thực sự thay đổi.
- Cách được chọn (**Aggregation**): CTV cha mới tại D_n được lập bằng cách **gộp CTV mới nhất hiện có của từng con**; trỏ tới CTV mới của con bị sửa và **tái sử dụng** CTV cũ của các con không đổi. Một CTV con có thể được dùng bởi nhiều CTV cha tại các thời điểm khác nhau.
- Ví dụ trong bài (Hình 5): CTV 1988-10-05 của `tit2_cap2` được gộp vào CTV 1993-09-14 của `tit2` (Chương không đổi, tái dùng). Hình 6: `v2` của `c1` gộp `v2` mới của C2 nhưng tái dùng `v1` của C3 không đổi.
- Lợi ích: biểu diễn kinh tế, không mơ hồ, và cho phép **dựng lại tất định toàn văn đúng của mọi quy định tại một ngày** bằng cách truy hồi tổ hợp đúng các phiên bản con.

### 2.5 Nhân quả và metadata thành đơn vị truy hồi
**(a) Sự kiện lập pháp = nút Action.**
- Mỗi thay đổi hạt mịn có một Action (sửa đổi, bãi bỏ, ban hành gốc), nối: (1) điều khoản nguồn ra lệnh thay đổi, (2) CTV bị chấm dứt (nếu có), (3) CTV mới tạo ra. Với ban hành gốc thì không có CTV tiền nhiệm và không có công cụ ra lệnh riêng: Action chỉ là sự kiện tạo CTV đầu tiên.
- Mỗi Action có một Text Unit mô tả tự nhiên có cấu trúc. Ví dụ trong bài: "Tu chính án Hiến pháp số 26 ngày 14/02/2000, qua caput Điều 1, đưa ra cách viết mới cho caput Điều 6 ... chấm dứt hiệu lực bản gốc (từ 1988-10-05) vào 2000-02-14 và lập bản mới hiệu lực từ 2000-02-15, nội dung: 'Các quyền xã hội gồm giáo dục, y tế, lao động, nhà ở, giải trí, an ninh, ...'". Nhúng văn bản này làm **sự kiện lập pháp truy hồi được** → trả lời được câu hỏi về lịch sử, tiến hóa, hành vi gây thay đổi.
- Hình 7: Action từ CA 26 chấm dứt CTV 1988-10-05 của caput Điều 6 và sinh CTV 2000-02-14.

**(b) Metadata thành Text Unit (multi-aspect retrieval).**
- Thông tin như ngày công bố, tên khác, quan hệ kế thừa/tương quan giữa các luật thường nằm trong metadata có cấu trúc nên "vô hình" với truy hồi văn bản. Với mỗi Norm/Component/TV, sinh Text Unit riêng cho từng thuộc tính hay quan hệ thông tin.
- Quan hệ thông tin (không tạo phiên bản mới) khác Action: ví dụ "Hiến pháp 1967 của Brazil kế thừa Hiến pháp 1946 của Hợp chúng quốc Brazil" (chấm dứt hiệu lực Work như một tổng thể), hay "Hiến pháp 1988 công bố ngày 05/10/1988".
- Triển khai ý tưởng **multi-aspect embedding** [16]: nhiều vector cho một thực thể (nội dung, từng Action, từng thuộc tính/quan hệ) → tìm luật theo nội dung, thuộc tính hoặc liên kết.

### 2.6 Truy hồi nhận biết cấu trúc qua "cộng đồng có người tuyển chọn"
Khác Graph RAG gốc dùng phát hiện cộng đồng bằng thuật toán, ở đây dùng hai dạng cộng đồng sẵn có của luật:
1. **Cộng đồng cấu trúc**: phân cấp nội tại (Title, Chapter, Section); mỗi nút nhóm là một cộng đồng chứa mọi hậu duệ.
2. **Cộng đồng chủ đề**: phân loại ngoài do con người tuyển chọn (thesaurus: "An sinh xã hội", "Luật môi trường") → nút **Theme** có Text Unit mô tả riêng (để tìm được bằng tìm kiếm ngữ nghĩa), liên kết tới Norm/Component liên quan → cộng đồng chủ đề xuyên văn bản.
- Cơ chế: người dùng/hệ thống chọn **điểm vào** (Theme, Norm, Component hoặc một Version); hệ thống duyệt đồ thị thu mọi Text Unit (của nút và hậu duệ), rồi mới **tìm vector chỉ trên tập con đã lọc**. Biến tìm kiếm phẳng toàn kho thành "điều hướng ngữ nghĩa": nhanh hơn và chính xác hơn vì phạm vi bị khóa trước.

## 3. WHAT – Case study và các mẫu truy vấn

### 3.1 Kiến trúc triển khai (khái niệm, chưa triển khai thật)
- Kho quan hệ–vector, ví dụ **Oracle Database 23ai** (bảng cho Theme, Norm_Component, Temporal Version, Language Version, Action; bảng phụ và khóa ngoại cho quan hệ; bảng Text Unit có cột vector); không cần graph DB riêng.
- Embedding: **Qwen3 Embedding** (đa ngôn ngữ, tự host); sinh câu trả lời: **Gemini 1.5 Flash**. Khung "tool-agnostic": có thể dùng Neo4j, Pinecone, FAISS...
- Nạp dữ liệu bán tự động từ bản hợp nhất đa thời điểm của Hiến pháp + các tu chính án; các sự kiện trong mỗi tu chính án mô hình hóa thành Action nối điều khoản nguồn với thành phần đích.
- Phần này dùng điều kiện "could/would" (chưa có triển khai kiểm chứng).

### 3.2 Ví dụ nền: caput Điều 6 (quyền xã hội)
Bản gốc 1988-10-05 → CA 26/2000 (thêm "nhà ở/moradia", hiệu lực 2000-02-15) → CA 64/2010 (thêm "thực phẩm/alimentação", hiệu lực 2010-02-04) → CA 90/2015 (thêm "giao thông vận tải"). Mô hình hóa CA 26: Action + chấm dứt CTV 1988 + tạo CTV 2000-02-14 + tạo CLV + Text Unit + lan truyền phiên bản lên Chương/Phần (tái dùng anh em không đổi).

### 3.3 Ba mẫu truy vấn (đánh giá **định tính** so với "RAG chuẩn" = chỉ mục phẳng của bản hiện hành)

**Mẫu 1 – Truy hồi theo thời điểm (point-in-time).** Ví dụ: "Các quyền xã hội nêu ở Điều 6 Hiến pháp năm 1999 là gì?"
- RAG phẳng: trả bản hiện hành → liệt kê cả nhà ở, thực phẩm vốn thêm sau → **anachronistic**; ngay cả khi chỉ mục có văn bản các tu chính án, truy hồi vẫn không bị ràng buộc bởi khoảng hiệu lực.
- SAT-Graph RAG (kế hoạch tất định):
  1. **Planner** (LLM biết schema) chuyển câu hỏi thành ràng buộc có cấu trúc: đích cấu trúc (ánh xạ "Điều 6" tới ComponentID chuẩn, ví dụ URN `urn:lex:br:federal:constituicao:1988-10-05;1988!art6`, xử lý bí danh); phạm vi thời gian ("năm 1999" = khoảng [1999-01-01, 1999-12-31], không dùng mốc tùy tiện 31/12; **nếu không nêu thời gian thì mặc định t = now()**); ràng buộc ngôn ngữ/định dạng.
  2. **Phân giải phạm vi thời gian qua duyệt đồ thị**: lấy Component đích và mọi hậu duệ có văn bản (Art. 6, caput, các item), duyệt chuỗi CTV, chọn phiên bản thỏa `tv.valid_start ≤ t < coalesce(tv.valid_end, +∞)`. Khi một khoảng có nhiều CTV, áp **chính sách phân giải thời gian**, mặc định **SnapshotLast** (`t* = sup{t ∈ [t1, t2]}`, trả CTV hiệu lực tại t*), và **công bố chính sách trong câu trả lời**.
  3. Truy hồi CLV rồi Text Unit tương ứng theo ngôn ngữ yêu cầu.
  4. **Sinh dựa trên sự kiện (fact-grounded)**: với truy vấn liệt kê, LLM được chỉ thị **trích nguyên văn (extractive, copy-based)**, giữ nguyên liệt kê và gắn trích dẫn tới CTV/CLV; tùy chọn lộ Action khởi/kết thúc phiên bản.
- Kết quả minh họa: "Năm 1999, các quyền xã hội ở Điều 6 gồm giáo dục, y tế, lao động, giải trí, an ninh, an sinh xã hội, bảo vệ thai sản và thiếu nhi, hỗ trợ người nghèo."
- Mở rộng: khoảng thời gian, phân biệt ngày ban hành và ngày hiệu lực, truy hồi đa ngôn ngữ có fallback, thay đổi phạm vi chỉ bằng đổi nút vào (phạm vi cấu trúc nội bộ hoặc chủ đề ngoài, ví dụ nút Theme "Social Security").

**Mẫu 2 – Phân tích tác động theo phân cấp.** Ví dụ: "Tóm tắt mọi thay đổi văn bản ở các thành phần trong Chương II ('Các quyền xã hội') sau năm 2010."
- RAG phẳng: không có biểu diễn phân cấp nên không xác định được thành phần nào thuộc Chương II.
- SAT: (1) planner nhận diện nút Chương II và cửa sổ thời gian, và chọn **chính sách thành viên phạm vi** (mặc định **snapshot-anchored**: gồm mọi thành phần thuộc Chương II ở *đầu* cửa sổ; thay thế: action-time, lifetime — để xử lý tái cấu trúc phân cấp theo thời gian; luôn công bố chính sách); (2) duyệt xuống lấy hậu duệ; (3) **gộp nhân quả**: lấy mọi Action tác động lên các CTV của các thành phần đó trong cửa sổ; (4) LLM tổng hợp bản tóm tắt phân cấp từ các Text Unit mô tả Action.
- Đầu ra minh họa (không phải kết quả thực nghiệm): Art. 6 caput: 2 sửa đổi (CA 64/2010 thêm "thực phẩm"; CA 90/2015 thêm "giao thông"); Art. 7: 1 sửa đổi (CA 72/2013 mở rộng quyền lao động giúp việc gia đình); ngày tác động cấp chương {2010-02-04, 2013-04-02, 2015-09-15}.

**Mẫu 3 – Dựng lại provenance và dòng nhân quả.** Ví dụ: "Truy vết toàn bộ dòng lập pháp đã đưa từ 'thực phẩm' vào Điều 6."
- RAG phẳng: có thể tìm mảnh văn bản chứa từ này nhưng không quy được thay đổi cho một văn bản pháp luật cụ thể hay dựng lại thứ tự thời gian của các lần sửa.
- SAT: planner chọn chiến lược **structure-first** vì có cả đích cấu trúc ("Điều 6") lẫn đích văn bản ("food"): (1) phân tích ràng buộc; (2) phân giải phạm vi phân cấp (nút + cây con); (3) **định vị đoạn văn bản bị ràng buộc**: tìm "food" chỉ trong lịch sử phiên bản của các thành phần trong phạm vi (chỉ mục từ vựng + ngữ nghĩa); (4) với mỗi đoạn tìm được, duyệt tới Action đã tạo CTV chứa nó; (5) lần ngược chuỗi Action theo thời gian thành **DAG có thứ tự tất định**; (6) sinh báo cáo provenance (chuỗi Action, đoạn "trước/sau", chú thích kiểm toán dạng JSON).
- Nếu câu hỏi không có đích cấu trúc, planner chuyển sang **span-first**: tìm "food" toàn kho trước rồi dùng đồ thị dựng provenance cho từng vị trí.
- Báo cáo minh họa: trạng thái trước (đến 2010-02-03, không có "food", lần đổi cuối do CA 26/2000), sự kiện nhân quả (Action CA 64/2010, hiệu lực 2010-02-04, chèn từ "food"), trạng thái sau (từ 2010-02-04), vết kiểm toán (chuỗi [Action(CA26/2000)] → [Action(CA64/2010)]; Match Confidence: Exact 1,0; phụ lục JSON).

### 3.4 Chiến lược thực thi hợp nhất (mục 4.4)
Tám bước tổ hợp: (1) chuẩn hóa ràng buộc cấu trúc/thời gian/văn bản; (2) phân giải phạm vi trên phân cấp (khai báo chính sách thành viên); (3) chọn chiến lược (structure-first / span-first / time-first); (4) chọn CTV tất định theo chính sách thời gian (ví dụ SnapshotLast); (5) truy hồi Text Unit theo phạm vi (lọc cấu trúc + thời gian rồi xếp hạng vector/từ vựng); (6) gộp nhân quả các Action và Text Unit mô tả; (7) lắp chuỗi provenance (DAG Action); (8) sinh dựa trên sự kiện, công bố chính sách và phụ lục JSON (vết provenance + điểm tin cậy).
- Đường đi theo loại truy vấn: **point-in-time** = 1,2,3,4,5,8; **impact** = 1,2,3,6,5,8; **provenance** = 1,2,3,5,6,7,8.
- Mặc định vận hành nên công bố để tái lập: embedding (ví dụ Qwen-3, **256 chiều**), tương đồng **cosine, k = 8**, chính sách thời gian mặc định SnapshotLast. Mọi câu trả lời phải nêu chính sách thời gian/thành viên đã dùng và đính phụ lục JSON provenance khi có Action.

## 4. Thảo luận, hạn chế và hướng tương lai (mục 5–6)
- **Quy mô và bảo trì**: cần pipeline nạp tự động có người kiểm; tính trước chỉ mục và hiện thực hóa sẵn ảnh chụp thời gian phổ biến; xử lý luật mới tăng dần. Đánh đổi: đầu tư biên tập và lưu trữ để có tính tất định và hiệu năng.
- **Phụ thuộc chất lượng dữ liệu nguồn**: tính tất định *khuếch đại* lỗi nguồn: khoảng hiệu lực sai hay metadata Action sai → truy hồi sai có hệ thống. Giảm thiểu: đối chiếu nhiều nguồn, điểm tin cậy cho đầu ra, quy trình kiểm định/rollback.
- **Phạm vi**: tối ưu cho luật thành văn nơi phân cấp và hành động sửa đổi rõ ràng, chuẩn. Án lệ cần mô hình khác (đồ thị trích dẫn, thứ bậc tư pháp, trôi dạt học thuyết). Hợp đồng/quy định: không đồng nhất cấu trúc, cần luật phân đoạn riêng. Ngoài luật: hợp đồng thương mại (sửa đổi, viết lại), tài liệu kỹ thuật (phiên bản, thay đổi API).
- **Đánh giá và chỉ số (đề xuất, chưa đo)**: cần benchmark chuyên biệt (bộ cặp hỏi–đáp trên kho có lịch sử sửa đổi phức tạp):
  - Truy hồi thời gian tất định: **Temporal Precision** (tỷ lệ CTV truy hồi đúng cho ngày/khoảng được hỏi), **Temporal Recall** (tỷ lệ CTV vàng được truy hồi).
  - Phân tích tác động: **Action-Attribution Accuracy** (F1 xác định đủ các Action tác động lên CTV trong phạm vi/cửa sổ), **Summary Completeness**.
  - Provenance: **Causal-Chain Completeness**.
  - Đo người dùng: giảm thời gian trả lời tác vụ tra cứu phức tạp; cảm nhận tin cậy và khả năng kiểm toán.
- **Đạo đức**: minh bạch chính sách phân giải; "justice gap" (chỉ nơi giàu dữ liệu máy đọc được mới xây được); nhật ký kiểm toán bất biến cho mọi thao tác tuyển chọn đồ thị. Hệ chỉ cho "đầu ra trợ lý có thể kiểm chứng", không phải tư vấn pháp lý.
- **Hướng tương lai**: công bố ontology OWL chính thức; benchmark có chú thích; áp dụng cho miền khác; mô hình lai (cấu trúc top-down + đồ thị thực thể bottom-up kiểu Graph RAG); công cụ trực quan hóa provenance.

## 5. Tài liệu tham khảo đáng lần theo
- [1] Lewis et al. 2020 (RAG gốc); [2] De Martim 2025 (mô hình LRMoo cấp thành phần, nền của bài này, arXiv:2506.07853); [3] Edge et al. 2024 (Graph RAG, arXiv:2404.16130); [4] LRMoo v1.0 IFLA 2024; [5] LegalBench-RAG (Pipitone 2024, arXiv:2408.10343, truy hồi là nút cổ chai); [6] Louis et al. 2023 (GNN cho truy hồi điều luật, arXiv:2301.12847); [8] Ho et al. 2025 (cấu trúc pháp lý trong RAG, fair use); [9] Cai et al. 2024 (khảo sát TKG); [10] Hooshafza 2022; [11] Akoma Ntoso (Palmirani–Vitali); [12] LegalHTML (Stellato 2023); [13] Zhu 2025 (TKG dataset); [14] Barron 2025 (RAG + KG + NMF phân cấp); [15] Oliveira Lima 2008; [16] Park 2020 (multi-aspect network embedding).

## 6. Dùng gì cho khóa luận ViLexTime

**Áp dụng được**
1. **Mô hình dữ liệu**: Norm/Component (Work) tách khỏi TV/CTV (phiên bản thời gian) và LV/CLV (lời văn). Với luật Việt: Điều/Khoản/Điểm là Component bền vững; mỗi lần văn bản sửa đổi tạo CTV mới với `valid_start`/`valid_end`; Text Unit gắn vào CLV.
2. **Aggregation** thay Composition khi lan truyền thay đổi lên cha (Điều → Mục → Chương → Văn bản), tránh nhân đôi dữ liệu và giúp biết "cái gì thực sự bị sửa".
3. **Action = sự kiện sửa đổi** là nút hạng nhất, có Text Unit mô tả → trả lời "ai/văn bản nào đã sửa, khi nào"; rất hợp với văn bản sửa đổi, bổ sung, thay thế, bãi bỏ (Nghị định sửa đổi Nghị định...). Ghi lại dạng 3 cạnh: điều khoản nguồn → CTV bị chấm dứt → CTV mới.
4. **Điều kiện hiệu lực** `valid_start ≤ t < coalesce(valid_end, +∞)` (nửa mở) + **chính sách phân giải thời gian công bố** (SnapshotLast) + mặc định `t = now()`. Cần quy ước rõ cho luật VN: ngày ký, ngày công bố, ngày có hiệu lực, hiệu lực hồi tố, hiệu lực từng phần.
5. **Ba loại truy vấn** làm phân loại câu hỏi benchmark: point-in-time, hierarchical impact, provenance; và **các chỉ số đề xuất** (Temporal Precision/Recall, Action-Attribution F1, Summary Completeness, Causal-Chain Completeness) làm sẵn bộ chỉ số mà khóa luận có thể hiện thực hóa.
6. **Planner nhận biết schema** với ba chiến lược (structure-first / span-first / time-first) và **công bố chính sách** với mỗi câu trả lời.
7. **Câu trả lời trích nguyên văn (extractive)** có gắn CTV/CLV: phù hợp mục tiêu chống ảo giác.
8. **Pre-filter bằng cấu trúc rồi mới tìm vector**; nút Theme cho lĩnh vực pháp luật.

**Cẩn trọng**
- **Không có thực nghiệm định lượng**; phần "RAG chuẩn sẽ ..." chỉ là suy diễn (dùng "would"). Đừng trích như bằng chứng thực nghiệm; trích như **mô hình/ý tưởng**. Bài FiscalQA Pro cũng nhận xét đây là "case study định tính".
- Cần quá trình dựng đồ thị phiên bản chính xác từ nguồn (văn bản hợp nhất, văn bản sửa đổi); tác giả thừa nhận lỗi nguồn bị khuếch đại → ViLexTime phải có kiểm định chất lượng đồ thị (mức khoảng hiệu lực và Action).
- Hiến pháp Brazil có ít văn bản và sửa đổi tường minh theo tu chính án; luật Việt Nam nhiều tầng văn bản dưới luật, nhiều văn bản sửa nhau, hiệu lực lồng nhau → phức tạp hơn (phần này suy ra từ mô tả của bài, bài không bàn).
- Bài ngầm cho rằng nguồn đã có **bản hợp nhất đa thời điểm** (văn bản hợp nhất chính thức); với Việt Nam, hợp nhất chính thức không phải lúc nào cũng có/đầy đủ.
- Bài FiscalQA Pro cho thấy ở câu hỏi một neo thì chỉ mục phiên bản đơn giản không cần đồ thị đã đạt ~98%; do đó giá trị đóng góp của đồ thị (Action, aggregation, impact, provenance) phải được chứng minh bằng loại câu hỏi mà chỉ đồ thị làm được (impact, provenance, so sánh nhiều phiên bản).
