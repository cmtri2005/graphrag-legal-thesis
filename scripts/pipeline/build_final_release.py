#!/usr/bin/env python3
"""ViLexTime final test release (G2, ADR 0006 §1): 156 main lineages + 43 T1 control lineages, split "test".

Inputs are the locked lists and worksheets only; no model is called, no label is changed.
  1. full pre-enrich boundary rows per lineage: first of lo2 compiled worksheet, supp18 chunk records, T1 compiled
     worksheet (the three sit outside the repo; copied into <out>/inputs/ with sha256), then derived/vilextime/T*.jsonl.
     Question, answer, version and short answer must equal the locked worksheets, or the build stops.
  2. the unchanged `enrich_vilextime.py` runs on a staging data dir (symlinks to the real data; only
     derived/vilextime, vilextime_pool and short_answers differ), so the mid-interval twins (`twin_of`),
     evidence and metadata are the ones of every older release. `check_release.py` runs on the same staging dir.
  3. `export_release.published` / `meta` write vilextime.jsonl + vilextime_meta.jsonl (schema of h6).

Usage: python scripts/pipeline/build_final_release.py [--out data/vilextime_final]
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/pipeline"))
sys.path.insert(0, str(ROOT / "scripts/review"))
from crosscheck import GUIDELINE  # noqa: E402
from export_release import SCHEMA_VERSION, meta, published, row_exclusions  # noqa: E402

AI = ROOT / "data/review/ai_research"
LOC = Path("/home/trica/vilextime_loc")
PID = re.compile(r'"provision_id"\s*:\s*"([^"]+)"')
SHEETS = {"silver": "lo1_silver", "new": "lo2_moi", "t1": "t1_moi"}
TIER = "AI gán, CMT duyệt, chưa qua luật sư"
REVIEW = {"status": "checked", "verdict": "dat", "source": "ai_cmt", "tier": TIER, "guideline_version": "4.0",
          "labeler": "AI-A + AI-B, CMT duyệt", "double_labelled": True, "adjudicated": False, "reasons": []}


def rd(p) -> list[dict]:
    return [json.loads(x) for x in Path(p).open(encoding="utf-8") if x.strip()]


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "data/vilextime_final")
    ap.add_argument("--stage", type=Path)
    args = ap.parse_args()
    out, data = args.out, ROOT / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "inputs").mkdir(exist_ok=True)

    main_ids = json.load(open(AI / "2026-11-11_final_count/final_lineages.json", encoding="utf-8"))["lineages"]
    t1_ids = json.load(open(AI / "2026-11-11_t1_labels/cmt_confirmed_t1.json", encoding="utf-8"))["t1_dat"]
    assert len(main_ids) == 156 and len(t1_ids) == 43 and not set(main_ids) & set(t1_ids)

    # locked worksheets: lineage -> (qsource, slim record)
    locked: dict[str, tuple[str, dict]] = {}
    for q, name in SHEETS.items():
        for r in rd(data / f"review/the4/{name}_worksheet.jsonl"):
            locked[r["lineage_id"]] = (q, r)
    supp = {}
    for f in sorted(glob.glob(str(AI / "2026-11-08_supp18/input/chunk*.jsonl"))):
        for r in rd(f):
            supp[r["record"]["lineage_id"]] = r["record"]
            locked[r["record"]["lineage_id"]] = ("supp", r["record"])

    # full boundary rows
    full: dict[str, list[dict]] = collections.defaultdict(list)
    sources = [("lo2", LOC / "gan5/compiled_worksheet.sourced.jsonl"), ("t1", LOC / "gan_t1/compiled_worksheet.jsonl")]
    for tag, p in sources:
        shutil.copyfile(p, out / "inputs" / f"{tag}_compiled_worksheet.jsonl")
        for r in rd(p):
            full.setdefault(r["lineage_id"], r["rows"])
    for lid, r in supp.items():
        full.setdefault(lid, r["rows"])
    want = set(main_ids) | set(t1_ids)
    for g in ("T1", "T2", "T3", "T6"):
        seen = collections.defaultdict(list)
        for r in rd(data / f"derived/vilextime/{g}.jsonl"):
            if r["lineage_id"] in want:
                seen[r["lineage_id"]].append(r)
        for lid, rs in seen.items():
            full.setdefault(lid, sorted(rs, key=lambda x: x["as_of"]))
    base: list[dict] = []
    for lid in main_ids + t1_ids:
        q, rec = locked[lid]
        slim = {x["id"]: x for x in rec["rows"]}
        rows = {x["id"]: x for x in full[lid]}
        assert set(slim) == set(rows), f"{lid}: boundary ids differ from the locked worksheet"
        for i, s in slim.items():
            x = rows[i]
            x["as_of_strategy"] = "ranh_gioi"
            for k in ("answer", "answerable", "version_id", "as_of"):
                assert x[k] == s[k], f"{i}: {k} differs from the locked worksheet"
            assert x["target"]["citation"] == s["target"]["citation"], i
            x["question"], x["short_answer"] = rec["question"], s["short_answer"]
            x["qsource"] = "t1" if lid in t1_ids else q
            # check_release wants review.guideline_version == crosscheck.GUIDELINE on the internal row; the real label tier
            # goes to the published meta (REVIEW), so this is a placeholder, not a claim.
            x["review"] = {"status": "unchecked", "guideline_version": GUIDELINE, "note": "placeholder, see meta"}
            base.append(x)
    assert not any("dafc3b40" in r["id"] for r in base)   # master plan 11/11: those two lo2 rows are outside the set

    # staging data dir
    stage = args.stage or Path(tempfile.mkdtemp(prefix="vilextime_final_stage_"))
    for sub, skip in (("", {"derived", "vilextime"}), ("derived", {"vilextime", "vilextime_pool.jsonl"}),
                      ("vilextime", {"short_answers.jsonl", "dropped_rows.jsonl"})):
        (stage / sub).mkdir(parents=True, exist_ok=True)
        for e in (data / sub).iterdir():
            if e.name not in skip and not (stage / sub / e.name).exists():
                os.symlink(e, stage / sub / e.name)
    (stage / "derived/vilextime").mkdir(exist_ok=True)
    with (stage / "derived/vilextime/selected.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in base)
    with (stage / "vilextime/short_answers.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps({"lineage_id": r["lineage_id"], "version_id": r["version_id"],
                                 "short_answer": r["short_answer"]}, ensure_ascii=False) + "\n"
                     for r in base if r["answerable"])
    # pool: the real pool plus a chain from versions.jsonl for lineages the 10/11 pool rebuild no longer holds
    have = {json.loads(x)["provision_id"] for x in (data / "derived/vilextime_pool.jsonl").open(encoding="utf-8")
            if json.loads(x)["provision_id"] in want}
    missing = want - have
    extra = collections.defaultdict(list)
    for x in (data / "derived/versions.jsonl").open(encoding="utf-8"):
        if (m := PID.search(x)) and (i := m.group(1)) in missing:
            extra[i].append(json.loads(x))
    assert set(extra) == missing, f"no version chain for {sorted(missing - set(extra))[:3]}"
    shutil.copyfile(data / "derived/vilextime_pool.jsonl", stage / "derived/vilextime_pool.jsonl")
    with (stage / "derived/vilextime_pool.jsonl").open("a", encoding="utf-8") as f, \
            (out / "inputs/extra_pool.jsonl").open("w", encoding="utf-8") as g:
        for lid, vs in sorted(extra.items()):
            entry = {"provision_id": lid, "versions": [{k: v[k] for k in ("id", "ordinal", "text", "effective_from",
                                                                            "effective_to", "created_by_event_id")}
                                                       for v in sorted(vs, key=lambda v: v["ordinal"])]}
            line = json.dumps(entry, ensure_ascii=False) + "\n"
            f.write(line)
            g.write(line)

    py = sys.executable
    subprocess.run([py, "scripts/pipeline/enrich_vilextime.py", "--data", str(stage)], cwd=ROOT, check=True)
    subprocess.run([py, "scripts/check/check_release.py", "--data", str(stage)], cwd=ROOT, check=True)

    rows = rd(stage / "derived/vilextime/release.jsonl")
    q_of = {r["id"]: r["qsource"] for r in base}
    kept = []
    for r in rows:
        if r["as_of_strategy"] not in ("ranh_gioi", "giua_khoang"):
            continue                       # truoc_hieu_luc: not in the ADR 0006 slices, not asked
        r["split"] = "test"
        r["qsource"] = q_of[r["twin_of"] or r["id"]]
        kept.append(r)
    excluded = row_exclusions(stage, kept)
    kept = [r for r in kept if r["id"] not in excluded]
    kept.sort(key=lambda r: (r["group"], r["lineage_id"], r["as_of_strategy"] != "ranh_gioi", r["as_of"]))
    ids = [r["id"] for r in kept]
    assert len(ids) == len(set(ids))
    with (out / "vilextime.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(published(r), ensure_ascii=False) + "\n" for r in kept)
    with (out / "vilextime_meta.jsonl").open("w", encoding="utf-8") as f:
        for r in kept:
            rev = dict(REVIEW) | ({"label_of": r["twin_of"]} if r["twin_of"] else {})
            m = meta(r, rev)
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    with (out / "excluded_rows.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps({"row_id": i, **x}, ensure_ascii=False) + "\n" for i, x in sorted(excluded.items()))
    shutil.copyfile(stage / "derived/vilextime/release.jsonl", out / "inputs/internal_release_with_truoc_hieu_luc.jsonl")
    shutil.copyfile(stage / "derived/vilextime/selected.jsonl", out / "inputs/selected_boundary_rows.jsonl")
    counts = collections.Counter(f"{r['group']} · {r['as_of_strategy']}" for r in kept)
    print(json.dumps({"rows": len(kept), "lineages": len({r["lineage_id"] for r in kept}), "schema": SCHEMA_VERSION,
                      "excluded_rows": len(excluded), "extra_pool_lineages": len(extra),
                      "counts": dict(sorted(counts.items())), "stage": str(stage)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
