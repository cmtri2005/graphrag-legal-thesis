# 0005 Kế hoạch phân tích: giả thuyết, đại lượng chính và kiểm định, khai báo trước khi chạy test

Date: 2026-10-11

## Status

Proposed (bản nháp, chờ nhóm duyệt).

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
  vì phần lớn dòng bãi bỏ có nội dung chuyển sang văn bản thay thế (R2, luật sư chốt 29/10). **Đề xuất để nhóm duyệt trước khi Accepted:** chuyển H1
  (XN6) và H2 (XN7) sang phân tích thăm dò vì các lát so sánh quá nhỏ; cập nhật họ Holm và
  §4–§8 nếu nhóm chấp thuận. Bản Proposed này vẫn giữ định nghĩa XN6/XN7 hiện tại để nhóm
  quyết định rõ ràng, không dùng số dev để chọn giả thuyết.

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
  theo `prompt_sha256` từng dòng và `prompt_file_sha256` trong `run.json`. Model kiểm độ bền là model
  qua cổng thuộc họ khác: [chưa có, xem amendment ADR 0004].
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
| XN5 | H3: lan truyền | `b7pp` − `b7plus` (E3) | Accuracy | T6 nút cha bị bãi bỏ | > 0 | ghép cặp |
| XN6 | H1 | VCR(T2 gần giống) − VCR(T2 thường), hệ `b2ctx` (E2) | VCR | hai lát T2 | > 0 | hai mẫu |
| XN7 | H2 | [`proposed` − `b7`] trên T6 − [`proposed` − `b7`] trên T2 ∪ T3 (E3) | Accuracy | T6; T2 ∪ T3 | > 0 | hai mẫu của hai hiệu ghép cặp |
| XN8 | RQ2: đồ thị phi thời gian | `proposed` − `b5` (E3) | Accuracy | all | > 0 | ghép cặp |
| XN9 | RQ1: giá trị của truy xuất | `b2ctx` − `b1` (E2) | Accuracy | all | > 0 | ghép cặp |

Ba kiểm định ở tầng truy xuất (XN1, XN3, XN4) chỉ dùng dòng có đáp án. Trên dòng không có đáp án,
TV-Recall chỉ chấm trúng khi lấy được lệnh bãi bỏ (`accepted_evidence` là một đơn vị `asis:event:`).
Lớp B không có đơn vị lệnh, nên `b7v`, `b7plus`, `b7pp` luôn bằng 0 ở đó do cấu trúc, không do chất
lượng truy xuất. Tác dụng của việc phát hiện bãi bỏ được kiểm ở tầng câu trả lời (XN2, XN5, XN7);
ở tầng truy xuất chỉ mô tả tỷ lệ dòng có điều khoản đã hết hiệu lực lọt vào top-k.

Không đưa vào họ này, chỉ báo ước lượng kèm khoảng tin cậy: `proposed` − `b7pp` (thành phần trực
tuyến, vì H4 là thăm dò), hai bước tách bằng `b7v` (`b7v` − `b7`, `b7plus` − `b7v`), `b6`, `a1`–`a3`,
và `a4` − `proposed` (lặp lại XN5 khi có đồ thị trực tuyến).

### 5. Thống kê

- Khoảng tin cậy: bootstrap theo cụm lineage, lấy lại lineage có hoàn lại, B = 10.000, lấy khoảng
  phân vị 95%.
- Ghép cặp: hai hệ trên cùng lát dùng chung các lần lấy mẫu lại. Scorer làm điều này bằng một seed
  cố định cho mỗi ô (chế độ `as_of`, nhóm).
- Hai mẫu: hai lát khác nhau lấy mẫu lại độc lập, mỗi lát một seed.
- p hai phía của bootstrap: 2 × min(tỷ lệ lần lấy mẫu có hiệu ≤ 0, tỷ lệ có hiệu ≥ 0).
- Hiệu chỉnh Holm trên XN1–XN9, α = 0,05.
- Báo độ lớn hiệu ứng bằng điểm phần trăm kèm khoảng tin cậy, cùng số dòng và số lineage của mẫu
  số, kể cả khi không có ý nghĩa.
