# Temporal Legal Foundation Roadmap

> Tài liệu theo dõi các thành phần nền tảng cần xây dựng trước khi triển khai
> hệ thống truy xuất và hỏi đáp hoàn chỉnh. Cập nhật trạng thái bằng checkbox,
> ngày hoàn thành và ghi chú quyết định ngay trong file này.
>
> Cập nhật gần nhất: 12/09/2026.

## 1. Mục tiêu

Xây dựng một lõi nghiệp vụ độc lập với Neo4j, Milvus và mô hình ngôn ngữ, có
khả năng:

- biểu diễn văn bản, đơn vị pháp lý và chuỗi phiên bản;
- chuẩn hóa và áp dụng các sự kiện sửa đổi;
- xác định hiệu lực của từng đơn vị tại một mốc thời gian;
- lan truyền hiệu lực theo cây cấu trúc;
- giữ đầy đủ nguồn gốc và bằng chứng của mọi kết quả;
- cung cấp interface ổn định cho graph storage, retrieval và verifier.

## 2. Nguyên tắc thiết kế

- Khoảng hiệu lực luôn là khoảng nửa mở `[start, end)`.
- Định danh đơn vị pháp lý ổn định, không thay đổi theo phiên bản nội dung.
- Logic nghiệp vụ không phụ thuộc trực tiếp vào Neo4j hoặc Milvus.
- Dữ liệu chưa chắc chắn được giữ lại để review, không tự động suy đoán.
- Sự kiện chưa xác định ngày hoặc node đích không được áp dụng vào version
  chain.
- Mọi phiên bản và sự kiện phải truy ngược được về văn bản nguồn.
- Các thao tác phải idempotent: chạy lại không tạo node, event hoặc version
  trùng lặp.
- Hiệu lực cấp văn bản không được dùng thay cho hiệu lực cấp điều khoản.
- Ưu tiên test logic thời gian bằng in-memory implementation trước khi viết
  database adapter.

## 3. Tổng quan tiến độ

| Mã | Thành phần | Trạng thái | Phụ thuộc |
|---|---|---|---|
| F01 | Domain models | Hoàn thành bước đầu | — |
| F02 | Deterministic identifiers | Hoàn thành bước đầu | F01 |
| F03 | Serialization | Hoàn thành phần lõi | F01, F02 |
| F04 | Version chain | Hoàn thành bước đầu | F01, F02 |
| F05 | Event applier | Hoàn thành phần lõi | F04 |
| F06 | Validity propagation | Hoàn thành phần lõi | F04, F05 |
| F07 | Snapshot service | Hoàn thành phần lõi | F04, F06 |
| F08 | VBPL adapters | Chưa thực hiện | F01, F03 |
| F09 | Amendment extraction models | Hoàn thành phần lõi | F01 |
| F10 | Target resolver | Hoàn thành lõi độc lập dữ liệu | F09; F08 để kiểm chứng dữ liệu thật |
| F11 | Repository ports | Hoàn thành contract và version transition | F01, F07 |
| F12 | In-memory repositories | Hoàn thành phần lõi và application boundary | F11 |
| F13 | Query and evidence models | Hoàn thành contract và serialization | F01, F07 |
| F14 | Storage adapters | Đang thực hiện: Neo4j authoritative adapter | F11, F12 |

## 4. F01 — Domain models

**Trạng thái:** bước đầu hoàn thành ngày 11/09/2026.

**Vị trí:** `src/legal_crawler/temporal/models.py`.

Đã có:

- [x] `LegalDocument`.
- [x] `Provision`.
- [x] `ProvisionVersion`.
- [x] `TemporalInterval`.
- [x] `LegalEvent`.
- [x] `TextUpdate` cho nội dung hợp nhất riêng của từng target.
- [x] `ProvisionInsertion` cho node mới và vị trí chèn trong cây.
- [x] `Provenance`.
- [x] `GraphEdge`.
- [x] Enum cho loại node.
- [x] Enum cho cấp điều khoản.
- [x] Enum cho thao tác pháp lý.
- [x] Enum cho quan hệ graph.
- [x] Enum cho phương pháp trích xuất.
- [x] Enum cho trạng thái kiểm duyệt event.
- [x] Kiểm tra bất biến cơ bản trong `__post_init__`.
- [x] Test ranh giới khoảng hiệu lực nửa mở.
- [x] Test event chưa giải quyết và event đã xác minh.

Cần rà soát khi các module sau được xây dựng:

- [ ] Xác nhận model có đủ dữ liệu cho tạm ngưng rồi khôi phục hiệu lực.
- [x] Biểu diễn node mới cùng vị trí chèn bằng `ProvisionInsertion` và
  `inserted_after_id`.
- [ ] Xác nhận có cần model riêng cho văn bản hợp nhất.
- [ ] Xác nhận có cần phân biệt hiệu lực pháp lý và thời gian ghi nhận dữ liệu.
- [ ] Chốt chính sách bất biến hoặc mutable cho `details` và `properties`.

## 5. F02 — Deterministic identifiers

**Mục tiêu:** mọi entity có ID tất định, tái tạo được và không phụ thuộc ID nội
bộ của database.

**Trạng thái:** bước đầu hoàn thành ngày 11/09/2026.

**Vị trí:** `src/legal_crawler/temporal/ids.py`.

Quy ước dự kiến:

