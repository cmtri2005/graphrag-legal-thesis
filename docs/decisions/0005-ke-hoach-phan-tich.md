# 0005 Kế hoạch phân tích: giả thuyết, đại lượng chính và kiểm định, khai báo trước khi chạy test

Date: 2026-10-11

## Status

Accepted, 29/10/2026. Người duyệt: CMT, NMT. Lúc duyệt chưa hệ nào chạy trên `test`
(`runs/**/test/` chỉ có probe kiểm scorer E0, không có dự đoán của hệ nào).

ADR này phải được commit và chuyển sang Accepted **trước** khi bất kỳ hệ nào chạy trên `test`.
Ngày commit sớm hơn ngày của file kết quả test đầu tiên trong `runs/` là bằng chứng giả thuyết có
trước kết quả. Sau khi Accepted, mọi thay đổi được ghi thành amendment ở cuối file, có ngày, lý do,
và nói rõ lúc đó đã thấy kết quả test nào chưa.

## Context

ADR 0003 §7 giữ `test` cho lần chạy cuối, và scorer mặc định chỉ chấm `test`. Ràng buộc đó chưa đủ:
nếu chọn giả thuyết hoặc đại lượng chính sau khi thấy kết quả test thì vẫn là HARKing (đặt giả
thuyết sau khi biết kết quả). Mỗi hệ có khoảng 15 cấu hình, 12 chỉ số, 5 nhóm và 4 chế độ `as_of`,
nên luôn tìm được một ô "có ý nghĩa".

Ngày 11/10, nhóm chốt H0–H4, đại lượng chính theo RQ và cách thống kê (MASTER_RESEARCH_GUIDE §2.4,
§8.4, §9.3; quyết định B4, B5, B9). ADR này ghi lại các lựa chọn đó ở dạng kiểm được: mỗi kiểm
định có so sánh, đại lượng, lát dữ liệu, chiều dự đoán và quy tắc kết luận.

Các dòng không độc lập: những dòng của một lineage dùng chung câu hỏi và bằng chứng (datasheet §4).
Vì vậy đơn vị phân tích là lineage.

## Decision

### 1. Dữ liệu được phân tích

- Bản final: `data/vilextime_dataset/vilextime.jsonl`, sha256
  `7cf51ee66c7e242b0d3a7b03e62f1ed9bede6527082d9b2f8483ec75d278b366`
  (`data/vilextime_dataset/manifest.json`, schema 2.0.0, `final: true`, xuất lại 29/10 sau khi luật sư
  kiểm 117 dòng nhãn agent và đảo Q2, định nghĩa §6): 769 dòng chính;
  859 dòng silver ngoài bảng chính. Các trường `near_identical` và `repeal_mode` lấy theo ID từ
  `data/vilextime_dataset/vilextime_meta.jsonl`. Số dưới đây đếm bằng `SLICES` của
  `scripts/eval/confirm_vilextime.py` trên `giua_khoang`.
- Bảng chính `test`: 211 dòng, 165 lineage; `dev`: 151 dòng, 81 lineage (dev không đổi so với bản 28/10). "all" gồm T1, T2, T3
  và T6, trùng toàn bộ bảng chính ở cả hai split. T5 không có trong file chính; các dòng T5 nằm
  ở silver và chỉ được mô tả, không vào "all" hay kiểm định.
- Các lát khai báo trước, lấy từ cột có sẵn trong release và đếm trên bảng chính:

  | Lát (`SLICES`) | Điều kiện | Dev dòng / lineage | Test dòng / lineage |
  |---|---|---:|---:|
  | `all` | `group ∈ {T1, T2, T3, T6}` | 151 / 81 | 211 / 165 |
  | `all_answerable` | `all`, `answerable = true` | 130 / 81 | 196 / 165 |
  | `t2_near` | `group = T2`, `near_identical = true` | 16 / 8 | 8 / 4 |
  | `t2_regular` | `group = T2`, `near_identical = false` | 56 / 28 | 38 / 19 |
  | `t6_ancestor_repealed` | `group = T6`, `repeal_mode = ancestor`, `answerable = false` | 16 / 16 | 12 / 12 |
  | `t6` | `group = T6` | 42 / 21 | 30 / 15 |
  | `t2_t3` | `group ∈ {T2, T3}` | 91 / 42 | 58 / 27 |

  Trên test, T2 chỉ có 46 dòng / 23 lineage; T3 chỉ có 12 dòng / 4 lineage; T6 chỉ có 30 dòng /
  15 lineage. `t2_near` còn 8 dòng / 4 lineage, `t6_ancestor_repealed` 12 / 12. T6 giảm từ 76 lineage
  vì phần lớn dòng bãi bỏ có nội dung chuyển sang văn bản thay thế (R2, luật sư chốt 29/10).
  **Quyết định của nhóm (29/10, trước mọi lần chạy test):** H1 (XN6), H2 (XN7) và H3 (XN5) chuyển
  sang phân tích thăm dò (§8), vì lát so sánh của chúng trên `test` chỉ có 4–15 lineage. Lý do là cỡ
  mẫu, không dựa vào số dev: trên dev XN7 nghiêng ngược chiều, XN6 nghiêng đúng chiều, và cả hai
  đều bị chuyển như nhau. Họ Holm còn sáu kiểm định (§4).

