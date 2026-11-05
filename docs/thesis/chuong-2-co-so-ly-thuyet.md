# Chương 2. Cơ sở lý thuyết và công trình liên quan

> **Tình trạng đọc của bản nháp:** các khóa dẫn trong chương được phân mức theo hồ sơ đọc của AI trong dự án, không phải xác nhận tác giả đã đọc. Có **23 khóa**: **6 khóa đọc hết thân bài**, **1 khóa đọc thân bài chưa trọn** (LawShift còn thiếu một đoạn cuối), **15 khóa đọc một phần** và **1 khóa chỉ đọc tóm tắt**. “Đọc thân bài” không bao gồm phụ lục. Lượt C9b dùng hồ sơ cục bộ, không mở mạng hay tự nâng mức đọc. Chương không dùng số từ bảng PDF bị vỡ hoặc số ngoài câu văn mà báo cáo xác nhận đã đọc.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->
<!-- nguồn: references.bib; các PDF và phần đọc cục bộ được liệt kê ở bảng dưới -->

**Câu hỏi của chương:** Những khái niệm và công trình nào giúp xác định bài toán hỏi đáp đúng phiên bản theo mốc; phần nào của hướng tiếp cận đã có tiền lệ và phần nào còn cần được kiểm bằng thực nghiệm của khóa luận?

## 2.1. Phạm vi khảo sát và mức độ bằng chứng

Khảo sát được tổ chức quanh các trục: truy xuất kết hợp sinh; biểu diễn cấu trúc và phiên bản; hỏi đáp nhạy thời gian; tài nguyên pháp luật tiếng Việt; và phương pháp đánh giá. Việc chia nhóm nhằm xác định phép đối chứng và nguy cơ sai lệch cần kiểm, không nhằm xếp hạng mọi công trình trên cùng một thang điểm. Các tác vụ chọn điều khoản, sinh câu trả lời, tổng hợp toàn corpus và dự đoán phán quyết có đầu ra và mẫu số khác nhau.
<!-- nguồn: MASTER_RESEARCH_GUIDE.md @51f36c7 -->

| Mức sử dụng trong chương | Các khóa |
|---|---|
| Đọc thân bài theo báo cáo ngày 05/11; chưa đọc phụ lục | `dror2018hitchhiker`, `huwiler2025versionrag`, `prior2026oldfriend` (v2), `prior2025consolidation`, `han2025lawshift` (thiếu đoạn cuối), `thanh2021alqac`, `yao2026lawinforce` |
| Đọc một phần trong lượt báo cáo | `lewis2020rag`, `karpukhin2020dpr`, `robertson2009bm25`, `edge2024graphrag` (v2), `guo2025lightrag`, `chen2021timeqa`, `dhingra2022templama`, `gardner2020contrast` |
| Đọc theo mục từ PDF cục bộ ở lượt trước | `cymbler2026fiscalqa`, `demartim2025satgraph`, `nguyen2026vihermes`, `nguyen2025vlqa` |
| Đọc một phần của nguồn bổ sung | `akarajaradwong2026nitibenchplus` (v2: p.1–7, 10–14, 27), `dong2026vietlegal` (tìm từ khóa và đoạn ở v5/v7), `nguyen2026vilegalexpert` (v1: p.1–6, tìm từ khóa) |
| Chỉ đọc tóm tắt | `gwet2008ac1` (PubMed; PDF tác giả không mở được) |

<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

Các lượt đọc dùng chữ trích bằng `pdftotext`; mức đọc không đồng nghĩa đã kiểm trực quan mọi trang và bảng. [CẦN XÁC MINH: đối chiếu trực quan PDF và tính đầy đủ của bản trích trước khi chốt định vị trang]. Bốn nguồn đọc theo mục ở lượt trước vẫn giữ nguyên giới hạn đó; không được nâng thành đọc toàn văn từ tên file.
<!-- nguồn: related_paper/2608.09393v1.pdf; related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf; related_paper/ViHERMES.pdf; related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->

Báo cáo ngày 05/11 ghi cả truy vấn khảo sát, nguồn mở được và nguồn bị chặn. Chương dùng nó làm hồ sơ về các phần gốc đã đọc, đồng thời giữ giới hạn truy cập và phiên bản. Không coi ghi chú, bản dịch hay nhãn “đã xác minh” là bằng chứng rằng tác giả đã tự đọc hoặc mọi kết luận trong nguồn đã được kiểm.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

## 2.2. Truy xuất, sinh câu trả lời và sự phù hợp của căn cứ

### 2.2.1. RAG như một quá trình có thể phân rã

