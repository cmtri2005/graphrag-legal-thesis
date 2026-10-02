# 0004 Framework truy xuất và sinh: thang biểu diễn, engine BM25, generator

Date: 2026-10-01

## Status

Proposed

Phần `Decision` 1–3 đã có bằng chứng đo và đang được dùng trong code. Phần 4
(embedding model) và phần 5 (chế độ Verifier) cần nhóm chốt trước khi chạy P4,
P3. Không embed 1,5M đơn vị trước khi phần 4 được Accepted.

## Context

Master plan §6 để mở P5.1 ("Chốt LLM sinh và embedding model") và §12 liệt kê
"Chọn embedding model và LLM" là vấn đề chặn. Đồng thời P5.2 giả định dùng
analyzer BM25 của Milvus, nhưng image đang ghim trong `docker-compose.yml` là
`milvusdb/milvus:v2.4.15`, **không có hàm BM25 native** (tính năng này có từ
Milvus 2.5). ADR 0001 Follow-Up đã yêu cầu đúng phép kiểm đó trước khi dựa vào.

Thêm vào đó, quyết định M4 ngày 01/10 (xem [plan](../plans/active/phase-5-6-framework.md))
đổi trọng tâm: giá trị của đồ thị nằm ở việc kiến tạo 𝒰ₜ ở tầng offline, nên
bảng kết quả chính là **thang biểu diễn** chứ không phải một kiến trúc duyệt đồ
thị. Điều này làm embedding rời khỏi đường găng và đổi thứ tự cần chốt.

## Decision

### 1. Thang biểu diễn là bốn tier của một pipeline

`none → document → version → propagated`, cài trong
`src/vilexgraph/framework/temporal.py`, mỗi tier thêm đúng một loại thông tin
I1–I3 của `graph_justification.md` §3. Tier `version` **bắt buộc mang cả
predicate cấp văn bản**, để thang lồng nhau:
𝒰ₜ(propagated) ⊆ 𝒰ₜ(version) ⊆ 𝒰ₜ(document). `assert_monotone` chứng minh tính
lồng trên dữ liệu thật; thang không lồng thì "nhiều thông tin hơn" lẫn với
"thông tin khác", và các cột không còn so được.

Hai cột nguồn không được trộn: khoảng **cục bộ** lấy từ `valid_from`/`valid_to`
của `data/derived/versions.jsonl`; khoảng **propagated** lấy từ
`effective_intervals` của `data/derived/corpus/versions.jsonl` (đã giao với cửa
sổ văn bản và coverage mọi tổ tiên bởi `temporal/effective_intervals.py`).
Chúng khác nhau trên 790.025/1.595.823 phiên bản (49,5%).

### 2. Engine BM25 là SQLite FTS5; Milvus vẫn là kho vector

Tín hiệu từ vựng chạy trên FTS5 với `tokenize='unicode61 remove_diacritics 0'`
— giữ dấu, vì index giữ dấu. Một bảng FTS **hai cột** (`ctx`, `body`), nên B2
(lọc cột `body` + trọng số 0 cho `ctx`) và B2+ctx dùng chung một lần dựng, và
độ lợi của chunk-header trở thành một con số được báo.

Đây **không** phải bỏ Milvus: theo ADR 0001 §1 Milvus vẫn giữ embedding của
từng `ProvisionVersion` và phục vụ truy xuất dày ở P4. Chỉ phần BM25 chuyển
engine, vì phiên bản Milvus đang ghim không cung cấp nó.

### 3. Generator đa nhà cung cấp, cấu hình bằng `.env`

Dùng `src/vilexgraph/llm.py` nguyên trạng: `chat/completions`, 6 nhà cung
cấp, không thêm dependency, Anthropic cố ý vắng mặt. Chọn nhà cung cấp và model
bằng `<PROVIDER>_API_KEY` / `<PROVIDER>_MODEL` trong `.env`, không hardcode.

**Cột kết quả chính phải dùng model không thuộc họ Claude** (master plan P5.1,
datasheet §3): câu hỏi và đáp án ngắn của ViLexTime do `claude-opus-5-5` viết,
và `question_source` của từng dòng release ghi lại điều đó để kiểm chéo được.

`answerable=false` trong file nộp chỉ được sinh từ một **khẳng định** của model
("HIỆU LỰC: không"), không phải từ việc model từ chối trả lời. Format có ba
trạng thái `còn | không | không rõ`; "không rõ" giữ `answerable=true` với câu
trả lời rỗng và bị chấm sai. Lý do: khi chỉ có hai trạng thái, model dùng
"không" để nói "tôi không biết" và được chấm **đúng** trên cả 293 dòng
unanswerable vì một lý do sai — mà lý do mới là thứ benchmark đo (ADR 0003 §3).

### 4. Embedding model — CHƯA CHỐT, cần nhóm quyết định