- Ba chế độ `as_of` còn lại chỉ chạy truy xuất (quyết định C2) và chỉ được mô tả.
- Kiểm scorer trên bản final (E0, `score_vilextime.py --probes`, 29/10): probe oracle đạt Accuracy
  1,000 ở cả ba chế độ, trên `dev` (151 dòng) và `test` (211 dòng). Có 12/246 trích dẫn chữ không
  phân giải được, toàn bộ ở T1 của `test`. Phần lớn thiếu Điều, số còn lại dùng nhãn lạ (`Khoản a`,
  `Điểm 4`, `(V19)`). Lỗi này chỉ ảnh hưởng đến trích dẫn viết bằng chữ; trích dẫn theo mã đơn vị
  không bị. Ghi là giới hạn, không nới parser.

### 2. Hệ và cấu hình bị khóa

- Thang biểu diễn: `b2ctx → b7 → b7v → b7plus → b7pp`, truy xuất từ vựng (`--no-dense`), `k = 20`.
  Hai nấc liền nhau khác nhau đúng một trường (`tests/test_rag_systems.py`). `proposed` là `b7pp`
  cộng mở rộng 1 bước và Verifier `reject` (ADR 0004 §5).
- Baseline: `b1`, `b2`, `b2ctx`, `b5`, `b6`. `b3` (dense) và `b4` (BM25 + dense trộn thứ hạng RRF,
  không reranker) dùng `data/derived/embed/asis-vietnamese-embedding` (ADR 0004, amendment 19/10).
  Ablation: `a1`–`a4`.
- Generator: `Qwen/Qwen3-4B-Instruct-2507` rev `cdbee75`, NF4, greedy, `max_new_tokens=512`, chạy
  qua batch Colab (ADR 0004, amendment 29/10). Nó qua cổng chất lượng trên 100 dòng `dev`
  (MASTER_RESEARCH_GUIDE §7.5) và không thuộc họ Claude hay DeepSeek (ADR 0004 §3). Prompt được khóa
  theo `prompt_sha256` từng dòng và `prompt_file_sha256` trong `run.json`. Không có model kiểm độ bền ở
  lần chạy này (§7).
- Mọi tinh chỉnh chỉ làm trên `dev`. Mỗi cấu hình chạy trên `test` một lần. Mỗi lần chạy nằm trong
  `runs/`, kèm `run.json` ghi commit, hash của release, manifest, prompt và model.

### 3. Đại lượng chính

| RQ / giả thuyết | Đại lượng chính | Lát | Đại lượng phụ (chỉ mô tả) |
|---|---|---|---|
| RQ1 | Accuracy tương phản; `wrong_version` (câu trả lời chứa đoạn mà chỉ phiên bản khác có) | all; `b1`, `b2ctx` | TVER kèm `citation_coverage` và `tver_strict`; TCS |
| RQ2 | TV-Recall@1 (chỉ truy xuất); Accuracy tương phản (có sinh) | all | TCS, TVER |
| RQ3 | TV-Recall@1 trên thang chỉ truy xuất; TVER trên thang có sinh | all | VCR, MRR |
| H1 | VCR | T2 gần giống so với T2 thường | — |
| H3 | Accuracy (tức khẳng định đúng "không còn hiệu lực") | T6 nút cha bị bãi bỏ | TVER |

Định nghĩa các chỉ số là định nghĩa trong docstring của `scripts/eval/score_vilextime.py` tại commit
Accepted ADR này.

### 4. Họ kiểm định xác nhận

Tên XN để khỏi trùng với mã quyết định C1–C5 và khuyến nghị K-xx của MASTER_RESEARCH_GUIDE.

| Mã | Giả thuyết | So sánh | Đại lượng | Lát | Dự đoán | Kiểu |
|---|---|---|---|---|---|---|
| XN1 | H0, truy xuất | `b7pp` − `b7` (E1) | TV-Recall@1 | all, có đáp án | > 0 | ghép cặp |
| XN2 | H0, câu trả lời | `b7pp` − `b7` (E3) | TVER | all | < 0 | ghép cặp |
| XN3 | RQ3: siêu dữ liệu cấp văn bản | `b7` − `b2ctx` (E1) | TV-Recall@1 | all, có đáp án | > 0 | ghép cặp |
| XN4 | RQ3: chuỗi phiên bản | `b7plus` − `b7` (E1) | TV-Recall@1 | all, có đáp án | > 0 | ghép cặp |
| XN8 | RQ2: đồ thị phi thời gian | `proposed` − `b5` (E3) | Accuracy | all | > 0 | ghép cặp |
| XN9 | RQ1: giá trị của truy xuất | `b2ctx` − `b1` (E2) | Accuracy | all | > 0 | ghép cặp |

