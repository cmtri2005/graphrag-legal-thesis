#!/usr/bin/env python3
"""ViLexTime — where to look, for the 100% check (guideline 3.0 §5). Never a verdict.

D5 measured why the two annotators of D4 disagreed: on 26 T6 rows one of them
never searched for where the repealed content went (§3 T6, step 2), and on T2/T3
they read differently whether the change touches what the question asks. Both
are look-ups a machine can do once, the same way for both people, so neither has
to dig alone and both read the same evidence. Writes
data/review/kiem_goi_y.jsonl, one line per boundary row of the release, read by
`crosscheck.py kiem`:

    cac_phien_ban   every version of the row's provision with its window, the act
                    that opened it and the word diff from the version before it
                    (generate_questions.changes, the diff the question writer saw);
                    the row's own version is marked. T6 adds the repeal.
    goi_y_cho_moi   T6 only: (1) what the repealing act also wrote into the same
                    base document ("Sửa đổi …", "Bổ sung …"), most similar to the
                    repealed text first; (2) the provisions in force on the
                    repeal date most similar to it, by the BM25 index of the
                    retrieval corpus (tier `propagated`).

Both cells say what was found and where, never what it means: whether content
moved is the seven-factor test a person makes (definition §6, item 7).

Usage:
    python scripts/review/kiem_hints.py
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/pipeline"))
from generate_questions import changes, words  # noqa: E402
from vilexgraph.framework.corpus import Corpus  # noqa: E402
from vilexgraph.framework.retrieve import lexical  # noqa: E402

OPS = {"amend": "sửa", "replace": "thay", "repeal": "bãi bỏ", "correct": "đính chính", "suspend": "ngưng"}
SNIPPET, DIFF_MAX, WHERE = 260, 700, 90
# Where content goes when it is repealed (guideline §3 T6, step 2): the repealing act itself, or
# a provision that changed the same day. Same-day hits are listed apart from the rest, which only
# resemble the text; SAME_DAY days either side absorbs acts dated a few days off their effect.
SAME_ACT, SAME_DAY_HITS, OTHER_HITS, SEARCH_K, SAME_DAY = 3, 3, 2, 40, 31
WRITES = ("sửa đổi", "bổ sung", "như sau", "thay thế")
NOTICE = "Gợi ý của máy, có thể sai, không phải kết luận: bạn tự đối chiếu bảy yếu tố."


def clip(text: str, n: int = SNIPPET) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n].rstrip() + "…"


def jaccard(a: str, b: str) -> float:
    x, y = set(words(a)), set(words(b))
    return len(x & y) / (len(x | y) or 1)


def timeline(versions: list[dict], openers: dict[int, str], mine: int | None,
             repeal: str | None = None) -> str:
    """The version chain as an annotator reads it: windows, who opened each, what changed."""
    lines = []
    for k, v in enumerate(versions):
        span = f"{v['from'] or '?'} → {v['to'] or 'nay'}"
        who = f" · {openers[v['ordinal']]}" if v["ordinal"] in openers else (" · bản gốc" if k == 0 else "")
        mark = "   ◀ đáp án của dòng này" if v["ordinal"] == mine else ""
        lines.append(f"[{v['ordinal']}] {span}{who}{mark}")
        if k:
            lines.append(f"    chỗ đổi: {clip(changes(versions[k - 1]['text'], v['text']), DIFF_MAX)}")
    if repeal:
        lines.append(repeal)
    return "\n".join(lines)


def law_id(corpus: Corpus, document_id: str | None) -> str:
    row = corpus.document(document_id) if document_id else None
    return (row["law_id"] or document_id) if row else (document_id or "?")


def versions_of(corpus: Corpus, lineage: str) -> list[dict]:
    rows = corpus.db.execute("SELECT ordinal, local_from, local_to, text FROM units"
                             " WHERE layer='version' AND provision_id=? ORDER BY ordinal", (lineage,))
    return [{"ordinal": r[0], "from": r[1], "to": r[2], "text": r[3]} for r in rows]


def same_act(corpus: Corpus, actor: str, base_document: str, repealed: str) -> list[str]:
    """What the repealing act also wrote into the base document, most similar first."""
    found, seen = [], set()
    for target, text in corpus.db.execute(
            "SELECT provision_id, text FROM units WHERE kind='instruction' AND document_id=?", (actor,)):
        # what was written in, not what was struck out: a repeal list item does not say "sửa đổi"
        if not target or text in seen or not any(w in text[:150].lower() for w in WRITES):
            continue
        seen.add(text)
        home = corpus.db.execute("SELECT document_id FROM units WHERE provision_id=? AND layer='asis' LIMIT 1",
                                 (target,)).fetchone()
        if home and home[0] == base_document:
            found.append((jaccard(text, repealed), text))
    return [f"«{clip(t)}»" for _, t in sorted(found, key=lambda x: -x[0])[:SAME_ACT]]


def in_force(corpus: Corpus, lineage: str, query: str, on: str, base_document: str,
             actor: str) -> tuple[list[str], list[str]]:
    """Provisions in force on `on` most like the repealed text: (opened within SAME_DAY days of it, the rest)."""
    same, other = [], []
    day = date.fromisoformat(on)
    for hit in lexical(corpus, query, on, layer="version", tier="propagated", context=True, k=SEARCH_K, fast=True):
        u = corpus.unit(hit.unit_id)
        if u is None or u.provision_id == lineage:
            continue
        start, end = corpus.db.execute("SELECT local_from, local_to FROM units WHERE unit_id=?",
                                       (u.unit_id,)).fetchone()
        near = bool(start) and abs((date.fromisoformat(start) - day).days) <= SAME_DAY
        bucket, cap = (same, SAME_DAY_HITS) if near else (other, OTHER_HITS)
        if len(bucket) == cap:
            continue
        tag = (" [cùng văn bản gốc]" if u.document_id == base_document
               else " [chính văn bản bãi bỏ]" if u.document_id == actor else "")
        where = clip(u.context.split(" › ")[-1], WHERE) if u.context else ""
        bucket.append(f"• {law_id(corpus, u.document_id)} · {where} · hiệu lực {start or '?'} → {end or 'nay'}"
                      f"{tag}: «{clip(u.text)}»")
        if len(same) == SAME_DAY_HITS and len(other) == OTHER_HITS:
            break
    return same, other


def repealer(corpus: Corpus, row: dict) -> str:
    """The document that repealed the row's provision, or its ancestor: the event, else the instruction."""
    event = (row.get("repealed_by") or {}).get("event_id") or ""
    if event.count(":") >= 2:
        return f"document:{event.split(':')[1]}"
    acts = {document: text for target in {row["lineage_id"], row["lineage_id"].split("#")[0]}
            for document, text in corpus.db.execute(
                "SELECT document_id, text FROM units WHERE kind='instruction' AND provision_id=?", (target,))}
    # A repeal is often a list item ("điểm a, điểm b khoản 1 Điều 21") that never says "bãi bỏ":
    # the act in force from the repeal date is the one; failing that, one whose text says so.
    on_day = [d for d in acts if (corpus.document(d) or {"effective_from": None})["effective_from"] == row["as_of"]]
    named = [d for d, text in acts.items() if "bãi bỏ" in text.lower()]
    return max(on_day or named, default="")   # ponytail: ties broken by id; a provision repealed twice is rare


