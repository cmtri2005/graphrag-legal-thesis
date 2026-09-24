# Execution Plan: Giai đoạn 3 — Đồ thị tri thức L0–L3 (đến M2)

Date: 2026-09-18

## Status

Active. Kế hoạch chi tiết cho mục 4 của [master plan](master-plan.md); trạng
thái từng việc vẫn cập nhật ở master plan. C1–C3 đã hoàn thành ngày 18/09;
C4–C6 và D1–D3, D5 hoàn thành ngày 19/09; D6 hoàn thành ngày 21/09. E1 đã có
công cụ và phép đo đầu ngày 21/09 nhưng chưa phủ đủ 356 VBHN do thiếu body
nguồn. Gói C và phần đã chốt của Gói D xong; D4 vẫn tạm hoãn theo yêu cầu.
Gói E còn E1 coverage và E2–E3; Phase 3 tổng thể chưa hoàn thành.

## Outcome

**M2 (26/10/2026):** Neo4j chứa chuỗi phiên bản thật, dựng lại được hoàn toàn
từ `data/` cộng file event. `snapshot(u, t)` trả đúng text và trạng thái hiệu
lực trên 100 truy vấn đối chiếu tay. Bốn tiêu chí xong Giai đoạn 3 trong master
plan đều có bằng chứng chạy được.

## Context

Hiện trạng sau D2 (19/09):

| Nhóm | Đã có | Còn thiếu |
|---|---|---|
| Hạ tầng | Stack 4 dịch vụ healthy; smoke test Neo4j/Milvus PASS; có [plan hạ tầng](neo4j-milvus-infra.md) | Chưa đo RAM full corpus |
| L0–L1 | Domain model, ID thống nhất; Neo4j có 23.139 Document, 1.700.484 Provision, đủ `CONTAINS` và 124.934 cạnh văn bản có kiểu | 3.614 cạnh thiếu đích được audit, không tạo Document giả |
| L2 | 16.804 event áp được (2.819 `verified`), precision 58/60 ([plan L2](l2-event-store.md)) | BỔ SUNG nút mới 0%; sửa đổi có thay đổi cấu trúc; câu hai thao tác; mới 60/200 mẫu kiểm tay |
| L3 | Khoảng hiệu lực thực offline; Neo4j có 1.592.178 Version, 50.540 LegalEvent, 37.640 cạnh `CAUSED_BY`; event log đủ 50.700 dòng | Kiểm chứng 100 snapshot; dẫn chiếu chéo |

Những điều đã biết mà plan phải xử lý:

- **Đã xử lý C1 (Q1, 20/09):** trước đó `ingest.py` dùng UUID của cổng cho nút
  và `"<uuid>:1"` cho phiên bản, còn `EventApplier` dùng `make_version_id`. Nay
  `ingest.py` là nơi duy nhất đổi ID cổng thành ID miền theo `temporal/ids.py`;
  index, event và `expiry_targets.jsonl` đều mang ID miền. Kiểm full SQLite: 0 ID thô.
- **Đã xử lý C2:** phiên bản 1 để mở. Nếu đóng tại `effTo` của văn bản, mọi event
  trên văn bản đã hết hiệu lực sẽ lỗi "no open version"; hiệu lực của văn bản đi
  qua công thức (3) trong `temporal/validity.py`.
- **Đã xử lý C2:** 424.409 Khoản/Điểm tách từ thân văn bản (backfill T5) có phiên
  bản trong index, vì event nhắm thẳng vào chúng.
- **Áp thử 16.804 event** (`scripts/pipeline/build_versions.py`): 550 lỗi,
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
| B3 | Sửa đổi có thay đổi cấu trúc (khối thêm hoặc bớt Khoản/Điểm): tách thành cập nhật text, chèn nút mới, và bãi bỏ các con bị bỏ (quyết định Q3). **Trước khi ghi bãi bỏ, phải dò xem cùng đợt sửa có dời nội dung đó sang đơn vị khác không; ca nghi di dời thì `needs_review`, không bãi bỏ thẳng** | Nhóm `structure_mismatch` (4.447) giảm; không tăng lỗi trên mẫu mới; có mẫu kiểm tay riêng cho ca di dời |
| B4 | ✅ 20/09 Thay cụm từ: `new_text = old.replace(A, B)` khi A có trong text cũ | `missing_resulting_text` 10.816 → 6.837; áp được 16.233 → 18.840; T3 321 → 407. Ca không tìm thấy cụm từ, hoặc xóa xong còn dấu câu thừa, thành `phrase_not_found` (1.060). **Chưa kiểm tay precision — điều kiện nhận chưa đạt** |
| B5 | (Tùy chọn, làm nếu dư thời gian) lời văn không nằm trong ngoặc kép | — |
| B6 | Đo lại: đủ 200 mẫu kiểm tay trên các seed mới; NMT kiểm chéo 50 mẫu, tính Cohen κ | P3.13 ✅ |

Mỗi lần sửa: chạy lại pipeline, `build_versions.py`, rồi kiểm trên một
seed chưa dùng (cách làm của [plan L2](l2-event-store.md)).

### Gói C — Dựng chuỗi phiên bản offline (NMT, CMT hỗ trợ) · P3.15, P3.16, P3.17

