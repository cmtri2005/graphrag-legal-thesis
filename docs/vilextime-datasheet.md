# ViLexTime — Datasheet

Theo khung *Datasheets for Datasets* (Gebru và cộng sự, 2021). Tài liệu này mô tả bản
phát hành `data/derived/vilextime/release.jsonl` (schema 1.4.0). Mã băm của bản phát
hành và của mọi đầu vào đã commit nằm ở `data/vilextime/manifest.json`, file này do
`scripts/check/check_release.py --manifest` ghi.

Trạng thái: **v1.0 chưa đóng băng.** Trước khi dùng số liệu cho khóa luận, xem mục 7
"Chưa xong".

## 1. Động cơ

ViLexTime là bộ hỏi đáp pháp luật Việt Nam theo mốc hiệu lực. Đầu vào của mỗi dòng
gồm câu hỏi *x* và mốc thời gian *t* (`as_of`). Đầu ra đúng gồm:
- nội dung điều khoản có hiệu lực tại *t*;
- bằng chứng *E* là đơn vị văn bản có hiệu lực tại *t* (công thức 1 của đề cương).

Bộ dữ liệu phục vụ ba câu hỏi nghiên cứu:
- RQ1: LLM và RAG dùng sai phiên bản thường xuyên đến đâu;
- RQ2: đồ thị tri thức thời gian có giảm lỗi đó không;
- RQ3: lợi ích đến từ đồ thị hay chỉ từ lọc thời gian.

Người làm là hai sinh viên của khóa luận (mã A, B) và hai model: `claude-opus-5-5` và
`deepseek-flash` (DeepSeek). Vai trò của model ghi ở mục 3.

## 2. Thành phần

Mỗi dòng là một cặp (câu hỏi, mốc). Một câu hỏi thuộc về một **lineage**, tức một điều
khoản cùng chuỗi phiên bản của nó. Câu hỏi không chứa ngày, nên một câu phục vụ được
mọi mốc.

- **Nhóm:**
  - T1: một phiên bản;
  - T2: cặp tương phản;
  - T3: chuỗi ≥ 3 phiên bản;
  - T4: hai phiên bản gần giống. Từ 07/10 là lát `near_identical` của T2, có suất riêng
    150 dòng từ 11/10;
  - T5: hiệu lực trở về trước theo Điều 152 Luật 80/2015/QH13, hoặc Điều 55 Luật 64/2025/QH15
    với văn bản ký từ 01/04/2025 (nguyên tắc không đổi, luật sư 12/10);
  - T6: hết hiệu lực một phần ở cấp Khoản/Điểm.
- **Chế độ `as_of`:**
  - `ranh_gioi`: sát lần chuyển phiên bản;
  - `giua_khoang`: cách hai đầu khoảng hiệu lực ≥ 30 ngày. Đây là **bảng kết quả chính**;
  - `sau_het_hieu_luc`: sau khi văn bản đích hết hiệu lực toàn bộ, không có đáp án;
  - `truoc_hieu_luc` (chỉ T2, từ 11/10): dòng trước của cặp, hỏi lại 30 ngày trước khi
    phiên bản sau có hiệu lực, khi văn bản sửa đổi đã ký. Đáp án vẫn là phiên bản cũ.
- **Split:**
  - chia theo văn bản đích: dev khoảng 20%, test khoảng 80%;
  - văn bản có dòng T5 luôn vào test;
  - một lineage hay một văn bản không bao giờ nằm ở hai split;
  - scorer mặc định chỉ chấm test.

(Bảng số liệu: mục 8.)

## 3. Cách dựng, và ai làm gì

Nguyên tắc là **gold dẫn xuất từ dữ liệu**. Đáp án, `version_id`, `accepted_evidence` và
ngày chuyển đều lấy từ chuỗi phiên bản (`data/derived/versions.jsonl`, L2–L3). Chuỗi này
được dựng từ văn bản gốc trên vbpl.vn và các câu lệnh sửa đổi, bãi bỏ mà pipeline trích
ra. Mỗi transition truy ngược được về `event_id`, văn bản tác động và câu lệnh.

Vai trò của LLM **rộng hơn** câu "LLM chỉ hỗ trợ diễn đạt câu hỏi" của đề cương:

