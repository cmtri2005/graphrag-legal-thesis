# Chương 2. Cơ sở lý thuyết và công trình liên quan

> **Tình trạng đọc của bản nháp:** trong 18 khóa được dẫn trong chương, **4 khóa đã đối chiếu bản gốc ở các phần được sử dụng**, **14 khóa mới đối chiếu metadata**, chưa đọc bản gốc trong lượt này. Không tự nhận đã đọc toàn văn các bài chỉ kiểm theo mục; không trích kết quả định lượng của các công trình ngoài dự án. Ghi chú và bản dịch trong repo dùng để định hướng, không tự thay thế bản gốc. Thống kê này chỉ áp dụng các khóa của chương, không phải toàn bộ `references.bib`.
<!-- nguồn: references.bib -->
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: related_paper/ViHERMES.pdf -->
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->

**Câu hỏi của chương:** Những khái niệm và công trình nào giúp xác định bài toán hỏi đáp đúng phiên bản theo mốc; phần nào của hướng tiếp cận đã có tiền lệ và phần nào còn cần được kiểm bằng thực nghiệm của khóa luận?

## 2.1. Phạm vi khảo sát và mức độ bằng chứng

Khảo sát được tổ chức quanh các trục: truy xuất kết hợp sinh; biểu diễn cấu trúc và phiên bản; hỏi đáp nhạy thời gian; tài nguyên pháp luật tiếng Việt; và phương pháp đánh giá. Việc chia nhóm nhằm xác định phép đối chứng và nguy cơ sai lệch cần kiểm, không nhằm xếp hạng mọi công trình trên cùng một thang điểm. Các tác vụ chọn điều khoản, sinh câu trả lời, tổng hợp toàn corpus và dự đoán phán quyết có đầu ra và mẫu số khác nhau.
<!-- nguồn: MASTER_RESEARCH_GUIDE.md -->

| Mức sử dụng trong chương | Các khóa |
|---|---|
| Đã đọc trực tiếp các phần được phân tích của PDF gốc cục bộ | `cymbler2026fiscalqa`, `demartim2025satgraph`, `nguyen2026vihermes`, `nguyen2025vlqa` |
| Mới đối chiếu metadata; nội dung chuyên biệt còn chờ đọc gốc | `lewis2020rag`, `karpukhin2020dpr`, `robertson2009bm25`, `edge2024graphrag`, `guo2025lightrag`, `huwiler2025versionrag`, `prior2026oldfriend`, `prior2025consolidation`, `han2025lawshift`, `chen2021timeqa`, `dhingra2022templama`, `thanh2021alqac`, `gardner2020contrast`, `dror2018hitchhiker` |

<!-- nguồn: references.bib -->

Các PDF được đọc qua phần chữ trích bằng `pdftotext`, tập trung vào tóm tắt, thiết kế dữ liệu, phương pháp và giới hạn liên quan. Chương dùng tên mục để định vị nội dung, không khẳng định đã kiểm chứng phân trang PDF. Công cụ preflight trong môi trường hiện tại không đủ phụ thuộc để xác nhận cấu trúc phân trang. [CẦN XÁC MINH: đối chiếu trực quan PDF và tính đầy đủ của bản trích trước khi chốt định vị trang hoặc nhận mức đọc toàn văn].

Ghi chú `related_paper/notes/` và bản dịch FiscalQA giúp xác định những đoạn cần đọc trực tiếp. Báo cáo tổng hợp trong `reports/` tự phân biệt mức đọc và thừa nhận một số phần chưa đọc. Vì vậy, chương không chép các bảng số từ báo cáo tổng hợp, không coi nhãn “đã xác minh” trong bảng hướng dẫn là bằng chứng đã đọc toàn văn ở lần soạn này. Khi nguồn thứ cấp và bản gốc khác nhau về phạm vi khẳng định, nội dung được giới hạn theo phần gốc đã kiểm.
<!-- nguồn: related_paper/notes/README.md -->
<!-- nguồn: related_work_paper/FiscalQA.md -->
<!-- nguồn: reports/Tham khảo bộ dữ liệu pháp luật có hiệu lực và phiên bản.md -->

