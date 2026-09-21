# 0003 Schema bộ dữ liệu ViLexTime

Date: 2026-09-21

## Status

Accepted

## Context

`data/derived/vilextime_pool.jsonl` (9.331 ứng viên, 2.949 văn bản) là bảng ứng
viên, chưa phải bộ hỏi đáp: nó không có trường `question`. Đợt audit
`vilextime_sample.tsv` ngày 20/09 và đợt khảo sát tài liệu ngày 21/09
(`reports/Schema bộ dữ liệu ViLexTime.md`) cùng chỉ vào một nhóm lỗi *hình
dạng*, không phải lỗi dữ liệu:

- Một bản ghi gộp nhiều mốc `as_of` vào mảng `gold`, nên độ dài bản ghi đổi
  theo nhóm (T1 một mốc, T3 ba đến bốn) và neo thời gian nằm lồng bên trong,
  không truy vấn phẳng được.
- `event_ids`, `evidence`, `actor_numbers` là ba mảng phẳng được `sorted(set())`
  **độc lập**, nên với chuỗi từ ba lần sửa đổi trở lên, `actor_numbers[i]`
  không ứng với `event_ids[i]`. Đo được trên
  `provision:3bf55646-e172-11f0-8230-79cf6a670840#k1`: lần sửa đầu tiên
  (38/2015/TT-NHNN, 2016-02-15) rơi xuống cuối mảng vì sắp theo chuỗi.
- `transition_on` là một giá trị vô hướng trong khi chuỗi T3 có ba lần chuyển,
  và cùng tên trường mang ba nghĩa khác nhau tuỳ nhóm.
- Trạng thái pháp lý bị trộn vào nội dung: worksheet ghi chuỗi
  `KHÔNG CÒN HIỆU LỰC` vào ô đáp án của T6.

Chín tên trường dự kiến mượn từ tài liệu tham khảo đã được truy nguồn từng cái.
Năm tên — `hop_level`, `reasoning`, `used_context_ids`, `source_tuple_id`,
`context_block` — **không truy được về bất kỳ bộ dữ liệu, bài báo hay framework
công bố nào**; đây là kết quả âm tính có giới hạn (chưa kiểm DeepEval, TruLens,
LlamaIndex, chưa tìm ở hội nghị tiếng Trung/tiếng Việt) nhưng đủ để không trích
dẫn chúng như quy ước trong khoá luận. `evidence` có thật nhưng mang ba nghĩa
khác nhau ở GraphRAG-Bench, 2WikiMultihopQA và StrategyQA, và không nghĩa nào
trùng với nghĩa ViLexTime đang dùng.

## Decision

### 1. Hai tầng, một bản ghi cho mỗi cặp (điều khoản, `as_of`)

`vilextime_pool.jsonl` ở lại làm **bảng ứng viên nội bộ**: một dòng cho mỗi
lineage điều khoản, giữ nguyên `versions`, dùng để lấy mẫu và chia split. Bộ
phát hành là **bảng QA** ở `data/derived/vilextime/<split>.jsonl`, một dòng cho
mỗi cặp (điều khoản, `as_of`). Đây là lựa chọn của mọi benchmark temporal QA
kiểm chứng được (TempLAMA phát lại cùng `query` mỗi năm với `id` hậu tố năm;
TimeQA tạo `idx` riêng cho mỗi ràng buộc thời gian trên cùng một trang). Giá
phải trả là lặp chuỗi câu hỏi; lợi ích là mỗi dòng tự nó chấm điểm được và sáu
nhóm dùng đúng một schema.

### 2. Sáu nhóm dùng một schema, khác biệt nằm ở trường tùy chọn

`group` (T1–T6) là **cột phân tầng**, không phải biến thể cấu trúc. Hai trường
chỉ có nghĩa ở một nhóm (`similarity` của T4, và trường mốc hồi tố của T5 khi
cố vấn luật chốt được) là **tùy chọn, null ở nhóm khác** — không tách schema
riêng. Sáu schema riêng sẽ buộc mọi loader, script chấm điểm và phép chia split
rẽ nhánh sáu lần trong khi khác biệt thật chỉ là hai trường.

### 3. Trạng thái hiệu lực tách khỏi nội dung đáp án