```text
document:{document_id}
provision:{tree_node_uuid}
version:{provision_id}:{ordinal}
event:{source_document_id}:{event_fingerprint}
edge:{source_id}:{relation}:{target_id}:{valid_from}
```

Checklist:

- [x] Hàm tạo ID cho document.
- [x] Hàm tạo ID cho provision.
- [x] Hàm tạo ID cho version.
- [x] Hàm tạo ID/fingerprint cho legal event.
- [x] Hàm tạo ID cho graph edge.
- [x] Canonicalization đầu vào trước khi hash.
- [x] ID không đổi khi thứ tự xử lý thay đổi.
- [x] Cùng dữ liệu nguồn luôn sinh cùng ID.
- [x] Các event khác nhau trong fixture kiểm thử sinh ID khác nhau.
- [x] Test với cả ID số và UUID của `vbpl.vn`.

## 6. F03 — Serialization

**Mục tiêu:** chuyển domain object sang JSON và đọc ngược lại mà không mất kiểu
dữ liệu hoặc provenance.

**Vị trí:** `src/legal_crawler/temporal/serialization.py`.

**Trạng thái:** hoàn thành phần lõi ngày 11/09/2026. Record dùng envelope có
`schema_version`, model type và data; decoder strict để dữ liệu sai hoặc schema
mới không bị đọc theo cách âm thầm làm mất ngữ nghĩa.

Checklist:

- [x] `date` được ghi theo ISO 8601 dạng canonical `YYYY-MM-DD`.
- [x] Enum được ghi bằng value ổn định.
- [x] Tuple và nested model được round-trip chính xác.
- [x] Có `schema_version` ở record đầu ra.
- [x] Giữ nguyên raw status code và dữ liệu mở rộng trong `details`/`properties`.
- [x] Báo lỗi rõ ràng khi gặp schema version không hỗ trợ.
- [x] Test round-trip cho mọi domain model.
- [x] Test Unicode tiếng Việt không bị thay đổi.
- [x] Từ chối field lạ, field bắt buộc bị thiếu và type không đúng.
- [x] Từ chối duplicate JSON key, `NaN`, infinity và metadata không tương thích
  JSON.

## 7. F04 — Version chain

**Mục tiêu:** quản lý các phiên bản liên tiếp của một `Provision` và trả đúng
phiên bản tại thời điểm truy vấn.

**Trạng thái:** bước đầu hoàn thành ngày 11/09/2026.

**Vị trí:** `src/legal_crawler/temporal/version_chain.py`.

API dự kiến:

```python
chain.add(version)
chain.current()
chain.at(query_date)
chain.close_current(effective_on)
chain.assert_consistent()
```

Checklist:

- [x] Sắp xếp version theo thời gian và ordinal.
- [x] Không cho phép hai khoảng hiệu lực chồng nhau.
- [x] Không cho phép hai version cùng ID hoặc ordinal.
- [x] Truy vấn đúng tại `start`.
- [x] Không trả bản cũ tại đúng `end`.
- [x] Hỗ trợ version cuối có `end=None`.
- [x] Trả `None` khi provision chưa tồn tại tại mốc hỏi.
- [x] Trả `None` khi provision đã bị bãi bỏ/đóng hiệu lực.
- [x] Kiểm tra chuỗi A → B → C bằng fixture.
- [x] Test ngày chuyển tiếp giữa hai version.
- [x] Thêm cùng một version chính xác là thao tác idempotent.
- [x] Cho phép khoảng trống giữa các version để không khóa thiết kế tạm ngưng.

## 8. F05 — Event applier

**Mục tiêu:** áp dụng `LegalEvent` hợp lệ lên version chain theo quy tắc tất
định.

**File dự kiến:** `src/legal_crawler/temporal/event_applier.py`.

**Trạng thái:** hoàn thành phần lõi ngày 11/09/2026. Bốn thao tác chính trong
phạm vi đề cương (`AMEND`, `SUPPLEMENT`, `REPEAL`, `REPLACE`) đã có executable
domain logic; `CORRECT` dùng chung quy tắc tạo version mới. Tạm ngưng và khôi
phục được giữ lại trong vocabulary như phần mở rộng nhưng không thuộc tập thao
tác L2 chính thức cần hoàn thành trong đề cương.

Checklist:

- [x] `AMEND`: đóng version cũ và tạo version mới.
- [x] `REPLACE`: thay toàn bộ nội dung node đích.
- [x] `SUPPLEMENT`: bổ sung nội dung hoặc node mới.
- [x] `REPEAL`: đóng hiệu lực mà không tạo text version mới.
- [x] `CORRECT`: tạo phiên bản có provenance từ văn bản đính chính.
- [ ] `SUSPEND`: phần mở rộng, ghi khoảng tạm ngưng.
- [ ] `RESUME`: phần mở rộng, kết thúc khoảng tạm ngưng.
- [x] Từ chối áp dụng event `needs_review` hoặc `rejected`.
- [x] Từ chối event thiếu `effective_on`.
- [x] Từ chối event chưa resolve target.
- [x] Áp dụng cùng event hai lần không tạo version trùng.
- [x] Lưu liên kết hai chiều nghiệp vụ: version mới biết event tạo ra, version
  cũ biết event kết thúc nó.
