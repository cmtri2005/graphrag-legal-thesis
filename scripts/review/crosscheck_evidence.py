#!/usr/bin/env python3
"""ViLexTime D4 — what an annotator reads behind `source_url`, for the model annotator A.

Writes data/review/crosscheck_evidence.jsonl, one line per row of crosscheck_A.tsv:

    base     the target document (number, dates, status) and the cited Article, or
             its Clause when the row cites one, cut from the raw vbpl text
             (data/raw/<doc>.json, documentContent): the wording as published
    actors   each document that acts on the row (the amend/repeal transitions, the
             repeal of an ancestor, the retroactive actor, and for a direct repeal,
             which has no transition, the event that closed the provision's
             version in data/derived/event_log.jsonl): number, dates, status,
             the passage that acts on the cited unit, its transitional provisions
             and its entry-into-force article

The text is cut from raw documents, never from the parsed provisions or the
`text_updates` that built the gold, so checking the gold against it is not
circular: the event log only says where to look (`evidence`, the sentence the
parser matched). A passage that cannot be found stays empty and is named in
`missing` rather than guessed.

Usage:
    python scripts/review/crosscheck_evidence.py
    python scripts/review/crosscheck_evidence.py --ids ids.txt --out evidence.jsonl   # any release rows
"""
from __future__ import annotations

import argparse
import collections
import csv
import html
import json
import re
import statistics
import unicodedata
from functools import lru_cache
from pathlib import Path

CAP = {"base": 9000, "passage": 5000, "transitional": 4000, "in_force": 2500}   # chars; a prompt carries all of them
BLOCK = re.compile(r"<(?:br|/p|/div|/tr|/li|/h\d|/td)\b[^>]*>", re.I)
ARTICLE = re.compile(r"Điều\s+\d+[a-zđ]?\s*[.:]", re.I)
HEADING = re.compile(r"Điều\s+\d+[a-zđ]?\s*[.:]|Chương\s+[IVXLCDM\d]+\b|Mục\s+\d+\b|Phụ lục\b", re.I)
CLAUSE = re.compile(r"\d+\s*\.\s")
INSTRUCTION = re.compile(r"(\d+|[a-zđ])\s*[.)]\s*(Sửa đổi|Bổ sung|Bãi bỏ|Thay thế|Thay|Bỏ|Đính chính|Điều chỉnh)")
IN_FORCE = re.compile(r"(\d+\s*\.\s*)?(Luật|Bộ luật|Nghị định|Thông tư|Quyết định|Nghị quyết|Pháp lệnh) này có hiệu lực")


def lines(content: str | None) -> list[str]:
    text = unicodedata.normalize("NFC", html.unescape(re.sub(r"<[^>]+>", " ", BLOCK.sub("\n", content or ""))))
    return [s for s in (" ".join(x.split()) for x in text.split("\n")) if s]


def block(ls: list[str], i: int, stop, cap: int) -> str:
    """Line i up to the next line that matches `stop`, cut at `cap` characters."""
    j = next((j for j in range(i + 1, len(ls)) if stop(ls[j])), len(ls))
    text = "\n".join(ls[i:j])
    return text if len(text) <= cap else text[:cap] + " [...cắt bớt]"


def base_passage(ls: list[str], target: dict) -> str:
    article, clause = target["article_id"], target.get("clause_id")
    chapter = re.search(r"Chương\s+([IVXLCDM\d]+)", target.get("provision_path") or "")
    start = 0
    if chapter:     # a decision can carry a second "Điều 1." in the regulation it issues
        start = next((i for i, x in enumerate(ls) if re.match(rf"Chương\s+{chapter[1]}\b", x, re.I)), 0)
    head = re.compile(rf"Điều\s+{re.escape(article)}\s*[.:]", re.I)
    i = next((i for i in range(start, len(ls)) if head.match(ls[i])), None)
    if i is None:
        return ""
    if clause:
        end = next((j for j in range(i + 1, len(ls)) if HEADING.match(ls[j])), len(ls))
        k = next((k for k in range(i + 1, end) if re.match(rf"{re.escape(clause)}\s*\.\s", ls[k])), None)
        if k is not None:
            return ls[i] + "\n" + block(ls, k, lambda x: HEADING.match(x) or CLAUSE.match(x), CAP["base"])
    return block(ls, i, HEADING.match, CAP["base"])


def actor_passage(ls: list[str], evidence: str, law_id: str, article: str) -> str:
    """The instruction that acts on the target, found by the sentence the parser matched."""
    ev = re.compile(re.escape(" ".join(evidence.split()).casefold()) + r"(?!\d)")   # "Điều 6" is not "Điều 60"
    hits = [i for i, x in enumerate(ls) if evidence.strip() and ev.search(x.casefold())]
    if not hits:    # fall back on the target's number and Article
        hits = [i for i, x in enumerate(ls) if law_id in x and re.search(rf"Điều\s+{re.escape(article)}\b", x, re.I)]
    if not hits:
        return ""
    i = next((i for i in hits if law_id in ls[i]), hits[0])
    numbered = bool(re.match(r"\d+\s*[.)]", ls[i]))     # "24. Sửa đổi ..." holds its own "a) Sửa đổi ..." items
    same_level = lambda x: (m := INSTRUCTION.match(x)) and (m[1].isdigit() or not numbered)
    return block(ls, i, lambda x: same_level(x) or HEADING.match(x), CAP["passage"])


