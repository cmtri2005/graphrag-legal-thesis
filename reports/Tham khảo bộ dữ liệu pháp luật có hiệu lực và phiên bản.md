# Các bộ dữ liệu pháp luật có yếu tố hiệu lực và phiên bản: họ làm gì, ViLexTime học được gì

Mục đích: xem các bài đã công bố dựng bộ dữ liệu, kiểm chứng nhãn, đánh giá và trình bày
như thế nào, để áp vào ViLexTime. Soạn ngày 05/10/2026.

## 0. Độ tin cậy của tài liệu này

Mình đọc 15 bài, nhưng không phải bài nào cũng đọc ở cùng một mức. Nên kiểm lại con số
gốc trong bài trước khi trích vào datasheet hay bài báo.

| Mức | Cách đọc | Bài |
|---|---|---|
| **A** | Trích chữ thẳng từ file gốc (`pdftotext`) rồi đọc | LawShift, ViHERMES |
| **B** | Đọc bản HTML/PDF qua công cụ tóm tắt tự động của trang. Con số có thể sai chi tiết | German, FiscalQA Pro, LexKairos, TALD, LeKUBE, CALRK-Bench, LegalSearch-R1, VLegal-Bench, VLQA, TimelyRAG, SAT-Graph RAG, Deterministic Legal Agents |
| **C** | Chỉ có tóm tắt (abstract) | HoH |

**Không đọc được:** "Beyond Probabilistic Similarity" (arXiv 2606.09724) vì PDF nén. Phần
kết quả và phụ lục của LawShift mình chưa đọc.

**Ba tóm tắt đầu tiên mình nhận được là chung chung hoặc suy đoán** (TimelyRAG,
Deterministic Legal Agents, ViHERMES). Mình đã đọc lại bằng bản HTML hoặc `pdftotext` và chỉ dùng bản
sau. Xem mục 5 về chỗ này sửa lại báo cáo trước.

---

## 1. Bảng so sánh

