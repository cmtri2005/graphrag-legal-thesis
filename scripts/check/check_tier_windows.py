#!/usr/bin/env python3
"""E0 (MASTER_RESEARCH_GUIDE §8.3): the index's version windows against their sources, and
what each tier of the ladder leaves of the gold.

For every version of every release lineage:

  (a) units.local_from/local_to == derived/versions.jsonl valid_from/valid_to (tier `version`)
  (b) prop_iv == corpus/versions.jsonl effective_intervals                      (tier `propagated`)

and for every release row, per tier (ADR 0004 §1; the predicates of framework/temporal.py):

  answerable    the gold version is admitted at as_of (`<tier>`), and is the only version
                of its lineage admitted (`<tier>_alone`): the most a filter can do for
                TV-Recall@1 before the ranking has a say
  unanswerable  no version of the lineage is admitted, so the repeal is visible to the tier

The windows are the KG's own, so this checks the index and the filters, not the KG: the
independent gold (§5.3.5) checks the KG. Every mismatch is listed in the report.

Usage:
    python scripts/check/check_tier_windows.py --out runs/E0/index_windows.json
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
from pathlib import Path

TIERS = ("document", "version", "propagated")


def _field(line: str, key: str) -> str | None:
    i = line.find(f'"{key}":"')
    if i < 0:
        return None
    i += len(key) + 4
    return line[i:line.index('"', i)]


def _versions(path: Path, lineages: set[str], id_key: str) -> dict[str, dict]:
    out = {}
    for line in path.open(encoding="utf-8"):
        if _field(line, "provision_id") in lineages:
            v = json.loads(line)
            out[v[id_key]] = v
    return out


def inside(windows, at: str) -> bool:
    return any(start is not None and start <= at and (end is None or at < end) for start, end in windows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    rows = [json.loads(line) for line in (args.data / "derived/vilextime/release.jsonl").open(encoding="utf-8")]
    lineages = {r["lineage_id"] for r in rows}
    derived = _versions(args.data / "derived/versions.jsonl", lineages, "id")
    corpus = _versions(args.data / "derived/corpus/versions.jsonl", lineages, "unit_id")
    ids = sorted(set(derived) | set(corpus))

    db = sqlite3.connect(f"file:{args.data / 'derived/corpus/index.sqlite'}?mode=ro", uri=True)
    local, prop, doc = {}, collections.defaultdict(set), {}
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        marks = ",".join("?" * len(chunk))
        for uid, start, end, document in db.execute(
                f"SELECT unit_id, local_from, local_to, document_id FROM units WHERE unit_id IN ({marks})", chunk):
            local[uid], doc[uid] = (start, end), document
        for uid, start, end in db.execute(f"SELECT unit_id, start, end FROM prop_iv WHERE unit_id IN ({marks})", chunk):
            prop[uid].add((start, end))
    window = {d: (start, end) for d, start, end in
              db.execute("SELECT document_id, effective_from, effective_to FROM documents")}

    counts, wrong = collections.Counter(versions=len(ids)), collections.defaultdict(list)
    for vid in ids:
        if vid not in local:
            wrong["missing_from_index"].append(vid)
            continue
        if vid in derived and local[vid] != (derived[vid]["valid_from"], derived[vid]["valid_to"]):
            wrong["local"].append([vid, local[vid], [derived[vid]["valid_from"], derived[vid]["valid_to"]]])
        want = {(w["start"], w["end"]) for w in corpus[vid]["effective_intervals"]} if vid in corpus else None
        if want is not None and prop.get(vid, set()) != want:
            wrong["propagated"].append([vid, sorted(prop.get(vid, ()), key=str), sorted(want, key=str)])
    counts.update({f"mismatch_{k}": len(v) for k, v in wrong.items()})

    def admitted(vid: str, at: str, tier: str) -> bool:
        if not inside([window.get(doc.get(vid), (None, None))], at):
            return False
        if tier == "version":
            return inside([local.get(vid, (None, None))], at)
        return tier == "document" or inside(prop.get(vid, ()), at)

    chain = collections.defaultdict(list)
    for vid in ids:
        chain["provision:" + vid.split(":", 1)[1].rsplit(":", 1)[0]].append(vid)
    tiers = collections.defaultdict(collections.Counter)
    for r in rows:
        if r.get("split") == "excluded":
            continue
        cell = tiers[" · ".join([str(r.get("split")), r["as_of_strategy"], r["group"],
                                 "answerable" if r["answerable"] else "unanswerable"])]
        cell["rows"] += 1
        for tier in TIERS:
            if r["answerable"]:
                gold = admitted(r["version_id"], r["as_of"], tier)
                cell[tier] += gold
                cell[f"{tier}_alone"] += gold and not any(
                    admitted(v, r["as_of"], tier) for v in chain[r["lineage_id"]] if v != r["version_id"])
            else:
                cell[tier] += not any(admitted(v, r["as_of"], tier) for v in chain[r["lineage_id"]])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"counts": counts, "mismatches": wrong,
                                    "tiers": {k: dict(v) for k, v in sorted(tiers.items())}},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(counts))
    for name, cell in sorted(tiers.items()):
        if "giua_khoang" in name:
            print(f"{name:<44} {cell['rows']:>4}  " + "  ".join(
                f"{k} {cell[k] / cell['rows']:.3f}" for k in sorted(cell) if k != "rows"))
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
