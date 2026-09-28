#!/usr/bin/env python3
"""ViLexTime — what must hold of release.jsonl before it is labelled, split or frozen.

  * a boundary row carries every field of its selected row unchanged;
  * a twin has its boundary row's question, answer and gold version, and its
    date lies inside the gold version's window (T5: inside the retroactive one);
  * every row has at least one `accepted_evidence` unit, each exists in
    corpus layer A, and every version
    of an `evidence_set` in layer B;
  * ids are unique.

Exits non-zero naming the first rows that break a rule.

Usage:
    python scripts/check/check_release.py
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

NEW = {"schema_version", "as_of_strategy", "twin_of", "changed_span", "evidence_set", "accepted_evidence",
       "domain", "domain_source", "legal_markers", "short_answer"}
UNIT = re.compile(r'"unit_id":\s*"([^"]+)"')


def problems(release: list[dict], selected: dict[str, dict], layer_a: set[str], layer_b: set[str]) -> list[str]:
    out = []
    ids = [r["id"] for r in release]
    if len(ids) != len(set(ids)):
        out.append("id trùng")
    for r in release:
        if r["as_of_strategy"] == "ranh_gioi":
            old = selected.get(r["id"])
            if old is None:
                out.append(f"{r['id']}: không có trong selected.jsonl")
                continue
            now = json.loads(json.dumps({k: v for k, v in r.items() if k not in NEW}))
            for t in now["derivation"]["transitions"]:
                t.pop("op", None)
            if now != {k: v for k, v in old.items() if k not in NEW}:
                out.append(f"{r['id']}: trường cũ bị đổi")
        else:
            base = selected.get(r["twin_of"])
            if base is None or any(r[k] != base[k] for k in ("question", "answer", "version_id", "lineage_id")):
                out.append(f"{r['id']}: khác dòng gốc {r['twin_of']}")
                continue
            at = date.fromisoformat(r["as_of"])
            if r["valid_from"] and not (date.fromisoformat(r["valid_from"]) <= at
                                        and (not r["valid_to"] or at < date.fromisoformat(r["valid_to"]))):
                out.append(f"{r['id']}: as_of ngoài khoảng hiệu lực của đáp án")
            retro = r.get("retroactive")
            if retro and r["valid_from"] == retro["effective_from"] and at >= date.fromisoformat(retro["issued_on"]):
                out.append(f"{r['id']}: ra ngoài khoảng hồi tố")
        if not r["accepted_evidence"]:
            out.append(f"{r['id']}: không có bằng chứng lớp A nào")
        missing = [u for u in r["accepted_evidence"] if u not in layer_a]
        missing += [e["version_id"] for e in r["evidence_set"] if e["version_id"] and e["version_id"] not in layer_b]
        if missing:
            out.append(f"{r['id']}: bằng chứng không có trong corpus: {missing[:3]}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    base, corpus = args.data / "derived/vilextime", args.data / "derived/corpus"
    release = [json.loads(line) for line in (base / "release.jsonl").open(encoding="utf-8")]
    selected = {r["id"]: r for r in map(json.loads, (base / "selected.jsonl").open(encoding="utf-8"))}
    need_a = {u for r in release for u in r["accepted_evidence"]}
    need_b = {e["version_id"] for r in release for e in r["evidence_set"] if e["version_id"]}
    layer_a = {m.group(1) for line in (corpus / "asis.jsonl").open(encoding="utf-8")
               if (m := UNIT.search(line)) and m.group(1) in need_a}
    layer_b = {m.group(1) for line in (corpus / "versions.jsonl").open(encoding="utf-8")
               if (m := UNIT.search(line)) and m.group(1) in need_b}
    found = problems(release, selected, layer_a, layer_b)
    if found:
        raise SystemExit(f"{len(found)} vi phạm:\n" + "\n".join(found[:20]))
    twins = sum(r["as_of_strategy"] == "giua_khoang" for r in release)
    print(f"OK: {len(release):,} dòng ({len(release) - twins:,} ranh giới, {twins:,} giữa khoảng); "
          f"{len(need_a):,} đơn vị lớp A và {len(need_b):,} phiên bản lớp B đều có trong corpus")


if __name__ == "__main__":
    main()