| Bộ | Nơi / năm | Cỡ | Gold từ đâu | Ai kiểm | Có IAA? | Cấp hiệu lực | Có nhóm đối chứng tĩnh? |
|---|---|---|---|---|---|---|---|
| [German statutory QA](https://arxiv.org/html/2605.23497) | ICAIL 2026 | 312 (từ 697) | buzer.de, không chính thức | 2 SV luật + 1 luật sư | **Không** (chỉ κ của giám khảo LLM) | Điều luật | Không rõ |
| [FiscalQA Pro](https://arxiv.org/html/2608.09393) | arXiv 2026 | 221 / 209 chấm | API Légifrance, chính thức | 1 chuyên gia thuế duyệt toàn bộ | **Không** | Article | Có (lọc "giá trị không đổi") |
| [LexKairos](https://arxiv.org/html/2608.09106) | arXiv 2026 | 3.796, 9 tác vụ | Siêu dữ liệu + LLM trích | Chuyên gia duyệt tay | **Không** | Cả văn bản | Không |
| [TALD](https://arxiv.org/html/2608.14610) | arXiv 2026 | 26.000 bản án | Phiên bản luật toà án đã dẫn | 2 chuyên gia lấy mẫu, **không nêu cỡ** | **Không** | Bộ luật | Không |
| [LawShift](https://papers.nips.cc/paper_files/paper/2025/hash/adf82a0a1d52d93961476458b9566a2b-Abstract-Datasets_and_Benchmarks_Track.html) | NeurIPS 2025 D&B | 31 loại thay đổi, 99–470 mẫu mỗi loại | Chuyên gia tự soạn bản sửa đổi | 1 GS luật + 2 NCS luật | **Không** | Điều luật | Không |
| [LeKUBE](https://arxiv.org/html/2407.14192) | arXiv 2024 | 180 điều đã sửa + 60 không sửa | Người sửa điều luật | Người thứ hai kiểm từng mẫu | **Không** | Điều luật | **Có** ("locality") |
| [CALRK-Bench](https://arxiv.org/html/2603.26332) | arXiv 2026 | 479 (ô sửa luật: 8) | Người + GPT-5 | 1 GS luật | **Không** | – | Không |
| [LegalSearch-R1](https://arxiv.org/html/2605.25920v2) | arXiv 2026 | 3.584 train / 896 test | Sinh viên luật gán cửa sổ hiệu lực | SV luật, hướng dẫn ở phụ lục | Không rõ | Điều luật | Không |
| [VLegal-Bench](https://arxiv.org/html/2512.14554v5) | arXiv 2025–26 | 10.450, 22 tác vụ | Luật sư viết | 2 junior + 1 senior | **κ 0,89** (trước thảo luận) | Tĩnh | – |
| [VLQA](https://arxiv.org/html/2507.19995v1) | arXiv 2025 | 3.129 | 5 SV luật gán đôi | 1 chuyên gia | **Không** — báo tỷ lệ sửa | **Loại** điều đã bãi bỏ | – |
| [ViHERMES](https://arxiv.org/abs/2602.07361) | arXiv 2026 | 1.560 (= 312 × 5 mức hop) | LLM sinh, đồ thị gợi ý | Annotator + chuyên gia, **chỉ ca biên** | Không | Có chuỗi sửa đổi, ưu tiên nút cuối | Không |
| [TimelyRAG](https://arxiv.org/html/2609.11572) | arXiv 2026 | 12.000 (4 miền × 3.000) | **Tổng hợp** bằng Llama-3.3-70B | 50 mẫu người kiểm | Không | Phiên bản tài liệu | Không |
| **ViLexTime** | – | 666 lineage / 2.481 dòng | Chuỗi phiên bản vbpl.vn | 2 SV + (sắp) cố vấn | **κ 0,236 pilot, báo cả AC1** | **Khoản/điểm** | **Có (T1)** |

Chữ in đậm cho thấy ViLexTime đứng ở đâu: **trong 12 bộ, chỉ VLegal-Bench báo κ giữa
người với người**, và nó là bộ tĩnh. ViLexTime đã có số đo thật ở 300 dòng, dù chưa đạt
mốc.

---

## 2. Từng bài

### 2.1 German statutory QA (Prior et al., ICAIL 2026) — gần ViLexTime nhất về thiết kế

**Dựng.** Ba loại câu hỏi, mỗi loại một quy trình riêng: *Post-cutoff* (115 câu: đoạn luật
sửa sau mốc cutoff của model), *Pre-amendment* (113: phải áp bản cũ), *Multi-provision*
(84: nhiều điều luật, ≥1 điều có nhiều phiên bản). LLM sinh 697 cặp, người nhận **312**
(44,8%).

**Kiểm chứng.** Hai SV luật năm cuối và một luật sư. **Ghi lại lý do loại**: chỉ sửa câu chữ;
nhiều vấn đề độc lập trong một câu; hậu quả pháp lý như nhau bất kể phiên bản; đáp án có lỗi
pháp lý. **Không báo IAA.** 39/312 câu là cặp trùng điều luật và trùng lần sửa, giữ lại
**có chủ ý** để kiểm tính nhất quán nội bộ.

**Đánh giá.** Giám khảo LLM với bốn tiêu chí 0–1: kết luận, lập luận, căn cứ pháp lý, **áp
dụng đúng phiên bản**. Giám khảo được kiểm trên 48 câu / 192 câu trả lời với người: Pearson
0,853, κ 0,751; **κ 0,860 ở kết luận nhưng chỉ 0,549 ở căn cứ pháp lý**. Bốn chế độ suy
luận: vanilla, web, RAG-kNN (lọc theo ngày rồi kNN), RAG-ToC. Kiểm định Welch.

**Kết quả đáng nhớ.** Claude Sonnet 3.7 vanilla trên câu sau cutoff chỉ đạt 24,35% kết
luận; RAG đạt ~87%. GPT-5.1 vanilla đạt 40% kết luận nhưng **0% lập luận** — con số kết luận
che mất lỗi sâu hơn.

**Trình bày.** Có mục Related Work với bảng khoảng trống, hai hình pipeline có số lượng, mục
AI Disclosure riêng, người gán nêu tên trong Acknowledgements, CC BY 4.0, prompt công bố đủ.

**Học được.** (1) Bảng lý do loại kèm tỷ lệ nhận. (2) Cặp trùng giữ lại để đo nhất quán —
giống dòng twin của ViLexTime. (3) Báo κ của giám khảo **theo từng chiều**, không chỉ tổng.
**Không nên bắt chước:** không báo IAA cho phần người kiểm, và dùng nguồn không chính thức.

### 2.2 FiscalQA Pro (Cymbler et al., 2026) — mẫu mực về thiết kế đánh giá

**Dựng.** Nguồn chính thức, API Légifrance, có `date_debut`/`date_fin`. Hai script
**tìm điểm chuyển giá trị bằng chương trình** (`r3_factory.py`, `r3_worksheet.py`) rồi tác giả
mới viết câu hỏi: đúng mô hình "máy tìm chỗ đổi, người viết câu".

**Phễu.** 221 câu → bộ lọc kiến thức tham số (11 model × 4 lượt, **bỏ mọi câu mà bất kỳ model
nào đoán đúng giá trị**) → rà phạm vi trả lời được, loại 12 (4 chỉ số hoá theo INSEE, 8 lỗi
dựng) → **209 câu chấm**.

**Kiểm chứng.** Một chuyên gia thuế duyệt toàn bộ 209 câu. Bộ lọc **"giá trị khác phiên bản
hiện hành"** bằng regex: giá trị vàng không được xuất hiện trong văn bản đang hiệu lực (208/209
qua, một câu giữ làm đối chứng). **Không báo IAA.**

**Đánh giá — chỗ đáng học nhất.**
- Chấm **hoàn toàn xác định**, không dùng LLM giám khảo "vì model mang chính thiên lệch thời
  gian đang được đo": mỗi câu có hai "nugget" (regex số hiệu điều, giá trị số kèm dung sai);
  `Coverage`, `Strict` (cả hai nugget), `Provenance` (phiên bản vàng nằm trong top-5 truy xuất).
- **Bootstrap theo cụm điều luật** (33 điều), không theo câu; McNemar từng model.
- **Ba điều kiện có kiểm soát:** A LLM-only (3,0%); B RAG tĩnh chỉ có bản hiện hành (2,7%,
  **provenance 0%**); C-oracle phiên bản đúng (99,1%); C-prod truy xuất end-to-end (98,3%).
  Khoảng cách C-oracle so với C-prod chỉ 0,8 điểm, tức nút cổ chai là truy hồi điều luật,
  không phải chọn phiên bản.
- Bốn giả thuyết H1–H4, nêu thành dạng **có thể bác bỏ** (bản tóm tắt không cho biết có đăng
  ký trước hay không).
- Canary GUID trong file benchmark; kiểm trùng huấn luyện encoder ở mức giá trị.

**Học được.** Gần như toàn bộ phần "Đánh giá" của bài này áp được cho ViLexTime (xem mục 4).
**Giới hạn họ tự nêu:** bộ R3 một mốc, chưa phủ "rò luật tương lai", "áp nhầm lần sửa đổi",
"nhầm nhiều phiên bản" — đúng các chế độ mà dòng ranh giới và twin của ViLexTime phủ.

### 2.3 LawShift (Han et al., NeurIPS 2025 D&B) — **mẫu cho việc tách "hiện tượng" khỏi "trường"**

Mức A (đọc văn bản gốc).

**Vấn đề họ chỉ ra:** bộ LJP hiện tại trộn các phiên bản luật dưới cùng một nhãn, làm lẫn
logic phán quyết.

**Taxonomy 31 loại thay đổi, dựng theo phương pháp** — đây là điều đáng học nhất:
1. Một **Law Article Template**: điều luật gồm *yếu tố cấu thành* (chủ thể, hành vi, đối
   tượng, điều kiện khách quan, điều kiện chủ quan) và *hậu quả pháp lý* (mức án).
2. Một tập **Amendment Dimensions**: mở rộng (rõ/ngầm), tái phân bổ, thu hẹp, thêm/bỏ điều
   kiện, tăng/giảm mức, đưa vào/bỏ mức cực đoan.
3. Tích của hai tập cho các cặp *thành phần × kiểu sửa*, rồi **chỉ giữ cặp xuất hiện thật**
   khi rà **cả 12 lần sửa đổi lịch sử** của Bộ luật Hình sự Trung Quốc.

**Kiểm thử "biến hình" (metamorphic testing), không cần nhãn vàng.** Họ giải thích rằng nhãn
do người gán không phải nhãn toà án nên làm vấn đề tính xác thực. Thay vào đó định nghĩa
**quan hệ biến hình**: nếu mức án đổi từ "3–10 năm" sang "trên 10 năm" thì model đạt khi dự
đoán mới vượt 10 năm, không cần biết đáp án đúng. Loại thứ hai là **kiểm thử tối thiểu**:
đổi đúng một chi tiết trong sự việc ("doanh nghiệp nhà nước" → "doanh nghiệp tư nhân"), giữ
nguyên phần còn lại.

**Thiết kế để so sánh công bằng.** Các loại sửa đổi cùng một thành phần **dùng chung điều luật
và vụ án gốc**, để khác biệt giữa loại không bị lẫn bởi sai khác học thuyết hay phân bố dữ
liệu. Chỉ chọn vụ án trong khoảng 04/11/2017–28/02/2021 vì cùng một phiên bản luật.

**Kiểm chứng.** Một GS luật và hai NCS luật. Người soạn bản sửa, người thứ hai duyệt, **xung
đột do GS chốt**. Lương 200 NDT/giờ. **Không báo IAA.** Dữ liệu và mã công bố trên Hugging
Face và GitHub.

**Kết quả.** Các model mặc định về logic cũ; model có mã hoá điều luật tường minh thích nghi
tốt hơn. Họ kết luận cần "temporal legal learning" kiểu timestamp-aware.

### 2.4 LeKUBE (2024) — khung 5 chiều và "locality"

Cập nhật kiến thức pháp lý, cụ thể: 180 điều luật đã sửa của Luật Hình sự và Bộ luật Dân sự
Trung Quốc, kèm 60 điều **không sửa**. SV luật sửa điều luật, GPT-4 sinh câu đúng/sai rồi
**người lọc**; mỗi mẫu được người thứ hai xác nhận. Trả 10 NDT một mẫu, làm được 4–5 mẫu/giờ
(~40–50 NDT/giờ). Không báo IAA.

**Khung đánh giá năm chiều:** chính xác, tổng quát hoá, **locality** (kiến thức không đổi có
bị phá không), khả năng mở rộng, khả năng giữ lại.

**Học được.** "Locality" là cách đặt tên đúng cho vai trò của nhóm T1: **T1 không phải "tra cứu
không mơ hồ", mà là phép đo xem hệ thống có làm hỏng điều không đổi hay không.** Đây là cách
trình bày thuyết phục hơn "đối chứng".

### 2.5 TALD (2026) — cách báo cáo lỗi theo hướng

26.000 bản án dân sự Trung Quốc, tách đúng bản án theo **Bộ luật Dân sự 2021** và bản án theo
luật cũ. Model đạt **0,014–0,237 trên án luật cũ nhưng 0,70–0,843 trên án luật mới**; trong
số lỗi, **69–94% là áp luật mới cho tình huống thuộc luật cũ**. Họ chia lỗi thành ba loại
(cũ→mới, mới→cũ, không liên quan phiên bản).

**Học được.** Báo kết quả **tách theo hướng lỗi**: gold là phiên bản cũ hay mới, và lỗi đi
theo chiều nào. Phần kiểm chứng của họ yếu (hai chuyên gia, không nêu cỡ mẫu), nên đừng
bắt chước chỗ đó.

### 2.6 LexKairos (2026) — tác vụ siêu dữ liệu rẻ, quy mô lớn

Ba nhóm tác vụ, chín tác vụ con. Nhóm 1 sát ViLexTime nhất: *Effective Date Inquiry* (485 mẫu),
*Effective Version Identification* (452), *Effective Status Verification* (480). **Tổng hợp
bằng luật từ siêu dữ liệu**, rồi người lọc trùng và chất lượng. Chỉ chấm accuracy. **Chỉ có
cấp cả văn bản, không xuống điều khoản.** Không báo IAA.

**Học được.** Đây là cách **lấp số lượng mà không độn**: ViLexTime có siêu dữ liệu để sinh hàng
nghìn mẫu tác vụ "version nào hiệu lực tại ngày t" bằng luật, không cần LLM. Gắn nhãn rõ là
**track chẩn đoán sinh tự động**, báo riêng, không tính vào bảng chính.

### 2.7 CALRK-Bench (2026) — biện hộ cho nhóm nhỏ

479 mẫu; trong 100 mẫu nhận biết bối cảnh thời gian, chỉ **8 mẫu về sửa đổi luật** (44 về
tuyên vô hiệu hiến pháp, 48 về án lệ). Họ nêu rõ lý do: thay đổi *có thể phân loại rõ* là
hiếm trong thực tế (498 phán quyết toàn thể trong 30 năm). **Cố ý loại thay đổi mơ hồ hoặc
dần dần** để khách quan, và ghi đó là "clarity bias". Một GS luật rà **lặp lại** định nghĩa và
cấu trúc phương án.

**Học được.** Câu mẫu cho phần Limitations khi T5 nhỏ: *nhóm nhỏ vì hiện tượng hiếm đúng như
bản chất, và tiêu chí loại trừ được nêu rõ*. Họ cũng chạy thử "tiêm ngữ cảnh không liên quan":
điểm tăng tới 4,4%, gợi ý model dựa vào kiến thức tham số.

### 2.8 LegalSearch-R1 (2026) — hình vẽ "model đỉnh ở mốc cutoff"

Bộ tác vụ có chỉ số thời gian. SV luật gán cho mỗi điều luật đã sửa đáng kể một **cửa sổ hiệu
lực (t_from, t_to)**; 16 bộ luật, tác vụ chép điều luật có 13 phiên bản từ 2000–2025. Trả 15
USD/giờ.

**Hình đáng học:** ROUGE-L theo năm của phiên bản — mọi model **đỉnh gần mốc cutoff
(2021–2022) và giảm ở cả hai phía**, trước lẫn sau. Điểm thưởng nhị phân ở ROUGE-L ≥ 0,95.

**Học được.** ViLexTime có thể vẽ đúng hình này: **độ chính xác theo `as_of`, đặt cạnh mốc
cutoff của từng model**. Rẻ, không cần dữ liệu thêm, và là hình chứng minh rõ nhất.

### 2.9 VLegal-Bench (2025–26) — chuẩn quy trình gán nhãn của mảng tiếng Việt

**Quy trình (rất cụ thể):**
- 3 chuyên gia senior (có chứng chỉ luật sư, ≥5 năm) + 8 junior (luật sư hoặc cử nhân năm cuối
  đã đỗ kỳ thi luật sư).
- **Huấn luyện 2 ngày, 50 mẫu pilot mỗi tác vụ có phản hồi tức thời, cổng ≥85% đồng thuận với
  nhãn chuẩn** trước khi gán chính thức.
- **Gán chéo mù mỗi 100 mẫu.**
- **κ 0,89 tính trên nhãn trước khi thảo luận**; đồng thuận ban đầu 92,39%. 794 mẫu bất đồng
  (7,61%): 683 do hai junior tự thống nhất, **111 lên senior** — tập trung ở các tác vụ nhiều
  điều khoản (31, 27, 22 ca ở ba tác vụ).
- Khoảng **1.400 giờ người trong 14 tuần**; trả ~150.000 VNĐ/giờ.
- Phần đánh giá do người: hai junior, mù, thang Likert, κ 0,92.

**Trình bày.** Mục Ethics đầy đủ (ẩn danh, trả công, đồng ý tham gia), mục **kiểm tra nhiễm
dữ liệu** riêng (tìm n-gram trên web, Common Crawl; 1,8% trùng, toàn là văn bản luật bắt buộc),
mục Limitations **nêu thẳng điểm yếu thời gian**: *"luật thường xuyên sửa đổi, bộ dữ liệu tĩnh,
giá trị lâu dài hạn chế"*. Giấy phép CC BY-NC-ND 4.0. Phụ lục B, D, E, G chứa giao diện gán
nhãn, đặc tả model, quy trình gán nhãn, mẫu hướng dẫn.

**Học được — chỗ này quan trọng nhất cho bạn.** Đồng thuận 92,39% của họ không đến từ người gán
giỏi hơn. Nó đến từ **cổng ≥85% trên 50 mẫu pilot có phản hồi trước khi gán chính thức**.
Pilot κ của ViLexTime chỉ 70,0% đồng thuận, và đó là **lượt gán đầu tiên với guideline v1.2
chưa hiệu chỉnh**, tức đúng loại số mà VLegal-Bench chặn lại ở cổng. Xem mục 4, việc 1.

Và câu Limitations của họ là lời mở đầu sẵn cho ViLexTime: một bộ **có chỉ số thời gian**
chính là phần khắc phục điểm yếu mà họ tự nhận.

### 2.10 VLQA (2025) — tỷ lệ sửa thay cho κ

2.162 văn bản, 59.636 điều. **Loại điều đã bãi bỏ** khỏi corpus và loại câu hỏi dẫn tới điều
đã bãi bỏ hoặc không có trong corpus. Hơn 430.000 câu hỏi thô từ trang tư vấn pháp luật →
**3.129** câu. Năm SV luật; **mỗi mẫu hai người gán độc lập**, một chuyên gia rà.

**Thay vì κ, họ báo tỷ lệ chuyên gia sửa:** 74,18% khớp hoàn toàn, 14,83% chỉ sửa điều luật,
3,8% chỉ sửa đáp án, 7,19% sửa cả hai.

**Học được.** (1) Câu hỏi thật lấy từ trang tư vấn pháp luật — đúng nguồn mình đề xuất cho
tập "câu hỏi thật". (2) Bảng tỷ lệ sửa là một cách báo cáo chất lượng **rẻ và đọc được**, nên
báo kèm κ. (3) Bài này là bằng chứng nội địa rằng bộ hiện có **loại** điều đã bãi bỏ — đúng
khoảng trống ViLexTime lấp.

### 2.11 ViHERMES (2026) — gần ViLexTime về miền, và có điều cần sửa trong báo cáo cũ

Mức A (đọc văn bản gốc). Hỏi đáp đa bước trên quy định y tế Việt Nam. **Một "hop" là một bước
phụ thuộc pháp lý**: truy vết sửa đổi, tra định nghĩa, ghép thủ tục liên văn bản.

- Bốn quan hệ pháp lý rút bằng luật theo mẫu ("sửa đổi Điều X", "bổ sung Khoản Y"): **Amends,
  Replaces, Supplements, Refers_To** — trùng với các loại sự kiện trong kho của ViLexTime.
- Id nút có quy ước `DocID::UnitID` để truy vết chuỗi sửa đổi.
- Dựng câu hỏi: gom cụm ngữ nghĩa, lấy bộ ngữ cảnh từ **các văn bản khác nhau**, LLM sinh
  đáp án phải dùng đủ h ngữ cảnh, rồi **kiểm cấu trúc tự động**; chỉ ca mơ hồ mới đến người.
  Annotator có chuyên gia hướng dẫn nhưng **không báo IAA**.
- Test: 5 mức hop × 312 = 1.560.

**Điều khác ViLexTime về bản chất.** Truy vết sửa đổi của họ **ưu tiên nút cuối chuỗi** ("terminal
node preferred as legally applicable"), tức mặc định "áp dụng là bản mới nhất". Không có trường
`as_of`, nên **không đo được trường hợp cần bản cũ** — chính là tình huống mà German, FiscalQA,
TALD và ViLexTime đo.

### 2.12 TimelyRAG / TimelyQABench (2026) — taxonomy có sẵn tên cho các ca của bạn

**Tổng hợp**, 12.000 câu (4 miền: quy định pháp luật, đại học, công ty, điều khoản dịch vụ),
tiếng Hàn, do Llama-3.3-70B sinh. Lý do: kiểm soát mức chồng chéo và tần suất sửa đổi.

**Sáu loại câu hỏi** — đọc kỹ, vì nhiều loại trùng đúng các ca ViLexTime gặp:

| Loại của họ | Tương ứng trong ViLexTime |
|---|---|
| Multi-Version Policy Rules | T2/T3 |
| **Legacy Exception Rules** (quy định cũ còn hiệu lực với một nhóm) | **Điều khoản chuyển tiếp** — mã `transitional_rule` mà model chưa dùng lần nào, người gán B đã gắn 2 lần |
| **Policy Name/Code Revisions** | **Đổi tên cơ quan** — 139 lần chuyển của T3, thuộc đợt sắp xếp bộ máy 2025 |
| Emergency/Temporary Rules | Chưa có |
| Historical, Retrospective Fact | `as_of` ở quá khứ |
| Implicit Time Context | Chưa có — câu hỏi không nêu ngày nhưng ngữ cảnh ngầm chứa |

**Gold** = "tập tối thiểu các phiên bản cần để suy ra đáp án"; các phiên bản còn lại trong cùng
họ là **hard negative**. Kiểm chất lượng bằng bốn chiều (độ liên quan, khả suy diễn, độ nhạy
thời gian, đặc thù miền) và **đồng thuận giữa ba model** (GPT-4o, Claude 3.7, Qwen 2.5-72B);
50 mẫu người kiểm khớp (4,74 người so với 4,93 LLM).

**Con số đáng mượn:** **độ tương đồng ngữ nghĩa trung bình giữa phiên bản** là 0,61–0,73 cho
TimelyQABench so với 0,35–0,36 cho CRAG và RealTimeQA. Đây là **cách định lượng "khó vì các
phiên bản giống nhau"**, đúng thứ trường `similarity` mới của ViLexTime đo.

**Không nên bắt chước.** Dữ liệu tổng hợp, và chính họ nêu giới hạn: câu hỏi tổng hợp có thể
không phản ánh hành vi tìm kiếm thật.

### 2.13 SAT-Graph RAG và Deterministic Legal Agents (de Martim, 2025) — **kiến trúc, không phải benchmark**

Cả hai là đặc tả kiến trúc, **không có đánh giá định lượng**, và SAT-Graph tự nhận: *"việc kiểm
chứng định lượng chặt chẽ đòi hỏi một benchmark chuyên biệt, hiện là một khoảng trống đáng kể"*.

Câu này **là lời mở đầu cho phần động cơ của ViLexTime**: một bộ dữ liệu đúng khoảng trống mà
các nhà thiết kế hệ thống thời gian tự nhận là còn thiếu.

**Mô hình dữ liệu đáng học:**
- Tách **Work** (thực thể trừu tượng, ổn định) khỏi **Expression** (bản có ngày), theo LRMoo.
- Mỗi phiên bản có **hai khoảng thời gian khác nhau**: `validityInterval` (có hiệu lực pháp lý)
  và `applicabilityInterval` (có thể áp dụng thực tế — để biểu diễn vacatio legis, hiệu lực
  chậm). Điều kiện chọn phiên bản: `valid_start ≤ t < coalesce(valid_end, +∞)`.
- Tham số `observerTime` cho **thời gian giao dịch**: hỏi "tại ngày t, hệ thống *biết* gì"
  tách khỏi "sự thật tại ngày t".
- **Mô hình tổng hợp, không phải thành phần:** khi một điều con đổi, phiên bản cha mới được
  tạo bằng cách **gom** phiên bản con mới với phiên bản cũ của các anh em không đổi. Đây đúng
  là cơ chế cần cho nhóm T6 "mất hiệu lực vì cha bị bãi bỏ".
- Hành động lập pháp (ban hành, sửa, bãi bỏ, đính chính) là **nút hạng nhất** có
  `producesVersionIds` và `terminatesVersionIds`.
- Bộ nguyên thuỷ API: `getValidVersions(itemId, at?, observerTime?)`,
  `getItemVersions`, `getItemHistory`, `queryActions`, `getVersionAncestors(versionId, at?)`…

**Học được.** `retrieved_at` của ViLexTime chính là thời gian giao dịch. Việc tách
`validityInterval` khỏi `applicabilityInterval` là **câu trả lời có sẵn** cho ca "đã ký nhưng
chưa có hiệu lực" (mới thêm trường `pending` cho nó).

### 2.14 HoH (2025)

Mức C. Dựng QA lớn bằng **diff mức token kết hợp LLM** để theo dõi tri thức đổi theo thời
gian; ghép thông tin cũ với thông tin mới trong cùng nguồn truy xuất. Kết luận: thông tin cũ
làm giảm độ chính xác và có thể dẫn model tới đầu ra có hại **dù thông tin mới có sẵn**. Đây
là họ hàng về ý tưởng với cách ViLexTime dùng `difflib` để tìm chỗ thay đổi.

---

## 3. Những mẫu lặp lại qua các bài

**(1) Máy tìm chỗ đổi, người quyết câu hỏi.** FiscalQA (script tìm điểm chuyển), German (LLM
sinh rồi người lọc), LeKUBE, HoH (diff). ViLexTime đúng hướng chung.

**(2) Chất lượng nhãn thường được báo yếu.** Trong 12 bộ ở bảng 1, chỉ **một** báo κ giữa
người với người. Nhiều bộ không báo gì (LexKairos, LeKUBE, LawShift), hoặc báo gián tiếp (VLQA).
Nên ViLexTime có κ pilot thật đã nổi bật hơn mặt bằng, kể cả khi con số thấp.

**(3) Người ta báo kết quả theo hướng lỗi.** TALD tách cũ→mới / mới→cũ; CALRK tách trước/sau
thay đổi (0,31 so với 0,70); German tách tiền cutoff/sau cutoff.

**(4) Giám khảo LLM bị tránh hoặc kiểm tra kỹ.** FiscalQA bỏ hẳn; German báo κ giám khảo **theo
từng chiều** (0,860 so với 0,549); VLegal dùng người.

**(5) Kiểm soát nhiễm dữ liệu là mục riêng.** FiscalQA (bộ lọc kiến thức tham số, canary
GUID), VLegal (n-gram, Common Crawl, 1,8%).

**(6) Lọc "giá trị không đổi qua phiên bản".** FiscalQA bằng regex; German bằng
"editorial-only"; ViLexTime bằng `cosmetic_change` và "đáp án trùng nhau ở các mốc". Cả ba
đang giải cùng một bài toán.

**(7) Phễu có số lượng ở từng bước** là hình bắt buộc: German 697→312, FiscalQA 221→209,
CALRK 569→293→100, LexKairos 4.000→260→180.

**(8) Limitations nêu thẳng.** VLegal tự nhận bộ tĩnh; FiscalQA nêu chế độ lỗi chưa phủ;
CALRK nêu "clarity bias".

---

## 4. Việc cụ thể cho ViLexTime, xếp theo ưu tiên

### Ưu tiên 1 — trước khi gán nhãn lại (đang chặn)

**Việc 1. Thêm cổng hiệu chỉnh trước khi gán nhãn sản xuất.** Theo VLegal-Bench: pilot **50 mẫu
có phản hồi tức thời**, cổng **≥85% đồng thuận với nhãn chuẩn** do cố vấn ký, rồi mới gán chính
thức. Pilot 300 dòng vừa xong là lượt đầu *không có cổng*, và 70,0% đúng là mức mà cổng sẽ
chặn. Đây là lý do mạnh nhất để **không gán lại ngay**: sau khi guideline v2.0 ra, chạy cổng,
rồi mới gán lại 90 dòng.

**Việc 2. Quy trình giải quyết bất đồng hai bậc.** Theo VLegal: hai người tự thảo luận trước,
chỉ ca còn lại lên cố vấn. Họ chốt 683/794 mà không cần senior. ViLexTime nên ghi sẵn quy trình
này vào guideline và **báo số ca ở mỗi bậc**.

**Việc 3. Tập trung ca khó vào cố vấn.** VLegal cho thấy ca lên senior tập trung ở tác vụ
nhiều điều khoản. Với ViLexTime, tương ứng là T6 và T3, đúng với hàng audit tier 1–2.

### Ưu tiên 2 — thiết kế dữ liệu

**Việc 4. Dựng taxonomy thay đổi theo phương pháp LawShift.** Template thành phần × kiểu sửa,
**chỉ giữ cặp xuất hiện thật** khi rà lịch sử sửa đổi. ViLexTime có sẵn `changed_span` và 19.182
event đã áp; có thể phân loại tự động (đổi số tiền, đổi thời hạn, đổi chủ thể, đổi tên cơ quan, thêm
điều kiện…). Kết quả là trường `change_type` trên mọi dòng, **đúng ý "tách hiện tượng khỏi
trường"** trong báo cáo refactor, kèm tiền lệ NeurIPS.

**Việc 5. Hai bộ lọc của FiscalQA.** (a) *Giá trị vàng không xuất hiện nguyên văn trong bản
hiện hành* — bằng regex, không cần LLM. (b) *Lọc kiến thức tham số*: bỏ câu mà model đoán
đúng không cần truy xuất. **Chỉ áp cho T2–T6**, không áp T1, vì T1 cố ý dễ. Thêm canary GUID
vào file kiểm.

**Việc 6. Kiểm thử bất biến bằng dòng twin.** Mượn ý "quan hệ biến hình" của LawShift:
hỏi cùng câu ở hai mốc **trong cùng một khoảng hiệu lực** thì đáp án phải giống; qua ranh giới
thì phải đổi. ViLexTime đã có sẵn dòng giữa khoảng làm twin, nên chỉ cần thêm chỉ số **TCS theo
bất biến**, giống kiểm tra nhất quán của TimeQA (chỉ 66% câu đúng giữ nguyên đúng khi đổi mốc).

**Việc 7. Thiết kế so sánh công bằng.** Theo LawShift, các nhóm cần so sánh với nhau nên **dùng
chung văn bản và điều luật khi có thể**, để chênh lệch không lẫn với sai khác học thuyết. Với
ViLexTime: khi so T6 trực tiếp và T6 lan truyền, chọn các cặp từ **cùng văn bản đích**.

**Việc 8. Track chẩn đoán sinh tự động, theo LexKairos.** Các tác vụ "ngày có hiệu lực",
"phiên bản nào hiệu lực tại ngày t", "phiên bản X có hiệu lực tại ngày t không" **sinh được
bằng luật** từ siêu dữ liệu. Thêm vài nghìn mẫu, gắn nhãn `track = metadata`, **báo riêng**.
Đây là cách tăng số lượng mà không độn lineage, và không có nhãn nào do model viết.

**Việc 9. Đặt lại tên T1 là "locality".** Theo LeKUBE: T1 đo việc hệ thống có **làm hỏng điều
không đổi** không. Trình bày thuyết phục hơn "đối chứng".

### Ưu tiên 3 — đánh giá

**Việc 10. Thí nghiệm có kiểm soát ba/bốn điều kiện như FiscalQA.** A: LLM không truy xuất.
B: RAG chỉ có bản hiện hành (báo **provenance**). C-oracle: biết sẵn phiên bản đúng. C-prod:
truy xuất đầy đủ. Khoảng cách giữa các điều kiện cho thấy nút cổ chai ở **truy hồi điều luật**
hay **chọn phiên bản**. Kèm H1–H4 dạng có thể bác bỏ, và bootstrap theo lineage (ViLexTime đã dự kiến).

**Việc 11. Hình "độ chính xác theo `as_of`, đặt cạnh mốc cutoff".** Theo LegalSearch-R1: model
đỉnh gần cutoff và giảm cả hai phía. Rẻ, không cần dữ liệu thêm.

**Việc 12. Chấm xác định là chính, giám khảo là phụ.** FiscalQA bỏ giám khảo vì thiên lệch
thời gian; German báo κ giám khảo theo từng chiều. ViLexTime đã chọn chấm tương phản; thêm
**κ giám khảo theo chiều (kết luận, căn cứ, phiên bản)** nếu dùng giám khảo, vì căn cứ pháp lý
là chiều dễ trượt nhất (0,549 ở German).

**Việc 13. Báo kết quả theo hướng lỗi.** Theo TALD: gold là phiên bản cũ hay mới, lỗi đi
chiều nào. Kèm bảng độ tương đồng giữa phiên bản (kiểu TimelyRAG, so với 0,35 của CRAG) để
chứng minh "các phiên bản thật sự giống nhau".

### Ưu tiên 4 — trình bày

**Việc 14. Datasheet và bài báo nên có đủ các mục mà các bài tốt cùng có:**

| Mục | Mẫu | ViLexTime hiện có? |
|---|---|---|
| Phễu có số lượng ở mọi bước | German, FiscalQA, CALRK | Có số, chưa có hình |
| **Bảng lý do loại kèm tỷ lệ nhận** | German | Có `rejected_reason`, chưa tổng hợp |
| **Bảng tỷ lệ người sửa** | VLQA, TimeQA (41,6%) | Chưa |
| Đồng thuận trước thảo luận | VLegal | **Có** (nhãn thô) |
| Mục kiểm tra nhiễm dữ liệu | VLegal, FiscalQA | Chưa |
| Ethics: trả công, đồng ý tham gia | VLegal (150.000 VNĐ/giờ), LawShift (200 NDT/giờ) | Chưa. Người gán là chính các tác giả, không được trả công — cần nói thẳng |
| Khai AI | German | Có phần vai trò LLM |
| Limitations nêu thẳng | VLegal, FiscalQA, CALRK | Có một phần |
| Canary GUID, giấy phép, kho mã | FiscalQA | Giấy phép có; canary chưa |

**Việc 15. Câu định vị mượn được.** Đặt SAT-Graph RAG làm động cơ: *các nhà thiết kế hệ thống
truy hồi theo thời gian tự nhận thiếu benchmark định lượng*. Đặt VLegal-Bench làm điểm so
sánh: *bộ tiếng Việt chuẩn nhất nhưng tĩnh, và tự nhận hạn chế về hiệu lực*.

---

## 5. Những chỗ sửa lại báo cáo trước

| Báo cáo cũ ghi | Đọc kỹ thấy |
|---|---|
| ViHERMES: "Không có `as_of`" và "312 × 5 mức là tiền lệ cho thiết kế 5 × 300 nhóm" | **Có truy vết sửa đổi** (Amends/Replaces/Supplements), nhưng ưu tiên nút cuối chuỗi nên đúng là không có `as_of`. Và **5 mức là số hop, không phải 5 hiện tượng**, nên *không* là tiền lệ cho 5 nhóm × 300 |
| German: "không có IAA" | Đúng, nhưng có κ giám khảo 0,751 (0,549 ở căn cứ pháp lý); đừng nhầm hai thứ |
| FiscalQA: "1 chuyên gia thuế" | Đúng: một chuyên gia **duyệt toàn bộ 209 câu**, nhưng cũng có bộ lọc xác định và kiểm tham số |
| "Chưa bộ nào kiểm tập hồi tố (T5)" | Chưa tìm thấy bộ có nhóm hồi tố riêng. **Tuy nhiên** TimelyRAG có loại "Legacy Exception" và LegalSearch-R1 có cửa sổ hiệu lực; không bộ nào xử lý đúng Điều 152 |

Và một điều báo cáo cũ **chưa có**: **LawShift (NeurIPS 2025), TimelyRAG, LeKUBE, LegalSearch-R1,
SAT-Graph RAG** chưa nằm trong bảng so sánh bảy bộ. Bảng 1 ở trên đã thay thế.

---

## 6. Phần còn mở

- **Chưa đọc kỹ:** phần kết quả và phụ lục của LawShift; "Beyond Probabilistic Similarity".
- **Chưa kiểm:** mọi con số mức B với bài gốc. Trước khi trích vào bài báo, kiểm lại.
- **Chưa tìm được:** bộ có nhóm hồi tố theo luật Việt Nam; bộ có hiệu lực **cấp khoản/điểm** ngoài
  ViLexTime. Cần một lượt tìm có mục tiêu trước khi khẳng định "đầu tiên".
