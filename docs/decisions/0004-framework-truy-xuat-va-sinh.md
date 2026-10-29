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

**Cột kết quả chính và LLM giám khảo phải dùng model không thuộc họ Claude và không
thuộc họ DeepSeek** (master plan P5.1, datasheet §3; mở rộng 11/10, CMT). Người viết
câu hỏi không được làm thí sinh chính, vì nó quen cách hỏi và chỗ được hỏi:
- đáp án ngắn đều do `claude-opus-5-5` viết; câu hỏi do Claude viết khoảng 2/3 lineage;
- từ 07/10, `deepseek-flash` viết 225/653 lineage, và người viết trùng gần khít với
  nhóm: H3 (T6 bãi bỏ qua nút cha) 144/150 lineage do DeepSeek viết, còn T1, T2 thường,
  T3, T5 do Claude viết hết. Lợi thế "tự viết, tự trả lời" vì vậy hiện ra như một khác
  biệt giữa các nhóm, và báo tách theo người viết không gỡ được, vì H3 gần như không có
  câu Claude viết để so.

Claude hoặc DeepSeek chỉ được chạy ở bảng phụ, báo tách theo `question_source`;
bảng đó đo luôn độ lớn của thiên lệch ở các nhóm có cả hai người viết (T2 gần giống,
T6 trực tiếp). Họ Claude bị loại ngay trong code (bảng nhà cung cấp của
`vilexgraph.llm` không có Anthropic); họ DeepSeek thì không, vì nó vẫn sinh câu hỏi và
vẫn được chạy ở bảng phụ, nên quy tắc này giữ bằng tài liệu và bằng `provider`/`model`
ghi trong file kết quả.

`answerable=false` trong file nộp chỉ được sinh từ một **khẳng định** của model
("HIỆU LỰC: không"), không phải từ việc model từ chối trả lời. Format có ba
trạng thái `còn | không | không rõ`; "không rõ" giữ `answerable=true` với câu
trả lời rỗng và bị chấm sai. Lý do: khi chỉ có hai trạng thái, model dùng
"không" để nói "tôi không biết" và được chấm **đúng** trên cả 293 dòng
unanswerable vì một lý do sai — mà lý do mới là thứ benchmark đo (ADR 0003 §3).

### 4. Embedding model — CHỐT 02/10/2026 (cài đặt), chưa embed

Phương án đề xuất: dedupe theo SHA-256 text (1.455.372 đơn vị layer A chỉ có
1.247.953 text phân biệt) rồi embed trên GPU miễn phí (Colab/Kaggle T4) với
`AITeamVN/Vietnamese_Embedding` (bge-m3, 1024d); fallback local
`intfloat/multilingual-e5-small` (384d) chạy theo lô có checkpoint. Chốt chiều
vector trước khi nạp Milvus, vì `neo4j-milvus-infra.md` không chịu ước RAM khi
chưa biết chiều.

**Chốt (CMT, 02/10):** dùng `sentence-transformers` với
`AITeamVN/Vietnamese_Embedding`; client là `pymilvus` (ghim `<2.5` theo Milvus
v2.4.15) và driver `neo4j`. Cài qua `pip install -e ".[graph,embed]"` (torch bản
CPU). Máy dev không có GPU, nên embed 1,25M text phân biệt nên chạy theo lô có
checkpoint hoặc trên Colab/Kaggle; chiều vector (1024) chốt trước khi nạp Milvus.

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

- 11/10 (CMT): mở rộng quy tắc ở §3 sang họ DeepSeek, cho cả generator cột chính và
  LLM giám khảo.
- Chốt phần 4 và phần 5; chuyển Status sang Accepted khi xong.
- Đo lại RAM theo giao thức D6 khi Milvus có vector thật (P0.3b).
- Ghi amendment vào ADR 0001 cho quyết định M4: đồ thị đóng góp ở tầng kiến tạo
  biểu diễn, B7+ là một tier của hệ đề xuất chứ không phải baseline đối thủ.
- Nếu nâng Milvus 2.5 ở P4, đo analyzer tiếng Việt và xem có nên gộp BM25 về
  Milvus để chỉ còn một engine.

## Amendment 2026-10-19 (§4, embedding)

