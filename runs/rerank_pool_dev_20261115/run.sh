#!/usr/bin/env bash
# PLAN_PAPER_GAP B2, bước 1: vùng ứng viên lai ghép sâu 100 trên DEV chứa căn cứ đúng ở bao nhiêu dòng?
# `--hybrid --k 100` cho đúng danh sách mà reranker (`--rerank`, `--pool 100`) sẽ xếp lại:
# BM25 100 + dense 100, trộn RRF, giữ 100. Chỉ truy xuất, không gọi model. KHÔNG chạm bộ test cuối.
# Đọc: recall@100 thấp thì reranker bị chặn trần ở đó; khi ấy phải đổi embedding trước.
set -euo pipefail
cd "$(dirname "$0")/../.."
O=runs/rerank_pool_dev_20261115; R=data/vilextime_dataset_h6/vilextime.jsonl
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p $O/pool
git rev-parse HEAD > $O/head.txt; git status --porcelain > $O/git_status_start.txt; date -u +%FT%TZ > $O/started_utc.txt
sha256sum $R > $O/inputs.sha256
for s in b4 b7plus b7 bvnone; do
  echo "=== $s $(date -u +%FT%TZ)"
  .venv/bin/python scripts/eval/run_vilextime.py --system $s --hybrid --retrieval-only --k 100 --split dev \
    --as-of-strategy giua_khoang --release $R --hits-cache $O/retrieval.sqlite --out $O/pool/$s.jsonl
done
echo "=== score $(date -u +%FT%TZ)"
PYTHONPATH=src:scripts/eval .venv/bin/python - $R $O <<'EOF'
import json, sys
from pathlib import Path
import score_vilextime as sv

release, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = sv.load_rows(release)
extra = sv.distractors(rows)
for r in rows:
    r["_distractors"] = extra.get(r["id"], [])
runs = {p.stem: {x["id"]: x for x in map(json.loads, p.open(encoding="utf-8"))} for p in sorted((out / "pool").glob("*.jsonl"))}
units, _, _ = sv.units_of(Path("data"), runs)
ks = (1, 5, 10, 20, 50, 100)
table = {}
for name, preds in runs.items():
    rep = sv.report(rows, preds, units, "dev", ks=ks)["giua_khoang"]
    table[name] = {g: {"rows": s["rows"], "mrr": s["mrr"], **{f"{m}@{k}": s[f"{m}@{k}"] for m in ("recall", "tv_recall") for k in ks}}
                   for g, s in rep.items()}
    a = table[name]["all"]
    print(f"{name:8s} all n={a['rows']:3d} MRR {a['mrr']:.3f} | recall@ " + " ".join(f"{k}:{a[f'recall@{k}']:.3f}" for k in ks)
          + " | tv_recall@ " + " ".join(f"{k}:{a[f'tv_recall@{k}']:.3f}" for k in ks))
(out / "pool_recall.json").write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
EOF
echo "exit=0 done $(date -u +%FT%TZ)"