| Phần | Ai làm | Ghi ở đâu |
|---|---|---|
| Câu hỏi | `claude-opus-5-5` viết khoảng hai phần ba, `deepseek-flash` khoảng một phần ba (các lô 07/10 và 11/10: T6 mới, lát gần giống của T2). Một số câu model tự viết lại, một số câu người sửa, một câu do `gpt-oss-120b` (Groq) viết (số liệu ở mục 8) | `question_source`, `data/vilextime/questions.jsonl` |
| Đáp án ngắn (`short_answer`, được Accuracy/EM/F1/TCS chấm) | `claude-opus-5-5` viết, phải là một đoạn của lời văn gold | `data/vilextime/short_answers.jsonl`, trường `by` |
| Nhãn ngoài bộ kiểm chéo | model gán trước, người audit theo mẫu và theo luật bắt buộc | `data/review/labels.tsv` |
| Quyết định loại lineage | model đề xuất, người xác nhận khi audit | `data/vilextime/dropped.jsonl` |
| Bộ kiểm chéo κ (300 dòng) | chỉ người (A, B), gán mù | `data/review/crosscheck_A/B.tsv` |
| Phân xử cờ hiệu lực, ngày hết hiệu lực của văn bản | model đề xuất kèm câu nguồn (`method: llm_reviewed`), người audit | `data/review/validity_queue.tsv`, `data/review/temporal_candidates.jsonl` |

Hệ quả: nếu một baseline dùng model họ Claude, nó trả lời câu hỏi do chính Claude viết
và bị chấm bằng đáp án ngắn do Claude chọn; với DeepSeek cũng vậy ở các câu nó viết. Người
viết lại trùng gần khít với nhóm (H3: 144/150 lineage do DeepSeek viết; T1, T2 thường, T3,
T5 do Claude viết hết), nên thiên lệch này hiện ra như khác biệt giữa các nhóm. **Chốt
11/10 (ADR 0004 §3):** cột kết quả chính và LLM giám khảo dùng LLM không thuộc họ Claude
và không thuộc họ DeepSeek; hai họ này chỉ chạy ở bảng phụ, báo tách theo `question_source`.

**Phễu chọn lineage** (G2, đếm lại 11/10): 1.490 lineage được viết câu hỏi → 299 bị bộ kiểm
tự động loại (249 `insufficient_context` do chính người viết đánh, 38 `copies_the_answer`,
12 bị cắt cụt) → 1.191 qua → 32 bị loại sau khi gán nhãn → số lineage trong bản phát
hành ở mục 8 (chọn theo thứ hạng đến khi đủ quota). Như vậy có thiên
lệch chọn về phía điều khoản dễ diễn đạt thành câu hỏi. Lineage bị nối nhầm (hai quy định
khác chủ đề chung số thứ tự, khoảng 7% ở T2) bị loại ở bước viết câu.

## 4. Khuyến nghị khi dùng và báo kết quả

- Báo **bảng `giua_khoang`** làm kết quả chính. `ranh_gioi` là phép thử ngày chuyển;
  `sau_het_hieu_luc` là phép thử siêu dữ liệu cấp văn bản. `truoc_hieu_luc` là phép thử
  luật đã ký mà chưa có hiệu lực: câu lệnh sửa đổi tương lai nằm trong lớp A ở cả 153
  dòng, nên baseline không xét ngày bị lừa; bộ lọc cấp văn bản của B7 loại cả 153, nên
  chế độ này không tách B7 với hệ thống đề xuất. Ngày ký lấy từ cổng, 30 dòng đang chờ
  kiểm tay (`data/review/audit_truoc_hieu_luc.tsv`).
- **Accuracy và TCS dùng bản tương phản** (chốt 29/09): câu trả lời phải chứa đoạn gold
  và không được chứa đoạn chỉ phiên bản khác có. Câu trả lời liệt kê mọi phiên bản
  (probe `hedge`) đạt 0,951 theo định nghĩa cũ nhưng thấp hẳn theo định nghĩa mới.
  `accuracy_lenient` và `tcs_lenient` chỉ để so sánh.
- **RQ3:** kết luận bằng TVER, VCR và TV-Recall@1, với B7+ (lọc theo phiên bản, không
  dùng đồ thị) làm phép đối chứng chính. TV-Recall@k với k ≥ 5 không phân biệt được,
  vì câu lệnh sửa đổi hay bãi bỏ ở lớp A còn hiệu lực theo ngày cấp văn bản.