## 2.2. Truy xuất, sinh câu trả lời và sự phù hợp của căn cứ

### 2.2.1. RAG như một quá trình có thể phân rã

Trong khung thực thi của khóa luận, hệ RAG nhận câu hỏi, tìm các đơn vị văn bản, đưa các đơn vị vào prompt và sinh câu trả lời dựa trên chúng. Cơ chế này tách được ít nhất hai loại thất bại: không đưa đúng căn cứ vào prompt và có căn cứ nhưng sử dụng sai. Một câu trả lời trôi chảy không tự chứng minh bước truy xuất đúng; ngược lại, lấy được điều khoản liên quan chưa bảo đảm câu trả lời sử dụng đúng phiên bản của nó.
<!-- nguồn: src/vilexgraph/framework/retrieve.py -->
<!-- nguồn: src/vilexgraph/framework/generate.py -->
<!-- nguồn: scripts/review/e7_error_analysis.py -->

Bản ghi nền tảng về Retrieval-Augmented Generation được quản lý bằng khóa [@lewis2020rag]. Trong bản nháp này, định nghĩa thao tác ở trên dựa vào cài đặt dự án; chưa dùng bài nền tảng để khẳng định các mức tăng, kết quả hay bảo đảm của RAG. [CẦN XÁC MINH: đọc bản gốc Lewis và cộng sự về kiến trúc RAG, phạm vi tác vụ và điều kiện đánh giá trước khi bổ sung diễn giải chuyên biệt].
<!-- nguồn: references.bib -->

### 2.2.2. Mức liên quan khác với điều kiện sử dụng

Bộ truy xuất của dự án có đường từ vựng, đường dense và đường trộn thứ hạng. Điểm liên quan giúp chọn ứng viên theo câu hỏi, còn bộ lọc hiệu lực kiểm ứng viên có được phép sử dụng tại mốc hỏi hay không. Hai tiêu chí không đồng nhất. Một đơn vị có nhiều từ trùng câu hỏi vẫn có thể chứa lời văn đã hết hiệu lực; phép xếp hạng không tự suy ra ngày áp dụng nếu ngày đó không được đưa vào điều kiện chọn.
<!-- nguồn: src/vilexgraph/framework/retrieve.py -->
<!-- nguồn: src/vilexgraph/framework/temporal.py -->

BM25 và Dense Passage Retrieval là các tài liệu nền được nhận diện trong bibliography [@robertson2009bm25] [@karpukhin2020dpr]. Metadata đủ để xác định tài liệu cần đọc, chưa đủ để chép công thức, cách huấn luyện hoặc kết quả của chúng. [CẦN XÁC MINH: đọc bản gốc BM25 và DPR; đối chiếu giả định của phương pháp với FTS5 và model embedding thực tế của dự án].
<!-- nguồn: references.bib -->

Với chính cài đặt hiện tại, điểm từ vựng được tính trong SQLite FTS5, còn dữ liệu phiên bản và khoảng hiệu lực nằm ở các bảng dẫn xuất. Đây là mô tả engine đã được kiểm qua code, không phải khẳng định rằng mọi hệ RAG đều dùng cùng cơ chế hoặc rằng điểm dense sẽ giải quyết được khác biệt nhỏ giữa các phiên bản.
<!-- nguồn: src/vilexgraph/framework/corpus.py -->
<!-- nguồn: src/vilexgraph/framework/retrieve.py -->

### 2.2.3. Đồ thị là một nhóm cơ chế, không phải một phép đo duy nhất

Tên GraphRAG có thể bao phủ nhiều cách đưa quan hệ vào xử lý. Đối với khóa luận, cần phân biệt quan hệ cấu trúc, quan hệ sửa đổi, việc dựng lịch sử ngoại tuyến và mở rộng căn cứ trực tuyến. Một phép đối chứng chỉ có ý nghĩa khi xác định rõ cơ chế nào được thêm hoặc bỏ. Tên của hệ không thể thay thế bảng cấu hình thực thi.
<!-- nguồn: src/vilexgraph/framework/systems.py -->
<!-- nguồn: docs/decisions/0004-framework-truy-xuat-va-sinh.md -->