Bốn trường, dư thừa có chủ ý: `answer` (null khi không có), `answerable`
(boolean), `in_force` (boolean), `no_answer_reason` (**từ vựng đóng**:
`not_yet_in_force` · `provision_repealed` · `document_repealed` ·
`out_of_corpus`). Chuỗi `KHÔNG CÒN HIỆU LỰC` không bao giờ xuất hiện trong
`answer`.

Dư thừa là có lý do: bản HuggingFace của SQuAD 2.0 đã bỏ hẳn boolean
`is_impossible` và chỉ báo bằng mảng rỗng, TimeQA dùng chuỗi canh
`"[unanswerable]"` ngay trong mảng đáp án — cả hai gộp mọi lý do vào một rọ.
Với benchmark này **lý do chính là thứ đang được đo**: hệ thống trả "không có
đáp án" vì không tìm thấy điều khoản không làm cùng việc với hệ thống truy được
một lần bãi bỏ.

### 4. `derivation.transitions` là mảng object, không còn mảng song song

Mỗi lần chuyển là một object gói `on`, `from_version`, `to_version`,
`event_id`, `actor` (`law_id`, `document_id`, `effective_from`), `evidence`,
`evidence_kind`. Không thu thập thêm dữ liệu: prefix của `event_id` chính là
`document_id` của văn bản tác động, và `effective_from` của văn bản đó chính là
ngày chuyển tiếp. Ba mảng `event_ids` / `evidence` / `actor_numbers` bị bỏ.

### 5. Chín tên trường tham khảo: giữ bốn, thay năm

| Trường | Quyết định |
|---|---|
| `id` | Giữ, đổi sang khoá hợp thành có chứa `as_of` |
| `question` | **Bổ sung** — trường đang thiếu khiến pool chưa phải bộ QA |
| `answer` | Giữ, scalar, kèm ba trường ở mục 3 |
| `evidence` | Giữ tên, chuyển vào `derivation.transitions[]`; README phải nói rõ đây là *câu lệnh sửa đổi*, không phải mệnh đề chứng minh đáp án |
| `hop_level` | **Bỏ.** Câu hỏi ViLexTime tra cứu một điều khoản tại một mốc, không có hop. Dùng `group`, `num_versions`, `num_transitions`. `level` còn nguy hiểm vì HotpotQA dùng nó cho độ khó và GrailQA cho mức tổng quát hoá |
| `reasoning` | **Bỏ.** Gold suy ra máy móc; một blob văn xuôi sẽ do model viết và lặng lẽ thành một phần của nhãn. Thay bằng `derivation` có cấu trúc |
| `used_context_ids` | **Đổi tên** thành `relevant_version_ids` / `utilized_version_ids`, theo phân biệt `all_relevant_*` / `all_utilized_*` của RAGBench |
| `source_tuple_id` | **Thay** bằng `event_id` + `version_id` ổn định *và* `derivation.query` tái chạy được |
| `context_block` | **Bỏ khỏi bản ghi gold.** Corpus phát hành riêng; bản ghi chỉ trỏ vào nó |

### 6. Khoảng hiệu lực nửa mở, hai trục thời gian

`valid_from` / `valid_to` là **nửa mở `[from, to)`**, `null` nghĩa là còn mở —
cùng quy ước với `effective_from`/`effective_to` đã dùng trong `versions.jsonl`.
`retrieved_at` là trục thứ hai (transaction time): nó trả lời "bản crawl của
chúng tôi tin gì vào ngày dựng gold", câu hỏi người phản biện sẽ đặt khi cổng
vbpl.vn đã được sửa từ đó.

### 7. Split: file là thẩm quyền, trường là tiện lợi

Giá trị: `dev` · `test` · `test_contested` · `excluded`. **Chỉ `test` được
metric mặc định nhìn thấy.** Mọi dòng cùng `lineage_id` **phải** cùng split
(bắt buộc — nếu không, các biến thể `as_of` của cùng một điều khoản làm rò gần
hết đáp án); mọi lineage cùng `document_id` **nên** cùng split.

Loại item khỏi chấm điểm bằng **cấu trúc, không bằng cờ**: item mà đồ thị hiện
tại không tái dựng được mang `flags: ["kg_unreproducible"]` *và* nằm trong file
`excluded`. `flags` để giải thích, `split` để thi hành. Một cờ mà scorer được
*tin* là sẽ tôn trọng thì một phần người dùng downstream sẽ bỏ qua.

### 8. Hai trục đánh số phiên bản

