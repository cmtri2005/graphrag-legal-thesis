#!/usr/bin/env python3
"""ViLexTime — what must hold of release.jsonl before it is labelled, split or frozen.

  * a boundary row carries every field of its selected row unchanged;
  * a twin has its boundary row's question, answer and gold version, and its
    date lies inside the gold version's window (T5: inside the retroactive one);
  * no row is asked after its document ended ("sau_het_hieu_luc", removed 20/10:
    docs/vilextime-dinh-nghia.md §5), and every row names its `subgroup`;
  * a row asked before the next version applies ("truoc_hieu_luc") carries the
    trap it exists for: `pending` names an act signed on or before as_of that
    takes effect after it;
  * no boundary row is asked after the corpus snapshot;
  * every row has a split, and a lineage or a document never sits in two; no T5
    row is in dev (ADR 0003 §7, decided 28/09);
  * every row carries `retrieved_at` and the guideline version the labels use;
  * every row has at least one `accepted_evidence` unit, each exists in
    corpus layer A, and every version
    of an `evidence_set` in layer B;
  * ids are unique.

Exits non-zero naming the first rows that break a rule. With `--manifest`, and
only when every rule holds, writes `data/vilextime/manifest.json` (committed; the
release itself is derived and gitignored): the sha256 of the release and of every
committed input it was built or judged from, the corpus manifest's, the commit
(and whether the tree had uncommitted changes), the snapshot, the schema and the
row counts per group, as_of mode and split (plan phase-4, J8; JUDGE C5).

Usage:
    python scripts/check/check_release.py [--manifest]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "review"))
from labels import GUIDELINE  # noqa: E402

NEW = {"schema_version", "as_of_strategy", "twin_of", "changed_span", "evidence_set", "accepted_evidence", "subgroup",
       "domain", "domain_source", "legal_markers", "short_answer", "split", "retrieved_at"}
SNAPSHOT = "2026-09-17"
SPLITS = {"dev", "test", "test_contested", "excluded"}
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
            if r["as_of"] > SNAPSHOT:
                out.append(f"{r['id']}: hỏi sau ngày chụp corpus {SNAPSHOT}")
        elif r["as_of_strategy"] == "sau_het_hieu_luc":
            out.append(f"{r['id']}: chế độ sau_het_hieu_luc đã bỏ khỏi bộ chấm (định nghĩa §5)")
        else:
            base = selected.get(r["twin_of"])
            if base is None or any(r[k] != base[k] for k in ("question", "answer", "version_id", "lineage_id")):
                out.append(f"{r['id']}: khác dòng gốc {r['twin_of']}")
                continue
            at = date.fromisoformat(r["as_of"])
            if r["valid_from"] and not (date.fromisoformat(r["valid_from"]) <= at
                                        and (not r["valid_to"] or at < date.fromisoformat(r["valid_to"]))):
                out.append(f"{r['id']}: as_of ngoài khoảng hiệu lực của đáp án")
            p = r.get("pending")
            if r["as_of_strategy"] == "truoc_hieu_luc" and not (p and p["signed_on"] <= r["as_of"] < p["effective_from"]):
                out.append(f"{r['id']}: dòng trước hiệu lực không có văn bản đã ký mà chưa có hiệu lực")
            retro = r.get("retroactive")
            if retro and r["valid_from"] == retro["effective_from"] and at >= date.fromisoformat(retro["issued_on"]):
                out.append(f"{r['id']}: ra ngoài khoảng hồi tố")
        if not r["accepted_evidence"]:
            out.append(f"{r['id']}: không có bằng chứng lớp A nào")
        missing = [u for u in r["accepted_evidence"] if u not in layer_a]
        missing += [e["version_id"] for e in r["evidence_set"] if e["version_id"] and e["version_id"] not in layer_b]
        if missing:
            out.append(f"{r['id']}: bằng chứng không có trong corpus: {missing[:3]}")
        if r.get("split") not in SPLITS:
            out.append(f"{r['id']}: split {r.get('split')!r}")
        elif r["group"] == "T5" and r["split"] == "dev":
            out.append(f"{r['id']}: T5 nằm trong dev")
        if not r.get("retrieved_at") or r["review"]["guideline_version"] != GUIDELINE:
            out.append(f"{r['id']}: thiếu retrieved_at hoặc guideline_version khác {GUIDELINE}")
        if r.get("subgroup") not in SUBGROUPS:
            out.append(f"{r['id']}: subgroup {r.get('subgroup')!r} ngoài {sorted(SUBGROUPS)}")
    for key in ("lineage_id", "document_id"):
        seen = collections.defaultdict(set)
        for r in release:
            seen[r[key] if key == "lineage_id" else r["target"]["document_id"]].add(r.get("split"))
        out += [f"{k}: nằm ở nhiều split {sorted(map(str, v))}" for k, v in seen.items() if len(v) > 1]
    return out


SUBGROUPS = {"T1", "T2", "T3", "T4", "T5a", "T5b", "T6a", "T6b"}   # docs/vilextime-dinh-nghia.md §4


MANIFESTED = ("derived/vilextime/release.jsonl", "derived/corpus/manifest.json", "vilextime/questions.jsonl",
              "vilextime/short_answers.jsonl", "vilextime/sample.jsonl", "vilextime/dropped.jsonl",
              "review/labels.tsv", "review/crosscheck_A.tsv", "review/crosscheck_B.tsv",
              "review/crosscheck_result.json", "review/validity_queue.tsv", "review/temporal_candidates.jsonl",
              "review/t5_documents.tsv", "review/t5_items.tsv")


def manifest(data: Path, release: list[dict]) -> dict:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=data.parent).stdout.strip()

    return {
        "schema_version": sorted({r["schema_version"] for r in release}),
        "snapshot": SNAPSHOT,
        "commit": git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes": bool(git("status", "--porcelain", "--", "scripts", "src", "data/vilextime", "data/review",
                                        ":(exclude)data/vilextime/manifest.json")),
        "sha256": {f: hashlib.sha256((data / f).read_bytes()).hexdigest() for f in MANIFESTED if (data / f).exists()},
        "rows": len(release),
        "counts": {f"{g} · {m} · {sp}": n for (g, m, sp), n in sorted(collections.Counter(
            (r["group"], r["as_of_strategy"], r["split"]) for r in release).items())},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--manifest", action="store_true", help="write data/vilextime/manifest.json when all rules hold")
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
    modes = collections.Counter(r["as_of_strategy"] for r in release)
    print(f"OK: {len(release):,} dòng ({dict(modes)}); "
          f"{len(need_a):,} đơn vị lớp A và {len(need_b):,} phiên bản lớp B đều có trong corpus")
    boundary = [r for r in release if r["as_of_strategy"] == "ranh_gioi"]
    for group in sorted({r["group"] for r in boundary}):
        these = [r for r in boundary if r["group"] == group]
        print(f"  {group}: dev {sum(r['split'] == 'dev' for r in these) / len(these):.1%} số dòng ranh giới")
    if args.manifest:
        out = args.data / "vilextime/manifest.json"
        out.write_text(json.dumps(manifest(args.data, release), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"-> {out}")


if __name__ == "__main__":
    main()