- **Trích dẫn:**
  - báo `citation_coverage` và `tver_strict` cạnh TVER, vì không trích dẫn thì né được TVER;
  - trích dẫn dạng chữ được quy về điều khoản;
  - trích dẫn dạng chữ không mang phiên bản, nên VCR không xác định được cho B1.
- **EM** gần như bằng 0 với câu trả lời sinh tự do (oracle đạt EM 0, F1 0,586), nên báo F1.
- **Tách số theo nhóm và chế độ `as_of`.** Riêng T3 và T5 phải báo riêng theo chế độ,
  kèm bảng probe theo nhóm (G3; `score_vilextime.py --probes --out`).
- **T5 là tập chẩn đoán, không vào con số chung** (11/10). Con số "all" của scorer bỏ
  T5 (`DIAGNOSTIC`). T5 báo trên dòng riêng, bằng số đếm theo văn bản tác động; không
  báo phần trăm, không kiểm định, không xếp hạng hệ thống.
- **Khoảng tin cậy:** bootstrap theo lineage, không theo dòng, vì các dòng của một
  lineage không độc lập.
- **TV-Recall@k** là định nghĩa lại của công thức 9: trúng khi lấy được đúng
  `version_id` hoặc một đơn vị trong `accepted_evidence`. Công thức 9 như đang viết
  thì trùng với Recall@k.

## 5. Lỗi đã biết và giới hạn

- **Gold dẫn xuất từ chính chuỗi phiên bản mà hệ thống đề xuất dùng** (N1). Lỗi và bỏ sót
  của KG không hiện ra trên bộ này; recall của L2 đo được 62,2%. Tập con gold độc lập
  (plan J7) là bảng đối chiếu.
- **Lỗi hiệu lực chưa dò được:** xem mục 8. Tỷ lệ báo ở đó là **cận dưới**, vì bộ dò
  không thấy được lần sửa đổi mà L2 không trích ra event nào.
- **Độ phủ hiện tượng** (N4):
  - mọi transition là `amend` hoặc `repeal`, không có dòng nào kiểm `supplement` hay `replace`;
  - H3 (mất hiệu lực vì nút cha bị bãi bỏ) có 150 lineage từ bản phát hành 11/10 (trước đó 12);
  - T5 đến từ 3 văn bản tác động.

  Kết luận về T5 chỉ ở mức minh họa.
- **Ngày ranh giới để lộ thông tin** (N3):
  - T1 từng hỏi ở ngày bắt đầu + 1; từ 07/10 ngày hỏi rải trong 30 ngày đầu (`spread_as_of`);
  - T5 ở chế độ giữa khoảng thường nằm sát một lần chuyển;
  - từ 29/09, T3 hỏi ở ngày trước mỗi lần chuyển, như T2.
- **Đáp án ở câu dẫn** (V3): ở một số dòng, đáp án ngắn nằm ở câu dẫn của khoản cha chứ
  không ở chính đơn vị gold (khung phạt của nghị định xử phạt). Recall@k chỉ tính đơn vị gold.
- **Khuôn câu lặp** (V4): đo 11/10 trên 653 câu hỏi của bản phát hành, 5 cụm mở đầu
  (4 từ đầu) chiếm 19%, riêng "theo quy định về" 13%. Bản 29/09 là khoảng 55%.
- **Điều khoản chuyển tiếp** (V5) có thể giữ quy định cũ cho một số quan hệ. Audit có bước
  kiểm riêng, và mọi dòng có dấu hiệu này đều bắt buộc audit.
- **Bỏ cấp huyện từ 01/07/2025** (V6) được xử lý bằng văn bản chuyển tiếp liên ngành,
  không bằng lệnh sửa từng điều. Dòng hỏi sau mốc này mà còn nói "cấp huyện" bắt buộc
  audit; văn bản chuyển tiếp có thể nằm ngoài corpus.
- **Siêu dữ liệu cổng:**
  - cổng giữ một số văn bản hai lần, ví dụ 19/2012/QH13 với hai ngày hiệu lực khác nhau;
  - có văn bản mà cổng vẫn để "Còn hiệu lực" dù đã bị thay thế. Các văn bản đã tìm ra được
    sửa bằng quyết định `effective_to` có câu nguồn;
  - `citation` của một số điều khoản không có Điều, vì văn bản cũ đánh số theo mục, nên
    trích dẫn dạng chữ không phân giải được.
