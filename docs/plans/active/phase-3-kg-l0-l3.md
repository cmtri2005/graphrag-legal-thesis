# Execution Plan: Giai đoạn 3 — Đồ thị tri thức L0–L3 (đến M2)

Date: 2026-09-18

## Status

Active. Kế hoạch chi tiết cho mục 4 của [master plan](master-plan.md); trạng
thái từng việc vẫn cập nhật ở master plan. C1–C3 đã hoàn thành ngày 18/09;
C4–C5 hoàn thành ngày 19/09; Gói C còn C6.

## Outcome

**M2 (26/10/2026):** Neo4j chứa chuỗi phiên bản thật, dựng lại được hoàn toàn
từ `data/` cộng file event. `snapshot(u, t)` trả đúng text và trạng thái hiệu
lực trên 100 truy vấn đối chiếu tay. Bốn tiêu chí xong Giai đoạn 3 trong master
plan đều có bằng chứng chạy được.

## Context

Hiện trạng ngày 18/09 (5/19 việc ✅):

| Nhóm | Đã có | Còn thiếu |
|---|---|---|
| Hạ tầng | Stack 4 dịch vụ healthy; smoke test Neo4j/Milvus PASS; có [plan hạ tầng](neo4j-milvus-infra.md) | Chưa đo RAM full corpus |
| L0–L1 | Domain model; ID thống nhất trong `ingest.py`, SQLite và event store; 1.700.484 provision | Loader Neo4j; cạnh có kiểu |
| L2 | 16.804 event áp được (2.819 `verified`), precision 58/60 ([plan L2](l2-event-store.md)) | BỔ SUNG nút mới 0%; sửa đổi có thay đổi cấu trúc; câu hai thao tác; mới 60/200 mẫu kiểm tay |
| L3 | Chuỗi offline thật: 1.592.178 version, 15.634 provision có nhiều version; event log đủ 50.700 dòng | Khoảng hiệu lực thực; loader Neo4j; kiểm chứng 100 snapshot; dẫn chiếu chéo |

Những điều đã biết mà plan phải xử lý:

- **Đã xử lý C1:** `ingest.py`, SQLite và event store dùng chung ID
  `document:`/`provision:`/`version:`; kiểm tra full index không còn ID thô.
- **Đã xử lý C2:** phiên bản 1 để mở; hiệu lực văn bản vẫn đi qua công thức (3)
  trong `temporal/validity.py`.
- **Đã xử lý C2:** 424.409 Khoản/Điểm backfill T5 có phiên bản trong index.
- **Áp thử 16.804 event** (`scripts/check/apply_provision_events.py`): 550 lỗi,
  gồm 269 sai thứ tự ngày, 170 nút không có text, 111 nút đã bị đóng trước đó.
- **Đáp án kiểm tra tự động:** 874 cạnh "Văn bản được hợp nhất" (CONSOLIDATES):
  356 văn bản hợp nhất, tất cả có trong `data/raw`, hợp nhất 621 văn bản gốc.
  Văn bản hợp nhất là text chính thức tại một ngày.

## Scope

In scope: P3.1–P3.19 của master plan, theo các gói việc dưới đây.

Out of scope:

- Tạo embedding và nạp Milvus (P5.2–P5.3). Giai đoạn 3 chỉ tính sẵn khoảng
  hiệu lực thực để sau này ghi vào Milvus.
- SUSPEND/RESUME (master plan §14).
- Phụ lục, bảng biểu, văn bản địa phương.

## Approach

Nguyên tắc: **L3 tính offline bằng Python, Neo4j chỉ nhận kết quả.** Chuỗi phiên
bản được dựng bằng chính `EventApplier`/`ValidityService` đã có test, ghi ra file
dẫn xuất trong `data/derived/`, rồi loader nạp vào Neo4j. Cách này giữ đúng ADR
0001 (xóa Neo4j vẫn dựng lại được), giữ một nơi duy nhất chứa logic thời gian,
và không phải viết lại L3 bằng Cypher.