Hai bản ghi nền trong repo là công trình GraphRAG của Edge và cộng sự và LightRAG [@edge2024graphrag] [@guo2025lightrag]. Chương chưa xác nhận trực tiếp từ bản gốc cấu trúc đồ thị, cơ chế truy xuất hoặc kết quả so sánh của hai bài này. [CẦN XÁC MINH: đọc bản gốc GraphRAG và LightRAG; chưa dùng tóm tắt hoặc tên bài để suy rằng chúng không xử lý thời gian hay kém hơn phương pháp của khóa luận].
<!-- nguồn: references.bib -->

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

Các bản ghi TimeQA và TempLAMA được đưa vào lộ trình đọc về hỏi đáp nhạy thời gian [@chen2021timeqa] [@dhingra2022templama]. Chương chỉ nhận diện phạm vi nghiên cứu qua metadata, chưa khẳng định schema, cách lấy mốc hoặc độ chính xác của các bài. [CẦN XÁC MINH: đọc bản gốc TimeQA và TempLAMA trước khi dùng chúng làm tiền lệ cụ thể cho thiết kế một câu hỏi ở nhiều mốc].
<!-- nguồn: references.bib -->

### 2.3.3. Sai lệch căn cứ theo thời gian trong FiscalQA Pro

FiscalQA Pro đặt hiện tượng temporal misgrounding làm đối tượng đánh giá [@cymbler2026fiscalqa]. Phần mở đầu bản gốc mô tả việc dùng bản đang có hiệu lực hiện tại trong khi ngữ cảnh câu hỏi đòi một phiên bản khác. Phần phương pháp phân biệt chỉ mục chỉ có bản hiện hành với chỉ mục nhiều phiên bản được điều kiện hóa theo ngày. Bài do đó là bằng chứng rằng bài toán RAG pháp luật theo thời gian đã có tiền lệ; khóa luận không thể tuyên bố phát minh ra bài toán này.
<!-- nguồn: related_paper/2608.09393v1.pdf -->

Điểm cần chú ý trong thiết kế FiscalQA Pro là điều kiện RAG tĩnh trong phép so sánh được cấp định danh điều luật gold nhưng phục vụ bản hiện hành. Đây không phải cùng điều kiện với một retriever phải tìm điều luật trên toàn kho mà không biết gold. Vì thế, khi học cách phân rã lỗi từ bài, cần giữ nguyên điều kiện thông tin của từng hệ thay vì gọi mọi cấu hình có truy xuất là tương đương.
<!-- nguồn: related_paper/2608.09393v1.pdf -->

Bài chấm bằng các nugget có thể kiểm tất định, phân biệt độ phủ nội dung, điểm strict và provenance của phiên bản. Phần lựa chọn câu hỏi còn lọc theo việc model đã trả được đáp án hay chưa và liệu giá trị gold còn xuất hiện trong bản hiện hành hay không. Tập được giữ vì thế có tính chọn lọc theo hiện tượng và năng lực của các model dùng khi chọn; nó không phải mẫu ngẫu nhiên của mọi câu hỏi thuế. Đây là nhận xét về thiết kế đã đọc, không trích lại kết quả điểm số của bài.
<!-- nguồn: related_paper/2608.09393v1.pdf -->

Phụ lục bản gốc phân biệt artifact công khai với bộ truy xuất end-to-end có thành phần độc quyền. Sự công khai của corpus hoặc câu trả lời không tự làm mọi điều kiện end-to-end tái lập được. Với khóa luận này, bài học phương pháp là phải công bố cả đơn vị gold, điều kiện cấp căn cứ và phần pipeline có thể dựng lại. Bản dịch tiếng Việt trong repo chỉ hỗ trợ đọc thuật ngữ; nội dung khẳng định ở đây được đối chiếu PDF gốc.
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_work_paper/FiscalQA.md -->

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

ViHERMES nghiên cứu hỏi đáp đa bước trên quy định y tế tiếng Việt [@nguyen2026vihermes]. Bản gốc mô tả dữ liệu có căn cứ và chú giải suy luận, cùng hệ graph-aware sử dụng các quan hệ sửa đổi, thay thế, bổ sung và dẫn chiếu. Vì đã có công trình như vậy, không được tuyên bố khóa luận là trường hợp đầu tiên dùng quan hệ đồ thị cho hỏi đáp pháp luật tiếng Việt.
<!-- nguồn: related_paper/ViHERMES.pdf -->

