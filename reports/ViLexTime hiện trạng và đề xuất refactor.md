# ViLexTime: hiện trạng và đề xuất refactor

Mục tiêu của tài liệu: nói rõ bộ dữ liệu đang sai ở đâu, và sửa theo thứ tự nào để
có một bộ ViLexTime hoàn chỉnh.

Căn cứ: `scripts/pipeline/build_question_pool.py`, `scripts/pipeline/sample_vilextime.py`,
`docs/vilextime-datasheet.md` (schema 1.2.0, 29/09), `docs/reports/JUDGE_DATASET.md`,
`docs/plans/active/phase-4-vilextime.md`, `docs/crawling-plan.md`, và Bảng 1 của đề cương.
Mọi số liệu lấy từ các file trên, chưa chạy lại script.

---

## 0. Kết luận trước

**Ba việc chặn, theo đúng thứ tự phụ thuộc:**

1. **Sửa cấu trúc nhóm rồi rebuild** — vì rebuild làm đổi id của dòng, nên phải xong
 *trước* khi gán nhãn. Tiền lệ J5: thay 3 lineage làm đổi id của 50 dòng T3 trong tập κ.
2. **Gán nhãn người** — đây là cửa sổ không mở lại được. Nhãn thô trước hoà giải,
 overlap mù, và việc giấu nhãn model chỉ làm được *trong khi* gán.
3. **Tập con gold độc lập** — thứ duy nhất trả lời được phản biện "gold và hệ thống
 dùng chung một nguồn".

Việc không chặn: cào thêm dữ liệu. **Không có thiếu hụt dữ liệu.** Thiếu hụt nằm ở
ba trần trong code, ở recall 62,2% của L2, và ở phễu viết câu hỏi.

---

## 1. Hiện trạng

Bản phát hành 29/09: **2.481 dòng · 666 lineage · 517 văn bản đích** (dev 131 / test 535).


| Nhóm     | Lineage | Dòng ranh giới | Quota đề cương | Trạng thái                        |
| -------- | -------: | --------------: | --------------: | --------------------------------- |
| T1       | 251     | 251            | 250            | Đủ, nhưng mốc hỏi bị lộ           |
| T2       | 200     | 400            | 400            | Đủ                                |
| T3       | 65      | 199            | 200            | Đủ **dòng**, thiếu **lineage**    |
| T4       | 75      | 150            | 150            | Đủ dòng                           |
| T5       | 19      | 38             | 50             | Không đạt, chỉ 3 văn bản tác động |
| T6       | 56      | 112            | 100            | Đủ dòng, nhưng mẫu bị nhiễu       |
| **Tổng** | **666** | **1.150**      | 1.150          |                                   |


**Đã xong:** schema, corpus hai lớp, scorer, split dev/test, manifest sha256, datasheet,
giấy phép, Accuracy/TCS bản tương phản (chốt 29/09), bộ phân giải trích dẫn chữ,
9 văn bản được sửa `effective_to` có câu nguồn.

**Chưa xong** (datasheet §7): κ trên tập kiểm chéo · audit 490 nhãn bắt buộc ·
luật sư chốt T5 · phân xử cờ hiệu lực của lineage κ · tập con gold độc lập · tag v1.0.

---

## 2. Vấn đề và cách sửa

### P1 — Cascade trong `classify` làm các nhóm nhiễm lẫn nhau ⛔ CHẶN

**Hiện trạng.** `build_question_pool.py:77-97` quyết định nhóm theo thứ tự, dừng ngay khi khớp:

```
Bước 1: ≥3 phiên bản         → T3, dừng
Bước 2: bị bãi bỏ một phần   → T6, dừng
Bước 3: 2 phiên bản          → T4 (độ giống ≥0,90) hoặc T2, dừng
Bước 4: còn lại              → T1
```

Comment trong code nói rõ đây là chủ ý: nhóm nào ít dữ liệu hơn thì được ưu tiên lấy.

**Vì sao sai.** Một khoản bị sửa 3 lần rồi bị bãi bỏ là ví dụ hoàn hảo của bãi bỏ một
phần. Nhưng nó có 4 phiên bản, nên bước 1 bắt trước và gán T3. Nó không bao giờ tới bước 2.
Hệ quả: **T6 chỉ chứa điều khoản có 1 hoặc 2 phiên bản.**

T6 vì vậy không phải mẫu của hiện tượng bãi bỏ một phần, mà là mẫu của bãi bỏ một phần
*ở những điều khoản ít bị sửa*. Khi báo "hệ thống tốt hơn 12 điểm ở T6 so với T2",
không ai biết 12 điểm đó do bãi bỏ một phần hay do T6 vốn có chuỗi ngắn hơn nên dễ hơn.
Hai nguyên nhân đã trộn vào nhau từ lúc chia nhóm, nên **không so sánh theo nhóm được nữa**.

Lỗi này không nằm ở đề cương. Đề cương không nói gì về thứ tự ưu tiên.