`schema_version` ở mức bản ghi (quy ước JSONL thực dụng — **không spec nào định
nghĩa nó ở mức bản ghi**, không trình bày như chuẩn) và `version` +
`datePublished` ở mức descriptor. Thay đổi MAJOR: đổi tên hoặc sắp xếp lại
trường, sửa gold đã phát hành, **xáo item giữa các split**, gán lại item giữa
các mã `no_answer_reason` đã có. Thêm trường mới hoặc thêm mã mới là MINOR.

### 9. Từ vựng đóng phải chốt trước đợt kiểm tay

`no_answer_reason`, `flags` và `review.guideline_version` phải cố định **trước**
khi hai người gán nhãn và cố vấn luật bắt đầu, không phải sau: nhãn thô trước
hoà giải là thứ không khôi phục được sau khi đã hoà giải, và gán lại item giữa
các mã sau phát hành là thay đổi MAJOR. `review` ship **nhãn thô của từng
annotator** kèm mã giả danh, không chỉ kappa, để bên thứ ba tính lại được.

Từ vựng `flags` v1.0.0, chốt 21/09 (CMT) — **chỉ lỗi cấu trúc**:

| Mã | Nghĩa | T1 |
|---|---|---:|
| `not_a_provision` | target là Chương/Mục/Tiểu mục, không phải Điều/Khoản/Điểm | 69 |
| `heading_only` | text của nút chính là tiêu đề của nó (`answer` = "Chương IV") | 32 |
| `untitled_ancestor` | nút nguồn không có số, làm citation hỏng ("Khoản 3 Điều") | 17 |
| `kg_unreproducible` | đồ thị hiện tại không tái dựng được gold (chưa gán, chờ đo) | — |