Trong khung thực thi của khóa luận, hệ RAG nhận câu hỏi, tìm các đơn vị văn bản, đưa các đơn vị vào prompt và sinh câu trả lời dựa trên chúng. Cơ chế này tách được ít nhất hai loại thất bại: không đưa đúng căn cứ vào prompt và có căn cứ nhưng sử dụng sai. Một câu trả lời trôi chảy không tự chứng minh bước truy xuất đúng; ngược lại, lấy được điều khoản liên quan chưa bảo đảm câu trả lời sử dụng đúng phiên bản của nó.
<!-- nguồn: src/vilexgraph/framework/retrieve.py -->
<!-- nguồn: src/vilexgraph/framework/generate.py -->
<!-- nguồn: scripts/review/e7_error_analysis.py -->

Lewis và cộng sự kết hợp mô hình seq2seq với chỉ mục vector Wikipedia được truy cập qua bộ truy xuất neural đã tiền huấn luyện [@lewis2020rag]. Cấu trúc này đã được đọc ở tóm tắt và phần kiến trúc của arXiv v4; chưa đọc toàn bài. Nó hỗ trợ phân biệt bộ nhớ tham số với căn cứ truy xuất, không bảo đảm hệ áp đúng hiệu lực của căn cứ pháp luật.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

### 2.2.2. Mức liên quan khác với điều kiện sử dụng

Bộ truy xuất của dự án có đường từ vựng, đường dense và đường trộn thứ hạng. Điểm liên quan giúp chọn ứng viên theo câu hỏi, còn bộ lọc hiệu lực kiểm ứng viên có được phép sử dụng tại mốc hỏi hay không. Hai tiêu chí không đồng nhất. Một đơn vị có nhiều từ trùng câu hỏi vẫn có thể chứa lời văn đã hết hiệu lực; phép xếp hạng không tự suy ra ngày áp dụng nếu ngày đó không được đưa vào điều kiện chọn.
<!-- nguồn: src/vilexgraph/framework/retrieve.py -->
<!-- nguồn: src/vilexgraph/framework/temporal.py -->

Chuyên khảo BM25 đặt phương pháp trong khung truy xuất xác suất; DPR dùng bộ mã hóa kép để tìm đoạn [@robertson2009bm25] [@karpukhin2020dpr]. Lượt đọc chỉ bao phủ mở đầu BM25 và tóm tắt cùng một đoạn DPR, nên chưa chép công thức hoặc dùng điểm bài gốc để dự đoán hiệu quả trên kho luật. [CẦN XÁC MINH: đối chiếu giả định BM25 với FTS5 và DPR với model embedding thực tế]. Metadata BM25 còn mâu thuẫn: trang đầu PDF ghi tập 3, số 4, tr.333–389; Crossref ghi tập 4, số 1–2, tr.1–174. Chưa chọn một bộ tập/trang để điền khi chưa đối chiếu bản nhà xuất bản.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

Với chính cài đặt hiện tại, điểm từ vựng được tính trong SQLite FTS5, còn dữ liệu phiên bản và khoảng hiệu lực nằm ở các bảng dẫn xuất. Đây là mô tả engine đã được kiểm qua code, không phải khẳng định rằng mọi hệ RAG đều dùng cùng cơ chế hoặc rằng điểm dense sẽ giải quyết được khác biệt nhỏ giữa các phiên bản.
<!-- nguồn: src/vilexgraph/framework/corpus.py -->
<!-- nguồn: src/vilexgraph/framework/retrieve.py -->

### 2.2.3. Đồ thị là một nhóm cơ chế, không phải một phép đo duy nhất

Tên GraphRAG có thể bao phủ nhiều cách đưa quan hệ vào xử lý. Đối với khóa luận, cần phân biệt quan hệ cấu trúc, quan hệ sửa đổi, việc dựng lịch sử ngoại tuyến và mở rộng căn cứ trực tuyến. Một phép đối chứng chỉ có ý nghĩa khi xác định rõ cơ chế nào được thêm hoặc bỏ. Tên của hệ không thể thay thế bảng cấu hình thực thi.
<!-- nguồn: src/vilexgraph/framework/systems.py -->
<!-- nguồn: docs/decisions/0004-framework-truy-xuat-va-sinh.md -->

GraphRAG của Edge và cộng sự dựng đồ thị thực thể rồi tạo trước tóm tắt cộng đồng cho câu hỏi toàn kho [@edge2024graphrag]. LightRAG trích đồ thị thực thể bằng LLM và truy xuất từ khóa hai mức; bài cũng lấy láng giềng một bước [@guo2025lightrag]. Vì vậy, “một bước” không đủ để phân biệt cài đặt của khóa luận với LightRAG. Khác biệt được xác định ở loại quan hệ sửa đổi tất định và cơ chế truy xuất, thay vì đồ thị thực thể và từ khóa hai mức. Các phần cơ chế đã đọc đủ để đóng yêu cầu xác minh này, nhưng chưa tạo một phép so sánh thực nghiệm. [CẦN XÁC MINH: đối chiếu cấu hình và corpus nếu so sánh trực tiếp với GraphRAG hoặc LightRAG].
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