**Sửa.** Cho một lineage mang nhiều nhãn cùng lúc, hoặc gán nhãn theo hiện tượng và để
số phiên bản làm trường riêng (xem §3). Ví dụ trên thành: hiện tượng `bãi bỏ một phần`,
`n_versions = 4`.

Trước khi sửa, chạy `classify` ở chế độ chỉ đọc để đếm bao nhiêu chuỗi đủ điều kiện T6
đang bị bước 1 ăn mất. Con số đó là thiệt hại thật của lỗi này.

---

### P2 — Gold và hệ thống đề xuất dùng chung một nguồn ⛔ CHẶN

**Hiện trạng.** Lớp B của corpus chính là đầu ra L2–L3. Gold `version_id` lấy từ cùng
`versions.jsonl`. Nhóm T2–T6 chỉ gồm những thay đổi mà L2 đã phát hiện được.
Recall của L2 là **62,2%**, precision 96,7%.

**Vì sao sai.** Hệ thống đề xuất sẽ "đúng theo gold" kể cả khi đồ thị tri thức sai.
Khoảng 38% thay đổi mà L2 bỏ sót không bao giờ xuất hiện trong bộ dữ liệu, nên lỗi thật
của KG không hiện ra. Một phần lợi thế ở RQ2/RQ3 là do cấu trúc bộ dữ liệu, không phải
do hệ thống tốt hơn. Đây là phản biện mạnh nhất mà bài báo sẽ nhận.

**Sửa.** Tập con có gold dựng từ nguồn **không đi qua KG**, báo kết quả hai cột
"gold theo KG" và "gold độc lập". Ba nguồn, theo thứ tự khả thi:


| Nguồn                                                                                                    | Kỳ vọng thật                                                                                                                                                                                                                                                                                          |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Người đọc văn bản thô (`crosscheck_evidence.py` cắt sẵn điều gốc, đoạn tác động, điều khoản chuyển tiếp) | Khả thi nhất. 100–150 dòng là đủ                                                                                                                                                                                                                                                                      |
| Danh mục điều khoản hết hiệu lực và cờ `hasClauseRelation` của cổng                                      | Rẻ, và đúng nhóm T6 đang mở rộng                                                                                                                                                                                                                                                                      |
| Cào thêm VBHN                                                                                            | **Đã thử, yếu.** E1 đóng 25/09: chỉ 51/356 VBHN so được, phủ 9/1.150 dòng, và vế trước không VBHN nào kiểm được vì VBHN chỉ hợp nhất đến trạng thái hiện hành. Crawling-plan xếp VBHN ngoài phạm vi (372/437 chưa cào), có 2.938 cạnh hợp nhất, nên cào nốt sẽ nâng độ phủ — nhưng đừng kỳ vọng nhiều |


Ghi chú: vế trước đã được kiểm bằng đường khác. `check_before_side.py` chạy cả 275 cặp
T2/T4: tỷ lệ sai **0/275**. Nên P2 chỉ còn là vấn đề của việc L2 bỏ sót, không phải của
lời văn gốc.

---

### P3 — Chưa có nhãn người nào ⛔ CHẶN, và cửa sổ chỉ mở một lần

**Hiện trạng.** κ: **0/300**. Audit: **0/490** nhãn bắt buộc. Phiếu luật sư T5: trống.
Mọi dòng ngoài tập κ mang nhãn `dat` của `claude-opus-5-5`. Cả hai dòng gold sai mà
người phản biện tìm ra đều được model gán `dat`. Mã `transitional_rule` chưa dùng lần nào
trong 923 nhãn model, dù 190 dòng có dấu hiệu điều khoản chuyển tiếp.

Thêm một vết: **8/300 dòng κ đã có nhãn người** từ bản Excel xem trước, nên không còn mù
hoàn toàn với người đã gán bản đó.

**Vì sao đây là cửa sổ một lần.** Nhãn thô trước hoà giải, overlap mù, và việc giấu nhãn
model ở lượt đầu chỉ làm được *trong khi* gán. Sau khi đã hoà giải thì không khôi phục
được, và đó chính là thứ duy nhất cho phép bên thứ ba tính lại độ đồng thuận.

**Sửa.**

- Gán đơn toàn bộ; **overlap mù 600 dòng** do hai sinh viên gán (sàn tuyệt đối 300 dòng).
- Giấu nhãn model ở lượt đầu. Hội đồng LLM chỉ dùng để xếp thứ tự hàng rà lại.
- Cài kiểm soát: 20–40 item lỗi cố ý, 3–5% dòng lặp lại, cột phút trên mỗi dòng.
- Báo cáo κ **kèm AC1 và p_neg**. Ở tỷ lệ đạt 85–95%, κ bị kéo thấp một cách cơ học:
mô phỏng cho thấy tỷ lệ đạt 0,90 → κ 0,605 nhưng AC1 0,875; tỷ lệ đạt 0,95 → κ rơi
xuống 0,448 trong khi AC1 vẫn 0,885. Mốc M3 "κ ≥ 0,6" có thể trượt chỉ vì người gán
làm tốt. Đăng ký trước ngưỡng AC1 ≥ 0,80.
- Ghi 8 dòng tiền-D4 vào biên bản κ.

