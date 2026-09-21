# Execution Plan: Hạ tầng Neo4j + Milvus (P3.1–P3.2)

Date: 2026-09-18

## Status

P3.1–P3.2 hoàn thành ngày 21/09/2026. Giữ file tại `active/` làm runbook và để
bổ sung phép đo Milvus sau khi P5.3 nạp embedding thật.

## Outcome

Neo4j và Milvus chạy được bằng `docker compose`, cả hai healthy, có runbook
bật/tắt và số đo RAM thực tế. Neo4j hiện chứa full corpus D2–D3; phép đo D6
giữ nguyên volume và xác nhận chạy lại loader không tạo trùng.

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
- Loader P3.4 đã hoàn thành ở D2; D6 dùng lại đúng loader đó để đo thời gian
  từng stage và RAM trong lúc MERGE toàn corpus.

## Scope

In scope:

- `docker-compose.yml` cho Neo4j + Milvus standalone, có giới hạn RAM.
- Runbook bật/tắt, kiểm tra healthy, xem log, dọn dẹp.
- Đo RAM stack đã nạp full corpus, RAM đỉnh trong một lượt MERGE và thời gian
  từng stage; lưu report dẫn xuất và số đo bền vững trong plan.

Out of scope:

- Thay đổi logic loader hoặc dữ liệu đã nạp; D6 chỉ thêm instrumentation và
  chạy lại phép MERGE idempotent.
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
5. Ghi số đo RAM full corpus và timing loader vào mục Validation.
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

# Đo steady-state, không sửa graph
python scripts/check/measure_graph_resources.py

# MERGE lại toàn corpus và lấy mẫu trong suốt lượt nạp; không xóa volume
python scripts/check/measure_graph_resources.py --run-loader
```

Hai lệnh đo yêu cầu chạy từ root repository, stack healthy và biến
`NEO4J_PASSWORD` khớp `.env`. JSON report nằm trong `data/derived/` và không
được commit. `docker stats` là nguồn số đo RAM thật cho mục Validation bên dưới.

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

- [x] `docker compose ps` — cả 4 dịch vụ `healthy`.
- [x] `verify_graph_stack.py` — Neo4j và Milvus đều ghi rồi đọc lại đúng dữ
  liệu tạm; cleanup chạy trong `finally`.
- [x] `load_neo4j.py --report ...` — chín số đếm khớp nguồn sau full MERGE.
- [x] `measure_graph_resources.py --run-loader` — 53 mẫu RAM/CPU, report JSON.
- [x] Sau đo: cả 4 container `OOMKilled=false`, `RestartCount=0`, healthy.

Máy đo: Docker Desktop/WSL2, Docker Compose **v5.1.4**, 4 logical CPU; WSL nhìn
thấy **11,68 GiB RAM**.
Corpus Neo4j: 23.139 Document, 1.700.484 Provision, 1.592.178 Version,
50.540 LegalEvent và các cạnh D2–D3. Milvus **chưa có embedding thật**.

| Dịch vụ | Bắt đầu MERGE | Đỉnh trong MERGE | Cuối MERGE | Giới hạn |
|---|---:|---:|---:|---:|
| Neo4j | 1.517,6 MiB | **3.813,4 MiB (93,09%)** | 3.808,3 MiB | 4 GiB |
| Milvus | 102,7 MiB | 103,4 MiB | 103,3 MiB | 4 GiB |
| etcd | 30,0 MiB | 35,3 MiB | 29,4 MiB | 512 MiB |
| MinIO | 90,0 MiB | 91,1 MiB | 91,1 MiB | 1 GiB |
| **Tổng** | **1,70 GiB** | **3,95 GiB** | **3,94 GiB** | — |

Hai mẫu steady hậu kiểm cuối cho tổng khoảng **3,95 GiB**, trong đó Neo4j
3.812,4 MiB. “Tổng đỉnh” là tổng peak riêng từng container; công cụ ghi rõ
peaks có thể không xảy ra đúng cùng một thời điểm.

| Lượt full corpus | Thời gian | Diễn giải |
|---|---:|---|
| D2 lượt 1 | 704,0s | Nạp lần đầu vào graph rỗng |
| D2 lượt 2 | 553,9s | MERGE lại, số đếm không đổi |
| D6 | **573,9s** | MERGE lại có sampling Docker mỗi 10s |

Timing D6: preflight 7,2s; Document 4,3s; Provision 170,3s; LegalEvent 4,9s;
Version 231,4s; `CONTAINS` 152,1s; `CAUSED_BY` 1,3s; hậu kiểm 2,3s.
Version, Provision và `CONTAINS` chiếm gần toàn bộ thời gian.

Với riêng stack đã đo, **không cần tắt `legal-rag-api` chỉ vì tổng RAM của bốn
container** (3,95/11,68 GiB). Tuy nhiên Neo4j đã dùng 93,09% cgroup limit, nên
không chạy API/query nặng song song với full MERGE. Kết luận này phải đo lại
khi `legal-rag-api` chạy workload thật và Milvus đã có embedding ở P5.3.

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
- **Neo4j đã chạm 93,09% giới hạn 4 GiB khi MERGE:** hiện chưa OOM nhưng
  headroom nhỏ. Không chạy full loader song song với workload nặng; trước khi
  query song song hoặc nạp Milvus thật, đo lại và cân nhắc tăng Neo4j limit.

## Progress

- [x] Cài Docker + Compose trên laptop.
- [x] Cấu hình Neo4j local; default dev không dùng khi mở dịch vụ ra mạng.
- [x] `docker compose up -d`, 4 dịch vụ healthy.
- [x] Cài graph dependencies trong `.venv`.
- [x] `python scripts/check/verify_graph_stack.py` → cả hai PASS.
- [x] Ghi số đo full-corpus/peak/timing vào Validation.
- [x] Cập nhật `master-plan.md` P3.1/P3.2 → ✅.

## Decisions

- 2026-09-18: Milvus chạy **standalone đầy đủ qua Docker** (không dùng Milvus
  Lite) — laptop triển khai thật có 16GB RAM, đủ chỗ cho cả hai dịch vụ theo
  đúng phương án gốc ADR-0001. (Milvus Lite từng được cân nhắc khi tưởng nhầm
  máy sandbox 7,8GB là máy triển khai — không còn áp dụng.)
- 2026-09-18: Không thêm Attu/GUI cho Milvus ở bước này — chỉ thêm khi cần
  debug trực quan (YAGNI).

## Result

P3.1–P3.2 và D6 hoàn thành ngày 21/09/2026. Công cụ mới:

- `scripts/check/measure_graph_resources.py`: steady-state hoặc
  `--run-loader`, không xóa volume;
- `load_neo4j.py --report`: timing từng stage và số đếm đã xác minh;
- `graph/resource_metrics.py`: parser byte/percent, Docker stats/inspect và
  tổng hợp start/final/peak có kiểm tra container thiếu;
- `verify_graph_stack.py`: smoke test có hậu điều kiện thật và cleanup kể cả
  khi lỗi.

`python -m pytest -q`: **268 passed**. Dữ liệu Neo4j vẫn được giữ nguyên sau
đo. Các JSON report ở `data/derived/` là output dẫn xuất và không commit.
