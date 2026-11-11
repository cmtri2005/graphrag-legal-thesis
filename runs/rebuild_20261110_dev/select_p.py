#!/usr/bin/env python3
"""ADR 0006 rule for P on dev: proposed3 - proposed2, paired lineage bootstrap (B=10,000, 95% percentile)."""
import json, random, sys
from pathlib import Path
sys.path.insert(0, "scripts/eval")
from score_vilextime import correct, distractors, interval, load_rows  # noqa: E402

O = Path("runs/rebuild_20261110_dev")
rows = [r for r in load_rows(Path("data/vilextime_dataset_h6/vilextime.jsonl")) if r.get("split") == "dev" and r["as_of_strategy"] == "giua_khoang"]
out_of = distractors(rows)
for r in rows:
    r["_distractors"] = out_of.get(r["id"], [])
pred = {s: {p["id"]: p for p in map(json.loads, (O / f"dev/{s}.jsonl").open(encoding="utf-8"))}
        for s in ("proposed2", "proposed3")}
hit = {s: {r["id"]: correct(r, pred[s][r["id"]]) for r in rows} for s in pred}


def diff(subset, draws=10_000, seed=20261109):
    lineages = sorted({r["lineage_id"] for r in subset})
    cell = {x: [0, 0, 0] for x in lineages}                      # p2 hits, p3 hits, rows
    for r in subset:
        c = cell[r["lineage_id"]]
        c[0] += hit["proposed2"][r["id"]]; c[1] += hit["proposed3"][r["id"]]; c[2] += 1
    rng, values = random.Random(seed), []
    for _ in range(draws):
        a = b = n = 0
        for x in rng.choices(lineages, k=len(lineages)):
            a += cell[x][0]; b += cell[x][1]; n += cell[x][2]
        values.append((b - a) / n)
    a, b, n = (sum(c[i] for c in cell.values()) for i in range(3))
    wins = sum(hit["proposed3"][r["id"]] > hit["proposed2"][r["id"]] for r in subset)
    loss = sum(hit["proposed3"][r["id"]] < hit["proposed2"][r["id"]] for r in subset)
    return {"rows": n, "lineages": len(lineages), "proposed2": a, "proposed3": b, "diff": (b - a) / n,
            "ci95": interval(values), "p3_only": wins, "p2_only": loss}


core = [r for r in rows if r["group"] in ("T2", "T3", "T6")]
result = {
    "t6_unanswerable": diff([r for r in core if r["group"] == "T6" and not r["answerable"]]),
    "all_answerable": diff([r for r in core if r["answerable"]]),
    "sensitivity_answerable_with_T1": diff([r for r in rows if r["answerable"]]),
}
t6, ans = result["t6_unanswerable"], result["all_answerable"]
result["P"] = "proposed3" if t6["ci95"][0] > 0 and ans["ci95"][0] >= -0.02 else "proposed2"
(O / "select_p.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(result, indent=1, ensure_ascii=False))
assert sum(hit["proposed2"].values()) / len(rows) == json.load((O / "all.score.json").open())["proposed2"]["giua_khoang"]["all"]["accuracy"]