- **Miền:** `domain` lấy từ tìm kiếm seed, nếu không có thì từ phân loại lĩnh vực và ngành
  của cổng. Bộ dữ liệu thực tế đa miền, không chỉ bốn miền của đề cương.

## 6. Chỗ lệch với đề cương đã nộp

Bản UIT đã nộp không sửa được, nên khóa luận phải công bố các chỗ lệch sau (N6):

| Đề cương | Bộ dữ liệu | Căn cứ |
|---|---|---|
| "1.150 câu hỏi" | 1.225 **dòng** (câu hỏi, mốc) ở chế độ ranh giới, trong khung 1.100–1.300; số câu hỏi khác nhau bằng số lineage (653, mục 8). Còn chờ khoa xác nhận "câu" là dòng | ADR 0003 Follow-Up 24/09; plan GĐ4 07/10 |
| "LLM chỉ hỗ trợ diễn đạt câu hỏi" | model viết câu hỏi, đáp án ngắn, nhãn đầu, đề xuất loại (mục 3) | plan GĐ4, 24/09 và 28/09 |
| T5 "có lợi cho đối tượng áp dụng", 50 câu | T5 theo Điều 152, bỏ vế "có lợi"; số câu là số ca luật sư xác nhận, phần thiếu chuyển sang T6 | quyết định Q3, 20/09 |
| κ ≥ 0,6 trên "toàn bộ T3, T4, T5, T6" | 300 dòng: T2 50 + lát gần giống 50, T3 50, toàn bộ T5, T6 phần còn lại tới 150 chia theo tỷ lệ H3/trực tiếp. Thước đo chính là AC1 ≥ 0,80 và p_neg ≥ 0,60 (AC1 chọn sau pilot 07/10/2026, không đăng ký trước); κ báo kèm | quyết định Q2 20/09, dựng lại 11/10 |
| Công thức 9 (TV-Recall@k) | định nghĩa lại theo `version_id`/`accepted_evidence` (mục 4) | plan GĐ4, V7 |
| Accuracy dạng "â = a*" | Accuracy tương phản trên đáp án ngắn | quyết định 29/09 |
| Kiểm định thủ công | κ giữa hai người; nhãn model có audit của người | hướng dẫn §5–§6 |
| Bốn miền | đa miền (mục 5) | JUDGE N5 |

## 7. Phân phối, giấy phép, bảo trì

- **Giấy phép:** CC BY 4.0 cho câu hỏi, đáp án ngắn, nhãn và các trường dẫn xuất
  (`data/vilextime/LICENSE`). Lời văn pháp luật lấy từ vbpl.vn, kể cả văn bản hợp nhất, không
  thuộc đối tượng bảo hộ theo Điều 15 Luật SHTT; phát hành phần nhóm viết theo CC BY 4.0 và thu
  thập tự động từ vbpl.vn không vướng quy định nào (luật sư xác nhận 12/10/2026).
- **Tái lập:** `release.jsonl` là file dẫn xuất (gitignore). Chuỗi dựng ghi ở plan GĐ4 (J3).
  Mã băm của mọi thứ dùng để dựng nằm ở `data/vilextime/manifest.json`.
- **Phiên bản:** theo ADR 0003 §8. Đổi gold hay chuyển dòng giữa các split là MAJOR; thêm
  trường hay thêm mã là MINOR.
- **Chưa xong** (plan GĐ4, J6–J8; cập nhật 11/10):
  - hướng dẫn v2.0 (T6 theo phán quyết chuyển chỗ 05/10), trước khi gán T6;
  - gán bộ kiểm chéo (A 134 dòng, B 135 dòng còn trống), AC1/κ, hoà giải D5;
  - nhãn cho 276 dòng T6 chưa có nhãn nào (chờ hướng dẫn v2.0);
  - audit 375 nhãn bắt buộc trên dòng đang phát hành;
  - T5: luật sư chốt cả 8 văn bản và 19 lineage trong bản phát hành ngày 12/10. Cả 19 đúng về
    mốc hồi tố; 5 lineage có lỗi câu hỏi: loại 2 (`dropped.jsonl`), viết lại 3 câu hỏi
    (`questions.jsonl`, `edited_at` 12/10) chờ luật sư xem lại. T5 còn 17 lineage, 34 dòng ranh
    giới sau khi dựng lại; T6 nhận 4 dòng thiếu theo quy tắc chọn;
  - phân xử các cờ hiệu lực của lineage κ sau D4, hàng đợi chuyển chỗ (20 dòng);
  - kiểm 30 dòng ngày ký của `truoc_hieu_luc`;
  - tập con gold độc lập;
  - tag `vilextime-v1.0`.