```text
data/raw, trees, provisions, derived/subtrees ─┐
data/derived/provision_events.jsonl ───────────┼─► build_versions.py ─► data/derived/versions.jsonl
                                                │                        data/derived/event_log.jsonl
data/edges.jsonl ──────────────────────────────┘                  │
                                                                  ▼
                                                    load_neo4j.py (MERGE, chạy lại không trùng)
```

### Gói A — Hạ tầng (CMT) · P3.1, P3.2

Làm theo [neo4j-milvus-infra.md](neo4j-milvus-infra.md): `docker compose up -d`,
đợi 4 dịch vụ healthy, `verify_graph_stack.py` báo PASS, ghi RAM baseline. RAM
khi đã nạp đủ corpus thì đo ở cuối Gói D.

Xong khi: hai dịch vụ healthy, có runbook, có số RAM baseline.

### Gói B — Hoàn thiện L2 đủ bốn thao tác (CMT) · P3.11, P3.13

| Bước | Việc | Xong khi |
|---|---|---|
| B1 | Tách câu hai thao tác ("Bãi bỏ Điều 6 và sửa đổi Điều 15") thành hai câu chỉ dẫn | Test cho hai lỗi của mẫu 20260923 |
| B2 | BỔ SUNG tạo nút mới ("Bổ sung khoản 5a vào sau khoản 5 Điều 51 như sau: “5a. …”") thành `ProvisionInsertion`: nút cha, nút đứng trước, ID tất định (quyết định Q1) | Số event BỔ SUNG áp được > 0; có precision trên mẫu riêng |
| B3 | Sửa đổi có thay đổi cấu trúc (khối thêm hoặc bớt Khoản/Điểm): tách thành cập nhật text, chèn nút mới, và bãi bỏ các con bị bỏ (quyết định Q3) | Nhóm `structure_mismatch` (4.457) giảm; không tăng lỗi trên mẫu mới |
| B4 | Thay cụm từ: `new_text = old.replace(A, B)` khi A có trong text cũ | Phần còn lại vẫn `needs_review` |
| B5 | (Tùy chọn, làm nếu dư thời gian) lời văn không nằm trong ngoặc kép | — |
| B6 | Đo lại: đủ 200 mẫu kiểm tay trên các seed mới; NMT kiểm chéo 50 mẫu, tính Cohen κ | P3.13 ✅ |

Mỗi lần sửa: chạy lại pipeline, `apply_provision_events.py`, rồi kiểm trên một
seed chưa dùng (cách làm của [plan L2](l2-event-store.md)).

### Gói C — Dựng chuỗi phiên bản offline (NMT, CMT hỗ trợ) · P3.15, P3.16, P3.17

| Bước | Việc | Xong khi |
|---|---|---|
| C1 ✅ | Thống nhất ID theo `temporal/ids.py` cho `ingest`, applier và loader (Q1) | Full SQLite: 0 Document/Provision/Version dùng ID thô; test |
| C2 ✅ | `scripts/pipeline/build_versions.py`: nâng `apply_provision_events.py` lên toàn corpus. Phiên bản 1 để mở; nút T5 có phiên bản; áp event theo `(effective_on, actor)` | `versions.jsonl` 1.592.178 dòng; `event_log.jsonl` 50.700 dòng |
| C3 ✅ | Xử lý xung đột (Q2): event sai thứ tự ngày, hoặc tác động lên nút đã đóng, thì không áp và ghi vào hàng đợi review, không sắp xếp lại ngầm | Mọi event có outcome; 550 event đã chấp nhận nhưng không áp được đều có lý do |
| C4 ✅ | P3.16: tính khoảng hiệu lực thực của mỗi phiên bản (giao với mọi tổ tiên, công thức (3)) và ghi vào `versions.jsonl` | 6.108 cặp (nút, t) trên dữ liệu thật khớp `ValidityService` |
| C5 ✅ | P3.17: chỉ còn `ValidityService` trả lời "có hiệu lực tại t"; bỏ `index.version_at` | Không còn định nghĩa/lời gọi API cũ; 225 test pass, kể cả local-open nhưng document-expired |
| C6 | Test chuỗi A → B → C trên dữ liệu thật: một nút bị sửa 2 lần, một Điều bị bãi bỏ kéo theo cả cây con | Test pass; chạy hai lần cho ra file giống hệt (so sha256) |