- [x] Test nhiều event có cùng ngày hiệu lực.
- [x] Chốt quy tắc ban đầu: nhiều event cùng ngày trên các node khác nhau được
  phép; cùng ngày trên một node phải được hợp nhất trước, nếu không sẽ bị từ
  chối để tránh version có độ dài bằng không.
- [x] Áp dụng atomic: nếu một target hoặc insertion sai thì không công bố bất kỳ
  thay đổi nào của event.
- [x] Văn bản nguồn và văn bản đích của event phải tồn tại trong state.

## 9. F06 — Validity propagation

**Mục tiêu:** tính hiệu lực cấp điều khoản dựa trên trạng thái của chính node và
các node tổ tiên.

**File dự kiến:** `src/legal_crawler/temporal/validity.py`.

**Trạng thái:** hoàn thành phần lõi ngày 11/09/2026 cho hiệu lực document,
version, bãi bỏ và lan truyền theo tổ tiên. Trạng thái tạm ngưng sẽ được bổ sung
sau khi F05 có quy tắc `SUSPEND`/`RESUME` chính thức.

API dự kiến:

```python
is_valid(provision_id, at)
invalidity_reason(provision_id, at)
valid_descendants(provision_id, at)
```

Checklist:

- [x] Node chỉ hợp lệ khi document chứa nó hợp lệ.
- [x] Node chỉ hợp lệ khi toàn bộ tổ tiên hợp lệ.
- [x] Bãi bỏ Chương làm vô hiệu toàn bộ cây con.
- [x] Bãi bỏ Điều làm vô hiệu các Khoản và Điểm con.
- [x] Bãi bỏ Khoản không làm Điều cha vô hiệu.
- [ ] Tạm ngưng node cha ảnh hưởng đúng cây con.
- [ ] Phân biệt thêm trạng thái `suspended`; các trạng thái
  `not_yet_effective`, `repealed`, `inactive_gap` và `parent_invalid` đã có.
- [x] Phát hiện cycle trong cấu trúc parent-child.
- [x] Test cây có độ sâu không cố định.
- [x] Test node gốc không có `parent_id`.
- [x] Trả lý do có kiểu rõ ràng, ancestor gây mất hiệu lực và event nguyên nhân.

## 10. F07 — Snapshot service

**Mục tiêu:** cung cấp API point-in-time thống nhất cho các tầng phía sau.

**File dự kiến:** `src/legal_crawler/temporal/snapshot.py`.

**Trạng thái:** hoàn thành phần lõi ngày 11/09/2026. Việc đối chiếu 100 truy vấn
với corpus thật được giữ lại cho giai đoạn dữ liệu sau khi nhóm hoàn tất re-check.

API dự kiến:

```python
snapshot(provision_id, at)
snapshot_document(document_id, at)
valid_provisions(document_id, at)
```

Kết quả snapshot dự kiến chứa:

- provision ổn định;
- version được chọn;
- thời điểm truy vấn;
- trạng thái hợp lệ;
- lý do không hợp lệ nếu có;
- event tạo/kết thúc version;
- provenance và cảnh báo dữ liệu.

Checklist:

- [x] Kết quả snapshot có model riêng.
- [x] Kết quả tất định với cùng input.
- [x] Không trả version/text nếu tổ tiên không hợp lệ.
- [x] Snapshot document giữ đúng thứ tự node, kể cả node được chèn sau một
  sibling xác định.
- [x] Cho phép lọc theo cấp Article/Clause/Point.
- [x] Cảnh báo khi version hợp lệ chưa có provenance.
- [x] Trả event tạo/kết thúc version để phục vụ giải thích và kiểm toán.
- [ ] Test tối thiểu 100 truy vấn đối chiếu thủ công khi có corpus đầy đủ.

## 11. F08 — VBPL adapters

**Mục tiêu:** chuyển dữ liệu crawler thành domain object mà không để chi tiết
định dạng nguồn rò rỉ vào lõi nghiệp vụ.

**Thư mục dự kiến:** `src/legal_crawler/adapters/vbpl/`.

Nguồn ánh xạ:

```text
data/raw/*.json         → LegalDocument
data/trees/*.json       → Provision
data/provisions/*.json  → ProvisionVersion ban đầu
data/history/*.json     → sự kiện hiệu lực sơ bộ
data/edges.jsonl        → GraphEdge
```

Checklist:

- [ ] Adapter document metadata.
- [ ] Adapter cây điều khoản với UUID và `parent_id`.
- [ ] Adapter nội dung provision.
- [ ] Adapter history, chỉ dùng ngày hợp pháp.
- [ ] Adapter reference edge theo bảng mã đã xác minh.
- [ ] Không tự diễn giải numeric suffix chưa rõ nghĩa.
- [ ] Không dùng metadata cấp văn bản để ghi đè hiệu lực cấp điều khoản.
- [ ] Ghi warning hoặc review item cho record thiếu dữ liệu.
- [ ] Fixture từ dữ liệu thật đã ẩn thông tin không cần thiết.
- [ ] Test cho văn bản hiện đại và văn bản cũ.

## 12. F09 — Amendment extraction models

**Mục tiêu:** tạo hợp đồng dữ liệu rõ ràng giữa bước tìm câu sửa đổi, bước
resolve target và bước áp dụng event.

**Vị trí:** `src/legal_crawler/extraction/models.py`.

**Trạng thái:** hoàn thành phần lõi ngày 11/09/2026. Đã có contract tách biệt
mention nguyên văn, reference dạng pháp lý, kết quả resolve và event đủ điều
kiện áp dụng. Parser và target-resolution algorithm không thuộc phạm vi F09.

