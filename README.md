# Temporal-Aware KG-RAG cho pháp luật Việt Nam

Khóa luận xây dựng đồ thị tri thức pháp luật có phiên bản theo thời gian từ vbpl.vn.
Hệ trả lời câu hỏi tại một mốc ngày và đánh giá bằng ViLexTime.
Trạng thái: [xem master plan](docs/plans/active/master-plan.md).

## Nguồn sự thật

Khi hai nơi mâu thuẫn, nơi đứng trên đúng.

| Thứ tự | Câu hỏi | Đọc ở đâu |
|---|---|---|
| 1 | Đã cam kết gì | `docs/DeCuongKLTN_23521635_23521643_UIT.docx` (không bao giờ sửa, xóa) |
| 2 | Quy tắc phân tích, cấu hình đã khóa | `docs/decisions/0005-ke-hoach-phan-tich.md` và các ADR khác |
| 3 | Thế nào là một câu hỏi đúng | `docs/vilextime-dinh-nghia.md`, `docs/vilextime-annotation.md` (4.0) |
| 4 | Đang làm gì, tiếp theo là gì | `docs/plans/active/master-plan.md` |
| 5 | Một con số đến từ đâu | `runs/README.md` trỏ tới file điểm trong `runs/` |
| 6 | Bộ dữ liệu là gì | `data/vilextime_dataset/manifest.json`, `docs/vilextime-datasheet.md` |
| 7 | Hệ làm gì thật | `src/vilexgraph/framework/`, `tests/` |

Số test 2: chỉ lấy Accuracy từ `runs/E3_test2/rescore/`.
Lần chấm đầu đã sai vì thiếu đáp án ngắn.

Tài liệu cũ được ADR hoặc comment code nhắc tới (`MASTER_RESEARCH_GUIDE.md`, các plan cũ, `DATASET_GAP`, `JUDGE_DATASET`…) đã xóa khỏi cây; đọc ở commit `51f36c7`.

## Cây thư mục

| Mục | Dùng để làm gì |
|---|---|
| `src/` | Cào văn bản, dựng đồ thị thời gian và hệ hỏi đáp |
| `scripts/` | Đường ống dữ liệu, rà soát, chấm điểm và dựng paper |
| `tests/` | Kiểm tra hành vi của code |
| `prompts/` | Lời dặn được lưu trong repo |
| `notebooks/` | Notebook Colab và hướng dẫn nhập kết quả |
| `data/` | Dữ liệu gốc, dẫn xuất, bản phát hành và nhãn |
| `runs/` | Dự đoán, bản ghi chạy và điểm; xem [sổ chạy](runs/README.md) |
| `docs/plans/active/master-plan.md` | Kế hoạch hiện hành |
| `docs/plans/completed/` | Hồ sơ việc đã đóng |
| `docs/decisions/` | Các quyết định đã chấp nhận |
| `docs/thesis/` | Bản nháp khóa luận |
| `docs/paper/` | Paper được dựng từ template |
| `docs/reports/` | Báo cáo còn được trích dẫn |
| `related_paper/` | Bài liên quan và ghi chú đọc |
| `references.bib` | Thư mục tài liệu trích dẫn |
| `AGENTS.md`, `CLAUDE.md` | Hướng dẫn làm việc cho agent |

## Bản đồ dữ liệu

| Nhóm | Nơi lưu | Khả năng dựng lại |
|---|---|---|
| Dữ liệu gốc | `data/raw/`, `data/trees/`, `data/history/`, `data/diagrams/`, `data/seeds.json`, `data/reverse_seeds.json`, `data/manifest.sqlite` | Mất bản cào phải tải lại; mất manifest mất lịch sử delta |
| Dẫn xuất | `data/edges.jsonl`, `data/provisions/`, `data/temporal.sqlite`, `data/derived/` | Dựng lại từ dữ liệu gốc; không xóa dữ liệu tốn công tạo |
| Bản phát hành | `data/vilextime_dataset/`, `data/vilextime/questions.jsonl`, `data/vilextime/test2_release_v2.jsonl` | Câu hỏi không tự dựng lại; manifest khóa bản phát hành |
| Nhãn | `data/review/`, `data/excluded_ids.txt`, `data/reference_type_map.json`, `data/eff_status_map.json`, `data/field_filter_map.json` | Quyết định người và bảng mã đã kiểm; giữ nguyên |

Chi tiết tệp, lệnh dựng dữ liệu đầy đủ và lưu ý vận hành: [docs/crawling-plan.md](docs/crawling-plan.md).

## Lệnh thường dùng

Chạy từ gốc repo với môi trường `.venv` đã cài.
Các lệnh sau chỉ kiểm tra, chấm dự đoán có sẵn và dựng tài liệu.

```bash
HF_HUB_OFFLINE=1 .venv/bin/python -m pytest -q
HF_HUB_OFFLINE=1 .venv/bin/python scripts/eval/score_vilextime.py runs/B2_dev/dev/b1.jsonl --split dev --release data/vilextime_dataset/vilextime.jsonl
.venv/bin/python scripts/paper/paper_build.py
.venv/bin/python scripts/paper/paper_check.py
```
