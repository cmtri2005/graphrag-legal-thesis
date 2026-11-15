#!/usr/bin/env bash
# PLAN_PAPER_GAP A2: gold mù do người đọc trên bộ test cuối.
#   gold_A = người đọc chính (NMT), mọi dòng.   gold_B = người đọc thứ hai, 30 dòng chung.
# Không rút mẫu. Lấy hết lineage T2/T6 của bộ cuối mà (a) chưa có trong gold mù đợt 1 và
# (b) chưa người gán nào (A hay B cũ) thấy kèm đáp án của kho (`seen_lineages`). Mỗi lineage một dòng;
# T6 lấy dòng sau bãi bỏ, vì đó là khẳng định cần kiểm. Phiếu không hiện nhóm, đáp án hay ngày của kho.
# Sau khi người đọc trả file:  independent_gold.py import A --review $O
#                              independent_gold.py reveal A --review $O --release $R
set -euo pipefail
cd "$(dirname "$0")/../../.."
R=data/vilextime_final/internal/derived/vilextime/release.jsonl
O=data/review/gold_final
SIZES=T2-near:19:6,T2-regular:39:12,T6-direct:14:7,T6-ancestor:9:5

PYTHONPATH=scripts/review .venv/bin/python - "$R" "$O" "$SIZES" <<'EOF'
import collections, json, sys
from pathlib import Path
import independent_gold as ig

release, out, sizes = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
rows = [json.loads(line) for line in release.open(encoding="utf-8")]
lineage_of = {r["id"]: r["lineage_id"] for r in map(json.loads, open("data/derived/vilextime/release.jsonl", encoding="utf-8"))}
lineage_of.update({r["id"]: r["lineage_id"] for r in rows})
gold1 = set(Path("runs/posthoc_g4_20261113/gold_subset/lineages.txt").read_text().split())
seen = ig.seen_lineages(Path("data/review"), lineage_of, "AB")
pool = [r for r in rows
        if r["as_of_strategy"] == "giua_khoang" and r["lineage_id"] not in gold1 | seen
        and (r["group"] == "T2" or (r["group"] == "T6" and not r["answerable"]))]
have = collections.Counter()
for lineage, stratum in {(r["lineage_id"], ig.stratum(r)) for r in pool}:
    have[stratum] += 1
want = {name: int(n) for name, n, _ in (part.split(":") for part in sizes.split(","))}
assert dict(have) == want, f"pool {dict(have)} khác cỡ đã khai {want}"
with (out / "pool.jsonl").open("w", encoding="utf-8") as f:
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in pool)
print(f"pool: {len(pool)} dòng, {sum(have.values())} lineage {dict(sorted(have.items()))}")
EOF

.venv/bin/python scripts/review/independent_gold.py build --release "$R" --review "$O" --only "$O/pool.jsonl" \
    --strata "$SIZES" --solo A --prefix F
for who in A B; do
    .venv/bin/python scripts/review/independent_gold.py export "$who" --review "$O"
done
sha256sum "$R" "$O/pool.jsonl" "$O/gold_sample.tsv" "$O/gold_A.tsv" "$O/gold_B.tsv" > "$O/SHA256SUMS"