Ba kiểm định ở tầng truy xuất (XN1, XN3, XN4) chỉ dùng dòng có đáp án. Trên dòng không có đáp án,
TV-Recall chỉ chấm trúng khi lấy được lệnh bãi bỏ (`accepted_evidence` là một đơn vị `asis:event:`).
Lớp B không có đơn vị lệnh, nên `b7v`, `b7plus`, `b7pp` luôn bằng 0 ở đó do cấu trúc, không do chất
lượng truy xuất. Tác dụng của việc phát hiện bãi bỏ được kiểm ở tầng câu trả lời (XN2), và mô tả
thêm ở XN5, XN7 (§8); ở tầng truy xuất chỉ mô tả tỷ lệ dòng có điều khoản đã hết hiệu lực lọt vào
top-k.

Không đưa vào họ này, chỉ báo ước lượng kèm khoảng tin cậy: `proposed` − `b7pp` (thành phần trực
tuyến, vì H4 là thăm dò), hai bước tách bằng `b7v` (`b7v` − `b7`, `b7plus` − `b7v`), `b6`, `a1`–`a3`,
và `a4` − `proposed` (lặp lại XN5 khi có đồ thị trực tuyến).

Ba kiểm định giữ nguyên định nghĩa nhưng chuyển ra ngoài họ (quyết định 29/10, §1). Chúng được tính
bằng cùng công cụ, báo ước lượng, khoảng tin cậy và p chưa hiệu chỉnh, kết luận ghi "thăm dò":

| Mã | Giả thuyết | So sánh | Đại lượng | Lát | Dự đoán | Kiểu | Test dòng / lineage |
|---|---|---|---|---|---|---|---|
| XN5 | H3: lan truyền | `b7pp` − `b7plus` (E3) | Accuracy | T6 nút cha bị bãi bỏ | > 0 | ghép cặp | 12 / 12 |
| XN6 | H1 | VCR(T2 gần giống) − VCR(T2 thường), hệ `b2ctx` (E2) | VCR | hai lát T2 | > 0 | hai mẫu | 8 / 4 và 38 / 19 |
| XN7 | H2 | [`proposed` − `b7`] trên T6 − [`proposed` − `b7`] trên T2 ∪ T3 (E3) | Accuracy | T6; T2 ∪ T3 | > 0 | hai mẫu của hai hiệu ghép cặp | 30 / 15 và 58 / 27 |

### 5. Thống kê

- Khoảng tin cậy: bootstrap theo cụm lineage, lấy lại lineage có hoàn lại, B = 10.000, lấy khoảng
  phân vị 95%.
- Ghép cặp: hai hệ trên cùng lát dùng chung các lần lấy mẫu lại. Scorer làm điều này bằng một seed
  cố định cho mỗi ô (chế độ `as_of`, nhóm).
- Hai mẫu: hai lát khác nhau lấy mẫu lại độc lập, mỗi lát một seed.
- p hai phía của bootstrap: 2 × min(tỷ lệ lần lấy mẫu có hiệu ≤ 0, tỷ lệ có hiệu ≥ 0).
- Hiệu chỉnh Holm trên sáu kiểm định của §4 (XN1–XN4, XN8, XN9), α = 0,05.
- Báo độ lớn hiệu ứng bằng điểm phần trăm kèm khoảng tin cậy, cùng số dòng và số lineage của mẫu
  số, kể cả khi không có ý nghĩa.
- Công cụ: `scripts/eval/confirm_vilextime.py` mã hóa đúng bảng §4 (so sánh, đại lượng, lát, chiều
  dự đoán, kiểu lấy mẫu lại) và tính XN1–XN9, Holm trên sáu kiểm định của §4 (`FAMILY`);
  `score_vilextime.py --ci` cho khoảng tin cậy của từng hệ. Script phải được commit trước khi chạy test, và chạy thử trên `dev` trước đó.

### 6. Quy tắc kết luận

- Một giả thuyết được **ủng hộ** khi p sau Holm < 0,05 và ước lượng điểm đúng chiều dự đoán. Nó
  **bị bác** khi p sau Holm < 0,05 nhưng ngược chiều. Ngoài hai trường hợp đó, kết luận là **không
  đủ bằng chứng**, kèm khoảng tin cậy.
