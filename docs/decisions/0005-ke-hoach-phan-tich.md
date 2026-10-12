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

- Bản phát hành 11/10: `data/derived/vilextime/release.jsonl`, sha256 `118e0a26…de3dc44`
  (`data/vilextime/manifest.json`, commit `cd4927e`), schema 1.4.0, 2.730 dòng. Corpus: manifest
  sha256 `36d04090…b660975`.
- Bảng chính là `test` ở chế độ `giua_khoang`: 994 dòng, 534 lineage. "all" gồm T1, T2, T3 và T6:
  956 dòng, 515 lineage. T5 (38 dòng, 19 lineage, 3 văn bản tác động) chỉ được mô tả, không vào
  "all", không kiểm định.
- Các lát khai báo trước, lấy từ cột có sẵn trong release và đếm trên bảng chính:

  | Lát | Điều kiện | Dòng | Lineage |
  |---|---|---|---|
  | T2 gần giống | `group = T2`, `near_identical = true` | 114 | 57 |
  | T2 thường | `group = T2`, `near_identical = false` | 240 | 120 |
  | T6 nút cha bị bãi bỏ | `group = T6`, `repeal_mode = ancestor`, `answerable = false` | 121 | 121 |
  | T6 trực tiếp | `group = T6`, `repeal_mode = direct` | 70 | 35 |
  | T2 ∪ T3 | `group ∈ {T2, T3}` | 514 | 229 |
  | all, có đáp án | "all" và `answerable = true` | 800 | 515 |

- Ba chế độ `as_of` còn lại chỉ chạy truy xuất (quyết định C2) và chỉ được mô tả.

### 2. Hệ và cấu hình bị khóa

- Thang biểu diễn: `b2ctx → b7 → b7v → b7plus → b7pp`, truy xuất từ vựng (`--no-dense`), `k = 20`.
  Hai nấc liền nhau khác nhau đúng một trường (`tests/test_rag_systems.py`). `proposed` là `b7pp`
  cộng mở rộng 1 bước và Verifier `reject` (ADR 0004 §5).
- Baseline: `b1`, `b2`, `b2ctx`, `b5`, `b6`. `b3`/`b4` chỉ chạy khi đã có dense (ADR 0004 §4).
  Ablation: `a1`–`a4`.
- Generator: model rẻ nhất qua cổng chất lượng trên 100 dòng `dev` (MASTER_RESEARCH_GUIDE §7.5),
  không thuộc họ Claude hay DeepSeek (ADR 0004 §3), nhiệt độ 0. Prompt được khóa theo
  `prompt_sha256` trong `run.json`. Model kiểm độ bền là model rẻ nhất qua cổng thuộc họ khác.
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
- Dao động của LLM: hệ chính chạy hai lần trên 100 dòng `dev`. Nếu chênh lệch giữa hai lần cỡ bằng
  một hiệu ứng ở §4, kết luận về hiệu ứng đó phải được giảm nhẹ.
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