### Gói D — Loader Neo4j (CMT) · P3.4, P3.5, P3.9, P3.2

| Bước | Việc | Xong khi |
|---|---|---|
| D1 | Schema: ràng buộc unique `id` cho Document, Provision, ProvisionVersion, LegalEvent; cạnh `CONTAINS`, `VERSION_OF`, `CAUSED_BY` | File schema chạy lại được |
| D2 | `scripts/pipeline/load_neo4j.py`: đọc `data/` + `versions.jsonl` + event, MERGE theo lô (`UNWIND`) | Chạy hai lần, số nút và cạnh không đổi; số nút khớp `data/` |
| D3 | P3.5: cạnh giữa văn bản thành 13 loại `RelationType`, khử trùng 157.795 → 128.289 | Đếm theo loại khớp `representation_benchmark.json` |
| D4 | 1.626 QPPL có text nhưng không có cây (Q4) | Theo quyết định Q4 |
| D5 | Truy vấn snapshot bằng Cypher trả cùng kết quả với `SnapshotService` trên mẫu | 200/200 khớp |
| D6 | P3.2: đo RAM và thời gian nạp full corpus | Số đo ghi vào plan hạ tầng |

### Gói E — Kiểm chứng snapshot (NMT, CMT kiểm chéo) · P3.18

| Bước | Việc |
|---|---|
| E1 | Kiểm tra tự động bằng văn bản hợp nhất: với mỗi văn bản hợp nhất (356), so `snapshot(u, ngày hợp nhất)` với text hợp nhất của cùng Điều/Khoản. Kết quả là tỷ lệ khớp trên hàng nghìn nút, không chỉ 100 |
| E2 | 100 truy vấn đối chiếu tay, phân tầng: 30 nút có ≥ 2 phiên bản · 20 nút bị bãi bỏ · 15 nút có cha bị bãi bỏ · 15 truy vấn đúng ngày chuyển phiên bản (t−1, t) · 20 nút không có event |
| E3 | Bảng kết quả gồm truy vấn, kết quả hệ thống, đáp án, người kiểm. Lỗi thì truy ngược về event và gói việc gây ra nó |

Xong khi: đạt ngưỡng Q5.

### Gói F — Dẫn chiếu chéo có nhận biết thời gian (NMT) · P3.19

"khoản 2 Điều 5 của Luật này" hoặc "Điều 3 Nghị định số X" trong text của một
phiên bản được nối tới đúng phiên bản của nút đích tại t. Dùng lại
`parse_locators`/`normalize_number` (L2) và `TargetResolver`. Không bắt buộc cho
M2; làm ở tuần 5 nếu Gói C–E đúng hạn.

### Gói G — Việc cần quyết lại · P3.6, P3.12

- **P3.6** (chuyển resolver sang Neo4j, xóa index SQLite): pipeline L2 hiện chạy
  offline trên SQLite, trong vài phút, không cần Docker. Chuyển sang Neo4j sẽ
  bắt mọi lần dựng lại phải có database đang chạy (Q6).
- **P3.12** (LLM cho ca khó): ViLexTime cần cặp phiên bản khác nhau, và 10.863
  event sửa đổi có lời văn đã là nguồn đủ lớn cho 1.150 câu hỏi. Đề xuất hoãn
  đến sau M2, xét lại ở điểm kiểm tra tuần 2.

### Lịch 5 tuần