- H0 được ủng hộ khi cả XN1 và XN2 được ủng hộ. Nếu chỉ một trong hai được ủng hộ, báo là ủng hộ
  một phần và nói rõ ở tầng nào. Nếu XN1 không được ủng hộ, đề tài theo nhánh "điểm quyết định B7"
  (MASTER_RESEARCH_GUIDE §2.7): đóng góp chuyển sang tài nguyên và phân tích. Đây là kết quả đã khai
  báo trước, không phải thất bại.
- Một cải thiện chỉ được gọi là cải thiện khi đáp ứng thêm §8.6 của MASTER_RESEARCH_GUIDE: lớn hơn
  dao động giữa hai lần chạy, không đến từ thay đổi độ phủ trích dẫn, và không hệ nào vượt oracle.

### 7. Kiểm tra độ bền (mô tả, không thêm kiểm định)

- Gold độc lập (E6, khoảng 120 dòng): báo XN1, XN2, XN4, XN5 trên gold người gán bên cạnh gold của
  KG, kèm thứ hạng các nấc thang. Chưa có gold độc lập (0/75), nên chưa chạy ở lần này.
- Model kiểm độ bền trên `b2ctx`, `b7`, `proposed`: **không chạy ở lần này** (nhóm quyết 29/10, vì
  thời gian; không có model thứ hai qua cổng B1). Bảng nhiều LLM cũng hoãn. Kết luận về XN2, XN8, XN9
  vì vậy chỉ gắn với một generator, phải ghi ở phần giới hạn.
- Dao động của LLM: đo trên `dev` thay cho việc chạy hệ chính hai lần (CMT đồng ý ngày 29/10). Qua
  hai lượt Colab với hai biến thể attention, prompt giống nhau cho output giống nhau ở 553/553 dòng
  (`a3` so với `proposed`, `a2` so với `b7pp`, 121 dòng `b5` so với `b2ctx`, 130 dòng `a4` so với
  `proposed`; `runs/README.md`, 29/10). Với greedy, dao động giữa các lần chạy vì thế bằng 0. Phép
  đo này không loại trừ dao động do đổi GPU hoặc thư viện. Nếu `test` chạy trên phần cứng khác, ghi
  lại phần cứng đó trong `run.json`.
- Bỏ từng nhóm khỏi "all", và các chế độ `as_of` khác: báo cùng chiều hay không.

### 8. Phân tích thăm dò

H1, H2, H3 (XN5–XN7, §4), H4, T5, phân rã theo miền, độ nhạy theo `k`, LightRAG trên tập con (E4) và giám khảo LLM được báo
là thăm dò: có số, có khoảng tin cậy khi cỡ mẫu cho phép, không kiểm định, không dùng để ủng hộ hay
bác giả thuyết nào.

## Alternatives Considered

1. **Kiểm định McNemar trên từng dòng.** Bị loại: các dòng của một lineage không độc lập, nên giả
   định của McNemar không thỏa.
2. **Không hiệu chỉnh đa so sánh.** Bị loại: sáu kiểm định ở α = 0,05 có xác suất ít nhất một
   dương tính giả khoảng 26% nếu mọi H0 thống kê đều đúng.
3. **Bonferroni.** Kiểm soát cùng mức sai số theo họ như Holm nhưng có lực thấp hơn, nên không chọn.
4. **Một đại lượng chính cho mọi giả thuyết.** Không khả thi: B1 không có VCR, thang chỉ truy xuất
   không có Accuracy, và H3 nằm trên dòng không có đáp án.
5. **Giữ H1 so với T1.** Bị loại: cả 150/150 dòng T1 chỉ có một phiên bản, nên VCR trên T1 luôn bằng 0.

## Consequences

Positive:

- Mỗi kết luận trong khóa luận trỏ được về một dòng của §4 hoặc được gắn nhãn thăm dò.
- Nhánh "điểm quyết định B7" là kết quả hợp lệ đã khai báo trước, nên kết quả âm vẫn viết được.

Tradeoffs:

- H1, H2, H3 không có kiểm định xác nhận ở lần này: lát của chúng trên `test` quá nhỏ sau khi luật sư
  loại phần lớn dòng bãi bỏ có nội dung chuyển chỗ. Đó là cái giá của việc khai báo trung thực.
- XN2, XN8, XN9 phụ thuộc generator, và chỉ có một generator.

## Follow-Up

- Đã duyệt 29/10 (CMT, NMT); commit trước lần chạy test đầu tiên.
- Commit `confirm_vilextime.py` cùng ADR này; chạy thử trên `dev` (XN1, XN3, XN4 có ngay từ E1 dev,
  các kiểm định còn lại khi có lượt chạy thử sinh câu trả lời W1-15).
- Ghi model đã chọn (MASTER_RESEARCH_GUIDE §7.5) vào amendment của ADR 0004 trước khi chạy E2, E3.

