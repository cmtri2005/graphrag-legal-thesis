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

## Chạy G4
`internal/` là thư mục `--data` cho `final_run.py`: `derived/vilextime/release.jsonl` (722 dòng nội bộ, `split` = `test`, đúng các id của `vilextime.jsonl`; `final_run` đòi `published(nội bộ) == công bố` từng dòng) và `selected.jsonl` là file thật; `temporal.sqlite`, `derived/corpus`, `derived/versions.jsonl` là symlink tương đối tới `data/`. Không ghi đè `data/derived/vilextime` (dev). `build_final_release.py` dựng lại thư mục này (cùng byte, đã kiểm hai lần); `sha256sum -c SHA256SUMS` kiểm hash.

Điều kiện: ADR 0006 `Accepted` đã commit; `internal/`, `vilextime*.jsonl`, `manifest.json` đã commit. Cổng `guard_test` đòi mọi đầu vào theo dõi của lệnh (`--release`, `--data`, `--raw`, `--retrieval`, `--source-prompts`, `--prompts` của `api_generate`) sạch trong git, nên **commit sau mỗi bước sinh ra file mà bước sau đọc** (truy xuất, prompt, raw). Chưa chạy trên test; phần dưới là đúng lệnh đã tập dượt trên dev ở `runs/final_rehearsal_g3_20261112/`.

```
cd /home/trica/UIT_Thesis/graphrag-legal-thesis
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; R=data/vilextime_final/vilextime.jsonl; D=data/vilextime_final/internal; O=runs/final_g4_$(date +%Y%m%d)
M=gpt-4o-mini-2024-07-18
FR="$PY scripts/eval/final_run.py --split test --release $R --data $D --raw $O/raw --retrieval $O/retrieval"
mkdir -p $O/raw $O/retrieval

# 1. F4-F6: truy xuất từ vựng k=20, không gọi model; rồi commit $O/retrieval
for s in b2ctx b7 b7plus b7pp; do
  $PY scripts/eval/run_vilextime.py --system $s --no-dense --retrieval-only --split test --as-of-strategy giua_khoang \
    --release $R --hits-cache $O/retrieval.sqlite --out $O/retrieval/$s.jsonl
done

# 2. kiểm + xuất prompt mọi hệ (bộ đệm truy xuất mới ở $O/r1/retrieval.sqlite); rồi commit $O/r1/prompts
$FR --step check --out $O/r1
$FR --step export --out $O/r1

# 3. gọi API hai lần độc lập, cùng prompt (ADR 0006 5b); commit $O/raw sau mỗi lần
for t in r1 r2; do
  for p in $O/r1/prompts/*.jsonl; do
    $PY scripts/eval/api_generate.py --prompts $p --provider openai --model $M --out-dir $O/raw --run-tag $t \
      --temperature 0 --max-tokens 1024 --seed 20261109
  done
done

# 4. nhập, chấm, kiểm định, báo cáo từng lần (lần 2 phát lại prompt của lần 1)
$FR --step check --run-tag r1 --out $O/r1
for st in import score confirm report; do $FR --step $st --run-tag r1 --out $O/r1; done
$FR --step check --run-tag r2 --source-prompts $O/r1/prompts --out $O/r2
for st in export import score confirm report; do $FR --step $st --run-tag r2 --source-prompts $O/r1/prompts --out $O/r2; done

# 5. so hai lần
$PY scripts/eval/compare_runs.py --confirm1 $O/r1/confirm.json --confirm2 $O/r2/confirm.json \
  --gen1 $O/r1/test --gen2 $O/r2/test --release $R --split test --out $O/compare_runs.json
```
Lần 1 là kết quả chính; lần 2 chỉ đo độ ổn định (ADR 0006 5b). `--systems` mặc định là `FINAL_GENERATION` + `proposed2`.

Đã kiểm (12/11, chưa có ADR Accepted): `final_run.py --split test --step check --release $R --data $D ...` dừng ngay ở cổng với `test requires ADR 0006 Status Accepted in a commit contained in HEAD (master plan G3); commit it before running test`. Với `guard_test` bị tắt trong bộ nhớ (chỉ để chứng minh, không sửa `final_run.py`), bước `check` đi hết: `check_release.py` OK 722 dòng, `validate_rows` (không rò dev theo lineage và document_id), `validate_published_release` (722/722 dòng công bố khớp bản nội bộ), tính hash đầu vào; exit 0.

## Hash
- vilextime.jsonl `5766f9162939bd7c37471d8b995b56b6b5dae0c0da11e52ff13d8030587e534c`
- vilextime_meta.jsonl `22142241f8eae7296b48ddad042a3552746070a89d1042663fd41c586acaaa49`
- manifest.json `87093c3f78f4205e77b2c64a45b116cb3dd627465c47b7491a8f264d6675cbcd`
- lineages_199.txt `d34a1ff2086b293152f24706006c25afcaf983b19326a64c014228e3156b4f1d`

## Giới hạn
- Nhãn tầng "AI gán, CMT duyệt, chưa qua luật sư" (meta `review.source = "ai_cmt"`, `guideline_version 4.0`); không người độc lập nào kiểm.
- T1: câu hỏi và đáp án ngắn do `claude-haiku-5-5` viết, chưa người đọc; AC1 AI-A/AI-B của T1 theo `2026-11-11_t1_labels/metrics.json`.
- `final_run.py --step check` so bản công bố với `<data>/derived/vilextime/release.jsonl`; bản nội bộ của release này nằm ở `internal/` (xem "Chạy G4").
- `check_release` đòi `review.guideline_version == crosscheck.GUIDELINE` (3.0) ở dòng nội bộ; dùng giá trị giữ chỗ, nhãn thật nằm ở meta.
