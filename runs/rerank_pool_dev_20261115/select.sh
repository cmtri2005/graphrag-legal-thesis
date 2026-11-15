#!/usr/bin/env bash
# PLAN_PAPER_GAP B2, bước 3 (DEV): chọn reranker.
# Tiêu chí khai trước khi có điểm: MRR của `b4` (RAG phẳng) trên `all`. Không nhìn độ lợi của bộ lọc.
# Cần điểm từ Colab ở $O/scores/scores__*.jsonl (`rerank_score.py score`, gói colab_upload/rerank/).
# Vùng ứng viên đọc lại từ retrieval.sqlite của run.sh, nên không truy xuất lại. Không gọi model, không chạm test.
set -euo pipefail
cd "$(dirname "$0")/../.."
O=runs/rerank_pool_dev_20261115; R=data/vilextime_dataset_h6/vilextime.jsonl
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
sha256sum $O/scores/scores__*.jsonl > $O/scores/SHA256SUMS
for f in $O/scores/scores__*.jsonl; do
  m=$(.venv/bin/python -c 'import json,sys; print(json.loads(open(sys.argv[1]).readline())["model"])' "$f")
  tag=$(basename "$f" .jsonl | sed 's/^scores__//')
  echo "=== $m $(date -u +%FT%TZ)"
  for s in b4 b7 b7plus bvnone; do
    .venv/bin/python scripts/eval/run_vilextime.py --system $s --rerank "$m" --rerank-scores "$f" --retrieval-only \
      --split dev --as-of-strategy giua_khoang --release $R --hits-cache $O/retrieval.sqlite --out $O/rr/$tag/$s.jsonl
  done
  .venv/bin/python scripts/eval/score_vilextime.py $O/rr/$tag/{b4,b7,b7plus,bvnone}.jsonl --split dev --release $R \
    --data data --out $O/rr/$tag/score.json > $O/rr/$tag/score.txt
done
.venv/bin/python - $O <<'PY'
import json, sys
from pathlib import Path
for path in sorted(Path(sys.argv[1], "rr").glob("*/score.json")):
    rep = json.loads(path.read_text(encoding="utf-8"))
    for name in ("b4", "b7", "b7plus", "bvnone"):
        a = rep[name]["giua_khoang"]["all"]
        print(f"{path.parent.name:40s} {name:7s} MRR {a['mrr']:.3f}  R@1 {a['recall@1']:.3f}  TV-R@1 {a['tv_recall@1']:.3f}")
PY
echo "exit=0 done $(date -u +%FT%TZ)"
