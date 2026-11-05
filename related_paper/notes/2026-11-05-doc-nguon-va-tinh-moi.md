# Đọc 15 nguồn và khảo sát tính mới, 05/11/2026

**Lượt này chưa trọn vẹn.** 6/15 nguồn đọc hết thân bài, 8/15 chỉ đọc một phần, 1/15 chỉ có tóm tắt. Semantic Scholar bị chặn ở cả 12 truy vấn, OpenAlex bị chặn 8/12. ACM DL, IEEE Xplore, Google Scholar, SSRN, DBLP, OpenReview không mở được (mục 5).

Đây là lượt đọc trong dự án của một phiên AI, không phải phản biện ngoài. Chữ PDF trích bằng `pdftotext`, nên số trong hình và bảng bị vỡ không được dùng. "tr." là số trang in; "p." là trang PDF. "Thân bài" nghĩa là phần trước tài liệu tham khảo, chưa đọc phụ lục.

**Ba kết luận chính:**
1. Paper có 3 lỗi mô tả nguồn. Nặng nhất: Holm được dẫn sang Dror, trong khi Dror không bàn Holm.
2. Lượt khảo sát tìm ra 2 công trình rất gần mà repo chưa có: LawInForce-eCFR (AACL 2026) và NitiBench+ (arXiv, 3/11/2026). Đóng góp 3 của paper không còn là phát hiện riêng.
3. Câu "đầu tiên" ở guide §2.5 nên bỏ. Mục 4.3 có câu thay thế, nằm trong phạm vi đã tìm.

## 1. Bảng tóm tắt

| Key | Mức truy cập thật | Lỗi mô tả trong ch.2/paper | Bib so với bản gốc |
|---|---|---|---|
| `dror2018hitchhiker` | Toàn văn thân bài | **Có:** paper dẫn cho Holm | Khớp |
| `huwiler2025versionrag` | Toàn văn thân bài, chưa đọc phụ lục | **Có:** xếp nhầm vào mục pháp luật | Khớp (chỉ có v1) |
| `guo2025lightrag` | Một phần (tóm tắt, p.4–6, p.9) | **Có:** lý do phân biệt không đủ | Khớp |
| `prior2026oldfriend` | Toàn văn thân bài (v2) | Không sai | `checked` cần sửa; ICAIL chưa có bản ghi ACM |
| `prior2025consolidation` | Toàn văn thân bài, chưa đọc phụ lục | Không sai, cần thêm một giới hạn | Khớp |
| `han2025lawshift` | Thân bài p.1–10 (thiếu khoảng 2.000 ký tự cuối), chưa đọc phụ lục | Không sai, cần thêm một giới hạn | **Lệch:** "Xuxing, Ding"; thiếu trang |
| `thanh2021alqac` | Toàn văn | Không sai | Khớp (tên theo Crossref, đảo họ) |
| `lewis2020rag` | Một phần (tóm tắt, p.1–2, đoạn p.4) | Không sai | Khớp tên, tác giả; chưa đọc lại số trang |
| `karpukhin2020dpr` | Một phần (tóm tắt, đoạn p.2) | Không sai | Khớp |
| `robertson2009bm25` | Một phần (trang đầu, mở đầu) | Không sai | **Mâu thuẫn tập/trang**, xem 2.14 |
| `edge2024graphrag` | Một phần (tóm tắt, p.3, p.8–9, tìm từ khóa) | Không sai | Tiêu đề v1 khác v2 |
| `chen2021timeqa` | Một phần (tóm tắt, p.2, p.4, p.7, p.9) | Không sai | **Thiếu nơi đăng** NeurIPS D&B 2021 |
| `dhingra2022templama` | Một phần (tóm tắt, p.2–3) | Không sai | Khớp |
| `gardner2020contrast` | Một phần (tóm tắt, p.2, p.4) | Không sai; đóng được một `[CẦN XÁC MINH]` | Khớp tập, trang |
| `gwet2008ac1` | **Chỉ tóm tắt** (PubMed); PDF tác giả HTTP 404 | Không sai trong phạm vi tóm tắt | Khớp |

14 nguồn đầu theo ch.2 cộng `gwet2008ac1`, vì bảng cuối paper cũng ghi nó là mới có metadata. Bốn khóa đã đọc theo mục (`cymbler2026fiscalqa`, `demartim2025satgraph`, `nguyen2026vihermes`, `nguyen2025vlqa`) không đọc lại lượt này.

**Cập nhật bib ngoài danh sách:** `nguyen2026vihermes` đã có bản LNCS, DOI 10.1007/978-981-92-0071-9_22, tr. 321–336, sách *Intelligent Information and Database Systems* (Crossref). Tên sách này khớp chuỗi ACIIDS theo suy luận của tôi; Crossref không ghi tên hội nghị.

## 2. Từng nguồn

### 2.1 `dror2018hitchhiker`: toàn văn thân bài
- **Làm gì:** bài ý kiến về chọn kiểm định trong NLP, kèm khảo sát ACL và TACL 2017. Trong 180 bài thực nghiệm ACL 2017, chỉ 63 bài có kiểm định (tr. 1389).
- **Trích:** "in this paper we do not deal with the problem of drawing valid conclusions from multiple comparisons" (tr. 1383). "The test is less effective for small test sets" (bootstrap, tr. 1388). "The first open issue is that of dependent observations." (tr. 1390).
- **Liên quan:** chỗ dựa cho bootstrap ghép cặp và cho việc nêu vấn đề phụ thuộc giữa các dòng.
- **Câu đang viết:** **Sai.** Paper §5 viết "hiệu chỉnh Holm, α = 0,05 [@dror2018hitchhiker]". Từ "Holm" xuất hiện 0 lần trong thân bài. Bài chỉ nhắc Bonferroni khi thống kê thói quen của cộng đồng. Bài cũng không nói về bootstrap theo cụm.
- **Sửa:** Holm cần nguồn riêng. Bootstrap theo cụm cần nguồn riêng (mục 7).