## Amendment 2026-11-03: bộ test 2 (T2, T3, T6) làm bản lặp lại của v1.0

Ngày: 03/11/2026. Người duyệt: CMT (giao cho agent soạn và commit, 03/11). **Lúc viết amendment này đã thấy kết quả
test nào:** đã có `runs/E1/test` của v1.0 (E1, 29/10, một lần), và chưa có dự đoán nào của hệ nào trên test 2. Nếu file
dự đoán đầu tiên trên test 2 trong `runs/` có ngày sớm hơn commit này thì amendment mất hiệu lực.

Lý do: v1.0 có test nhỏ ở T3 (12 dòng / 4 lineage) và T6 (30 / 15), và đo 29/10 cho thấy phần lớn lệch A–B nằm ở dòng
đưa cho người. Test 2 (kế hoạch `docs/plans/active/vilextime-test2.md`) kiểm lại kết luận của v1.0 trên dữ liệu khác.

1. **Dữ liệu.** `data/review/test2_candidate_worksheet_v3.jsonl` sha256 `c0925d5bee759d4b6c188cb4b419d367158a591cb53111b066b3609ccda9d2d1`
   (138 câu hỏi); nhãn `data/review/test2_llm/test2_LLM_silver.tsv` sha256
   `5107c4ce4f29ff7dd8dfaf45ae1b1ca17ec90574ddf82abefc623e908d847291`. Bảng chính test 2 là các câu `verdict = dat`:
   **107 lineage / 240 dòng mốc** (T2 63 gồm 16 "gần giống"; T3 26; T6 18 gồm 15 đích danh và 3 cấp trên).
2. **Nhãn không phải của người.** Nhãn do hai LLM gán độc lập (Claude Sonnet 5.5, Codex), 53 câu lệch do Opus hòa giải,
   sáu câu phân vân kiểm lại bằng agent tra luật (Lawgical); đồng thuận hai LLM **không đạt** cổng thẻ 4.0
   (AC1 Q1–Q3 0,77–0,91; p_neg Q1 0,48, Q2 0,22, Q3 0,13; `data/review/test2_llm/agreement.json`). Không có luật sư hay
   người nào kiểm. Mọi kết quả trên test 2 phải gọi là "nhãn LLM", không dùng chung bảng với v1.0.
3. **Q4 ba mức.** Khi tính p_neg, `Có` và `Không chắc` gộp thành một mức bất lợi (Không so với {Có, Không chắc}); một câu
   `Không chắc` không bao giờ vào bảng chính (đã áp dụng khi suy ra `dat`).
4. **Kiểm định.** Giữ nguyên §4: XN1–XN4, XN8, XN9, Holm trên sáu, bootstrap theo lineage, cùng generator và cấu hình bị
   khóa ở §2, mỗi cấu hình chạy trên test 2 một lần. XN5–XN7 vẫn thăm dò (T6 chỉ 18 lineage, "cấp trên" chỉ 3).
   Test 2 báo riêng, không gộp với `test` của v1.0; kết luận chỉ "lặp lại" khi hai bảng cùng chiều.
5. **Giới hạn đã biết.** (a) nhãn LLM, T6 và T3 ít mẫu; (b) cảnh báo của agent kiểm luật rằng `data/temporal.sqlite` (kho 02/10) thiếu phiên bản của hai điều khoản chưa được kiểm trên đồ thị dùng để chạy; phiếu test 2 có đủ mốc và `provision_events.jsonl` có đủ lệnh sửa đổi tương ứng; (c) mới đo trên một generator.

### Điều chỉnh cùng ngày 03/11/2026 (trước mọi lần chạy trên test 2)

Dựng release test 2 bằng `scripts/pipeline/enrich_vilextime.py` (thêm `accepted_evidence`, dòng `giua_khoang`, `truoc_hieu_luc`) cho kết quả:
6 lineage thuộc văn bản của split `dev` nên bị loại để không rò dev. Bảng chính test 2 còn **101 lineage**, **492 dòng**
(T2 ranh giới 120, giữa khoảng 120, trước hiệu lực 38; T3 75 và 75; T6 32 và 32) trong
`data/vilextime/test2_release.jsonl`, sha256 `8c140f5c14b1dbc00a7d34954abf161d1a94fd6e69d3a56ee16d3e80c0bd4c28`.
Con số 107 / 240 ở mục 1 phía trên là trước bước này. Thang truy xuất chạy với `--release` file này và `--split test`.

## Amendment 2026-11-04: sửa đáp án ngắn của test 2 sau lần chấm E3 đầu

Ngày: 04/11/2026. Người duyệt: CMT (đồng ý phương án trong phiên làm việc 04/11). Amendment này viết **sau** khi đã chấm E3
một lần, nên đây là sửa lỗi có khai báo, không phải khai báo trước.

