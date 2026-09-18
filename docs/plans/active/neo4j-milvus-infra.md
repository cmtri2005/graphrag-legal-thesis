# Execution Plan: Hạ tầng Neo4j + Milvus (P3.1–P3.2)

Date: 2026-09-18

## Status

Active. Chưa bắt đầu — file này là bản kế hoạch để CMT triển khai.

## Outcome

Neo4j và Milvus chạy được bằng `docker compose`, cả hai healthy, có runbook
bật/tắt và số đo RAM thực tế — làm nền cho P3.4 (loader), P3.5 (nạp cạnh) và
P3.6 (chuyển resolver sang Neo4j). Không nạp dữ liệu thật ở đây; đó là P3.4.

## Context

- Quyết định stack: [ADR 0001](../../decisions/0001-neo4j-milvus-la-kho-dan-xuat.md)
  — Neo4j lưu đồ thị, Milvus lưu embedding, cả hai là kho dẫn xuất từ `data/`.
- Máy triển khai thật: laptop 16GB RAM (không phải máy sandbox lúc lập kế
  hoạch, máy đó chỉ có ~7,8GB và đang chạy container của các project khác —
  số đo RAM ở máy đó không áp dụng được).
- `docker-compose.yml` (repo root) đã viết sẵn: Neo4j 5.24.2-community +
  Milvus standalone 2.4.15 (etcd + MinIO + milvus).
- `scripts/check/verify_graph_stack.py`: smoke test đọc/ghi cả hai dịch vụ,
  không đụng `data/`.
- Loader thật (P3.4) sẽ tái dùng `src/legal_crawler/ingest.py` (đã có
  `build_document` v.v. cho SQLite) — viết plan riêng khi tới lượt, không nằm
  trong phạm vi file này.

## Scope

In scope:

- `docker-compose.yml` cho Neo4j + Milvus standalone, có giới hạn RAM.
- Runbook bật/tắt, kiểm tra healthy, xem log, dọn dẹp.
- Đo RAM baseline (stack rỗng) và ước tính RAM khi nạp full corpus dựa trên
  quy mô dữ liệu đã biết (1,15 triệu node có text, 1,27 triệu node cấu trúc).

Out of scope:

- Loader `data/` → Neo4j (P3.4) — việc riêng, viết plan khi bắt đầu.
- Tạo embedding và nạp Milvus thật (P3.5, P5.3) — cần model đã chốt (P5.1).
- Bất kỳ thay đổi nào lên `data/` hoặc script pipeline hiện có.

## Approach

1. Cài đặt Docker Desktop / Docker Engine + Compose v2 trên laptop (xem
   Prerequisites bên dưới).
2. `cp .env.example .env`, đặt mật khẩu Neo4j thật (không dùng
   `changeme123` ngoài môi trường dev cá nhân).
3. `docker compose up -d`, đợi cả 4 container `healthy`
   (`docker compose ps`).
4. `pip install -e ".[graph]"` rồi chạy `verify_graph_stack.py` — xác nhận
   đọc/ghi được cả hai chiều trước khi build loader thật.
5. Ghi số đo RAM baseline vào mục Validation.
6. Không tắt container qua đêm nếu định tiếp tục P3.4 hôm sau — Neo4j
   Community khởi động lại vẫn giữ dữ liệu nhờ volume, nhưng khởi động lại
   tốn vài chục giây mỗi lần.

## Runbook

### Prerequisites

- Docker Engine ≥ 24 và Docker Compose v2 (`docker compose version`).
- ≥ 8GB RAM rảnh cho riêng stack này (Neo4j 4GB + Milvus 4GB + etcd/MinIO
  1.5GB theo giới hạn đặt trong compose file) — trên laptop 16GB, để lại
  ~6-7GB cho OS, IDE, trình duyệt.
- Cổng rảnh: `7474`, `7687` (Neo4j), `19530`, `9091` (Milvus), `9001`
  (MinIO console, tuỳ chọn).
- File `.env` (copy từ `.env.example`) với `NEO4J_PASSWORD` thật.

### Start

```bash
docker compose up -d
docker compose ps          # đợi tới khi cả 4 dịch vụ "healthy"
```

Neo4j Browser: `http://localhost:7474` (đăng nhập `neo4j` / mật khẩu trong
`.env`). Bolt driver: `bolt://localhost:7687`. Milvus gRPC:
`localhost:19530`.

### Readiness

- Neo4j: `docker compose ps neo4j` → `healthy`, hoặc
  `curl -sf http://localhost:7474` trả về HTML.
- Milvus: `curl -sf http://localhost:9091/healthz` → `OK`.
- Xác nhận đọc/ghi thật: `python scripts/check/verify_graph_stack.py` → cả
  hai `[PASS]`.

### Deterministic State

