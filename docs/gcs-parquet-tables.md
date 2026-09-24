# Bảng Parquet trên GCS và BigQuery

Luồng này tạo một biểu diễn phân tích **dẫn xuất** từ corpus và artifact L0–L3.
Nó không thay thế snapshot nguồn/full trong `gs://graphrag-legal-thesis/snapshots/`.

```text
data/temporal.sqlite + data/derived/*.jsonl + data/edges.jsonl
                              │
                              ▼
                 7 bảng Parquet có version
                              │
                              ▼
     gs://graphrag-legal-thesis/tables/<snapshot-id>/
                              │
                              ▼
                  BigQuery external tables
```

## Bảy bảng

| Bảng | Nội dung |
|---|---|
| `documents` | Metadata văn bản pháp luật |
| `provisions` | Chương/Mục/Điều/Khoản/Điểm và quan hệ cha qua `parent_id` |
| `provision_versions` | Text, thứ tự version và khoảng hiệu lực |
| `legal_events` | Event đã gom theo ID, trạng thái audit và kết quả áp dụng |
| `containment_edges` | `Document/Provision -[:CONTAINS]-> Provision` |
| `causal_edges` | Version → Event (`created`/`ended`) và Event → Document (`actor`) |
| `document_reference_edges` | 13 loại liên kết văn bản; giữ cả đích chưa resolve |

Các danh sách/cấu trúc lồng nhau cần giữ nguyên bằng chứng được ghi dưới dạng
JSON string để schema Parquet và BigQuery ổn định. Ngày được ghi bằng kiểu
Parquet `date32`, sang BigQuery là `DATE`.

## Cài dependency

```bash
pip install -e ".[tables]"
```

## Export local

Chọn một ID bất biến; không dùng lại ID đã xuất hoặc upload:

```bash
TABLE_SNAPSHOT=20260923-phase3-v2

python scripts/pipeline/export_parquet_tables.py \
  --data data \
  --output "/tmp/$TABLE_SNAPSHOT" \
  --snapshot-id "$TABLE_SNAPSHOT"
```

Thư mục đích phải chưa tồn tại. Export ghi theo batch, chia mỗi bảng thành các
file `part-*.parquet`, rồi tạo:

- `manifest.json`: schema, row count, Git commit, hash input và metadata file;
- `checksums.sha256`: checksum tất cả file Parquet.

Nếu export lỗi, thư mục staging được xóa và đích hoàn chỉnh không xuất hiện.

## Upload và tạo BigQuery external tables

```bash
python scripts/gcs_tables.py "/tmp/$TABLE_SNAPSHOT" \
  --bucket gs://graphrag-legal-thesis \
  --project-id graphrag-509313 \
  --dataset legal_graph \
  --location us-east1 \
  --create-bigquery
```

Uploader đọc lại toàn bộ checksum, số dòng và schema trước khi upload. Object
không được ghi đè (`generation-match=0`); `manifest.json` được upload cuối cùng
làm completion marker. Script cũng tải lên file
`create_external_tables.sql` có URI cụ thể của snapshot.

Với `--create-bigquery`, script tạo dataset nếu chưa tồn tại rồi tạo/cập nhật
bảy external table. Dữ liệu vẫn nằm trong GCS; BigQuery chỉ giữ định nghĩa
bảng. Bỏ cờ này nếu chỉ muốn upload Parquet.

## Truy vấn thử

```sql
SELECT level, COUNT(*) AS provisions
FROM `graphrag-509313.legal_graph.provisions`
GROUP BY level
ORDER BY provisions DESC;
```

```sql
SELECT
  v.provision_id,
  COUNT(*) AS version_count
FROM `graphrag-509313.legal_graph.provision_versions` AS v
GROUP BY v.provision_id
HAVING version_count >= 2
ORDER BY version_count DESC;
```

## Snapshot đã triển khai ngày 23/09/2026

Đã export, kiểm tra checksum/schema/số dòng, upload và tạo external table cho
snapshot sau:

- GCS: `gs://graphrag-legal-thesis/tables/20260923-phase3-v2-d7ada236/`;
- BigQuery: `graphrag-509313.legal_graph` tại `us-east1`;
- 25 file Parquet, tổng cộng 246.460.861 byte (xấp xỉ 235 MiB).

| Bảng | Số dòng đã đối chiếu |
|---|---:|
| `documents` | 23.139 |
| `provisions` | 1.700.484 |
| `provision_versions` | 1.592.178 |
| `legal_events` | 50.540 |
| `containment_edges` | 1.700.484 |
| `causal_edges` | 88.180 |
| `document_reference_edges` | 128.548 |

Trong 128.548 cạnh dẫn chiếu nguồn, 124.934 cạnh có đủ hai Document để nạp
Neo4j và 3.614 cạnh thiếu Document đích vẫn được giữ trong bảng với
`target_resolved = false`, thay vì bị loại khỏi dữ liệu phân tích. Truy vấn
đếm trực tiếp trên cả bảy external table trả đúng các số ở trên. Truy vấn nối
`provision_versions` → `causal_edges` → `legal_events` → `causal_edges`
(`role = 'actor'`) → `documents` cũng trả về các chuỗi nhân quả thật.

Manifest ghi commit nguồn
`d7ada236bd1264136445781741311ec2533153dc` và `git_dirty = true`, vì công cụ
export chưa được commit tại thời điểm phát hành snapshot. Hash từng input và
từng file Parquet vẫn cho phép kiểm tra chính xác artifact này. Nếu cần một
artifact gắn với trạng thái Git sạch để trích dẫn chính thức, hãy commit thay
đổi rồi phát hành bằng một `snapshot-id` mới; không ghi đè snapshot hiện tại.

## Cập nhật snapshot

Mỗi lần dữ liệu thay đổi, tạo `snapshot-id` mới và prefix GCS mới. Không sửa
Parquet của snapshot cũ. Nếu chạy `--create-bigquery`, bảy external table trong
dataset `legal_graph` sẽ được chuyển sang snapshot mới bằng `CREATE OR REPLACE`;
snapshot cũ vẫn còn trên GCS để truy nguyên hoặc rollback định nghĩa bảng.

## Snapshot active sau khi đồng bộ main — 24/09/2026

- GCS: `gs://graphrag-legal-thesis/tables/20260924-phase3-v2-c9adff4/`;
- BigQuery: `graphrag-509313.legal_graph` tại `us-east1`;
- tổng kích thước prefix: 246.747.197 byte;
- BigQuery external tables hiện trỏ tới snapshot này.

| Bảng | Số dòng đã truy vấn lại |
|---|---:|
| `documents` | 23.139 |
| `provisions` | 1.700.484 |
| `provision_versions` | 1.595.391 |
| `legal_events` | 50.623 |
| `containment_edges` | 1.700.484 |
| `causal_edges` | 94.683 |
| `document_reference_edges` | 128.548 |

Snapshot `20260923-phase3-v2-d7ada236` ở mục trên là artifact lịch sử theo
schema ID trước khi đồng bộ `main`; nó vẫn được giữ nguyên để truy nguyên.