Mục Seeded Retrieval and Propagation mô tả lấy các nút seed, mở rộng theo loại quan hệ và ưu tiên nút cuối chuỗi sửa đổi như căn cứ có thể áp dụng. Phần phương pháp đã đọc không đặc tả việc chọn một phiên bản theo mốc `as_of` tường minh như ViLexTime; kết luận của bài đặt việc làm giàu temporal validity vào hướng tiếp tục. Sự khác biệt cần nêu là cách điều kiện hóa bằng chứng theo mốc, không phải quy ViHERMES thành hệ “không biết gì về sửa đổi”.
<!-- nguồn: related_paper/ViHERMES.pdf -->

Các ghi chú trong repo cũng nhắc quan hệ sửa đổi và validity tracing của ViHERMES. Vì thế, cách viết phủ định tuyệt đối rằng công trình trong nước chưa xét quan hệ hoặc tính hợp lệ sẽ bỏ qua chính phần đã xác minh. Khóa luận chỉ dùng đối chiếu này để xác định yêu cầu thử nghiệm theo ngày, không khẳng định đã có một phép so sánh trực tiếp với hệ ViHERMES trên cùng dữ liệu.
<!-- nguồn: related_paper/notes/03-vihermes.md -->
<!-- nguồn: reports/Tham khảo bộ dữ liệu pháp luật có hiệu lực và phiên bản.md -->

### 2.4.3. Giới hạn phạm vi khảo sát trong nước

Bản ghi ALQAC trong thư mục tham khảo hiện là bài tổng kết cuộc thi với khóa [@thanh2021alqac]. Không được thay nó bằng một bài tổng kết năm khác chỉ vì tên cuộc thi giống nhau. [CẦN XÁC MINH: đọc bản gốc ALQAC đã có khóa, xác định tác vụ và phạm vi corpus; không sử dụng mục chưa xác minh của đề cương để khẳng định nội dung].
<!-- nguồn: references.bib -->
<!-- nguồn: MASTER_RESEARCH_GUIDE.md -->

Repo còn các ghi chú về VietLegal, LegalGraphRAG và một khung suy luận có kiểm chứng; chúng cho thấy khảo sát chưa nên dừng ở các khóa hiện có. Chương chưa dùng các ghi chú này để khẳng định kết quả hoặc tính mới. [CẦN TRÍCH DẪN: hoàn tất xác minh bản gốc và khóa bib cho các công trình trong nước/bổ sung còn nằm ngoài references.bib trước khi đưa vào đối chiếu học thuật].
<!-- nguồn: related_paper/notes/05-vietlegal-benchmark.md -->
<!-- nguồn: related_paper/notes/08-legalgraphrag-acl2026.md -->
<!-- nguồn: related_paper/notes/09-verifiable-reasoning-framework-icoco2026.md -->

## 2.5. Bảng đối chiếu các công trình gần nhất

Bảng tách nội dung được xác nhận trực tiếp với phần mới nhận diện qua metadata. “Chưa xác minh” là trạng thái đọc của bản nháp, không có nghĩa công trình thiếu thành phần đó. Không trình bày điểm số của các tác vụ khác nhau thành bảng xếp hạng chung.

