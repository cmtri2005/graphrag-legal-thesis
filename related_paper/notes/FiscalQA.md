# Temporal Misgrounding trong RAG pháp lý: Bộ benchmark kho văn bản có phiên bản cho luật thuế Pháp

**Rose Cymbler¹, Daniel Guez¹, Laurent Fabre²**

¹Talia, Paris, Pháp · ²Databricks · Liên hệ: Rose Cymbler &lt;rose.cymbler@talia-ai.com&gt;

*ICML 2026 Workshop on AI for Law (AI4Law), Seoul, Hàn Quốc, 2026. arXiv:2608.09393v1 [cs.CL], 10/08/2026.*

&gt; *Đây là bản dịch tiếng Việt không chính thức. Tên riêng, tên mô hình, tên bộ dữ liệu, thuật ngữ kỹ thuật và tên file được giữ nguyên tiếng Anh/Pháp. Một số thuật ngữ được kèm bản gốc trong ngoặc ở lần xuất hiện đầu tiên.*

---

## Tóm tắt (Abstract)

Chúng tôi nhận diện và định lượng hiện tượng **temporal misgrounding** (sai lệch căn cứ theo thời gian): việc hệ thống truy xuất và trích dẫn một cách có hệ thống phiên bản *đang có hiệu lực hiện nay* của một điều luật, trong khi phiên bản cần áp dụng lại là một phiên bản trước đó hoặc trong tương lai. RAG pháp lý tiêu chuẩn coi kho văn bản là tĩnh; chúng tôi cho rằng việc trả lời câu hỏi pháp lý là một bài toán truy xuất *được đánh chỉ mục theo thời gian*. Chúng tôi giới thiệu **FiscalQA Pro**, gồm một kho văn bản có phiên bản với 32.436 phiên bản điều luật của Bộ luật Thuế Pháp (93 năm, 1938–2031) cùng một track suy luận thời gian "khó đối với mọi mô hình": 209 câu hỏi được chấm điểm, do chuyên gia rà soát, thuộc 33 điều của CGI (công bố 221 câu; mười hai câu bị đánh dấu nằm ngoài phạm vi có thể trả lời). Tại thời điểm tuyển chọn, không mô hình nào được đánh giá khôi phục được đáp án áp dụng theo ngày ở chế độ closed-book trong bất kỳ lần nào trong bốn lần lấy mẫu, và văn bản đang có hiệu lực hiện hành không chứa giá trị đáp án chuẩn ở tất cả trừ một câu hỏi được chấm. Câu trả lời được chấm điểm một cách tất định (deterministic) thông qua các "nugget" sự thật nguyên tử (regex và so khớp số có dung sai), không bao giờ dùng LLM-as-judge: một LLM làm giám khảo sẽ thừa hưởng chính thiên lệch về thời gian mà nó đáng ra phải chấm. Trên mười một mô hình (năm hệ thống API đóng hàng đầu cộng Gemini 2.5 Pro làm mục thay thế, và năm mô hình open-weight), tri thức tham số (parametric) cho độ chính xác strict trung bình 3,0% và RAG trên kho văn bản chỉ-phiên-bản-hiện-hành tĩnh cho 2,7%. RAG tĩnh truy xuất được phiên bản áp dụng theo ngày trong 0% trường hợp, và tự tin trích dẫn một phiên bản có thật nhưng không áp dụng được. Bộ truy xuất end-to-end của chúng tôi trên chỉ mục đa phiên bản, không dùng oracle, đạt **98,3%** strict trung bình; thí nghiệm ablation với điều luật oracle đạt 99,1%, cho thấy khoảng cách còn lại nằm ở recall giai đoạn đầu, không phải ở việc chọn phiên bản. Chúng tôi cũng công bố một bộ dữ liệu án lệ có nhận biết phiên bản gồm 69.208 liên kết trích dẫn, cùng với kho văn bản, benchmark, các phản hồi của mô hình và mã pipeline.¹

---

## 1. Giới thiệu

**Động lực.** Những tiến bộ gần đây của các mô hình ngôn ngữ lớn (LLM) và sinh văn bản tăng cường truy xuất (RAG) đã thúc đẩy một làn sóng benchmark NLP pháp lý nhằm đo lường khả năng suy luận pháp lý, trích xuất trích dẫn và hiểu tài liệu (Guha và cs., 2023; Niklaus và cs., 2023; Douka và cs., 2021). Tuy nhiên, phần lớn các benchmark này có chung một giả định ngầm quan trọng: rằng kho văn bản pháp luật là *tĩnh*. Giả định này bị vi phạm rõ rệt nhất trong luật thuế, nơi các đạo luật được sửa đổi hằng năm thông qua các đạo luật tài chính (*lois de finances*) và nơi câu trả lời đúng cho một câu hỏi pháp lý thường phụ thuộc quyết định vào ngày áp dụng. Một người nộp thuế hỏi "thuế suất thuế thu nhập doanh nghiệp tiêu chuẩn năm 2018 là bao nhiêu?" cần nhận được 33⅓%, chứ không phải mức 25% hiện hành. Tuy nhiên, một LLM tiên tiến được huấn luyện đến năm 2025, dù có hay không có truy xuất trên kho văn bản phiên bản hiện hành, sẽ luôn trả về mức sau.

**Hiện tượng: temporal misgrounding.** Chúng tôi đặt tên cho kiểu thất bại này: **temporal misgrounding**. Đó là việc thay thế một cách có hệ thống phiên bản đang có hiệu lực hiện nay của một điều luật cho phiên bản lẽ ra phải được áp dụng theo bối cảnh thời gian của câu hỏi. Temporal misgrounding có ba nguyên nhân gốc đồng thời:

1. *Thiên lệch tính mới của tri thức tham số (parametric recency bias).* LLM được huấn luyện trên các "ảnh chụp nhanh" vốn đại diện quá mức cho trạng thái pháp lý gần đây nhất, khiến giả định tiên nghiệm của chúng nghiêng về luật hiện hành.
2. *Thiếu điều kiện hóa theo thời gian trong truy xuất.* Các bộ truy xuất dense tiêu chuẩn đánh chỉ mục kho văn bản theo độ tương đồng ngữ nghĩa mà không điều kiện hóa theo ngày được ngầm hiểu trong truy vấn.
3. *Hiện tượng trùng lặp số hiệu điều luật (article-number aliasing).* Số hiệu điều luật tồn tại xuyên suốt các phiên bản (ví dụ: điều 219 của CGI có mặt ở mọi phiên bản của bộ luật), nên truy xuất ngây thơ không thể phân biệt phiên bản nào được nhắm đến.

**Câu hỏi nghiên cứu.** Chúng tôi hỏi: *Trên các câu hỏi pháp lý mà đáp án áp dụng theo ngày khác với luật đang có hiệu lực hiện nay, temporal misgrounding làm nghẽn độ chính xác của các LLM và hệ thống RAG hiện đại nhất ở mức độ nào?* Chúng tôi chủ ý cô lập chế độ này (§5): đây là nơi temporal misgrounding mang tính chẩn đoán, vì vậy các khoảng cách được báo cáo là có điều kiện trên chế độ này chứ không phải trung bình trên toàn bộ QA pháp lý. Chúng tôi đưa ra giả thuyết **(H)** rằng tính hợp lệ theo thời gian là một trục bậc nhất của việc neo căn cứ pháp lý (legal grounding), rằng việc điều kiện hóa truy xuất một cách tường minh theo bối cảnh thời gian của truy vấn sẽ thu hẹp phần lớn khoảng cách giữa hiệu năng chỉ-LLM và hiệu năng có điều kiện phiên bản, và rằng một bộ truy xuất end-to-end, chứ không chỉ một oracle, hiện thực hóa được điều đó.

**Đóng góp.** Chúng tôi hỗ trợ giả thuyết này bằng các đóng góp sau:

- Một đặc trưng hóa temporal misgrounding như một kiểu thất bại riêng biệt của RAG pháp lý, kèm phân loại gồm bốn chế độ con (§3).
- Một kho văn bản có phiên bản gồm 32.436 phiên bản điều luật CGI/LPF trải dài 93 năm (1938–2031), bao gồm cả các phiên bản có hiệu lực trong tương lai, cùng một bộ dữ liệu phụ gồm 69.208 liên kết án lệ có nhận biết phiên bản (độ chính xác 98–99%; §4, Phụ lục B).
- Một benchmark mà track thời gian R3 gồm 209 câu hỏi được chấm điểm, do chuyên gia rà soát, khó đối với mọi mô hình, thuộc 33 điều CGI (công bố 221 câu) trong khung bốn chế độ, được chấm tất định qua nugget thay vì LLM-as-judge (§5); R2/R4 được công bố như các track bổ sung.
- Một thí nghiệm có kiểm soát gồm ba điều kiện (§6) định lượng khoảng cách độ chính xác giữa LLM-only / RAG tĩnh / RAG nhận biết phiên bản trên các câu hỏi thời gian.

**Định vị.** FiscalQA Pro mở rộng phương pháp luận của OfficeQA Pro (Opsahl-Ong và cs., 2026) (suy luận có neo căn cứ tất định trên các Bản tin của Kho bạc Hoa Kỳ) sang một bối cảnh nơi các tài liệu nền được sửa đổi tại chỗ thay vì được nối thêm, và nơi ngày áp dụng tự nó là một tín hiệu truy xuất hạng nhất. Khác với SAT-Graph RAG (de Martim, 2025), vốn giải quyết các truy vấn pháp lý theo thời điểm thông qua một đồ thị tri thức dựa trên ontology, phương pháp của chúng tôi không cần ontology hay xây dựng đồ thị, chỉ cần đánh chỉ mục phiên bản tường minh và truy xuất có điều kiện theo ngày trên kho văn bản có phiên bản thô. Chúng tôi tập trung vào luật thuế vì nó tối đa hóa hiện tượng được nghiên cứu: sửa đổi hằng năm qua các đạo luật tài chính, đáp án nhạy cảm với ngày (thuế suất, ngưỡng, quy tắc khấu trừ), và án lệ có tham chiếu chéo phong phú cho phép liên kết có nhận biết phiên bản giữa luật thành văn và án lệ.

¹ https://github.com/rosecymbler/fiscal-fr-bench

---

## 2. Các công trình liên quan

**Các benchmark pháp lý.** LegalBench (Guha và cs., 2023) cung cấp 162 tác vụ bao phủ suy luận pháp lý Hoa Kỳ về áp dụng quy tắc, phát hiện vấn đề và hiểu biết tu từ, tất cả bằng tiếng Anh và chủ yếu không đánh chỉ mục thời gian. LEXTREME (Niklaus và cs., 2023) mở rộng độ phủ đa ngôn ngữ với 18 tác vụ trên 24 ngôn ngữ thuộc nhiều hệ thống pháp luật. LEXam (Fan và cs., 2026b) đánh giá suy luận pháp lý trên 340 đề thi luật song ngữ (EN/DE) thuộc nhiều khu vực pháp lý, chấm theo rubric; trực giao với trục của chúng tôi, nó đánh giá chất lượng suy luận trên một trạng thái pháp luật cố định thay vì neo căn cứ theo thời gian xuyên các phiên bản. JuriBERT (Douka và cs., 2021) là một BERT pháp lý tiếng Pháp, và ClaimRAG-LAW (Das và cs., 2026) là một benchmark RAG pháp lý ở mức mệnh đề (claim) chi tiết. Không benchmark nào trong số này đánh giá tường minh sự trôi dạt theo thời gian trong QA pháp lý.

**Suy luận có neo căn cứ trong doanh nghiệp.** OfficeQA Pro (Opsahl-Ong và cs., 2026) giới thiệu một benchmark doanh nghiệp cho suy luận có neo căn cứ end-to-end trên các Bản tin Kho bạc Hoa Kỳ, gồm 133 câu hỏi trên kho văn bản 89.000 trang trải dài gần một thế kỷ. Đánh giá của họ là tất định: câu trả lời được kiểm tra với các giá trị số, trích dẫn và ngày tháng thay vì qua LLM-as-judge. Họ cho thấy các LLM hàng đầu đạt dưới 5% độ chính xác chỉ với tri thức tham số, 12% khi có truy cập web, và 34,1% khi truy cập trực tiếp kho văn bản (cho thấy còn nhiều dư địa ngay cả ở tuyến đầu).