**Độ dài đáp án không phải tiêu chí.** Đo trên T1: ngưỡng 80 ký tự cắt 779 dòng
(31,2%) mà phần lớn là điều khoản ngắn hợp lệ ("đ) Số lượng, khối lượng dịch vụ
thủy nông được trợ cấp;"); ngưỡng 40 ký tự cắt 329 dòng và vẫn không có căn cứ.
Tiêu chí loại theo độ dài thuộc về đợt kiểm tay B3, không đóng băng ở đây.

### 10. Câu hỏi do model sinh, một câu cho mỗi lineage

`question` là thứ duy nhất trong bản ghi do model viết; gold không bao giờ.
Mỗi lineage có **một** câu hỏi dùng chung cho mọi `as_of` (C3), và **mốc thời
gian không nằm trong câu hỏi** — nó là trường `as_of`. Đây là điều kiện để một
câu hỏi phục vụ được hai mốc của cặp tương phản T2.

Văn phong: câu hỏi nội dung, neo bằng chủ đề văn bản ("Theo <chủ đề>, ..."),
văn phong khoa học. Không dẫn số hiệu, không dẫn Điều/Khoản/Điểm, không lời
dẫn hội thoại. Prompt nằm trong `prompts/vilextime/` (`base.md` + một file mỗi
nhóm), và `question_source` ghi `provider`, `model`, `temperature`,
`prompt_sha` trên từng dòng (C1). Dòng chưa sinh hoặc bị C2 loại giữ khuôn máy
và `question_source.kind` = `template`.

Từ vựng lý do loại của C2, chốt 21/09: `not_one_line` · `insufficient_context`
· `not_a_question` · `conversational_filler` · `presumes_the_present` ·
`cites_a_provision` · `mentions_a_date` · `unsourced_number:<n>` ·
`copies_the_answer` · `too_short`. Câu bị loại được **ghi lại kèm nguyên văn**,
không thử lại ngầm cho tới khi lọt.

`presumes_the_present` đáng nói riêng: "Theo quy định pháp luật **hiện hành**,
..." là cách mở đầu thông dụng của hỏi đáp pháp luật tiếng Việt đã công bố, và
nó sai ở đây — nó ghim câu hỏi vào hiện tại của người đọc, trong khi mốc là
`as_of` và cùng một câu được hỏi ở 2016 lẫn 2026.

**Giới hạn của C2, phải nói rõ:** nó không phát hiện được câu hỏi hợp lệ về
hình thức nhưng có gold không duy nhất. "Những hành vi nào bị phạt tiền từ
20.000.000 đồng đến 40.000.000 đồng?" qua được mọi luật, nhưng đáp án đúng là
cả danh sách chứ không phải mục được giao. Prompt dạy tránh; chỉ đợt kiểm tay
mới chặn được. Đây là rủi ro lớn nhất còn lại của Gói C.

Nhà cung cấp LLM: `src/legal_crawler/llm.py`, đa nhà cung cấp qua giao thức
`chat/completions`, ưu tiên Groq. Không thêm dependency — `requests` đủ.
Anthropic không có trong bảng vì API khác hình dạng; thêm khi nào cần thật.

## Alternatives Considered

1. **Giữ một dòng cho mỗi điều khoản, `gold` là mảng.** Bị loại vì độ dài bản
   ghi đổi theo nhóm, neo `as_of` không truy vấn phẳng được, và đây là nguyên
   nhân gốc của việc worksheet cắt mất đáp án thứ tư của T3.
2. **Sáu schema riêng cho sáu nhóm.** Bị loại: khác biệt thật chỉ là hai trường
   tùy chọn, còn cái giá là mọi công cụ downstream rẽ nhánh sáu lần và metric
   giữa các nhóm khó so sánh.
3. **Dùng nguyên chín tên trường tham khảo.** Bị loại sau khi truy nguồn: năm
   trong chín tên không có nguồn công bố, và `hop_level` mô tả sai bản chất câu
   hỏi.
4. **Một boolean `graph_ready` để loại item khỏi chấm điểm.** Bị loại: không
   benchmark nào chuẩn hoá ngữ nghĩa loại-trừ-lúc-chấm; mẫu hình quan sát được
   là loại trừ bằng cấu trúc split.
5. **Chỉ ghi kappa tổng hợp trong bài báo, như ALQAC và VLegal-Bench.** Bị loại
   vì mất khả năng tính lại độ đồng thuận; giữ cả hai (thống kê trong bài,
   nhãn thô trong file) không tốn gì thêm.

## Consequences

Positive:

- Mỗi dòng tự chấm điểm được; `as_of` là cột hạng nhất.
- Chuỗi T3 không còn lệch actor–event–evidence–ngày.
- Trạng thái pháp lý đo được riêng khỏi độ khớp văn bản.
- Chi phí sửa là viết lại một hàm dựng bản ghi, không phải chú giải lại 9.331
  ứng viên: mọi thông tin cần thiết đã có trong pool và `data/temporal.sqlite`.

Tradeoffs:

- 9.331 ứng viên nở thành ~16.513 dòng QA; chuỗi câu hỏi bị lặp giữa các mốc
  của cùng một điều khoản. Ràng buộc split theo `lineage_id` là thứ giữ cho
  việc lặp đó không thành rò rỉ.
- `review` ở mức bản ghi **không có tiền lệ** ở bất kỳ bộ dữ liệu nào đã kiểm;
  đây là superset có chủ ý, phải tự bảo vệ trong khoá luận.
- `akn_ref` (Akoma Ntoso) giữ ở mức tùy chọn: mẫu cho luật Việt Nam là minh hoạ
  dựng theo template `art_5__para_2` của spec, **không phải trích dẫn spec**.
- Khẳng định closed-open của SQL:2011 chưa đối chiếu văn bản chuẩn; trong khoá
  luận nên dẫn quy ước nội bộ của repo thay vì dẫn SQL:2011 như thẩm quyền.

## Follow-Up

- **Chưa chốt:** quota trong `docs/plans/active/phase-4-vilextime.md` (T1 250 ·
  T2 400 · T3 200 · T4 150 · T5 50 · T6 100 = 1.150) đếm theo **câu** hay theo
  **điều khoản**. Dưới schema này một điều khoản T2 sinh 2 dòng, T3 sinh 3–4.
  Cần quyết định của CMT trước khi sinh T2–T6; T1 không bị ảnh hưởng vì một
  điều khoản T1 sinh đúng một dòng.
- T5 có thể cần một trường tùy chọn thứ hai cho mốc hồi tố (hiệu lực trở về
  trước theo Điều 152 có hai mốc, không phải một). Chờ cố vấn luật xác nhận 95
  ca trong 13 văn bản (Q3, D2).
- Kiểm bản phát hành chính thức của TimeQA trước khi đóng băng v1: đây là prior
  art liên quan nhất và bản mirror trên HuggingFace có thể thiếu trường.
- `reports/Schema bộ dữ liệu ViLexTime.md` giữ phần truy nguồn từng tên trường
  và các giới hạn của kết quả âm tính.