### 2.2 `huwiler2025versionrag`: toàn văn thân bài
- **Làm gì:** đồ thị 5 tầng (category, document, version, content, change), định tuyến theo loại câu hỏi. VersionQA có 100 câu trên 34 tài liệu kỹ thuật, chấm bằng GPT-4.1 có người rà.
- **Số:** 90% so với RAG thường 58% và GraphRAG 64% (cấu hình DeepSeek-R1 70B, p.6). Token dựng chỉ mục 186K so với 2.970K (p.6).
- **Trích:** "The dataset focuses exclusively on technical documentation (Node.js, Apache Spark, Bootstrap)." (p.9). "require mapping calendar time to version releases, which our current system does not support" (p.9).
- **Liên quan:** đối chứng về biểu diễn phiên bản, không về luật. RAG thường trong bài "without version awareness" (p.5), và không có nấc chỉ lọc siêu dữ liệu. Vì vậy bài không trả lời được RQ3.
- **Câu đang viết:** **Sai chỗ.** Paper §2 đặt bài dưới tiêu đề "Hỏi đáp pháp luật theo thời gian" và gọi là "ứng viên đối chiếu trực tiếp". Bài không có dữ liệu luật và không xử lý mốc ngày. Nên chuyển sang đoạn "Mô hình hóa phiên bản". Dòng bảng ch.2 ("biểu diễn phiên bản") đúng.
- **Bib:** khớp. arXiv chỉ có v1, không có nơi đăng.

### 2.3 `guo2025lightrag`: một phần
- **Làm gì:** đồ thị thực thể do LLM trích, truy xuất hai mức. Dữ liệu là "four datasets from the UltraDomain benchmark ... Agriculture, CS, Legal, and Mixed" (p.5). Chấm bằng tỷ lệ thắng theo cặp (bảng tr. 10751 bị vỡ, không chép số).
- **Trích:** "one-hop neighboring nodes of the retrieved nodes v and edges e" (tr. 10749).
- **Câu đang viết:** **Thiếu chính xác.** Paper §2 viết mở rộng của mình "chỉ là lấy láng giềng một bước, nên kết quả không phải phép đánh giá các hệ đó". Kết luận đúng, nhưng lý do không tách được khỏi LightRAG, vì LightRAG cũng lấy láng giềng một bước.
- **Sửa:** nêu khác biệt thật: đồ thị thực thể do LLM trích và truy xuất theo từ khóa hai mức, so với quan hệ sửa đổi tất định. Từ "temporal" xuất hiện 1 lần (p.9), ở đoạn về khả năng mở rộng, không phải phần đánh giá.

### 2.4 `edge2024graphrag`: một phần (bản v2)
- **Làm gì:** dựng đồ thị thực thể rồi tóm tắt cộng đồng để trả lời câu hỏi toàn kho. Dữ liệu podcast (1.669 đoạn 600 token) và tin tức, khoảng 1 triệu token mỗi bộ.
- **Trích:** "first, to derive an entity knowledge graph from the source documents, then to pregenerate community summaries" (p.1). Tỷ lệ thắng về độ bao quát 72–83% (podcast) và 72–80% (tin tức), p.9; chữ trích từ PDF mất dấu gạch ở "72-83%".
- **Liên quan:** mục tiêu là câu hỏi toàn kho, không phải câu hỏi theo mốc. Trong thân bài, `temporal|timestamp` có 0 lần (đây chỉ là tìm chữ).
- **Câu đang viết:** đúng. Có thể gỡ `[CẦN XÁC MINH]` phần cấu trúc đồ thị.
- **Bib:** khóa ghi tiêu đề v1 "A Graph RAG Approach" (24/4/2024). PDF đã đọc là v2 "A GraphRAG Approach" (19/2/2025). Trích bản nào thì ghi tiêu đề bản đó.

### 2.5 `prior2026oldfriend`: toàn văn thân bài (v2, 25/9/2026)
- **Làm gì:** 312 cặp hỏi đáp luật Đức (115 sau cutoff, 113 trước sửa đổi, 84 nhiều điều). LLM sinh 697 cặp, người nhận 312. Bốn điều kiện: không truy xuất, web, RAG-kNN, RAG-ToC. Dữ liệu lấy từ buzer.de, không chính thức.
- **Số (tỷ lệ điểm tuyệt đối, Bảng 1 và p.8):** Claude Sonnet 3.7 không truy xuất 24,35% kết luận đúng; RAG-kNN 86,96%. Giám khảo so với chuyên gia: κ 0,751, riêng căn cứ pháp lý 0,549. Trong thân bài không có số đồng thuận giữa các người gán.
- **Trích:** "acting as a hard constraint for legal validity" (p.6). "what is retrieved (the correct timeframe) matters more than how it is retrieved" (p.8). "Removing the temporal filter reduced the system to a standard RAG pipeline, which caused a substantial drop in accuracy." (p.8; bài không in số của phép bỏ này).
- **Liên quan:** gần RQ1 và RQ3. Lọc của bài ở mức phiên bản đoạn luật; không có nấc lọc theo ngày văn bản.
- **Câu đang viết:** đúng.
- **Bib:** `checked` cần đổi. arXiv ghi "Accepted as full paper at ICAIL 2026. Nominated for the Best Paper Award". PDF không in DOI ACM. ACM DL trả 403, nên chưa xác minh được bản kỷ yếu. Giữ `@misc`.

### 2.6 `prior2025consolidation`: toàn văn thân bài
- **Làm gì:** dùng GPT-4.1-mini áp lệnh sửa đổi lên luật Đức. 908 cặp từ 140 công báo, 4 bộ luật, 117 chuỗi sửa đổi. Chuyên gia chấm 100 mẫu không khớp.
- **Trích:** "only 50.3% of exact matches (single-step) and 20.51% (multi-step) could be achieved" (tr. 396). "We define an exact match as an exact string match after removing non-printable characters and whitespace." (tr. 401).
- **Câu đang viết:** "liên quan trực tiếp đến chất lượng lời văn dẫn xuất" đúng về vấn đề. **Cần thêm:** bài đo bộ hợp nhất bằng LLM, trên luật Đức. Không đặt 50,33%/20,51% cạnh 80,02% của mình, vì khác cách làm và mẫu số.
- **Lưu ý nguồn:** bài tự lệch 51% (tr. 397) và 53% (tr. 403) cho nhóm S0–S2. Cộng số ở tr. 401 được 13+14+24 = 51. Không chép số 53%.
- **Bib:** khớp.