| Bước | Việc | Xong khi |
|---|---|---|
| C1 ✅ | Thống nhất ID theo `temporal/ids.py` cho `ingest`, applier và loader (Q1) | Full SQLite: 0 Document/Provision/Version dùng ID thô; test |
| C2 ✅ | `scripts/pipeline/build_versions.py`: nâng lên toàn corpus. Phiên bản 1 để mở; nút T5 có phiên bản; áp event theo `(effective_on, actor)` | `versions.jsonl` 1.592.178 dòng; `event_log.jsonl` 50.700 dòng |
| C3 ✅ | Xử lý xung đột (Q2): event sai thứ tự ngày, hoặc tác động lên nút đã đóng, thì không áp và ghi vào hàng đợi review, không sắp xếp lại ngầm | Mọi event có outcome; 550 event đã chấp nhận nhưng không áp được đều có lý do, và vào `data/review/provision_events.jsonl` đủ ngữ cảnh để duyệt. Verdict của LLM hay người không bị ghi đè khi chạy lại (có test) |
| C4 ✅ | P3.16: tính khoảng hiệu lực thực của mỗi phiên bản (giao với mọi tổ tiên, công thức (3)) và ghi vào `versions.jsonl` | 6.108 cặp (nút, t) trên dữ liệu thật khớp `ValidityService`. **Đo lại ở C7** |
| C5 ✅ | P3.17: chỉ còn `ValidityService` trả lời "có hiệu lực tại t"; bỏ `index.version_at` | Không còn định nghĩa/lời gọi API cũ; test pass, kể cả local-open nhưng document-expired |
| C6 ✅ | Test chuỗi A → B → C trên dữ liệu thật: một nút bị sửa 2 lần, một Điều bị bãi bỏ kéo theo cả cây con | 2 ca snapshot v2 pass; 2 lượt full corpus có SHA-256 của cả hai artifact giống hệt |
| C7 | Hợp nhất `main` và `feature/phase3-v2` (22/09): hai nhánh cài trùng P3.15–P3.17 | Xem mục [C7](#c7--22092026) |

### Gói D — Loader Neo4j (CMT) · P3.4, P3.5, P3.9, P3.2

| Bước | Việc | Xong khi |
|---|---|---|
| D1 ✅ | Schema: ràng buộc unique `id` cho Document, Provision, ProvisionVersion, LegalEvent; cạnh `CONTAINS`, `VERSION_OF`, `CAUSED_BY` | File schema chạy lại được; 2 lượt áp dụng + check-only trên Neo4j thật pass |
| D2 ✅ | `scripts/pipeline/load_neo4j.py`: đọc `data/` + `versions.jsonl` + event, MERGE theo lô (`UNWIND`) | Hai lượt full corpus: toàn bộ 9 số đếm node/cạnh giống nhau, khớp nguồn; chuỗi A→B→C trong Neo4j pass |
| D3 ✅ | P3.5: nạp 13 loại `RelationType` từ snapshot v2; không dùng số cạnh M1 cũ | 128.548 cạnh nguồn phân biệt = 124.934 cạnh Neo4j + 3.614 unresolved; hai lượt không tăng cạnh/báo cáo; đếm theo từng loại khớp |
| D4 | 1.626 QPPL có text nhưng không có cây (Q4) | Theo quyết định Q4 |
| D5 ✅ | Truy vấn Cypher đọc snapshot từ khoảng hiệu lực thực đã nạp; đối chiếu `valid`/version ID/text với `SnapshotService` | 200/200 cặp khớp trên 32 văn bản có cây; xem bằng chứng dưới đây |
| D6 ✅ | P3.2: đo RAM và thời gian nạp full corpus | Cold load 704,0s; lượt MERGE đo chi tiết 573,9s; Neo4j peak 3,72 GiB/4 GiB; report và runbook đã cập nhật |

### Gói E — Kiểm chứng snapshot (NMT, CMT kiểm chéo) · P3.18

| Bước | Việc |
|---|---|
| E1 🟡 | Kiểm tra tự động bằng văn bản hợp nhất: kiểm kê 356 VBHN, so `snapshot(u, ngày hợp nhất)` với text hợp nhất của cùng Điều/Khoản nếu đủ dữ liệu; công bố cả phạm vi so được và tỷ lệ khớp | Công cụ và báo cáo chạy được: 51 VBHN đủ điều kiện, 5.762/7.201 cặp text khớp chính xác (80,02%). Chưa đạt phạm vi 356 vì 299 VBHN thiếu body hiển thị |
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

Q1–Q2 chốt khi triển khai C1–C3; Q3, Q4 và Q6 chốt ngày 20/09. Chỉ còn Q5
là đề xuất và cần nhóm xác nhận trước khi E2 bắt đầu.

| # | Câu hỏi | Đề xuất | Chặn |
|---|---|---|---|
| Q1 | Một sơ đồ ID cho mọi nút và phiên bản | **Chốt 20/09 (CMT): prefix đầy đủ theo `temporal/ids.py`, áp ở `ingest.py`.** Theo `temporal/ids.py` (`provision:<uuid>`, `version:<provision>:<n>`). Nút chèn mới: băm từ (id event, nhãn). Làm lúc Neo4j còn rỗng thì không tốn chi phí chuyển đổi | ~~C1~~, B2, ~~D2~~ |
| Q2 | Event sai thứ tự ngày, hoặc tác động lên nút đã đóng | **Chốt 20/09 (CMT): không áp; ghi `event_log` kèm lý do; đưa vào hàng đợi review.** Duyệt bằng LLM trước, người double-check và điều chỉnh sau | ~~C3~~ |
| Q3 | "Sửa đổi khoản 3 như sau" mà khối mới không còn điểm c: điểm c có hết hiệu lực không? | **Chốt 20/09 — cố vấn luật xác nhận: CÓ.** Khối sau "như sau:" là kỹ thuật thay toàn bộ đơn vị được nêu tên, không phải cộng dồn; điểm không được lặp lại thì hết hiệu lực cùng ngày. **Kèm cảnh báo:** nội dung có thể bị *di dời* sang đơn vị khác trong cùng đợt sửa, khi đó là đổi vị trí chứ không phải biến mất | B3 |
| Q4 | 1.626 QPPL có text nhưng không có cây (master plan §12) | **Chốt 20/09 (CMT):** cho M2 chỉ nạp Document, không có Provision. Xét lại khi thiết kế ViLexTime | D4 |
| Q5 | Ngưỡng đạt của P3.18 | ≥ 95/100, giống ngưỡng đã dùng cho backfill T5 | E2 |
| Q6 | Giữ index SQLite cho pipeline offline hay chuyển hết sang Neo4j (ADR 0001 ghi là chuyển) | **Chốt 20/09 (CMT): giữ SQLite, hoãn migrate sang sau.** Neo4j chỉ phục vụ truy vấn. Đã ghi chú vào ADR 0001; P3.6 hoãn | ~~Gói G~~ |

## Decisions đã chốt

- 2026-09-20 (cố vấn luật, Q3): khối lời văn sau "như sau:" **thay toàn bộ** đơn vị
  được nêu tên. Điểm cũ không xuất hiện lại trong khối thì hết hiệu lực cùng ngày, và
  đây không phải "văn bản im lặng nên giữ nguyên". Căn cứ: kỹ thuật trình bày văn bản
  (Nghị định 34/2016/NĐ-CP và các văn bản kế thừa). Mở khóa 4.447 ca
  `structure_mismatch` cho B3. **Ràng buộc kèm theo:** nội dung bị bỏ đôi khi được dời
  sang đơn vị khác trong cùng đợt sửa (đánh số lại, gộp vào điều khác); đó là đổi vị
  trí, không phải hết hiệu lực, nên B3 phải dò trước khi ghi bãi bỏ.
- 2026-09-20 (CMT, Q2): 550 event bị từ chối đi vào
  `data/review/provision_events.jsonl`. **Quy trình duyệt: LLM chạy trước, người
  double-check và điều chỉnh sau.** Mỗi dòng mang sẵn lời văn hiện hành, tiêu đề
  nút và câu chỉ dẫn, nên duyệt được mà không cần mở corpus. `build_versions.py`
  chỉ sở hữu dòng `method: auto_rejected`; dòng đã có verdict (`llm_reviewed`,
  `human_reviewed`) được đọc lại nguyên vẹn, theo đúng khuôn của
  `verify_temporal_candidates.py`.
- 2026-09-20 (CMT, Q6): giữ index SQLite cho pipeline offline, Neo4j chỉ phục vụ
  truy vấn. Không phải đảo quyết định của ADR 0001, chỉ là hoãn; P3.6 lùi lại.
- 2026-09-20 (CMT): **nút không có phiên bản là trong suốt khi lan truyền hiệu
  lực.** `ValidityService` trước đó bắt nút cha phải có text thì con mới có
  hiệu lực, nên 72.049 nút có text (66.008 trong VB đủ điều kiện benchmark,
  trải trên 1.640 VB) không bao giờ trả về text ở bất kỳ mốc nào: 65.443 do
  Chương/Phần/Mục vốn không có text, 6.606 do Điều/Khoản cha thiếu text. Nay
  chỉ tổ tiên bị bãi bỏ, có khoảng trống, hoặc văn bản hết hiệu lực mới chặn;
  bản thân nút thiếu text vẫn trả lời `NO_VERSION_HELD`. Căn cứ: nguyên tắc
  §11 "không coi thiếu dữ liệu là dữ liệu nói khác", nay thành D12.

Quyết định D3 ngày 19/09: với cạnh có đích không nằm trong `data/raw`, **không
tạo `Document` giả**. Chỉ nạp khi cả hai đầu có trong corpus; ghi từng cạnh
thiếu đích vào `data/derived/neo4j_unresolved_references.jsonl` và thống kê
theo loại. Phương án này giữ đúng tập 23.139 Document đã kiểm ở D2 và cho phép
backfill đích sau này mà không làm sai bản sắc văn bản.

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

- [ ] Chốt Q1–Q6 (đã chốt Q1–Q4, Q6; còn Q5)
- [ ] Gói A — hạ tầng (P3.1, P3.2)
- [ ] Gói B — L2 đủ bốn thao tác, 200 mẫu, κ (P3.11, P3.13). B4 xong 20/09 (chờ kiểm tay); còn B1, B2, B3, B6
- [ ] Gói C — chuỗi phiên bản offline (P3.15–P3.17; phần Neo4j của P3.15 đã qua D2)
  - [x] C1 — thống nhất ID
  - [x] C2 — dựng chuỗi toàn corpus
  - [x] C3 — log đầy đủ event áp dụng/xung đột + hàng đợi review
  - [x] C4 — tính khoảng hiệu lực thực
  - [x] C5 — hợp nhất đường tính hiệu lực
  - [x] C6 — test chuỗi thật A → B → C và bãi bỏ cây con
  - [ ] C7 — hợp nhất hai nhánh, dựng lại artifact, đo lại C4/D5
- [ ] Gói D — loader Neo4j (P3.4, P3.5, P3.9)
  - [x] D1 — schema node ID và hợp đồng cạnh cấu trúc
  - [x] D2 — loader corpus + version + event, chạy lại không trùng
    - [x] Bổ sung `LegalEvent -[:CAUSED_BY]-> Document` theo `actor_id`
  - [x] D3 — 13 loại cạnh văn bản, audit đích vắng mặt, chạy lại không trùng
  - [ ] D4 — Q4 (tạm bỏ qua theo yêu cầu, chưa chốt)
  - [x] D5 — snapshot Cypher đối chiếu 200 cặp với bản offline
  - [x] D6 — đo RAM và thời gian nạp full corpus
- [ ] Gói E — kiểm chứng snapshot (P3.18)
  - [ ] E1 — công cụ đối chiếu và báo cáo đã chạy; còn thiếu body ở 299 VBHN
    - [x] Triển khai phép so tự động và report từng Điều/Khoản
    - [ ] Phủ đủ nguồn VBHN theo phạm vi 356 văn bản của plan
  - [ ] E2 — 100 truy vấn kiểm tay phân tầng
  - [ ] E3 — bảng đáp án, người kiểm và truy nguyên lỗi
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
- **Đo lại ở [C7](#c7--22092026) sau khi hợp nhất hai nhánh: các số dưới đây
  đo khi quy tắc §11 chưa có trong nhánh này.**
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

### C6 — 19/09/2026

- `tests/test_real_version_chains.py` cố định hai ca trong snapshot v2 bằng ID,
  ngày, event và SHA-256 text; khi không có `data/raw`, test skip có lý do.
  Nếu có raw mà thiếu artifact hoặc ca cố định thay đổi, test fail. Test dựng
  lại **riêng hai văn bản** hai lần từ raw + event và so từng dòng với phần
  tương ứng trong artifact toàn corpus; không chỉ đọc một file đã dựng sẵn.
  Khi tái kiểm C6 trên máy có snapshot v2, chạy
  `python -m pytest -q tests/test_real_version_chains.py` và yêu cầu **2 passed**,
  không tính kết quả skipped là bằng chứng.
- **A → B → C:** Khoản 2 Điều 4 Thông tư 03/2014/TT-NHNN
  (`document:105518`) có ba text khác nhau: từ 15/03/2014, sửa lần 1 ngày
  01/09/2017 theo Thông tư 06/2017/TT-NHNN, sửa lần 2 ngày 01/01/2020 theo
  Thông tư 21/2019/TT-NHNN. Test kiểm tra SHA-256 của từng text, liên kết
  `ended_by_event_id`/`created_by_event_id`, event log `applied`, text mới
  trong event nguồn, và `ValidityService` + `SnapshotService` đúng ở hai phía
  các mốc nửa mở.
- **Bãi bỏ cha → cả cây con:** Điều 14 Nghị định 144/2025/NĐ-CP
  (`document:178250`) bị bãi bỏ từ 01/07/2026 theo Nghị định
  209/2026/NĐ-CP. Văn bản gốc chỉ hết hiệu lực 01/03/2027. Cả 5 Khoản/Điểm
  con vẫn có version cục bộ mở, nhưng khoảng hiệu lực thực đều kết thúc tại
  01/07/2026; `ValidityService` trả `PARENT_INVALID` với đúng Điều và event,
  `SnapshotService` không trả text sau mốc đó.
- Hai lượt **dựng full 23.139 văn bản** độc lập: cùng 1.592.178 version,
  50.700 outcome; SHA-256 `versions.jsonl` ở cả hai lượt là
  `f7941a296f2952400784e72a3309aae04dbfea75085d0d1f2810393586b16246`,
  SHA-256 `event_log.jsonl` là
  `a7f82aec48a974a36f0c8591383da9212f22ccc20075e5c9e9ef383aed2a3591`.
  `python -m pytest -q`: 227 passed (bao gồm 2 ca thật).
- Ba event của hai ca đều là `auto_accepted`, **chưa phải gold kiểm tay**.
  C6 chứng minh tính nhất quán/tái lập của pipeline trên dữ liệu thật, không
  thay thế đánh giá pháp lý 100 snapshot ở Gói E. Gói C hoàn thành; loader
  Neo4j và các gói còn lại của Phase 3 chưa hoàn thành.

### C7 — 22/09/2026

Hợp nhất `main` và `feature/phase3-v2`. Hai nhánh tách từ cùng `6cebde3` rồi
**cài trùng** P3.15–P3.17 (19 commit so với 14), nên `git merge` báo xung đột
11 file, trong đó `build_versions.py` và `test_build_versions.py` là add/add.
Bốn quyết định đã chốt:

- **Khoảng hiệu lực:** giữ `temporal/effective_intervals.py` (nhánh v2) vì nó
  trả **danh sách khoảng rời**, còn bản của `main` gộp thành một khoảng duy
  nhất `(versions[0].start, versions[-1].end)`. Ca cha bị bãi bỏ rồi khôi
  phục: bản gộp trả `[2020-01-01, ∞)` trong khi chính `ValidityService` của nó
  trả `False` giữa hai mốc. Phép kiểm C4 cũ không bắt được vì chỉ lấy ngày
  biên *của chính nút đó*; `_verify_effective_intervals` nay lấy thêm ngày
  biên của **mọi tổ tiên**.
- **Nút không có text là trong suốt (§11):** giữ quy tắc của `main`. Nhánh v2
  bỏ `NO_VERSION_HELD`, nên một Điều nằm dưới Chương không có text là vô hiệu
  ở mọi thời điểm và `effective_intervals` của nó rỗng. Đo A/B trên cùng 3.000
  văn bản: **3.987 → 9** version có ngày nhưng chưa từng có hiệu lực, tức
  3.978/102.325 (3,9%) version bị tắt oan nếu bỏ quy tắc này. Đo trên
  `data/provisions`, 500 văn bản mẫu: 8,4% văn bản có ≥ 1 nút cha không text.
  Hai phép đo 6.108/6.108 (C4) và 200/200 (D5) đo dưới luật cũ nên **phải đo
  lại**; C4 đã đo lại dưới đây, D5 còn chờ nạp lại Neo4j.
- **`VersionChain.at` → `local_at`:** giữ tên của v2. P3.17 tách "phiên bản cục
  bộ tại t" khỏi "có hiệu lực pháp lý tại t"; để nguyên `at()` là mời gọi nhầm,
  đúng lỗi mà `index.version_at` đã gây ra và vừa bị xóa.
- **Tên ID trong scripts:** giữ `portal_id` / `document_id` của `main`
  (`make_document_id` idempotent nên mọi biên đều chuẩn hóa được).

Những thứ `git` tự merge sạch nhưng sai, phải sửa tay: `version_chain.py` về
phía v2 (`local_at`) trong khi phía `main` còn 6 chỗ gọi `at()`;
`source_id_by_domain` thành biến chết sau khi `actors` giữ dạng dict;
`scripts/check/apply_provision_events.py` giữ trạng thái đã xóa vì
`build_versions.py` ghi `event_log.jsonl` bao trùm nó.

Hằng số ghim trong `tests/test_real_version_chains.py` sinh bởi sơ đồ ID
**trước** bản vá `8b7e98e`, nên không còn tồn tại sau hợp nhất. Đã tra lại
theo nội dung và cập nhật: `#` không bị escape trong ID provision
(`…#k2`, không phải `…%23k2`), ID event nhúng phần cục bộ
(`event:122819:…`, không phải `event:document%3A122819:…`). Ba SHA-256 text
của chuỗi A → B → C giữ nguyên.

Dựng lại toàn corpus (`build_versions.py --verify-pairs 2000`):

- 1.595.391 version (30.313 không có ngày), 124.285 nút không có text;
  18.840 event áp được và 31.783 bị từ chối trên 50.623 dòng; 797 dòng vào
  `data/review/provision_events.jsonl`.
- **12.294/12.294 cặp (nút, ngày)** trên 3.451 văn bản khớp `ValidityService`,
  nay có cả ngày biên của tổ tiên. Chỉ còn **138** version chưa từng có hiệu
  lực (số cũ 71.225 đo dưới luật không có §11 và trên event store khác).
- SHA-256 `versions.jsonl`:
  `64db0acb219368c44c527443127060b353c724d52a3d32622adad77f187a1832`;
  `event_log.jsonl`:
  `4aaa694a49a5f98a6ae458a7a697277ab94918715467fb21a2a10584c258a6a0`.
- Hai lượt full corpus cho ra hai file **giống nhau từng byte** (cùng hai
  SHA-256 trên, `cmp` pass), và cùng 797 dòng review.
- `python -m pytest -q`: 319 passed. `scripts/check/verify_pipeline.py`:
  all checks passed.

Chưa làm: nạp lại Neo4j và chạy lại D5 (`compare_neo4j_snapshots.py`) dưới
khoảng hiệu lực mới — P3.16 giữ 🟡 đến lúc đó. Merge **chưa commit**.

### D1 — 19/09/2026

- `scripts/pipeline/neo4j_schema.cypher` tạo bốn unique constraint có tên cố
  định cho `id` của `Document`, `Provision`, `ProvisionVersion`, `LegalEvent`.
  `IF NOT EXISTS` cho phép chạy lại; `init_neo4j_schema.py` đối chiếu nội dung
  file với bốn câu lệnh được duyệt rồi đọc `SHOW CONSTRAINTS` để bắt trường hợp
  trùng tên nhưng sai nhãn/thuộc tính/loại constraint. Có chế độ `--check-only`.
- `graph/neo4j_schema.py` là hợp đồng nhãn và cạnh cho D2: `Document` →
  `Provision` và `Provision` → `Provision` qua `CONTAINS`, `ProvisionVersion` →
  `Provision` qua `VERSION_OF`, `ProvisionVersion` → `LegalEvent` qua
  `CAUSED_BY`. Neo4j D1 **không** ép kiểu hai đầu cạnh; D2 phải kiểm tra khi nạp.
  Vai trò event tạo/kết thúc version cũng phải giữ tách biệt ở D2.
- Neo4j local: áp dụng schema **hai lượt** đều báo 4/4 constraint hợp
  lệ; `--check-only` pass; sau đó đọc trực tiếp còn **0 node, 0 cạnh**. Không
  có corpus nào được nạp ở D1. Thử tạo hai `Document` trùng `id` trong một
  transaction: Neo4j từ chối node thứ hai; rollback xong vẫn có 0 `Document`.
  Bảy test mới có cả ca đúng, chạy lặp và ca sai schema; toàn suite
  `python -m pytest -q`: **234 passed**.
- Unique constraint không buộc `id` phải tồn tại trên mọi node. D2 phải không
  tạo node thiếu `id`, chạy hai lần không sinh trùng và so số lượng với `data/`.
  P3.4/Gói D/Phase 3 **chưa xong**; bước kế tiếp là D2.

### D2 — 19/09/2026

- `scripts/pipeline/load_neo4j.py` đọc `data/temporal.sqlite` (index dẫn xuất
  bởi `build_store.py --with-subtrees` từ raw/tree/subtree), đối chiếu toàn bộ
  tập Document ID với `data/raw`, rồi nạp `versions.jsonl`,
  `provision_events.jsonl` và `event_log.jsonl`. Mọi batch dùng `UNWIND` +
  `MERGE` theo ID ổn định trong một transaction; thiếu endpoint thì rollback
  batch với lỗi rõ ràng. Có kiểm tra D1 constraint trước và chín số đếm cuối.
- LegalEvent được gom theo ID: 50.700 dòng nguồn thành **50.540 node** (160
  dòng lặp ID). `source_and_audit_json` giữ **từng dòng nguồn và outcome**,
  kể cả trường hợp các bản lặp khác `status_reason`; không suy ra một event
  mới từ mỗi dòng lặp. Version giữ text, khoảng cục bộ, số/khoảng hiệu lực
  thực và provenance; `CAUSED_BY.role` phân biệt `created` và `ended`.
- Hai lượt full corpus độc lập trên cùng Neo4j (704,0s và 553,9s), đều đạt:

  | Nhóm | Số lượng mỗi lượt |
  |---|---:|
  | `Document` | 23.139 |
  | `Provision` | 1.700.484 |
  | `ProvisionVersion` | 1.592.178 |
  | `LegalEvent` | 50.540 |
  | `Document → CONTAINS → Provision` | 101.063 |
  | `Provision → CONTAINS → Provision` | 1.599.421 |
  | `VERSION_OF` | 1.592.178 |
  | `CAUSED_BY` role `created` | 15.979 |
  | `CAUSED_BY` role `ended` | 21.661 |

- Trước full load, probe Cypher nạp **hai lượt trong cùng transaction** giữ
  5 node/4 cạnh rồi rollback sạch. Sau full load, chuỗi thật A→B→C của C6
  trong Neo4j có đúng ba version, đúng SHA-256 text và đúng các cạnh event
  tạo/kết thúc. `python -m pytest -q`: **241 passed**, gồm test mới về event
  ID lặp, audit sai, event thiếu, hai vai trò event và batch thiếu endpoint.
  `python scripts/check/verify_pipeline.py`: **all checks passed** trên nguồn.
- D2/P3.4 hoàn thành, phần nạp version/event của P3.15 đã có bằng chứng.
  **Chưa** nạp 13 loại cạnh văn bản (D3), chưa quyết Q4 (D4), chưa đối chiếu
  Cypher với `SnapshotService` (D5), chưa đo RAM (D6). Gói D/Phase 3 chưa xong.
- Lưu ý cho D3: snapshot hiện tại có **128.548 dòng** `data/edges.jsonl`
  (`verify_pipeline.py` pass), trong khi `representation_benchmark.json` M1
  ghi **128.289 cạnh phân biệt** từ snapshot cũ 22.550 văn bản. Phải đối
  chiếu/đóng băng baseline snapshot v2 trước khi dùng ngưỡng 128.289 của D3;
  D2 không nạp hoặc sửa các cạnh này.

### D2 extension — 22/09/2026: văn bản nguồn gây ra event

- Theo yêu cầu minh họa chuỗi nhân quả, bổ sung cạnh có hướng
  `LegalEvent -[:CAUSED_BY]-> Document` với đích là `actor_id` của event.
  Cạnh `ProvisionVersion -[:CAUSED_BY {role}]-> LegalEvent` giữ nguyên; role
  `created`/`ended` chỉ thuộc cạnh version → event. `target_document_id` là
  văn bản bị tác động, **không phải** văn bản gây ra event.
- Loader kiểm toàn bộ `actor_id` có trong `data/raw` trước khi ghi, dùng
  `MATCH` hai endpoint và `MERGE` cạnh, không tạo `Document` giả. Thêm số đếm
  hậu kiểm riêng cho cạnh event → document, nên chạy lại loader không nhân đôi.
- Snapshot local: 50.540 event phân biệt, 50.540 `actor_id` khớp Document;
  không có actor thiếu. Trên Neo4j đang chạy đã backfill theo lô: **50.540
  cạnh / 50.540 event**, 0 cạnh nối sai `actor_id`. Chạy lại phép backfill vẫn
  50.540 cạnh; số cạnh version → event giữ **37.640**, số Document giữ 23.139.
  Test tập trung `tests/test_load_neo4j.py` và `tests/test_neo4j_schema.py`:
  **17 passed**. Chưa chạy lại toàn bộ full-corpus loader sau thay đổi này;
  Neo4j hiện tại được cập nhật trực tiếp và lần nạp lại sau sẽ dùng loader mới.

### D3 — 19/09/2026

- `neo4j_references.py` ánh xạ cố định 13 `reference_type` đã xác minh sang
  13 `RelationType`; `load_neo4j_references.py` kiểm tra mã, nhãn tiếng Việt
  và `group` theo `data/reference_type_map.json` **trước khi ghi Neo4j**.
  Cạnh được chuẩn hóa theo `(source_id, target_id, reference_type)` và nạp
  theo batch `UNWIND`/`MERGE` với hai đầu `:Document`. Không có lệnh tạo node
  trong D3; thiếu endpoint ở Neo4j hoặc quan hệ trùng ngoài dự kiến thì batch
  rollback. Số Document vẫn **23.139**.
- Baseline snapshot v2 là `data/edges.jsonl` SHA-256
  `18d5f36ef0ed4ce31bacf53519aa8c2b4ea9c664335c393e74b241a3a8c756e6`:
  **128.548 dòng = 128.548 bộ ba phân biệt, 0 trùng**. M1 cũ (128.289 cạnh,
  22.550 văn bản) không dùng làm ngưỡng của snapshot v2. Hai lượt D3 trên
  Neo4j (14,4s; 7,9s) cho đúng cùng số cạnh từng loại:

  | `RelationType` | Nguồn v2 | Neo4j | Thiếu đích |
  |---|---:|---:|---:|
  | `REPEALS` | 7.498 | 7.468 | 30 |
  | `ANNOUNCES` | 23 | 22 | 1 |
  | `ISSUED_UNDER` | 67.644 | 65.835 | 1.809 |
  | `REFERS_TO` | 18.009 | 16.400 | 1.609 |
  | `HALTS_ENFORCEMENT` | 33 | 33 | 0 |
  | `CORRECTS` | 132 | 132 | 0 |
  | `CONSOLIDATES` | 874 | 874 | 0 |
  | `GUIDES` | 349 | 297 | 52 |
  | `DETAILS` | 19.566 | 19.488 | 78 |
  | `AMENDS` | 6.975 | 6.959 | 16 |
  | `SUSPENDS` | 31 | 31 | 0 |
  | `REPLACES` | 7.400 | 7.383 | 17 |
  | `INTERPRETS` | 14 | 12 | 2 |
  | **Tổng** | **128.548** | **124.934** | **3.614** |

- `data/derived/neo4j_reference_load_report.json` ghi checksum nguồn và
  số đếm từng loại; `neo4j_unresolved_references.jsonl` ghi đủ **3.614 cạnh
  thiếu đích thuộc 1.863 target ID**, gồm 3.473 `open_citation` và **141
  `genealogy`**. Mỗi file được thay thế atomically sau khi Neo4j pass; hai
  lượt sinh cùng SHA-256 (`e8e92706df1a8a1f2ee75d40ba84b194dfdd5f49ff4eca32657e7f3941462c3c`
  và `17d50a0a4ebef8847eef630678537489a1f9f165d44e6344e3caec4360c15f41`).
- Probe trên cạnh thật: nạp hai lượt trong transaction vẫn có một quan hệ,
  rollback xong không lưu cạnh thử. Test mới chứng minh mapping 13 loại, khử
  trùng, audit đích thiếu, từ chối mã/nhãn/sources sai và rollback khi Neo4j
  thiếu endpoint. `python -m pytest -q`: **249 passed**.
- D3/P3.5 hoàn thành theo phạm vi văn bản **đã thu thập**. 141 cạnh phả hệ
  thiếu đích cần rà soát/backfill riêng; không được xem 124.934 cạnh Neo4j là
  toàn bộ 128.548 cạnh nguồn. D4–D6 và Phase 3 vẫn đang mở.

### D5 — 19/09/2026

- `graph/neo4j_snapshot.py` truy vấn `Provision` → `ProvisionVersion` bằng Cypher,
  lọc theo ngày trong `effective_intervals_json` đã tính offline ở C4 và nạp
  ở D2. Dùng APOC JSON có sẵn trong `docker-compose.yml` để đọc các cửa sổ;
  không tính lại giao khoảng với tổ tiên trong Cypher, không sửa Neo4j.
  Khi không có cửa sổ hiệu lực thì không trả text; khoảng `[start, end)` giữ
  đúng ngày chuyển phiên bản. Reader phân biệt provision vắng mặt với
  provision có thật nhưng không hiệu lực, và báo lỗi nếu các version được trả
  về có ID trùng, JSON/count hỏng hoặc nhiều version cùng hiệu lực.
- `scripts/check/compare_neo4j_snapshots.py` chọn mẫu cố định seed `20260919`
  từ **32 văn bản có cây**, dựng trạng thái offline từ SQLite +
  `versions.jsonl` + event nguồn, rồi so `valid`, version ID và nguyên văn text
  giữa Neo4j với `SnapshotService` cho **200 cặp (provision, ngày) phân biệt**.
  Các ca bắt buộc gồm chuỗi A → B → C và mốc bãi bỏ Điều + con vào
  `2026-07-01`. Phân tầng thực chạy: 50 ca ranh giới, 25 cha vô hiệu,
  40 ranh giới văn bản, 25 bất hoạt, 60 hợp lệ. Kết quả **200/200 khớp**;
  report từng cặp và SHA-256 text ở
  `data/derived/neo4j_snapshot_parity_report.json` (file dẫn xuất, không commit).
- `tests/test_neo4j_snapshot.py` có 8 test dương/âm cho khoảng nửa mở,
  nhiều cửa sổ rời nhau, provision không tồn tại, khoảng lỗi, version trùng và
  cùng ngày chồng lấn. Full suite: **257 passed**.
- Phạm vi D5 là **tính nhất quán của read model** (trạng thái, version và text),
  không đánh giá đúng/sai pháp lý của text, không đối chiếu đầy đủ reason,
  event object hay provenance của `SnapshotResult`. E2 vẫn phải có 100 truy
  vấn kiểm tay; tại thời điểm chốt D5, D4 và D6 vẫn mở. Không tính 200 cặp này
  vào E2.

### D6 — 21/09/2026

- `load_neo4j.py --report PATH` ghi atomically số đếm đã kiểm, kích thước bốn
  input, tổng thời gian và timing riêng cho preflight, Document, Provision,
  LegalEvent, ProvisionVersion, `CONTAINS`, `CAUSED_BY` và hậu kiểm. Report chỉ
  được công bố sau khi chín số đếm nguồn–Neo4j đều khớp.
- `measure_graph_resources.py` đọc `docker stats`/`docker inspect`, có chế độ
  chỉ đo stack và `--run-loader` để lấy mẫu trong suốt một lượt MERGE toàn
  corpus. Công cụ không có lệnh xóa graph/volume, không ghi credential vào
  report, báo lỗi nếu container thiếu, unhealthy hoặc bị OOM. Parser và phép
  tổng hợp start/final/peak có test dương/âm.
- Thời gian trên máy đo (4 logical CPU, WSL2 nhìn thấy 11,68 GiB RAM): lượt nạp
  đầu vào graph rỗng ở D2 là **704,0s**; lượt MERGE thứ hai ở D2 **553,9s**;
  lượt D6 **573,9s**. Timing lượt D6: preflight 7,2s; Document 4,3s;
  Provision 170,3s; LegalEvent 4,9s; Version 231,4s; `CONTAINS` 152,1s;
  `CAUSED_BY` 1,3s; kiểm số đếm 2,3s.
- Trong 53 mẫu lúc MERGE, Neo4j từ 1.517,6 MiB lên đỉnh **3.813,4 MiB**,
  tương đương **93,09%** giới hạn 4 GiB. Đỉnh/final của Milvus là
  103,4/103,3 MiB, MinIO 91,1/91,1 MiB, etcd 35,3/29,4 MiB; tổng các đỉnh là
  **3,95 GiB**. Hậu kiểm steady cuối gồm hai mẫu, vẫn khoảng 3,95 GiB toàn
  stack, riêng Neo4j 3.812,4 MiB. Milvus chưa có embedding thật nên con số này không
  dự báo RAM ở P5.3.
- Sau phép đo, cả bốn container `healthy`, `OOMKilled=false`, `RestartCount=0`.
  Chín số đếm vẫn đúng (23.139 Document, 1.700.484 Provision, 1.592.178
  Version, 50.540 Event và đủ các cạnh); lượt MERGE không tạo trùng. Smoke test
  đã được siết để thật sự assert node/vector đọc lại đúng và luôn dọn state;
  Neo4j + Milvus đều PASS. Full suite: **268 passed**.
- Report dẫn xuất: `data/derived/neo4j_resource_report.json`, report timing
  loader cùng tên `.loader.json`, và `neo4j_resource_steady_report.json`.
  Các file này không phải nguồn sự thật và không commit; số đo bền vững được
  ghi tại [plan hạ tầng](neo4j-milvus-infra.md). D6/P3.2 hoàn thành, nhưng cần
  tăng giới hạn để Neo4j có ít nhất 0,5 GiB headroom trước workload truy vấn
  song song; phải đo lại khi Milvus có vector thật.

### E1 — 21/09/2026

- `scripts/check/compare_consolidated_snapshots.py` quét toàn bộ 874 cạnh
  `CONSOLIDATES` từ snapshot v2, kiểm kê **356 VBHN**. Với nhiều target, chỉ
  chọn văn bản gốc khi số văn bản đó là target được dẫn đầu tiên trong phần
  mở đầu VBHN; không chọn theo thứ tự cạnh hoặc đoán bằng ngày. Ngày truy vấn
  là `issueDate` của VBHN, không tự bù ngày thiếu. Đọc `SnapshotService` từ
  SQLite, `versions.jsonl` và event nguồn bằng cùng loader offline đã dùng ở
  D5; không sửa corpus hay Neo4j.
- Bộ căn chỉnh chỉ dùng **Điều có số duy nhất** và **Khoản có số duy nhất dưới
  đúng Điều**. Không join UUID giữa hai văn bản, không fuzzy match để chọn
  target; bỏ các khóa trùng, dừng trước phụ lục/chữ ký, tách Điểm ra khỏi text
  Khoản. So text sau Unicode NFC và gộp whitespace; khác dấu câu/từ ngữ vẫn
  là sai khác. Report có nguồn, thời điểm, ID, phiên bản, SHA-256 và đoạn đầu
  hai phía; có checksum của `edges.jsonl`, `versions.jsonl` và event nguồn.
- Kết quả thật: **51/356 VBHN** đủ điều kiện đối chiếu; **299** body không có
  chữ hiển thị, **2** không có marker Điều, **4** văn bản gốc không có cây.
  Trong 51 VBHN này có **7.688 đơn vị nguồn** Điều/Khoản có khóa duy nhất;
  **20 khóa nguồn trùng** bị loại trước khi tạo cặp. **7.201 cặp có text ở cả
  hai phía**, trong đó **5.762 khớp chính xác = 80,02%**; 1.393 khác text và
  46 chỉ khác phần tiêu đề Điều. Ngoài mẫu số text: 406 đơn vị không có khóa
  tương ứng trong cây gốc, 42 marker bãi bỏ khớp trạng thái, 36 marker bãi bỏ
  trái trạng thái snapshot và 3 snapshot không có text hiệu lực.
- Trong 1.393 sai khác text, 1.260 đang ở version 1, 130 ở version 2 và 3 ở
  version 3; đây là **hàng đợi điều tra**, chưa được quy tất cả cho lỗi trích
  xuất event vì cũng có khác biệt định dạng, nguồn và căn chỉnh. Tỷ lệ 80,02%
  chỉ có mẫu số là 7.201 cặp đủ điều kiện, **không phải độ chính xác pháp lý
  toàn bộ corpus** và không thay thế 100 ca kiểm tay E2. D5 đã đối chiếu
  Neo4j–offline 200/200 trên cùng read model, nhưng không phải gold VBHN.
- Chạy lại: `python scripts/check/compare_consolidated_snapshots.py`; báo cáo
  dẫn xuất `data/derived/consolidated_snapshot_report.json` (không commit).
  Test có ca khớp, sai khác, body rỗng, marker/chú thích, khóa trùng và chọn
  văn bản gốc; full suite **275 passed**. Báo cáo chạy hai lượt có cùng SHA-256
  `f6c352879a42c2016965cfc9fe1ed24d71b0011c2f5a3fc8e59e9fc2c7b38ec8`.
  **Chưa chốt E1 theo phạm vi 356 VBHN**: muốn tăng coverage phải phục hồi
  body nguồn và chạy lại, không điền đoán từ graph. P3.18/M2 vẫn mở đến khi
  E2–E3 có đáp án kiểm tay và đạt Q5.

### Mở rộng vận hành — 23/09/2026: bảng Parquet trên GCS và BigQuery

- Bổ sung pipeline dẫn xuất bảy bảng Parquet có schema cố định từ SQLite,
  version/event JSONL và cạnh nguồn: `documents`, `provisions`,
  `provision_versions`, `legal_events`, `containment_edges`, `causal_edges`,
  `document_reference_edges`. Export theo batch, nén ZSTD, ghi manifest chứa
  hash input/file, schema và row count; thư mục đích bất biến và chỉ được công
  bố sau khi export hoàn tất.
- Uploader kiểm lại checksum, schema và số dòng trước khi ghi GCS; dùng
  precondition không ghi đè và upload `manifest.json` cuối cùng. Có thể tạo
  bảy BigQuery external table cùng vùng với bucket, nên dữ liệu Parquet không
  bị sao chép sang BigQuery storage.
- Đã phát hành snapshot
  `gs://graphrag-legal-thesis/tables/20260923-phase3-v2-d7ada236/`: 25 file,
  246.460.861 byte. BigQuery dataset `graphrag-509313.legal_graph` tại
  `us-east1` có đúng 23.139 Document, 1.700.484 Provision, 1.592.178 Version,
  50.540 Event, 1.700.484 cạnh containment, 88.180 cạnh causal và 128.548 cạnh
  dẫn chiếu nguồn. Trong cạnh dẫn chiếu, 124.934 đích resolve được và 3.614
  đích chưa có Document vẫn được giữ cùng cờ trạng thái.
- Truy vấn đếm cả bảy bảng và phép nối Version → Event → Document đã chạy trực
  tiếp trên BigQuery và trả dữ liệu thật. Manifest ghi `git_dirty = true` vì
  công cụ chưa được commit khi tạo snapshot; muốn artifact chính thức gắn với
  working tree sạch thì phải phát hành ID mới sau commit, không sửa snapshot
  này.
- Đây là mở rộng phục vụ lưu trữ/chia sẻ và phân tích artifact L0–L3, không
  thay đổi tiêu chí hoàn thành E1–E3 hay tự đóng Phase 3.

### Rebuild sau khi đồng bộ `main` — 23/09/2026

- Thay `data/` bằng bản đã giải nén trong
  `hf-snapshot-incoming-odO6eKml` sau khi kiểm checksum archive thành công.
  `SNAPSHOT.txt` ghi `as_of: 2026-09-12`, 23.139 văn bản và code commit
  `429558de38650a9b895f8c64f784302135d468f0`. Bản `data/` trước khi thay được
  giữ tại `/mnt/c/Users/Admin/OneDrive/Desktop/KLTN/data-before-hf-incoming-20260923`
  để phục hồi thủ công nếu cần.
- Dựng lại đúng thứ tự `build_store.py --with-subtrees` →
  `resolve_expiry_targets.py` → `extract_provision_events.py` →
  `build_versions.py`. Kết quả: 23.139 Document, 1.700.484 Provision;
  55.019 expiry target (8.046/8.518 cặp provision-level resolve được);
  50.623 event; 1.595.391 version; 18.840 event áp được và 31.783 event bị từ
  chối có lý do.
- ID lồng nhau đã theo schema sau merge: `version:<provision-local-id>:<n>` và
  `event:<document-local-id>:<fingerprint>`, không còn
  `version:provision%3A...` hoặc `event:document%3A...`. SHA-256:
  `temporal.sqlite` =
  `6a7bde74dcbf1790cfb0e53c612715f5e9ca6a4be88f5068866041c26c923eed`;
  `expiry_targets.jsonl` =
  `c1fe29122d61ed667d4294f86594926677847beb220d6b607a9da585e6ae3ef6`;
  `provision_events.jsonl` =
  `05643b2c5ecd96cd701f33471e7589d9e522472ce80bb18c4687c918406b7520`;
  `versions.jsonl` =
  `64db0acb219368c44c527443127060b353c724d52a3d32622adad77f187a1832`;
  `event_log.jsonl` =
  `4aaa694a49a5f98a6ae458a7a697277ab94918715467fb21a2a10584c258a6a0`.
- `verify_pipeline.py`: **all checks passed**. Full suite: **331 passed**;
  hai test chuỗi version trên dữ liệu thật từng lỗi do artifact ID cũ đều đã
  pass.
- Neo4j và snapshot Parquet/BigQuery ngày 23/09 ở mục trên vẫn là artifact
  lịch sử theo ID cũ. Phải reload graph và phát hành table snapshot ID mới
  trước khi dùng chúng với artifact vừa dựng; không ghi đè snapshot GCS cũ.
  Việc rebuild này không tự đóng E1–E3 hoặc Phase 3.

### Đồng bộ Neo4j và bảng cloud — 24/09/2026

- Reset riêng volume `graphrag-legal_neo4j_data`; giữ nguyên log/plugin và
  toàn bộ volume Milvus, MinIO, etcd. Tạo lại bốn ID constraint rồi full-load
  artifact mới. Loader tự hậu kiểm trong **937,6s**: 23.139 Document,
  1.700.484 Provision, 1.595.391 ProvisionVersion, 50.623 LegalEvent,
  1.700.484 `CONTAINS`, 1.595.391 `VERSION_OF`, 44.060 cạnh Version → Event và
  50.623 cạnh Event → Document. Không còn Version/Event dùng ID lồng schema cũ.
- Nạp lại 13 loại quan hệ văn bản: **124.934** cạnh graph và **3.614** cạnh
  unresolved. Smoke test Neo4j/Milvus PASS và phép đối chiếu D5 sau reload đạt
  **200/200 snapshot khớp**.
- Export và phát hành snapshot Parquet bất biến mới tại
  `gs://graphrag-legal-thesis/tables/20260924-phase3-v2-c9adff4/`
  (246.747.197 byte cả prefix). Bảy BigQuery external table trong
  `graphrag-509313.legal_graph` đã chuyển sang prefix này; truy vấn trực tiếp
  trả đúng 23.139 Document, 1.700.484 Provision, 1.595.391 Version, 50.623
  Event, 1.700.484 containment edge, 94.683 causal edge và 128.548 reference
  edge.
- Snapshot ngày 23/09 được giữ nguyên như artifact lịch sử; không ghi đè hoặc
  xóa. Việc đồng bộ kho dẫn xuất này không tự đóng E1–E3 hoặc Phase 3.
