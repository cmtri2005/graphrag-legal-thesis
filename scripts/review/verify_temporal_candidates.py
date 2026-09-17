#!/usr/bin/env python3
"""Backfill T4.3 — independent text corroboration for `effective_to` candidates.

`build_temporal_candidates.py` derives `effective_to` from a single piece of
portal metadata: an edge whose `referenceType` says one held document repeals
or replaces another. That is the same signal used to discover the candidate
in the first place, so it cannot confirm it — accepting it as-is would let a
mis-tagged portal edge become a silent wrong answer to a point-in-time query
(the exact "temporal hallucination" this project is built to avoid).

This script looks for a second, independent signal: does the acting
document's own legal text actually name the target document's `docNum` next
to a repeal/replace/expiry keyword? That is what a human reviewer would look
for by opening the vbpl.vn link, and it draws on data already crawled
(`documentContent.content`), not on the referenceType classification.

A match is strong corroboration and is written as `decision=accept`. A
document that doesn't cite its predecessor by number is NOT written as
`reject` — Vietnamese legal drafting before ~2000 often omits the citation,
so absence of a text match is inconclusive, not contradictory (see
docs/plans/active/backfill-corpus-v2.md, T4.3 note). Those stay out of this
file and need a human (open the links in
`data/derived/temporal_candidates_review.tsv`) or an L2 extraction pass
(master plan P3.10+) to resolve.

Writes `data/review/temporal_candidates.jsonl`. This script only owns
records whose `method` is `text_corroborated` — every re-run recomputes
exactly those and rewrites them, so that part alone is a pure function of
`data/`, delete-and-rerun. Records left by a human or by another reviewing
process (`method` != `text_corroborated`, e.g. `human_reviewed`,
`llm_reviewed`) are read back untouched and never recomputed here — a human
`reject` must never be silently reinstated as `accept` just because this
script's own heuristic later learns to match it. A document already decided
by one of those is also skipped when scanning for new matches, for the same
reason.

Usage:
    python scripts/review/verify_temporal_candidates.py
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

KEYWORDS = ("bãi bỏ", "hết hiệu lực", "thay thế", "hủy bỏ")
ARTICLE_SPLIT = re.compile(r"(?=Điều\s+\d+\.)")
TAG_RE = re.compile(r"<[^>]+>")
WINDOW = 300
# A locator (Điều/khoản/Điểm/Mục/Chương <n>) sitting directly in front of the
# citation scopes the repeal to that one provision — "Bãi bỏ khoản 2 Điều 11
# Nghị định số 78/2016/NĐ-CP" repeals one clause of 78/2016/NĐ-CP, not the
# decree itself, so it can never confirm a document-level `effective_to`.
# The locator word MUST be followed by a number: "Điều kiện", "quy định",
# "danh mục" all contain "điều"/"mục" as ordinary Vietnamese syllables with
# nothing that numbers a provision, and matched this regex as a false alarm
# before the `\s+\d+` requirement was added.
SCOPED_LOCATOR = re.compile(
    r"(Điều|khoản|Điểm|Mục|Chương)\s+\d+[\sA-Za-zĐđÀ-ỹ\d,và]{0,60}?\s*(của\s+)?"
    r"(Nghị định|Thông tư|Quyết định|Luật|Pháp lệnh|Nghị quyết)(\s+liên tịch)?\s+số\s*$",
    re.IGNORECASE,
)


def strip_html(raw_html: str) -> str:
    """Tags dropped with NO inserted separator, entities decoded, whitespace collapsed.

    The portal sometimes splits one citation across adjacent inline tags with
    no whitespace between them — `<a>44/</a><a>2016/QĐ-TTg</a>` — purely for
    its own link styling. Replacing each tag with a space (the usual safe
    default) would turn that into "44/ 2016/QĐ-TTg", which never matches the
    exact docNum string pulled from the document's own field. Dropping tags
    with nothing is safe here because real word/paragraph boundaries in this
    portal's HTML already carry a literal space or newline in the text nodes
    themselves (e.g. `</p>\n  <p>`), so no words get glued together.

    Entities matter too: "BGD&amp;ĐT" in the raw payload must become "BGD&ĐT"
    or it never matches a docNum field that already has the plain ampersand.
    """
    return " ".join(html.unescape(TAG_RE.sub("", raw_html)).split())


def _flexible_pattern(num: str) -> re.Pattern:
    """A docNum matcher tolerant of '-' vs '/' vs ' ' between its parts.

    The structured `docNum` field and the number as actually typed in a
    document's prose disagree on separator conventions often enough to
    matter — "191/CP" in the field, "191-CP" in the text; "64/TC-TCT" in the
    field, "64 TC/TCT" in the text (pre-2000 numbering was never
    standardised). Splitting on separator runs and letting any of '-', '/',
    ' ' stand in for each one catches all of these as the same citation.
    """
    parts = re.split(r"([-/\s]+)", num)
    pattern = "".join(r"[-/\s]*" if re.fullmatch(r"[-/\s]+", p) else re.escape(p) for p in parts)
    return re.compile(pattern, re.IGNORECASE)


def text_confirms(target_num: str, actor_content: str) -> dict | None:
    """A citation and a repeal keyword sharing one "Điều" article.

    A fixed character window around the citation catches a short "Điều X.
    Bãi bỏ Thông tư Y" but misses a numbered repeal list (a) ... b) ... c)
    <our citation>) — item c) can sit arbitrarily far (character-wise) past
    the keyword that opens the list, and the list may live in its own "Điều
    N. Bãi bỏ ..." article, separate from a later "Điều N+1. Hiệu lực thi
    hành" that only states the date. Splitting on "Điều <n>." boundaries and
    checking within one article at a time handles both shapes without
    guessing a window size, since the boundary that matters is the article,
    not a character count.

    A citation immediately preceded by its own locator ("khoản 2 Điều 11
    Nghị định số <target_num>") is repealing one provision OF the target, not
    the target itself, and must not confirm a document-level `effective_to` —
    found by cross-checking 350 auto-accepted candidates against an
    independent reading and generalized here (see backfill-corpus-v2.md,
    T4.3 LLM-as-judge pass).
    """
    if not target_num or not actor_content:
        return None
    text = strip_html(actor_content)
    pattern = _flexible_pattern(target_num)

    for article in ARTICLE_SPLIT.split(text):
        hit = next((k for k in KEYWORDS if k in article.lower()), None)
        if not hit:
            continue
        for m in pattern.finditer(article):
            if SCOPED_LOCATOR.search(article[: m.start()]):
                continue  # this occurrence repeals one provision of target_num, not all of it
            window = article[max(0, m.start() - WINDOW) : m.start() + WINDOW]
            return {"keyword": hit, "snippet": " ".join(window.split())[:300]}
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    args = ap.parse_args()
    d = args.data

    def load(sub: str, doc_id: str) -> dict | None:
        p = d / sub / f"{doc_id}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    candidates = [
        json.loads(line) for line in (d / "derived/temporal_candidates.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    eff_to = [c for c in candidates if c.get("field") == "effective_to"]

    out_path = d / "review" / "temporal_candidates.jsonl"
    kept = []  # decisions this script does not own: never recomputed, never overwritten
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                if rec.get("method") != "text_corroborated":
                    kept.append(rec)
    already_decided = {rec["document_id"] for rec in kept}

    accepted = []
    inconclusive = 0
    now = datetime.now(timezone.utc).isoformat()
    for c in eff_to:
        doc_id = c["document_id"]
        if doc_id in already_decided:
            continue
        actor_id = c["evidence_document_ids"][0]
        target = load("raw", doc_id) or {}
        actor = load("raw", actor_id) or {}
        actor_content = (actor.get("documentContent") or {}).get("content") or ""
        evidence = text_confirms(target.get("docNum", ""), actor_content)
        if evidence is None:
            inconclusive += 1
            continue
        accepted.append(
            {
                "schema_version": 1,
                "document_id": doc_id,
                "field": "effective_to",
                "value": c["value"],
                "decision": "accept",
                "method": "text_corroborated",
                "evidence_document_ids": c["evidence_document_ids"],
                "evidence": evidence,
                "reviewer": "claude-sonnet-5-agent",
                "reviewed_at": now,
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for rec in kept + accepted:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"{len(eff_to)} effective_to candidates ({len(already_decided)} already decided by a human/other reviewer, left untouched)")
    print(f"  {len(accepted)} accepted -> {out_path} (target docNum cited near a repeal/replace keyword in actor's own text)")
    print(f"  {inconclusive} inconclusive (no explicit citation found — common in pre-2000 drafting; needs human or L2 extraction, NOT rejected)")


if __name__ == "__main__":
    main()