### 2.7 `han2025lawshift`: thân bài
- **Làm gì:** 7.569 mẫu kiểm, 31 loại thay đổi, kiểm thử biến hình cho dự đoán phán quyết trên luật hình sự Trung Quốc.
- **Trích:** "manually construct corresponding revised versions that reflect the intended changes" (p.6). "LawShift encompasses a total of 7,569 test instances" (p.7).
- **Câu đang viết:** đúng. **Cần thêm:** loại thay đổi lấy từ 12 lần sửa thật, nhưng bản sửa dùng để kiểm do chuyên gia tự soạn. Đầu vào không có mốc `as_of`.
- **Lưu ý nguồn:** tóm tắt ghi "five" mô hình (p.1), mục 4.1 ghi "nine" (p.7).
- **Bib:** `Xuxing, Ding` trùng lỗi của Crossref; PDF in "Xuxing Ding". Theo suy luận của tôi nên ghi `Ding, Xuxing`. Thêm trang 133131–133163 (Crossref).

### 2.8 `thanh2021alqac`: toàn văn
- **Làm gì:** ba tác vụ: truy xuất điều luật, entailment, trả lời đúng/sai. Dữ liệu có tiếng Việt và tiếng Thái, nhưng mọi đội chỉ chọn tiếng Việt. Bài không nêu cỡ dữ liệu.
- **Số:** Macro-F2 tốt nhất 0,8807 (p.3). Accuracy 0,6989 ở Task 2 (p.3) và 0,7102 ở Task 3 (p.4). Baseline đa số 0,5455.
- **Trích:** "The competition this year contains three tasks" (p.1). Nhãn gold chỉ gồm `law_id` và `article_id` (p.2).
- **Liên quan:** trong bài đã đọc không có trường ngày hay phiên bản.
- **Câu đang viết:** đúng. Có thể gỡ `[CẦN XÁC MINH]`.
- **Lưu ý nguồn:** bài viết F2 cho "precision is weighted higher" (p.1), nhưng công thức in ra nghiêng về recall. Đừng chép câu đó. Số lượt nộp cũng lệch: 36 lượt ở tóm tắt; 10 lượt ở mục Task 1 so với 11 lượt ở phần kết.

### 2.9 `lewis2020rag`: một phần
- **Làm gì:** kết hợp mô hình seq2seq với chỉ mục vector Wikipedia. Đánh giá trên NQ, TQA, MS-MARCO, Jeopardy, FEVER.
- **Trích:** "the non-parametric memory is a dense vector index of Wikipedia, accessed with a pre-trained neural retriever" (p.1). "within 4.3% of state-of-the-art pipeline models" (FEVER, p.2).
- **Câu đang viết:** đúng, chương chỉ dẫn bản ghi. Có thể gỡ phần kiến trúc khỏi `[CẦN XÁC MINH]`. Đọc từ arXiv v4; bản NeurIPS mới xác nhận trang tồn tại.

### 2.10 `karpukhin2020dpr`: một phần
- **Làm gì:** bộ mã hóa kép cho truy xuất dense trên 21 triệu đoạn.
- **Trích (chữ trích từ PDF):** "outperforms a strong LuceneBM25 system greatly by 9%-19% absolute in terms of top-20 passage retrieval accuracy" (tr. 6769).
- **Câu đang viết:** đúng. Chưa kiểm giả định so với model embedding của dự án, nên `[CẦN XÁC MINH]` về đối chiếu vẫn mở.

### 2.11 `chen2021timeqa`: một phần
- **Làm gì:** sự kiện đổi theo thời gian từ WikiData, gióng với Wikipedia. Hai bộ dễ và khó, mỗi bộ 20K cặp hỏi đáp, 5,5K sự kiện, 70 quan hệ.
- **Trích:** "The bestperforming model FiD can only achieve 46% accuracy, still far behind the human performance of 87%." (p.1). "roughly 41.6% of the segments are revised" (p.4). "We observe only 66% of model predictions are agnostic to these perturbations." (p.9).
- **Liên quan:** tiền lệ cho phép kiểm cùng câu hỏi ở nhiều mốc. Ghi chú repo chép đúng 41,6% và 66%.
- **Bib:** nên đổi sang NeurIPS Datasets and Benchmarks 2021 (đã mở trang kỷ yếu; arXiv ghi "Accepted to NeurIPS21 (dataset track)").

### 2.12 `dhingra2022templama`: một phần
- **Làm gì:** bộ thử TempLAMA cho kiến thức đóng, không có truy xuất, và kỹ thuật mô hình hóa văn bản kèm dấu thời gian.
- **Trích:** "In total we construct 50,310 queries across 11 years." (p.3). "we propose a simple technique for jointly modeling text with its timestamp" (p.1).
- **Câu đang viết:** đúng. Không dùng làm tiền lệ cho RAG, vì đây là thiết lập đóng.

### 2.13 `gardner2020contrast`: một phần
- **Làm gì:** tác giả bộ dữ liệu sửa tay mẫu kiểm để đổi nhãn; làm trên 10 bộ dữ liệu.
- **Trích:** "manually perturb the test instances in small but meaningful ways that (typically) change the gold label" (tr. 1307). "whether it makes correct predictions ŷ on every element in the set" (p.4). Hiệu năng giảm "up to 25% in some cases" (tr. 1307).
- **Quan hệ với TCS (đóng `[CẦN XÁC MINH]` ở ch.2 §2.6.1):** TCS tại `scripts/eval/score_vilextime.py:52` lấy Accuracy trên cả hai dòng của cặp T2, tức contrast consistency với nhóm cỡ 2. **Khác:** cặp của ViLexTime đến từ phiên bản luật thật, không do tác giả sửa tay. "Accuracy tương phản" theo từng dòng không phải contrast consistency; chỉ TCS mới tương ứng.

### 2.14 `robertson2009bm25`: một phần
- **Làm gì:** chuyên khảo về khung xác suất, trong đó có BM25. Không chép công thức vì chưa đọc các mục đó.
- **Trích:** "This monograph addresses the classical probabilistic model of information retrieval." (p.4).
- **Câu đang viết:** đúng. `[CẦN XÁC MINH]` so với FTS5 vẫn mở.
- **Bib, chưa giải quyết được:** trang đầu PDF tác giả ghi "Vol. 3, No. 4 (2009) 333–389". Crossref ghi tập 4, số 1-2, tr. 1–174, và DOI chuyển sang đường dẫn Emerald `article/4/1-2/1/...`. PDF dài 59 trang, hợp với 333–389 hơn. Emerald trả 403, DBLP trả 202. Khuyên điền theo trang đầu PDF, giữ chú thích về sự lệch, và mở bản nhà xuất bản trước khi nộp.

