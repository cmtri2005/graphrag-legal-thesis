# Temporal Misgrounding in Legal RAG: A Versioned-Corpus Benchmark for French Tax Law

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/2608.09393v1.pdf` (bản trùng: `Temporal Misgrounding in Legal RAG_...pdf`).

## 0. Thông tin chung

| Mục | Nội dung |
|---|---|
| Tác giả | Rose Cymbler (Talia, Paris), Daniel Guez (Talia), Laurent Fabre (Databricks) |
| Nơi đăng | arXiv:2608.09393v1 [cs.CL], 10/08/2026. Workshop ICML 2026 AI for Law (AI4Law), Seoul |
| Mã nguồn / dữ liệu | https://github.com/rosecymbler/fiscal-fr-bench (dữ liệu CC-BY-4.0, mã MIT) |
| Tên bộ dữ liệu | **FiscalQA Pro** (bản phát hành: Fiscal-FR-Bench v0) |
| Độ gần với ViLexTime | **Rất cao**: cùng là benchmark "đúng phiên bản luật theo ngày áp dụng", chấm tất định, không dùng LLM-judge |
| Lưu ý | Đây là bài workshop, có nhiều tác giả công ty, bộ truy hồi end-to-end (C_prod) **không phát hành** |

## 1. WHY – Bài toán và động lực

- Phần lớn benchmark pháp lý (LegalBench, LEXTREME, LEXam, JuriBERT, ClaimRAG-LAW) ngầm giả định **kho luật tĩnh**. Luật thuế thì ngược lại: sửa mỗi năm qua luật tài chính, và đáp án đúng phụ thuộc **ngày áp dụng**.
- Ví dụ mở đầu: "Thuế suất TNDN chuẩn năm 2018 là bao nhiêu?" Đáp án đúng là 33⅓%, nhưng LLM (có hoặc không có RAG trên kho bản hiện hành) trả 25% (mức hiện nay).
- Đặt tên hiện tượng: **temporal misgrounding** (neo sai thời điểm) = việc hệ thống lấy và trích **bản đang có hiệu lực hiện tại** của một điều luật trong khi câu hỏi cần **bản có hiệu lực ở thời điểm khác** (cũ hoặc tương lai).
- Câu hỏi nghiên cứu: với các câu hỏi mà đáp án theo ngày khác với luật hiện hành, temporal misgrounding làm nghẽn độ chính xác của LLM/RAG hiện đại đến mức nào?
- Giả thuyết (H) của tác giả: tính hợp lệ theo thời gian là **trục bậc nhất** của việc neo căn cứ pháp lý; điều kiện hóa truy hồi theo thời gian của câu hỏi sẽ đóng phần lớn khoảng cách, và một retriever end-to-end (không cần oracle) làm được điều đó.

### 1.1 Ba nguyên nhân gốc (root causes)
1. **Thiên lệch gần đây của tri thức tham số (parametric recency bias)**: LLM huấn luyện trên ảnh chụp nghiêng về trạng thái luật mới nhất.
2. **Truy hồi thiếu điều kiện thời gian**: dense retriever chỉ xếp hạng theo tương đồng ngữ nghĩa, không dùng ngày ngầm trong câu hỏi.
3. **Trùng số hiệu điều (article-number aliasing)**: số hiệu điều (ví dụ Điều 219 CGI) tồn tại ở mọi phiên bản nên truy hồi ngây thơ không biết phiên bản nào được hỏi.

### 1.2 Ba tính chất cấu trúc của kho luật làm RAG tĩnh thất bại (mục 3.1)
- **P1 – Cùng định danh, khác nội dung**: art. 219 CGI luôn tồn tại, nhưng thuế suất chuẩn là 33⅓% (2018), 31% (2019), 28% (2020), 26,5% (2021), 25% (từ 2022). Định danh (cid) ổn định; cặp (article id, version id) mới biến thiên.
- **P2 – Tính đúng phụ thuộc ngày**: mỗi phiên bản có `date_debut`/`date_fin`; một câu hỏi neo 2018 có đúng một phiên bản đúng. Tính đúng là **nhị phân**, "gần đúng" là sai.
- **P3 – Tương đồng ngữ nghĩa chéo phiên bản**: các phiên bản kế tiếp gần như giống hệt về chữ, thường chỉ khác một mức thuế hay ngưỡng. Embedding của chúng là láng giềng gần nhất của nhau, nên **không thể phân biệt bằng độ tương đồng**.

### 1.3 Bốn kiểu thất bại (taxonomy, mục 3.2)
1. **Current-law substitution**: trả bản hiện hành bất kể ngày hỏi (kiểu chủ đạo, do chỉ mục chỉ có bản hiện hành hoặc ưu tiên bản mới).
2. **Future-law leakage**: trả bản "VIGUEUR_DIFF" (chưa có hiệu lực) cho câu hỏi ở hiện tại.
3. **Wrong-amendment resolution**: hỏi "phiên bản trước luật X" nhưng nhận bản hiện hành hoặc bản cũ tùy ý (hay gặp trong án lệ: tòa áp dụng bản đã bị thay thế cho sự kiện phát sinh dưới bản đó).
4. **Multi-version confusion**: câu hỏi so sánh trước/sau cải cách bị gộp thành một phiên bản điểm cao nhất.

Bài chỉ đo kiểu (1); ba kiểu còn lại để v1.

### 1.4 Vì sao mô hình lớn hơn không giải quyết (mục 3.3)
(i) thiên lệch gần đây mang tính cấu trúc; (ii) khối lượng lịch sử khổng lồ (30k+ phiên bản chỉ riêng CGI và LPF), học thuộc không giải bài toán phân biệt P3; (iii) câu hỏi theo thời gian dễ nhận ra nhưng khó trả lời nếu không có chỉ mục phiên bản. Kết luận: cần thay đổi **cấu trúc truy hồi** (đánh chỉ mục phiên bản, điều kiện hóa ngày), không phải mô hình to hơn.

## 2. HOW – Phương pháp

### 2.1 Kho luật có phiên bản (mục 4.1, Phụ lục A)
- Nguồn: API PISTE Légifrance (DILA). Dùng endpoint `/consult/getArticleByCid` (trả **toàn bộ lịch sử phiên bản**), khác `/consult/getArticle` (chỉ bản hiện hành). Mỗi phiên bản có định danh `LEGIARTI...` riêng dưới một `cid` ổn định.
- Quy trình: liệt kê các định danh hằng (cid) qua endpoint mục lục của từng LEGITEXT, gọi `getArticleByCid` một lần mỗi cid, upsert mọi phiên bản với `date_debut`, `date_fin`, `etat` (đang hiệu lực, đã sửa, bị bãi bỏ, có hiệu lực tương lai) và toàn văn. Pipeline idempotent, tái lập được từ nguồn công khai.
- Quy mô: **32.436 phiên bản điều luật**, 8.076 cid, trung bình 4,02 phiên bản/cid, trải 93 năm (1938–2031).

| Bộ luật | Số phiên bản | Số cid | Phiên bản/cid |
|---|---|---|---|
| CGI chính | 21.040 | 3.696 | 5,69 |
| CGI phụ lục III | 3.801 | 1.467 | 2,59 |
| LPF | 3.031 | 1.095 | 2,77 |
| CGI phụ lục II | 2.390 | 1.005 | 2,38 |
| CGI phụ lục IV | 1.879 | 705 | 2,67 |
| CGI phụ lục I | 295 | 108 | 2,73 |
| **Tổng** | **32.436** | **8.076** | **4,02** |

- Điều có nhiều phiên bản nhất: art. 81 CGI (thu nhập miễn thuế), **94 phiên bản**.
- Cảnh báo hai đầu mút: mốc 1938 chỉ đến từ **một** phiên bản (art. L28 LPF; `date_debut` ghi ngày hiệu lực của quy định tiền thân, décret-loi 01/06/1938; bản thân LPF có từ 1981–82). Mốc 2031 loại 20 dòng mang ngày giữ chỗ của Légifrance (2222-02-22, 2999-01-01), lớp chọn phiên bản không bao giờ trả các dòng này.

### 2.2 Liên kết án lệ có phiên bản (mục 4.2, Phụ lục B) – nguồn phụ
- Mục đích: giám sát yếu cho track R1/R4, **không** dùng làm ground truth R3, không dùng trong thí nghiệm chính.
- Nguồn án lệ: arianeweb (Conseil d'État, 51.564), inca (Cour de cassation, 300.383), judilibre (Cour de cassation có visa có cấu trúc, 265.891), decisions_unified (hợp nhất + EU + cơ quan ngành, 663.748). Báo cáo số liệu theo từng nguồn để tránh đếm đôi. Lọc ra tập thuế: **61.835 quyết định**.
- Trích dẫn bằng regex nhạy với quy ước viết điều luật thuế Pháp (209 B; L. 16 B, R. 281-1; bis/ter/quater...). Hai tầng khử nhập nhằng: (i) **proximity veto** (±70 ký tự bên phải gắn với nguồn khác như "du Code civil", "de la loi n° X" thì loại); (ii) yêu cầu **ngữ cảnh thuế** trong cửa sổ ±100 ký tự (số 1–3 chữ số mơ hồ cần nhắc rõ CGI/LPF; số có hậu tố hay tiền tố LPF thì ngữ cảnh yếu hơn là đủ).
- Chọn phiên bản bằng cách giao với khoảng `date_debut`–`date_fin` tại ngày ra quyết định. Gắn nhãn `VISE` (nêu chính thức làm căn cứ, Judilibre) hoặc `CITE`.
- Kết quả: **69.208 liên kết** trên **32.034 quyết định**; 97% trỏ đến phiên bản có khoảng hiệu lực chứa ngày quyết định, phần còn lại lùi về phiên bản hoạt động gần nhất.

| Thập niên | Quyết định | Liên kết |
|---|---|---|
| Trước 1990 | 7.629 | 15.953 |
| 1990–1999 | 6.995 | 13.774 |
| 2000–2009 | 7.679 | 17.182 |
| 2010–2019 | 4.991 | 10.588 |
| 2020–2026 | 4.740 | 11.711 |

- Kiểm định chất lượng: độ chính xác mức liên kết **98–99%** (mẫu 100 liên kết phân tầng theo nguồn, seed 42; tự động gán nhãn hai bước rồi người xem các ca độ tin thấp). Theo nguồn: Conseil d'État 100%, Cour de cassation 92%, Judilibre 100%, decisions_unified 99%; mọi loại số điều đều ≥97%. 1–2% dương tính giả thuộc 4 mẫu: (a) trùng số giữa bộ luật (art. 1382 Dân sự vs CGI), (b) gắn với luật/công ước thay vì bộ luật, (c) trích từ phần metadata đầu quyết định, (d) đồng tham chiếu mơ hồ ("le même code").
- Recall: mẫu vàng 50 quyết định, đọc toàn văn, 116 tham chiếu điều ở 34 quyết định (16 quyết định không trích điều CGI/LPF nào). Kết quả: **88,6% precision cấp điều, 53,4% recall cấp điều, 97% recall cấp quyết định (33/34)**. Recall theo nguồn: Judilibre 71%, decisions_unified 55%, Ariane 53%, inca 48%. Với 907 quyết định thuế của Judilibre: 843 (93%) có ít nhất một liên kết; trên 485 quyết định có visa đọc được, recall cấp điều theo visa 37,6% sau khớp mờ. Nguyên nhân bỏ sót: trích dẫn nằm sâu trong quyết định dài (20–45k ký tự, ngoài khoảng extractor xử lý), điều thủ tục LPF (loạt L./R.), nhãn visa thô hơn (L16 vs L. 16 B). Hướng tiếp: NER tinh chỉnh với giám sát yếu từ 69.208 liên kết.

### 2.3 Thiết kế benchmark: 4 chế độ câu hỏi (R1–R4)
| Chế độ | Nội dung | Cách chấm | Số lượng |
|---|---|---|---|
| R1 | Trích dẫn: từ một quyết định + câu hỏi, tìm điều CGI/LPF làm căn cứ | khớp đúng cid | (không nêu) |
| R2 | Tính toán tất định: áp thuế suất/quy tắc vào số liệu | khớp đúng có dung sai | 43 |
| **R3** | **Suy luận thời gian (đóng góp chính)** | 2 nugget bắt buộc + kiểm tra provenance phía truy hồi | **221 phát hành, 209 chấm** |
| R4 | Tổng hợp đa tài liệu (CGI + BOFiP + án lệ) | 3–7 nugget/câu | 209 |

Ví dụ R3: "Thuế suất TNDN chuẩn cho năm tài chính mở từ 01/01/2018 trở đi, chế độ chung (không SME)?" → nugget: `\b219\b` (regex) và 33,333% (số có dung sai); phiên bản áp dụng được kiểm chứng bằng provenance truy hồi.

### 2.4 Chấm điểm bằng nugget, **không** LLM-judge (mục 5.2)
- Công thức: `score(r, N) = (1/|N|) Σ 1[n_i ∈ r]`; mỗi nugget là mệnh đề nguyên tử kiểm tra được tất định: mã điều (regex), giá trị số (khớp có dung sai sau chuẩn hóa: dấu ngăn nghìn kiểu Pháp, dấu phẩy thập phân), hoặc khớp chuỗi chính xác.
- Mượn khung nugget của KARL (Databricks 2026) nhưng **bỏ hẳn judge**, vì nugget trong KARL vẫn là biến thể LLM-as-judge.
- Lý do bỏ LLM-judge: trục thời gian chính là chỗ các LLM chia sẻ cùng thiên lệch, nên judge sẽ **thừa hưởng lỗi nó phải chấm** (chấp nhận câu trả lời trôi chảy nêu giá trị sai ngày vì trùng với tiên nghiệm của nó). Đổi lại, biểu đạt hẹp hơn; tác giả giữ biểu đạt bằng cách cố định phần định tính (chọn điều, tách giá trị phân biệt, chọn dung sai) lúc chú thích, kiểm với văn bản nguồn; lúc chấm chỉ là regex hoặc so số. Bất đồng giải quyết bằng đọc lại kho, không phải hỏi lại judge.
- Ba chỉ số: **coverage** (tỷ lệ nugget trúng), **strict** (cả hai nugget: đúng điều và đúng giá trị), **provenance** (phiên bản vàng nằm trong số phiên bản đã truy hồi: điều đơn cho B và C_or; top-5 cho C_prod).
- Rò rỉ nugget điều: regex của nugget điều khớp ngay trong câu hỏi ở 175/209 câu (83,7%), nên trích đúng điều không chứng minh truy hồi tốt. Do đó báo thêm **value-only coverage** (chỉ nugget giá trị); chỉ số này bám strict trong 1 điểm (A 3,0%; B 2,7%; C_or 99,2%; C_prod 98,5%). Hệ quả: C_prod nhận số điều trong 83,7% truy vấn, nên recall điều là có điều kiện "người dùng đã nêu số điều" như luật sư thực tế.

### 2.5 Bộ lọc độ khó và quy trình tạo câu hỏi (mục 5.3–5.4)
- **Bộ lọc tri thức tham số (zero-knowledge)**: đưa từng câu ứng viên cho mọi LLM đánh giá **không** kho/web; loại câu nếu bất kỳ mô hình nào nêu đúng giá trị vàng trong ít nhất một trong **4 lần lấy mẫu**. Chặt hơn tiêu chí "hợp trên các mô hình tiên phong" của OfficeQA Pro: hợp trên **cả 11 mô hình** (frontier + open-weight) → tập "all-model-hard".
- **Bộ lọc phân kỳ phiên bản hiện hành (không dùng LLM)**: regex kiểm tra giá trị vàng có xuất hiện nguyên văn trong bản hiện hành không; còn thì loại. Kết quả: văn bản hiện hành thiếu giá trị vàng ở **208/209** câu (1 câu ngoại lệ giữ làm đối chứng well-formedness). Hệ quả thừa nhận thẳng: điều kiện B thất bại **một phần do xây dựng**; phần có thể bác bỏ (falsifiable) của giả thuyết là provenance và trần, không phải điểm strict thấp.
- Câu hỏi: **tự động phát hiện điểm trôi, tác giả viết tay**. `r3_factory.py` quét lịch sử phiên bản tìm các bước chuyển giá trị (ngưỡng/thuế suất thay đổi giữa hai phiên bản liền kề); `r3_worksheet.py` xuất bảng làm việc (điều, ngày chuyển, giá trị trước/sau). Tác giả soạn câu, xác minh giá trị với phiên bản kho, đặt dung sai; toàn bộ tập được **một chuyên gia thuế Pháp có chứng chỉ** rà soát. Một phần câu xuất phát từ pool nội bộ độc quyền (Fiscal-FR-Bench v1).
- Chọn câu nhắm vào **tham số ít được học thuộc** (khoản miễn trừ có chỉ số hóa, ngưỡng, biểu giá IFER theo lắp đặt), không phải mức thuế nổi tiếng (như art. 219, art. 197), để chống tri thức tham số.
- 209 câu bao phủ 33 điều CGI, 7 lĩnh vực phụ (thuế thu nhập cá nhân; thuế kinh doanh/nhà ở địa phương; cá cược; gián thu; BIC/nông nghiệp/xuyên biên giới; thuế tiền lương; thuế tài sản ISF), thời gian trôi 1989–2025 (36 năm, gồm chuyển franc sang euro). Điều nhiều câu nhất: 1466 A (34), 156 (16), 1519 A (20), 1586 nonies (17), 302 bis ZI (16), 1519 HA (16).
- Loại 12 câu khỏi phạm vi chấm: 4 câu (art. 199 undecies A, trần/m² tái định giá hằng năm theo chỉ số INSEE công bố qua BOFiP) loại thận trọng ở khâu soạn; 8 câu loại ở lần rà toàn tập do lỗi soạn hoặc đặt sai neo ngày.
- **Đóng băng** 209 câu trước mọi phát triển retriever/reranker (`killer_qids_v2.txt`). Reranker đã thử chỉ fit trên điều rời tập này, không cải thiện top-1, và không thuộc pipeline C_prod.
- Nugget và đáp án **thủ công hoàn toàn**; đáp án chuẩn được đối chiếu nguyên văn với phiên bản mà nugget trỏ tới (cả 221 câu).
- Quy mô: ban đầu k=35 (R3 gốc, cố ý nhỏ), mở rộng lên 221 câu/33 điều (từ 10) sau phản hồi reviewer để đủ sức thống kê cho 11 mô hình.
- **Rò rỉ còn lại lúc đánh giá**: ít nhất một mô hình nêu đúng giá trị ở điều kiện A cho 37/209 câu (17,7%); mỗi mô hình 0–25 câu, cao nhất GPT-5.5 (25) và Opus 4.7 (16). Giải thích: sai khác lấy mẫu và tái dựng giá trị, không phải học thuộc (giá trị học thuộc sẽ xuất hiện đủ cả 4 lần và bị lọc).

### 2.6 Ba điều kiện thí nghiệm (mục 6)
Mười một mô hình: **frontier (đóng)**: Claude Opus 4.7, Opus 4.8, Sonnet 4.6, GPT-5.4, GPT-5.5, cộng Gemini 2.5 Pro thay thế (Gemini 3 Pro Preview bị giới hạn tốc độ); **open-weight**: Mistral Large 2407, Llama 4 Maverick, Qwen 3 235B (thay Qwen 2.5 72B bị gỡ khỏi mọi nhà cung cấp), Gemma 3 27B, GLM 5.2 (qua OpenRouter và Together AI).

- **A – LLM-only**: không truy hồi, không web, một lần chạy đánh giá/câu.
- **B – RAG trên kho hiện hành**: kho tĩnh chỉ bản đang hiệu lực. Được đưa đúng cid vàng nên **thiên vị có lợi cho baseline tĩnh**; vì vậy khoảng cách A/B ≪ C là cận dưới.
- **C – RAG trên kho có phiên bản** (lớp phiên bản trả bản áp dụng tại ngày trong câu hỏi):
  - **C_or (oracle)**: cid vàng, cô lập phần đóng góp của việc chọn phiên bản (trần).
  - **C_prod (end-to-end)**: tự tìm cả điều lẫn phiên bản, không oracle. Kênh dày = bộ mã hóa dày chuyên miền, tinh chỉnh, trên chỉ mục nhiều phiên bản đã chia chunk (3 phiên bản/cid: đầu, trung vị, cuối theo date_debut, loại các bản "MODIFIE_MORT_NE" chết lúc sinh); kênh thưa = BM25 trên cùng chunk; hợp nhất bằng **reciprocal-rank fusion** (không dùng cross-encoder). Top-5 điều duy nhất → lớp phiên bản chọn bản áp dụng theo ngày cho từng cid → mới đưa vào prompt.
- Cùng prompt "điều có nhãn", ngân sách **8.000 ký tự/điều** theo cửa sổ truy vấn (giữ đầu + đoạn liên quan nhất), đã kiểm trước rằng giá trị vàng nằm trong cửa sổ cho cả 209 câu. Thay thế giới hạn cũ 6.000 ký tự làm rớt giá trị ở một số điều dài (art. 158, 1605 bis, 261, 83). Nhét toàn văn **làm giảm** C_or ở điều dài (nhiễu ngữ cảnh dài).

### 2.7 Bốn giả thuyết có thể bác bỏ
- H1: A thấp về strict, đồng đều theo quy mô/nhà cung cấp; coverage không tầm thường vì nugget mã điều dễ.
- H2: B truy hồi phiên bản áp dụng 0% và strict <10%. (Phần falsifiable: 0% provenance là cấu trúc; trần <10% có thể bị vượt nếu mô hình tự suy lại giá trị lịch sử từ bản hiện hành, ví dụ bỏ chỉ số hóa.)
- H3: C_or đóng phần lớn khoảng cách (>80% strict, 100% provenance) → chọn phiên bản, không phải độ đầy đủ kho hay kích cỡ mô hình, là nút thắt.
- H4: C_prod gần bằng trần C_or; phần dư là trần recall@5 ở vài truy vấn ngách → đòn bẩy là recall, không phải rerank top-1.

## 3. WHAT – Kết quả

### 3.1 Bảng 1 (k=209, đơn vị %)

| Mô hình | Cov A | Cov B | Cov C_or | Cov C_prod | Strict A | Strict B | Strict C_or | Strict C_prod |
|---|---|---|---|---|---|---|---|---|
| Opus 4.7 | 53,8 | 55,3 | 100,0 | 99,8 | 7,7 | 10,5 | 100,0 | 99,5 |
| Opus 4.8 | 53,3 | 51,4 | 100,0 | 99,5 | 6,7 | 3,3 | 100,0 | 99,0 |
| Sonnet 4.6 | 49,5 | 50,0 | 100,0 | 99,5 | 1,0 | 1,4 | 100,0 | 99,0 |
| GPT-5.4 | 50,7 | 51,2 | 100,0 | 99,5 | 1,4 | 2,4 | 100,0 | 99,0 |
| GPT-5.5 | 56,0 | 54,1 | 100,0 | 99,8 | 12,0 | 8,1 | 100,0 | 99,5 |
| Gemini 2.5 Pro | 46,2 | 49,5 | 99,0 | 99,0 | 1,4 | 0,5 | 99,0 | 98,6 |
| Mistral Large | 50,2 | 50,7 | 99,8 | 99,0 | 0,5 | 1,4 | 99,5 | 98,1 |
| Llama 4 Maverick | 48,1 | 50,2 | 99,0 | 98,6 | 0,0 | 0,5 | 98,1 | 97,1 |
| Qwen 3 235B | 46,7 | 49,3 | 97,4 | 98,6 | 1,0 | 0,5 | 94,7 | 97,1 |
| Gemma 3 27B | 42,8 | 48,6 | 99,8 | 97,4 | 0,0 | 0,5 | 99,5 | 95,2 |
| GLM 5.2 | 49,0 | 50,2 | 99,8 | 99,5 | 1,0 | 1,0 | 99,5 | 99,0 |
| **Trung bình 11** | 49,7 | 51,0 | 99,5 | 99,1 | **3,0** | **2,7** | **99,1** | **98,3** |

Provenance: B = 0% mọi mô hình; C_or = 100%; C_prod = 99%.

### 3.2 Phát hiện chính
1. **A (tham số)**: strict 3,0%, bootstrap theo cụm 95% CI [1,4; 4,7]. Đồng đều giữa các thế hệ cùng họ (Opus, GPT-5) và giữa mô hình đóng/mở → quy mô hay đời mới không đóng khoảng cách (phù hợp H1).
2. **B (RAG kho hiện hành)**: strict 2,7% [1,3; 4,8], không khác A về thống kê, **provenance 0%**. Thất bại "tự tin": nền trên một bản có thật, hợp thức, nhưng không áp dụng được. 100% lỗi của B là current-law substitution.
3. **C_or**: strict **99,1%** [98,4; 99,9], provenance 100% → câu hỏi trả lời được, đọc không là vấn đề.
4. **C_prod** (không oracle): strict **98,3%** [95,9; 99,6]; mọi mô hình ≥95% theo điểm ước, mọi cận dưới CI theo mô hình >89%; phiên bản vàng nằm trong top-5 ở 99% câu. Khoảng C_or→C_prod chỉ **0,8 điểm**, nằm ở **recall bước đầu** chứ không ở chọn phiên bản; lần trượt provenance duy nhất là art. 1417 (2 câu). Reranker cross-encoder không thêm gì.
5. **Đối chứng well-formedness**: (i) đổi duy nhất phiên bản phục vụ (C_or) kéo B 2,7% lên 99,1%; (ii) hiện hành thiếu giá trị vàng ở 208/209 câu; ở câu ngoại lệ (giá trị có trong bản hiện hành) B truy hồi đúng. → lỗi của B là do trôi phiên bản, không phải câu hỏi khó hay pipeline hỏng.
6. **Ý nghĩa thống kê (theo cụm)**: giao thức ghép cặp có hai phụ thuộc mà phép phân tích iid bỏ qua: 11 mô hình trả lời cùng câu, và câu hỏi gom theo điều (33 cụm; riêng art. 1466 A chiếm 34 câu). Mô hình là đơn vị suy luận; bootstrap bằng **lấy mẫu lại điều** (10.000 lần, seed 42). Các cải thiện B→C_or và B→C_prod có ý nghĩa **cho từng mô hình** (McNemar hai phía chính xác, 11 phép kiểm, p<10⁻⁵⁵). Leave-one-article-out cho strict gộp C_prod trải từ 98,1% (bỏ art. 1519 A) đến 99,2% (bỏ art. 1417) → không điều đơn lẻ nào mang kết quả.
7. **Case study art. 219 (Phụ lục C, Hình 1)**: thuế suất TNDN chuẩn từ 01/01/2018, đáp án 33⅓%, phiên bản `LEGIARTI000036431672`. A: "25%" (thiên lệch tham số); B: "25%" bám bản hợp nhất 2026 (mức 25% không đổi từ 2022) nên "provenance được giữ nhưng tính đúng thì không"; C: truy hồi bản 2018 → "33⅓%". Cùng LLM, cùng kho, chỉ khác chọn phiên bản; độ phủ nugget nhảy từ 2/4 lên 4/4.

## 4. Hạn chế tác giả nêu (mục 9)
- Chỉ luật thuế Pháp; lập luận temporal misgrounding mang tính cấu trúc cho mọi hệ dân luật có API phiên bản (Fedlex Thụy Sĩ, Gesetze-im-Internet Đức, Justel Bỉ, Légilux Luxembourg). Bước tiếp: tái lập Fedlex.
- Quy mô 221 câu < LegalBench (162 *tác vụ*) hay KARLBench (2.000+); là đánh đổi có chủ ý vì độ khó tập trung, chuyên gia rà soát (so OfficeQA Pro 133 câu).
- R3 chỉ chạm kiểu current-law substitution; thiếu future-law leakage, "trước luật X", so sánh hai phiên bản (v1).
- R1–R3 đo **áp dụng luật**, không phải diễn giải pháp lý.
- Bộ truy hồi C_prod **độc quyền** (trọng số encoder, chỉ mục nhiều phiên bản, mã suy luận) → không tái lập từ artefact công khai; phát hành phản hồi từng câu để chấm lại bằng scorer tất định.
- Ô nhiễm dữ liệu: cặp tinh chỉnh encoder chồng cấp điều với benchmark trên 5 điều phát hành (art. 150 U đã loại; còn 28 câu chấm trên 4/33 điều) nhưng **không** có giá trị vàng nào xuất hiện trong dữ liệu huấn luyện (cặp chứa văn bản hiện hành, benchmark nhắm giá trị lịch sử). Tệp benchmark nhúng GUID canary kiểu BIG-bench.
- Qwen thay thế giữa lúc chọn và đánh giá; 22 phản hồi rỗng từ nhà cung cấp (Gemini 2.5 Pro, GLM 5.2) chấm là thất bại (hướng bảo thủ).

## 5. Các công trình liên quan được bài định vị (để lần theo)
- **OfficeQA Pro** (Opsahl-Ong 2026, arXiv:2603.08655): 133 câu, 89.000 trang Treasury Bulletins; chấm tất định; LLM <5% tham số, 12% có web, 34,1% có truy cập kho. FiscalQA Pro mở rộng sang tài liệu **sửa tại chỗ**, nơi ngày áp dụng là tín hiệu truy hồi hạng nhất.
- **KARL / KARLBench** (Databricks 2026, arXiv:2603.05218): 6 chế độ tìm kiếm, nugget; OAPL.
- **SAT-Graph RAG** (de Martim 2025, JURIX): giải truy vấn point-in-time bằng đồ thị tri thức ontology, đánh giá định tính trên Hiến pháp Brazil; FiscalQA Pro đối chiếu: **không cần ontology/đồ thị**, chỉ cần lập chỉ mục phiên bản tường minh + truy hồi điều kiện hóa ngày.
- **Fan et al. 2026a** (arXiv:2605.25920): thiên lệch ngưỡng huấn luyện và thiếu ràng buộc thời gian trong agent tìm kiếm pháp lý (benchmark RL 13 tác vụ).
- **Prior et al. 2026** (arXiv:2605.23497, "Asking for an old friend"): 312 cặp hỏi-đáp luật thành văn Đức được chuyên gia xác nhận, điều kiện RAG lọc phiên bản; nhưng dùng LLM-as-judge.
- Khác: LexTime (Barale 2025, thứ tự sự kiện pháp lý), TimeQA, TempLAMA, FreshQA (Vu 2023), khảo sát temporal QA (Piryani 2025), LEXam (Fan 2026b), ClaimRAG-LAW (Das 2026).

## 6. Dùng gì cho khóa luận ViLexTime

**Áp dụng trực tiếp**
1. **Thuật ngữ và khung động lực**: "temporal misgrounding" + 3 nguyên nhân + 3 tính chất cấu trúc (P1–P3) + taxonomy 4 kiểu lỗi. Luật Việt Nam cũng có "số hiệu điều giữ nguyên, nội dung đổi" qua sửa đổi/bổ sung (văn bản sửa đổi, hợp nhất).
2. **Chấm tất định bằng nugget (regex + số có dung sai) thay LLM-judge**, kèm lập luận "judge thừa hưởng thiên lệch thời gian". Phù hợp mục tiêu độ tin cậy của ViLexTime; cần thích nghi nugget cho đáp án tiếng Việt (định dạng số, ngày, ký hiệu văn bản).
3. **Ba chỉ số tách rời** coverage / strict / provenance, và cảnh báo **rò rỉ nugget điều vào câu hỏi** (83,7%) → báo thêm value-only.
4. **Bộ lọc độ khó 2 tầng**: (a) zero-knowledge nhiều lần lấy mẫu trên mọi mô hình; (b) phân kỳ so với phiên bản hiện hành bằng regex. Cần lưu ý (b) làm điều kiện B "thua theo xây dựng": phải nói rõ phần nào là kiểm thật, phần nào là kiểm xây dựng.
5. **Ba điều kiện A / B / C (oracle và end-to-end)** là thiết kế ablation chuẩn để chứng minh giá trị của thành phần thời gian.
6. **Thống kê theo cụm** (bootstrap lấy mẫu lại theo điều, McNemar theo mô hình) vì câu hỏi tập trung theo điều/văn bản; liên hệ với tình trạng câu hỏi ViLexTime gom theo văn bản.
7. **Quy trình tạo câu hỏi**: tự động phát hiện "điểm trôi giá trị" giữa hai phiên bản liền kề → bảng làm việc → người soạn + chuyên gia rà soát; đóng băng bộ chấm trước khi phát triển retriever; canary GUID chống ô nhiễm; phát hành đủ phản hồi mô hình để chấm lại.
8. **Chuẩn tái lập**: liệt kê rõ cái gì phát hành/không phát hành; seed cố định; checksum.

**Cẩn trọng / khác biệt cần xử lý**
- Bài **không dùng đồ thị**; luận điểm "đồ thị cần thiết" của khóa luận phải dựa vào bằng chứng khác (SAT-Graph RAG, ViHERMES, câu hỏi nhiều bước/truy vết sửa đổi). Kết quả 98,3% cho thấy với câu hỏi một neo thì **chỉ mục phiên bản + lọc ngày** đã đủ → ViLexTime cần câu hỏi vượt single-anchor (so sánh trước/sau, chuỗi sửa đổi) để đồ thị có chỗ thắng.
- Kết quả B≈0 **một phần do bộ lọc**; đừng trích "RAG tĩnh đúng 0%" như phát hiện độc lập.
- Quy mô nhỏ, một lĩnh vực, bộ truy hồi độc quyền; trần 99% cho thấy tập này gần bão hòa → ViLexTime nên có câu khó hơn (nhiều bước, nhiều văn bản).
- Số liệu đa phần do một nhóm tác giả công ty tự báo cáo, chưa có tái lập độc lập.