**Nếu người gán A là hội đồng LLM** thì κ(A, B) là độ khớp model–người, **không được gọi
là IAA**. Báo như IAA là khai sai ở mục D của checklist ARR.

---

### P4 — T4 và T3 nên là trường, không phải nhóm

**Hiện trạng.** T4 = T2 với `difflib ratio >= 0.90` (`NEAR_IDENTICAL`, `:59`).
T3 = chuỗi ≥ 3 phiên bản. Cả hai là ngưỡng cắt trên một biến liên tục.

**Vì sao sai.**

*T4:*

- Cặp có độ giống 0,91 thành T4, cặp 0,89 thành T2. Hai cặp gần như giống nhau bị xếp
hai nhóm, mỗi nhóm quota riêng, không so được với nhau.
- Chữ ký probe không phân biệt được với T2: (0,500 · 0,500 · 0,772 · 0,057) so với
(0,500 · 0,500 · 0,741 · 0,028). Với 108 dòng test, sai số khoảng ±8 pp, khác biệt 3,1 pp.
*Lưu ý ngược lại:* các probe này biết trước điều khoản gold và chỉ chọn theo ngày, nên
về bản chất không thể thấy độ giống. Nhưng điều đó cũng có nghĩa **hiện chưa có phép đo
nào tách được T4 khỏi T2.**
- Ngưỡng nằm sát một hiện vật pipeline: 2.132/19.192 cặp liền nhau (11,1%) giống hệt nhau
về chữ và bị loại, trong đó **1.947 ca là T4**. Chưa rõ nguyên nhân là luật hay do cổng
đã áp sẵn lời văn mới.
- `difflib` so theo ký tự, không theo nghĩa: một khoản dài đổi một con số đạt trên 0,99,
còn một khoản ngắn bị đổi tên cơ quan lại đạt thấp. Việc gán T2 hay T4 có thể ngược.
- Vai trò "đo ảo giác trích dẫn" là một chỉ số (TVER/VCR), áp lên mọi nhóm.

*T3:*

- **Mức ngẫu nhiên khác nhau nên điểm không so được.** Chọn phiên bản ngẫu nhiên cho
1/3 ở T3 và 1/2 ở T2. Datasheet thể hiện đúng vậy: probe "mới nhất" đạt 0,325 ở T3 và
0,500 ở T2. T3 thấp hơn **không** có nghĩa là T3 khó hơn. Bất kỳ bảng nào đặt hai con số
cạnh nhau sẽ bị phản biện đọc sai.
- Vai trò "đo lợi ích của đồ thị" là phép so sánh giữa các hệ thống, đo được trên mọi nhóm.
- 18,4% lần chuyển của T3 chỉ là thay đổi hình thức (6 ca đổi hoa thường hoặc dấu câu,
139 ca đổi tên tổ chức; 56/139 thuộc đợt sắp xếp bộ máy 2025).

**Sửa.** Giữ dữ liệu, bỏ tư cách nhóm. `version_similarity` và `n_versions` thành trường
trên mọi lineage. Báo kết quả theo tư phân vị độ giống, và chuẩn hoá độ chính xác theo mức
ngẫu nhiên của từng item. Bạn được cả 275 cặp trong một nhóm thay vì 150, nên lực thống kê
cao hơn.

---

### P5 — T6 gộp hai cơ chế khác nhau, và che mất H3

**Hiện trạng.** Định nghĩa đề cương là "hết hiệu lực một phần ở cấp khoản, điểm".
Code tách riêng hai cơ chế nhưng dán cùng một nhãn:


| Cơ chế                       | Code                                                         | Trữ lượng            | Cần đồ thị? |
| ---------------------------- | ------------------------------------------------------------ | --------------------: | ----------- |
| Bị bãi bỏ trực tiếp          | `classify` nhánh T6, `ended_by_event_id` có giá trị          | 6.001 đơn vị         | Không       |
| Cha bị bãi bỏ, con chết theo | `repealed_by_ancestor` (`:116`), `ended_by_event_id is None` | 14.157 đơn vị (2,4×) | **Có**      |


**Vì sao sai.** Chỉ cơ chế thứ hai cần đi từ khoản lên điều, lên mục, lên chương để kiểm
từng cấp. Đó đúng là chỗ đồ thị có ích, và đúng là **giả thuyết H3** cùng bậc "lan truyền"
của RQ3. Gộp hai cơ chế thì khi báo "T6 đạt 70%" không ai biết 70% đến từ đâu. Nếu hệ thống
giỏi cơ chế 1 và dở cơ chế 2 thì bạn che mất đúng kết quả quan trọng nhất của bài báo.

