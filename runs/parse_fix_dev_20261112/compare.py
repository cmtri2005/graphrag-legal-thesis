#!/usr/bin/env python3
"""Rows changed by the parser fix (before = rebuild_20261110_dev, after = this folder), Accuracy before/after, and the
ADR 0006 P rule re-applied (as select_p.py) on full dev and on dev minus the 12 T6 lineages of t6_dev_r2_20261111."""
import json, random, sys
from pathlib import Path
sys.path.insert(0, "scripts/eval")
from score_vilextime import correct, distractors, interval, load_rows  # noqa: E402

SRC, O = Path("runs/rebuild_20261110_dev"), Path("runs/parse_fix_dev_20261112")
DROP = ["41522558", "6e3d884a", "2cb2c1fa", "7dd23e64", "c203f3d0", "fe9e225a", "7dc9e82a", "92d51460", "1634ac90",
        "6cab03a0", "6caa8e70", "1a267400"]
rows = [r for r in load_rows(Path("data/vilextime_dataset_h6/vilextime.jsonl")) if r.get("split") == "dev" and r["as_of_strategy"] == "giua_khoang"]
out_of = distractors(rows)
for r in rows: r["_distractors"] = out_of.get(r["id"], [])
key = lambda r: r["lineage_id"].split(":")[1][:8]
t6u = [r for r in rows if r["group"] == "T6" and not r["answerable"]]
drop_lin = {x["lineage_id"] for k in DROP for x in t6u if key(x) == k}
assert len(drop_lin) == 12
systems = sorted(p.stem for p in (SRC / "dev").glob("*.jsonl") if not p.stem.endswith(".sample"))
load = lambda d, s: {p["id"]: p for p in map(json.loads, (d / f"dev/{s}.jsonl").open(encoding="utf-8"))}
before = {s: load(SRC, s) for s in systems}; after = {s: load(O, s) for s in systems}
hb = {s: {r["id"]: correct(r, before[s][r["id"]]) for r in rows} for s in systems}
ha = {s: {r["id"]: correct(r, after[s][r["id"]]) for r in rows} for s in systems}
res = {}
for s in systems:
    ch = [r["id"] for r in rows if any(before[s][r["id"]][k] != after[s][r["id"]][k] for k in ("answer", "answerable", "citations"))]
    fo = [r["id"] for r in rows if before[s][r["id"]]["format_ok"] != after[s][r["id"]]["format_ok"]]
    flip = [r["id"] for r in rows if hb[s][r["id"]] != ha[s][r["id"]]]
    res[s] = {"rows_changed": len(ch), "format_ok_changed": len(fo), "correct_flipped": len(flip),
              "acc_before": sum(hb[s].values()) / len(rows), "acc_after": sum(ha[s].values()) / len(rows),
              "changed_ids": ch}
    print(f"{s:10} changed {len(ch):3} format_ok {len(fo):3} correct_flip {len(flip):3}  acc {res[s]['acc_before']:.4f} -> {res[s]['acc_after']:.4f}")

def diff(hit, subset, draws=10_000, seed=20261109):
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

def rule(hit, rs):
    core = [r for r in rs if r["group"] in ("T2", "T3", "T6")]
    out = {"t6_unanswerable": diff(hit, [r for r in core if r["group"] == "T6" and not r["answerable"]]),
           "all_answerable": diff(hit, [r for r in core if r["answerable"]])}
    out["P"] = "proposed3" if out["t6_unanswerable"]["ci95"][0] > 0 and out["all_answerable"]["ci95"][0] >= -0.02 else "proposed2"
    return out
kept = [r for r in rows if r["lineage_id"] not in drop_lin]
sel = {"full_dev_before": rule(hb, rows), "full_dev_after": rule(ha, rows), "minus12_before": rule(hb, kept), "minus12_after": rule(ha, kept)}
for k, v in sel.items(): print(k, json.dumps(v, ensure_ascii=False))
(O / "compare.json").write_text(json.dumps({"systems": res, "select_p": sel, "dropped_lineages": sorted(drop_lin)}, ensure_ascii=False, indent=1) + "\n")
