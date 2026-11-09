# ViLexTime — Datasheet

Theo khung *Datasheets for Datasets* (Gebru và cộng sự, 2021). Tài liệu mô tả
bản `data/vilextime_dataset/`, schema **2.0.0**, `final: true`, `draft: false`.
Nguồn số và hash: `data/vilextime_dataset/manifest.json`. Đối chiếu lại 09/11/2026.
Có **769 dòng chính, 859 dòng silver**. Trạng thái final của bản này không
chứng minh bộ test cuối G2 đã hoàn tất. Xem mục 7 và báo cáo G2.

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
| "1.150 câu hỏi" | 362 **dòng chính** ranh giới, 246 lineage; 389 dòng silver ranh giới, 178 lineage. Chưa đạt khung 1.100–1.300; không cộng silver thành nhãn đã kiểm | ADR 0003 Follow-Up 24/09; plan GĐ4 07/10 |
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
- **Tái lập:** bản chính là `data/vilextime_dataset/vilextime.jsonl`; silver là
  `vilextime_silver.jsonl`. Hash phát hành nằm ở manifest cùng thư mục.
  `data/derived/vilextime/release.jsonl` và manifest cũ chỉ mô tả bản lịch sử.
- **Phiên bản:** theo ADR 0003 §8. Đổi gold hay chuyển dòng giữa các split là MAJOR; thêm
  trường hay thêm mã là MINOR.
- **Trạng thái kiểm định (29/10/2026).** Bản phát hành `data/vilextime_dataset/` (schema 2.0.0, `final: true`):
  769 dòng chính, 859 dòng silver. Tập test, chế độ ranh giới, trong file chính: T1 123, T2 46, T3 12, T6 30,
  T5 0. Nguồn nhãn của 211 dòng này: luật sư 33 dòng (10 dòng hòa giải, có phiếu Claude hỗ trợ; 23 dòng từ lượt
  kiểm nhãn agent), A và B cùng nhãn 88 dòng, nhãn agent 90 dòng (T1, T6).
  - Hiệu chuẩn mù của agent (Codex gpt-6-sol) trên 178 dòng có nhãn người độc lập: AC1 0,721, p_neg 0,610;
    ngưỡng AC1 ≥ 0,80 **không đạt** ở mức toàn tập, đạt ở T1 (0,970) và chỉ T6 đạt p_neg (0,833, AC1 0,681).
    Nên nhãn agent chỉ dùng cho T1, T6 (định nghĩa mục 6, sửa 28/10).
  - Hai người gán độc lập: AC1 0,377 trên 246 dòng chung, chưa đạt ngưỡng. Nhãn của A: khoảng 5 giây mỗi dòng,
    288 ghi chú nháp do Claude viết.
  - Luật sư kiểm nhãn agent: mẫu 50 dòng đồng ý 43/50 (Wilson 95% [0,738; 0,930]); 67 dòng A–agent lệch còn lại
    đồng ý 54/67. A và agent lệch thì lấy nhãn agent (định nghĩa mục 6, sửa 29/10; trước đó lấy `dat`). T6 test
    giảm từ 152 xuống 30 dòng: luật sư xác nhận phần lớn dòng bãi bỏ có nội dung chuyển sang văn bản thay thế
    (R2), hoặc không chắc có chuyển hay không.
  - Dòng test T2, T3, T5 chưa có đủ người kiểm nằm ở silver (389 dòng ranh giới). H1 và H2 chỉ thăm dò.
  - **Chưa xong:** tập gold độc lập (0/75); kiểm 30 dòng ngày ký của
    `truoc_hieu_luc`; T5 chưa có dòng nào được kiểm; tag `vilextime-v1.0`.

## 8. Số liệu bản schema 2.0.0

Nguồn: `data/vilextime_dataset/manifest.json`. Bảng sau chép đủ
`counts_main` và `counts_silver`. Dòng không được liệt kê có số lượng 0.
T4 là lát của T2, không cộng lần hai. Không dùng bảng 2.730 dòng schema
1.4.0 ngày 11/10 làm mô tả bản hiện tại.

