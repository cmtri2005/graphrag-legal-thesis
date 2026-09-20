#!/usr/bin/env python3
"""A hand-checkable sheet of ViLexTime candidates (plan phase-4, B3).

`build_question_pool.py` derives every gold answer from the version chain, so
what a human still has to judge is whether that chain is *true*: did this
provision really read this way on this date? That needs the source document,
so each row carries its vbpl.vn link, the acting document's number and the
instruction sentence the change was read from.

Stratified by group and deterministic, so two people checking "the 2026-09-20
sample" are checking the same rows. Leave `correct` as 1 or 0 and put the
reason in `note`; the file is a worksheet, not an output of the pipeline.

Columns after the two you fill in:
    group · doc_num · provision · link · transition_on · actor · as_of_N /
    answer_N (one pair per date the question is asked at) · evidence

Writes `data/derived/vilextime_sample.tsv`.

Usage:
    python scripts/check/sample_question_pool.py               # 30 per group
    python scripts/check/sample_question_pool.py --per-group 50
    python scripts/check/sample_question_pool.py --all         # every candidate
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sqlite3
from pathlib import Path

SEED = 20260920
MAX_DATES = 3


def cell(value: str | None, limit: int = 4000) -> str:
    """One TSV cell: no tabs, no newlines, nothing that splits a row."""
    if not value:
        return ""
    flat = " ".join(str(value).split())
    return flat[:limit] + ("…" if len(flat) > limit else "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--per-group", type=int, default=30)
    parser.add_argument("--all", action="store_true", help="every candidate, not a sample")
    args = parser.parse_args()
    data = args.data

    db = sqlite3.connect(data / "temporal.sqlite")
    documents = {
        doc_id: (number, title, url)
        for doc_id, number, title, url in db.execute("SELECT id, number, title, source_url FROM documents")
    }
    parents = dict(db.execute("SELECT id, parent_id FROM provisions"))
    titles = dict(db.execute("SELECT id, title FROM provisions"))

    def path_of(pid: str) -> str:
        """"Điều 5 › Khoản 2 › Điểm a", so a checker knows where to look."""
        chain = []
        node = pid
        while node and len(chain) < 8:
            if titles.get(node):
                chain.append(titles[node])
            node = parents.get(node)
        return " › ".join(reversed(chain))

    rows = [json.loads(line) for line in
            (data / "derived/vilextime_pool.jsonl").read_text(encoding="utf-8").splitlines()]
    by_group: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by_group[row["group"]].append(row)

    picked: list[dict] = []
    for group in sorted(by_group):
        candidates = sorted(by_group[group], key=lambda r: r["id"])
        if args.all or len(candidates) <= args.per_group:
            picked.extend(candidates)
        else:
            picked.extend(sorted(random.Random(SEED).sample(candidates, args.per_group),
                                 key=lambda r: r["id"]))

    out_path = data / "derived/vilextime_sample.tsv"
    header = ["correct", "note", "group", "doc_num", "provision", "link", "transition_on", "actor"]
    for n in range(1, MAX_DATES + 1):
        header += [f"as_of_{n}", f"answer_{n}"]
    header += ["evidence", "candidate_id"]

    with out_path.open("w", encoding="utf-8") as out:
        out.write("\t".join(header) + "\n")
        for row in picked:
            number, _, url = documents.get(row["document_id"], ("?", "", ""))
            line = ["", "", row["group"], cell(number, 40), cell(path_of(row["provision_id"]), 120),
                    cell(url, 120), cell(row["transition_on"], 12),
                    cell(", ".join(row["actor_numbers"]), 60)]
            for n in range(MAX_DATES):
                gold = row["gold"][n] if n < len(row["gold"]) else None
                if gold is None:
                    line += ["", ""]
                else:
                    answer = gold["text"] if gold["in_force"] else "KHÔNG CÒN HIỆU LỰC"
                    line += [cell(gold["as_of"], 12), cell(answer)]
            line += [cell(" | ".join(row["evidence"]), 600), row["id"]]
            out.write("\t".join(line) + "\n")

    print(f"{len(picked):,} dòng -> {out_path}")
    for group in sorted(by_group):
        taken = sum(1 for r in picked if r["group"] == group)
        print(f"   {group}: {taken:>4,} / {len(by_group[group]):,} ứng viên")
    print("\nĐiền cột `correct` (1 hoặc 0) và `note`. Mở cột `link` để đối chiếu văn bản gốc.")
    print("Cần xác nhận: tại mốc as_of_N, điều khoản có đúng nội dung answer_N không.")


if __name__ == "__main__":
    main()