### 2.15 `gwet2008ac1`: chỉ tóm tắt
- **Làm gì:** đề xuất hệ số AC1 và ước lượng phương sai cho nhiều người gán.
- **Trích (PubMed):** "introduces an alternative and more stable agreement coefficient referred to as the AC1 coefficient". "whose validity does not depend upon the hypothesis of independence between raters".
- **Câu đang viết:** "AC1 được chọn sau pilot, không khai báo trước" đúng trong phạm vi: nguồn chỉ cấp định nghĩa AC1. Không trích công thức hay số.
- **Truy cập:** `agreestat.com/papers/bjmsp2008_interrater.pdf` trả 404, dù kết quả tìm kiếm vẫn liệt kê. OpenAlex ghi đóng. `checked` hiện ghi "bản PDF của tác giả" cần sửa thành PubMed.
- **Bib:** khớp 61(1):29–48.

## 3. Việc sửa trong chương 2 và paper

| Vị trí | Sửa |
|---|---|
| Paper §5 | Bỏ `[@dror2018hitchhiker]` khỏi cụm Holm; thêm nguồn Holm khi xác minh được |
| Paper §2 | Chuyển VersionRAG khỏi đoạn pháp luật; nêu rõ tài liệu kỹ thuật, không xử lý ngày |
| Paper §2 | Viết lại lý do phân biệt với LightRAG |
| Paper §1, §2 | Bổ sung VLegal-Bench, ViLegalExpert, LawInForce-eCFR, NitiBench+ |
| Paper đóng góp 3 | Hai điểm nghẽn đã được công bố (mục 4.2); viết thành "phân rã trên pháp luật Việt Nam" |
| Paper, câu dẫn "lọc thời gian" | Dẫn Prior 2026, LawInForce-eCFR, NitiBench+ |
| Ch.2 đầu chương | Cập nhật số khóa đã đọc theo bảng mục 1; "toàn văn" chỉ dành cho hàng ghi thế |
| Ch.2 §2.2.3 | Gỡ `[CẦN XÁC MINH]` phần cơ chế GraphRAG và LightRAG; giữ phần so sánh |
| Ch.2 §2.4.3 | Gỡ `[CẦN XÁC MINH]` về ALQAC 2021 |
| Ch.2 §2.6.1 | Thay `[CẦN XÁC MINH]` bằng mô tả TCS ở 2.13 |
| Ch.2 §2.6.2 | Giữ Dror cho bootstrap và vấn đề phụ thuộc, không dùng cho Holm |
| `related_paper/notes/README.md:33` | Câu "chưa bài nào có..." phải gắn với phạm vi tìm và ngày tìm |
| Ghi chú "Tham khảo bộ dữ liệu..." | TALD đang ghi 26.000; tóm tắt arXiv ghi 51.956 |
| Ghi chú 05 | Bài có v7 (27/10/2026), chân trang p.1 ghi NeurIPS 2026; PDF trong repo là v5 |

## 4. Tính mới

### 4.1 Công trình gần nhất

| Công trình | Nơi đăng | Mức đọc | Trùng với ViLexTime | Khác với ViLexTime | Vai trò |
|---|---|---|---|---|---|
| **LawInForce-eCFR** (Yao và cs.) | AACL-IJCNLP 2026, tr. 879–893 | Toàn văn thân bài | Khoảng `[valid_from, valid_to)`, cặp đổi đáp án, BM25 có/không lọc ngày, oracle, phân tích lỗi | Quy định liên bang Mỹ; chỉ ngưỡng số; hỏi đúng/sai; không có lọc theo ngày văn bản; không xét lan truyền hay bãi bỏ | **Đe dọa cao, nên làm đối chứng thiết kế** |
| **NitiBench+** (Akarajaradwong và cs.) | arXiv v2, 3/11/2026, chưa thấy phản biện | p.1–7, p.10–14, p.27 | Mọi phiên bản có ngày, văn bản hiện hành so với văn bản đang hiệu lực, nhóm bãi bỏ, đối chứng không đổi, RAG theo mốc | Luật Thái; câu hỏi từ phán quyết; cấp section; giám khảo LLM; không có thang lọc | **Đe dọa cao** |
| `prior2026oldfriend` | ICAIL 2026 theo arXiv | Toàn văn thân bài | Lọc `as_of`, chấm áp đúng phiên bản, câu sinh bằng LLM rồi người lọc | Luật Đức; cấp đoạn; nguồn không chính thức; không so các mức lọc | **Đe dọa cao, nên làm baseline** |
| `cymbler2026fiscalqa` | arXiv 2026 | Theo mục, không đọc lại | Chỉ mục nhiều phiên bản, chấm tất định | Luật thuế Pháp | Đã biết |
| Retrieving What Is Still True (Rodrigues và cs.) | Poster workshop NeurIPS 2026 | Tóm tắt trên neurips.cc | Trích sự kiện đổi hiệu lực, kho phiên bản; 79,0% so với 70,4% | ANEEL Brazil; 693 văn bản, 162 câu; so chỉ mục có/không cập nhật | Đe dọa vừa; PDF OpenReview không mở được |
| Version-Aware KG for Multi-Version Legal QA | *Computer Science and Application* 2026 | Tóm tắt trên Hans | KG sửa đổi, câu hỏi hiệu lực theo ngày | Một luật Trung Quốc, 4 bản, 67 câu | Đe dọa vừa, quy mô nhỏ |
| VLegal-Bench / VietLegal (Dong và cs.) | arXiv v7; chân trang ghi NeurIPS 2026 | Tìm từ khóa v5, v7 | Tiếng Việt; có KG; RAG có lọc thời gian | Không có gold phiên bản trong phần đã xem; v5 tự nhận tĩnh | **Phải dẫn**; hiện chưa có khóa |
| ViLegalExpert (Nguyen và cs., UIT) | arXiv v1, 30/9/2026 | Tìm từ khóa, đọc p.1–6 | Tiếng Việt, cỡ lớn, bằng chứng cấp điều/khoản | Tìm từ khóa không thấy xử lý hiệu lực hay phiên bản | Phải dẫn; cùng trường |
| SBV-LawGraph (Phan và cs.) | ACIIDS 2026 theo tên file, chưa xác nhận | Tóm tắt, tìm từ khóa | Tiếng Việt, đồ thị có quan hệ sửa đổi | `temporal` 0 lần; không có mốc hỏi | Dẫn cho "đồ thị tiếng Việt" |
| CLaw (Xu và cs.) | Findings EMNLP 2025 | Tóm tắt | Đến subparagraph, có mốc sửa đổi lịch sử (64.849 mục) | Tiếng Trung; đo ghi nhớ, không phải RAG theo mốc | Đe dọa tuyên bố "cấp Khoản/Điểm" |
| TALD-Bench, LexKairos | arXiv 2026 | Tóm tắt, tìm từ khóa | Bộ đánh giá đúng phiên bản | Tiếng Trung; không truy xuất theo mốc; LexKairos ở cấp văn bản | Đối chiếu |
| LegalSearch-R1 | NLLP 2026 (Crossref) | Tóm tắt | Chỉ mục luật có cửa sổ hiệu lực | Tác tử học tăng cường, tiếng Trung | Đối chiếu |
| TimelyRAG | arXiv 2026 | Tìm từ khóa | Truy xuất cấp phiên bản | Dữ liệu tổng hợp | Đối chiếu |
| FourCorners (Akarajaradwong và cs.) | ACL Demo 2026, tr. 463–472 | Tóm tắt, tìm từ khóa | KG thời gian pháp luật (552K nút), trích dẫn theo phiên bản | Hệ thống; đánh giá bằng phỏng vấn 20 người | Tiền lệ temporal KG pháp lý |
| de Martim (2505.00039, 2506.07853, 2510.06002, 2606.09724) | arXiv; 2505.00039 có bản JURIX | Tóm tắt, tìm từ khóa | Mô hình hóa theo thời gian | Khái niệm, không có benchmark số trong phần đã xem | Dẫn cho kiến trúc |