Stack khởi động rỗng (volume mới) → chạy `verify_graph_stack.py` (tự dọn
node/collection nó tạo ra) để có trạng thái sạch mà không đụng dữ liệu thật.
Muốn reset hoàn toàn: `docker compose down -v` (xoá cả volume — mất toàn bộ
dữ liệu đã nạp, chỉ dùng khi cố ý làm lại từ đầu).

### Interface

- Neo4j Browser (`:7474`) để chạy Cypher tay khi kiểm tra dữ liệu.
- `cypher-shell` trong container:
  `docker compose exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD"`.
- Milvus: qua `pymilvus.MilvusClient` (xem `verify_graph_stack.py` làm mẫu),
  hoặc Attu (GUI, chưa thêm vào compose — thêm sau nếu cần).

### Runtime Evidence

```bash
docker compose logs -f neo4j      # log Neo4j
docker compose logs -f milvus     # log Milvus
docker stats legal-kg-neo4j legal-kg-milvus legal-kg-etcd legal-kg-minio
```

`docker stats` là nguồn số đo RAM thật cho mục Validation bên dưới.

### Ownership And Cleanup

Toàn bộ container tên `legal-kg-*`, chỉ ảnh hưởng project này (không đụng
container của project khác trên cùng máy nếu triển khai trên máy dùng
chung). Dừng:

```bash
docker compose stop        # dừng, giữ dữ liệu trong volume
docker compose down        # dừng + xoá container, giữ volume
docker compose down -v     # dừng + xoá container + xoá volume (mất dữ liệu)
```

### Validation

- [ ] `docker compose ps` — cả 4 dịch vụ `healthy`.
- [ ] `verify_graph_stack.py` — cả hai `[PASS]`.
- [ ] Số đo RAM baseline (stack rỗng, ghi lại từ `docker stats`):

  | Dịch vụ | RAM baseline | Giới hạn đặt |
  |---|---:|---:|
  | Neo4j | _điền sau khi chạy_ | 4g |
  | Milvus | _điền sau khi chạy_ | 4g |
  | etcd | _điền sau khi chạy_ | 512m |
  | MinIO | _điền sau khi chạy_ | 1g |

- [ ] Ước tính RAM khi nạp full corpus: Neo4j page cache cỡ ~2GB đủ giữ phần
  lớn 1,27 triệu node cấu trúc trong RAM (mỗi node quan hệ nhỏ, page cache
  scale theo kích thước file dữ liệu trên đĩa chứ không phải số node trực
  tiếp) — **số thật chỉ có sau khi P3.4 nạp xong**, ghi lại ở plan của P3.4.

### Unknowns

- RAM Milvus cần khi nạp thật ~1,15 triệu vector (kích thước embedding chưa
  chốt — phụ thuộc P5.1 chọn model). Không đoán trước; đo sau khi P5.1+P5.3
  chạy thử trên tập nhỏ.
- Có cần Attu (Milvus GUI) hay không — thêm vào compose khi thực sự cần debug
  trực quan, không thêm trước (YAGNI).

## Risks And Recovery

- **Xung đột cổng** với dịch vụ khác trên máy (7474/7687/19530 đã bị chiếm):
  đổi mapping cổng bên trái dấu `:` trong `docker-compose.yml`, không đổi
  cổng bên trong container.
- **Volume hỏng do tắt đột ngột**: Neo4j/Milvus đều ghi WAL, khởi động lại
  container thường tự phục hồi; nếu Neo4j không lên được, xem
  `docker compose logs neo4j` tìm dòng lỗi cụ thể trước khi xoá volume.
- **Hết RAM thật trên laptop** (ví dụ chạy thêm IDE nặng + trình duyệt nhiều
  tab): hạ `mem_limit`/heap trong compose file, hoặc dừng Milvus khi chỉ cần
  làm việc với đồ thị (`docker compose stop milvus etcd minio`).

## Progress

- [ ] Cài Docker + Compose trên laptop, xác nhận `docker compose version`.
- [ ] `cp .env.example .env`, đặt mật khẩu thật.
- [ ] `docker compose up -d`, đợi 4 dịch vụ healthy.
- [ ] `pip install -e ".[graph]"`.
- [ ] `python scripts/check/verify_graph_stack.py` → cả hai PASS.
- [ ] Ghi số đo RAM baseline vào Validation.
- [ ] Cập nhật `master-plan.md` P3.1/P3.2 → ✅.

## Decisions

- 2026-09-18: Milvus chạy **standalone đầy đủ qua Docker** (không dùng Milvus
  Lite) — laptop triển khai thật có 16GB RAM, đủ chỗ cho cả hai dịch vụ theo
  đúng phương án gốc ADR-0001. (Milvus Lite từng được cân nhắc khi tưởng nhầm
  máy sandbox 7,8GB là máy triển khai — không còn áp dụng.)
- 2026-09-18: Không thêm Attu/GUI cho Milvus ở bước này — chỉ thêm khi cần
  debug trực quan (YAGNI).

## Result

_Điền sau khi chạy `docker compose up -d` thật và đo được RAM._