## 2.3. Danh tính điều khoản, phiên bản và thời điểm áp dụng

### 2.3.1. Tách danh tính khỏi lời văn

Một đối tượng điều khoản có thể giữ danh tính trong khi lời văn thay đổi. Với mô hình dữ liệu của dự án, điều khoản, phiên bản và sự kiện là các đối tượng khác nhau. Phiên bản chỉ rõ lời văn và khoảng cục bộ; sự kiện ghi nguyên nhân tạo hoặc kết thúc; quan hệ cha–con cung cấp ràng buộc hiệu lực bổ sung. Đây là đặc tả của biểu diễn đang nghiên cứu, không phải một kết luận rằng mọi thay đổi pháp lý đều có thể được suy ra từ khác biệt chuỗi ký tự.
<!-- nguồn: src/vilexgraph/build/temporal/models.py -->
<!-- nguồn: src/vilexgraph/build/temporal/validity.py -->

SAT-Graph RAG là một tiền lệ trực tiếp về việc phân biệt danh tính và biểu đạt có phiên bản [@demartim2025satgraph]. PDF cục bộ của de Martim tách Norm/Component ở mức Work, các Temporal Version và Language Version ở mức biểu đạt; Text Unit được nối với tầng lời văn cụ thể. Bài đồng thời biểu diễn sự kiện lập pháp bằng nút Action để có thể truy nguyên nguyên nhân thay đổi. Đây là nội dung đã đọc ở phần mô hình và dựng đồ thị, không phải suy từ tên công trình.
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->

Bản PDF cục bộ là arXiv v5 với cụm “Structural, Temporal, and Deterministic” trong tiêu đề; khóa bib trỏ bản kỷ yếu có cụm “Hierarchical, Temporal, and Deterministic”. Các phát biểu cơ chế trong chương này dựa vào PDF cục bộ. [CẦN XÁC MINH: đối chiếu PDF arXiv v5 với bản kỷ yếu của khóa demartim2025satgraph trước khi chốt phiên bản trích dẫn; chưa coi hai bản là hoàn toàn giống nhau].
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: references.bib -->

SAT-Graph RAG trình bày mô hình aggregation để tái sử dụng thành phần không đổi và đưa ra các chính sách chọn phiên bản, tác động phân cấp, truy nguyên. Phần case study và Discussion của bản gốc là minh họa định tính; bài đề xuất benchmark và các phép đo cho bước đánh giá tiếp theo. Do đó, không chuyển các tuyên bố kiến trúc của bài thành kết quả định lượng đã chứng minh khả năng hỏi đáp. Bài cũng chỉ rõ lỗi khoảng hiệu lực hoặc metadata Action ở thượng nguồn có thể tạo truy xuất sai một cách có hệ thống.
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->

### 2.3.2. Truy xuất theo mốc khác với chọn bản mới nhất

Trong ViLexTime, đầu vào có mốc `as_of` tường minh. Câu hỏi cần bản áp dụng tại mốc đó, có thể là bản cũ hoặc bản chưa phải mới nhất của kho. Phiên bản mới nhất chỉ là một quy tắc lựa chọn đối chứng; nó không tương đương với điều kiện có hiệu lực tại ngày hỏi. Cũng cần tách một lần sửa lời văn của nút cha khỏi việc nút cha bị bãi bỏ: hai sự kiện có thể tác động khác nhau đến hiệu lực nút con.
<!-- nguồn: docs/vilextime-dinh-nghia.md -->
<!-- nguồn: scripts/eval/score_vilextime.py -->
<!-- nguồn: src/vilexgraph/build/temporal/effective_intervals.py -->

TimeQA lấy sự kiện thay đổi theo thời gian từ WikiData rồi gióng với Wikipedia, là tiền lệ cho việc kiểm một nội dung ở nhiều mốc [@chen2021timeqa]. TempLAMA là bộ thử kiến thức trong thiết lập đóng và nghiên cứu mô hình hóa văn bản kèm dấu thời gian, không phải tiền lệ đánh giá RAG [@dhingra2022templama]. Hai bài mới được đọc một phần, nên chương chỉ sử dụng các cơ chế này.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

VersionRAG thuộc nhóm biểu diễn phiên bản cho **tài liệu kỹ thuật**, không xếp vào hỏi đáp pháp luật [@huwiler2025versionrag]. Bài dựng đồ thị category–document–version–content–change và định tuyến theo loại câu hỏi. Giới hạn tác giả nêu là chưa ánh xạ ngày lịch sang bản phát hành; vì vậy nó không trực tiếp giải quyết đầu vào `as_of`. Phép so với RAG không nhận biết phiên bản của bài cũng chưa tách riêng nấc chỉ lọc siêu dữ liệu như RQ3.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