Model dense đổi sang `dangvantuan/vietnamese-embedding` (PhoBERT-base, 768 chiều), đầu vào tách
từ bằng `pyvi` ở cả lời văn và câu hỏi, `max_seq_length` 256 (CMT cho chạy 14/10). Lý do: máy duy
nhất của nhóm là CPU 4 nhân; `AITeamVN/Vietnamese_Embedding` cần khoảng 15 ngày, model mới chạy
xong 1.484.106 lời văn lớp A trong 217.756 giây (khoảng 2,5 ngày, máy khác). `verify_embed.py` trên
máy chính in `OK` ngày 19/10 (`docs/plans/active/embed-phobert-cpu.md`).

Truy xuất dense không qua Milvus: `retrieve.Dense` quét hết vector trong RAM (khoảng 2,3 GB,
khoảng 7 giây/câu), nên kết quả là top-k chính xác, không xấp xỉ, và lọc theo tier trước top-k
như công thức (4).

Hệ quả: B3, B4 là baseline dense yếu hơn mức có thể đạt (1,5% lời văn bị cắt ở 256 token). Bảng
chính không đổi vì chỉ dùng truy xuất từ vựng. Trên dev, B3 có R@1 0,260 so với `b2ctx` 0,420
(`runs/README.md`, 19/10).

## Amendment 2026-10-29 (§3, generator) — Proposed, chờ CMT duyệt

Soạn theo bước B1.5 của `docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md`. Thay quyết định
Groq ngày 27/10 (Q4): Groq giới hạn 8.000 TPM, trong khi một prompt `b2ctx` dài khoảng 18.000 token.

**Generator chính:** `Qwen/Qwen3-4B-Instruct-2507`, revision `cdbee75f17c01a7cc42f958dc650907174af0554`,
chỉ chế độ non-thinking. Không thuộc họ Claude hay DeepSeek (§3).

- Chạy: trọng số Hugging Face trên Google Colab, 4-bit NF4 (`bitsandbytes`, compute float16), greedy
  (`do_sample=False`), `max_new_tokens=512`. Phần cứng: 2×Tesla T4. Riêng `b3`, `b4` lượt 3 chạy
  trên 1×T4.
- Attention: SDPA ép kernel memory-efficient, nhân head KV (`t4_sdpa_repeat_kv`, trong
  `scripts/eval/colab_b1_runtime.py`). Lượt B1 và lượt B2 thứ 2 dùng biến thể
  `t4_sdpa_force_repeat_kv`, **chưa có trong repo**. Prompt giống nhau cho output giống nhau ở
  553/553 dòng giữa hai biến thể, nên hai biến thể không đổi kết quả trên dev.
- Đường chạy: `scripts/eval/colab_b1.py export` xuất prompt (không có nhãn), sau đó
  `colab_b1_runtime.py` trên Colab, rồi `colab_b1.py import` nạp kết quả cho scorer. Mỗi dòng có
  `prompt_sha256`; `run.json` ghi `prompt_file_sha256`, `raw_file_sha256`, model, revision, GPU.
  Cột chính không dùng `vilexgraph.llm`.

**Số đo cổng B1** (`runs/W1-09_generator/dev/qwen/`): 100 prompt `b2ctx`, `dev`, `giua_khoang`, file
prompt sha256 `991eada9…`.

- Đúng định dạng: 100/100. Bị cắt cụt (`length`): 0.
- Token trung bình: vào 5.061, ra 104. Thời gian trung bình: 12,7 giây/câu.
- CMT đã đọc 20 câu (`doc_20_cau.md`).
- Trên 151 dòng dev × 15 hệ (B2, `runs/README.md` 28–29/10): đúng định dạng 97,4–100%, cắt cụt
  tối đa 3 câu/hệ, 12,6–15,3 giây/câu.

**Chi phí:** [CMT điền: gói Colab, số giờ GPU đã dùng]. Ước cho test: 333 dòng × khoảng 13 giây,
tức khoảng 70 phút mỗi hệ.

**Model độ bền:** chưa có. `microsoft/Phi-3.5-mini-instruct` chưa chạy cổng B1. Cổng G mục 3 cần
model này trước C6; nếu không kịp, ADR 0005 §7 phải ghi bỏ kiểm tra độ bền.