H3 hiện chỉ có **12 lineage**, sai số khoảng ±25 pp, nên chỉ ở mức minh hoạ.

**Sửa.** Tách T6a (trực tiếp) và T6b (lan truyền). Nâng `ANCESTOR_CAP` để T6b lên 150–200
lineage, khi đó MDE ghép cặp khoảng 8–9 pp và H3 thành giả thuyết kiểm được.

Thêm một lưu ý khi báo cáo: chữ ký riêng của T6 (probe "ngày gần nhất" chỉ 0,500 trong khi
các nhóm khác 0,7+) **một phần là hiện vật**. `ask_dates` cho T6 mốc `[end − 1, end]`
(`:106-107`), nên đúng một nửa số dòng không có đáp án.

---

### P6 — T5 quá nhỏ để làm nhóm, và định nghĩa lẫn pháp lý với độ khó

**Hiện trạng.** 19 lineage, 3 văn bản tác động (65/2025/TT-BQP, 12/2015/NĐ-CP,
119/2026/NĐ-CP). Câu hiệu lực của 12/2015/NĐ-CP không nêu ngày hồi tố. 65/2025/TT-BQP có
cửa sổ hồi tố 2 ngày nên không đặt được câu giữa khoảng. Chữ ký probe trùng T2.
Toàn kho chỉ có 194 lineage T5 từ 8 văn bản tác động; sạch còn 148 từ 4 văn bản.

**Vì sao sai.** Đề cương ghi "hiệu lực trở về trước **có lợi cho đối tượng áp dụng**".
Trong Điều 152, "có lợi" là **điều kiện cho phép** hồi tố, không phải thứ làm bài toán hỏi
đáp khó hơn. Nhóm đã tự bỏ vế này, và đó là quyết định đúng. Với 19 lineage, sai số ±15 pp:
báo "60%" thì con số thật có thể là 45% hoặc 75%.

**Sửa.** Hạ xuống **tập chẩn đoán 30–45 lineage**, có trần theo văn bản đích, cố vấn ký
từng ca, báo theo cụm văn bản tác động, không tính vào trung bình macro, ghi rõ "minh hoạ".
Không nới định nghĩa để lấp số (quyết định Q3 đã chốt).

---

### P7 — T1 lộ mốc hỏi và chi quá nhiều

**Hiện trạng.** `ask_dates` cho T1 trả `[starts[0] + ONE_DAY]` (`:104`), tức luôn hỏi ở
ngày phiên bản bắt đầu + 1. T1 có 251 lineage. Probe đạt 1,000 ở mọi hàng.

**Vì sao sai.** Một hệ thống chẳng hiểu gì, chỉ chọn phiên bản có ngày bắt đầu gần mốc hỏi
nhất, sẽ đúng mọi lần. Đây đã từng là lỗi của T3 và probe giải đúng 100%; T3 được dời ngày
29/09, T1 thì chưa.

Điểm 1,000 của T1 là **đúng với vai trò đối chứng** — nó cho biết lợi ích trên T2–T6 đến
từ khả năng thời gian hay chỉ từ truy xuất tốt hơn. Nhưng vai trò đó không cần 251 lineage:
150 đã cho ±7,9 pp.

**Sửa.** Dời mốc hỏi khỏi vị trí "ngày bắt đầu + 1". Giảm còn 150 lineage, chuyển 100
lineage công gán nhãn sang T6b. Mô tả lại vai trò: T1 đo **việc từ chối sai và việc bộ lọc
thời gian kích hoạt quá mức**, không phải "tra cứu không mơ hồ về thời gian".

---

### P8 — Thiếu hai hiện tượng

**Chưa có hiệu lực (`not_yet_in_force`).** Schema có giá trị này nhưng **0 dòng dùng**.

Ví dụ: nghị định ký tháng 3/2025, hiệu lực từ 01/01/2026. Hỏi vào tháng 6/2025 thì nghị
định đó **chưa phải luật**, dù đã nằm trên cổng, tìm được bằng truy xuất, và nguyên văn
hoàn toàn đúng.

Đây là bẫy khó nhất với RAG: mọi tín hiệu đều nói "đây là văn bản mới nhất, dùng nó đi",
mà đáp án đúng lại là văn bản cũ. Và nó phổ biến hơn hồi tố rất nhiều, vì **mọi** văn bản
đều có khoảng cách giữa ngày ký và ngày hiệu lực, nên dữ liệu dồi dào.

→ Đây là thứ nên thay vào chỗ của T5: cùng là "ca khó", nhưng có đủ dữ liệu để kết luận.

**Bổ sung và thay thế.** 100% transition trong bản phát hành là `amend`, trong khi kho
event có **5.095 `supplement` và 2.211 `replace`**. Bộ dữ liệu đang kiểm một trong ba loại
tác vụ, trong khi mô tả mình là benchmark về sửa đổi văn bản.