**Chỉ thấy bản ghi, chưa đọc:** Apofasi (DOI 10.1109/iscaie68866.2026.11576429), CTE-RAG (10.3724/2096-7004.di.2026.0676), Temporal Legal-RAG (10.1109/click68749.2026.11741776), Enhancing RAFT with Knowledge Graphs tiếng Việt (10.1007/978-981-92-2597-2_33), Towards a Benchmark Dataset for Legal Language Understanding in Vietnamese (10.1145/3805862.3805890), Relevance Is Not Applicability (SSRN 7526099, chỉ đọc đoạn tóm tắt trên Crossref), DRILL VLSP 2025, ALQAC 2024 và 2026. **Những mục này có thể làm đổi kết luận.**

**Dự án không phải bài báo, chỉ thấy qua tìm kiếm:** `lqkiet07/vat-temporal-graphrag` (đã mở README), `EigenKai/lexvi`, `Hatsu-Phat/vietnamese-legal-agentic-rag`, `tamnd/luatdo`, bài nói Neo4j NODES 26. Chúng cho thấy cách làm "lọc hiệu lực trên vbpl.vn" đã có trong thực hành. Không dẫn như nguồn khoa học.

**Con số chính đã đọc:**
- **LawInForce-eCFR:** Recall@1 của BM25 thuần 0,31%, BM25 có lọc ngày 2,80%, AuthorityFirst-RAG 30,90% (tr. 885). Accuracy khi cấp sẵn căn cứ đúng 53,8% (tr. 885).
- **NitiBench+:** văn bản đang hiệu lực hơn văn bản hiện hành +0,25 ở nhóm sửa đổi, +0,79 ở nhóm bãi bỏ, +0,01 ở đối chứng (p.12). Qua RAG chỉ còn +0,11 và +0,47 (p.12).

### 4.2 Điều làm yếu tuyên bố hiện có

1. **Câu "đầu tiên" ở guide §2.5 nên bỏ.** Bản hiện tại: "đầu tiên cho pháp luật Việt Nam ở cấp Khoản/Điểm, có trường hợp bãi bỏ một phần và hiệu lực lan truyền..., kèm độ đồng thuận". Tôi không tìm thấy bộ nào phản ví dụ trong tiếng Việt. Nhưng các mục ở dòng "chưa đọc" và các chỉ mục bị chặn đủ để không dám giữ chữ "đầu tiên". Paper hiện đã viết đúng hướng: "không khẳng định... là bộ đầu tiên".
2. **Đóng góp 3 đã có người công bố gần như cùng kết luận.** LawInForce-eCFR: "dual bottleneck", "retrieving the law in force and applying numeric legal rules" (tr. 879). Viết lại thành phép đo trên pháp luật Việt Nam và nêu phần riêng: nhận diện bãi bỏ.
3. **Thông điệp "lọc thời gian đáng giá nhất" không còn mới.** Prior 2026 và NitiBench+ đều cho thấy lọc theo mốc có lợi. Phần còn riêng là tách các nấc lọc trên cùng dữ liệu.
4. **Oracle đang là chỗ thua rõ.** LawInForce-eCFR và NitiBench+ đều có điều kiện cấp sẵn căn cứ; paper chưa có trên test. Reviewer đọc các bài này sẽ hỏi ngay.
5. **Đừng chép câu của NitiBench+** rằng trong 53 bộ "none grades the version" (p.2). Prior 2026 có tiêu chí "Version application correctness" (p.6), nên câu đó khó đứng vững. Cũng đừng dùng nó làm khoảng trống cho mình.
6. **Đồng thuận người gán là thế yếu.** LawInForce-eCFR báo thỏa thuận 95,28% giữa hai người gán (p.4), với phạm vi hẹp hơn nhiều. ViLexTime có AC1 0,377.

### 4.3 Điều còn có thể nói, trong phạm vi đã tìm

Câu đề xuất cho paper (trống chỗ danh sách chỉ mục thì lấy từ mục 5):

> Trong các truy vấn ghi ở phụ lục, chạy ngày 05/11/2026 trên arXiv, Crossref, OpenAlex (4/12 truy vấn), danh mục tiêu đề ACL Anthology và tìm kiếm web, chúng tôi không thấy (a) bộ đánh giá nào cho pháp luật Việt Nam gán gold đến phiên bản điều khoản theo mốc `as_of` và chấm nhầm phiên bản, và (b) công trình nào so sánh có đối chứng, trên cùng dữ liệu, giữa lọc theo ngày văn bản, lọc theo khoảng hiệu lực phiên bản và lan truyền hiệu lực từ nút cha. Semantic Scholar, ACM DL, IEEE Xplore, Google Scholar, SSRN và DBLP không mở được ở lượt này, và một số bài liên quan mới xem đến bản ghi. Chúng tôi không khẳng định đây là bộ đầu tiên, cũng không khẳng định chưa có ai làm.