Phương án đề xuất: dedupe theo SHA-256 text (1.455.372 đơn vị layer A chỉ có
1.247.953 text phân biệt) rồi embed trên GPU miễn phí (Colab/Kaggle T4) với
`AITeamVN/Vietnamese_Embedding` (bge-m3, 1024d); fallback local
`intfloat/multilingual-e5-small` (384d) chạy theo lô có checkpoint. Chốt chiều
vector trước khi nạp Milvus, vì `neo4j-milvus-infra.md` không chịu ước RAM khi
chưa biết chiều.

### 5. Chế độ Verifier — CHỐT 02/10/2026

P6.6 ghi "loại bỏ **hoặc** cảnh báo" — một either/or chưa giải. Đề xuất
`--verify=off|warn|reject`, cấu hình chính là `reject` có một lần sinh lại; A3
chính là `off`. Phải chốt trước khi A3 có nghĩa.

**Chốt (CMT, 02/10):** `reject` với một lần sinh lại là cấu hình chính, A3 là `off`.
Cài đặt ở `rag/verify.py`; nguyên nhân abstain: `no_valid_evidence`,
`invalid_after_regeneration`.

### 6. Tham số mặc định

k = 20 truy xuất, Neo4j xác nhận top-20 (ADR 0001 §3), báo Recall@{1,5,10} theo
scorer; mở rộng 1 bước; λ/μ của công thức (5) là tổ hợp lồi ba tín hiệu đã
chuẩn hóa, **mỗi tín hiệu lưu riêng** trong file nộp để A1–A4 phân tích lại
không cần chạy lại. Mọi tinh chỉnh chỉ trên `dev` (P4.9, ADR 0003 §7).

## Alternatives Considered

1. **Nâng Milvus lên 2.5 để có BM25 native.** Sát P5.2 nhất, nhưng phải đổi
   image, đo lại RAM (D6) và dựng lại hạ tầng, trong khi máy dev 7 GB đã chật
   với Neo4j 4g + Milvus 4g. Chưa loại hẳn: nếu P4 cần Milvus 2.5 vì lý do
   khác thì đo lại và xem xét gộp.
2. **Tự tính vector thưa BM25 rồi nạp `SPARSE_INVERTED_INDEX` của Milvus 2.4.**
   Giữ được Milvus nhưng phải tự viết tokenize và IDF — nhiều code hơn FTS5 mà
   không thêm giá trị nào đo được.
3. **`rank_bm25` trong bộ nhớ.** Không khả thi: 2,98M đơn vị không nằm trong
   7 GB RAM.
4. **Hai bảng FTS riêng cho có/không có header.** Gấp đôi thời gian dựng và
   dung lượng; lọc cột cho cùng kết quả từ một lần dựng.
5. **Chỉ hai trạng thái hiệu lực (còn/không).** Đã thử và bị loại bằng phép đo:
   gpt-oss-120b trả "không" với TRẢ LỜI rỗng trên 7/8 dòng B1, tức dùng nó như
   "không biết".

## Consequences

Positive:

- Bảng kết quả chính chạy được **không cần embedding nào**, vì bốn tier dùng
  chung một retriever và chỉ khác bộ lọc. Embedding rời đường găng; quy mô model
  thành ablation A6.
- Không thêm dependency runtime nào: `requests` vẫn là phụ thuộc duy nhất, FTS5
  và `sqlite3` có trong stdlib.
- Mọi baseline là một dòng cấu hình của cùng một pipeline, nên không còn phản
  biện "baseline bị làm yếu".
- Index là dẫn xuất đúng ADR 0001 §2: xóa `data/derived/corpus/index.sqlite` rồi
  dựng lại bằng `scripts/eval/index_corpus.py`.

Tradeoffs:

- Lệch khỏi chữ của P5.2 ("analyzer BM25 của Milvus"). Giữ nguyên ý định (một
  đường cơ sở BM25) nhưng đổi engine, và phải nói rõ trong khóa luận.
- Hai engine cho hai tín hiệu (FTS5 cho từ vựng, Milvus cho dày) thay vì một.
  Phần hợp nhất công thức (5) do đó chạy ở tầng ứng dụng.
- `index.sqlite` thêm khoảng 2,6 GB cộng bảng BM25 bên cạnh `temporal.sqlite`.

## Follow-Up

- Chốt phần 4 và phần 5; chuyển Status sang Accepted khi xong.
- Đo lại RAM theo giao thức D6 khi Milvus có vector thật (P0.3b).
- Ghi amendment vào ADR 0001 cho quyết định M4: đồ thị đóng góp ở tầng kiến tạo
  biểu diễn, B7+ là một tier của hệ đề xuất chứ không phải baseline đối thủ.
- Nếu nâng Milvus 2.5 ở P4, đo analyzer tiếng Việt và xem có nên gộp BM25 về
  Milvus để chỉ còn một engine.
