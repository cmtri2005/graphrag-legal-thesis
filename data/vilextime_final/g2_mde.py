#!/usr/bin/env python3
"""Pre-run MDE estimate for ADR 0006 F1-F7 (G2). Reads dev / test 2 predictions of OTHER sets only; no test-final row.
SD of the per-lineage paired difference (system B - system A) on the dev / test 2 slice, scaled to the final N:
SE = SD / sqrt(N); MDE80 = (z_{1-a/2} + 0.84) * SE. Two alphas: 0.05 and the Holm worst case 0.05/7.
Run: PYTHONPATH=src:scripts/eval:scripts/review:scripts/pipeline .venv/bin/python data/vilextime_final/g2_mde.py"""
import collections, json, math, statistics
from pathlib import Path
from statistics import NormalDist
import score_vilextime as sc, confirm_vilextime as cv

R = Path("runs")
SETS = {  # name -> (release, split, generation dir, retrieval dir or None)
    "dev": (Path("data/vilextime_dataset/vilextime.jsonl"), "dev", R / "rebuild_20261110_dev/dev", None),
    "test2": (Path("data/vilextime/test2_release_v2.jsonl"), "test", R / "E3_test2/test", R / "E1_test2/test"),
}
# F: (metric, slice, A, B, final lineages)
F = {"F1": ("accuracy", "all", "b4", "proposed2", 156), "F2": ("accuracy", "all", "b5", "proposed2", 156),
     "F3": ("wrong_version", "all", "b4", "proposed2", 156), "F4": ("tv_recall@1", "all_answerable", "b2ctx", "b7", 156),
     "F5": ("tv_recall@1", "all_answerable", "b7", "b7plus", 156), "F6": ("tv_recall@1", "all_answerable", "b7", "b7pp", 156),
     "F7": ("accuracy", "t6_unanswerable", "b7pp", "proposed2", 23)}
ALIAS = {"test2": {"proposed2": "proposed"}}   # test 2 ran P's ancestor `proposed`
z = lambda a: NormalDist().inv_cdf(1 - a / 2) + NormalDist().inv_cdf(0.8)
out = {}
for name, (rel, split, gen, ret) in SETS.items():
    rows = [r for r in sc.load_rows(rel) if r.get("split") == split and r["as_of_strategy"] == "giua_khoang"]
    extra = sc.distractors(sc.load_rows(rel))
    rows = [{**r, "_distractors": extra.get(r["id"], [])} for r in rows]
    preds = {}
    for d in (gen, ret):
        for p in (d.glob("*.jsonl") if d else []):
            if not p.name.endswith("sample.jsonl"):
                preds.setdefault(p.stem, {r["id"]: r for r in map(json.loads, p.open(encoding="utf-8"))})
    units = sc.units_of(Path("data"), {f"x/{k}": v for k, v in preds.items()})[0]
    for fid, (metric, sl, a, b, n) in F.items():
        a, b = ALIAS.get(name, {}).get(a, a), ALIAS.get(name, {}).get(b, b)
        cut = [r for r in rows if cv.SLICES[sl](r) and r["group"] != "T1"] if sl != "all" else [r for r in rows if r["group"] in ("T2", "T3", "T6")]
        if sl == "all_answerable": cut = [r for r in cut if r["answerable"]]
        if sl == "t6_unanswerable": cut = [r for r in rows if r["group"] == "T6" and not r["answerable"]]
        if a not in preds or b not in preds or not cut:
            out[(fid, name)] = None; continue
        by = collections.defaultdict(list)
        for r in cut:
            x, y = (sc.row_scores(r, preds[s].get(r["id"], {}), units)[metric] for s in (a, b))
            if x is not None and y is not None:
                by[r["lineage_id"]].append(y - x)
        d = [statistics.mean(v) for v in by.values()]
        if len(d) < 5: out[(fid, name)] = None; continue
        sd = statistics.stdev(d)
        out[(fid, name)] = dict(n_lin=len(d), mean=statistics.mean(d), sd=sd, se=sd / math.sqrt(n),
                                mde_05=z(0.05) * sd / math.sqrt(n), mde_holm=z(0.05 / 7) * sd / math.sqrt(n))
lines = ["| Mã | Đại lượng, lát | Nguồn SD | lineage nguồn | hiệu quan sát | SD ghép cặp | N cuối | SE | MDE (α 0,05) | MDE (Holm xấu nhất α/7) |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
for fid, (metric, sl, a, b, n) in F.items():
    for name in SETS:
        v = out[(fid, name)]
        lines.append(f"| {fid} | {metric}, {sl} | {name} | " + (" | ".join(["—"] * 7) + " (thiếu dự đoán) |" if v is None else
                     f"{v['n_lin']} | {v['mean']:+.3f} | {v['sd']:.3f} | {n} | {v['se']:.3f} | {v['mde_05']:.3f} | {v['mde_holm']:.3f} |"))
Path("data/vilextime_final/g2_mde_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