| Công trình | Bài toán hoặc cơ chế được phép mô tả ở bản nháp | Quan hệ với khóa luận | Đã xác minh ở đâu | Giới hạn sử dụng |
|---|---|---|---|---|
| FiscalQA Pro [@cymbler2026fiscalqa] | Chọn phiên bản theo ngày; nugget và provenance; lọc câu hỏi theo hiện tượng | Tiền lệ trực tiếp cho đánh giá temporal misgrounding | PDF `2608.09393v1.pdf`, các mục Introduction, Nugget-Based Scoring, Experimental Design và phụ lục public/private artifacts | Chưa đọc toàn văn; không trích số; pipeline end-to-end không hoàn toàn công khai |
| SAT-Graph RAG [@demartim2025satgraph] | Work/Expression, phiên bản thành phần, Action, chính sách truy vấn | Tiền lệ mô hình cấu trúc–thời gian và truy nguyên | PDF `An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf`, Proposed Framework, Case Study, Discussion | Bản gốc đã đọc là arXiv v5; case study định tính; còn đối soát bản kỷ yếu |
| ViHERMES [@nguyen2026vihermes] | Graph-aware multihop QA; mở rộng theo quan hệ; ưu tiên cuối chuỗi sửa đổi | Đối chiếu trong nước về vai trò đồ thị và điều kiện thời gian | PDF `ViHERMES.pdf`, SRKG, Seeded Retrieval and Propagation, Conclusion | Không biến tracing sửa đổi thành phủ định “không có thời gian”; chưa so trực tiếp cùng benchmark |
| VLQA [@nguyen2025vlqa] | Câu hỏi tư vấn, corpus điều luật, kiểm chuyên gia; loại điều khoản bãi bỏ | Đối chiếu dữ liệu tiếng Việt và nguồn gốc nhãn | PDF VLQA, Dataset Construction và Expert Annotation | Cần xác nhận thông tin xuất bản; không suy chất lượng ViLexTime từ quy trình của VLQA |
| VersionRAG [@huwiler2025versionrag] | Metadata nhận diện công trình nhận biết phiên bản cho tài liệu thay đổi | Ứng viên đối chiếu trực tiếp về biểu diễn phiên bản | `references.bib`, trường title/eprint/checked | [CẦN XÁC MINH: đọc bản gốc VersionRAG trước khi mô tả đồ thị, định tuyến, dữ liệu hoặc kết quả] |
| Statutory QA theo thời gian [@prior2026oldfriend] | Metadata nhận diện bài chẩn đoán failure modes trong statutory QA | Ứng viên đối chiếu trực tiếp về ngày áp dụng và thiết kế benchmark | `references.bib`; báo cáo tổng hợp chỉ dùng làm chỉ dẫn đọc | [CẦN XÁC MINH: đọc bản gốc Prior và cộng sự về temporal statutory QA; chưa xác nhận bộ nhãn, IAA hoặc kết quả lọc ngày] |
| Hợp nhất luật tự động [@prior2025consolidation] | Metadata nhận diện nghiên cứu về rủi ro và giới hạn hợp nhất | Nguồn cần kiểm để lập luận về chất lượng lời văn dẫn xuất | `references.bib`, trường title/DOI/checked | [CẦN XÁC MINH: đọc bản gốc Risks and Limits of Automatic Consolidation of Statutes; chưa sử dụng tỷ lệ khớp từ bản tóm tắt] |
| LawShift [@han2025lawshift] | Metadata ghi bài toán dự đoán phán quyết khi luật thay đổi | Hướng đối chiếu về loại biến đổi, khác đầu ra QA theo mốc | `references.bib`; báo cáo repo ghi có đọc một số phần nhưng chưa đủ toàn bài | [CẦN XÁC MINH: đối chiếu bản gốc LawShift trước khi mượn taxonomy, cách tạo thay đổi và quy trình chuyên gia] |

<!-- nguồn: references.bib -->
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: related_paper/ViHERMES.pdf -->
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->
<!-- nguồn: reports/Tham khảo bộ dữ liệu pháp luật có hiệu lực và phiên bản.md -->

## 2.6. Cơ sở đánh giá và độ tin cậy

### 2.6.1. Tách đúng nội dung, đúng phiên bản và đúng căn cứ

FiscalQA Pro phân biệt kiểm nugget nội dung với provenance của phiên bản. SAT-Graph RAG phân biệt chọn phiên bản, quy tác động và dựng provenance trong phần đề xuất đánh giá. Hai tiền lệ cho thấy “có trích dẫn” và “trích đúng căn cứ theo thời gian” là những điều cần kiểm riêng. Tuy nhiên, chương không gộp các metric của họ với metric ViLexTime: phép chấm của khóa luận vẫn do ADR và scorer đã khóa quyết định.
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