## 8. Số liệu

Số liệu tính trên bản phát hành dựng lại ngày 11/10 (schema 1.4.0, ngày chụp corpus 17/09/2026),
trừ mục "Bộ dò hiệu lực" là kết quả đợt 29/09. `data/vilextime/manifest.json` ghi mã băm
của bản này.

### Kích thước và split

Bản phát hành dựng ngày 11/10 có 2.730 dòng, 653 lineage (tức 653 câu hỏi khác nhau) và 503 văn bản đích. Chia theo lineage:
dev 119, test 534.

Số dòng theo nhóm, chế độ `as_of` và split (dev / test). T4 đã gộp vào T2 từ 07/10; từ 11/10 lát `near_identical` (T4 cũ) có suất riêng 150 dòng trong 450 dòng T2:

| Nhóm | Lineage | `ranh_gioi` | `giua_khoang` | `truoc_hieu_luc` | `sau_het_hieu_luc` |
|---|---:|---:|---:|---:|---:|
| T1 | 150 | 20 / 130 | 20 / 130 | – | 5 / 44 |
| T2 | 225 | 96 / 354 | 96 / 354 | 34 / 119 | 10 / 46 |
| T3 | 65 | 39 / 160 | 39 / 160 | – | 1 / 14 |
| T5 | 19 | 0 / 38 | 0 / 38 | – | 0 / 7 |
| T6 | 194 | 76 / 312 | 76 / 312 | – | – |
| **Tổng** | **653** | **1.225** | **1.225** | **153** | **127** |

**Quota.** Chế độ `ranh_gioi` có 1.225 dòng (07/10, trong khung 1.100–1.300 của đề cương):
- T1 150, T3 199;
- T2 450 = 300 dòng thường + 150 dòng gần giống (75 cặp, `near_identical`, T4 150 của Bảng 1). Gộp T4 ngày 07/10 không chừa suất, nên lát này đứng cuối bảng xếp hạng và bản 11/10 đầu tiên không có dòng nào;
- T5 có 38 dòng, T6 nhận phần thiếu (quyết định Q3): T6 388 = 300 dòng H3 (bãi bỏ qua nút cha) + 88 dòng bãi bỏ trực tiếp.

**Dòng không có đáp án:** 388 dòng `provision_repealed` (T6) và 127 dòng `document_repealed`. Có 66 lineage không có dòng `sau_het_hieu_luc` vì không tìm được câu chấm dứt trong corpus.

**Tỷ lệ dev trên dòng ranh giới:** T1 13,3% · T2 21,3% · T3 19,6% · T5 0% (luôn vào test) · T6 19,6%.

### Ai viết gì (dòng ranh giới)

- **Câu hỏi** (theo lineage, 653):
  - `claude-opus-5-5` viết 389 câu, tự viết lại 35 câu;
  - `deepseek-flash` viết 225 câu (450 dòng ranh giới);
  - người sửa 3 câu;
  - `gpt-oss-120b` viết 1 câu.
- **Đáp án ngắn:** 1.031 phiên bản dùng trong bản phát hành, đều do `claude-opus-5-5` viết.
- **Nhãn trên dòng ranh giới ngoài bộ kiểm chéo:** 662 nhãn model, 98 nhãn người (bản
  Excel). 375 nhãn bắt buộc audit, 0 đã audit. T6 có 276 dòng chưa có nhãn nào.
- **Lineage bị loại:** 32 lineage, đều do model đề xuất (other 11, group_mismatch 9,
  gold_wrong 6, question_ambiguous 4, question_leaks 1, unanswerable_as_asked 1).

### Bộ dò hiệu lực (J2) và sửa gốc (J3)

**Event được áp.** Số event được áp tăng từ 18.840 lên 19.182. Mẫu 30 event mới được áp có 29/30 đúng nội dung (Wilson 95% [83,3; 99,4]).