---

### P9 — Số lượng: trần trong code, không phải thiếu dữ liệu

**Trữ lượng không giới hạn** (chạy lại `classify` không đặt trần):


| Nhóm          | Lineage sạch trong pool             | Không giới hạn                  | Nút chặn       |
| ------------- | -----------------------------------: | ------------------------------- | -------------- |
| T1            | 1.975                               | 1.434.735 / 17.091 văn bản      | Quota          |
| T2            | 3.619                               | 10.155 / 1.445                  | Quota          |
| T3            | 346 (≥2 lần sửa thực chất: 130–249) | 386 / 126 — **pool đã lấy hết** | Dữ liệu thật   |
| T4            | 1.313                               | 5.530 / 998                     | Quota          |
| T5            | 184 (sạch 148, từ 4 văn bản)        | 194 / 8 văn bản tác động        | Dữ liệu thật   |
| T6 trực tiếp  | 852                                 | 2.213 / 663                     | Quota          |
| T6 lan truyền | 264                                 | **10.055 / 484**                | `ANCESTOR_CAP` |


Chỉ **T3 và T5** thiếu thật. Mọi nhóm khác bị chặn bởi code.

**Bốn đòn bẩy, xếp theo sản lượng trên mỗi giờ công. Ba cái đầu không cần cào gì thêm.**

**A. Bỏ trần trong code.** Sản lượng cao nhất, chi phí gần như bằng không.


| Trần                      | Chỗ                                                     | Ghi chú                                                                                   |
| ------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `ANCESTOR_CAP = 300`      | `build_question_pool.py:61`                             | Comment tự thừa nhận "10,249 exist for a 24-row quota". Nút chặn lớn nhất                 |
| `QUOTA` đếm theo **dòng** | `build_question_pool.py:57` và `sample_vilextime.py:48` | Đổi đơn vị sang lineage. Hai file còn **lệch nhau**: T6 là 100 ở file đầu, 150 ở file sau |
| `PER_DOCUMENT = 2`        | `sample_vilextime.py:54`                                | Nâng lên 3 riêng cho T3. Vẫn cần trần: 10 văn bản lớn nhất chiếm 33,5% chuỗi T3 sạch      |
| Cascade                   | `build_question_pool.py:84-93`                          | Xem P1                                                                                    |


**B. Sửa L2 trước khi cào thêm.** Recall 62,2%, khoảng **21.900 event kẹt ở `needs_review`**.
Mỗi event lấy lại được sinh ra transition mới, tức lineage mới, **và** đồng thời sửa lỗi
gold. Một việc, hai kết quả:

- Lỗi hoa/thường và khoảng trắng khi so cụm từ: trong 779 event `phrase_not_found`, có
**274 cặp khớp nguyên văn và 332 cặp khớp khi bỏ phân biệt hoa thường** → 606 ca lấy lại được.
- `structure_mismatch`: 4.447 ca.

Đây là phần việc kỹ thuật giá trị nhất của cả đồ án, vì nó là đòn bẩy duy nhất vừa tăng
số lượng vừa tăng độ tin cậy của RQ2/RQ3.

**C. Thu lại phần mất ở phễu.** 930 lineage được viết câu hỏi → 751 qua → 20 bị loại sau
khi gán nhãn. 145 ca bị chính người viết đánh `insufficient_context`. Nhiều ca sửa được
bằng cách đưa thêm câu dẫn của khoản cha cho người viết — V3 cho thấy đáp án thường nằm ở
câu dẫn. Lấy lại một nửa là khoảng 70 lineage, chỉ bằng một lần đổi prompt.

**D. Thêm chế độ `as_of`, nhưng nói thật về nó.** Thêm `not_yet_in_force` và một mốc giữa
khoảng thứ hai là chính đáng, vì mỗi dòng kiểm một trạng thái thời gian khác. Nhưng các
dòng trong cùng lineage tương quan với nhau, nên khoảng tin cậy phải bootstrap theo lineage.
300 lineage × 2 dòng với tương quan 0,5 chỉ có cỡ mẫu hiệu dụng khoảng 400, không phải 600.
Cách này giúp con số "1.150 câu", **không** giúp lực thống kê. Đừng để nó thay cho việc
tăng lineage.

**Nguồn mới, nếu vẫn cần:** xem bảng ở P2 cho VBHN và cờ `hasClauseRelation`.
Văn bản địa phương (23 shard, ~116 nghìn văn bản) nhiều về lượng nhưng phá tuyên bố
"chỉ cấp trung ương" và chất lượng cấu trúc kém hơn — để ngoài v1.0.
thuvienphapluat và luatvietnam dùng để lấy **câu hỏi thật** và đối chiếu ngày hiệu lực cho
298 văn bản có `effective_to` rỗng, **không** dùng làm gold: thương mại, ràng buộc điều
khoản sử dụng, không chính thức.

---

