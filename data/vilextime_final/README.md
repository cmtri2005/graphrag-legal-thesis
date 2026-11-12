# ViLexTime bộ test cuối (NHÁP, chưa Accepted, chưa commit)

199 lineage, split `test`, 722 dòng: mỗi lineage có `ranh_gioi` và `giua_khoang` (`twin_of` của `enrich_vilextime.py`). Schema 2.0.0 như release dev h6 (13 cột + `vilextime_meta.jsonl`). Chưa hệ nào chạy trên bộ này.

| Nhóm | Lineage | ranh_gioi | giua_khoang |
|---|---:|---:|---:|
| T2 | 127 | 254 | 254 |
| T3 | 6 | 18 | 18 |
| T6 | 23 | 46 | 46 |
| T1 đối chứng (ngoài `all`) | 43 | 43 | 43 |

`all` = T2+T3+T6 = 156 lineage / 318 dòng giữa khoảng. T6 không đáp án: 23. `qsource` (trong meta): silver 75 lineage, new (lo2) 70, supp 11, t1 43.

## Nguồn
- 156 lineage chính: `data/review/ai_research/2026-11-11_final_count/final_lineages.json` (`count_final.py`); 43 T1: `2026-11-11_t1_labels/cmt_confirmed_t1.json` (`t1_dat`). Danh sách gộp: `lineages_199.txt`.
- Câu hỏi, đáp án, đáp án ngắn: phiếu khóa `data/review/the4/{lo1_silver,lo2_moi,t1_moi}_worksheet.jsonl` và `2026-11-08_supp18/input/chunk*.jsonl`; script dừng nếu câu hỏi, đáp án, phiên bản hoặc mốc lệch phiếu. Không sửa đáp án ngắn nào.
- Dòng đầy đủ trước làm giàu: `inputs/selected_boundary_rows.jsonl` (nguồn: `inputs/lo2_compiled_worksheet.jsonl`, `inputs/t1_compiled_worksheet.jsonl` sao từ `~/vilextime_loc/`, supp18, `derived/vilextime/T*.jsonl`).
- 27 lineage (16 lo2, 11 supp) không còn trong `derived/vilextime_pool.jsonl` sau dựng lại 10/11; chuỗi phiên bản lấy từ `derived/versions.jsonl` (`inputs/extra_pool.jsonl`) để dựng giữa khoảng. Gold ranh giới của cả 199 trùng phiếu khóa.
- Không có dòng bị loại theo dòng (`excluded_rows.jsonl` rỗng; 0 `partial_repeal`; 2 dòng dafc3b40 không thuộc tập đạt).
- Không dựng dòng `truoc_hieu_luc` (ngoài lát ADR 0006); bản có dòng đó: `inputs/internal_release_with_truoc_hieu_luc.jsonl`.

## Dựng và kiểm
```
.venv/bin/python scripts/pipeline/build_final_release.py          # enrich_vilextime + check_release trên thư mục tạm
PYTHONPATH=src:scripts/eval:scripts/review:scripts/pipeline .venv/bin/python data/vilextime_final/g2_mde.py
sha256sum -c SHA256SUMS
```
`check_release.py` OK (805 dòng nội bộ gồm truoc_hieu_luc); `final_run.validate_rows` OK (361 dòng giua_khoang); 0 trùng lineage và 0 trùng document_id với dev; 0 file dự đoán trong `runs/` có id dòng của 199 lineage (chỉ bản chụp release/phiếu ở `runs/rebuild_*`).

## Hash
- vilextime.jsonl `5766f9162939bd7c37471d8b995b56b6b5dae0c0da11e52ff13d8030587e534c`
- vilextime_meta.jsonl `22142241f8eae7296b48ddad042a3552746070a89d1042663fd41c586acaaa49`
- manifest.json `87093c3f78f4205e77b2c64a45b116cb3dd627465c47b7491a8f264d6675cbcd`
- lineages_199.txt `d34a1ff2086b293152f24706006c25afcaf983b19326a64c014228e3156b4f1d`

## Giới hạn
- Nhãn tầng "AI gán, CMT duyệt, chưa qua luật sư" (meta `review.source = "ai_cmt"`, `guideline_version 4.0`); không người độc lập nào kiểm.
- T1: câu hỏi và đáp án ngắn do `claude-haiku-5-5` viết, chưa người đọc; AC1 AI-A/AI-B của T1 theo `2026-11-11_t1_labels/metrics.json`.
- `final_run.py --step check` đọc `<data>/derived/vilextime/release.jsonl` và so với bộ công bố: để chạy G3 phải có thư mục `--data` chứa bản nội bộ của release này (như thư mục tạm của build); chưa làm.
- `check_release` đòi `review.guideline_version == crosscheck.GUIDELINE` (3.0) ở dòng nội bộ; dùng giá trị giữ chỗ, nhãn thật nằm ở meta.