**Truy xuất dạng tác tử và chấm điểm theo nugget.** KARL (Databricks AI Research, 2026) giới thiệu KARLBench, một bộ đánh giá đa năng lực bao phủ sáu chế độ tìm kiếm, và đề xuất một thước đo dựa trên nugget: các đáp án chuẩn được chuyển thành các "nugget" nguyên tử, và một phản hồi của mô hình được chấm theo tỷ lệ nugget mà nó bao phủ. Chúng tôi lưu ý rằng chấm điểm theo nugget như được hiện thực trong KARL vẫn là một biến thể của LLM-as-judge: một LLM phán xét liệu mỗi nugget có được phản hồi hỗ trợ hay không, nhưng phán xét đó được neo vào các sự kiện nguyên tử do chuyên gia biên soạn thay vì các rubric tự do. Họ cũng giới thiệu OAPL, một quy trình học tăng cường off-policy để huấn luyện các tác tử tìm kiếm doanh nghiệp. Chúng tôi tiếp nhận cách phân rã nugget và khung đa tác vụ của họ, nhưng loại bỏ hoàn toàn giám khảo bằng cách giới hạn nugget ở các loại có thể kiểm tra tất định: định danh điều luật được so khớp bằng regex và giá trị số được so khớp có dung sai (§5.2).

**Neo căn cứ thời gian trong NLP.** Hỏi đáp thời gian được khảo sát bởi Piryani và cs. (2025). TempLAMA (Dhingra và cs., 2022) và TimeQA (Chen và cs., 2021) khám phá suy luận thời gian trong QA dữ kiện, phát hiện rằng LLM mặc định một cách có hệ thống theo sự kiện gần nhất đã thấy trong huấn luyện. Vu và cs. (2023) mở rộng điều này sang QA miền mở động với benchmark FreshQA. LexTime (Barale, 2025) nghiên cứu sắp xếp thứ tự sự kiện thời gian trong các đơn kiện liên bang Hoa Kỳ; FiscalQA Pro bổ sung cho công trình này bằng cách giải quyết việc điều kiện hóa theo phiên bản của truy xuất luật thành văn (nơi trục thời gian là chính bộ luật chứ không phải các sự kiện đang được xét xử). Trực tiếp nhất, SAT-Graph RAG (de Martim, 2025) giải quyết các truy vấn pháp lý theo thời điểm thông qua một đồ thị tri thức dựa trên ontology (đối chiếu với cách tiếp cận không đồ thị của chúng tôi ở §1), nhưng đánh giá nó như một nghiên cứu tình huống định tính trên Hiến pháp Brazil thay vì một benchmark có chấm điểm. Hai công trình đồng thời với bài nộp của chúng tôi nghiên cứu cùng thất bại này: Fan và cs. (2026a) chẩn đoán thiên lệch mốc huấn luyện và việc thiếu các ràng buộc thời gian trong các tác tử tìm kiếm pháp lý (nguyên nhân (1)–(2) của chúng tôi) trên một benchmark RL gồm 13 tác vụ, và Prior và cs. (2026) công bố 312 cặp QA luật thành văn Đức được chuyên gia xác thực với các điều kiện RAG lọc theo phiên bản. Sự hội tụ độc lập của họ nhấn mạnh rằng temporal misgrounding là một thất bại thực sự và có tính tổng quát của RAG pháp lý. Chúng tôi khác ở ba trục: cách chấm điểm của chúng tôi là tất định (regex / số có dung sai), trong khi Prior và cs. (2026) dùng LLM-as-judge vốn thừa hưởng chính thiên lệch thời gian mà nó chấm (§5.2); kho văn bản của chúng tôi được đánh chỉ mục phiên bản ở độ chi tiết mịn (32.436 phiên bản trong 93 năm, kể cả các phiên bản có hiệu lực trong tương lai); và bộ lọc "khó đối với mọi mô hình" của chúng tôi bao trùm mười một mô hình. Chúng tôi dự định temporal misgrounding là một khái niệm bao trùm, gồm cả tình trạng lỗi thời sau mốc huấn luyện và thiên lệch tính mới của họ.

**NLP pháp lý tiếng Pháp.** Các tài nguyên sẵn có gồm API Légifrance mở (DILA/PISTE) cho luật thành văn, Judilibre cho án lệ của Cour de cassation, và Arianeweb cho các quyết định của Conseil d'État. Chúng tôi xây dựng trực tiếp trên các nguồn công khai này, giữ nguyên đầy đủ nguồn gốc (provenance) ở mức phiên bản điều luật.

---

## 3. Vì sao RAG tĩnh thất bại trong QA pháp lý

Trước khi mô tả kho văn bản và benchmark, chúng tôi trình bày lý do các kiến trúc RAG tiêu chuẩn (vốn chiếm ưu thế trong các triển khai AI pháp lý hiện nay) thất bại một cách có hệ thống trên các câu hỏi pháp lý có neo căn cứ thời gian. Chúng tôi cho rằng nguyên nhân gốc mang tính cấu trúc, không phải giai thoại: nó phát sinh từ sự kết hợp của ba thuộc tính độc lập của (i) kho văn bản pháp luật, (ii) các kiến trúc truy xuất điển hình, và (iii) các tiên nghiệm tham số của LLM.

### 3.1. Các thuộc tính cấu trúc của kho văn bản pháp luật làm hỏng truy xuất tĩnh

**(P1) Cùng định danh, nội dung khác nhau.** Điều 219 của CGI Pháp tồn tại ở mọi thời điểm, nhưng nội dung thực chất của nó (ví dụ: thuế suất thuế thu nhập doanh nghiệp tiêu chuẩn) khác nhau giữa các phiên bản: 33⅓% năm 2018, 31% năm 2019, 28% năm 2020, 26,5% năm 2021, 25% từ năm 2022 trở đi. Các định danh điều luật (`cid`) ổn định, nhưng các cặp (`article id`, `version id`) thì thay đổi. Một bộ truy xuất chỉ đánh chỉ mục một ảnh chụp của kho văn bản sẽ làm sụp đổ cấu trúc mịn này thành một điểm duy nhất trong không gian truy xuất.

**(P2) Tính đúng đắn phụ thuộc ngày.** Mỗi phiên bản mang các trường `date_debut`/`date_fin` tường minh, nên một câu hỏi neo vào năm 2018 có đúng một phiên bản đúng, khác với 2020 hay 2024. Không như các kho bách khoa, tính đúng đắn pháp lý là nhị phân và có điều kiện theo ngày: một phiên bản "liên quan" hay "gần đúng" đơn giản là sai.

**(P3) Tương đồng ngữ nghĩa xuyên phiên bản.** Các phiên bản liên tiếp của một điều luật gần như giống hệt nhau về văn bản, thường chỉ khác nhau một mức thuế suất hoặc một ngưỡng. Các embedding dense của chúng là các láng giềng gần nhất của nhau dưới bất kỳ bộ mã hóa câu tiêu chuẩn nào, khiến gần như không thể phân biệt chỉ bằng độ tương đồng.

### 3.2. Phân loại các chế độ thất bại temporal misgrounding

Sự tương tác giữa (P1)–(P3) với các kiến trúc RAG hiện tại tạo ra bốn chế độ thất bại:

- **Thay thế bằng luật hiện hành (current-law substitution):** bộ truy xuất trả về phiên bản đang có hiệu lực bất kể ngày của truy vấn; đây là chế độ chi phối, xuất phát từ chỉ mục chỉ-hiện-hành hoặc từ việc gán trọng số theo độ mới.
- **Rò rỉ luật tương lai (future-law leakage):** một phiên bản `VIGUEUR_DIFF` chưa có hiệu lực được trả về cho một câu hỏi ở thì hiện tại.
- **Giải quyết sai lần sửa đổi (wrong-amendment resolution):** một truy vấn về một điều luật "ở phiên bản trước luật X" trả về phiên bản hiện hành hoặc một phiên bản lịch sử tùy ý; thường gặp trong án lệ, nơi tòa án áp dụng một phiên bản đã lỗi thời cho các sự việc phát sinh dưới nó.
- **Nhầm lẫn đa phiên bản (multi-version confusion):** một phép so sánh trước/sau cải cách bị sụp đổ về một phiên bản có điểm cao nhất duy nhất.

Chúng tôi quan sát thấy chế độ đầu tiên một cách nhất quán ở các LLM hàng đầu; ba chế độ còn lại đòi hỏi các loại câu hỏi nằm ngoài tập R3 đơn mốc (single-anchor) của chúng tôi (§9).

### 3.3. Vì sao các LLM lớn hơn hay mới hơn không giải quyết được vấn đề này

Người ta có thể kỳ vọng các LLM mới hơn, được huấn luyện trên kho văn bản pháp lý lớn hơn, sẽ giải quyết temporal misgrounding bằng tri thức tham số. Ba quan sát cho thấy điều ngược lại. (i) Thiên lệch tính mới là mang tính cấu trúc: dữ liệu huấn luyện nghiêng về nội dung mới xuất bản, được trích dẫn rộng rãi, đại diện quá mức cho luật hiện hành. (ii) Khối lượng lịch sử là rất lớn (hơn 30 nghìn phiên bản chỉ riêng CGI và LPF), và việc ghi nhớ chúng không giải quyết vấn đề phân biệt (P3). (iii) Các câu hỏi có neo căn cứ thời gian thì dễ nhận ra nhưng khó trả lời nếu không có kho văn bản được đánh chỉ mục phiên bản, như bộ lọc tri thức tham số của chúng tôi cho thấy bằng thực nghiệm (§5; Opsahl-Ong và cs., 2026). Do đó, neo căn cứ thời gian đòi hỏi những thay đổi cấu trúc đối với truy xuất (đánh chỉ mục phiên bản, điều kiện hóa theo ngày), chứ không phải các mô hình lớn hơn. Chúng tôi hình thức hóa các giả thuyết tương ứng ở §6, mỗi giả thuyết là một điều kiện truy xuất mà chúng tôi đánh giá.

---

## 4. Xây dựng kho văn bản

Chúng tôi xây dựng kho văn bản FiscalQA Pro qua hai giai đoạn: (i) trích xuất luật thuế có phiên bản theo thời gian, và (ii) liên kết có nhận biết phiên bản các phán quyết của tòa án liên quan đến thuế với các phiên bản điều luật liên quan. Toàn bộ việc trích xuất có thể tái lập đầy đủ từ các nguồn công khai thông qua các script được công bố cùng bài báo này.

### 4.1. Luật thuế có phiên bản theo thời gian

**Nguồn.** CGI (*Code général des impôts*), bốn phụ lục của nó, và LPF (*Livre des procédures fiscales*) được trích xuất từ API PISTE Légifrance chính thức (DILA): endpoint `/consult/getArticleByCid` trả về toàn bộ lịch sử phiên bản của một điều luật (so với chỉ phiên bản hiện hành từ `/consult/getArticle`), mỗi phiên bản mang một định danh riêng (`LEGIARTI...`) dưới một `cid` ổn định.

**Pipeline.** Với mỗi `LEGITEXT` của bộ luật, chúng tôi liệt kê các định danh hằng số qua endpoint mục lục, sau đó gọi `getArticleByCid` một lần cho mỗi `cid` và upsert mọi phiên bản trả về cùng `date_debut`, `date_fin`, `etat` (đang có hiệu lực, đã sửa đổi, đã bãi bỏ, có hiệu lực trong tương lai) và toàn văn. Pipeline có tính lũy đẳng (idempotent) và có thể tái lập đầy đủ từ các nguồn công khai.

