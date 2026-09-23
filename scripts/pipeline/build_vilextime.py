#!/usr/bin/env python3
"""ViLexTime — the released QA records, one per (provision, as_of) (ADR 0003).

`build_question_pool.py` writes one row per provision lineage, with a `gold`
array holding one entry per date the question is asked at. That shape is why
the hand-check worksheet silently dropped a four-version chain's last answer,
and why the time anchor cannot be filtered on. Here the array is unrolled: one
record per (provision, `as_of`), so every record scores on its own and all six
groups share one schema.

Nothing is re-derived. The pool already holds the gold, the version chain, the
events and the amending documents; this reads `data/temporal.sqlite` only for
what the pool does not carry — the document's number and type, and the
provision's ancestor titles, which together make the citation a human reads.

`split` stays null until P4.9 assigns it; ADR 0003 requires every row sharing a
`lineage_id` to land in the same split, which is a decision over all groups at
once, not one this script can make per group.

Writes `data/derived/vilextime/<group>.jsonl`. Offline and deterministic:
delete and re-run for a byte-identical file.

Usage:
    python scripts/pipeline/build_vilextime.py --group T1
    python scripts/pipeline/build_vilextime.py            # every group in the pool
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
from datetime import date
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
QUESTION_TEMPLATE_ID = "as_of_provision_text.v1"
# "Điểm đ" -> "đ", "Khoản 3" -> "3", "Điều 23" -> "23". The label is the whole
# tail because an article can be "23a" and a point can be "đ".
_LABEL = re.compile(r"^(?:Điều|Khoản|Điểm)\s+(?P<label>\S+)$")
_CITED = {"Article": "article_id", "Clause": "clause_id", "Point": "point_id"}
# A source node whose title is the bare word ("Điều" with no number), which makes
# the citation unusable: "Khoản 3 Điều".
_UNTITLED = re.compile(r"(?:Điều|Khoản|Điểm)(?:\s|$)(?!\S)")
_CONTAINERS = ("Chapter", "Section", "Subsection")


def citation(chain: list[tuple[str, str]]) -> str:
    """"Điểm đ Khoản 3 Điều 23" — innermost first, the way a lawyer cites it."""
    return " ".join(title for level, title in reversed(chain) if level in _CITED)


def parts_of(chain: list[tuple[str, str]]) -> dict[str, str | None]:
    """The Điều/Khoản/Điểm numbers, which no published Vietnamese dataset carries."""
    out: dict[str, str | None] = {"article_id": None, "clause_id": None, "point_id": None}
    for level, title in chain:
        match = _LABEL.match(title)
        if level in _CITED and match:
            out[_CITED[level]] = match.group("label")
    return out


def flags_of(level: str, cite: str, answer: str | None, chain: list[tuple[str, str]]) -> list[str]:
    """Closed vocabulary (ADR 0003 §9): what is wrong with this candidate.

    Structural faults only — a target that is not a provision at all, a text
    that is only the node's own heading, a source node with no number. Answer
    length is deliberately not judged here: most short answers are short
    provisions ("đ) Số lượng, khối lượng dịch vụ thủy nông được trợ cấp;"), and
    the B3 hand-check owns that criterion.

    A flag explains; it does not exclude. P4.9 routes flagged rows to the
    `excluded` split, which is what keeps them out of the default metric.
    """
    flags = []
    if level in _CONTAINERS:
        flags.append("not_a_provision")
    if answer and chain and answer.strip() == chain[-1][1].strip():
        flags.append("heading_only")
    if _UNTITLED.search(cite or ""):
        flags.append("untitled_ancestor")
    return flags


def question_of(cite: str, doc_type: str, law_id: str, as_of: str) -> str:
    day = date.fromisoformat(as_of).strftime("%d/%m/%Y")
    where = f"{cite} {doc_type} số {law_id}".strip() if cite else f"{doc_type} số {law_id}".strip()
    return f"Tính đến ngày {day}, {where} quy định nội dung gì?"


def transitions_of(row: dict, documents: dict[str, tuple]) -> list[dict]:
    """One object per amendment, so actor, event, evidence and date cannot drift.

    The pool's `event_ids`, `evidence` and `actor_numbers` are three lists each
    sorted independently, so index i of one does not describe index i of
    another once a chain has three amendments. The join is already in the data:
    an event id is `event:<portal id>:<digest>`, that portal id names the
    acting document, and that document's `effective_from` is the date the new
    version opens.
    """
    acting = {}
    for event_id in row["event_ids"]:
        document_id = f"document:{event_id.split(':', 2)[1]}"
        document = documents.get(document_id)
        if document and document[4]:
            acting.setdefault(document[4], (event_id, document_id))

    out = []
    for before, after in zip(row["versions"], row["versions"][1:]):
        event_id, actor_id = acting.get(after["effective_from"], (None, None))
        number, _, _, _, effective_from, _ = documents.get(actor_id, (None,) * 6)
        out.append({
            "on": after["effective_from"],
            "from_version": before["ordinal"],
            "to_version": after["ordinal"],
            "event_id": event_id,
            "actor": {"law_id": number, "document_id": actor_id,
                      "effective_from": effective_from},
        })
    return out


def records_of(row: dict, documents: dict[str, tuple], chains: dict[str, list],
               parents: dict[str, str], lead_ins: dict[tuple[str, str], str],
               questions: dict[str, dict]) -> list[dict]:
    """One record per entry in the pool row's `gold` array."""
    number, doc_type, url, _, _, title = documents[row["document_id"]]
    parent_id = parents.get(row["provision_id"])
    chain = chains[row["provision_id"]]
    cite = citation(chain)
    version_ids = [v["id"] for v in row["versions"]]
    by_id = {v["id"]: v for v in row["versions"]}
    transitions = transitions_of(row, documents)
    # One generated question serves every date of a lineage (C3). Rows whose
    # question has not been generated — or whose generated one failed C2 — keep
    # the template, and `question_source.kind` says which is which.
    generated = questions.get(row["provision_id"])
    out = []
    for gold in row["gold"]:
        version = by_id.get(gold["version_id"]) if gold["version_id"] else None
        out.append({
            "schema_version": SCHEMA_VERSION,
            "id": f"{row['id']}:{gold['as_of']}",
            "lineage_id": row["provision_id"],
            "group": row["group"],
            "split": None,                      # P4.9, grouped by lineage_id
            "num_versions": len(row["versions"]),
            "num_transitions": len(transitions),
            "question": (generated["question"] if generated
                         else question_of(cite, doc_type or "", number or "", gold["as_of"])),
            "question_source": (
                {"kind": "llm", "provider": generated["provider"], "model": generated["model"],
                 "temperature": generated["temperature"], "prompt_sha": generated["prompt_sha"]}
                if generated else {"kind": "template", "id": QUESTION_TEMPLATE_ID}),
            "as_of": gold["as_of"],
            "target": {
                "document_id": row["document_id"],
                "law_id": number,
                "doc_type": doc_type,
                "document_title": title,
                **parts_of(chain),
                "citation": cite,
                "provision_path": " › ".join(title for _, title in chain),
                "provision_id": row["provision_id"],
                "parent_id": parent_id,
                "level": row["level"],
                # The ancestor's lead-in as it stood at `as_of`. Half the
                # provisions are list items ("d) Đá gốc tạo vỏ phong hóa;")
                # that mean nothing without the Khoản that introduces them, so
                # a question cannot be phrased — or answered — without it.
                # This is structural framing, not retrieval context: ADR 0003
                # §5 keeps the searchable corpus a separate artifact.
                "lead_in": lead_ins.get((parent_id, gold["as_of"])),
            },
            "answer": gold["text"],
            "answerable": gold["in_force"],
            "no_answer_reason": None if gold["in_force"] else "provision_repealed",
            "in_force": gold["in_force"],
            "version_id": gold["version_id"],
            "valid_from": version["effective_from"] if version else None,
            "valid_to": version["effective_to"] if version else None,
            "derivation": {
                "transitions": transitions,
                "query": f"as_of({row['provision_id']}, {gold['as_of']})",
            },
            "relevant_version_ids": version_ids,
            "utilized_version_ids": [gold["version_id"]] if gold["version_id"] else [],
            "source_url": url,
            "jurisdiction": "VN",
            "language": "vi",
            "review": {"status": "unchecked", "labels": [], "adjudicator": None,
                       "guideline_version": "1.0", "note": ""},
            "flags": flags_of(row["level"], cite, gold["text"], chain),
            "similarity": row.get("similarity"),
        })
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--group", action="append", help="repeatable; default: every group in the pool")
    args = parser.parse_args()
    data = args.data
    wanted = set(args.group) if args.group else None

    rows = [json.loads(line) for line
            in (data / "derived/vilextime_pool.jsonl").read_text(encoding="utf-8").splitlines()
            if wanted is None or json.loads(line)["group"] in wanted]
    if not rows:
        raise SystemExit(f"no candidates for {sorted(wanted or [])} in vilextime_pool.jsonl")

    db = sqlite3.connect(data / "temporal.sqlite")
    documents = {row[0]: row[1:] for row in
                 db.execute("SELECT id, number, rank, source_url, issued_on, effective_from, title FROM documents")}

    # Two streaming passes, so 1.7M provisions never land in a dict: the first
    # reads the candidates' materialised paths, the second only the ancestors
    # those paths name.
    wanted_provisions = {row["provision_id"] for row in rows}
    paths = {pid: path for pid, path in db.execute("SELECT id, path FROM provisions")
             if pid in wanted_provisions}
    needed = {pid for path in paths.values() for pid in path.strip("/").split("/") if pid}
    titles = {pid: (level, title) for pid, level, title
              in db.execute("SELECT id, level, title FROM provisions")
              if pid in needed and title}
    chains = {pid: [titles[a] for a in path.strip("/").split("/") if a in titles]
              for pid, path in paths.items()}

    parents = {pid: parent for pid, parent
               in db.execute("SELECT id, parent_id FROM provisions")
               if pid in wanted_provisions and parent}

    # One streaming pass for the ancestors' text. `versions.jsonl` is ~1 GB, so
    # it is read once and only the handful of parents the candidates name is
    # kept.
    wanted_parents = set(parents.values())
    parent_versions: dict[str, list[tuple[str, str | None, str]]] = collections.defaultdict(list)
    for line in (data / "derived/versions.jsonl").open(encoding="utf-8"):
        if '"provision_id": "' not in line:
            continue
        version = json.loads(line)
        if version["provision_id"] in wanted_parents and version["effective_from"]:
            parent_versions[version["provision_id"]].append(
                (version["effective_from"], version["effective_to"], version["text"]))

    lead_ins: dict[tuple[str, str], str] = {}
    for row in rows:
        parent = parents.get(row["provision_id"])
        for gold in row["gold"]:
            at = gold["as_of"]
            for start, end, text in parent_versions.get(parent, ()):
                if start <= at and (end is None or at < end):
                    lead_ins[(parent, at)] = text
                    break

    questions_path = data / "derived/vilextime/questions.jsonl"
    questions: dict[str, dict] = {}
    if questions_path.exists():
        for line in questions_path.open(encoding="utf-8"):
            generated = json.loads(line)
            if generated["question"]:            # a C2 rejection keeps the template
                questions[generated["lineage_id"]] = generated

    out_dir = data / "derived/vilextime"
    out_dir.mkdir(parents=True, exist_ok=True)
    written: collections.Counter[str] = collections.Counter()
    by_group: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        for record in records_of(row, documents, chains, parents, lead_ins, questions):
            by_group[row["group"]].append(record)

    for group in sorted(by_group):
        path = out_dir / f"{group}.jsonl"
        with path.open("w", encoding="utf-8") as out:
            for record in sorted(by_group[group], key=lambda r: r["id"]):
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
        written[group] = len(by_group[group])
        print(f"  {group}: {len(by_group[group]):,} câu từ "
              f"{sum(1 for r in rows if r['group'] == group):,} điều khoản -> {path}")

    llm = sum(1 for rs in by_group.values() for r in rs if r["question_source"]["kind"] == "llm")
    total = sum(written.values())
    print(f"\n{total:,} câu hỏi, schema {SCHEMA_VERSION} (ADR 0003)")
    print(f"  câu hỏi do model sinh: {llm:,}/{total:,}"
          + ("" if llm else "  (chạy generate_questions.py để thay khuôn máy)"))
    print("  `split` còn null: P4.9 chia theo lineage_id/document_id")


if __name__ == "__main__":
    main()
