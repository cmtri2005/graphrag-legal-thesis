# Chia sẻ snapshot dữ liệu nguồn qua Google Cloud Storage

Bucket `gs://graphrag-legal-thesis` đã được tạo và các thành viên đã được cấp
quyền, nhìn thấy bucket. Script dưới đây chỉ vận chuyển dữ liệu; mỗi người dùng
`gcloud` với tài khoản của mình. Không lưu khóa hoặc credential trong repo.

## Phạm vi snapshot

`scripts/gcs_snapshot.py` đóng gói `data/` thành một `data.tar.gz`, **loại**:

- `data/derived/` — event, version và các artifact pipeline có thể dựng lại;
- `data/temporal.sqlite` — index SQLite dựng lại từ nguồn;
- `data/expiry_targets.jsonl` — kết quả của `resolve_expiry_targets.py`.

Các đầu vào khác như `raw/`, `trees/`, `history/`, `provisions/`, `review/`,
`diagrams/`, `edges.jsonl` và `manifest.sqlite` được giữ. File
`data/SNAPSHOT.txt` nếu có được giữ như dữ liệu lịch sử; **manifest riêng của
GCS** (`manifest.json`) mới là metadata của lần upload này. Snapshot này không
phải bản backup đầy đủ của các artifact đã tính; sau khi pull phải chạy lại
pipeline tương ứng với commit code/dữ liệu trong manifest.

## Push

Chạy từ repository với `gcloud` đã đăng nhập bằng tài khoản có quyền tạo
object trong bucket:

```bash
python scripts/gcs_snapshot.py push
```

Script tự tạo ID dạng `YYYYMMDDTHHMMSSZ-<short-git-commit>` và in đường dẫn
`gs://.../snapshots/<id>`. Có thể đặt ID rõ ràng:

```bash
python scripts/gcs_snapshot.py push --snapshot-id corpus-v2-reviewed
```

Để xem các ID đã upload:

```bash
gcloud storage ls gs://graphrag-legal-thesis/snapshots/
```

Nó tạo archive, SHA-256 và manifest; upload `manifest.json` **cuối cùng** để
đánh dấu snapshot hoàn chỉnh. Mỗi object dùng điều kiện generation `0`, nên
không ghi đè ID đã tồn tại. Nếu một lần upload thất bại giữa chừng, dùng ID
mới sau khi kiểm tra nguyên nhân; prefix cũ không có manifest hoàn chỉnh và
không được pull. Không chạy các bước thay đổi `data/` đồng thời với push.

## Pull

Chỉ pull vào **thư mục cha trống**; archive sẽ tạo thư mục `data/` bên trong:

```bash
python scripts/gcs_snapshot.py pull corpus-v2-reviewed /tmp/corpus-v2-reviewed
```

Script kiểm `manifest.json`, SHA-256, kích thước, nội dung archive và từ chối
đích không trống trước khi giải nén. Nó không tự xóa hoặc ghi đè `data/` đang
dùng trong project. Nếu muốn dùng bản vừa pull, hãy kiểm tra nó trước, rồi
chủ động chuyển sang checkout/thư mục làm việc phù hợp.

Sau khi pull, tối thiểu kiểm nguồn và dựng lại index:

```bash
python scripts/check/verify_pipeline.py --data /tmp/corpus-v2-reviewed/data
python scripts/pipeline/build_store.py --data /tmp/corpus-v2-reviewed/data --with-subtrees
```

Các artifact trong `derived/` cần được tái tạo bằng pipeline tương ứng; không
coi chúng đã có sẵn trong snapshot này. Nếu dùng bucket khác, đặt `--bucket`
**trước** subcommand:

```bash
python scripts/gcs_snapshot.py --bucket gs://another-bucket push
```

## Quyền và chi phí

Việc cấp IAM là thao tác riêng, không được script thay đổi. Thành viên chỉ
pull cần quyền đọc object; người push cần quyền tạo object. Snapshot là bất
biến để tránh ghi đè dữ liệu của nhau. Bucket vẫn phát sinh phí lưu trữ,
request và có thể có phí tải về; theo dõi số snapshot giữ lại và chính sách
soft delete trước khi dọn dẹp. Không dùng `rsync --delete` với nguồn dùng chung.