def articles(ls: list[str], wanted, cap: int) -> str:
    """Every passage of the actor whose opening line satisfies `wanted`, each up to the next heading."""
    found = [block(ls, i, (HEADING.match if ARTICLE.match(x) else lambda y: HEADING.match(y) or CLAUSE.match(y)), cap)
             for i, x in enumerate(ls)
             if wanted(x)]
    return "\n\n".join(found)[: 2 * cap]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--ids", type=Path, help="one row id per line, instead of the rows of crosscheck_A.tsv")
    ap.add_argument("--out", type=Path, help="default: <data>/review/crosscheck_evidence.jsonl")
    args = ap.parse_args()
    d = args.data

    @lru_cache(maxsize=None)
    def doc(document_id: str) -> dict | None:
        path = d / "raw" / f"{document_id.split(':', 1)[1]}.json"
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        day = lambda v: (v or "")[:10] or None
        return {"meta": {"document": raw.get("docNum"), "title": raw.get("title"), "issued": day(raw.get("issueDate")),
                         "effective_from": day(raw.get("effFrom")), "effective_to": day(raw.get("effTo")),
                         "status_today": (raw.get("effStatus") or {}).get("name")},   # at crawl time, not at as_of
                "lines": lines((raw.get("documentContent") or {}).get("content"))}

    if args.ids:
        order = [x.strip() for x in args.ids.read_text(encoding="utf-8").splitlines() if x.strip()]
    else:
        with (d / "review/crosscheck_A.tsv").open(encoding="utf-8", newline="") as f:
            order = [r["id"] for r in csv.DictReader(f, delimiter="\t")]
    wanted = set(order)
    rows = {r["id"]: r for r in map(json.loads, (d / "derived/vilextime/release.jsonl").open(encoding="utf-8"))
            if r["id"] in wanted}
    assert len(rows) == len(order), f"{len(order) - len(rows)} dòng không còn trong release.jsonl"

    closers = collections.defaultdict(list)     # provision -> applied events that closed one of its versions
    for line in (d / "derived/event_log.jsonl").open(encoding="utf-8"):
        e = json.loads(line)
        if e["outcome"] == "applied":
            for v in e["closed_version_ids"]:
                closers["provision:" + v.split(":")[1]].append((e["event_id"], e["operation"]))

    def acts_of(r: dict) -> list[tuple[str, str]]:
        acts = [(x["event_id"], x["op"]) for x in r["derivation"]["transitions"]]
        if r.get("repealed_by"):
            acts.append((r["repealed_by"]["event_id"], "repeal_ancestor"))
        if r.get("retroactive") and r["retroactive"]["event_id"] not in {e for e, _ in acts}:
            acts.append((r["retroactive"]["event_id"], "amend"))
        return acts or closers[r["target"]["provision_id"]]     # T6 direct repeal: no transition is recorded

    need = {event_id for r in rows.values() for event_id, _ in acts_of(r)}
    events = {}
    for line in (d / "derived/provision_events.jsonl").open(encoding="utf-8"):
        e = json.loads(line)
        if e["id"] in need:
            events[e["id"]] = e

    out, sizes, stats = args.out or d / "review/crosscheck_evidence.jsonl", [], {"actors": 0, "passage": 0, "transitional": 0}
    with out.open("w", encoding="utf-8") as f:
        for rid in order:
            r, missing = rows[rid], []
            t = r["target"]
            base = doc(t["document_id"])
            passage = base_passage(base["lines"], t) if base else ""
            if not passage:
                missing.append("base_passage")
            actors = []
            for event_id, op in acts_of(r):
                e = events.get(event_id)
                a = doc(e["actor_id"]) if e else None
                if not a:
                    missing.append(f"actor:{event_id}")
                    continue
                item = {"op": op, **a["meta"],
                        "passage": actor_passage(a["lines"], e["evidence"] or "", t["law_id"], t["article_id"]),
                        "transitional": articles(a["lines"], lambda x: (ARTICLE.match(x) or CLAUSE.match(x))
                                                and "chuyển tiếp" in x[:80].casefold(),
                                                CAP["transitional"]),
                        "in_force": articles(a["lines"], lambda x: ARTICLE.match(x) and "hiệu lực" in x.casefold()
                                             or IN_FORCE.match(x), CAP["in_force"])}
                stats["actors"] += 1
                stats["passage"] += bool(item["passage"])
                stats["transitional"] += bool(item["transitional"])
                if not item["passage"]:
                    missing.append(f"actor_passage:{a['meta']['document']}")
                actors.append(item)
            rec = {"id": rid, "base": {**(base["meta"] if base else {}), "passage": passage},
                   "actors": actors, "missing": missing}
            line = json.dumps(rec, ensure_ascii=False)
            sizes.append(len(line))
            f.write(line + "\n")

    marked = sum("actor_has_transitional" in (r.get("legal_markers") or []) for r in rows.values())
    found = sum(any(a["transitional"] for a in rec_actors)
                for rec_actors in ([json.loads(x)["actors"] for x in out.open(encoding="utf-8")]))
    no_base = sum(1 for x in out.open(encoding="utf-8") if "base_passage" in json.loads(x)["missing"])
    print(f"{len(order)} dòng -> {out}")
    print(f"  Điều/Khoản ở văn bản gốc: {len(order) - no_base}/{len(order)}")
    print(f"  văn bản tác động: {stats['actors']}, tìm được đoạn tác động {stats['passage']}, "
          f"có điều khoản chuyển tiếp {stats['transitional']}")
    print(f"  dòng mang actor_has_transitional: {marked}; dòng tìm thấy đoạn chuyển tiếp: {found}")
    print(f"  ký tự/dòng: trung vị {int(statistics.median(sizes))}, lớn nhất {max(sizes)}")


if __name__ == "__main__":
    main()
