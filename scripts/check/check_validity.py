#!/usr/bin/env python3
"""ViLexTime — flag release rows whose gold may not be the law in force at as_of (plan phase-4, J2).

The version chain only knows the amendments L2 extracted and applied, and the
portal's own `effTo`. The independent review of 29/09 (docs/reports/JUDGE_DATASET.md,
C1) found gold errors where one of those was missing, almost all on mid-interval
rows. This re-runs its detectors inside the repo, on every row:

  missed_event        an event on the row's document, at any status, that names the
                      target or an ancestor (by id, or by a locator consistent with
                      the target's Điều/Khoản/Điểm), takes effect in (valid_from, as_of]
                      and is not in the row's chain. Supplements are left out: adding a
                      sibling does not change the target's wording
  document_ended      the document may have ended before as_of although its effective_to
                      says otherwise: a genealogy edge that replaces it, or a sentence of
                      another document naming its number with "hết hiệu lực", "thay thế",
                      "bãi bỏ" and no Điều/Khoản, "một số" or phrase named with it
  effectivity_clause  the gold is an entry-into-force sentence: its answer follows from as_of
  after_snapshot      a boundary row asked after the corpus snapshot
  cap_huyen           asked after district level was abolished (01/07/2025) but the row
                      still speaks of "cấp huyện"

A detector, not a verdict: the 29/09 review found 31–37% of its flags true. The
queue is `data/review/validity_queue.tsv`, one line per (row, kind, ref); a re-run
keeps every decision already typed in and marks lines it no longer finds as
`active = khong`. Rows of a cross-check (D4) lineage get `decision = sau_D4`: they
are adjudicated only after the blind labels are in.

Decisions: `loi` (gold wrong) · `co_the_sai` · `bao_dong_gia` · `da_sua` (fixed
upstream) · `sau_D4`. What a `loi` becomes is plan J4's: a twin moves before the
date, a boundary row's lineage is dropped and replaced.

Usage:
    python scripts/check/check_validity.py [--data data]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

SNAPSHOT = "2026-09-17"
DISTRICTS_ABOLISHED = "2025-07-01"
# build_temporal_candidates.ENDING_CODES has 1 ("Văn bản bị bãi bỏ") too, but the portal also uses it
# for the repeal of a single article; only a replacement ends the whole document
ENDING_CODES = {12: "thay thế"}
COLUMNS = ["id", "lineage", "group", "strategy", "kind", "in_kappa", "date", "ref", "evidence",
           "active", "decision", "reviewer", "note"]
DECISIONS = {"", "loi", "co_the_sai", "bao_dong_gia", "da_sua", "sau_D4"}
_EFFECTIVITY = re.compile(r"(?i)có hiệu lực(?: thi hành)?(?: kể)? từ ngày|có hiệu lực thi hành|có hiệu lực kể từ")
_DOC_TYPE = r"(?:Bộ luật|Luật|Pháp lệnh|Nghị định|Nghị quyết|Thông tư liên tịch|Thông tư|Quyết định|Chỉ thị)"
# "Thông tư này thay thế Thông tư số X": the verb, then nothing but the kind of document
_ENDS_BEFORE = re.compile(rf"(?i)(?:thay thế|bãi bỏ|hủy bỏ|huỷ bỏ)\s+(?:toàn bộ\s+)?(?:các\s+)?{_DOC_TYPE}\s+(?:số\s+)?$")
_ENDS_AFTER = re.compile(r"(?i)hết hiệu lực")        # "Nghị định số X ngày … hết hiệu lực (toàn bộ) kể từ …"
_PARTIAL = re.compile(r"(?i)\b(?:điều|khoản|điểm|chương|mục)\s+[0-9a-zđ]+\b|cụm từ|từ ngữ|một số|một phần|các điều"
                      r"|phụ lục|mẫu|biểu|nội dung|hướng dẫn|quy định tại")
# the date the ending takes effect, not the ended document's own date earlier in the sentence
_DATE = re.compile(r"từ ngày\s+(?:(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})|(\d{1,2})/(\d{1,2})/(\d{4}))")
_LEVELS = {"Article": "article_id", "Clause": "clause_id", "Point": "point_id"}


def locator_fits(locator: list[list[str]], target: dict) -> bool:
    """Every part of the locator is the target's own label at that level: the target or an ancestor."""
    return bool(locator) and all(
        lv in _LEVELS and (target.get(_LEVELS[lv]) or "").lower() == str(lb).lower() for lv, lb in locator)