**Lúc viết amendment này đã thấy kết quả test nào:** toàn bộ E1 và E3 của v1.0; E1 của test 2; lần chấm E3 đầu của test 2 trong
`runs/E3_test2/test/` với Accuracy sai (`b1` 0,903; `b2ctx` 0,855; `b5` 0,872; `b7` 0,885; `b7pp` 0,885; `proposed` 0,894) và các
phán quyết dựa trên nó (XN8 "không đủ bằng chứng", XN9 "bác"). **Chưa tính Accuracy, XN7, XN8, XN9 nào trên đáp án ngắn đúng.**

1. **Lỗi.** `scripts/pipeline/enrich_vilextime.py` chỉ đọc `short_answers.jsonl`, nên `data/vilextime/test2_release.jsonl` (sha256
   `8c140f5c…`) chỉ có đáp án ngắn ở 12/460 dòng có đáp án (6/211 ở `giua_khoang`). `contains()` coi đáp án ngắn rỗng là đúng, nên ở các
   dòng còn lại, câu trả lời nào không ghi "không" cũng được tính đúng.
2. **Sửa.** Chấm bằng `data/vilextime/test2_release_v2.jsonl` (sha256
   `b299408327e3bb5c0e520d4457b27225d866afe3c7976e1c3b0aff2b8093855c`), dựng bằng `scripts/review/test2_fill_shorts.py` từ
   `data/vilextime/short_answers_test2.jsonl` (sha256 `9c827eb0…`, commit `f6ee3c0` trước release và trước mọi lần chạy trên test 2).
   Chỉ trường `short_answer` thay đổi: 448 dòng được điền, 6 dòng được thay, 6 dòng giữ nguyên. Khi hai nguồn khác nhau, lấy file của
   test 2. Cả 460 dòng đều qua `check_short_answer`.
3. **Không chạy lại gì.** Prompt không dùng đáp án ngắn, nên giữ nguyên câu trả lời của E3 và dự đoán của E1. Đây là lần chấm lại duy
   nhất; định nghĩa chỉ số, cấu hình, họ Holm và chiều dự đoán không đổi.
4. **Điều kiện hợp lệ.** XN1, XN2, XN3, XN4 và XN6 phải giống hệt lần chấm đầu, vì không phụ thuộc đáp án ngắn. Nếu khác thì dừng và
   tìm nguyên nhân, không báo số mới.
5. **Báo cáo.** Mọi số Accuracy trên test 2 lấy từ `runs/E3_test2/rescore/`. Khóa luận phải nêu lần chấm sai đầu tiên. Cột Accuracy
   trong `runs/E1_test2/test/ladder.score.json` cũng sai vì cùng lỗi, và không được dùng (thang này chỉ truy xuất, không sinh câu trả lời).
6. **Kết quả kiểm điều kiện ở mục 4 (ghi sau khi chấm lại).** Ước lượng, KTC, `p` và phán quyết của XN1, XN2, XN3, XN4, XN6 giống hệt lần chấm đầu.
   Trường duy nhất đổi là `p_Holm` của XN1 và XN4 (0,6894 → 0,4596). Mục 4 viết "giống hệt" nhưng chưa tách trường này; nó đổi là đúng vì
   Holm phụ thuộc `p` của cả họ, trong đó XN8 và XN9 đã đổi. Phán quyết của XN1 và XN4 không đổi.

## Amendment 2026-11-04 (b): kiểm độ nhạy của test 2 theo lời dặn gán nhãn v2

Ngày: 04/11/2026. Người duyệt: CMT (đồng ý phương án bốn bước trong phiên làm việc 04/11). Amendment này chỉ thêm một phép phân tích
độ nhạy. **Không đổi bảng chính, phán quyết hay kết luận H0 của test 2.** Nếu nhãn v2 đầu tiên có thời điểm sớm hơn commit này thì amendment
mất hiệu lực.

**Lúc viết amendment này đã thấy kết quả test nào:** toàn bộ E1 và E3 của v1.0 và test 2, gồm `runs/E3_test2/rescore/`, cùng các nhãn LLM cũ.
Người viết lời dặn v2 đã thấy các số này. Phiên gán v2 chạy ở thư mục riêng ngoài repo, không có khóa, nhãn cũ hay kết quả hệ thống.

1. **Vì sao cần.** Rà ngày 04/11 thấy lời dặn gán nhãn test 2 không có file trong repo. Bản dựng lại khớp từng byte với bản các phiên gán đã đọc:
   `prompts/vilextime/test2_gan_v1.md` (sha256 `761811d39e87fdd47c0fdcb4d3afa6adce426419e69e258f673f6a9b824e51a5`) và `test2_hoa_giai_v1.md` (sha256 `a981f2863660c38f17fe093d0939d4603cc9c4be06c85eba847a1da1c5a13bac`).
   Lời dặn này chỉ gồm thẻ 4.0 và vài dòng: thiếu các định nghĩa mà thẻ trỏ tới, nói về "phần tô màu" mà model không thấy, cấm tra cứu ngoài đoạn trích
   nên Q4 phần lớn chỉ có nghĩa "không thấy trong đoạn trích", thêm chỉ dẫn "phải khắt khe" ngoài thẻ, và không được hiệu chuẩn.