### 2.3.3. Sai lệch căn cứ theo thời gian trong FiscalQA Pro

FiscalQA Pro đặt hiện tượng temporal misgrounding làm đối tượng đánh giá [@cymbler2026fiscalqa]. Phần mở đầu bản gốc mô tả việc dùng bản đang có hiệu lực hiện tại trong khi ngữ cảnh câu hỏi đòi một phiên bản khác. Phần phương pháp phân biệt chỉ mục chỉ có bản hiện hành với chỉ mục nhiều phiên bản được điều kiện hóa theo ngày. Bài do đó là bằng chứng rằng bài toán RAG pháp luật theo thời gian đã có tiền lệ; khóa luận không thể tuyên bố phát minh ra bài toán này.
<!-- nguồn: related_paper/2608.09393v1.pdf -->

Điểm cần chú ý trong thiết kế FiscalQA Pro là điều kiện RAG tĩnh trong phép so sánh được cấp định danh điều luật gold nhưng phục vụ bản hiện hành. Đây không phải cùng điều kiện với một retriever phải tìm điều luật trên toàn kho mà không biết gold. Vì thế, khi học cách phân rã lỗi từ bài, cần giữ nguyên điều kiện thông tin của từng hệ thay vì gọi mọi cấu hình có truy xuất là tương đương.
<!-- nguồn: related_paper/2608.09393v1.pdf -->

Bài chấm bằng các nugget có thể kiểm tất định, phân biệt độ phủ nội dung, điểm strict và provenance của phiên bản. Phần lựa chọn câu hỏi còn lọc theo việc model đã trả được đáp án hay chưa và liệu giá trị gold còn xuất hiện trong bản hiện hành hay không. Tập được giữ vì thế có tính chọn lọc theo hiện tượng và năng lực của các model dùng khi chọn; nó không phải mẫu ngẫu nhiên của mọi câu hỏi thuế. Đây là nhận xét về thiết kế đã đọc, không trích lại kết quả điểm số của bài.
<!-- nguồn: related_paper/2608.09393v1.pdf -->

Phụ lục bản gốc phân biệt artifact công khai với bộ truy xuất end-to-end có thành phần độc quyền. Sự công khai của corpus hoặc câu trả lời không tự làm mọi điều kiện end-to-end tái lập được. Với khóa luận này, bài học phương pháp là phải công bố cả đơn vị gold, điều kiện cấp căn cứ và phần pipeline có thể dựng lại. Bản dịch tiếng Việt trong repo chỉ hỗ trợ đọc thuật ngữ; nội dung khẳng định ở đây được đối chiếu PDF gốc.
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/notes/FiscalQA.md -->

## 2.4. Tài nguyên và hệ pháp luật tiếng Việt

### 2.4.1. VLQA: truy xuất điều luật và câu trả lời dài

VLQA định nghĩa dữ liệu dưới dạng câu hỏi, các điều luật liên quan và câu trả lời, hướng đến cả truy xuất lẫn hỏi đáp [@nguyen2025vlqa]. Phần Dataset Construction của bản gốc mô tả thu thập câu hỏi tư vấn, gióng tham chiếu tới corpus điều luật, chú giải và xác minh chuyên gia. Vai trò này khác với việc dựng các cặp mốc có gold phiên bản của ViLexTime; không thể đánh đồng quy mô câu hỏi tư vấn với quy mô tương phản phiên bản.
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->

Trong phần chuẩn bị corpus và câu hỏi, VLQA ghi rõ loại các điều khoản bị bãi bỏ và câu hỏi dẫn đến các điều khoản đó. Đây là khác biệt thiết kế có thể kiểm trực tiếp, chứ không phải bằng chứng rằng VLQA không có giá trị. ViLexTime giữ lịch sử để hỏi đúng nội dung theo mốc, còn VLQA trong các phần đã đọc ưu tiên câu hỏi gắn với điều luật hợp lệ của corpus được chuẩn bị. Không suy từ khác biệt này rằng chưa có tài nguyên tiếng Việt nào khác xử lý lịch sử.
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->

Phần chú giải của VLQA mô tả người gán đánh giá và có thể sửa cả câu trả lời lẫn điều luật liên quan dưới sự kiểm của chuyên gia. Bài học áp dụng cho khóa luận là công bố can thiệp của người ở cấp nội dung và căn cứ, không chỉ ghi rằng có “expert verification”. Chương không lấy tên quy trình đó làm bằng chứng cho đồng thuận hoặc chất lượng nhãn của ViLexTime.
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->