**Đầu ra.** Kho văn bản cuối cùng gồm 32.436 phiên bản điều luật thuộc sáu bộ luật thuế (phân tích theo từng bộ luật ở Phụ lục A, Bảng 2). Riêng kho CGI chứa 21.040 phiên bản trên 3.696 điều luật khác nhau, trung bình 5,69 phiên bản lịch sử mỗi điều (cao nhất: 94 phiên bản cho điều 81, về thu nhập được miễn thuế). Khoảng thời gian trải từ 1938 (LPF) đến 2031 (các điều CGI mà việc có hiệu lực đã bị các đạo luật tài chính gần đây hoãn lại), tổng cộng 93 năm.

### 4.2. Liên kết án lệ có nhận biết phiên bản

Như một tài nguyên thứ cấp, chúng tôi liên kết các phán quyết của tòa án liên quan đến thuế với phiên bản điều luật cụ thể có hiệu lực tại ngày phán quyết: một bộ trích xuất dùng regex (veto theo lân cận + bộ lọc ngữ cảnh thuế) giải quyết từng trích dẫn dựa trên chỉ mục điều luật và giao nó với các khoảng `date_debut`/`date_fin`. Việc này cho ra 69.208 liên kết có nhận biết phiên bản trên 32.034 phán quyết, với độ chính xác ở mức liên kết 98–99% (kiểm toán phân tầng) và recall ở mức phán quyết 83–93% trên các nguồn thuộc cơ quan tài phán. Phụ trợ cho thí nghiệm có kiểm soát, nó đóng vai trò giám sát yếu cho các track R1/R4; việc xây dựng và kiểm toán đầy đủ nằm ở Phụ lục B.

---

## 5. Thiết kế benchmark

FiscalQA Pro định nghĩa bốn chế độ câu hỏi (R1–R4) lấy cảm hứng từ khung đa tác vụ của KARLBench. Benchmark và thí nghiệm có kiểm soát của bài báo này tập trung vào track suy luận thời gian **R3**: 209 câu hỏi được chấm điểm, do chuyên gia rà soát, khó đối với mọi mô hình, thuộc 33 điều CGI (221 câu hỏi đã biên soạn được công bố; mười hai câu bị đánh dấu nằm ngoài phạm vi có thể trả lời và bị loại khỏi chấm điểm: bốn câu mà giá trị áp dụng theo ngày là một con số được INSEE chỉ số hóa hằng năm và công bố bằng văn bản hành chính, bị loại một cách thận trọng ngay khi biên soạn, và tám câu bị loại trong đợt rà soát toàn bộ tập vì là lỗi biên soạn hoặc đặt câu hỏi không chuẩn theo mốc ngày của chúng), mỗi câu đi kèm các nugget sự thật chuẩn nguyên tử cho phép chấm điểm tất định mà không cần LLM-as-judge. Các chế độ R2 (43 câu) và R4 (209 câu) được công bố như các track đánh giá bổ sung.

### 5.1. Các chế độ câu hỏi