def hints(rows: list[dict], corpus: Corpus) -> dict[str, dict]:
    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_lineage[r["lineage_id"]].append(r)
    out = {}
    for n, (lid, rs) in enumerate(sorted(by_lineage.items()), 1):
        rs.sort(key=lambda r: r["as_of"])
        versions = versions_of(corpus, lid)
        openers = {t["to_version"]: f"{OPS.get(t['op'], t['op'])} bởi {t['actor']['law_id']} (hiệu lực {t['on']})"
                   for r in rs for t in (r.get("derivation") or {}).get("transitions") or ()}
        repeal, suggest = None, ""
        if rs[0]["group"] == "T6":
            after = next((r for r in rs if r["answer"] is None), rs[-1])
            actor = repealer(corpus, after)
            mode = "bãi bỏ đích danh" if after.get("repeal_mode") != "ancestor" else "điều khoản cấp trên bị bãi bỏ"
            repeal = f"Hết hiệu lực từ {after['as_of']} ({mode}) bởi {law_id(corpus, actor) if actor else '?'}"
            text = versions[-1]["text"] if versions else ""
            base = after["target"].get("document_id")
            act = same_act(corpus, actor, base, text) if actor and text else []
            query = f"{after['target'].get('lead_in') or ''} {text}"
            same, other = in_force(corpus, lid, query, after["as_of"], base, actor) if text else ([], [])
            by = law_id(corpus, actor) if actor else "Văn bản bãi bỏ"
            suggest = "\n".join(
                [NOTICE]
                + ([f"(1) {by} cũng sửa, bổ sung văn bản gốc ở:", *act] if act
                   else [f"(1) {by} không sửa, bổ sung chỗ nào khác của văn bản gốc."])
                + [f"(2) Đoạn giống nội dung bị bãi bỏ, mới có hiệu lực quanh ngày {after['as_of']}:", *(same or ["• không có"])]
                + [f"(3) Đoạn giống khác, có hiệu lực ngày {after['as_of']}:", *(other or ["• không có"])])
        for r in rs:
            mine = int(r["version_id"].rsplit(":", 1)[1]) if r.get("version_id") else None
            chain = timeline(versions, openers, mine, repeal) if len(versions) > 1 or repeal else ""
            out[r["id"]] = {"id": r["id"], "cac_phien_ban": chain, "goi_y_cho_moi": suggest}
        if n % 50 == 0:
            print(f"  {n}/{len(by_lineage)} lineage", flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--index", type=Path, default=Path("data/derived/corpus/index.sqlite"))
    args = ap.parse_args()
    rows = [r for r in map(json.loads, (args.data / "derived/vilextime/release.jsonl").open(encoding="utf-8"))
            if r["as_of_strategy"] == "ranh_gioi"]
    corpus = Corpus(args.index)
    got = hints(rows, corpus)
    path = args.data / "review/kiem_goi_y.jsonl"
    path.write_text("".join(json.dumps(got[r["id"]], ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    t6 = [g for g in got.values() if g["goi_y_cho_moi"]]
    print(f"{len(got)} dòng -> {path} · {sum(bool(g['cac_phien_ban']) for g in got.values())} có chuỗi phiên bản"
          f" · {len(t6)} dòng T6 có gợi ý chỗ mới")


if __name__ == "__main__":
    main()