| Tuần | CMT | NMT | Kết thúc tuần phải có |
|---|---|---|---|
| 1 · 21–27/09 | Gói A; B1; chốt Q1–Q6 | C1, C2 (bản đầu, chạy trên 100 văn bản) | Docker healthy; ID thống nhất; `versions.jsonl` mẫu |
| 2 · 28/09–04/10 | D1, D2, D3 | C2 toàn corpus, C3, C4 | **Điểm kiểm tra:** Neo4j có L0–L1; chuỗi phiên bản offline toàn corpus |
| 3 · 05–11/10 | B2, B3, B4; nạp event và phiên bản (D2) | C5, C6; E1 | Neo4j có đơn vị ≥ 2 phiên bản (P3.15); tỷ lệ khớp văn bản hợp nhất |
| 4 · 12–18/10 | B6 (200 mẫu); D5, D6 | E2, E3 | Bảng 100 truy vấn; κ của L2 |
| 5 · 19–26/10 | Sửa lỗi từ E3; D4; dự phòng | F (nếu kịp); sửa lỗi từ E3 | **M2**; bốn tiêu chí Giai đoạn 3 có bằng chứng |

Nếu điểm kiểm tra tuần 2 trễ, cắt theo thứ tự: F → B5 → B4 → P3.12 (vốn đã hoãn).
Không cắt E2, vì đó là điều kiện của M2.

Song song, ngoài Giai đoạn 3: P1.2 và P1.5 (sửa đề cương) đã quá hạn 14/09.
Đây là việc viết, nên xen vào được mà không chặn gói nào.

## Decisions

Q1–Q2 đã chốt ngày 18/09 khi triển khai C1–C3. Q3–Q6 vẫn là đề xuất và cần
nhóm xác nhận trước khi phần phụ thuộc bắt đầu.

| # | Câu hỏi | Đề xuất | Chặn |
|---|---|---|---|
| Q1 | Một sơ đồ ID cho mọi nút và phiên bản | **Đã chốt:** theo `temporal/ids.py` (`provision:<uuid>`, `version:<provision>:<n>`). Nút chèn mới: băm từ (id event, nhãn) | C1, B2, D2 |
| Q2 | Event sai thứ tự ngày, hoặc tác động lên nút đã đóng | **Đã chốt:** không áp; ghi `event_log` kèm lý do; đưa vào hàng đợi review | C3 |
| Q3 | "Sửa đổi khoản 3 như sau" mà khối mới không còn điểm c: điểm c có hết hiệu lực không? | Có, cùng ngày, vì cả đơn vị được thay. Hỏi cố vấn luật để xác nhận | B3 |
| Q4 | 1.626 QPPL có text nhưng không có cây (master plan §12) | Cho M2: chỉ nạp Document, không có Provision. Xét lại khi thiết kế ViLexTime | D4 |
| Q5 | Ngưỡng đạt của P3.18 | ≥ 95/100, giống ngưỡng đã dùng cho backfill T5 | E2 |
| Q6 | Giữ index SQLite cho pipeline offline hay chuyển hết sang Neo4j (ADR 0001 ghi là chuyển) | Giữ SQLite làm index dựng offline; Neo4j chỉ phục vụ truy vấn. Nếu chọn phương án này thì sửa ADR 0001 | Gói G |

## Risks And Recovery

- **L2 thêm tính năng lại làm giảm precision** (vòng 4 từng bị như vậy): mỗi
  thay đổi đều đo lại trên seed mới trước khi nạp.
- **Văn bản hợp nhất khác cấu trúc với văn bản gốc** (đánh số lại, gộp điều):
  E1 chỉ là kiểm tra phụ; E2 vẫn là điều kiện của M2.
- **Nạp full corpus chậm hoặc thiếu RAM:** nạp theo lô có checkpoint; nếu cần,
  tắt Milvus trong lúc nạp (runbook hạ tầng).
- **Phục hồi:** mọi đầu ra đều dẫn xuất từ `data/`. Hỏng thì chạy
  `docker compose down -v` rồi chạy lại `build_versions.py` và `load_neo4j.py`.

## Progress