**Văn bản hết hiệu lực mà cổng chưa ghi.** 9 văn bản được sửa bằng quyết định `effective_to` có trích câu nguồn:
- 176/2013/NĐ-CP, 147/2014/TT-BTC, 47/2020/NĐ-CP;
- 09/2017/TT-BLĐTBXH, 28/2018/TT-BNNPTNT, 135/2004/NĐ-CP;
- 62/2014/QH13, 81/CP (1995), 50/2016/TT-BGTVT.

**Cờ `missed_event` ngoài bộ κ.** 32 cờ, trong đó 13 cờ đúng (10 lineage):
- dòng anh em sai: dời về trước ngày của event bị bỏ sót;
- dòng ranh giới sai: loại lineage.

**Loại thêm trong đợt 29/09:**
- 5 lineage là điều khoản hiệu lực thi hành;
- 3 cặp hỏi sau ngày chụp corpus.

**Còn chờ D4:** 18 cờ `missed_event` và 8 cờ `document_ended` thuộc lineage κ. Tỷ lệ lỗi báo ở đây là cận dưới (mục 5).

### Hiện tượng

- Transition của dòng ranh giới: 906 transition, đều là `amend`. Việc bãi bỏ được thể hiện bằng dòng không có đáp án.
- H3 (mất hiệu lực theo nút cha): 150 lineage (300 dòng); bãi bỏ trực tiếp: 44 lineage (88 dòng).
- T5: 19 lineage, đến từ 3 văn bản tác động là 65/2025/TT-BQP, 12/2015/NĐ-CP và 119/2026/NĐ-CP. Câu hiệu lực của 12/2015/NĐ-CP không nêu ngày hồi tố.
- Có 8 dòng ranh giới mà đáp án ngắn nằm ở câu dẫn, không nằm trong đơn vị gold: T1 7, T2 1.

### Miền (theo lineage)

**Nguồn nhãn:**
- `portal_field`: 228 lineage;
- `seed`: 199 lineage;
- `portal_major`: 132 lineage;
- `khong_ro`: 94 lineage.

**Nhãn** (một lineage có thể mang nhiều nhãn):
- ngoài bốn miền của đề cương: 425;
- giao thông: 92;
- doanh nghiệp – đầu tư: 72;
- thuế: 56;
- đất đai: 16.

### Corpus

- Có 78 cặp văn bản cùng số hiệu và cùng ngày ký, tức cổng lưu một văn bản hai lần.
- 15/653 trích dẫn chữ của chính điều khoản đích không phân giải được: `citation` không có Điều, hoặc số hiệu cũ trùng mà không có năm.

### Probe theo nhóm (G3; split test)

Mỗi probe biết sẵn điều khoản gold và chỉ chọn phiên bản. Chỉ số là TV-Recall@1; riêng dòng `hedge` là Accuracy tương phản.

Bảng `giua_khoang` (bảng chính). Cột "T2" là cả nhóm; "gần giống" là lát `near_identical` của T2 (T4 cũ):

| Probe | T1 | T2 | gần giống | T3 | T5 | T6 | TCS |
|---|---:|---:|---:|---:|---:|---:|---:|
| mới nhất | 1,000 | 0,500 | 0,500 | 0,325 | 0,500 | 0,500 | 0,000 |
| đầu tiên | 1,000 | 0,500 | 0,500 | 0,325 | 0,447 | 0,500 | 0,000 |
| ngày gần nhất | 1,000 | 0,788 | 0,772 | 0,713 | 0,789 | 0,500 | 0,576 |
| rào đón, Accuracy tương phản | 1,000 | 0,065 | 0,061 | 0,000 | 0,026 | 0,500 | 0,000 |
| rào đón, Accuracy lỏng | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 0,500 | 0,000 |

Bảng `ranh_gioi`: probe "ngày gần nhất" đạt T3 0,325 và T2 0,500, bằng các probe khác.

Bảng `truoc_hieu_luc` (chỉ T2): "mới nhất" và "ngày gần nhất" đạt TV-Recall@1 0,000, vì
phiên bản sắp có hiệu lực là bản mới nhất và cũng gần ngày hỏi nhất; "đầu tiên" đạt 1,000,
vì mọi cặp T2 chỉ có hai phiên bản. Chế độ này vì vậy bắt được heuristic "lấy bản mới",
không bắt được heuristic "lấy bản đầu".

Oracle đạt trần ở mọi chỉ số và mọi chế độ. Riêng EM/F1 thì không: oracle đạt F1 0,586 vì câu trả lời là cả điều khoản.
