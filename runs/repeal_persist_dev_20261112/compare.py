#!/usr/bin/env python3
"""B (12/11): repeal command kept after its acting document lapses. Dev only; 4/151 prompts changed per
system, only those re-requested (147 answers reused byte-identical prompts). Accuracy before (parse_fix)
vs after, and ADR 0006 P rule on full dev and dev minus 12 T6 lineages (R2 + Q1)."""
import json, random, sys
from pathlib import Path
sys.path.insert(0, "scripts/eval")
from score_vilextime import correct, distractors, interval, load_rows  # noqa: E402

O, B = Path(__file__).parent, Path("runs/parse_fix_dev_20261112/dev")
DROP = ["41522558", "6e3d884a", "2cb2c1fa", "7dd23e64", "c203f3d0", "fe9e225a", "7dc9e82a", "92d51460", "1634ac90",
        "6cab03a0", "6caa8e70", "1a267400"]
rows = [r for r in load_rows(Path("data/vilextime_dataset_h6/vilextime.jsonl")) if r.get("split") == "dev" and r["as_of_strategy"] == "giua_khoang"]
od = distractors(rows)
for r in rows: r["_distractors"] = od.get(r["id"], [])
key = lambda r: r["lineage_id"].split(":")[1][:8]
drop = {r["lineage_id"] for r in rows if r["group"] == "T6" and not r["answerable"] and key(r) in DROP}
assert len(drop) == 12
load = lambda p: {x["id"]: x for x in map(json.loads, p.open(encoding="utf-8"))}
hit = {}
for s in ("proposed2", "proposed3", "p2a3"):
    for tag, d in (("before", B), ("after", O / "dev")):
        pr = load(d / f"{s}.jsonl"); hit[s, tag] = {r["id"]: correct(r, pr[r["id"]]) for r in rows}

def diff(sub, a, b, draws=10_000, seed=20261109):
    lin = sorted({r["lineage_id"] for r in sub}); cell = {x: [0, 0, 0] for x in lin}
    for r in sub:
        c = cell[r["lineage_id"]]; c[0] += hit[a][r["id"]]; c[1] += hit[b][r["id"]]; c[2] += 1
    rng, vals = random.Random(seed), []
    for _ in range(draws):
        x = y = n = 0
        for l in rng.choices(lin, k=len(lin)): x += cell[l][0]; y += cell[l][1]; n += cell[l][2]
        vals.append((y - x) / n)
    x, y, n = (sum(c[i] for c in cell.values()) for i in range(3))
    return {"rows": n, "lineages": len(lin), "a": x, "b": y, "diff": (y - x) / n, "ci95": interval(vals)}

out = {"accuracy": {}, "select_p": {}}
for s in ("proposed2", "proposed3", "p2a3"):
    out["accuracy"][s] = {t: sum(hit[s, t].values()) / len(rows) for t in ("before", "after")}
for name, rs in (("full", rows), ("minus12", [r for r in rows if r["lineage_id"] not in drop])):
    core = [r for r in rs if r["group"] in ("T2", "T3", "T6")]
    p = {"t6_unanswerable": diff([r for r in core if r["group"] == "T6" and not r["answerable"]], ("proposed2", "after"), ("proposed3", "after")),
         "all_answerable": diff([r for r in core if r["answerable"]], ("proposed2", "after"), ("proposed3", "after"))}
    p["P"] = "proposed3" if p["t6_unanswerable"]["ci95"][0] > 0 and p["all_answerable"]["ci95"][0] >= -0.02 else "proposed2"
    out["select_p"][name] = p
(O / "compare.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
print(json.dumps(out, ensure_ascii=False, indent=1))
