# H6: dựng lại một lần sau khi sửa lỗi đồ thị (10/11/2026)

Nháp, chưa qua đối soát độc lập. Authority: `docs/plans/active/master-plan.md` Decisions 2026-11-10
"H5/H6 theo đề xuất"; ADR 0006 mục 7 (sửa và dựng lại một lần). Không tải mạng, không cào lại, không chạm split test.

## Chuỗi lệnh chuẩn (nguồn: `docs/crawling-plan.md` "Running the pipeline", cộng bước L2 mới)

Chạy từ gốc repo, `PYTHONPATH=src`, `.venv/bin/python` (Python 3.12.3). Mỗi bước ghi log ở `runs/rebuild_20261110/logs/<tên>.log`.

`runs/rebuild_20261110/rebuild_graph.sh` (từ `data/raw` đến `versions.jsonl`):

| # | Lệnh | Ghi ra |
|---|---|---|
| 01 | `scripts/pipeline/attach_provision_text.py --force` | `data/provisions/` (L4 `align_by_marker`) |
| 02 | `scripts/pipeline/build_store.py --with-subtrees` | `data/temporal.sqlite` |
| 03 | `scripts/pipeline/resolve_expiry_targets.py` | `data/expiry_targets.jsonl` |
| 04 | `scripts/pipeline/extract_provision_events.py` | `data/derived/provision_events.jsonl` (L1, L2) |
| 05 | `scripts/pipeline/apply_document_scope.py` (mới) | `documents.effective_to` trong sqlite, `data/derived/document_scope_applied.jsonl` |
| 06 | `scripts/pipeline/build_versions.py` | `data/derived/versions.jsonl`, `event_log.jsonl`, `data/review/provision_events.jsonl` |

`runs/rebuild_20261110/rebuild_release.sh` (từ `versions.jsonl` đến release và vector):

| # | Lệnh | Ghi ra |
|---|---|---|
| 07 | `scripts/pipeline/build_corpus.py` | `data/derived/corpus/{asis,versions,documents}.jsonl`, `manifest.json` |
| 08 | `scripts/eval/index_corpus.py` | `data/derived/corpus/index.sqlite` |
| 09 | `scripts/eval/index_corpus.py --lexical` | chỉ mục BM25 trong cùng file |
| 10 | `scripts/pipeline/build_question_pool.py` | `data/derived/vilextime_pool.jsonl` |
| 11 | `scripts/pipeline/build_vilextime.py` | `data/derived/vilextime/T*.jsonl` |
| 12 | `scripts/pipeline/sample_vilextime.py --select` | `data/derived/vilextime/selected.jsonl` |
| 13 | `scripts/pipeline/enrich_vilextime.py` | `data/derived/vilextime/release.jsonl` |
| 14 | `scripts/review/pending_events.py` | `data/review/pending_events.tsv` (giữ phần người đã gõ) |
| 15 | `scripts/check/check_release.py` | không ghi |
| 16 | `scripts/pipeline/export_release.py --final --out data/vilextime_dataset_h6` | release mới, thư mục riêng |
| 17, 18 | `scripts/eval/embed_corpus.py --layer {asis,version} --max-seq-length 256 --model dangvantuan/vietnamese-embedding --rescan` | vector chỉ cho văn bản mới |

Không chạy: `generate_questions.py` (câu hỏi LLM nằm sẵn ở `data/vilextime/questions.jsonl`, không đổi),
`sample_vilextime.py` không `--select` (thứ hạng lineage của bản ghi `sample.jsonl` giữ nguyên),
`build_subtrees.py` (chỉ đọc `data/raw` và `data/trees`, không phụ thuộc L1/L2/L4), mọi bước cào.

## Quyết định thực thi

- Release mới ghi vào `data/vilextime_dataset_h6/`, không ghi đè `data/vilextime_dataset/` (bản v1.0 có sha256 khóa
  trong ADR 0005). Muốn thay bản chính thì copy sau gate.
- `data/vilextime/test2_release*.jsonl` và các phiếu lô 0/1/2 không do chuỗi này sinh ra (nhãn LLM/người). Không sửa;
  diff tính lại đáp án của từng dòng từ `versions.jsonl` mới (`h6_diff.py`).
- Bản cũ để ở `runs/rebuild_20261110/before/` (xem `before.sha256`); phần lớn gitignore.

Kết quả từng bước, sha256 sau và diff: xem phần cuối của file này và `diff.md`.