### P10 — Đếm "câu" theo gì, và các chỗ lệch đề cương

**Hiện trạng.** Đề cương ghi ~1.100–1.300 câu. Hiện có 1.150 **dòng** ranh giới nhưng chỉ
**666 lineage**, tức 666 câu hỏi khác nhau.

- Nếu "câu" là dòng → **quota đã đạt**.
- Nếu "câu" là câu hỏi khác nhau → đang ở 666, khoảng 60% sàn.

Đây trước hết là thiếu hụt về **định nghĩa**, sau đó mới là về dữ liệu.

**Sửa.** Hỏi khoa xem "câu" nghĩa là gì. Báo cả hai con số trong mọi bảng. Ghi vào bảng
lệch đề cương của datasheet (§6 đã có 8 dòng, cần thêm các mục của tài liệu này).
**Không** độn lineage từ vài văn bản để đạt con số — đó là nước đi duy nhất mất nhiều hơn được.

Ngoài ra còn hai chỗ lệch chưa khai đủ:

- **Nhãn miền.** Đề cương hứa 4 miền. Thực tế: 422 lineage mang nhãn ngoài bốn miền, so với
giao thông 99, doanh nghiệp 83, thuế 56, đất đai 15. Nguồn nhãn: `portal_field` 223,
`seed` 215, `portal_major` 135, `khong_ro` 93. Kiểm tay 25 lineage cho thấy nhãn kế thừa
gần như đều sai (Luật Tổ chức TAND bị gán `dat_dai`, nghị định giáo dục bị gán `giao_thong`).
→ Gán lại theo cơ quan ban hành, hoặc bỏ trường này khỏi phân tích. Không mô tả bộ dữ liệu
là "4 miền".
- **Vai trò LLM.** Đề cương ghi "LLM chỉ hỗ trợ diễn đạt câu hỏi". Thực tế
`claude-opus-5-5` viết 1.039 câu hỏi, tự viết lại 99 câu, viết toàn bộ 1.094 đáp án ngắn,
gán 923 nhãn, đề xuất loại 32/32 lineage. Người sửa 9 câu.
→ Hệ quả bắt buộc cho thực nghiệm: **baseline chính phải thuộc họ model không phải Claude,
và không dùng Claude làm giám khảo.**

---

## 3. Đề xuất refactor schema