PDF VLQA cục bộ còn phần mẫu định dạng ACM chưa hoàn thiện, trong khi metadata repo quản lý theo bản arXiv. [CẦN XÁC MINH: kiểm phiên bản xuất bản của VLQA trước khi ghi nơi công bố; không dùng thông tin mẫu trong PDF như thông tin kỷ yếu đã được xác nhận].
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->
<!-- nguồn: references.bib -->

### 2.4.2. ViHERMES: quan hệ pháp lý và mở rộng căn cứ

ViHERMES nghiên cứu hỏi đáp đa bước trên quy định y tế tiếng Việt [@nguyen2026vihermes]. Bản gốc mô tả dữ liệu có căn cứ và chú giải suy luận, cùng hệ graph-aware sử dụng các quan hệ sửa đổi, thay thế, bổ sung và dẫn chiếu. Đây là tiền lệ về dùng quan hệ đồ thị cho hỏi đáp pháp luật tiếng Việt, cần được phản ánh khi định vị đóng góp.
<!-- nguồn: related_paper/ViHERMES.pdf -->

Mục Seeded Retrieval and Propagation mô tả lấy các nút seed, mở rộng theo loại quan hệ và ưu tiên nút cuối chuỗi sửa đổi như căn cứ có thể áp dụng. Phần phương pháp đã đọc không đặc tả việc chọn một phiên bản theo mốc `as_of` tường minh như ViLexTime; kết luận của bài đặt việc làm giàu temporal validity vào hướng tiếp tục. Sự khác biệt cần nêu là cách điều kiện hóa bằng chứng theo mốc, không phải quy ViHERMES thành hệ “không biết gì về sửa đổi”.
<!-- nguồn: related_paper/ViHERMES.pdf -->

Các ghi chú trong repo cũng nhắc quan hệ sửa đổi và validity tracing của ViHERMES. Vì thế, cách viết phủ định tuyệt đối rằng công trình trong nước chưa xét quan hệ hoặc tính hợp lệ sẽ bỏ qua chính phần đã xác minh. Khóa luận chỉ dùng đối chiếu này để xác định yêu cầu thử nghiệm theo ngày, không khẳng định đã có một phép so sánh trực tiếp với hệ ViHERMES trên cùng dữ liệu.
<!-- nguồn: related_paper/notes/03-vihermes.md -->
<!-- nguồn: related_paper/notes/Tham khảo bộ dữ liệu pháp luật có hiệu lực và phiên bản.md -->

### 2.4.3. ALQAC và các tài nguyên bổ sung

Bài tổng kết ALQAC có khóa trong danh mục mô tả truy xuất điều luật, entailment và trả lời đúng/sai; gold trong bài chỉ gồm `law_id` và `article_id`, không nêu trường ngày hoặc phiên bản [@thanh2021alqac]. Báo cáo đã đọc toàn bài tổng kết này, nên yêu cầu đọc gốc cho mô tả tác vụ được đóng. Không dùng nó thay một bài tổng kết năm khác chỉ vì cùng tên cuộc thi.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

VLegal-Bench/VietLegal đánh giá kiến thức pháp luật tiếng Việt, có KG và RAG có lọc thời gian [@dong2026vietlegal]. Phần đã xem ở arXiv v5 tự nhận benchmark tĩnh dù theo dõi phiên bản tại lúc dựng; v7 đổi tên và kết quả tìm từ khóa không đủ để suy mọi phần giữ nguyên. ViLegalExpert tập trung truy xuất và hỏi đáp từ tư vấn thực tế, có bằng chứng cấp điều/khoản [@nguyen2026vilegalexpert]. Báo cáo mới đọc phần đầu và tìm từ khóa; chưa thấy gold phiên bản theo mốc trong phần đã xem không chứng minh toàn bộ hai công trình không xử lý thời gian. Không trích quy mô QA của ViLegalExpert vì câu văn và bảng trong nguồn lệch nhau.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

[CẦN XÁC MINH: đọc đầy đủ VLegal-Bench/VietLegal và ViLegalExpert; các ghi chú LegalGraphRAG và khung suy luận có kiểm chứng chưa đủ bản ghi gốc để đưa vào đối chiếu học thuật]. Chương chỉ dẫn các khóa đã có trong `references.bib`.
<!-- nguồn: references.bib; related_paper/notes/08-legalgraphrag-acl2026.md; related_paper/notes/09-verifiable-reasoning-framework-icoco2026.md -->

## 2.5. Bảng đối chiếu các công trình gần nhất

Bảng ghi riêng cơ chế đã đọc và giới hạn truy cập của từng nguồn. “Chưa xác minh” là trạng thái đọc của bản nháp, không có nghĩa công trình thiếu thành phần đó. Không trình bày điểm số của các tác vụ khác nhau thành bảng xếp hạng chung.