**R1 – Trích xuất trích dẫn.** Cho một phán quyết của tòa án và một câu hỏi pháp lý, xác định (các) điều CGI/LPF làm căn cứ cho lập luận của tòa; chấm bằng khớp chính xác với `cid` được trích dẫn (ví dụ: một phán quyết của Conseil d'État năm 2023 → `LEGIARTI000006303451`, điều 209 B CGI).

**R2 – Tính toán tất định.** Áp dụng một thuế suất hoặc quy tắc cho một tình huống số, chấm bằng khớp chính xác (có dung sai): ví dụ, thuế thu nhập doanh nghiệp trên khoản lợi nhuận 1,2 triệu € của năm tài chính 2024 theo chế độ tiêu chuẩn → 300.000 € (1,2 triệu × 25%).

**R3 – Suy luận thời gian (đóng góp chính).** Các câu hỏi mà đáp án đúng phụ thuộc vào phiên bản của luật áp dụng tại một ngày cụ thể. Đánh giá: hai nugget bắt buộc xác định điều luật và giá trị số chính xác tại ngày đó, được bổ sung bằng một phép kiểm tra nguồn gốc (provenance) phía truy xuất (§5.2). Đây là chế độ mà thí nghiệm có kiểm soát của chúng tôi nhắm đến (Mục 6).

&gt; "Thuế suất thuế thu nhập doanh nghiệp tiêu chuẩn áp dụng cho các năm tài chính bắt đầu từ ngày 1 tháng 1 năm 2018 trở đi, theo chế độ chung (không gồm doanh nghiệp vừa và nhỏ) là bao nhiêu?"
&gt;
&gt; Nugget kỳ vọng: điều 219 CGI (regex `\b219\b`) và 33,333% (số có dung sai); phiên bản áp dụng được xác thực dựa trên provenance truy xuất.

Chúng tôi dùng điều 219 ở đây, và trong nghiên cứu tình huống ở Phụ lục C, cho rõ ràng; tập được chấm điểm chủ ý nhắm đến các điều ít bị ghi nhớ hơn (Bảng 3, và bộ lọc tham số bên dưới).

**R4 – Tổng hợp đa tài liệu.** Kết hợp CGI, BOFiP (học thuyết hành chính) và án lệ để trả lời một câu hỏi phức tạp, chấm bằng nugget (3–7 nugget mỗi câu bao gồm điều luật, thuế suất, tham chiếu học thuyết và một phán quyết làm căn cứ).

### 5.2. Chấm điểm dựa trên nugget

Theo Databricks AI Research (2026), chúng tôi chấm một phản hồi r bằng tỷ lệ nugget chuẩn mà nó bao phủ, score(r, N) = (1/|N|) Σᵢ 1[nᵢ ∈ r], trong đó một nugget là một khẳng định nguyên tử, có thể kiểm tra tất định (định danh điều luật, giá trị số) và 1[·] là một khớp regex (định danh), khớp số có dung sai (giá trị, sau khi chuẩn hóa số học: dấu phân cách hàng nghìn kiểu Pháp, dấu thập phân là dấu phẩy), hoặc khớp chuỗi chính xác, không bao giờ là một phán đoán của LLM. Chúng tôi báo cáo thêm điểm **strict** (cả hai nugget bắt buộc đều đúng: điều luật đúng và giá trị đúng) và điểm **provenance** cho các điều kiện có truy xuất: phiên bản chuẩn áp dụng theo ngày nằm trong số các phiên bản được truy xuất (điều luật duy nhất đối với B và C_or, top-5 đối với C_prod).

**Rò rỉ nugget điều luật.** Nugget điều luật phần lớn đã bị chính văn bản câu hỏi tiết lộ: regex của nó khớp ngay trên prompt ở 175 trên 209 câu được chấm (83,7%), nên việc trích dẫn điều luật thường không phải bằng chứng của việc truy xuất, và điểm coverage bị chi phối bởi nugget giá trị. Do đó, chúng tôi báo cáo thêm độ phủ chỉ-giá-trị (chỉ nugget giá trị), theo sát độ chính xác strict trong phạm vi 1 điểm khi gộp (A 3,0%, B 2,7%, C_or 99,2%, C_prod 98,5%; bảng theo từng mô hình trong `stats_clustered_report.md` của repository); hiệu ứng chính hoàn toàn do giá trị neo theo ngày mang lại. Về phía truy xuất, cùng sự thật đó có nghĩa là C_prod nhận được số hiệu điều luật trong 83,7% truy vấn: các số liệu recall điều luật ở §7.2 có điều kiện trên việc thông tin đó hiện diện, như trong thực tế với truy vấn của một luật sư.

**Vì sao dùng nugget, không dùng LLM-as-judge?** Neo căn cứ thời gian chính là trục mà các LLM hàng đầu có chung một thiên lệch hệ thống (§3.3), nên một giám khảo LLM thừa hưởng chính chế độ thất bại mà nó được yêu cầu chấm: nó có thể chấp nhận một câu trả lời trôi chảy trích giá trị sai ngày vì giá trị đó khớp với tiên nghiệm tham số của chính nó. Các nugget tất định tránh được vòng luẩn quẩn này, với cái giá là tính biểu đạt hẹp hơn (một nugget là nguyên tử, không phải dạng tự do). Chúng tôi giữ tính biểu đạt bằng cách cố định các thành phần định tính (chọn điều luật, cô lập giá trị phân biệt, chọn dung sai) tại thời điểm chú thích, được xác minh với nguồn sơ cấp (văn bản điều luật có phiên bản); tại thời điểm chấm điểm, phép kiểm tra là một regex hoặc một phép so sánh số bằng nhau. Do đó, bất đồng có thể được giải quyết bằng cách đọc lại kho văn bản thay vì nhắc lại một giám khảo.

### 5.3. Bộ lọc tri thức tham số

Theo Opsahl-Ong và cs. (2026), chúng tôi xác thực rằng benchmark đòi hỏi neo căn cứ (không phải tri thức tham số) thông qua một đường cơ sở không-tri-thức: mỗi câu hỏi ứng viên được đưa cho mọi LLM được đánh giá mà không có kho văn bản hay truy cập web, và bất kỳ câu hỏi nào mà giá trị chuẩn được ít nhất một mô hình nêu ra trong ít nhất một trong bốn lần lấy mẫu sẽ bị loại. Chúng tôi siết chặt tiêu chí "hợp trên các mô hình hàng đầu" của Opsahl-Ong và cs. thành hợp trên cả mười một mô hình được đánh giá, tức là năm hệ thống hàng đầu, mục Gemini thay thế và năm hệ thống open-weight dùng trong C_prod (§6), nhờ đó tập được giữ lại là khó đối với *mọi mô hình* chứ không chỉ khó đối với mọi mô hình hàng đầu.²

**Bộ lọc phân kỳ với phiên bản hiện hành.** Một bộ lọc thứ hai, không dùng LLM, thực thi tiền đề của Điều kiện B (§6): một phép kiểm tra regex xem giá trị neo theo ngày chuẩn có còn xuất hiện nguyên văn trong phiên bản đang có hiệu lực hiện nay của điều luật hay không, và các ứng viên có giá trị không đổi bị loại. Trên tập chấm điểm cuối cùng, văn bản hiện hành không chứa giá trị chuẩn ở 208 trên 209 câu hỏi (ngoại lệ duy nhất được giữ lại như một đối chứng về tính đúng dạng ngay trong tập, §7.2); khi một điều luật không có phiên bản đang có hiệu lực, sự phân kỳ đúng một cách hiển nhiên và Điều kiện B không truy xuất được gì. Chúng tôi nêu rõ hệ quả: **Điều kiện B thất bại một phần là do cách xây dựng**: các câu hỏi được giữ lại đã được sàng lọc để văn bản phiên bản hiện hành không chứa giá trị chuẩn. Nội dung có thể bị bác bỏ của giả thuyết tương ứng do đó là các thành phần provenance và trần của nó, chứ không phải bản thân điểm strict thấp (xem H2 được phát biểu lại, §6).

### 5.4. Biên soạn câu hỏi

Chúng tôi nêu rõ các thành phần thủ công và tự động của benchmark, một mối quan tâm thường gặp với các bài báo benchmark.

**Câu hỏi: ứng viên do kho văn bản gợi ra, câu hỏi do tác giả viết.** Các câu hỏi được tạo ra bởi một pipeline hai giai đoạn, cả hai giai đoạn đều được công bố trong repository. Thứ nhất, các điểm trôi dạt ứng viên được tự động nêu ra từ kho văn bản có phiên bản: `r3_factory.py` quét lịch sử phiên bản để tìm các chuyển đổi giá trị (một ngưỡng hay thuế suất thay đổi giữa các phiên bản liên tiếp) và `r3_worksheet.py` xuất chúng thành một bảng làm việc (điều luật, ngày chuyển đổi, giá trị trước/sau). Thứ hai, mọi câu hỏi, mốc ngày, đáp án chuẩn và nugget đều do các tác giả viết, họ soạn văn bản câu hỏi, xác minh giá trị với phiên bản trong kho văn bản và đặt dung sai; toàn bộ tập sau đó được một chuyên gia thuế Pháp có chuyên môn rà soát về tính đúng đắn. Một tập con có nguồn gốc từ một kho nội bộ (Fiscal-FR-Bench v1) do các tác giả tập hợp trước đó.³

**Tiêu chí chọn lọc.** 209 câu hỏi được chấm điểm (sau bộ lọc tham số khó-đối-với-mọi-mô-hình và đợt kiểm toán phạm vi có thể trả lời) bao phủ 33 điều CGI thuộc bảy tiểu lĩnh vực thuế (Bảng 3): thuế thu nhập cá nhân (IR), thuế kinh doanh địa phương và thuế nhà ở (IFER, CFE, TH, TSE), cá cược và trò chơi, thuế gián thu (VAT, thuốc lá, TV, khai khoáng), BIC/nông nghiệp và xuyên biên giới, thuế tiền lương, và thuế tài sản (ISF). Mỗi câu tham chiếu một điều luật có nội dung thay đổi đáng kể trong giai đoạn 1989–2025 (trôi dạt theo luật định). Nhất quán với bộ lọc, chúng tôi nhắm đến các tham số ít người biết, không tròn số (các khoản trợ cấp được chỉ số hóa, ngưỡng, biểu phí IFER theo từng cơ sở) thay vì các mức thuế suất tiêu đề nổi tiếng (ví dụ: thuế suất doanh nghiệp của điều 219 hay biểu thuế thu nhập của điều 197) mà các LLM hàng đầu ghi nhớ chắc chắn.

**Tập đánh giá bị đóng băng.** Tập 209 câu được chấm điểm được đóng băng trước mọi hoạt động phát triển bộ truy xuất hay reranker (`killer_qids_v2.txt`); cuộc kiểm toán phạm vi có thể trả lời đánh dấu mười hai câu hỏi đã công bố là ngoài phạm vi theo một tiêu chí độc lập với mô hình, gồm bốn câu (điều 199 undecies A, có mức trần trên mỗi mét vuông được điều chỉnh lại hằng năm bằng chỉ số hóa INSEE theo luật định và công bố qua BOFiP; bị loại thận trọng khi biên soạn) cộng tám câu phát hiện trong rà soát toàn tập (lỗi biên soạn hoặc các mục đặt không chuẩn theo mốc ngày của chúng; được liệt kê trong `excluded_qids_scope.txt` của repository), để lại k=209 câu được chấm trên 221 câu đã công bố. Reranker thuế mà chúng tôi đánh giá bổ sung chỉ được fit trên các điều luật không giao với các điều của tập này; nó không mang lại cải thiện top-1 và không thuộc pipeline C_prod được báo cáo.

**Nugget và đáp án: hoàn toàn thủ công.** Mỗi câu hỏi được ghép với hai nugget bắt buộc nguyên tử, do các tác giả chú thích thủ công: một regex trên số hiệu điều luật áp dụng và một phép khớp số có dung sai trên giá trị chính xác áp dụng theo ngày. Vì nugget giá trị là con số chính xác áp dụng theo ngày (số có dung sai), độ chính xác strict đã đòi hỏi giá trị đúng ngày, không chỉ một điều luật hợp lý; chất lượng chọn phiên bản được theo dõi riêng bằng điểm provenance phía truy xuất (§5.2), nên hai thước đo được tách rời và cái này không làm phồng cái kia. Đáp án chuẩn được đối chiếu nguyên văn với phiên bản mà các nugget trỏ tới (cả 221 câu đã biên soạn được xác minh với kho văn bản) và được một chuyên gia thuế Pháp có chuyên môn rà soát tính đúng đắn. Các liên kết án lệ (§4.2) chỉ đóng vai trò giám sát yếu cho R1/R4, không bao giờ là đáp án chuẩn cho R3.

**Bộ lọc tham số, trong thực tế.** Tại thời điểm tuyển chọn, không mô hình nào được đánh giá khôi phục được đáp án áp dụng theo ngày trong bất kỳ lần nào trong bốn lần lấy mẫu; đây là nghĩa mà tập được gọi là khó đối với mọi mô hình. Tại thời điểm đánh giá, độ chính xác strict trung bình của Điều kiện A là 3,0% trên mười một mô hình (khoảng tin cậy 95% bootstrap theo cụm [1,4; 4,7]; giá trị từng mô hình ở Bảng 1). Phương sai còn lại đến từ nhiệt độ lấy mẫu mặc định của các mô hình hàng đầu Anthropic (các lần lấy mẫu thực sự đa dạng), tính không tất định của stack suy luận GPT-5.x ngay cả ở nhiệt độ 0, và các mục còn lại thực chất chỉ có một lần lấy mẫu tất định ở nhiệt độ 0, khiến bộ lọc thận trọng chứ không dễ dãi (một đáp án được ghi nhớ sẽ xuất hiện giống hệt ở cả bốn lần lấy mẫu và bị bắt).

**Rò rỉ còn lại.** Độ khó tại thời điểm tuyển chọn không đóng băng hành vi tại thời điểm đánh giá: trên mười một mô hình, ít nhất một mô hình đã đưa ra giá trị chuẩn trong Điều kiện A cho 37 trên 209 câu hỏi (17,7%; số lượng theo từng mô hình từ 0–25, cao nhất ở GPT-5.5 (25) và Opus 4.7 (16), phản ánh trong điểm strict Cond A cao hơn của chúng ở Bảng 1): đó là trôi dạt do lấy mẫu và tái dựng giá trị, không phải ghi nhớ (một giá trị được ghi nhớ giống hệt trên cả bốn lần lấy mẫu sẽ đã bị bắt khi tuyển chọn). Do đó tập là khó đối với mọi mô hình *dưới các cấu hình đánh giá của các mô hình*, và phép so sánh B→C không bị ảnh hưởng, vì mọi điều kiện dùng chung cấu hình. Số lượng theo từng mô hình: `stats_clustered_report.md` (§4).

**Vì sao 209 câu hỏi?** Track R3 ban đầu chủ ý nhỏ (k=35; so với 162 tác vụ của LegalBench, Guha và cs., 2023), được thiết kế để cô lập hiện tượng temporal misgrounding với chi phí chú thích tối thiểu. Để đáp lại phản hồi của người phản biện về quy mô và để có chỗ cho mười một mô hình (hàng đầu + open-weight), chúng tôi mở rộng track lên 221 câu hỏi đã biên soạn theo cùng giao thức chú thích (209 câu trong phạm vi chấm điểm sau kiểm toán phạm vi có thể trả lời), trải trên 33 điều thay vì 10. Mỗi câu hỏi bổ sung tuân theo cùng giao thức biên soạn (chọn lọc, xác định phiên bản, đáp án chuẩn, hai nugget, đối chiếu với kho văn bản) và vượt qua bộ lọc khó-đối-với-mọi-mô-hình đã siết chặt. Giờ đây chúng tôi đọc Bảng 1 ở cả mức khoảng cách giữa các điều kiện (A/B ≪ C, không đổi so với bài nộp ban đầu) lẫn mức xếp hạng mô hình (hàng đầu so với open-weight), mà k lớn hơn giúp có đủ lực thống kê (§7.2).

Phân bố theo từng điều và từng tiểu lĩnh vực của tập được chấm điểm được cho ở Bảng 3 (Phụ lục A).

² Về việc thay thế Qwen giữa tuyển chọn và đánh giá, xem ghi chú ‡ của Bảng 1.
³ Fiscal-FR-Bench v1 là một benchmark độc quyền do các tác giả nắm giữ. Chúng tôi công bố track R3 (221 câu hỏi, 209 trong phạm vi chấm điểm), cùng các track R2 (43) và R4 (209), dưới tên Fiscal-FR-Bench v0 cùng với bài báo này.

---

## 6. Thí nghiệm

Chúng tôi chạy một thí nghiệm có kiểm soát gồm ba điều kiện, đo khoảng cách độ chính xác giữa các tiếp cận LLM/RAG tiêu chuẩn và truy xuất có phiên bản theo thời gian của chúng tôi trên các câu hỏi R3.

### 6.1. Thí nghiệm có kiểm soát: Trôi dạt theo thời gian

**Thiết kế.** Chúng tôi đánh giá ba điều kiện truy xuất trên tập con R3 khó-đối-với-mọi-mô-hình đã đóng băng (k=209 được chấm điểm; Bảng 3), với mười một mô hình trả lời: năm hệ thống API đóng hàng đầu (Claude Opus 4.7, Claude Opus 4.8, Claude Sonnet 4.6, GPT-5.4, GPT-5.5), cộng Gemini 2.5 Pro như một mục hàng đầu thay thế (Gemini 3 Pro Preview bị giới hạn tốc độ trong thời gian đánh giá; ghi chú † của Bảng 1), và năm hệ thống open-weight: Mistral Large 2407, Llama 4 Maverick, Qwen 3 235B, Gemma 3 27B và GLM 5.2. Tập hàng đầu gồm hai thế hệ Opus và hai thế hệ GPT-5 để kiểm tra liệu những cải thiện giữa các thế hệ trong cùng một dòng có thu hẹp khoảng cách temporal misgrounding bằng tri thức tham số hay không (không; §7). Năm hệ thống open-weight, chạy qua các endpoint suy luận công khai (OpenRouter và Together AI), cho phép chúng tôi kiểm tra xem neo căn cứ thời gian có phụ thuộc vào quy mô mô hình hay nhà cung cấp hay không (không).

1. **Điều kiện A: chỉ LLM.** Mô hình trả lời chỉ bằng tri thức tham số: không truy xuất, không web. Một lần lấy mẫu đánh giá cho mỗi câu hỏi; việc dò bốn lần lấy mẫu áp dụng cho bộ lọc tham số tại thời điểm tuyển chọn (§5; cấu hình lấy mẫu trong chú thích Bảng 1).
2. **Điều kiện B: RAG trên kho văn bản hiện hành.** Mô hình truy xuất trên kho CGI tĩnh chỉ có phiên bản hiện hành (đại diện cho phần lớn các hệ thống RAG pháp lý đang được triển khai hiện nay). Việc truy xuất điều luật dùng `cid` chuẩn; chỉ phiên bản đang có hiệu lực được cung cấp. Vì B được đưa sẵn `cid` chuẩn, nó có lợi cho đường cơ sở tĩnh, nên khoảng cách A/B ≪ C được báo cáo là một cận dưới.
3. **Điều kiện C: RAG trên kho văn bản có phiên bản của chúng tôi.** Mô hình truy xuất trên kho văn bản có phiên bản theo thời gian của chúng tôi, nơi lớp phiên bản trả về phiên bản điều luật áp dụng tại ngày trong câu hỏi. Chúng tôi đánh giá hai bộ truy xuất dùng chung lớp phiên bản này:
   - **C_or (oracle):** truy xuất điều luật dùng `cid` chuẩn, cô lập đóng góp của việc chọn phiên bản (trần một khi đã tìm đúng điều luật).
   - **C_prod (end-to-end):** một bộ truy xuất end-to-end tìm cả điều luật lẫn phiên bản, không oracle: bối cảnh triển khai thực tế. Kênh dense là một bộ mã hóa dense thích nghi miền trên một chỉ mục điều luật đa phiên bản đã chia chunk (ba phiên bản mỗi `cid`: đầu, trung vị, cuối theo `date_debut`, loại trừ các artefact `MODIFIE_MORT_NE`); kênh thưa là BM25 trên cùng các chunk; hai kênh được hợp nhất bằng reciprocal-rank fusion (không có cross-encoder rerank trong C_prod). Top-5 điều luật duy nhất được chuyển cho lớp phiên bản, lớp này xác định phiên bản áp dụng theo ngày cho mỗi `cid` trước khi nhắc LLM.

**Thước đo.** Các thước đo theo từng câu hỏi (coverage, strict, provenance) như định nghĩa ở §5.2; điểm theo từng điều kiện là trung bình trên k=209 câu hỏi được chấm, theo từng mô hình hoặc gộp trên mười một mô hình.

**Giả thuyết.** Chúng tôi kiểm định bốn dự đoán có thể bị bác bỏ, mỗi dự đoán gắn với một điều kiện:

- **(H1)** A thấp về độ chính xác strict (gần như không có tri thức tham số về các giá trị đặc thù theo ngày), đồng đều trên các quy mô và nhà cung cấp, dù coverage vẫn đáng kể vì nugget định danh điều luật dễ;
- **(H2)** B truy xuất phiên bản áp dụng theo ngày trong 0% trường hợp và giữ dưới 10% strict. Điểm strict gần bằng không phần lớn là một phép kiểm tra cấu trúc, vì bộ lọc phân kỳ với phiên bản hiện hành (§5) sàng lọc các câu được giữ lại để văn bản hiện hành không chứa giá trị chuẩn; nội dung có thể bị bác bỏ của H2 là provenance 0% (mang tính cấu trúc: chỉ mục một phiên bản không thể chứa phiên bản) và trần &lt;10%, mà một mô hình về nguyên tắc có thể vượt qua bằng cách tái suy ra giá trị lịch sử từ văn bản hiện hành (ví dụ: gỡ chỉ số hóa một ngưỡng đã được điều chỉnh);
- **(H3)** C_or thu hẹp phần lớn khoảng cách (&gt;80% strict, 100% provenance), cho thấy chọn phiên bản (không phải độ đầy đủ của kho văn bản hay quy mô mô hình) là nút thắt;
- **(H4)** một bộ truy xuất thực tế đưa vào top-5 các phiên bản áp dụng theo ngày khôi phục về cơ bản trần C_or, khoảng cách còn lại là một trần recall@5 trên một vài truy vấn ngách, nên đòn bẩy là recall chứ không phải rerank top-1.

---

## 7. Kết quả

### 7.1. Chất lượng kho văn bản

**Độ sâu phiên bản.** Bảng 2 báo cáo phân bố số phiên bản điều luật theo từng bộ luật: trung bình 4,02 phiên bản mỗi `cid`, với điều 81 chính của CGI (thu nhập được miễn thuế), được các đạo luật tài chính sửa đổi lặp đi lặp lại, nắm giữ 94 phiên bản lịch sử riêng biệt. Độ sâu này, chính là cấu trúc mà một chỉ mục tĩnh làm sụp đổ (§3.1), là điều mà thí nghiệm có kiểm soát khai thác. Chất lượng của bộ dữ liệu phụ liên kết án lệ (độ chính xác, recall, kiểm toán tiêu chuẩn vàng) được báo cáo ở Phụ lục B.

### 7.2. Kết quả thí nghiệm có kiểm soát

Trên tập con k=209 khó-đối-với-mọi-mô-hình, tri thức tham số (A) thấp đồng đều trên cả mười một mô hình (strict trung bình 3,0%, khoảng tin cậy 95% bootstrap theo cụm [1,4; 4,7]; Bảng 1), do cách xây dựng bộ lọc, được siết chặt từ "không mô hình hàng đầu nào khôi phục được" (Opsahl-Ong và cs., 2026) thành "không mô hình được đánh giá nào khôi phục được trên bốn lần lấy mẫu tại thời điểm tuyển chọn", loại trừ mọi câu hỏi mà một mô hình tình cờ đã ghi nhớ (trôi dạt còn lại tại thời điểm đánh giá được định lượng ở §5). RAG kho tĩnh (B), bối cảnh được hầu hết các sản phẩm AI pháp lý triển khai hiện nay, không cải thiện so với đường cơ sở chỉ-LLM (strict trung bình 2,7%, khoảng tin cậy 95% bootstrap theo cụm [1,3; 4,8], không khác biệt có ý nghĩa thống kê so với A) và truy xuất phiên bản áp dụng theo ngày trong 0% trường hợp: nó thất bại không âm thầm mà tự tin, neo vào một phiên bản có thật, đúng dạng, nhưng không áp dụng (cả hai là các phép kiểm tra cấu trúc chứ không phải các phép đo gây ngạc nhiên; §5 và H2, §6).

**Bảng 1.** Kết quả trên tập con R3 khó-đối-với-mọi-mô-hình được chấm điểm k=209. Tất cả số liệu tính bằng phần trăm.

| Mô hình | Cov. A | Cov. B | Cov. C_or | Cov. C_prod | Strict A | Strict B | Strict C_or | Strict C_prod | Prov. B | Prov. C_or | Prov. C_prod |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Hàng đầu (API đóng)** | | | | | | | | | | | |
| Opus 4.7 | 53,8 | 55,3 | 100,0 | 99,8 | 7,7 | 10,5 | 100,0 | 99,5 | 0 | 100 | 99 |
| Opus 4.8 | 53,3 | 51,4 | 100,0 | 99,5 | 6,7 | 3,3 | 100,0 | 99,0 | 0 | 100 | 99 |
| Sonnet 4.6 | 49,5 | 50,0 | 100,0 | 99,5 | 1,0 | 1,4 | 100,0 | 99,0 | 0 | 100 | 99 |
| GPT-5.4 | 50,7 | 51,2 | 100,0 | 99,5 | 1,4 | 2,4 | 100,0 | 99,0 | 0 | 100 | 99 |
| GPT-5.5 | 56,0 | 54,1 | 100,0 | 99,8 | 12,0 | 8,1 | 100,0 | 99,5 | 0 | 100 | 99 |
| Gemini 2.5 Pro† | 46,2 | 49,5 | 99,0 | 99,0 | 1,4 | 0,5 | 99,0 | 98,6 | 0 | 100 | 99 |
| **Open-weight** | | | | | | | | | | | |
| Mistral Large 2407 | 50,2 | 50,7 | 99,8 | 99,0 | 0,5 | 1,4 | 99,5 | 98,1 | 0 | 100 | 99 |
| Llama 4 Maverick | 48,1 | 50,2 | 99,0 | 98,6 | 0,0 | 0,5 | 98,1 | 97,1 | 0 | 100 | 99 |
| Qwen 3 235B‡ | 46,7 | 49,3 | 97,4 | 98,6 | 1,0 | 0,5 | 94,7 | 97,1 | 0 | 100 | 99 |
| Gemma 3 27B | 42,8 | 48,6 | 99,8 | 97,4 | 0,0 | 0,5 | 99,5 | 95,2 | 0 | 100 | 99 |
| GLM 5.2 | 49,0 | 50,2 | 99,8 | 99,5 | 1,0 | 1,0 | 99,5 | 99,0 | 0 | 100 | 99 |
| **Trung bình (11 mô hình)** | **49,7** | **51,0** | **99,5** | **99,1** | **3,0** | **2,7** | **99,1** | **98,3** | **0** | **100** | **99** |

*Chú thích Bảng 1.* Kết quả trên tập con R3 khó-đối-với-mọi-mô-hình được chấm điểm k=209 (các câu hỏi mà không mô hình nào được đánh giá, hàng đầu hay open-weight, trả lời được từ tri thức tham số trên bốn lần lấy mẫu tại thời điểm tuyển chọn; 221 câu hỏi đã biên soạn được công bố, mười hai câu bị đánh dấu ngoài phạm vi có thể trả lời). **A:** chỉ LLM, một lần lấy mẫu đánh giá cho mỗi câu hỏi (ba mô hình hàng đầu Anthropic dùng nhiệt độ lấy mẫu mặc định; stack suy luận GPT-5.x không tất định ngay cả ở nhiệt độ 0; sáu mục còn lại (năm open-weight và Gemini 2.5 Pro) chạy ở nhiệt độ 0, thực chất là tất định). **B:** RAG trên kho tĩnh phiên bản hiện hành (điều luật chuẩn, phiên bản hiện hành). **C_or:** chọn phiên bản oracle (điều luật chuẩn, phiên bản áp dụng theo ngày): trần một-điều-luật. **C_prod:** bộ truy xuất end-to-end đưa vào top-5 các phiên bản áp dụng theo ngày, không oracle (chi tiết bộ truy xuất ở §6). **Coverage** = tỷ lệ nugget trung bình; **Strict** = cả hai nugget bắt buộc đúng (điều luật đúng và giá trị chính xác); **Provenance** = % câu hỏi mà phiên bản chuẩn áp dụng theo ngày nằm trong top-5 được truy xuất. Mọi điều kiện dùng chung một prompt điều-luật-có-nhãn giống hệt với ngân sách 8.000 ký tự/điều luật theo cửa sổ truy vấn (bảo toàn giá trị: giá trị chuẩn áp dụng theo ngày nằm trong cửa sổ được cung cấp cho cả 209 câu hỏi được chấm), nên C_or và C_prod chỉ khác nhau ở số điều luật được truy xuất. Khoảng tin cậy bootstrap 95% nhận biết cụm (resample theo điều luật) và các kiểm định McNemar/Wilcoxon chính xác theo từng mô hình được báo cáo ở §7.2.

† Gemini 3 Pro Preview bị giới hạn tốc độ trong thời gian đánh giá mở rộng; chúng tôi báo cáo mô hình sẵn có ở bậc kế tiếp của Google (Gemini 2.5 Pro) như một mục hàng đầu thay thế. Các điều kiện A/B/C_or chạy trên endpoint AI Studio gốc; C_prod chạy qua OpenRouter sau khi hạn mức theo ngày của endpoint gốc cạn kiệt. Stack suy luận bắt buộc của nó không thể cấu hình, nên Cond A là một lần lấy mẫu có điều kiện suy luận. Các mục Gemini 2.5 Pro và GLM 5.2 gồm một số ít phản hồi rỗng từ phía nhà cung cấp được chấm là thất bại (tổng cộng 22 trên các điều kiện, theo hướng thận trọng; kiểm toán trong repository, `parametric_filter_empty_audit.md`).

‡ Qwen 2.5 72B (dùng tại thời điểm tuyển chọn cho bộ lọc tham số) bị mọi nhà cung cấp có thể truy cập ngừng cung cấp suy luận serverless trong thời gian đánh giá; chúng tôi thay bằng Qwen 3 235B (Together AI). Một mô hình lớn hơn, mới hơn về nguyên tắc có thể khôi phục thêm câu hỏi bằng tri thức tham số; theo thực nghiệm, strict Cond A của nó là 0,0%, nên phép dò vẫn là khó-đối-với-mọi-mô-hình.

**Điều kiện đối chứng (tính đúng dạng).** Hai đối chứng trên cùng tập loại trừ khả năng câu hỏi đặt không chuẩn hoặc pipeline hỏng là lời giải thích cho thất bại của B. Thứ nhất, dưới cùng prompt điều-luật-có-nhãn và pipeline, chọn phiên bản oracle (C_or, chỉ thay đổi phiên bản được cung cấp của cùng điều luật) đạt strict trung bình 99,1% trên cùng 209 câu hỏi (Bảng 1): các câu hỏi là trả lời được và mô hình trích xuất đúng giá trị khi được đưa phiên bản áp dụng theo ngày, nên điểm gần bằng không của B không phải do đặt câu hỏi không chuẩn hay lỗi đọc. Thứ hai, văn bản phiên bản hiện hành không chứa giá trị neo theo ngày chuẩn ở 208 trên 209 câu hỏi được chấm (tiền đề phân kỳ của Điều kiện B, §5); ở ngoại lệ không trôi dạt duy nhất, với giá trị có mặt trong văn bản hiện hành, B tĩnh truy xuất đúng. Do đó thất bại của B trên tập trôi dạt là do trôi dạt phiên bản, không phải pipeline hỏng.

**Kết quả vận hành: truy xuất end-to-end.** C_prod, bộ truy xuất end-to-end, không có oracle (nó phải xác định cả điều luật lẫn phiên bản áp dụng theo ngày chỉ từ truy vấn) và đạt strict trung bình **98,3%** (khoảng tin cậy 95% bootstrap theo cụm [95,9; 99,6]); cả mười một mô hình đều vượt 95% theo ước lượng điểm (95,2–99,5%; mọi khoảng tin cậy theo cụm của từng mô hình đều trên 89%, §7.2), và phiên bản chuẩn nằm trong top-5 cho 99% câu hỏi (so với 0% cho B). Nắm giữ các phiên bản là cần nhưng chưa đủ: một thí nghiệm ablation với điều luật oracle (C_or, `cid` chuẩn, chỉ để lại việc chọn phiên bản) đạt trung bình 99,1% (CI [98,4; 99,9]) với provenance 100%. Khoảng cách C_or → C_prod chỉ là 0,8 điểm, tập trung ở recall giai đoạn đầu thay vì chọn phiên bản: lần trượt provenance duy nhất là điều 1417 (2 câu hỏi có phiên bản áp dụng theo ngày nằm ngoài top-5 được truy xuất). Một khi kho văn bản đã có phiên bản, nút thắt là recall điều luật, không phải xác định ngày; một cross-encoder reranker không bổ sung gì trên tập ngách này.

**Ý nghĩa thống kê (nhận biết cụm).** Giao thức là ghép cặp, với hai phụ thuộc mà một phân tích iid gộp sẽ bỏ qua: mười một mô hình trả lời cùng các câu hỏi, và các câu hỏi tụ cụm theo điều luật (33 cụm; riêng điều 1466 A có 34). Do đó chúng tôi coi mô hình là đơn vị suy luận và bootstrap bằng cách resample các điều luật, không phải các câu hỏi (10.000 lần lặp, seed 42). Các mức tăng B→C_or và B→C_prod có ý nghĩa thống kê với từng mô hình riêng lẻ (McNemar hai phía chính xác trên kết quả strict theo từng câu hỏi, 11 kiểm định, tất cả p &lt; 10⁻⁵⁵), nên kết luận không phụ thuộc vào việc gộp; các kiểm định Wilcoxon theo từng mô hình trên coverage đồng thuận, trong khi chênh lệch coverage C_or → C_prod là nhỏ và không có ý nghĩa đồng đều, phù hợp với trần recall@5 1%. Các kiểm định đầy đủ theo từng mô hình nằm trong `stats_clustered_report.md` của repository. Khoảng tin cậy 95% bootstrap theo cụm cho strict gộp: A 3,0 [1,4; 4,7], B 2,7 [1,3; 4,8], C_or 99,1 [98,4; 99,9], C_prod 98,3 [95,9; 99,6]; cận dưới C_prod của mọi mô hình đều trên 89% (kết luận đứng vững khi xét theo cụm, không chỉ ở ước lượng điểm). Leave-one-article-out trên strict C_prod gộp trải từ 98,1% (bỏ điều 1519 A) đến 99,2% (bỏ điều 1417): không một điều luật đơn lẻ nào gánh kết quả. Một bản đi qua từng bước một câu hỏi (điều 219 CGI) nằm ở Phụ lục C (Hình 1).

**Chính sách cửa sổ (windowing).** Mọi điều kiện cung cấp một đoạn trích bảo toàn giá trị, theo cửa sổ truy vấn, với ngân sách 8.000 ký tự/điều luật: với mỗi điều luật được truy xuất, chúng tôi giữ phần đầu cộng các đoạn liên quan nhất tới truy vấn, giới hạn 8.000 ký tự. Một phép kiểm tra trước khi chấm điểm xác nhận giá trị chuẩn áp dụng theo ngày nằm trong cửa sổ được cung cấp cho cả 209 câu hỏi được chấm, nên không điều kiện nào được đưa một đoạn trích không thể chứa đáp án, và ngân sách ảnh hưởng đối xứng đến B, C_or và C_prod. Điều này giải quyết artefact cắt đầu (head-truncation) của giới hạn 6.000 ký tự ban đầu, dưới đó giá trị chuẩn của một số ít điều luật dài (ví dụ: các điều 158, 1605 bis, 261, 83) nằm ngoài cửa sổ. Nhắc bằng toàn văn đồng nhất thì không ưu việt hơn: nó làm suy giảm C_or trên các điều luật dài do phân tán trong ngữ cảnh dài (các script ablation trong repository).

**Phân bố chế độ thất bại.** Điều kiện B truy xuất phiên bản hiện hành trong 100% trường hợp (Bảng 1, provenance), nên 100% lỗi của điều kiện B là thay thế bằng luật hiện hành, chế độ chi phối do cách xây dựng của một chỉ mục tĩnh.

---

## 8. Kết luận

Chúng tôi đã nhận diện temporal misgrounding, tức việc truy xuất và trích dẫn một cách có hệ thống phiên bản đang có hiệu lực của một điều luật khi câu hỏi đòi hỏi một phiên bản trước đó hoặc trong tương lai, như một chế độ thất bại mang tính cấu trúc của RAG pháp lý: các định danh ổn định, tính đúng đắn phụ thuộc ngày và tương đồng ngữ nghĩa xuyên phiên bản gặp việc đánh chỉ mục một phiên bản, không điều kiện hóa theo ngày và thiên lệch tính mới của tri thức tham số. Để định lượng nó, chúng tôi xây dựng FiscalQA Pro: một kho văn bản có phiên bản theo thời gian gồm 32.436 phiên bản điều luật CGI/LPF trong 93 năm (cộng 69.208 liên kết án lệ phụ có nhận biết phiên bản) và một track suy luận thời gian R3 gồm 209 câu hỏi được chấm điểm, do chuyên gia rà soát, khó đối với mọi mô hình, thuộc 33 điều CGI (công bố 221 câu), được chấm tất định qua nugget.

Trên mười một mô hình, thí nghiệm có kiểm soát của chúng tôi cho thấy các LLM thất bại trên các câu hỏi có neo căn cứ thời gian dù có hay không có RAG kho tĩnh (strict trung bình gộp 3,0% và 2,7%; RAG tĩnh truy xuất phiên bản áp dụng theo ngày trong 0% trường hợp), trong khi bộ truy xuất end-to-end của chúng tôi, điều kiện hóa truy xuất theo ngày của truy vấn mà không có oracle, đạt strict trung bình 98,3% (cả mười một mô hình đều vượt 95% theo ước lượng điểm), một thí nghiệm ablation điều luật oracle đặt trần ở 99,1% và khoảng cách còn lại 0,8 điểm nằm ở recall giai đoạn đầu chứ không phải chọn phiên bản. Chúng tôi cho rằng QA pháp lý nên được tái định khung như một bài toán truy xuất được đánh chỉ mục theo thời gian, và công bố kho văn bản, benchmark, các phản hồi của mô hình và mã pipeline (trừ trọng số bộ mã hóa đã tinh chỉnh; Phụ lục D).

---

## 9. Hạn chế và hướng phát triển

**Phạm vi và khả năng khái quát hóa sang luật dân sự (civil-law).** FiscalQA Pro chỉ bao phủ luật thuế Pháp (CGI, bốn phụ lục của nó và LPF). Tuy nhiên, chúng tôi cho rằng temporal misgrounding mang tính cấu trúc đối với truy xuất luật thành văn theo hệ thống civil-law chứ không phải một artefact của Pháp: bất kỳ kho văn bản nào được sửa đổi tại chỗ và có phiên bản theo thời gian đều thể hiện cùng sự kết hợp các thuộc tính (§3), và một số khu vực pháp lý cung cấp các API luật thành văn có phiên bản với ngày hiệu lực tường minh tương tự Légifrance (Fedlex, Gesetze-im-Internet, Justel, Legilux; Swiss Federal Chancellery; German Federal Ministry of Justice; Belgian Federal Public Service Justice; Government of Luxembourg). Lớp phương pháp của chúng tôi không phụ thuộc khu vực pháp lý; chỉ lớp dữ liệu thì có. Nghiên cứu Đức đồng thời của Prior và cs. (2026) tìm thấy cùng hiện tượng, là bằng chứng độc lập về khả năng khái quát hóa; một bản sao lặp (replication) trên Fedlex của Thụy Sĩ là bước tiếp theo.

**Quy mô câu hỏi.** Track R3 chứa 221 câu hỏi đã biên soạn (209 trong phạm vi chấm điểm), tăng từ 35 trong bài nộp ban đầu (§5). Tập mở rộng vẫn nhỏ hơn LegalBench (162 tác vụ; Guha và cs., 2023) hay KARLBench (hơn 2.000 câu hỏi): một sự đánh đổi có chủ ý trước việc mở rộng tổng hợp hoặc do LLM tạo, vì độ khó tập trung, do chuyên gia rà soát, khó đối với mọi mô hình là chế độ phù hợp để đo temporal misgrounding (so sánh với 133 câu hỏi của OfficeQA Pro).

**Các chế độ thất bại được đánh giá.** Tập R3 đơn mốc của chúng tôi chỉ thực hiện thay thế bằng luật hiện hành; ba chế độ còn lại của phân loại (§3.2) đòi hỏi các câu hỏi về trạng thái có hiệu lực trong tương lai (`VIGUEUR_DIFF`), "ở phiên bản trước luật X" và so sánh hai phiên bản, mà chúng tôi để lại cho v1; các phiên bản `VIGUEUR_DIFF` của kho văn bản, kéo dài tới 2031, đã cho phép chế độ rò rỉ luật tương lai thông qua các câu hỏi về trạng thái pháp lý tương lai được ấn định bởi luật đã ban hành nhưng bị hoãn. Cuối cùng, vượt ra ngoài "áp dụng luật": R1–R3 nhắm đến áp dụng quy tắc, không phải diễn giải pháp lý; R4 là bước đầu hướng tới các benchmark diễn giải.

---

## Tuyên bố tác động (Impact Statement)

Công trình này nghiên cứu một thất bại về độ tin cậy của AI pháp lý, temporal misgrounding, và cung cấp một benchmark cùng phương pháp luận để đo lường và giảm thiểu nó. Việc cải thiện tính đúng đắn theo thời gian của hỏi đáp pháp lý có thể giảm các đầu ra sai một cách tự tin trong các bối cảnh rủi ro cao (tuân thủ thuế, nghiên cứu pháp lý). Kho văn bản và benchmark được xây dựng hoàn toàn từ luật thành văn và án lệ công khai; không có dữ liệu cá nhân nào được đưa vào. Như với mọi công cụ AI pháp lý, đầu ra cần được một chuyên gia có chuyên môn xác minh và không được coi là tư vấn pháp lý.

---

## Đóng góp của các tác giả

R.C. dẫn dắt nghiên cứu, thiết kế benchmark, xây dựng kiến trúc truy xuất, chạy thí nghiệm có kiểm soát và dẫn dắt việc viết. D.G. xây dựng hạ tầng dữ liệu, việc trích xuất và kho văn bản có phiên bản. L.F. đóng góp vào phương pháp luận đánh giá, thiết kế thí nghiệm, phân tích và diễn giải kết quả, và định vị công trình.

---

## Tài liệu tham khảo

*(Giữ nguyên bản gốc)*

- Barale, C. LexTime: A benchmark for temporal ordering of legal events. In Findings of EMNLP, 2025. https://arxiv.org/abs/2506.04041
- Belgian Federal Public Service Justice. Justel: Consolidated Belgian legislation. https://www.ejustice.just.fgov.be/. Accessed July 2026.
- Chen, W., Wang, X., and Wang, W. Y. TimeQA: A benchmark for time-sensitive question answering. In NeurIPS Datasets and Benchmarks Track, 2021.
- Das, S., Abualhaija, S., and Bianculli, D. Fine-grained claim-level RAG benchmark for law. arXiv:2605.21071, 2026.
- Databricks AI Research. KARL: Knowledge agents via reinforcement learning. arXiv:2603.05218, 2026. https://arxiv.org/abs/2603.05218
- de Martim, H. An ontology-driven graph RAG for legal norms: A structural, temporal, and deterministic approach. In JURIX 2025, Frontiers in AI and Applications, pp. 282–287. IOS Press, 2025. doi: 10.3233/FAIA251598.
- Dhingra, B., Cole, J. R., Eisenschlos, J. M., Gillick, D., Eisenstein, J., and Cohen, W. W. TempLAMA: Time-aware language models as temporal knowledge bases. TACL, 2022.
- Douka, S., Abdine, H., Vazirgiannis, M., El Hamdani, R., and Restrepo Amariles, D. JuriBERT: A masked-language model adaptation for French legal text. In Proceedings of the Natural Legal Language Processing Workshop, 2021.
- Fan, W., Zhou, Y., Zhang, M., Weng, Y., Hu, Y., Zheng, T., Xu, B., Li, C., Yang, J., Li, H., and Song, Y. Can LLMs time travel? Enhancing temporal consistency in legal agentic search through reinforcement learning. arXiv:2605.25920, 2026a.
- Fan, Y., Ni, J., Huang, Y., Tian, Y., Stammbach, D., Ash, E., Engel, C., et al. LEXam: Benchmarking legal reasoning on 340 law exams. In ICLR, 2026b. https://arxiv.org/abs/2505.12864
- German Federal Ministry of Justice. Gesetze im Internet. https://www.gesetze-im-internet.de/. Accessed July 2026.
- Government of Luxembourg. Legilux. https://legilux.public.lu/. Accessed July 2026.
- Guha, N., Nyarko, J., Ho, D. E., Ré, C., et al. LegalBench. In NeurIPS Datasets and Benchmarks Track, 2023.
- Niklaus, J., Matoshi, V., Rani, P., Galassi, A., Stürmer, M., and Chalkidis, I. LEXTREME. In Findings of EMNLP, 2023.
- Opsahl-Ong, K., Singhvi, A., Collins, J., Zhou, I., Wang, C., Baheti, A., Oertell, O., Portes, J., Havens, S., Elsen, E., Bendersky, M., Zaharia, M., and Chen, X. OfficeQA Pro. arXiv:2603.08655, 2026. https://arxiv.org/abs/2603.08655
- Piryani, B., Abdallah, A., Mozafari, J., Anand, A., and Jatowt, A. It's high time: A survey of temporal question answering. arXiv:2505.20243, 2025.
- Prior, M., Schultz, A., and Grabmair, M. Asking for an old friend: Diagnosing and mitigating temporal failure modes in LLM-based statutory question answering. arXiv:2605.23497, 2026.
- Swiss Federal Chancellery. Fedlex. https://www.fedlex.admin.ch/. Accessed July 2026.
- Vu, T., Iyyer, M., Wang, X., Constant, N., et al. FreshLLMs. arXiv:2310.03214, 2023.

---

## Phụ lục A. Thống kê kho văn bản và benchmark

Bảng 2 phân tích kho văn bản theo bộ luật: số phiên bản, số điều luật riêng biệt (`cid`) và độ sâu phiên bản trung bình. Bảng 3 cho biết phân bố 209 câu hỏi R3 được chấm điểm theo các điều CGI và các tiểu lĩnh vực thuế.

Hai lưu ý về điểm cuối của khoảng 93 năm. Mốc 1938 được mang bởi một phiên bản điều luật LPF duy nhất (điều L28) mà `date_debut` ghi lại ngày có hiệu lực của quy định tiền thân mà nó pháp điển hóa (decret-loi ngày 1/6/1938); bản thân LPF có từ 1981–82. Điểm cuối 2031 loại trừ 20 dòng mang các ngày giữ chỗ của Légifrance (2222-02-22, 2999-01-01), mà lớp chọn phiên bản không bao giờ cung cấp.

**Bảng 2.** Thống kê kho luật thuế. V/CID = số phiên bản trung bình mỗi điều luật (định danh hằng số).

| Bộ luật | Số phiên bản | Số CID | V/CID |
|---|---|---|---|
| CGI chính | 21.040 | 3.696 | 5,69 |
| CGI phụ lục III | 3.801 | 1.467 | 2,59 |
| LPF | 3.031 | 1.095 | 2,77 |
| CGI phụ lục II | 2.390 | 1.005 | 2,38 |
| CGI phụ lục IV | 1.879 | 705 | 2,67 |
| CGI phụ lục I | 295 | 108 | 2,73 |
| **Tổng** | **32.436** | **8.076** | **4,02** |

**Bảng 3.** Phân bố 209 câu hỏi suy luận thời gian (R3) được chấm điểm, khó-đối-với-mọi-mô-hình, theo các điều CGI và tiểu lĩnh vực thuế (mười hai câu hỏi đã công bố bị đánh dấu ngoài phạm vi có thể trả lời, gồm điều 199 undecies A và tám câu loại trừ qua rà soát, không được hiển thị). Tập trải trên bảy tiểu lĩnh vực thuế và 36 năm trôi dạt luật định (1989–2025), kể cả giai đoạn chuyển từ franc sang euro. Các điều được liệt kê theo thứ tự giảm dần số câu hỏi trong từng tiểu lĩnh vực (số trong ngoặc).

| Tiểu lĩnh vực | Các điều chính (# câu hỏi) | # | Khoảng thời gian |
|---|---|---|---|
| Thuế kinh doanh địa phương &amp; nhà ở (IFER, CFE, TH, TSE) | 1466 A (34), 1519 A (20), 1586 nonies (17), 1519 HA (16), 1647 D (4), 1414 A (4), 1609 C (4), 1417 (2), 1414 B (1) | 102 | 1990–2024 |
| Thuế thu nhập cá nhân (IR) | 156 (16), 196 B (5), 168 (5), 158 (4), 157 bis (4), 204 H (4), 200 (2), 199 decies H (2), 83 (2), 199 sexies (1), 5 (1) | 46 | 1989–2024 |
| Cá cược &amp; trò chơi | 302 bis ZI (16), 302 bis ZG (9) | 25 | 2012–2025 |
| Thuế gián thu (VAT, thuốc lá, TV, khai khoáng) | 568 (7), 1587 (7), 261 (3), 302 bis ZC (3), 1605 bis (3) | 23 | 1996–2025 |
| BIC, nông nghiệp &amp; xuyên biên giới | 50-0 (3), 182 A (1), 1679 A (1), 73 (1) | 6 | 1991–2025 |
| Thuế tiền lương | 231 (5) | 5 | 2002–2019 |
| Thuế tài sản (ISF) | 885 H (2) | 2 | 2010–2014 |
| **Tổng: 33 điều, 7 tiểu lĩnh vực** | | **209** | **1989–2025** |

---

## Phụ lục B. Liên kết án lệ có nhận biết phiên bản

Cùng với luật thành văn có phiên bản, chúng tôi công bố một bộ dữ liệu liên kết các phán quyết của tòa án liên quan đến thuế với phiên bản điều luật cụ thể áp dụng tại ngày phán quyết. Tài nguyên này là phụ trợ cho nghiên cứu temporal misgrounding (nó không được dùng trong thí nghiệm có kiểm soát ở §6); chúng tôi cung cấp đầy đủ việc xây dựng và phân tích chất lượng của nó ở đây.

### B.1. Xây dựng

**Các phán quyết nguồn.** Chúng tôi làm việc với bốn nguồn án lệ liên quan đến thuế của Pháp: các phán quyết `arianeweb` (Conseil d'État, 51.564 phán quyết), `inca` (Cour de cassation, 300.383), các phán quyết `judilibre` (Cour de cassation với visa có cấu trúc, 265.891), và `decisions_unified` (tổng hợp các nguồn trên cùng các cơ quan EU và ngành, 663.748). Để tránh đếm trùng giữa bản tổng hợp và các nguồn gốc của nó, chúng tôi báo cáo các thước đo theo từng nguồn riêng lẻ. Chúng tôi giới hạn mỗi nguồn vào một tập con thuế bằng một truy vấn PostgreSQL `tsvector` (cho `decisions_unified`) hoặc khớp mẫu trên các thuật ngữ liên quan đến thuế (cho các nguồn còn lại); các tập con thu được tổng cộng 61.835 phán quyết.

**Trích xuất trích dẫn và chọn phiên bản.** Với mỗi phán quyết thuế, chúng tôi áp dụng một bộ trích xuất dùng biểu thức chính quy nhạy với các quy ước trích dẫn thuế của Pháp: các điều có đánh số (ví dụ: điều 209 B), tiền tố LPF (L. 16 B, R. 281-1) và các số thứ tự Latin (bis, ter, quater, ...). Các ứng viên được lọc bằng một cơ chế khử nhập nhằng hai tầng: (i) một veto lân cận loại bỏ các khớp mà ngữ cảnh bên phải liền kề (±70 ký tự) gắn chúng với một nguồn khác (ví dụ: *du Code civil*, *de la loi n° X*), và (ii) một yêu cầu về ngữ cảnh thuế trong cửa sổ ±100 ký tự.⁴ Mỗi ứng viên sống sót được giải quyết dựa trên một chỉ mục điều luật trong bộ nhớ; sau đó chúng tôi chọn phiên bản điều luật có hiệu lực tại ngày của phán quyết bằng cách giao với các khoảng `date_debut` và `date_fin`. Khi có các trường visa có cấu trúc (Judilibre), chúng tôi gắn nhãn liên kết là `VISE` (được trích dẫn chính thức làm căn cứ pháp lý); mọi liên kết khác được gắn nhãn `CITE`.

**Đầu ra.** Việc liên kết tạo ra 69.208 liên kết có nhận biết phiên bản trên 32.034 phán quyết riêng biệt. Trong số này, 97% trỏ tới một phiên bản có thời kỳ hiệu lực bao gồm chặt chẽ ngày của phán quyết; phần còn lại quay về phiên bản hoạt động gần nhất tại thời điểm phán quyết. Các phán quyết được liên kết trải năm thập kỷ (thập niên 2000 chiếm nhiều nhất; Bảng 4), cho phép đánh giá theo chiều dọc. Phân bố thập kỷ và tỷ lệ bao hàm hiệu lực được tính trên các bảng phán quyết nền, có thể tái dựng từ các nguồn công khai qua các script trích xuất được công bố; bộ dữ liệu liên kết được phát hành kèm theo chính các liên kết đã được giải quyết.

⁴ Với các số một đến ba chữ số nhập nhằng, chúng tôi yêu cầu ngữ cảnh thuế mạnh (nhắc tường minh CGI/LPF). Với các số có hậu tố hoặc tiền tố LPF, ngữ cảnh thuế yếu hơn là đủ.

**Bảng 4.** Phân bố các liên kết án lệ có nhận biết phiên bản và các phán quyết được liên kết theo thập kỷ. Mỗi phán quyết được xếp vào nhóm theo ngày phán quyết nếu có, nếu không thì theo ngày bắt đầu sớm nhất của phiên bản áp dụng (đối với 25% liên kết từ các bản ghi `decisions_unified` tổng hợp có trường ngày phán quyết chưa được điền trong ảnh chụp này); tổng khớp với 69.208 liên kết trên 32.034 phán quyết.

| Thập kỷ | Phán quyết | Liên kết |
|---|---|---|
| Trước 1990 | 7.629 | 15.953 |
| 1990–1999 | 6.995 | 13.774 |
| 2000–2009 | 7.679 | 17.182 |
| 2010–2019 | 4.991 | 10.588 |
| 2020–2026 | 4.740 | 11.711 |
| **Tổng** | **32.034** | **69.208** |

### B.2. Kiểm toán chất lượng

**Độ chính xác.** Chúng tôi lấy mẫu 100 liên kết phân tầng tỷ lệ theo nguồn (seed=42, tái lập được) và kiểm toán chúng bằng một bộ tự chú thích hai giai đoạn, sau đó rà soát thủ công các trường hợp độ tin cậy thấp. Bộ tự chú thích trước tiên kiểm tra ngữ cảnh bên phải liền kề (±60 ký tự sau số điều luật) xem có nhắc tường minh CGI/LPF (dương tính thật độ tin cậy cao) hay gắn với nguồn cạnh tranh (dương tính giả độ tin cậy cao); các trường hợp không có tín hiệu nào được kiểm tra trong cửa sổ rộng hơn ±300 ký tự. Chúng tôi đo được độ chính xác 98–99% trên mẫu phân tầng này. Dương tính giả còn lại duy nhất là một artefact trích xuất tiêu đề (một số điều luật trong tiêu đề metadata của một *arrêt* không có ngữ cảnh thuế). Độ chính xác đồng đều giữa các nguồn (Conseil d'État: 100%, Cour de cassation: 92%, Judilibre: 100%, `decisions_unified`: 99%) và giữa các loại số điều luật (hậu tố chữ cái, số thứ tự Latin, số ngắn, tiền tố LPF: tất cả ≥ 97%).

**Các chế độ thất bại.** 1–2% dương tính giả còn lại rơi vào bốn mẫu: (a) trùng số giữa các bộ luật (ví dụ: điều 1382 của Bộ luật Dân sự so với CGI), (b) gắn với một luật hoặc công ước có đánh số thay vì một bộ luật, (c) trích xuất từ metadata không thực chất (tiêu đề phán quyết), và (d) đồng tham chiếu nhập nhằng như "*le même code*". Các mẫu (a) và (b) phần lớn được veto lân cận xử lý; (c) và (d) thúc đẩy việc tinh chỉnh dựa trên NER được thảo luận bên dưới (Hạn chế và bước tiếp theo).

**Kiểm chứng chéo với visa Judilibre.** Trong 907 phán quyết thuế Judilibre, 843 (93%) nhận được ít nhất một liên kết (recall ở mức phán quyết). Trên 485 phán quyết có visa phân tích được là tham chiếu CGI/LPF, recall ở mức điều luật trên các điều khớp visa là 37,6% sau khi khớp thân từ mờ. Phần chênh còn lại được giải thích một phần bởi (i) nhãn visa thô hơn (ví dụ: L16) so với trích dẫn văn bản mịn hơn (L. 16 B), và (ii) các điều luật được trích dẫn trong lập luận của phán quyết nhưng không chính thức thuộc visa.

**Recall tiêu chuẩn vàng thủ công.** Mọi điều CGI/LPF được trích dẫn trong một mẫu ngẫu nhiên phân tầng gồm 50 phán quyết thuế được chú thích toàn diện (đọc trên toàn văn, không phải đoạn trích bị cắt), cho ra 116 tham chiếu điều luật trên 34 phán quyết (16 phán quyết không trích điều CGI/LPF nào cụ thể). So sánh các liên kết của pipeline với chân lý nền này, với chuẩn hóa danh tính điều luật áp dụng đối xứng cho cả hai phía (giữ hậu tố chữ cái và số thứ tự Latin; bỏ dấu đoạn/khoản), chúng tôi đo được độ chính xác 88,6% ở mức điều luật, recall 53,4% ở mức điều luật và recall 97% ở mức phán quyết (33/34 phán quyết nhận ít nhất một liên kết đúng). Recall cao nhất trên các nguồn cơ quan tài phán có cấu trúc (Judilibre 71%, `decisions_unified` 55%, Arianeweb 53%) và thấp nhất trên `inca` (48%). Các âm tính giả còn lại tập trung ở (i) các trích dẫn xuất hiện sâu trong các phán quyết dài (20–45 nghìn ký tự, vượt quá khoảng mà bộ trích xuất xử lý) và (ii) các điều luật thủ tục LPF (chuỗi L./R.); cả hai thúc đẩy bộ trích xuất dựa trên NER bên dưới. Phép đo ở mức điều luật này bổ sung cho kiểm toán độ chính xác ở mức liên kết ở trên: pipeline tìm được ít nhất một điều luật làm căn cứ trong gần như mọi phán quyết, và khoảng một nửa số điều luật được trích dẫn.

**Hạn chế và bước tiếp theo.** Recall không đồng đều: 83–93% trên ba nguồn cơ quan tài phán nhưng chỉ 39% trên bảng `decisions_unified` tổng hợp nhiễu hơn, với 1–2% dương tính giả còn lại (trùng giữa các bộ luật, artefact tiêu đề, đồng tham chiếu nhập nhằng). Một bộ trích xuất NER pháp lý tinh chỉnh, được giám sát yếu bởi 69.208 liên kết regex cộng tiêu chuẩn vàng 50 phán quyết, là bước tiếp theo tự nhiên để thu hẹp phần lớn khoảng cách này.

---

## Phụ lục C. Nghiên cứu tình huống: Temporal misgrounding trên điều 219 CGI

Hình 1 đi qua từng bước một câu hỏi R3 từ đầu đến cuối qua ba điều kiện. Câu hỏi hỏi thuế suất thuế thu nhập doanh nghiệp tiêu chuẩn cho các năm tài chính bắt đầu từ ngày 1/1/2018 trở đi (chuẩn: điều 219 CGI, phiên bản `LEGIARTI000036431672` có hiệu lực từ 2018-01-01, "... fixé à 33 1/3 %"; nugget `{art_219_CGI, 33_one_third_pct, version_2018, rate_general_regime}`). **LLM-only (A)** và **RAG kho tĩnh (B)** đều trả lời "25%" (2/4 nugget): A do thiên lệch tính mới của tri thức tham số, B do neo vào một phiên bản hợp nhất hiện hành có thật nhưng không áp dụng (hợp nhất 2026; bản thân mức 25% không đổi từ năm 2022): chế độ ngấm ngầm nhất, vì provenance được giữ nhưng tính đúng đắn thì không. Điều kiện hóa truy xuất theo ngày của câu hỏi (C) trả về phiên bản 2018 và cho kết quả đúng "33⅓%" (4/4). Cùng LLM, cùng kho văn bản, chỉ khác việc chọn phiên bản, và khoảng cách chuyển từ 50% lên 100% ở câu hỏi này. (Chúng tôi dùng điều 219 ở đây chỉ cho rõ ràng; tập được chấm điểm nhắm đến các điều ít bị ghi nhớ hơn, Bảng 3.)

```
Q: thuế suất thuế TNDN tiêu chuẩn cho các năm tài chính bắt đầu từ 1/1/2018?
   (chuẩn: 33 1/3 %, điều 219 CGI)

A  LLM-only (không truy xuất)                          → 25%        ✗
B  RAG tĩnh: điều 219 phiên bản 2026 "25 %"            → 25%        ✗  (sai một cách tự tin)
C  có phiên bản (của chúng tôi): điều 219 phiên bản 2018
   "33 1/3 %"                                          → 33 1/3 %   ✓
```

*Hình 1.* Ba điều kiện truy xuất trên một câu hỏi trôi dạt theo thời gian (điều 219 CGI, năm tài chính 2018). B truy xuất một phiên bản có thật nhưng không áp dụng, là phiên bản hợp nhất hiện hành (hợp nhất 2026; mức 25% của nó không đổi từ năm 2022), và sai một cách tự tin; C điều kiện hóa truy xuất theo ngày của câu hỏi, trả về phiên bản 2018 và neo căn cứ cho đáp án đúng. Cùng LLM, cùng kho văn bản; chỉ khác việc chọn phiên bản.

---

## Phụ lục D. Khả năng tái lập

Chúng tôi liệt kê tường minh những gì được công bố.⁵

**Dữ liệu** (CC-BY-4.0, kèm ghi nhận nguồn Légifrance/Judilibre–Etalab 2.0; có kèm checksum SHA256): kho văn bản có phiên bản (32.436 phiên bản điều luật, Parquet); bộ dữ liệu liên kết (69.208 trích dẫn có nhận biết phiên bản); benchmark (R3, 221 câu hỏi với 209 câu trong phạm vi chấm điểm, cộng các track R2/R4, cùng nugget và đáp án chuẩn); mẫu kiểm toán phân tầng 100 liên kết và tiêu chuẩn vàng 50 phán quyết; toàn bộ phản hồi của mô hình đằng sau Bảng 1 (thí nghiệm ablation cửa sổ truy vấn ở §7.2 có thể chạy lại qua các script được công bố).

**Mã** (MIT): trích xuất chrono, liên kết, kiểm toán và lấy mẫu tiêu chuẩn vàng, bộ khung thí nghiệm cho các điều kiện có thể tái lập (mọi prompt điều kiện và ngân sách 8.000 ký tự/điều luật theo cửa sổ truy vấn có thể kiểm chứng trong `run_conditions.py`; các điều kiện A, B và C_or chạy với `--retriever oracle`), bộ chấm điểm tất định, và thống kê nhận biết cụm (`stats_clustered.py`).

**Không được công bố:** bộ truy xuất C_prod end-to-end, gồm trọng số bộ mã hóa thích nghi miền, chỉ mục đa phiên bản và mã suy luận, tất cả đều độc quyền. Do đó C_prod không thể tái lập từ các thành phần được công bố; chúng tôi công bố các phản hồi của mô hình theo từng câu hỏi để các điểm C_prod được báo cáo vẫn có thể kiểm chứng độc lập bằng bộ chấm điểm tất định.

Giữa bài nộp ban đầu và bản camera-ready này, chỉ mục điều luật được điều chỉnh từ một phiên bản "dài nhất" cho mỗi `cid` sang ba phiên bản đại diện cho mỗi `cid` (đầu, trung vị, cuối theo `date_debut`, loại trừ các artefact `MODIFIE_MORT_NE`), giữ nguyên mô hình embedding, siêu tham số BM25, bộ chia chunk và hằng số hợp nhất RRF.

Về vấn đề nhiễm dữ liệu liên quan: các cặp tinh chỉnh của bộ mã hóa trùng với benchmark trên năm điều luật được công bố ở mức điều luật, trong đó điều 150 U, một trong năm điều, bị đánh dấu ngoài phạm vi có thể trả lời, để lại 28 câu hỏi được chấm bị ảnh hưởng trên bốn trong số 33 điều được chấm; nhưng không một giá trị chuẩn nào của các câu hỏi đó xuất hiện trong bất kỳ đoạn huấn luyện nào (các cặp chứa văn bản phiên bản hiện hành; benchmark nhắm đến các giá trị lịch sử); phép kiểm tra, cùng script chạy lại được, có thể xin từ các tác giả (các điều luật huấn luyện của reranker không giao với benchmark, như nêu ở §5; bộ mã hóa cần phép kiểm tra mịn hơn ở mức giá trị này). Các file benchmark nhúng một GUID canary kiểu BIG-bench để có thể phát hiện nhiễm dữ liệu huấn luyện trong tương lai. Toàn bộ việc trích xuất có thể tái lập end-to-end từ dữ liệu công khai của Légifrance và Judilibre (truy cập API miễn phí qua PISTE và cổng của Cour de cassation). Các seed ngẫu nhiên được cố định (42 cho mẫu kiểm toán, 2026 cho tiêu chuẩn vàng, 42 cho bộ chấm điểm và các bootstrap theo cụm). Các thiết lập đánh giá riêng của từng nhà cung cấp được ghi lại trong mã và trong README của repository (ghim phiên bản SDK; suy luận của GLM 5.2 bị tắt qua cờ extra body của OpenRouter; GPT-5.5 được gọi với `reasoning_effort="none"` để tương đương với GPT-5.4 trong các phép dò closed-book). Repository cũng chứa các tài liệu `README`, `METHODOLOGY`, `DATA_SCHEMA` và `SPEC_GOLD_STANDARD` quy định giao thức chú thích mà các tác giả đã tuân theo.

⁵ https://github.com/rosecymbler/fiscal-fr-bench

---

## Phụ lục E. Điều kiện đối chứng (tính đúng dạng)

Tính đúng dạng của thất bại ở Điều kiện B được thiết lập ngay trong tập được chấm điểm (§7.2), không cần một tập đối chứng riêng. Hai sự thật cùng nhau loại trừ khả năng câu hỏi đặt không chuẩn hoặc pipeline hỏng.

**(i)** Dưới cùng prompt điều-luật-có-nhãn và pipeline truy xuất, chỉ thay đổi phiên bản được cung cấp của cùng điều luật (chọn phiên bản oracle, C_or) nâng độ chính xác strict gộp từ 2,7% (Điều kiện B) lên 99,1% trên cùng 209 câu hỏi (Bảng 1): các câu hỏi là trả lời được và mô hình trích xuất đúng giá trị khi được đưa phiên bản áp dụng theo ngày.

**(ii)** Văn bản phiên bản hiện hành không chứa giá trị neo theo ngày chuẩn ở 208 trên 209 câu hỏi được chấm (§5); ở ngoại lệ không trôi dạt duy nhất, giá trị có mặt và Điều kiện B tĩnh truy xuất đúng.

Do đó, điểm strict gần bằng không của Điều kiện B là do trôi dạt phiên bản, không phải do độ khó của câu hỏi hay lỗi pipeline.