#!/usr/bin/env python3
"""ViLexTime T5 — the worksheet a lawyer fills in (plan phase-4, Q3, D2).

T5 asks about a change made by a document that takes effect before it was
signed. Whether that falls under Điều 152 Luật BHVBQPPL is a legal judgement;
this script lays out the facts for it and decides nothing.

Writes two tab-separated files into `data/review/`:

  t5_documents.tsv  one row per acting document: its dates, the retroactive
                    window, the kind this pipeline guessed (stated
                    retroactive / guidance taking effect with its law /
                    correction), the effectivity clause quoted from its own
                    text, how many candidates and released pairs depend on
                    it, and empty columns for the lawyer's decision.
  t5_items.tsv      one row per T5 lineage that has a question: the question,
                    both dates and both answers, whether it is in the
                    release, and empty columns for the lawyer's verdict.

Re-run after build_vilextime.py; it only reads.

Usage:
    python scripts/review/t5_worksheet.py
"""
from __future__ import annotations

import argparse
import collections
import html
import json
import re
from pathlib import Path

from vilexgraph.build.vocab.status_codes import effective_clause_dates

KIND = {"stated_retroactive": "hồi tố, cần luật sư xét",
        "guidance_in_sync": "hướng dẫn cùng ngày hiệu lực với văn bản được hướng dẫn (cố vấn: loại)",
        "correction": "đính chính (cố vấn: loại)"}


# "có hiệu lực ... kể từ ngày ký" carries no date, so effective_clause_dates
# misses it and shows only a dated exception (97/2026/NĐ-CP did exactly that).
_FROM_SIGNING = re.compile(r"[^.;]*có hiệu lực[^.;]*(?:ngày ký|ngày ban hành|ngày được ban hành)[^.;]*")


UNREADABLE = "(không đọc được)"
NO_CLAUSE = (" · CÂU HIỆU LỰC KHÔNG NÊU NGÀY HỒI TỐ: ngày hiệu lực chỉ lấy từ siêu dữ liệu cổng;"
             " luật sư xác nhận văn bản có thật sự hồi tố không (JUDGE_DATASET N4)")


def effectivity_words(content: str) -> str:
    text = " ".join(re.sub(r"<[^>]+>", " ", html.unescape(content)).split())
    parts = [m[0].strip() for m in _FROM_SIGNING.finditer(text)][:1]
    parts += [words for _, words in effective_clause_dates(content)[:2]]
    return " | ".join(parts) or UNREADABLE


def cell(value: object) -> str:
    return " ".join(str(value if value is not None else "").split())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    d = ap.parse_args().data

    records = [json.loads(line) for line in (d / "derived/vilextime/T5.jsonl").open(encoding="utf-8")]
    released = {json.loads(line)["lineage_id"] for line in (d / "derived/vilextime/selected.jsonl").open(encoding="utf-8")
                if json.loads(line)["group"] == "T5"}
    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for r in records:
        by_lineage[r["lineage_id"]].append(r)

    actors: dict[str, dict] = {}
    candidates, pairs = collections.Counter(), collections.Counter()
    for lid, rs in by_lineage.items():
        retro = rs[0]["retroactive"]
        actors[retro["actor_document_id"]] = retro
        candidates[retro["actor_document_id"]] += 1
        pairs[retro["actor_document_id"]] += lid in released

    out = d / "review"
    with (out / "t5_documents.tsv").open("w", encoding="utf-8") as f:
        f.write("\t".join(["văn bản tác động", "tên", "ngày ký", "ngày hiệu lực", "số ngày hồi tố",
                           "phân loại (máy đoán)", "câu hiệu lực trong văn bản", "số điều khoản ứng viên",
                           "số cặp trong bản phát hành", "link",
                           "LUẬT SƯ: thuộc Điều 152? (có/không)", "LUẬT SƯ: ghi chú"]) + "\n")
        for doc_id, retro in sorted(actors.items(), key=lambda kv: -candidates[kv[0]]):
            raw_path = d / "raw" / f"{doc_id.split(':', 1)[1]}.json"
            raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
            words = effectivity_words((raw.get("documentContent") or {}).get("content") or "")
            # 12/2015/NĐ-CP (7 released pairs): the retroactive date comes from the portal's
            # metadata alone, so whether it is retroactive at all is the lawyer's first question
            kind = KIND[retro["kind"]] + (NO_CLAUSE if words == UNREADABLE else "")
            f.write("\t".join(cell(v) for v in [
                retro["actor_law_id"], raw.get("title"), retro["issued_on"], retro["effective_from"],
                retro["window_days"], kind, words,
                candidates[doc_id], pairs[doc_id],
                f"https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID={doc_id.split(':', 1)[1]}", "", "",
            ]) + "\n")

    with (out / "t5_items.tsv").open("w", encoding="utf-8") as f:
        f.write("\t".join(["lineage_id", "trong bản phát hành", "văn bản tác động", "phân loại",
                           "văn bản bị sửa", "điều khoản", "câu hỏi", "mốc trước", "đáp án trước",
                           "mốc sau (trong khoảng hồi tố)", "đáp án sau",
                           "LUẬT SƯ: đáp án mốc sau đúng? (có/không)", "LUẬT SƯ: ghi chú"]) + "\n")
        for lid, rs in sorted(by_lineage.items(), key=lambda kv: (kv[1][0]["retroactive"]["actor_law_id"], kv[0])):
            if rs[0]["question_source"]["kind"] != "llm":
                continue                                   # no question yet: nothing to judge
            before, after = sorted(rs, key=lambda r: r["as_of"])
            t = before["target"]
            f.write("\t".join(cell(v) for v in [
                lid, "có" if lid in released else "không", before["retroactive"]["actor_law_id"],
                KIND[before["retroactive"]["kind"]], t["law_id"], t["citation"], before["question"],
                before["as_of"], before["answer"], after["as_of"], after["answer"], "", "",
            ]) + "\n")

    print(f"{len(actors)} văn bản -> {out / 't5_documents.tsv'}")
    print(f"{sum(1 for rs in by_lineage.values() if rs[0]['question_source']['kind'] == 'llm')} điều khoản có câu hỏi "
          f"({len(released)} trong bản phát hành) -> {out / 't5_items.tsv'}")


if __name__ == "__main__":
    main()