| Công trình | Bài toán hoặc cơ chế được phép mô tả ở bản nháp | Quan hệ với khóa luận | Đã xác minh ở đâu | Giới hạn sử dụng |
|---|---|---|---|---|
| FiscalQA Pro [@cymbler2026fiscalqa] | Chọn phiên bản theo ngày; nugget và provenance; lọc câu hỏi theo hiện tượng | Tiền lệ trực tiếp cho đánh giá temporal misgrounding | PDF `2608.09393v1.pdf`, các mục Introduction, Nugget-Based Scoring, Experimental Design và phụ lục public/private artifacts | Chưa đọc toàn văn; không trích số; pipeline end-to-end không hoàn toàn công khai |
| SAT-Graph RAG [@demartim2025satgraph] | Work/Expression, phiên bản thành phần, Action, chính sách truy vấn | Tiền lệ mô hình cấu trúc–thời gian và truy nguyên | PDF `An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf`, Proposed Framework, Case Study, Discussion | Bản gốc đã đọc là arXiv v5; case study định tính; còn đối soát bản kỷ yếu |
| ViHERMES [@nguyen2026vihermes] | Graph-aware multihop QA; mở rộng theo quan hệ; ưu tiên cuối chuỗi sửa đổi | Đối chiếu trong nước về vai trò đồ thị và điều kiện thời gian | PDF `ViHERMES.pdf`, SRKG, Seeded Retrieval and Propagation, Conclusion | Không biến tracing sửa đổi thành phủ định “không có thời gian”; chưa so trực tiếp cùng benchmark |
| VLQA [@nguyen2025vlqa] | Câu hỏi tư vấn, corpus điều luật, kiểm chuyên gia; loại điều khoản bãi bỏ | Đối chiếu dữ liệu tiếng Việt và nguồn gốc nhãn | PDF VLQA, Dataset Construction và Expert Annotation | Cần xác nhận thông tin xuất bản; không suy chất lượng ViLexTime từ quy trình của VLQA |
| VersionRAG [@huwiler2025versionrag] | Đồ thị nhiều tầng và định tuyến câu hỏi cho tài liệu kỹ thuật | Đối chiếu biểu diễn phiên bản, không phải dữ liệu luật | Báo cáo đọc §2.2: thân bài v1 | Chưa ánh xạ ngày lịch; không có đối chứng chỉ lọc metadata |
| Statutory QA theo thời gian [@prior2026oldfriend] | Luật Đức, lọc mốc như ràng buộc cứng, chấm áp đúng phiên bản | Tiền lệ trực tiếp về temporal QA và lợi ích lọc | Báo cáo §2.5: thân bài v2 | Nguồn buzer.de không chính thức; không có nấc lọc ngày văn bản; không có số IAA người–người trong thân bài |
| Hợp nhất luật tự động [@prior2025consolidation] | LLM áp lệnh sửa đổi lên luật Đức | Rủi ro của lời văn dẫn xuất | Báo cáo §2.6: thân bài | Khác cách làm và mẫu số, không đặt tỷ lệ khớp cạnh tỷ lệ của khóa luận |
| LawShift [@han2025lawshift] | Kiểm thử biến hình cho dự đoán phán quyết luật hình sự Trung Quốc | Đối chiếu loại thay đổi, khác đầu ra QA theo mốc | Báo cáo §2.7: thân bài, thiếu đoạn cuối | Loại thay đổi lấy từ sửa đổi thật, nhưng bản kiểm do chuyên gia tự soạn; không có đầu vào `as_of` |
| LawInForce-eCFR [@yao2026lawinforce] | Khoảng hiệu lực, cặp đổi đáp án, BM25 có/không lọc ngày và oracle | Đối chứng thiết kế gần: tìm đúng luật và đọc quy tắc | Báo cáo §4.1: thân bài | Quy định liên bang Mỹ, ngưỡng số, đúng/sai; không tách lọc ngày văn bản hay lan truyền và bãi bỏ |
| NitiBench+ [@akarajaradwong2026nitibenchplus] | Luật Thái, bản hiện hành so với bản đúng mốc, nhóm sửa đổi/bãi bỏ và đối chứng | Đối chứng cho X8 về điều kiện cấp sẵn căn cứ | Báo cáo §4.1: một phần arXiv v2 | Chưa xác nhận phản biện; chưa đọc hết thân bài/phụ lục; không có thang lọc trong phần đã xem |
| VLegal-Bench/VietLegal [@dong2026vietlegal] | Tiếng Việt, KG và RAG có lọc thời gian | Đối chiếu trong nước về tài nguyên và căn cứ | Báo cáo §4.1: tìm từ khóa/đoạn v5, v7 | V5 tự nhận tĩnh; phải phân biệt phiên bản khi dẫn; còn chờ đọc đầy đủ |
| ViLegalExpert [@nguyen2026vilegalexpert] | Truy xuất, QA tư vấn tiếng Việt, căn cứ cấp điều/khoản | Đối chiếu trong nước về dữ liệu | Báo cáo §4.1: p.1–6 và tìm từ khóa v1 | Chưa đọc đủ; số QA trong nguồn tự lệch; chưa suy phủ định về phiên bản |