2. **Lời dặn v2.** `prompts/vilextime/test2_gan_v2.md` (sha256 `400b5b7b37c8ae7831d01124220a31d9276558dfa0db10f2bb83759447f01542`) và `test2_hoa_giai_v2.md` (sha256 `cde19b8aaf03f6c226345de699d3d30a4aef6ec643dcaa521c60e65b59a766de`).
   Nội dung lấy từ `docs/vilextime-dinh-nghia.md`, `docs/vilextime-annotation.md` §3, §4, §7 và điều chuyển tiếp của `test2_loc.md`. Phần viết mới: ranh giới Q1, Q2, Q3;
   cách xử lý khi thiếu đoạn nguồn; câu nói rõ giới hạn của Q4; bỏ chỉ dẫn "khắt khe". Gói có thêm chuỗi phiên bản với chỗ đổi, gợi ý chỗ chuyển (T6) và quy định giống nhất trong kho (T2, T3),
   dựng bằng `scripts/review/test2_relabel.py` và `kiem_hints.py`. Hai bên gán cùng bằng chứng. Không sửa lời dặn sau commit này.
3. **Quy trình.** LLM-A Sonnet 5.5 và LLM-B Codex gán độc lập trong phiên mới, không tra web; phiên Opus 5.5 hòa giải các câu lệch, không biết nhãn nào của model nào. Model thực tế ghi vào `runs/`. Không phải người hay luật sư.
4. **Hiệu chuẩn, trước khi gán test 2.** 68 câu của v1.0 có nhãn người độc lập (A và B cùng nhãn, hoặc luật sư tự chốt, không có phiếu AI hỗ trợ); khóa `gan_v2_key.tsv` sha256
   `2906af67cca9f5ca981ed4d9767f2b14ac0e3834ce766a685c2cef7dfe9ce8cc`, gói sha256 `11ee6bc82ed45bc2639bd1601c3e5b5898ca73ee1580e972c68104a4b10b5836`. Câu xấu khi có ít nhất một mốc `khong_dat`.
   Bỏ một câu trùng ví dụ trong lời dặn. **Cổng:** nhãn cuối so với người trên toàn tập đạt AC1 ≥ 0,80 và p_neg ≥ 0,60 (cùng ngưỡng định nghĩa §6). Báo thêm LLM-A, LLM-B, và T2, T3, T6.
   **Không đạt thì dừng:** không gán test 2, không sửa lời dặn, không đổi ngưỡng, không chạy lại; ghi kết quả vào khóa luận và phần phân tích dưới đây không tồn tại.
   Giới hạn đã biết: mẫu có 29 câu xấu nhưng 25 câu ở T6, T2 và T3 chỉ có 4, nên cổng gần như không đo được khả năng bắt câu xấu ở T2, T3; câu hỏi v1.0 viết theo quy trình khác test 2.
5. **Gán test 2.** 138 câu của phiếu v3, gói sha256 `632e5fd36d5d4527e27fc9f64cd3ef293dafa637af5b88f73f168566412ce851`. Lần duy nhất, chỉ chạy lại câu lỗi định dạng.
   Sau đó một agent tra luật (Lawgical) kiểm Q4 của các câu T6 đang đạt, không phải luật sư. Câu Q4 thành `co` hoặc `khong_chac` thì không đạt. Số câu chưa kịp kiểm được báo kèm.
6. **Phân tích.** Lọc `test2_release_v2.jsonl` chỉ còn lineage đạt theo nhãn v2 bằng `test2_relabel.py subset`; chạy `score_vilextime.py` và `confirm_vilextime.py` với `--split test --draws 10000` trên dự đoán đã có
   (`runs/E1_test2/test`, `runs/E3_test2/test`). Không sinh hay truy xuất lại. Câu đạt theo v2 nhưng ngoài release chưa có dự đoán, chỉ báo số đếm. Holm trên sáu kiểm định như §4, chạy một lần.
7. **Diễn giải.** Sáu phán quyết không đổi thì ghi "kết luận test 2 vững với lời dặn v2"; có phán quyết đổi thì ghi "kết luận nhạy với cách gán nhãn" và nêu kiểm định nào. Dù theo hướng nào, bảng chính và H0 vẫn
   theo amendment 03/11 và 04/11; phân tích này không được dùng để chọn bảng đẹp hơn. Luôn gọi là nhãn LLM, không chung bảng với v1.0.