- Công cụ: `scripts/eval/confirm_vilextime.py` mã hóa đúng bảng §4 (so sánh, đại lượng, lát, chiều
  dự đoán, kiểu lấy mẫu lại) và tính XN1–XN9 cùng Holm; `score_vilextime.py --ci` cho khoảng tin cậy
  của từng hệ. Script phải được commit trước khi chạy test, và chạy thử trên `dev` trước đó.

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
  KG, kèm thứ hạng các nấc thang.
- Model kiểm độ bền trên `b2ctx`, `b7`, `proposed`: cùng chiều với XN2, XN8, XN9 hay không.
- Dao động của LLM: đo trên `dev` thay cho việc chạy hệ chính hai lần (CMT đồng ý ngày 29/10). Qua
  hai lượt Colab với hai biến thể attention, prompt giống nhau cho output giống nhau ở 553/553 dòng
  (`a3` so với `proposed`, `a2` so với `b7pp`, 121 dòng `b5` so với `b2ctx`, 130 dòng `a4` so với
  `proposed`; `runs/README.md`, 29/10). Với greedy, dao động giữa các lần chạy vì thế bằng 0. Phép
  đo này không loại trừ dao động do đổi GPU hoặc thư viện. Nếu `test` chạy trên phần cứng khác, ghi
  lại phần cứng đó trong `run.json`.
- Bỏ từng nhóm khỏi "all", và các chế độ `as_of` khác: báo cùng chiều hay không.

### 8. Phân tích thăm dò

H4, T5, phân rã theo miền, độ nhạy theo `k`, LightRAG trên tập con (E4) và giám khảo LLM được báo
là thăm dò: có số, có khoảng tin cậy khi cỡ mẫu cho phép, không kiểm định, không dùng để ủng hộ hay
bác giả thuyết nào.

## Alternatives Considered

1. **Kiểm định McNemar trên từng dòng.** Bị loại: các dòng của một lineage không độc lập, nên giả
   định của McNemar không thỏa.
2. **Không hiệu chỉnh đa so sánh.** Bị loại: chín kiểm định ở α = 0,05 có xác suất ít nhất một
   dương tính giả khoảng 37% nếu mọi H0 thống kê đều đúng.
3. **Bonferroni.** Kiểm soát cùng mức sai số theo họ như Holm nhưng có lực thấp hơn, nên không chọn.
4. **Một đại lượng chính cho mọi giả thuyết.** Không khả thi: B1 không có VCR, thang chỉ truy xuất
   không có Accuracy, và H3 nằm trên dòng không có đáp án.
5. **Giữ H1 so với T1.** Bị loại: cả 150/150 dòng T1 chỉ có một phiên bản, nên VCR trên T1 luôn bằng 0.

## Consequences

Positive:

- Mỗi kết luận trong khóa luận trỏ được về một dòng của §4 hoặc được gắn nhãn thăm dò.
- Nhánh "điểm quyết định B7" là kết quả hợp lệ đã khai báo trước, nên kết quả âm vẫn viết được.

Tradeoffs:

- Holm trên chín kiểm định làm H1 (57 so với 120 lineage) khó đạt ý nghĩa. Đó là cái giá của việc
  khai báo trung thực.
- XN2, XN5, XN6, XN7, XN8, XN9 phụ thuộc generator. Model kiểm độ bền chỉ là kiểm tra mô tả.

## Follow-Up

- Nhóm duyệt; ghi người duyệt và ngày; chuyển Status sang Accepted rồi commit trước lần chạy test
  đầu tiên.
- Commit `confirm_vilextime.py` cùng ADR này; chạy thử trên `dev` (XN1, XN3, XN4 có ngay từ E1 dev,
  các kiểm định còn lại khi có lượt chạy thử sinh câu trả lời W1-15).
- Ghi model đã chọn (MASTER_RESEARCH_GUIDE §7.5) vào amendment của ADR 0004 trước khi chạy E2, E3.