<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->
<!-- nguồn: references.bib -->
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: related_paper/ViHERMES.pdf -->
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->
<!-- nguồn: related_paper/notes/Tham khảo bộ dữ liệu pháp luật có hiệu lực và phiên bản.md -->

## 2.6. Cơ sở đánh giá và độ tin cậy

### 2.6.1. Tách đúng nội dung, đúng phiên bản và đúng căn cứ

FiscalQA Pro phân biệt kiểm nugget nội dung với provenance của phiên bản. SAT-Graph RAG phân biệt chọn phiên bản, quy tác động và dựng provenance trong phần đề xuất đánh giá. Hai tiền lệ cho thấy “có trích dẫn” và “trích đúng căn cứ theo thời gian” là những điều cần kiểm riêng. Tuy nhiên, chương không gộp các metric của họ với metric ViLexTime: phép chấm của khóa luận vẫn do ADR và scorer đã khóa quyết định.
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Trong cài đặt ViLexTime, Recall đo lấy được điều khoản hoặc bằng chứng chấp nhận; TV-Recall yêu cầu phiên bản hoặc ID bằng chứng gold. Accuracy kiểm các span bắt buộc và tránh span riêng của phiên bản khác. TVER chỉ xét phạm vi trích dẫn theo định nghĩa của scorer, nên cần báo kèm độ phủ và strict. Đây là các định nghĩa thao tác của bộ đánh giá, không phải khẳng định đã tạo ra một họ chỉ số mới.
<!-- nguồn: scripts/eval/score_vilextime.py -->

Gardner và cộng sự định nghĩa contrast consistency là dự đoán đúng mọi phần tử trong một nhóm tương phản [@gardner2020contrast]. TCS của ViLexTime yêu cầu **cả hai dòng** của cặp T2 cùng lineage và chế độ mốc đều đúng Accuracy; do đó tương ứng contrast consistency cho nhóm cỡ hai. Accuracy tương phản tính riêng từng dòng không phải contrast consistency. Khác biệt về dữ liệu là cặp ViLexTime lấy từ phiên bản luật thật trong kho, còn contrast sets của bài được tác giả sửa tay để đổi nhãn. Không coi TCS là một chỉ số mới.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->
<!-- nguồn: scripts/eval/score_vilextime.py, TCS và aggregate -->

### 2.6.2. Chất lượng gold và đơn vị độc lập

Một pipeline chạy tất định có thể tái tạo cùng lỗi nhiều lần. SAT-Graph RAG nêu rõ phụ thuộc chất lượng metadata và khoảng hiệu lực thượng nguồn. Trong ViLexTime, gold và hệ đề xuất cùng dùng chuỗi phiên bản, nên việc hai bên đồng ý không phải kiểm chứng độc lập về pháp lý. Cần tách kiểm nhất quán code, đồng thuận nhãn và kiểm gold độc lập; mỗi loại bằng chứng trả lời một câu hỏi khác nhau.
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: docs/vilextime-datasheet.md -->

Các dòng cùng lineage chia sẻ câu hỏi và bằng chứng. Phân tích dự án lấy lineage làm cụm lấy mẫu lại, theo ADR và code. Dror và cộng sự bàn về bootstrap và nêu vấn đề quan sát phụ thuộc [@dror2018hitchhiker]; bài không bàn Holm và không đặc tả bootstrap theo cụm. Vì vậy không dùng bài này làm nguồn cho hai lựa chọn đó. Họ kiểm định, chiều và ngưỡng là đặc tả phân tích của dự án; số thăm dò không tự trở thành xác nhận khi thấy khoảng tin cậy thuận lợi. [CẦN TRÍCH DẪN: nguồn gốc đã xác minh cho Holm và bootstrap theo cụm; chưa có khóa phù hợp trong references.bib].
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md; scripts/eval/confirm_vilextime.py -->

AC1 có tài liệu nền [@gwet2008ac1], nhưng hồ sơ chỉ đọc tóm tắt PubMed; PDF tác giả không mở được. Chương chỉ dùng nguồn để nhận diện hệ số, không chép công thức hay suy ra ngưỡng chất lượng. Việc dự án chọn AC1 sau pilot phải được khai riêng ở chương dữ liệu, không biến thành lựa chọn đã đăng ký trước nhờ dẫn tài liệu này.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->
<!-- nguồn: docs/vilextime-datasheet.md -->