def missed_events(rows: list[dict], events: list[dict], lineage_nodes: dict[str, set[str]]) -> list[tuple]:
    """(row, event) pairs: an event on the target or an ancestor, in (valid_from, as_of], not in the chain."""
    by_doc = collections.defaultdict(list)
    for e in events:
        if e["operation"] == "supplement" or not e.get("effective_on"):
            continue
        for doc in {e.get("target_document_id")} | set(e.get("candidate_document_ids") or ()):
            if doc:
                by_doc[doc].append(e)
    out = []
    for r in rows:
        if not r["answerable"]:
            continue
        chain = {t["event_id"] for t in r["derivation"]["transitions"]}
        mine = lineage_nodes.get(r["lineage_id"], {r["lineage_id"]})
        for e in by_doc.get(r["target"]["document_id"], ()):
            if e["id"] in chain or not (r["valid_from"] < e["effective_on"] <= r["as_of"]):
                continue
            if e.get("target_provision_id"):
                hit = e["target_provision_id"] in mine or r["lineage_id"] in (e.get("affected_provision_ids") or ())
            else:
                hit = locator_fits(e.get("locator") or [], r["target"])
            if hit:
                out.append((r, e))
    return out


def number_pattern(number: str) -> str:
    variants = {number, number.replace("/", "-", 1), number.replace("-", "/", 1)}
    return "|".join(re.escape(v) for v in sorted(variants, key=len, reverse=True))


def sentence_endings(text: str, number: str) -> list[tuple[str, str | None]]:
    """(sentence, date named in it) for each sentence that ends this document as a whole."""
    out = []
    for sentence in re.split(r"(?<=[.;:])\s+|\n", text):
        m = re.search(rf"(?<![\w/-])(?:{number_pattern(number)})(?![\w/])", sentence)
        if not m:
            continue
        before = sentence[:m.start()]
        k = _ENDS_AFTER.search(sentence, m.end())
        # "Các điều 5, 6 của Nghị định X hết hiệu lực": what is named before the number counts too
        after_ok = k and k.start() - m.end() <= 200 and not _PARTIAL.search(sentence[:k.start()])
        if not (_ENDS_BEFORE.search(before) or after_ok):
            continue
        d = _DATE.search(sentence)
        day = None
        if d:
            dd, mm, yy = (d.group(1), d.group(2), d.group(3)) if d.group(1) else (d.group(4), d.group(5), d.group(6))
            day = f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
        out.append((sentence.strip(), day))
    return out