**Trước khi nộp nên:** chạy lại mục bị chặn; đọc các bài ở dòng "chưa đọc"; đọc các phụ lục của NitiBench+ và LawInForce-eCFR. Phần (b) là phần dễ giữ nhất. Phần (a) phụ thuộc vào việc đọc các bài tiếng Việt chưa mở.

### 4.4 Nên làm baseline

| Baseline | Lý do | Điều kiện |
|---|---|---|
| Cấp sẵn căn cứ đúng, và bản hiện hành với bản đúng mốc (NitiBench+, LawInForce-eCFR) | Tách lỗi tìm khỏi lỗi đọc | Hợp với oracle đã có trong kế hoạch G4 |
| RAG-kNN có lọc `as_of` (Prior 2026) | Trả lời câu hỏi "dense ở đâu" | Bài có công bố dữ liệu; chưa kiểm phần code |
| ColBERT lọc sau truy xuất (LawInForce-eCFR) | So lọc trước với lọc sau | Không bắt buộc |
| LightRAG, GraphRAG (E4) | Trả lời câu hỏi đồ thị | Nói rõ không phải baseline thời gian |
| VersionRAG | Có code công khai | Cần sửa nhiều vì nhận số phiên bản, không nhận ngày |

## 5. Log tìm kiếm (mọi truy vấn chạy ngày 05/11/2026)

**arXiv API**, `sortBy=submittedDate`. Số trong ngoặc là tổng kết quả. Trả 40–50 mới nhất mỗi truy vấn. Không bị chặn.

```
A1 (11) all:temporal AND all:legal AND all:"retrieval-augmented"
A2 (3)  all:"point-in-time" AND all:legal AND (all:retrieval OR all:RAG)
A3 (1)  all:statute AND all:amendment AND all:retrieval AND (all:temporal OR all:version)
A4 (7)  all:"temporal validity" AND all:legal
A5 (1)  all:"version-aware" AND (all:legal OR all:law OR all:statute)
A6 (3)  all:"as-of" AND all:legal AND (all:RAG OR all:retrieval)
B1 (7)  all:benchmark AND all:legal AND all:version AND (all:statute OR all:law) AND all:question
B2 (4)  all:benchmark AND (all:statute OR all:legislation) AND all:temporal AND all:LLM
B3 (3557, chỉ xem 40 mới nhất, lọc tiêu đề) all:versioned AND (all:law OR all:legal OR all:statute OR all:regulation)
B4 (0)  all:"legal" AND all:"knowledge update" AND all:amended
C1 (18) all:Vietnamese AND all:legal AND (all:"question answering" OR all:RAG OR all:retrieval)
C2 (14) all:Vietnamese AND all:legal AND (all:temporal OR all:version OR all:amendment OR all:effective)
C3 (1)  all:Vietnamese AND all:law AND all:"knowledge graph"
C4 (3)  all:Vietnam AND all:legal AND all:benchmark
D1 (2)  all:temporal AND all:GraphRAG AND (all:legal OR all:law)
D2 (3)  all:"knowledge graph" AND all:legal AND all:temporal AND (all:RAG OR all:"retrieval-augmented")
D3 (21) all:GraphRAG AND all:temporal
D4 (2)  all:GraphRAG AND (all:statute OR all:amendment OR all:legislation OR all:regulation)
E1 (35) all:temporal AND all:legal AND all:benchmark
E2 (9)  all:temporal AND all:legal AND all:"question answering"
E3 (1)  all:amended AND all:statute AND all:LLM
E4 (3)  all:repealed AND (all:LLM OR all:RAG OR all:retrieval)
E5 (1)  all:"historical version" AND (all:law OR all:legal OR all:statute)
E6 (2)  all:"knowledge cutoff" AND all:legal
E7 (1)  all:"recency bias" AND all:legal
E8 (0)  all:"legal" AND all:"time-aware" AND (all:RAG OR all:retrieval)
E9 (14) ti:temporal AND ti:legal
E10 (12) ti:legal AND (ti:version OR ti:versioned OR ti:versions OR ti:time OR ti:timeline OR ti:amendment OR ti:amendments)
E11 (15) ti:Vietnamese AND (ti:legal OR ti:law)
E12 (0) all:"Vietnamese" AND all:"legal" AND all:"knowledge graph" AND (all:RAG OR all:GraphRAG OR all:"retrieval")
E13 (1) all:legislation AND all:consolidation AND (all:LLM OR all:"language model")
E14 (3) all:regulatory AND all:temporal AND (all:RAG OR all:"retrieval-augmented")
E16 (9) all:"temporal" AND all:"RAG" AND all:"version" AND all:benchmark
E17 (8) all:GraphRAG AND all:legal
E18 (0) all:"metadata filtering" AND (all:legal OR all:temporal) AND all:RAG
G1 (0) all:Vietnamese AND all:legal AND all:temporal AND all:validity   (theo guide §6.5)
G2 (0) all:"vbpl"
G3 (0) all:ALQAC AND all:repealed
G4 (4) all:ALQAC
G5 (2) all:VLSP AND all:legal
G6 (0) all:vbpl.vn OR all:"vbpl.vn"
G7 (0) all:consolidated AND all:Vietnamese AND all:legal
```

**Cùng 12 truy vấn trên OpenAlex, Semantic Scholar, Crossref** (từ 2023). Kết quả theo thứ tự OpenAlex | S2 | Crossref. "chặn" là HTTP 429.

| Truy vấn | Kết quả |
|---|---|
| temporal legal RAG point-in-time statute version | chặn | chặn | có |
| version-aware legal retrieval statute amendments as-of date | chặn | chặn | có (ra bài Hans) |
| benchmark legal question answering versioned statutes temporal validity | 711 | chặn | có |
| temporal misgrounding legal retrieval | chặn | chặn | có |
| Vietnamese legal question answering benchmark | 2.851 | chặn | có |
| Vietnamese legal RAG temporal validity amendment version | chặn | chặn | có |
| Vietnamese law knowledge graph RAG amended documents effective date | chặn | chặn | có |
| hỏi đáp pháp luật Việt Nam hiệu lực văn bản truy xuất | chặn | chặn | có (nhiễu, bài luật học) |
| temporal GraphRAG legal statutes versioning | 28 | chặn | có (ra FourCorners) |
| legal knowledge graph temporal versioning retrieval augmented generation | chặn | chặn | có |
| ALQAC 2024 automated legal question answering competition | chặn | chặn | có (bài của đội thi, không thấy bài tổng kết) |
| ablation temporal filter legal RAG knowledge graph vs metadata filtering | 657 | chặn | có |