## 2.7. Khoảng trống nghiên cứu và ranh giới tuyên bố

### 2.7.1. Điều có thể nói từ phạm vi đã khảo sát

Các tiền lệ đã có trong danh mục gồm LawInForce-eCFR và NitiBench+: bài sau đã có nhóm luật bãi bỏ, nên nhận diện bãi bỏ không tự tạo tính mới [@yao2026lawinforce; @akarajaradwong2026nitibenchplus]. Phạm vi Việt Nam cần kiểm là lời văn dựng lại từ lệnh ở văn bản khác và bãi bỏ qua nút cha. Ở thang hiện có, hai nấc đã đo được là ngày văn bản và khoảng phiên bản; bước lan truyền không đổi TV-Recall@1 ở mọi nhóm trên cả hai bộ. XN5 về Accuracy lan truyền chưa chạy, nên chưa xác lập đóng góp này.
<!-- nguồn: references.bib; related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md; runs/E1/test/ladder.score.json; runs/E1_test2/test/ladder.score.json; runs/E3_v1/test/confirm.json; runs/E3_test2/rescore/confirm.json -->

Log khảo sát còn nêu các nguồn gần chưa có khóa trong `references.bib`: [CẦN: Retrieving What Is Still True]; [CẦN: arXiv 2604.14220, CFR và cạnh SUPERSEDES]; [CẦN: Version-Aware KG for Multi-Version Legal QA]; [CẦN: FourCorners]; [CẦN: Temporal Legal-RAG]. Chưa thêm hay dùng chúng làm bằng chứng chi tiết khi chưa có mục bib và lượt đọc đủ. Do đó rút khẳng định phủ định “không thấy công trình nào” về phép đối chứng; phạm vi khảo sát hiện chưa đủ xác lập khoảng trống toàn lĩnh vực.
<!-- nguồn: related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md, bảng công trình và log truy vấn; references.bib -->

Điều kiện X8 đúng mốc/hiện hành còn chờ, phải đo dev trước rồi bộ cuối; không suy lợi ích lan truyền từ mục tiêu thiết kế.
<!-- nguồn: docs/plans/active/master-plan.md, mục "Phản biện 05/11 và cách xử lý"; docs/decisions/0005-ke-hoach-phan-tich.md -->

Các khái niệm chuẩn hóa như Akoma Ntoso và LRMoo được nhắc trong SAT-Graph RAG. Chương chỉ mô tả cách bài đó sử dụng các khái niệm, không nhận đã xác minh đầy đủ chính tiêu chuẩn gốc. [CẦN TRÍCH DẪN: tài liệu chuẩn gốc của Akoma Ntoso và LRMoo nếu khóa luận trình bày độc lập cấu trúc hoặc bảo đảm của chúng; hiện chưa có khóa phù hợp trong references.bib].
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->

## 2.8. Câu trả lời có bằng chứng

Các nguồn gốc đã đối chiếu hỗ trợ việc phân biệt hiệu lực theo ngày, danh tính điều khoản, lời văn phiên bản và provenance; đồng thời cho thấy đồ thị và xử lý lịch sử không phải các ý tưởng chưa từng được nghiên cứu. Tài nguyên tiếng Việt đã có kiểm chuyên gia và truy xuất theo quan hệ, nhưng thiết kế theo mốc và phép đối chứng cụ thể vẫn cần được xem xét trên từng công trình. Cách lập luận có thể bảo vệ cho khóa luận là xác định rõ đầu vào–đầu ra, công bố nguồn gold và kiểm nguồn gốc chênh lệch trong phạm vi đã đo. Chưa có cơ sở để tuyên bố ưu thế hay thứ tự công bố trên toàn lĩnh vực.
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: related_paper/ViHERMES.pdf -->
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->

## Việc còn thiếu trước khi nộp

- Đọc bản gốc các mục còn mới đối chiếu metadata, ghi chính xác phần đã đọc và chỉ bổ sung số liệu sau khi đọc đủ phạm vi.
- Kiểm trực quan PDF, phiên bản SAT-Graph RAG, thông tin xuất bản VLQA và định vị trích dẫn; không suy nơi công bố từ mẫu trình bày.
- Tiếp tục khảo sát từ log đã có, mở lại phần bị chặn; tránh mọi khẳng định phủ định toàn lĩnh vực.
- Nhóm xác minh các nguồn còn thiếu khóa khi có điều kiện; bản nháp này không tự thêm tài liệu vào bibliography.
- Tác giả kiểm nội dung phương pháp luận và thuật ngữ; ghi chú/bản dịch do AI hỗ trợ không thay việc đọc gốc.