Trong cài đặt ViLexTime, Recall đo lấy được điều khoản hoặc bằng chứng chấp nhận; TV-Recall yêu cầu phiên bản hoặc ID bằng chứng gold. Accuracy kiểm các span bắt buộc và tránh span riêng của phiên bản khác. TVER chỉ xét phạm vi trích dẫn theo định nghĩa của scorer, nên cần báo kèm độ phủ và strict. Đây là các định nghĩa thao tác của bộ đánh giá, không phải khẳng định đã tạo ra một họ chỉ số mới.
<!-- nguồn: scripts/eval/score_vilextime.py -->

Bản ghi về contrast sets được giữ trong danh mục [@gardner2020contrast]. [CẦN XÁC MINH: đọc bản gốc contrast sets trước khi khẳng định quan hệ chính xác giữa contrast consistency trong bài và TCS của ViLexTime; không tuyên bố TCS là chỉ số mới].
<!-- nguồn: references.bib -->
<!-- nguồn: MASTER_RESEARCH_GUIDE.md -->

### 2.6.2. Chất lượng gold và đơn vị độc lập

Một pipeline chạy tất định có thể tái tạo cùng lỗi nhiều lần. SAT-Graph RAG nêu rõ phụ thuộc chất lượng metadata và khoảng hiệu lực thượng nguồn. Trong ViLexTime, gold và hệ đề xuất cùng dùng chuỗi phiên bản, nên việc hai bên đồng ý không phải kiểm chứng độc lập về pháp lý. Cần tách kiểm nhất quán code, đồng thuận nhãn và kiểm gold độc lập; mỗi loại bằng chứng trả lời một câu hỏi khác nhau.
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: docs/vilextime-datasheet.md -->

Các dòng cùng lineage chia sẻ câu hỏi và bằng chứng. Phân tích của dự án vì thế lấy lineage làm cụm lấy mẫu lại thay vì giả định mỗi dòng là quan sát độc lập. Họ kiểm định, chiều dự đoán và ngưỡng được quy định trong ADR; số thăm dò không tự trở thành xác nhận khi thấy một khoảng tin cậy thuận lợi. Tài liệu nền về kiểm định trong NLP đã có khóa [@dror2018hitchhiker], nhưng chưa được đọc gốc trong lượt này. [CẦN XÁC MINH: đọc bản gốc tài liệu kiểm định NLP trước khi dùng nó để biện minh cho lựa chọn thống kê cụ thể; hiện đặc tả được dẫn từ ADR và code].
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->
<!-- nguồn: scripts/eval/confirm_vilextime.py -->
<!-- nguồn: references.bib -->

## 2.7. Khoảng trống nghiên cứu và ranh giới tuyên bố

### 2.7.1. Điều có thể nói từ phạm vi đã khảo sát

Các phần gốc đã kiểm cho thấy có tiền lệ về temporal legal QA, mô hình điều khoản có phiên bản và graph-aware QA tiếng Việt. Vì vậy, đóng góp của khóa luận không thể được xác lập bằng các tuyên bố rộng như “đầu tiên mô hình hóa phiên bản luật”, “đầu tiên làm benchmark pháp luật theo thời gian” hoặc “đầu tiên dùng đồ thị cho RAG pháp luật tiếng Việt”. Sự có mặt của các tiền lệ này cần được phản ánh ngay cả khi cài đặt, ngôn ngữ hoặc cách đánh giá của chúng khác khóa luận.
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: related_paper/ViHERMES.pdf -->
<!-- nguồn: MASTER_RESEARCH_GUIDE.md -->

Một mục tiêu hẹp hơn là xây phép đánh giá theo mốc trên nguồn pháp luật tiếng Việt của dự án và dùng B7 cùng thang biểu diễn để kiểm nguồn gốc chênh lệch. Việc này nối câu hỏi về tài nguyên với câu hỏi về phép đối chứng: có cần lời văn hợp nhất và khoảng phiên bản, hay phần lớn lợi ích quan sát được đã xuất hiện ở bộ lọc cấp văn bản? Đây là câu hỏi thực nghiệm được đặt ra, không phải một kết luận mới về hiệu quả phương pháp.
<!-- nguồn: docs/decisions/0004-framework-truy-xuat-va-sinh.md -->
<!-- nguồn: docs/decisions/0005-ke-hoach-phan-tich.md -->