OpenAlex và Crossref chỉ xem 15 và 10 kết quả đầu, có lọc tiêu đề. **Stopped: có.** Lần chạy đầu có thử lại nhiều lần và mất quá lâu; tôi đã dừng nó, và lần chạy dừng này không có kết quả dùng được. Lần chạy trong bảng chỉ thử 1 lần mỗi truy vấn.

**Danh mục tiêu đề ACL Anthology.** Tải trang sự kiện, lọc tiêu đề bằng từ pháp lý cộng từ thời gian. Chỉ xét tiêu đề.

aacl-2026 (751 tiêu đề), acl-2026 (6.419), emnlp-2026 (7.068), eacl-2026 (1.455), findings-2026 (5.247), lrec-2026 (1.937), emnlp-2025 (4.207), acl-2025 (4.547), naacl-2025 (1.958), aacl-2025 (644), findings-2025 (3.418), ws-2025 (3.600), ws-2026 (4.686), nllp-2025 (33), nllp-2026 (52). `naacl-2026` và `coling-2026` trả 404.

Kết quả liên quan: LawInForce-eCFR, FourCorners, Sycophants in the Courtroom, LegalSearch-R1, LexTime, LexTempus, VLSP 2025 TemporalQA (không về luật). Sycophants: có đọc tóm tắt, dữ liệu EUR-Lex với quan hệ bãi bỏ, trắc nghiệm.

**Tìm kiếm web** (US-only; chế độ standard, trừ khi ghi "ext."). Chỉ các nguồn đã nêu ở mục 4 mới được mở.

- `Vietnamese legal RAG temporal validity point-in-time amended repealed provisions benchmark knowledge graph 2026`: VLegal-Bench, ViHERMES, VLQA.
- `temporal GraphRAG statutes versioned legal knowledge graph retrieval as-of date evaluation benchmark`: SAT-Graph, bài nói Neo4j.
- `legal RAG point-in-time retrieval statutes amendment evaluation document-date filter vs version-level filter 2026 arXiv`: **Retrieving What Is Still True**.
- `benchmark hỏi đáp pháp luật Việt Nam theo thời gian phiên bản văn bản hiệu lực RAG đồ thị tri thức bài báo khoa học 2025 2026` (ext.): **SBV-LawGraph**, dự án VAT.
- `temporal legal RAG benchmark statute versions point-in-time question answering paper 2026 ACL EMNLP JURIX ICAIL NLLP` (ext.): **LawInForce-eCFR**, NitiBench+.
- `knowledge graph versus metadata filter legal RAG amendment chains in-force retrieval comparison evaluation statutes GraphRAG versioned` (ext.): arXiv 2604.14220 (CFR, cạnh SUPERSEDES, đã đọc tóm tắt); không thấy nghiên cứu so trực tiếp đồ thị với lọc siêu dữ liệu.
- `Vietnamese legal retrieval expired documents validity filter RAG "văn bản hết hiệu lực" OR "effective date" ALQAC VLSP SoICT legal IR 2025 2026 paper` (ext.): đoạn lọc thời gian của VLegal-Bench, các dự án GitHub.
- `ALQAC 2024 Automated Legal Question Answering Competition summary paper KSE proceedings`: không thấy bài tổng kết. **Chưa mở kỷ yếu KSE 2024.**
- `"văn bản hợp nhất" hỏi đáp pháp luật LLM RAG bộ dữ liệu`: không thấy bộ dữ liệu liên quan.
- `vbpl.vn dataset amendment Vietnamese legal documents version history NLP`: `tamnd/luatdo`, Hugging Face `th1nhng0/vietnamese-legal-documents` (chưa mở).
- `VLSP legal temporal ALQAC repealed Vietnamese law shared task effective version`: ALQAC 2026, DRILL 2025 (chưa mở).
- Tra bản ghi: `Prior Schultz Grabmair "Asking For An Old Friend" ICAIL 2026 ACM proceedings doi`; `Gwet 2008 ... pdf agreestat`; `Holm 1979 ... jstor`.

**Trang đã mở trực tiếp:** ALQAC 2025 (trang chính: không nhắc hiệu lực hay phiên bản; không mở các trang con), arXiv abs các bài trên, NeurIPS virtual 173733, các PDF liệt kê ở mục 1 và 4.1.

**Không mở được:**

| Nguồn | Trạng thái |
|---|---|
| Semantic Scholar API | HTTP 429 cả 12 truy vấn |
| OpenAlex | HTTP 429 ở 8/12; có lúc báo "Anonymous search is paused" |
| ACM DL (tìm kiếm và ICAIL) | HTTP 403 |
| IEEE Xplore | HTTP 420 |
| Google Scholar | HTTP 429 |
| SSRN | Không kết nối được |
| DBLP (API, ICAIL 2026, JURIX 2025) | HTTP 202, không có nội dung |
| OpenReview | Bước kiểm tra trình duyệt |
| ACL Anthology, trang tìm kiếm | HTTP 200 nhưng không đọc được kết quả; thay bằng quét danh mục |
| Springer, tìm kiếm | HTTP 200, chỉ 3 KB, không dùng |
| Emerald (BM25) | HTTP 403 |
| agreestat.com (Gwet) | HTTP 404 |
| doi.org/10.2307/4615733 | HTTP 404 |

**Giới hạn lớn nhất của khảo sát:** các truy vấn arXiv không ra LawInForce-eCFR, vì bài này không xuất hiện trong kết quả của chúng. Nó chỉ lộ qua tìm web mở rộng và ACL Anthology. Do đó, không thấy trên arXiv không có nghĩa là không có. Không kết luận "chưa ai làm" từ log này.

## 6. Mâu thuẫn trong các nguồn

