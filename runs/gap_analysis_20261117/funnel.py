"""Phễu lỗi proposed2 so với oracle trên lát all (giua_khoang, test, không T5, không qsource t1). Chỉ đọc artifact G4."""
import collections, json, sys
from pathlib import Path
sys.path.insert(0, "scripts/eval")
import score_vilextime as sv

G = Path(sys.argv[1]); REL = Path("data/vilextime_final/vilextime.jsonl")
rows = sv.load_rows(REL)
for r in rows:
    r["answerable"] = r["answerable"] in (True, "True", "true")
    r["accepted_evidence"] = r["accepted_evidence"] if isinstance(r["accepted_evidence"], list) else eval(r["accepted_evidence"])
ex = sv.distractors(rows)
for r in rows: r["_distractors"] = ex.get(r["id"], [])
rows = [r for r in rows if r.get("split") == "test" and r["as_of_strategy"] == "giua_khoang"
        and r["group"] not in sv.DIAGNOSTIC and r.get("qsource") != "t1"]
load = lambda s: {p["id"]: p for p in map(json.loads, (G / f"{s}.jsonl").open(encoding="utf-8"))}
P, O = load("proposed2"), load("oracle")
def rank(r, p):
    acc = set(r["accepted_evidence"])
    for i, u in enumerate(p.get("retrieved") or [], 1):
        if u in acc or u == r["version_id"]: return i
cells = collections.Counter(); by_group = collections.defaultdict(collections.Counter); ex_rows = collections.defaultdict(list)
for r in rows:
    p, o = P[r["id"]], O[r["id"]]
    ok, ook = sv.correct(r, p), sv.correct(r, o)
    if not r["answerable"]:
        cat = "khong_dap_an:" + ("dung" if ok else ("he_van_tra_loi" if p.get("answerable") is not False else "?"))
    else:
        k = rank(r, p)
        pos = "gold@1" if k == 1 else "gold@2-5" if k and k <= 5 else "gold@6-20" if k else "gold_ngoai_top20"
        if ok: why = "dung"
        elif p.get("answerable") is False: why = "sai:tu_choi"
        elif r["_distractors"] and any(f" {s} " in f" {sv.norm(p.get('answer'))} " for s in r["_distractors"]): why = "sai:sai_phien_ban"
        else: why = "sai:noi_dung_khac"
        cat = f"{pos}|{why}|oracle_{'dung' if ook else 'sai'}"
    cells[cat] += 1; by_group[r["group"]][cat] += 1; ex_rows[cat].append(r["id"])
n = len(rows)
print("n", n, "proposed2 acc", round(sum(sv.correct(r, P[r["id"]]) for r in rows) / n, 3),
      "oracle acc", round(sum(sv.correct(r, O[r["id"]]) for r in rows) / n, 3))
for c, v in sorted(cells.items()): print(f"{v:4d}  {c}")
for g, c in sorted(by_group.items()):
    print(g, sum(c.values()), "dung", sum(v for k, v in c.items() if "|dung|" in k or k.endswith(":dung")))
json.dump({"cells": cells, "by_group": by_group, "rows": ex_rows}, open(G.name + "_funnel.json" if False else sys.argv[2], "w"), ensure_ascii=False, indent=1)