- [ ] Chốt Q1–Q6 (đã chốt Q1–Q2; còn Q3–Q6)
- [ ] Gói A — hạ tầng (P3.1, P3.2)
- [ ] Gói B — L2 đủ bốn thao tác, 200 mẫu, κ (P3.11, P3.13)
- [ ] Gói C — chuỗi phiên bản offline (P3.15–P3.17)
  - [x] C1 — thống nhất ID
  - [x] C2 — dựng chuỗi toàn corpus
  - [x] C3 — log đầy đủ event áp dụng/xung đột
  - [x] C4 — tính khoảng hiệu lực thực
  - [x] C5 — hợp nhất đường tính hiệu lực
  - [ ] C6 — test chuỗi thật A → B → C và bãi bỏ cây con
- [ ] Gói D — loader Neo4j (P3.4, P3.5, P3.9)
- [ ] Gói E — kiểm chứng snapshot (P3.18)
- [ ] Gói F — dẫn chiếu chéo (P3.19)
- [ ] Gói G — P3.6, P3.12 theo quyết định

## Validation

Ánh xạ tiêu chí xong Giai đoạn 3 (master plan) sang bằng chứng:

| Tiêu chí | Bằng chứng |
|---|---|
| ID ổn định, `[start, end)` nhất quán | C1; C6 chạy hai lần cho ra file giống hệt |
| Bốn thao tác ở cấp Điều/Khoản/Điểm; bãi bỏ cha vô hiệu cây con | B2, B3; test C6; tầng "cha bị bãi bỏ" của E2 |
| Event chưa chắc chắn không bị áp âm thầm; có coverage và hàng đợi review | `status` + `event_log.jsonl`; bảng coverage từ `measure_provision_events.py` |
| Chuỗi A → B → C có test; P3.18 đạt; chạy lại không trùng | C6; E2 đạt Q5; D2 chạy hai lần |

Kiểm tra chung của repository: `python -m pytest -q`.

## Result

### C1–C3 — 18/09/2026

- `ingest.py` chuẩn hóa ID ngay tại ranh giới raw → domain, dùng constructor
  idempotent để không tạo double-prefix. Full SQLite có 23.139 Document,
  1.700.484 Provision và 1.576.199 version ban đầu; 0 ID sai prefix và 0 version
  ban đầu bị đóng tại `Document.effective_to`.
- 424.409 Khoản/Điểm backfill T5 có version; 30.313 version không có ngày vẫn
  được lưu nhưng không được đưa vào chuỗi có thể trả lời tại thời điểm `t`.
- `build_versions.py` xử lý toàn corpus theo từng văn bản, ghi file tạm rồi
  thay thế atomically, áp event ổn định theo `(effective_on, actor)` và giữ thứ
  tự nguồn khi hai khóa bằng nhau.
- `data/derived/versions.jsonl`: 1.592.178 dòng; 15.634 provision có ít nhất
  hai version; chuỗi dài nhất 4; 15.979 version có `created_by_event_id`.
- `data/derived/event_log.jsonl`: đủ 50.700/50.700 event input. Có 16.254 event
  áp thành công và 34.446 event bị từ chối/không đủ điều kiện. Trong 550 event
  đã được chấp nhận nhưng không áp được: 269 sai thứ tự ngày, 124 target không
  có version, 111 target không còn version mở, 46 văn bản đích không có
  `effective_from`. Có 21 dòng event trùng ID được nhận diện là đã áp trước đó.
- Hai lượt full corpus độc lập cho file giống nhau:
  - `versions.jsonl`: `3fcf25cb678dc68b86c1388717940e243c75c1555561df3de96e22ccbda96789`
  - `event_log.jsonl`: `a7f82aec48a974a36f0c8591383da9212f22ccc20075e5c9e9ef383aed2a3591`
- `resolve_expiry_targets.py`: 8.046/8.518 cặp provision-level resolve được
  (94,5%); `apply_provision_events.py`: 16.254/16.804 (96,7%).
- Validation repository: `python -m pytest -q` → 220 passed;
  `scripts/check/verify_pipeline.py` → all checks passed.

### C4 — 19/09/2026