### 2.7.2. Điều chưa đủ để khẳng định tính mới

Guide yêu cầu một lượt tìm có mục tiêu trước khi dùng tuyên bố hẹp kèm cụm “theo khảo sát của chúng tôi”. Lượt soạn này không có mạng và không tiến hành tìm mới. Chưa thể chuyển việc chưa thấy một artifact tương ứng trong repo thành bằng chứng chưa có ai làm. [CẦN XÁC MINH: hoàn tất hoặc tìm lại biên bản khảo sát có truy vấn, phạm vi, ngày tra và kết quả trước khi chốt tuyên bố tính mới hẹp].
<!-- nguồn: MASTER_RESEARCH_GUIDE.md -->

Với SAT-Graph RAG, phần đã đọc xác nhận mô hình cấu trúc–thời gian và các chính sách truy vấn, nhưng chưa đủ để kết luận toàn bộ công trình không có một phép đối chứng cụ thể nếu chưa kiểm các phiên bản liên quan. Với VersionRAG và các công trình temporal QA còn mới đọc metadata, càng không được viết một mệnh đề phủ định về điều tác giả “chưa làm”. Khoảng trống hiện được trình bày như nhu cầu kiểm chứng của khóa luận, chờ hoàn tất khảo sát, thay vì chứng nhận sự vắng mặt của mọi tiền lệ.
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: references.bib -->

Các khái niệm chuẩn hóa như Akoma Ntoso và LRMoo được nhắc trong SAT-Graph RAG. Chương chỉ mô tả cách bài đó sử dụng các khái niệm, không nhận đã xác minh đầy đủ chính tiêu chuẩn gốc. [CẦN TRÍCH DẪN: tài liệu chuẩn gốc của Akoma Ntoso và LRMoo nếu khóa luận trình bày độc lập cấu trúc hoặc bảo đảm của chúng; hiện chưa có khóa phù hợp trong references.bib].
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->

## 2.8. Câu trả lời có bằng chứng

Các nguồn gốc đã đối chiếu hỗ trợ việc phân biệt hiệu lực theo ngày, danh tính điều khoản, lời văn phiên bản và provenance; đồng thời cho thấy đồ thị và xử lý lịch sử không phải các ý tưởng chưa từng được nghiên cứu. Tài nguyên tiếng Việt đã có kiểm chuyên gia và truy xuất theo quan hệ, nhưng thiết kế theo mốc và phép đối chứng cụ thể vẫn cần được xem xét trên từng công trình. Cách lập luận có thể bảo vệ cho khóa luận là xác định rõ đầu vào–đầu ra, công bố nguồn gold và kiểm nguồn gốc chênh lệch trong phạm vi đã đo. Chưa có cơ sở để tuyên bố đứng đầu hoặc đầu tiên trên toàn lĩnh vực.
<!-- nguồn: related_paper/2608.09393v1.pdf -->
<!-- nguồn: related_paper/An_Ontology_Driven_GraphRAG_for_LegalNorms.pdf -->
<!-- nguồn: related_paper/ViHERMES.pdf -->
<!-- nguồn: related_paper/VLQA_ The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering.pdf -->

## Việc còn thiếu trước khi nộp

- Đọc bản gốc các mục còn mới đối chiếu metadata, ghi chính xác phần đã đọc và chỉ bổ sung số liệu sau khi đọc đủ phạm vi.
- Kiểm trực quan PDF, phiên bản SAT-Graph RAG, thông tin xuất bản VLQA và định vị trích dẫn; không suy nơi công bố từ mẫu trình bày.
- Hoàn tất khảo sát có mục tiêu trước khi xác lập tính mới; tránh mọi khẳng định phủ định toàn lĩnh vực.
- Nhóm xác minh các nguồn còn thiếu khóa khi có điều kiện; bản nháp này không tự thêm tài liệu vào bibliography.
- Tác giả kiểm nội dung phương pháp luận và thuật ngữ; ghi chú/bản dịch do AI hỗ trợ không thay việc đọc gốc.