- NitiBench+ nói không bộ nào chấm phiên bản, trong khi Prior 2026 có tiêu chí phiên bản (mục 4.2).
- VersionRAG và TimelyRAG đều tự nhận "first" trong phạm vi của mình; LawShift và CLaw cũng dùng cách nói tương tự. Không chép các tuyên bố đó.
- VLegal-Bench đổi tên giữa các bản; v5 có cụm "tracks historical versions at the time of construction, the benchmark itself is static" (p.9), còn tìm từ khóa v7 không thấy "historical versions". Khi dẫn phải nêu rõ phiên bản.
- ViLegalExpert tự lệch: 177.158 mẫu QA trong Bảng 2, 117.158 trong câu ngay dưới (p.6).

## 7. BibTeX

Trường lấy nguyên từ arXiv BibTeX hoặc ACL Anthology, chỉ đổi khóa và thêm `checked`.

```bibtex
@inproceedings{yao2026lawinforce,
  title = "When the Correct Law Still Fails: A Diagnostic Benchmark for Law-in-Force Retrieval in Versioned Legal {RAG}",
  author = "Yao, Yuchen and HU, Yiran and Zhang, Kaixiang and Su, Yixin and Ge, Jiani and Liu, Yun",
  editor = "Zhang, Yue and Xu, Ruifeng and Purwarianti, Ayu and Rong, Tong and Suzuki, Jun",
  booktitle = "Proceedings of the 15th International Joint Conference on Natural Language Processing and the 5th Conference of the {A}sia-Pacific Chapter of the {A}ssociation for {C}omputational {L}inguistics (Volume 1: Long Papers)",
  month = nov, year = "2026", address = "Hengqin, China",
  publisher = "Association for Computational Linguistics",
  url = "https://aclanthology.org/2026.aacl-long.42/",
  pages = "879--893", ISBN = "979-8-89176-439-2",
  checked = {2026-11-05; ACL Anthology; toàn văn thân bài}
}
@misc{akarajaradwong2026nitibenchplus,
  title={NitiBench+: A Temporal Thai Legal Question Answering Benchmark Across 17 Domains},
  author={Pawitsapak Akarajaradwong and Sarana Nutanong and Chompakorn Chaksangchaichot},
  year={2026}, eprint={2611.03576}, archivePrefix={arXiv}, primaryClass={cs.CL},
  url={https://arxiv.org/abs/2611.03576},
  checked={2026-11-05; arXiv v2; đọc một phần: p.1-7, 10-14, 27}
}
@misc{dong2026vietlegal,
  title={Benchmarking Vietnamese Legal Knowledge of Large Language Models},
  author={Nguyen Tien Dong and Minh-Anh Nguyen and Thanh Dat Hoang and Nguyen Tuan Ngoc and Dao Xuan Quang Minh and Phan Phi Hai and Nguyen Thi Ngoc Anh and Binh Vu and Dung D. Le},
  year={2026}, eprint={2512.14554}, archivePrefix={arXiv}, primaryClass={cs.CL},
  url={https://arxiv.org/abs/2512.14554},
  checked={2026-11-05; arXiv v7, repo giữ v5; tìm từ khóa, đọc đoạn}
}
@misc{nguyen2026vilegalexpert,
  title={ViLegalExpert: A Large-Scale Benchmark for Vietnamese Legal Retrieval and Question Answering from Real-World Consultations},
  author={Dat Tien Nguyen and Nghia Hieu Nguyen and Anh Thi-Hoang Nguyen and Dung Ha Nguyen and Kiet Van Nguyen and Ngan Luu-Thuy Nguyen},
  year={2026}, eprint={2609.39189}, archivePrefix={arXiv}, primaryClass={cs.CL},
  url={https://arxiv.org/abs/2609.39189},
  checked={2026-11-05; arXiv v1; đọc p.1-6, tìm từ khóa}
}
@inproceedings{akarajaradwong2026fourcorners,
  title = "{F}our{C}orners: Grounded {T}hai Legal Research over a Temporal Knowledge Graph",
  author = "Akarajaradwong, Pawitsapak and Nopparatbundit, Thitiwat and Saeteng, Treephop and Phoncharoen, Kasidit and Nutanong, Sarana and Chaksangchaichot, Chompakorn",
  editor = "Durrett, Greg and Jian, Ping",
  booktitle = "Proceedings of the 64th Annual Meeting of the {A}ssociation for {C}omputational {L}inguistics (Volume 3: System Demonstrations)",
  month = jul, year = "2026", address = "San Diego, California, United States",
  publisher = "Association for Computational Linguistics",
  url = "https://aclanthology.org/2026.acl-demo.46/",
  doi = "10.18653/v1/2026.acl-demo.46", pages = "463--472", ISBN = "979-8-89176-392-0",
  checked = {2026-11-05; ACL Anthology; tóm tắt, tìm từ khóa}
}
```

**Lấy thêm khi cần:** TALD (`arxiv.org/bibtex/2608.14610`), LexKairos (`arxiv.org/bibtex/2608.09106`), CLaw (`aclanthology.org/2025.findings-emnlp.646.bib`), ViHERMES LNCS (DOI ở mục 1).

**Không cấp BibTeX, vì chưa xác minh từ bản ghi gốc:**
- **Holm (1979):** Wikipedia và tóm tắt tìm kiếm ghi *Scand. J. Statist.* 6(2):65–70, JSTOR 4615733. DOI mà tóm tắt đưa ra trả 404, Crossref không trả về bài. Cần mở JSTOR hoặc bản giấy trước khi thêm vào bib.
- **Bootstrap theo cụm:** Field và Welsh, "Bootstrapping Clustered Data", JRSS-B 69(3):369–390, DOI 10.1111/j.1467-9868.2007.00593.x. Mới xác minh metadata qua Crossref, chưa đọc nên chưa biết có khớp cách làm của ADR 0005 không.

## 8. Chưa làm

- Chưa đọc đủ: phụ lục của mọi bài; 8 nguồn "một phần" ở mục 1; NitiBench+ p.8–9, p.15–26.
- Chưa kiểm hình và bảng bị vỡ khi trích chữ. Mọi số ở trên lấy từ câu văn, trừ khi ghi "Bảng".
- Chưa xác minh bản kỷ yếu ICAIL của Prior 2026, nơi đăng của SBV-LawGraph, và ALQAC 2024–2026.
- Không sửa file nào trong repo. Lead có thể lưu báo cáo này vào `/home/trica/UIT_Thesis/graphrag-legal-thesis/related_paper/notes/`.