| Nhóm | Chế độ | Main dev | Main test | Silver test |
|---|---|---:|---:|---:|
| T1 | giua_khoang | 18 | 123 | 0 |
| T1 | ranh_gioi | 18 | 123 | 0 |
| T2 | giua_khoang | 72 | 46 | 274 |
| T2 | ranh_gioi | 72 | 46 | 274 |
| T2 | truoc_hieu_luc | 26 | 19 | 81 |
| T3 | giua_khoang | 19 | 12 | 95 |
| T3 | ranh_gioi | 19 | 12 | 95 |
| T5 | giua_khoang | 0 | 0 | 20 |
| T5 | ranh_gioi | 0 | 0 | 20 |
| T6 | giua_khoang | 42 | 30 | 0 |
| T6 | ranh_gioi | 42 | 30 | 0 |
| **Tổng mọi chế độ** | | **328** | **441** | **859** |

Main: **769 dòng, 246 lineage** (dev 81, test 165). Silver: **859 dòng,
178 lineage**, đều mang split test trong bản đã lưu; chưa đưa vào bảng chính.
Ranh giới main: 151 dev + 211 test = **362**; silver **389**.
Giữa khoảng có cùng các số đếm đó. Trước hiệu lực main: 26 dev + 19 test
= **45**; silver **81**. Không có dòng sau hết hiệu lực trong bản này.

### Tầng nhãn và kiểm định

Manifest ghi trạng thái lineage: `dat` **246**, `khong_dat` **185**,
`not_verified` **178**. Đây là phễu kiểm nhãn, không phải 609 lineage
được phát hành. Các trường audit ranh giới: checked **731**, not_verified
**389**, unsettled **0**; review_counts: human_checked **523**,
agent_checked **208**, a_agent_disagreement **5**. Chúng khác đơn vị với
số lineage và số dòng main; không gộp mẫu số.

Đồng thuận người–người trong manifest (hướng dẫn 3.0): **246 dòng**;
AC1 **0,377277**, p_neg **0,394558**, κ **0,235491**. Theo lineage:
**138**; AC1 **0,389639**, p_neg **0,483516**. Chưa đạt ngưỡng AC1
0,80 và p_neg 0,60. Không dùng đồng thuận AI–AI thay số này.

Các lô AI và phê duyệt CMT tháng 11 nằm ở `data/review/ai_research/`,
chưa tích hợp vào manifest bản này. Báo cáo cỡ mẫu G2 tính riêng;
silver được chấp nhận hàng loạt không được gọi là người kiểm từng dòng.

### Hash phát hành

| File | SHA256 |
|---|---|
| `vilextime.jsonl` | `7cf51ee66c7e242b0d3a7b03e62f1ed9bede6527082d9b2f8483ec75d278b366` |
| `vilextime_silver.jsonl` | `c864a545a52279883303c703c17ec2eba98797cad42b544c8d6c5199e8030c4b` |
| `vilextime_meta.jsonl` | `b43dc0cc6ff01bbcbf0bd3b054f8a0cfc9dd01ecb799e95b76cf69acd039f8a7` |
| `vilextime.csv` | `7bbe91e2157ec829de47f02eb22e8f1f2734ccee524641f4c6c2cedab3e18c7a` |
| `vilextime_silver.csv` | `1e355f45048d0ad0c5931b6b5ab1e2ffa30c8b9828bcdf073c9483eb5a10d50e` |

Kiểm tái lập: chạy `PYTHONPATH=src .venv/bin/python scripts/check/audit_g2_statistics.py`
để kiểm hash, số dòng theo manifest, và tái tạo báo cáo cỡ mẫu.
Các số lịch sử về probe, miền và người viết của schema 1.4.0 không
được suy sang bản 2.0.0 nếu chưa đếm lại trên đúng bản.
