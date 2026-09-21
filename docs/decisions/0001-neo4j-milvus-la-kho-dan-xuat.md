# 0001 Neo4j và Milvus là kho dẫn xuất từ `data/`

Date: 2026-09-14

## Status

Accepted

## Context

Commit `5b8ee70` (13/09/2026) đã xóa adapter Neo4j/vector và thay bằng một index
SQLite (`src/legal_crawler/index.py`). Nhóm cần một stack cố định cho đồ thị tri
thức (L0–L3), truy xuất có ràng buộc thời gian (L4), baseline B2–B7 và phần
trình diễn bằng chứng trước hội đồng.

Ràng buộc đã biết:

- Milvus lọc được theo trường số nhưng không biết cây cha–con. Nếu chỉ lọc trong
  Milvus theo khoảng hiệu lực của văn bản, hệ thống chỉ đạt mức baseline B7.
- Máy phát triển hiện có 4 CPU, 7 GB RAM (WSL) và đã chạy container `legal-rag-api`.
- Corpus crawl lúc 12/09/2026 không tái tạo được, vì vbpl.vn thay đổi liên tục.

## Decision

1. **Neo4j** lưu đồ thị: Document, Provision, ProvisionVersion, LegalEvent, cạnh
   cấu trúc và cạnh quan hệ có kiểu. **Milvus** lưu embedding của từng
   `ProvisionVersion`.
2. `data/` vẫn là nguồn sự thật duy nhất. Neo4j và Milvus là **kho dẫn xuất**:
   xóa đi thì dựng lại được từ `data/` cộng các event đã duyệt.
3. Lọc hiệu lực theo cách **A (tính trước khoảng hiệu lực thực)**. Offline, mỗi
   phiên bản nhận khoảng hiệu lực đã giao với khoảng hiệu lực của mọi tổ tiên
   (công thức (3)); kết quả được ghi vào Milvus. Online, Milvus lọc theo khoảng
   đó, sau đó Neo4j xác nhận lại top-k bằng logic trong `temporal/validity.py`.
4. Chạy bằng **Docker trên máy phát triển**, có giới hạn RAM cho từng dịch vụ.
5. Nạp và tạo embedding cho **toàn bộ 22.550 văn bản**.

## Alternatives Considered

1. Chỉ dùng SQLite (index hiện tại). Đủ nhanh cho các truy vấn L3 đã đo
   (`data/representation_benchmark.json`), nhưng nhóm chọn Neo4j/Milvus cho phần
   trình diễn đồ thị và truy xuất vector.
2. Neo4j là nguồn sự thật (ADR-018 cũ). Bị loại vì phải backup dump riêng và tái
   lập khó hơn.
3. Lọc thô trong Milvus rồi lọc tinh trong Neo4j (cách B). Bị loại vì có thể
   thiếu ứng viên.
4. Neo4j trả tập 𝒰ₜ trước rồi Milvus tìm trong tập đó (cách C). Bị loại vì 𝒰ₜ có
   hàng trăm nghìn id.

## Consequences

Positive:

- Có đồ thị để trình diễn và truy vấn Cypher; có vector search có lọc theo trường.
- Mọi kết quả vẫn tái lập được từ snapshot `data/` trên Hugging Face.

Tradeoffs:

- Event L2 đã duyệt phải được lưu thành file trong `data/` (ví dụ `data/events/`),
  vì Neo4j có thể bị dựng lại bất cứ lúc nào.
- Khi một event làm đổi cây hoặc chuỗi phiên bản, phải tính lại khoảng hiệu lực
  thực và cập nhật các vector liên quan.
- RAM 7 GB có thể không đủ để chạy Neo4j và Milvus standalone cùng lúc với
  corpus đầy đủ. Cần đo thực tế.
- Tạo embedding khoảng 1,14 triệu nút có text trên CPU có thể mất nhiều ngày.
- `index.py`, `ingest.py`, `build_store.py` chỉ là cầu nối tạm. Chúng bị thay
  khi loader Neo4j chạy được; `target_resolver` phải đổi nguồn đọc.

## Amendments

- **2026-09-20.** Quyết định 3 (cách A) đã cài đặt: `scripts/pipeline/build_versions.py`
  ghi `effective_from`/`effective_to` cho từng phiên bản vào
  `data/derived/versions.jsonl`, khớp `ValidityService` 1.005/1.005 cặp kiểm tra.
- **2026-09-20.** Mục Consequences viết `index.py`, `ingest.py`, `build_store.py`
  "bị thay khi loader Neo4j chạy được". Nhóm hoãn việc này: SQLite ở lại làm index
  dựng offline (pipeline L2/L3 chạy trong vài phút, không cần Docker), Neo4j chỉ
  phục vụ truy vấn và trình diễn. Migrate sau, không phải trước M2. Quyết định
  vẫn giữ nguyên, chỉ lùi thời điểm.

## Follow-Up

- Master plan: `docs/plans/active/master-plan.md`, các việc P3.1–P3.6, P3.9,
  P3.16, P5.2–P5.3.
- Kiểm chứng trước khi dựa vào: analyzer BM25 của Milvus với tiếng Việt, và các
  loại index mà Milvus Lite hỗ trợ.