Vấn đề gốc của Bảng 1 là nó trộn ba loại thứ vào cùng một biến phân loại:
thuộc tính của chuỗi phiên bản (số phiên bản, độ giống), thuộc tính của ngữ nghĩa hiệu lực
(hồi tố, bãi bỏ một phần), và **mục đích đo lường** ("đo lợi ích của đồ thị", "đo ảo giác
trích dẫn"). Hai cái đầu là dữ liệu; cái thứ ba là giả thuyết, không phải nhãn.

**Tách hiện tượng (nhóm) khỏi biến độ khó (trường):**


| Loại                                         | Nội dung                                                                                                                                                                    |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nhóm** — hiện tượng pháp lý, loại trừ nhau | versioning thường · lan truyền hiệu lực · bãi bỏ một phần trực tiếp · chưa có hiệu lực · hồi tố (chẩn đoán) · đối chứng tĩnh                                                |
| **Trường** — trên mọi dòng                   | `n_versions` · `version_similarity` · chế độ `as_of` · loại tác vụ (amend/supplement/replace) · có đáp án hay không · `question_source` (human / llm_edited / llm_unedited) |


Khi đó mọi phân tích là một lát cắt, và quota thôi làm cái cùm.

**Ánh xạ về Bảng 1 để khóa luận vẫn đọc được.** Đề cương không sửa được, nên giữ sáu nhãn T
làm tầng trình bày, thêm các trường, và khai trong bảng lệch:


| Bảng 1                     | Sau refactor                                    | Lineage đề xuất |
| -------------------------- | ----------------------------------------------- | ---------------: |
| T1 đối chứng               | đối chứng tĩnh, mốc hỏi đã dời                  | 150             |
| T2 cốt lõi                 | versioning thường, `n_versions = 2`             | 300             |
| T3 chuỗi nhiều bước        | versioning thường, `n_versions ≥ 3`, qua lọc R2 | ~200 (sàn 130)  |
| T4 bẫy thời gian           | versioning thường, `version_similarity` cao     | gộp vào T2      |
| T5 ca khó                  | hồi tố — **tập chẩn đoán**                      | 30–45           |
| T6 hiệu lực cấp điều khoản | **T6a** bãi bỏ trực tiếp + **T6b** lan truyền   | 200 + 200       |
| *(mới)*                    | chưa có hiệu lực                                | 100–150         |


**Lọc R2 cho T3:** một chuỗi chỉ tính là T3 khi có ≥3 phiên bản cho **đáp án khác nhau với
chính câu hỏi đó**. Phát hiện then chốt: cả 15 lineage T3 bị loại vì `group_mismatch` đều có
đủ hai lần sửa thực chất — lỗi nằm ở câu hỏi, vì nó chỉ chạm vào một trong hai thay đổi.
**Việc một lineage có phải T3 hay không là tính chất của câu hỏi, không phải của chuỗi.**
Diff văn bản chỉ cho cận trên.

---

## 4. Thứ tự làm

Phụ thuộc là thật: **rebuild làm đổi id dòng**, nên mọi thay đổi cấu trúc phải xong trước
khi gán nhãn. Tiền lệ J5: thay 3 lineage làm đổi id của 50 dòng T3 trong tập κ.

### Giai đoạn 0 — sửa cấu trúc, rồi rebuild một lần


| Việc                                                                                       | Vấn đề | Loại             |
| ------------------------------------------------------------------------------------------ | ------ | ---------------- |
| Đếm chuỗi T6 bị cascade ăn mất (chế độ chỉ đọc)                                            | P1     | Đo trước khi sửa |
| Sửa cascade: nhiều nhãn, hoặc nhãn hiện tượng + trường                                     | P1     | Logic mới        |
| Thêm trường `n_versions`, `version_similarity`, loại tác vụ                                | P4     | Schema           |
| Tách T6a / T6b                                                                             | P5     | Schema           |
| Nâng `ANCESTOR_CAP`; đổi `QUOTA` sang lineage ở **cả hai** file; `PER_DOCUMENT = 3` cho T3 | P9     | Tham số          |
| Dời mốc hỏi T1; giảm T1 còn 150                                                            | P7     | Tham số          |
| Thêm chế độ `not_yet_in_force`                                                             | P8     | Logic mới        |
| Sửa lỗi hoa/thường khi so cụm từ trong `build_versions.py`; áp lại event `needs_review`    | P9-B   | Sửa lỗi          |
| Lọc R2 cho T3                                                                              | P4     | Logic mới        |
| Đưa câu dẫn của khoản cha vào prompt viết câu hỏi                                          | P9-C   | Prompt           |


Khoảng 80% là đổi tham số. Logic mới chỉ có: cascade, R2, `not_yet_in_force`.

**Cổng ra:** `check_release` xanh trên pool mới; mỗi nhóm có ≥1,3× quota ứng viên;
đếm lại số lineage T6 thu được sau khi bỏ trần.

### Giai đoạn 1 — gán nhãn (cửa sổ một lần)

Pilot 1 (~60 lineage phân tầng) → họp hiệu chỉnh → pilot 2 (~50 lineage, nặng T3/T6) →
đóng băng guideline v2.0 → **cổng go/no-go dựa trên phút trung vị mỗi dòng** → gán theo lô.

Đo đạc trước khi quyết quota: nếu ≤3 phút/dòng thì giữ mục tiêu đầy đủ; nếu &gt;4 phút thì cắt
theo thứ tự T1 → T4 → T3. **Không cắt T2, không cắt T6b dưới 150, không cắt overlap.**

Cần dự trù lượt bốc thay thế: khoảng 7,3% lineage T2 (18/247) ghép nhầm hai điều khoản
trùng số thứ tự, và **không có tín hiệu máy nào bắt được** — chỉ lộ ra khi viết câu hỏi.
Bỏ lineage hỏng rồi bốc thay từ pool dư thường rẻ hơn viết lại câu hỏi.

Chi tiết nhãn: xem P3.

### Giai đoạn 2 — gold độc lập và audit

- Tập con gold độc lập 100–150 dòng (P2).
- Audit tỷ lệ lỗi 300–500 dòng, **do người không gán dòng đó làm**, kèm CI nhị thức.
Tiền lệ TACRED: audit 300 item ước 6,7% lỗi, kiểm lại toàn bộ ra 23,9%.
- Báo tỷ lệ gold tự động mà người gán phải sửa, theo từng nhóm. TimeQA là mốc tham chiếu
với 41,6%.
- Cố vấn luật 12–20 giờ: ký phần pháp lý của guideline (hồi tố Điều 152, bãi bỏ một phần,
điều khoản chuyển tiếp) · hai buổi hiệu chỉnh · phân xử 60–100 dòng (T5, T6b, chuyển tiếp,
tranh chấp `gold_wrong`) · audit mù 50–100 dòng. Hàng chờ gom theo tuần, bằng chứng cắt sẵn
bằng `crosscheck_evidence.py` từ `data/raw/<doc>.json` — vì lấy từ văn bản thô chứ không từ
KG nên phép kiểm này không vòng tròn.

### Giai đoạn 3 — đóng băng

`enrich` → `check_release --manifest` → datasheet kèm bảng lệch đề cương đầy đủ →
Croissant → tag `vilextime-v1.0`.

Ràng buộc: mọi thay đổi dữ liệu sau khi GĐ5 bắt đầu buộc chạy lại baseline, và việc tính
BM25/embedding trên khoảng 1,5 triệu đơn vị với 4 CPU, 7 GB RAM, không GPU là giới hạn thật.

---

## 5. "Hoàn chỉnh" nghĩa là gì

Một bộ ViLexTime đóng băng được phải có đủ sáu điều:

1. **Nhóm diễn giải được.** Không nhóm nào bị nhiễm bởi thứ tự gán. Mỗi nhóm có một hiện
 tượng pháp lý và một chữ ký riêng trên baseline tầm thường.
2. **Nhãn có người kiểm.** Overlap mù ≥300 dòng (mục tiêu 600) do hai người gán, nhãn thô
 trước hoà giải được phát hành, κ kèm AC1 và p_neg có CI.
3. **Gold có đường kiểm không đi qua KG** trên một tập con, báo hai cột.
4. **Metric không lách được.** Accuracy và TCS bản tương phản (đã có), cộng
 `citation_coverage` và `tver_strict` (đã có), cộng bảng probe chứng minh baseline tầm
 thường rơi về sàn.
5. **Đủ lực thống kê cho đúng giả thuyết bài báo cần.** H3 ≥150 lineage T6b, không phải 12.
6. **Khai đủ các chỗ lệch** đề cương: cách đếm câu, vai trò LLM, nhãn miền, định nghĩa T5,
 T4 gộp vào T2, T6 tách hai, thành phần tập κ.

Nếu phải chọn giữa số lượng và chất lượng: **một bộ ~1.200 lineage có IAA giữa người với
người, gold kiểm trên văn bản gốc và chấm điểm tương phản đứng vững trước phản biện tốt hơn
một bộ 1.500 lineage chỉ có một lượt kiểm.** Số lượng mua được sau; cửa sổ chất lượng chỉ
mở một lần.

---

## 6. Quyết định cần chốt


| #   | Quyết định                                | Mặc định đề xuất                                            | Chặn việc gì   |
| --- | ----------------------------------------- | ----------------------------------------------------------- | -------------- |
| 1   | "Câu" là lineage hay dòng QA?             | Đếm theo lineage cho bài báo, báo cả hai số, hỏi khoa       | Toàn bộ quota  |
| 2   | Sửa cascade hay giữ nguyên để lấp quota   | Sửa — không sửa thì mất khả năng so sánh theo nhóm          | Giai đoạn 0    |
| 3   | T4 thành trường, hay giữ làm nhóm         | Thành trường, giữ nhãn T4 ở tầng trình bày                  | Schema         |
| 4   | Người gán A là sinh viên hay hội đồng LLM | Hai sinh viên gán overlap; hội đồng LLM chỉ xếp hàng rà lại | Tuyên bố IAA   |
| 5   | Có thêm nhóm "chưa có hiệu lực" không     | Có, thay vào chỗ T5                                         | Giai đoạn 0    |
| 6   | Rebuild ngay hay giữ tập κ 300 dòng cũ    | Rebuild trước mọi nhãn mù; tập cũ thành nguyên liệu pilot   | Giai đoạn 1    |
| 7   | Ngưỡng đồng thuận                         | Giữ κ cho M3, đăng ký trước AC1 ≥ 0,80 và p_neg ≥ 0,6       | Guideline v2.0 |
| 8   | Phạm vi T5 (giữ 12/2015/NĐ-CP không)      | Cố vấn quyết; 30–45 lineage có trần theo văn bản            | Tập κ          |
| 9   | Gán lại nhãn miền hay bỏ khỏi phân tích   | Bỏ khỏi phân tích, khai trong datasheet                     | Datasheet      |


---

## 7. Những việc KHÔNG nên làm

- **Cào thêm nguồn mới trước khi bỏ trần và sửa L2.** Dữ liệu đang bị chặn bởi code, không
bởi nguồn.
- **Độn T3 hoặc T5 cho đủ quota.** Nới định nghĩa hoặc lặp lại vài văn bản làm mất đúng thứ
benchmark định đo. Cỡ mẫu hiệu dụng khi đó xấp xỉ số văn bản, không phải số dòng.
- **Gán nhãn trước khi rebuild.** Id dòng sẽ đổi và công gán nhãn mất trắng.
- **Cắt tập overlap để tiết kiệm giờ công.** Đó là bằng chứng chất lượng mà hội nghị chấm,
và không bù lại được sau.
- **Dùng model họ Claude làm baseline chính hoặc làm giám khảo.** Câu hỏi và đáp án ngắn do
Claude viết.
- **Tự nhận "benchmark pháp luật theo thời gian đầu tiên" hoặc "lớn nhất".** Đã có ít nhất
sáu bộ trong 2025–2026; LexKairos có 3.796 item, TALD có 26.000 bản án. Định vị đứng được:
**benchmark point-in-time đầu tiên cho luật Việt Nam, ở cấp khoản/điểm, có bãi bỏ một phần
và hiệu lực lan truyền, có độ đồng thuận giữa người với người.**