Model dự kiến:

- `RawAmendmentMention`.
- `TargetReference`.
- `ResolvedTarget`.
- `ExtractionResult`.
- `ExtractionWarning`.
- `SourceSpan`, `ProvisionLocator`, `ProvisionReferencePart`.
- `PhraseReplacement` cho chỉ dẫn tìm/thay chưa được consolidation.

`TargetReference` cần biểu diễn được:

- một Điều/Khoản/Điểm;
- nhiều Điều không liên tiếp;
- cả Chương hoặc cây con;
- vị trí chèn “sau điểm d”;
- thay cụm từ tại nhiều đơn vị;
- tham chiếu “Luật này” hoặc một văn bản được nêu tên.

Checklist:

- [x] Lưu nguyên văn mention nguồn và provenance.
- [x] Lưu span/offset nửa mở `[start, end)` nếu xác định được.
- [x] Phân biệt target document và target provision.
- [x] Cho phép nhiều target không liên tiếp trong một event.
- [x] Biểu diễn exact target, toàn subtree và document scope.
- [x] Tách root bị tác động trực tiếp khỏi tập descendant bị ảnh hưởng của
  subtree để không đóng version con như target trực tiếp.
- [x] Biểu diễn locator ngoài-vào-trong như Điều → Khoản → Điểm.
- [x] Biểu diễn vị trí chèn sau một provision khác.
- [x] Liên kết node bổ sung với parent/anchor đã resolve và kiểm tra payload
  insertion khớp vị trí đó.
- [x] Giữ candidate khi mơ hồ mà không chọn target tạm thời.
- [x] Có confidence riêng cho extraction và resolution.
- [x] Có danh sách warning với code, severity và review context.
- [x] Phrase replacement không được coi là complete resulting text.
- [x] Chỉ materialize thành `LegalEvent` khi ngày, operation, target và payload
  đều đầy đủ, không có error warning.
- [x] Việc chấp nhận event phải truyền `VERIFIED` hoặc `AUTO_ACCEPTED` rõ ràng.
- [x] Test bốn thao tác lõi, multi-target, subtree, insertion anchor và dữ liệu
  mơ hồ.

## 13. F10 — Target resolver

**Mục tiêu:** ánh xạ mô tả pháp lý sang đúng UUID node trong cây của đúng văn
bản.

**File dự kiến:** `src/legal_crawler/extraction/target_resolver.py`.

**Trạng thái:** hoàn thành lõi độc lập dữ liệu ngày 12/09/2026. Resolver làm
việc trên repository port và fixture tổng hợp; việc hiệu chỉnh/đối chiếu với
tiêu đề bất thường trong corpus được giữ lại đến khi dữ liệu hoàn tất re-check.

Checklist:

- [x] Resolve Điều theo document và số điều.
- [x] Resolve Khoản trong đúng Điều.
- [x] Resolve Điểm trong đúng Khoản.
- [x] Resolve nhiều target trong cùng câu và giữ thứ tự reference.
- [x] Resolve toàn bộ cây con khi target là Chương/Mục/Điều.
- [x] Không fuzzy-match hoặc đoán tiêu đề bất thường/không đánh số.
- [ ] Kiểm chứng quy tắc trên tiêu đề bất thường từ corpus thật.
- [x] Không chọn tùy tiện khi có nhiều candidate.
- [x] Trả `needs_review` khi không resolve duy nhất.
- [x] Ghi lại candidate và mã lý do có kiểu cho mọi outcome.
- [x] Resolve insertion parent/sibling và từ chối hai anchor không nhất quán.
- [x] Fixture tổng hợp bao phủ multi-step locator và partial-subtree semantics.
- [ ] Test trực tiếp các mẫu T3 và T6 từ corpus sau re-check.

## 14. F11 — Repository ports

**Mục tiêu:** định nghĩa interface nghiệp vụ trước khi chọn cách lưu trữ.

**Vị trí:** `src/legal_crawler/ports/`.

**Trạng thái:** hoàn thành contract ngày 11/09/2026. Đã định nghĩa boundary cho
repository nghiệp vụ, temporal read, provenance, vector version và transaction;
implementation in-memory thuộc F12.

Interface dự kiến:

- `DocumentRepository`.
- `ProvisionRepository`.
- `VersionRepository`.
- `EventRepository`.
- `TemporalGraphRepository`.
- `SnapshotRepository`.
- `VectorRepository`.

Checklist:

- [x] Dùng `Protocol` nhất quán và hỗ trợ runtime structural check.
- [x] Không import Neo4j/Milvus trong port.
- [x] Có batch API cho corpus lớn.
- [x] Có contract ghi idempotent: `CREATED`, `UNCHANGED`, conflict có exception.
- [x] Có exception hierarchy độc lập backend.
- [x] Có API lấy provenance.
- [x] Có API lọc theo khoảng thời gian hoặc point-in-time.
- [x] Có transaction boundary cho việc áp dụng event atomic.
- [x] Embedding bắt buộc gắn version, provision, document, validity và model.
- [x] `SnapshotService` hiện tại thỏa `SnapshotRepository` protocol.
- [x] Có in-memory implementation và behavioral contract test dùng lại cho
  database adapter.
- [x] Có optimistic closure transition; không cho update version tùy ý.