def document_endings(db: sqlite3.Connection, data: Path, targets: dict[str, str]) -> dict[str, list[tuple]]:
    """Target document -> [(date, ref, evidence)] from genealogy edges and from other documents' text."""
    docs = {i: (n, f) for i, n, f in db.execute("SELECT id, number, effective_from FROM documents")}
    out = collections.defaultdict(list)
    raw = {d.removeprefix("document:"): d for d in targets}
    for line in (data / "edges.jsonl").open(encoding="utf-8"):
        edge = json.loads(line)
        if edge["reference_type"] in ENDING_CODES and edge["target_id"] in raw:
            actor = docs.get(f"document:{edge['source_id']}")
            if actor and actor[1]:
                out[raw[edge["target_id"]]].append(
                    (actor[1], f"document:{edge['source_id']}", f"cạnh genealogy: {actor[0]} {ENDING_CODES[edge['reference_type']]}"))
    pattern = re.compile("|".join(f"(?:{number_pattern(n)})" for n in targets.values() if n))
    owners = collections.defaultdict(set)
    for doc, number in targets.items():
        for v in {number, number.replace("/", "-", 1), number.replace("-", "/", 1)}:
            owners[v].add(doc)
    query = ("SELECT p.document_id, v.text FROM versions v JOIN provisions p ON p.id = v.provision_id "
             "WHERE v.ordinal = 1 AND (v.text LIKE '%hiệu lực%' OR v.text LIKE '%thay thế%' OR v.text LIKE '%bãi bỏ%' "
             "OR v.text LIKE '%hủy bỏ%' OR v.text LIKE '%huỷ bỏ%')")
    for actor, text in db.execute(query):
        for found in {m.group(0) for m in pattern.finditer(text)}:
            for doc in owners.get(found, ()):
                if doc == actor:
                    continue
                for sentence, day in sentence_endings(text, targets[doc]):
                    when = day or (docs.get(actor, (None, None))[1])
                    if when:
                        out[doc].append((when, actor, f"{docs.get(actor, ('?',))[0]}: {sentence[:300]}"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    args = ap.parse_args()
    data = args.data
    rows = [json.loads(line) for line in (data / "derived/vilextime/release.jsonl").open(encoding="utf-8")]
    kappa_ids = {r["id"] for r in csv.DictReader((data / "review/crosscheck_A.tsv").open(encoding="utf-8"), delimiter="\t")}
    kappa = {r["lineage_id"] for r in rows if r["id"] in kappa_ids}

    db = sqlite3.connect(f"file:{data / 'temporal.sqlite'}?mode=ro", uri=True)
    lineages = {r["lineage_id"] for r in rows}
    nodes = {pid: set(filter(None, path.strip("/").split("/"))) | {pid}
             for pid, path in db.execute("SELECT id, path FROM provisions") if pid in lineages}
    events = [json.loads(line) for line in (data / "derived/provision_events.jsonl").open(encoding="utf-8")]
    ends = {d: e for d, _, _, e in db.execute("SELECT id, number, effective_from, effective_to FROM documents")}
    targets = {r["target"]["document_id"]: r["target"]["law_id"] for r in rows}

    found: dict[tuple, dict] = {}

    def flag(r: dict, kind: str, date: str, ref: str, evidence: str) -> None:
        found[(r["id"], kind, ref)] = {
            "id": r["id"], "lineage": r["lineage_id"], "group": r["group"], "strategy": r["as_of_strategy"],
            "kind": kind, "in_kappa": "co" if r["lineage_id"] in kappa else "khong", "date": date, "ref": ref,
            "evidence": " ".join(evidence.split())[:400], "active": "co"}

    for r, e in missed_events(rows, events, nodes):
        flag(r, "missed_event", e["effective_on"], e["id"],
             f"{e['operation']} {e['status']}/{e.get('status_reason') or ''} {e.get('actor_number') or ''}: {e.get('evidence') or ''}")
    endings = document_endings(db, data, targets)
    for r in rows:
        doc = r["target"]["document_id"]
        for when, ref, evidence in endings.get(doc, ()):
            known = ends.get(doc)
            if when <= r["as_of"] and (known is None or known > when):
                flag(r, "document_ended", when, ref, evidence)
        if r["answerable"] and _EFFECTIVITY.search(r["answer"] or ""):
            flag(r, "effectivity_clause", r["as_of"], "", r["answer"])
        if r["as_of_strategy"] == "ranh_gioi" and r["as_of"] > SNAPSHOT:
            flag(r, "after_snapshot", r["as_of"], "", f"ngày chụp corpus {SNAPSHOT}")
        said = " ".join(filter(None, (r["question"], r["answer"], r.get("short_answer")))).lower()
        if r["as_of"] >= DISTRICTS_ABOLISHED and "cấp huyện" in said:
            flag(r, "cap_huyen", r["as_of"], "", r["question"])

    path = data / "review/validity_queue.tsv"
    old = {}
    if path.exists():
        for line in csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"):
            if line["decision"] not in DECISIONS:
                raise SystemExit(f"{path}: quyết định lạ {line['decision']!r} ở {line['id']}")
            old[(line["id"], line["kind"], line["ref"])] = line
    merged = []
    typed = {k for k, v in old.items() if v["decision"] not in ("", "sau_D4") or v["note"]}
    for key in sorted(set(found) | typed):
        line = {**old.get(key, {}), **found.get(key, {"active": "khong"})}
        line.setdefault("decision", "")
        if line["in_kappa"] == "co" and not line["decision"]:
            line["decision"] = "sau_D4"
        merged.append({c: line.get(c, "") for c in COLUMNS})
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(merged)

    active = [m for m in merged if m["active"] == "co"]
    print(f"{len(active)} cờ đang bật ({len({m['id'] for m in active})} dòng) -> {path}")
    for kind, n in collections.Counter((m["kind"], m["in_kappa"]) for m in active).most_common():
        print(f"  {kind[0]:<26} κ={kind[1]:<5} {n:>5}")
    for key, n in sorted(collections.Counter((m["kind"], m["strategy"], m["decision"] or "chờ") for m in active).items()):
        print(f"  {' · '.join(key):<50} {n:>5}")


if __name__ == "__main__":
    main()