- `temporal/effective_intervals.py` tính giao khoảng cục bộ của version với
  khoảng văn bản và **hợp các khoảng có hiệu lực** của toàn bộ tổ tiên. Sửa đổi
  text của cha liền ngày không cắt hiệu lực của con; bãi bỏ cha hoặc khoảng
  trống hiệu lực của cha thì có. Không gộp hai khoảng rời nhau thành một.
- `versions.jsonl` giữ `valid_from`/`valid_to` là khoảng **cục bộ**, bổ sung
  `effective_intervals` (danh sách khoảng `[start,end)`),
  `effective_interval_count`, và `effective_from`/`effective_to` chỉ khi có
  đúng một khoảng. Khi count = 0 hoặc > 1, hai trường scalar bằng `null`;
  không được hiểu `null` là khoảng mở. Text không có ngày có danh sách rỗng.
- Full corpus: 1.592.178 version; 30.313 version không có ngày và 71.225
  version có ngày nhưng không có khoảng hiệu lực thực vì bị chặn bởi hiệu lực
  văn bản/cây tổ tiên. Còn 1.490.640 version có đúng một khoảng hiệu lực thực;
  không có version với nhiều khoảng rời nhau trong snapshot hiện tại.
- Chạy `build_versions.py --verify-pairs 1000`: 6.108/6.108 cặp (nút, ngày)
  trên 1.729 văn bản ngẫu nhiên khớp `ValidityService`; bao gồm ngày ranh giới
  và ngày ngẫu nhiên quanh khoảng cục bộ. SHA-256 `versions.jsonl` mới:
  `f7941a296f2952400784e72a3309aae04dbfea75085d0d1f2810393586b16246`.
  SHA-256 `event_log.jsonl` vẫn
  `a7f82aec48a974a36f0c8591383da9212f22ccc20075e5c9e9ef383aed2a3591`.
- Test hồi quy kiểm tra cha sửa đổi liên tục, cha bãi bỏ, document hết hiệu lực,
  cha thiếu text, khoảng rời nhau và version không có ngày. `python -m pytest -q`:
  224 passed; `scripts/check/verify_pipeline.py`: all checks passed. C5 (một
  đường tính hiệu lực) và C6 (chuỗi thật A → B → C) chưa làm.

### C5 — 19/09/2026

- Xóa `TemporalIndex.version_at()`: truy vấn SQLite cũ chỉ xét
  `valid_from`/`valid_to` của version, bỏ qua hiệu lực văn bản và mọi tổ tiên.
  SQLite vẫn giữ `versions_of()`/`versions_for_document()` để đọc **lịch sử
  cục bộ** khi dựng dữ liệu; các hàm này không kết luận hiệu lực tại `t`.
- Đổi `ProvisionVersion.is_valid_at()` → `is_locally_valid_at()` và
  `VersionChain.at()` → `local_at()` để tên API không gợi nhầm hiệu lực pháp lý.
  `ValidityService.check()` gọi `local_at()` rồi kiểm tra document và tổ tiên;
  `SnapshotService` tiếp tục dùng `ValidityService`. Khoảng tính trước ở C4 là
  bộ lọc ứng viên, không phải phán quyết hiệu lực online. Script benchmark
  flat-index dùng tên `flat_local_interval_match()` và được ghi rõ là phản ví
  dụ, không phải đường trả lời pháp lý thứ hai.
- Test SQLite chứng minh version cục bộ vẫn mở tại `2025-01-01` nhưng
  `ValidityService` trả `DOCUMENT_EXPIRED` đúng ranh giới `[start,end)`; test
  cấu trúc chặn API `TemporalIndex.version_at` quay lại. Test snapshot bãi bỏ
  cha vẫn đảm bảo text con bị ẩn.
- `python -m pytest -q`: 225 passed. Rà `src/`, `scripts/`, `tests/` không còn
  định nghĩa/lời gọi `version_at`, `is_valid_at` hoặc `VersionChain.at`; các
  thao tác khoảng cục bộ được đặt tên rõ. C6 vẫn chưa làm.