## 15. F12 — In-memory repositories

**Mục tiêu:** chạy toàn bộ logic versioning và snapshot trong test mà không cần
Docker hoặc dịch vụ bên ngoài.

**Thư mục dự kiến:** `src/legal_crawler/adapters/memory/`.

**Trạng thái:** hoàn thành phần lõi ngày 11/09/2026. Các repository dùng chung
một authoritative store, hỗ trợ rollback tại chỗ và snapshot luôn nhìn thấy
trạng thái đã commit. Vector repository được tách riêng vì embedding là dữ liệu
dẫn xuất.

Checklist:

- [x] Lưu document theo ID và lọc hiệu lực `[start, end)`.
- [x] Lưu provision, kiểm tra parent/anchor và giữ legal document order.
- [x] Lưu version theo provision và thời gian, từ chối overlap/ordinal conflict.
- [x] Lưu event theo source/target/provision và trạng thái đã áp dụng.
- [x] Lưu temporal graph edge và truy vấn theo hướng, relation, thời gian.
- [x] Truy xuất provenance từ version, event, edge và provision.
- [x] Upsert idempotent; ID trùng nhưng nội dung khác phải báo conflict.
- [x] Batch write atomic và transaction rollback toàn authoritative state.
- [x] Snapshot là live read model trên cùng state.
- [x] Vector search tách theo embedding model, lọc thời gian trước khi chấm điểm.
- [x] Contract test tham số hóa để dùng lại cho database adapter sau này.
- [x] Application service dựng target aggregate, chạy domain applier và persist
  delta trong cùng unit-of-work transaction.
- [x] Đóng version theo compare-and-swap, hỗ trợ exact replay và từ chối stale
  hoặc unrelated update.
- [x] Persist provision/version/event/application marker/graph edge nguyên tử.
- [x] Rollback cả event registration và version transition khi lỗi xảy ra muộn.
- [x] Sinh `CONTAINS`, `VERSION_OF`, `CAUSED_BY` và operation edge tất định.

## 16. F13 — Query and evidence models

**Mục tiêu:** tạo hợp đồng dữ liệu cho temporal retrieval và citation verifier.

**Vị trí:** `src/legal_crawler/query/models.py` và
`src/legal_crawler/query/serialization.py`.

**Trạng thái:** hoàn thành contract và versioned serialization ngày 11/09/2026.
Model giữ riêng temporal interpretation, retrieval signals, evidence từ
snapshot, citation claims và verifier outcome. Thuật toán retrieval, verifier
và metric chưa thuộc F13.

Model dự kiến:

```text
TemporalQuery(id, text, at, temporal_resolution)
RetrievedEvidence
RetrievalSignal
Citation
AnswerClaim
VerificationIssue
VerificationResult
AnswerResult
```

Checklist:

- [x] `TemporalQuery` bắt buộc có mốc thời gian hoặc trạng thái unresolved rõ
  ràng; ngày inferred bắt buộc có confidence.
- [x] Evidence gắn trực tiếp với một `SnapshotResult` hợp lệ và version cụ thể.
- [x] Evidence luôn có validity, text và provenance của exact version.
- [x] Lưu riêng lexical, dense, graph và rerank signal để phục vụ ablation.
- [x] Graph-derived evidence bắt buộc có đường đi kết thúc tại provision đích.
- [x] Citation phân biệt document và mọi cấp provision trong domain.
- [x] Claim liên kết citation để đo coverage ở tầng đánh giá.
- [x] Verification result ghi typed issue cho sai văn bản, node, version, level,
  thời gian, provenance và evidence support.
- [x] `AnswerResult` kiểm tra liên kết chéo query–evidence–citation–claim–verifier.
- [x] Không cho trạng thái `ANSWERED` che giấu verifier fail hoặc citation chưa
  được xác minh.
- [x] Model giữ đủ dữ liệu đầu vào để tầng đánh giá tính TVER, VCR và TCS.
- [x] Versioned query envelope độc lập với temporal domain schema.
- [x] Round-trip mọi query artifact và nested snapshot/domain record.
- [x] Decoder từ chối schema/type/field/date/enum/container sai, duplicate JSON
  key, duplicate filter và số không hữu hạn.
- [x] JSON tất định, giữ Unicode và thứ tự evidence/citation/claim/issue.

## 17. F14 — Storage adapters

**Mục tiêu:** lưu domain model vào graph/vector store mà không thay đổi ngữ nghĩa
đã kiểm thử ở lõi.

Chỉ bắt đầu sau khi version chain, validity và snapshot đã ổn định.

**Trạng thái:** đã hoàn thành phần authoritative Neo4j độc lập dữ liệu ngày
12/09/2026 gồm codec, schema, transaction executor, concrete repository và
point-in-time snapshot. Adapter vector vẫn chưa thực hiện; kiểm thử tích hợp
với server thật chờ môi trường Neo4j.

Checklist Neo4j:

- [x] Constraint duy nhất cho deterministic domain ID.
- [x] Index cho document ID, provision ID, loại node và khoảng hiệu lực.
- [x] Constraint ID riêng cho mọi relationship type đã định nghĩa.
- [x] Codec giữ versioned domain payload làm nguồn dữ liệu authoritative.
- [x] Indexed projection không được dùng để tái dựng ngữ nghĩa domain.
- [x] Explicit transaction executor hỗ trợ commit, rollback và chống nested.
- [x] Repository implementation cho document/provision/version/event/graph.
- [x] `CONTAINS`, `VERSION_OF`, `CAUSED_BY` và quan hệ pháp lý.
- [x] Upsert theo deterministic ID.
- [x] Truy vấn snapshot hoặc subgraph tại `t`.
- [x] Không dùng internal Neo4j ID làm domain ID.
- [x] Batch và event application chạy trong một transaction atomic.
- [x] Version closure dùng optimistic comparison và khóa theo provision chain.
- [ ] Chạy integration test với Neo4j server thật.

Checklist vector store:

- [ ] Embedding gắn với `ProvisionVersion`, không chỉ `Provision`.
- [ ] Metadata có `eff_from`, `eff_to`, document và provision ID.
- [ ] Lọc thời gian trước hoặc trong truy xuất.
- [ ] Hỗ trợ dense, lexical/sparse và reranking.
- [ ] Xóa/cập nhật đúng version khi delta crawl thay đổi dữ liệu.
- [ ] Đo recall trước và sau temporal filtering.

## 18. Thứ tự triển khai đề xuất

```text
F01 Domain models
  ↓
F02 Deterministic IDs ──→ F03 Serialization ──→ F08 VBPL adapters
  ↓                                             ↓
F04 Version chain                         F09 Extraction models
  ↓                                             ↓
F05 Event applier ←────────────────────── F10 Target resolver
  ↓
F06 Validity propagation
  ↓
F07 Snapshot service
  ↓
F11 Repository ports
  ↓
F12 In-memory repositories
  ↓
F13 Query/evidence models
  ↓
Repository-backed event application
  ↓
F14 Storage adapters
```

Ưu tiên gần nhất:

1. Implement vector-store adapter theo version và khoảng hiệu lực trong F14.
2. Chuẩn bị fixture adapter F08 nhỏ và đã xác minh khi corpus hoàn tất re-check.
3. Khi có Neo4j server, chạy integration test cho schema và Cypher repository.
4. Khi fixture thật sẵn sàng, implement từng mapper F08 độc lập và fail-loud.

Sau khi corpus hoàn tất re-check: thực hiện F08 để ánh xạ dữ liệu thật, rồi đối
chiếu F10 trên fixture đã xác minh. Không để sự chậm trễ của corpus chặn các hợp
đồng dữ liệu và repository độc lập nguồn ở trên.

F03 và F04–F07 đã có domain logic cùng unit test. Có thể hoàn thành adapter bằng
fixture tổng hợp, nhưng chưa đưa nó vào pipeline chính trước khi kiểm chứng đầu
vào trên fixture từ corpus đã re-check.

## 19. Definition of Done chung

Một thành phần chỉ chuyển sang “Hoàn thành” khi:

- [ ] API và trách nhiệm module được mô tả rõ.
- [ ] Không phụ thuộc ngoài phạm vi cần thiết.
- [ ] Có unit test cho luồng bình thường.
- [ ] Có test cho ranh giới thời gian.
- [ ] Có test cho dữ liệu thiếu hoặc mâu thuẫn.
- [ ] Không bỏ qua lỗi bằng exception handler quá rộng.
- [ ] Không tự động suy đoán dữ liệu pháp lý chưa chắc chắn.
- [ ] Kết quả giữ được provenance.
- [ ] Chạy lại không tạo dữ liệu trùng.
- [ ] Toàn bộ test của repository vẫn pass.
- [ ] Tài liệu tiến độ này được cập nhật.

## 20. Nhật ký tiến độ