8. **Kết quả hiệu chuẩn (ghi sau khi chạy, 04/11): KHÔNG ĐẠT, dừng theo mục 4.** Nhãn cuối so với người trên 68 câu: AC1 **0,530** (ngưỡng 0,80), p_neg 0,758 (ngưỡng 0,60). LLM-A: 0,652 và 0,800.
   LLM-B: 0,412 và 0,697. Nhãn cuối theo nhóm: T2 0,667 và 0,364 (30 câu, 2 xấu); T3 0,333 và 0,667 (6 câu, 2 xấu); T6 0,659 và 0,857 (32 câu, 25 xấu). Trong 29 câu người gán xấu, nhãn cuối bắt 25;
   trong 39 câu người gán tốt, nhãn cuối loại nhầm 12. Chưa gán câu nào của test 2 bằng v2, không sửa lời dặn, không đổi ngưỡng, không chạy lại. Mục 5–7 không thực hiện; **không có phân tích độ nhạy**.
   Bảng chính test 2 giữ nguyên, nhãn LLM. Kết quả này đo lời dặn v2, không đo trực tiếp nhãn test 2 đang dùng (lời dặn v1 chưa từng được hiệu chuẩn). Hồ sơ: `data/review/test2_llm_v2/`.
   Hai ghi chú quy trình: trước khi chạy có một lượt thử định dạng trên một câu của mẫu (nhãn thử bị bỏ, phiên riêng); `test2_relabel.py` có sửa cách đọc tham số dòng lệnh sau commit, không đổi logic. Sonnet và Opus theo log là `claude-sonnet-5-5`, `claude-opus-5-5`; Codex dùng model trong cấu hình máy (`gpt-6.1-sol`), log không xác nhận.

## Dự thảo Amendment G3: bộ test cuối theo ADR 0006 (CHƯA có hiệu lực)

Soạn: 10/11/2026 (agent, theo yêu cầu của CMT). Người duyệt: **chưa**. Tiêu đề cố ý không bắt đầu bằng `Amendment`, vì `final_run.guard_test` mở cổng test khi một commit thêm dòng `## Amendment` vào file này. Sau khi CMT và NMT duyệt, đổi tiêu đề thành `## Amendment <ngày>: ...` trong một commit riêng, rồi truyền commit đó vào `final_run.py --amendment`.

**Lúc soạn đã thấy kết quả test nào:** E1 và E3 của v1.0; E1, E3 của test 2 gồm lần chấm sai và lần chấm lại. Trên dev đã thấy mọi kết quả, gồm 15 hệ chạy với GPT-4o mini ngày 09/11 (`runs/gpt4omini_dev/`). **Chưa thấy:** mọi dự đoán trên bộ test cuối; kết quả Colab đợt 2 vẫn niêm phong theo ADR 0006 §9.

1. **Phạm vi.** Bộ test cuối phân tích theo ADR 0006. Amendment này không đổi kết luận đã báo: v1.0 có 6/6 kiểm định ủng hộ; test 2 có XN2, XN3, XN8, XN9 ủng hộ, XN1 và XN4 không đủ bằng chứng. Hai bộ này là vòng thử, báo cạnh bộ cuối, không gộp.
2. **Hệ khóa.** P = `proposed2`, chọn trên dev theo quy tắc khai trước ở ADR 0006 §2 (`runs/gpt4omini_dev/select_p.json`). Generator, danh sách hệ và chế độ truy xuất theo ADR 0006 §2 và `FINAL_GENERATION` trong `systems.py`. Mỗi cấu hình chạy bộ test cuối một lần.
3. **Họ xác nhận, Holm α = 0,05.** F1 P − `b4` Accuracy; F2 P − `b5` Accuracy; F3 P − `b4` `wrong_version`; F4 `b7` − `b2ctx`, F5 `b7plus` − `b7`, F6 `b7pp` − `b7` TV-Recall@1; F7 P − `b7pp` Accuracy trên `t6_unanswerable`, chỉ vào họ khi đủ 20 lineage. Định nghĩa đầy đủ ở ADR 0006 §3. H0 chỉ quyết bằng F6.
4. **Điều kiện trước khi đổi tiêu đề:**
   - ADR 0006 và amendment 09/11 của ADR 0004 được CMT và NMT duyệt, chuyển Accepted;
   - các chỗ `[ĐIỀN Ở G2]` của ADR 0006 đã có số thật: danh sách lineage, sha256 release và manifest, cỡ mẫu, power;
   - gold mù có kết quả theo ADR 0006 §7; nếu phải sửa đồ thị thì đã chạy lại mọi hệ trên dev và áp lại quy tắc chọn P;
   - X6 đã kết luận và dòng embedding ở ADR 0006 §2 đã điền.
