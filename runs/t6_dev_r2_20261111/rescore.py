#!/usr/bin/env python3
"""H10: T6 dev Accuracy after R2/Q1 exclusions (whole lineage dropped), all 15 systems, plus ADR 0006 P rule
re-applied on the reduced dev. Diagnostic on dev only; predictions from runs/rebuild_20261110_dev (no new calls)."""
import json, random, sys
from pathlib import Path
sys.path.insert(0, "scripts/eval")
from score_vilextime import correct, distractors, interval, load_rows  # noqa: E402

SRC, O = Path("runs/rebuild_20261110_dev"), Path(__file__).parent
# 2026-11-11_t6_package (9 loại) + Q1 chốt loại bởi CMT 11/11 (6cab03a0, 6caa8e70 ở package; 1a267400 ở t6_dev4)
DROP = ["41522558", "6e3d884a", "2cb2c1fa", "7dd23e64", "c203f3d0", "fe9e225a", "7dc9e82a", "92d51460", "1634ac90",
        "6cab03a0", "6caa8e70", "1a267400"]
rows = [r for r in load_rows(Path("data/vilextime_dataset_h6/vilextime.jsonl")) if r.get("split") == "dev" and r["as_of_strategy"] == "giua_khoang"]
out_of = distractors(rows)
for r in rows: r["_distractors"] = out_of.get(r["id"], [])
key = lambda r: r["lineage_id"].split(":")[1][:8]
t6u = [r for r in rows if r["group"] == "T6" and not r["answerable"]]
hits = {k: [r for r in t6u if key(r) == k] for k in DROP}
assert all(len(v) == 1 for v in hits.values()), {k: len(v) for k, v in hits.items()}   # each prefix = exactly one T6 unanswerable lineage
drop_lin = {v[0]["lineage_id"] for v in hits.values()}
kept = [r for r in rows if r["lineage_id"] not in drop_lin]
systems = sorted(p.stem for p in (SRC / "dev").glob("*.jsonl") if not p.stem.endswith(".sample"))
pred = {s: {p["id"]: p for p in map(json.loads, (SRC / f"dev/{s}.jsonl").open(encoding="utf-8"))} for s in systems}
hit = {s: {r["id"]: correct(r, pred[s][r["id"]]) for r in rows} for s in systems}

def acc(s, sub): return [sum(hit[s][r["id"]] for r in sub), len(sub)]
def slices(rs):
    core = [r for r in rs if r["group"] in ("T2", "T3", "T6")]
    return {"all": rs, "t6": [r for r in rs if r["group"] == "T6"], "t6_answerable": [r for r in rs if r["group"] == "T6" and r["answerable"]],
            "t6_unanswerable": [r for r in rs if r["group"] == "T6" and not r["answerable"]], "all_answerable_core": [r for r in core if r["answerable"]]}
table = {when: {s: {k: acc(s, v) for k, v in slices(rs).items()} for s in systems} for when, rs in (("before", rows), ("after", kept))}

def diff(subset, draws=10_000, seed=20261109):
    lin = sorted({r["lineage_id"] for r in subset}); cell = {x: [0, 0, 0] for x in lin}
    for r in subset:
        c = cell[r["lineage_id"]]; c[0] += hit["proposed2"][r["id"]]; c[1] += hit["proposed3"][r["id"]]; c[2] += 1
    rng, vals = random.Random(seed), []
    for _ in range(draws):
        a = b = n = 0
        for x in rng.choices(lin, k=len(lin)): a += cell[x][0]; b += cell[x][1]; n += cell[x][2]
        vals.append((b - a) / n)
    a, b, n = (sum(c[i] for c in cell.values()) for i in range(3))
    return {"rows": n, "lineages": len(lin), "proposed2": a, "proposed3": b, "diff": (b - a) / n, "ci95": interval(vals)}
sl = slices(kept)
p = {"t6_unanswerable": diff(sl["t6_unanswerable"]), "all_answerable": diff(sl["all_answerable_core"])}
p["P"] = "proposed3" if p["t6_unanswerable"]["ci95"][0] > 0 and p["all_answerable"]["ci95"][0] >= -0.02 else "proposed2"
# sanity: 'before' all-accuracy equals the published dev score
ref = json.load((SRC / "all.score.json").open())
for s in systems:
    if s in ref: assert abs(table["before"][s]["all"][0] / table["before"][s]["all"][1] - ref[s]["giua_khoang"]["all"]["accuracy"]) < 1e-9, s
out = {"dropped_lineages": sorted(drop_lin), "rows_before": len(rows), "rows_after": len(kept), "accuracy": table, "select_p_after": p}
(O / "rescore.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
print("rows", len(rows), "->", len(kept))
fmt = lambda x: f"{x[0]}/{x[1]}"
for s in systems:
    b, a = table["before"][s], table["after"][s]
    print(f"{s:10} T6u {fmt(b['t6_unanswerable']):>6} -> {fmt(a['t6_unanswerable']):>5} | T6 {fmt(b['t6']):>6} -> {fmt(a['t6']):>6} | all {b['all'][0]/b['all'][1]:.3f} -> {a['all'][0]/a['all'][1]:.3f}")
print(json.dumps(p, ensure_ascii=False))