| Ngày | Thành phần | Thay đổi | Kiểm chứng | Ghi chú |
|---|---|---|---|---|
| 11/09/2026 | F01 | Tạo domain models và các enum nền tảng | Unit test model; toàn bộ 64 test pass | Cần rà soát thêm khi triển khai versioning |
| 11/09/2026 | F02 | Thêm deterministic ID cho document, provision, version, event và edge | Unit test tính ổn định, canonicalization và input khác nhau | Event/edge dùng SHA-256 rút gọn 24 ký tự |
| 11/09/2026 | F04 | Thêm in-memory `VersionChain` và fixture chuỗi A → B → C | Test lookup, overlap, idempotency và transition boundary; toàn bộ 82 test pass | Cho phép gap giữa version để hỗ trợ tạm ngưng về sau |
| 11/09/2026 | F05 | Thêm `TemporalState`, event applier atomic và payload có cấu trúc cho update/insertion | Test bốn thao tác lõi, multi-target, cùng ngày, rollback và idempotency | Chưa áp dụng `SUSPEND`/`RESUME`; cùng node/cùng ngày phải hợp nhất trước |
| 11/09/2026 | F06 | Thêm validity theo document, local version và toàn bộ chuỗi tổ tiên | Test bãi bỏ Chương/Khoản, cây sâu, gap, cycle và typed reason | Descendant mất hiệu lực gián tiếp, không bị đóng version hàng loạt |
| 11/09/2026 | F07 | Thêm snapshot provision/document, level filter, provenance warning và event audit | 112 test toàn repository pass | Còn đối chiếu 100 truy vấn khi corpus đã re-check |
| 11/09/2026 | F03 | Thêm JSON serialization có schema version cho toàn bộ temporal domain model | 24 test serialization; toàn bộ 136 test pass | Decoder strict; metadata mở rộng chỉ nhận kiểu tương thích JSON |
| 11/09/2026 | F09 | Thêm typed contract từ raw amendment mention đến `LegalEvent` | 31 test extraction model; toàn bộ 167 test pass | Candidate mơ hồ chỉ được giữ để review; chưa implement parser/resolver |
| 11/09/2026 | F11 | Thêm repository protocols, write outcomes, transaction và version-aware vector port | 24 test port contract; toàn bộ 191 test pass | In-memory behavior để F12; vector record là dữ liệu dẫn xuất ngoài authoritative transaction |
| 11/09/2026 | F12 | Thêm authoritative in-memory repositories, unit of work, live snapshot và temporal vector search | Behavioral, rollback, hierarchy, boundary và vector tests; toàn bộ 216 test pass | Contract suite có thể mở rộng bằng cách thêm factory adapter; vector nằm ngoài authoritative transaction |
| 11/09/2026 | F13 | Thêm temporal query, exact-snapshot evidence, citation, claim, verifier, answer contract và versioned serialization | 70 test model/serialization; toàn bộ 286 test pass | Query schema độc lập temporal schema; chưa triển khai retrieval/verifier algorithm hoặc công thức metric |
| 11/09/2026 | F11/F12 | Thêm closure-only version transition và application service persist event delta qua unit of work | Port, behavioral, optimistic closure, rollback và graph tests; toàn bộ 303 test pass | Event edge dùng event ID để nhiều event cùng ngày không xung đột; vector vẫn ở ngoài transaction |
| 12/09/2026 | F10 | Thêm deterministic target resolver trên repository port | Exact/subtree/document/insertion, ambiguity và fail-safe tests; toàn bộ 318 test pass | Fixture tổng hợp; còn kiểm chứng T3/T6 và tiêu đề bất thường trên corpus thật |
| 12/09/2026 | F14 | Thêm Neo4j schema, strict domain codec và transaction executor | Codec, schema, transaction commit/rollback và validation tests; toàn bộ 339 test pass | Chưa có concrete Neo4j repositories hoặc integration test với server |
| 12/09/2026 | F14 | Thêm concrete Neo4j repository, unit of work, temporal snapshot và graph query | Repository behavior, atomic rollback, version closure và application service tests; toàn bộ 349 test pass | Cypher được kiểm tra qua driver giả lập; integration test với server thật còn chờ hạ tầng |

## 21. Quyết định kiến trúc

Ghi các quyết định ảnh hưởng dài hạn tại đây để tránh thay đổi ngầm về sau.

### ADR-001 — Khoảng hiệu lực nửa mở

- **Quyết định:** dùng `[start, end)` cho mọi version và cạnh có hiệu lực.
- **Lý do:** tại đúng ngày chuyển phiên bản chỉ phiên bản mới hợp lệ, tránh hai
  phiên bản cùng đúng.
- **Trạng thái:** chấp nhận.

### ADR-002 — Tách provision identity khỏi provision version

- **Quyết định:** `Provision` giữ định danh ổn định; nội dung thay đổi nằm trong
  `ProvisionVersion`.
- **Lý do:** cùng một Điều/Khoản/Điểm phải truy vấn được xuyên suốt nhiều lần
  sửa đổi.
- **Trạng thái:** chấp nhận.

### ADR-003 — Lõi nghiệp vụ độc lập storage

- **Quyết định:** logic versioning, validity và snapshot không viết trực tiếp
  bằng Cypher hoặc API của vector database.
- **Lý do:** có thể kiểm thử chính xác và thay đổi backend mà không thay đổi
  ngữ nghĩa pháp lý.
- **Trạng thái:** chấp nhận.

### ADR-004 — Event chưa chắc chắn không được áp dụng

- **Quyết định:** event thiếu ngày hoặc target duy nhất được lưu để review nhưng
  không làm thay đổi version chain.
- **Lý do:** lỗi bỏ sót có thể quan sát và sửa; áp dụng nhầm sẽ âm thầm làm sai
  mọi snapshot phía sau.
- **Trạng thái:** chấp nhận.

### ADR-005 — Áp dụng event theo giao dịch atomic

- **Quyết định:** event được áp dụng trên working copy; chỉ thay state chính khi
  toàn bộ target, version và insertion đều hợp lệ.
- **Lý do:** một event nhiều target không được để lại trạng thái cập nhật một
  phần khi target sau bị lỗi.
- **Trạng thái:** chấp nhận.

### ADR-006 — Bãi bỏ node cha không đóng version của toàn bộ cây con

- **Quyết định:** chỉ đóng version của node được nêu trực tiếp trong event; hiệu
  lực của descendant được tính động từ chuỗi tổ tiên.
- **Lý do:** giữ đúng sự khác nhau giữa tác động trực tiếp và mất hiệu lực do
  cấu trúc, đồng thời vẫn truy được nguyên nhân gốc.
- **Trạng thái:** chấp nhận.

### ADR-007 — Event cùng node và cùng ngày phải được hợp nhất trước

- **Quyết định:** từ chối event thứ hai có cùng ngày hiệu lực trên cùng một
  provision; bước extraction/resolution phải tạo ra kết quả hợp nhất cuối ngày.
- **Lý do:** khoảng `[start, end)` không cho phép version có `start == end`, còn
  tự chọn thứ tự event khi thiếu căn cứ sẽ tạo snapshot sai nhưng khó phát hiện.
- **Trạng thái:** chấp nhận.

### ADR-008 — Serialization dùng versioned envelope và strict decoder

- **Quyết định:** mỗi record có `schema_version`, `type`, `data`; decoder từ
  chối field lạ, duplicate key, kiểu sai và schema chưa hỗ trợ.
- **Lý do:** không để thay đổi schema hoặc record hỏng âm thầm làm mất ngày,
  provenance hay ý nghĩa của một event pháp lý.
- **Trạng thái:** chấp nhận.

### ADR-009 — Reference mơ hồ không có tentative final target

- **Quyết định:** resolution chưa được chấp nhận chỉ lưu candidate IDs;
  `target_document_id` và `target_provision_ids` cuối cùng phải để trống.
- **Lý do:** ngăn target có confidence thấp vô tình đi vào event applier như một
  kết luận đã xác minh.
- **Trạng thái:** chấp nhận.

### ADR-010 — Phrase replacement phải được consolidation trước Event Applier

- **Quyết định:** giữ riêng `PhraseReplacement` làm chỉ dẫn nguồn; thao tác sửa
  hoặc thay thế chỉ materialize khi mọi target có `TextUpdate` hoàn chỉnh.
- **Lý do:** Event Applier cần trạng thái nội dung sau tác động, không được nối
  hoặc tìm/thay chuỗi một cách mù quáng.
- **Trạng thái:** chấp nhận.

### ADR-011 — Repository dùng structural Protocol và domain model

- **Quyết định:** service phụ thuộc `Protocol` trả typed domain object, không
  phụ thuộc driver session, internal database ID hoặc query language.
- **Lý do:** memory, graph và vector adapter có thể thay thế mà không định nghĩa
  lại temporal semantics.
- **Trạng thái:** chấp nhận.

### ADR-012 — Event transaction chỉ bao phủ authoritative temporal state

- **Quyết định:** document, provision, version, event và graph thay đổi trong
  cùng `TemporalUnitOfWork`; vector embedding là dữ liệu dẫn xuất và không nằm
  trong distributed transaction này.
- **Lý do:** không giả định khả năng transaction nguyên tử xuyên Neo4j và vector
  store. Embedding có thể rebuild từ version đã commit bằng deterministic ID.
- **Trạng thái:** chấp nhận.

### ADR-013 — Retrieval evidence phải xuất phát từ exact valid snapshot

- **Quyết định:** `RetrievedEvidence` chứa `SnapshotResult` hợp lệ thay vì nhận
  riêng các ID và text có thể không đồng bộ.
- **Lý do:** ngăn retrieval ghép nhầm text, provision, version hoặc mốc thời
  gian; đồng thời giữ provenance và invalidity propagation từ F07.
- **Trạng thái:** chấp nhận.

### ADR-014 — Query artifact và temporal domain dùng schema version độc lập

- **Quyết định:** query record có `QUERY_SCHEMA_VERSION`; provision, version,
  event và provenance lồng bên trong vẫn giữ temporal envelope riêng.
- **Lý do:** hai nhóm model có vòng đời khác nhau; migration query không được
  âm thầm thay đổi ngữ nghĩa dữ liệu pháp lý đã lưu.
- **Trạng thái:** chấp nhận.

### ADR-015 — Version đã persist chỉ được chuyển từ open sang closed

- **Quyết định:** repository không có generic update. `replace_closed` dùng
  expected open version và closed form cùng ID; exact replay là idempotent,
  stale value hoặc thay đổi text/provenance bị từ chối.
- **Lý do:** áp dụng sửa đổi cần đóng version hiện hành nhưng không được mở cửa
  cho việc ghi đè lịch sử pháp lý ngoài transaction.
- **Trạng thái:** chấp nhận.

### ADR-016 — Event application persist validated delta trong một transaction

- **Quyết định:** application service dựng aggregate của văn bản đích, dùng
  `EventApplier` tính next state rồi persist provision, version closure/version
  mới, event marker và graph edge trong cùng unit of work.
- **Lý do:** giữ domain semantics độc lập storage và ngăn trạng thái cập nhật
  một phần nếu lỗi xảy ra sau khi version cũ đã đóng.
- **Trạng thái:** chấp nhận.

### ADR-017 — Target resolver chỉ chấp nhận một structural match duy nhất

- **Quyết định:** chuẩn hóa marker Điều/Khoản/Điểm nhưng không fuzzy-match tiêu
  đề. Chỉ trả `RESOLVED` khi toàn bộ locator và quan hệ tổ tiên cho đúng một
  provision hoặc một cấu hình insertion anchor.
- **Lý do:** chọn nhầm UUID tạo event hợp lệ về hình thức nhưng làm sai toàn bộ
  version chain; trường hợp mơ hồ phải giữ candidate và đi qua review.
- **Trạng thái:** chấp nhận.

### ADR-018 — Neo4j lưu authoritative versioned payload

- **Quyết định:** mỗi node/cạnh giữ JSON domain đã version hóa làm payload nguồn;
  các property như `document_id`, `provision_id`, `eff_from`, `eff_to` chỉ là
  projection phục vụ index và truy vấn.
- **Lý do:** tránh việc schema Neo4j vô tình định nghĩa lại temporal semantics;
  decoder luôn kiểm tra ID, kind, endpoint và relation với payload gốc.
- **Trạng thái:** chấp nhận.
