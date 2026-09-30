#!/usr/bin/env python3
"""ViLexTime — the official scorer, and the version-choice probes (plan phase-4, V7, J1).

A submission is JSONL, one line per release row it answers:

    {"id": "<row id>", "answer": "...", "answerable": true,
     "citations": ["<unit id or a written citation>", ...],   # what the answer cites
     "retrieved": ["<unit id>", ...]}                         # ranked, best first

Unit ids are the corpus's (build_corpus.py): layer B `version:<provision>:<n>`;
layer A `asis:provision:<id>` (the original wording, i.e. version 1) and
`asis:event:<id>` (an amending instruction stands for the versions it wrote; a
repeal for the repeal itself, in force from the day it takes effect). A citation
that is not a unit id is a written one ("Điểm s Khoản 3 Điều 16 Nghị định
109/2026/NĐ-CP"), resolved to the provision by its document number and its
Điều/Khoản/Điểm; it names no version. A row the submission has no line for
scores as an empty answer.

Metrics: the proposal's evaluation framework and its formulas 6–9, with the
choices it leaves open decided 28/09 and revised 29/09 after the independent
review (CMT, plan phase-4 V7 and J1). E* is the gold unit alone, the row's
provision, so |E*| = 1:

  Recall@k      a top-k unit is that provision (any version) or in accepted_evidence
  MRR           1 / rank of the first such unit
  TV-Recall@k   a top-k unit is the version in force at as_of or in accepted_evidence;
                for a repealed provision that is the repeal instruction. Formula 9 as
                written (u ∈ E* ∧ valid(u, t)) equals Recall@k, since every gold unit is
                valid at t; this version-exact reading is the official one
  Accuracy      answerable row: the normalised answer contains every span of
                short_answer (" … " separates spans), contains no span that only
                another version's short_answer has (so an answer that recites every
                version is wrong), and answerable is not false;
                unanswerable row: answerable is false
  accuracy_lenient  the 28/09 definition: the first condition alone
  EM / F1       against short_answer (spans joined), syllable tokens, answerable rows
                only. EM is near zero for any generated sentence; report F1
  TVER          rows with a resolved citation: one of them is not in force at as_of
                (formula 6). A unit id the corpus does not have is not in force; a
                written citation that does not resolve is left out here; a unit of
                the row's accepted_evidence is never an error
  tver_strict   every row: no citation, an unresolved one, or TVER — an error
  VCR           rows with a versioned citation: it cites the gold provision but never
                at the gold version; for a repealed provision every version is wrong
                (formula 7). A written citation names no version, so a row citing
                only in writing has no VCR
  citation_coverage  rows with at least one resolved citation
  TCS           T2 pairs (same lineage, same as_of_strategy): Accuracy on both
                (formula 8); tcs_lenient uses accuracy_lenient

Every metric is reported per `as_of_strategy` (giua_khoang is the main table,
ranh_gioi the boundary test) and per group. Only `test` is scored by default
(ADR 0003 §7); until the release is split, every row is, and the header says so.
Rows whose split is "excluded" are never scored.

`--probes` scores systems that are handed the gold provision and only choose its
version: oracle (in force at as_of), latest, first, and nearest (the version whose
start is closest to as_of, either side). Each answers with the row's lead-in and
the chosen version's text, cites and retrieves that version, and never abstains,
except oracle on a repealed provision, which abstains and cites the repeal
instruction. Three more check the scorer itself: hedge (recites every version),
no_cite (oracle without citations), text_cite (oracle citing in writing).

Usage:
    python scripts/eval/score_vilextime.py predictions.jsonl [--split test] [--ids ids.txt] [--out report.json]
    python scripts/eval/score_vilextime.py --probes
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
import unicodedata
from datetime import date
from pathlib import Path

KS = (1, 5, 10)
PROBES = ("oracle", "latest", "first", "nearest", "hedge", "no_cite", "text_cite")
UNIT_PREFIXES = ("version:", "asis:")
ANY_VERSION = "any"      # what a written citation stands for: the provision, no version


def norm(text: str | None) -> str:
    """Lowercase, punctuation to spaces, one space between syllables; diacritics kept."""
    text = unicodedata.normalize("NFC", text or "").lower()
    text = "".join(" " if unicodedata.category(ch).startswith("P") else ch for ch in text)
    return " ".join(text.split())


def spans(short_answer: str) -> list[str]:
    return [s for s in (norm(part) for part in short_answer.split("…")) if s]


def contains(answer: str, short_answer: str) -> bool:
    padded = f" {norm(answer)} "
    return all(f" {s} " in padded for s in spans(short_answer))


def distractors(rows: list[dict]) -> dict[str, list[str]]:
    """Row id -> the spans only another version of its lineage has (not in this row's gold text)."""
    shorts = collections.defaultdict(dict)
    for r in rows:
        if r["version_id"] and r.get("short_answer"):
            shorts[r["lineage_id"]][r["version_id"]] = r["short_answer"]
    out = {}
    for r in rows:
        if not r["answerable"]:
            continue
        gold = f" {norm((r['target'].get('lead_in') or '') + ' ' + (r['answer'] or ''))} "
        out[r["id"]] = sorted({s for v, short in shorts[r["lineage_id"]].items() if v != r["version_id"]
                               for s in spans(short) if f" {s} " not in gold})
    return out


def f1(answer: str, gold: str) -> float:
    pred, ref = norm(answer).split(), gold.split()
    common = sum((collections.Counter(pred) & collections.Counter(ref)).values())
    if not common:
        return 0.0
    p, r = common / len(pred), common / len(ref)
    return 2 * p * r / (p + r)


def in_force(intervals: list[tuple[str, str | None]], when: str) -> bool:
    return any(start <= when and (end is None or when < end) for start, end in intervals)


def ordinal(version_id: str | None) -> int | None:
    return int(version_id.rsplit(":", 1)[1]) if version_id else None


def correct(row: dict, pred: dict, lenient: bool = False) -> bool:
    if not row["answerable"]:
        return pred.get("answerable") is False
    answer = pred.get("answer") or ""
    if pred.get("answerable") is False or not contains(answer, row["short_answer"] or ""):
        return False
    padded = f" {norm(answer)} "
    return lenient or not any(f" {s} " in padded for s in row.get("_distractors", ()))


def row_scores(row: dict, pred: dict, units: dict, ks=KS) -> dict:
    """One row's contribution to every metric; None where the row is outside that metric's denominator.

    `units` maps a unit id — or a written citation — to what it stands for:
    [(provision, ordinal, None for a repeal or ANY_VERSION for a written citation,
    [(start, end or None)])]. A unit id missing from it is not in the corpus; a
    written citation missing from it did not resolve.
    """
    gold_p, gold_n = row["lineage_id"], ordinal(row["version_id"])
    accepted = set(row["accepted_evidence"])
    retrieved = pred.get("retrieved") or []
    hit = [u in accepted or any(p == gold_p for p, _, _ in units.get(u, ())) for u in retrieved]
    tv_hit = [u in accepted or (u == row["version_id"] and row["version_id"] is not None) for u in retrieved]
    first = next((i for i, h in enumerate(hit, 1) if h), None)
    out = {"accuracy": float(correct(row, pred)), "accuracy_lenient": float(correct(row, pred, lenient=True)),
           "mrr": 1 / first if first else 0.0}
    for k in ks:
        out[f"recall@{k}"] = float(any(hit[:k]))
        out[f"tv_recall@{k}"] = float(any(tv_hit[:k]))
    if row["answerable"]:
        gold = " ".join(spans(row["short_answer"] or ""))
        said = (pred.get("answer") or "") if pred.get("answerable") is not False else ""
        out["em"], out["f1"] = float(norm(said) == gold), f1(said, gold)
    else:
        out["em"] = out["f1"] = None
    cites = pred.get("citations") or []
    unit_cites = [u for u in cites if u.startswith(UNIT_PREFIXES)]
    written = [c for c in cites if not c.startswith(UNIT_PREFIXES)]
    stands = [units.get(u) for u in unit_cites] + [units[c] for c in written if c in units]
    unresolved = any(c not in units for c in written)
    if stands:
        # a unit of the row's accepted_evidence is right by definition, even when it has
        # itself ended since (the sentence that ended a document, in a document later replaced)
        dead = [u not in accepted and (s is None or not any(in_force(iv, row["as_of"]) for _, _, iv in s))
                for u, s in zip(unit_cites + [c for c in written if c in units], stands)]
        out["tver"] = float(any(dead))
    else:
        out["tver"] = None
    out["tver_strict"] = float(not cites or unresolved or bool(out["tver"]))
    out["citation_coverage"] = float(any(s is not None for s in stands))
    versioned = [s for s in stands if s is None or any(n != ANY_VERSION for _, n, _ in s)]
    if versioned:
        mine = {(p, n) for s in versioned if s for p, n, _ in s if p == gold_p}
        out["vcr"] = float(bool(mine) and (gold_p, gold_n) not in mine)
    else:
        out["vcr"] = None
    return out


def score(rows: list[dict], preds: dict[str, dict], units: dict, ks=KS) -> dict:
    """Mean of each metric over the rows in its denominator, plus TCS over T2 pairs and the counts."""
    per_row = {r["id"]: row_scores(r, preds.get(r["id"], {}), units, ks) for r in rows}
    out: dict = {"rows": len(rows), "cited_rows": sum(s["tver"] is not None for s in per_row.values()),
                 "contrast_rows": sum(bool(r.get("_distractors")) for r in rows)}
    for metric in next(iter(per_row.values()), {}):
        values = [s[metric] for s in per_row.values() if s[metric] is not None]
        out[metric] = sum(values) / len(values) if values else None
    pairs = collections.defaultdict(list)
    for r in rows:
        if r["group"] == "T2":
            pairs[(r["lineage_id"], r["as_of_strategy"])].append(r["id"])
    both = [ids for ids in pairs.values() if len(ids) == 2]
    for name, metric in (("tcs", "accuracy"), ("tcs_lenient", "accuracy_lenient")):
        out[name] = sum(all(per_row[i][metric] for i in ids) for ids in both) / len(both) if both else None
    out["tcs_pairs"] = len(both)
    return out


def default_split(rows: list[dict]) -> str | None:
    """`test` once the release is split (ADR 0003 §7: only test is seen by default); before that, everything."""
    return "test" if any(r.get("split") for r in rows) else None


def report(rows: list[dict], preds: dict[str, dict], units: dict, split: str | None, ks=KS) -> dict:
    rows = [r for r in rows if r.get("split") != "excluded" and (split is None or r.get("split") == split)]
    out = {}
    for strategy in sorted({r["as_of_strategy"] for r in rows}):
        these = [r for r in rows if r["as_of_strategy"] == strategy]
        out[strategy] = {"all": score(these, preds, units, ks)}
        for group in sorted({r["group"] for r in these}):
            out[strategy][group] = score([r for r in these if r["group"] == group], preds, units, ks)
    return out


# ------------------------------------------------------------------ written citations

_NUMBER = re.compile(r"\b\d+[a-zđ]?(?:\s?/\s?[\wĐđÐ]+|-[\wĐđÐ]+)+", re.IGNORECASE)   # "08 /2024/TT-BTNMT"
_PART = re.compile(r"\b(điều|khoản|điểm)\s+([0-9]+[a-zđ]?|[a-zđ][0-9]?)(?![\w/])", re.IGNORECASE)
_YEAR = re.compile(r"\b(1[89]\d\d|20\d\d)\b")
_LEVEL = {"điều": "Article", "khoản": "Clause", "điểm": "Point"}
_TITLE = re.compile(r"^(?:Điều|Khoản|Điểm)\s+(\S+?)[.:]?$")


def number_key(number: str) -> str:
    """"81-CP", "81/CP" and "81 / cp" are one number; "NĐ-CP" and "NĐ/CP" too."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", number).upper().replace("Ð", "Đ").replace("-", "/"))


def parse_citation(text: str) -> tuple[str | None, dict[str, str], set[str]]:
    """(number key, {level: label}, years named outside the number) of a written citation."""
    numbers = [m.group(0) for m in _NUMBER.finditer(text) if re.search(r"[^\W\d_]", m.group(0))]
    number = number_key(numbers[0]) if numbers else None
    parts: dict[str, str] = {}
    for word, label in _PART.findall(text):
        parts.setdefault(_LEVEL[word.lower()], label.lower())
    rest = _NUMBER.sub(" ", text)
    return number, parts, set(_YEAR.findall(rest))


def resolve_written(text: str, documents: dict[str, list[tuple[str, str | None]]],
                    trees: dict[str, list[tuple[str, str | None, str, str]]]) -> list[str] | None:
    """The provision a written citation names, or None when it names none or more than one.

    `documents` maps a number key to [(document id, issued_on)]; `trees` maps a
    document id to its provisions [(id, parent id, level, label)]. A number shared
    by several documents (40/CP of 1994 and of 1996) needs a year in the citation
    or a path only one of them has. The portal keeps some laws twice (19/2012/QH13:
    same number, same day); a citation of one names the provision in every copy.
    """
    number, parts, years = parse_citation(text)
    if not number or "Article" not in parts:
        return None
    candidates = documents.get(number, [])
    if years:
        candidates = [(d, issued) for d, issued in candidates if issued and issued[:4] in years]
    found, days = [], set()
    for doc, issued in candidates:
        nodes = trees.get(doc, [])
        layer = {pid for pid, _, level, label in nodes if level == "Article" and label == parts["Article"]}
        for level in ("Clause", "Point"):
            if level in parts:
                layer = {pid for pid, parent, lv, label in nodes
                         if lv == level and label == parts[level] and parent in layer}
        if len(layer) > 1:
            return None
        if layer:
            found += layer
            days.add(issued)
    return sorted(found) if found and len(days) == 1 else None


def citation_index(data: Path, texts: set[str]) -> tuple[dict, dict]:
    """The documents and provision trees the written citations can name — corpus documents only."""
    keys = {parse_citation(t)[0] for t in texts} - {None}
    documents = collections.defaultdict(list)
    for line in (data / "derived/corpus/documents.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if (k := number_key(d["law_id"] or "")) in keys:
            documents[k].append((d["document_id"], d["issued_on"]))
    trees = collections.defaultdict(list)
    db = sqlite3.connect(f"file:{data / 'temporal.sqlite'}?mode=ro", uri=True)
    for doc in {d for docs in documents.values() for d, _ in docs}:
        for pid, parent, level, title in db.execute(
                "SELECT id, parent_id, level, title FROM provisions WHERE document_id = ?", (doc,)):
            if level in ("Article", "Clause", "Point") and (m := _TITLE.match(title)):
                trees[doc].append((pid, parent, level, m.group(1).lower()))
    return documents, trees


# ------------------------------------------------------------------ units

def _field(line: str, key: str) -> str | None:
    """A string field of a compact JSON line, without parsing the ~1 KB of text around it."""
    i = line.find(f'"{key}":"')
    if i < 0:
        return None
    i += len(key) + 4
    return line[i:line.index('"', i)]


def versions(data: Path, provisions: set[str], events: set[str]) -> list[dict]:
    """Versions of these provisions, and those the events created or ended (derived/versions.jsonl, ~1 GB)."""
    out = []
    for line in (data / "derived/versions.jsonl").open(encoding="utf-8"):
        if (_field(line, "provision_id") in provisions or _field(line, "created_by_event_id") in events
                or _field(line, "ended_by_event_id") in events):
            out.append(json.loads(line))
    return out


def resolve(data: Path, ids: set[str], written: dict[str, list[str]] | None = None) -> dict:
    """Unit id or written citation -> [(provision, ordinal / None for a repeal / ANY_VERSION, intervals)].

    `written` maps a written citation to the provision(s) it resolved to; it stands
    for every version of them, so it is in force whenever one is.
    """
    written = written or {}
    events = {u.removeprefix("asis:") for u in ids if u.startswith("asis:event:")}
    provisions = {"provision:" + u.split(":", 1)[1].rsplit(":", 1)[0] for u in ids if u.startswith("version:")}
    provisions |= {u.removeprefix("asis:") for u in ids if u.startswith("asis:provision:")}
    provisions |= {pid for pids in written.values() for pid in pids}
    out: dict[str, list] = collections.defaultdict(list)
    created, ended = collections.defaultdict(dict), collections.defaultdict(dict)
    by_provision = collections.defaultdict(list)
    for v in versions(data, provisions, events):
        iv = [(i["start"], i["end"]) for i in v["effective_intervals"]]
        n, pid, maker = int(v["ordinal"]), v["provision_id"], v.get("created_by_event_id")
        by_provision[pid].append((pid, ANY_VERSION, iv))
        if v["id"] in ids:
            out[v["id"]].append((pid, n, iv))
        if n == 1 and not maker and f"asis:{pid}" in ids:     # layer A keeps only original wording
            out[f"asis:{pid}"].append((pid, n, iv))
        if maker in events:
            created[maker][pid] = (pid, n, iv)
        if v.get("ended_by_event_id") in events:
            end = max((e for _, e in iv if e), default=None)
            if end:
                ended[v["ended_by_event_id"]][pid] = (pid, None, [(end, None)])
    for e in events:
        out[f"asis:{e}"] += list({**ended[e], **created[e]}.values())   # an amendment ends one version, writes the next
    for text, pids in written.items():
        out[text] = [u for pid in pids for u in by_provision[pid]]
    return {u: s for u, s in out.items() if s}


# ------------------------------------------------------------------ probes

def nearest(chain: list[dict], when: str) -> dict:
    day = date.fromisoformat(when)
    gap = lambda v: min((abs((date.fromisoformat(i["start"]) - day).days) for i in v["effective_intervals"]),
                        default=10**6)
    return min(chain, key=lambda v: (gap(v), -int(v["ordinal"])))


def probe(name: str, rows: list[dict], chains: dict[str, list[dict]]) -> dict[str, dict]:
    """Predictions of a system that knows the gold provision and picks its version by one rule."""
    preds = {}
    for r in rows:
        chain = sorted(chains.get(r["lineage_id"], []), key=lambda v: int(v["ordinal"]))
        if not chain:
            continue
        t = r["target"]
        written = f"{t.get('citation') or ''} {t.get('doc_type') or ''} {t.get('law_id') or ''}".strip()
        if name in ("oracle", "no_cite", "text_cite") and not r["answerable"]:
            cites = {"oracle": r["accepted_evidence"], "no_cite": [], "text_cite": [written]}[name]
            preds[r["id"]] = {"answerable": False, "citations": cites, "retrieved": r["accepted_evidence"]}
            continue
        lead = t.get("lead_in") or ""
        if name == "hedge":
            ids = [v["id"] for v in chain]
            preds[r["id"]] = {"answer": "\n".join([lead] + [v["text"] for v in chain]).strip(),
                              "answerable": True, "citations": ids, "retrieved": ids}
            continue
        pick = {"latest": lambda: chain[-1], "first": lambda: chain[0],
                "nearest": lambda: nearest(chain, r["as_of"])}.get(
            name, lambda: next(v for v in chain if v["id"] == r["version_id"]))()
        cites = {"no_cite": [], "text_cite": [written]}.get(name, [pick["id"]])
        preds[r["id"]] = {"answer": f"{lead}\n{pick['text']}".strip(), "answerable": True,
                          "citations": cites, "retrieved": [pick["id"]]}
    return preds


def table(title: str, results: dict[str, dict]) -> str:
    cols = ("recall@1", "tv_recall@1", "mrr", "accuracy", "accuracy_lenient", "f1", "tver", "tver_strict",
            "vcr", "citation_coverage", "tcs")
    heads = ("R@1", "TV-R@1", "MRR", "Acc", "Acc(lỏng)", "F1", "TVER", "TVER(ng)", "VCR", "phủ tr.d", "TCS")
    fmt = lambda x: "   —  " if x is None else f"{x:6.3f}"
    lines = [title, f"{'':<26}" + "".join(f"{h:>10}" for h in heads)]
    for name, rep in results.items():
        for strategy, groups in rep.items():
            lines.append(f"{name + ' · ' + strategy:<26}" + "".join(f"{fmt(groups['all'][c]):>10}" for c in cols))
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predictions", type=Path, nargs="?")
    ap.add_argument("--probes", action="store_true", help="score the version-choice and scorer-check probes")
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--split", help="score only this split (default: test, or every row before the split)")
    ap.add_argument("--ids", type=Path, help="score only the row ids listed in this file, one per line")
    ap.add_argument("--out", type=Path, help="write the full report (per strategy and group) as JSON")
    args = ap.parse_args()
    if bool(args.predictions) == args.probes:
        ap.error("give a predictions file or --probes")
    rows = [json.loads(line) for line in (args.data / "derived/vilextime/release.jsonl").open(encoding="utf-8")]
    extra = distractors(rows)
    for r in rows:
        r["_distractors"] = extra.get(r["id"], [])
    split = args.split or default_split(rows)
    if args.ids:
        wanted = set(args.ids.read_text(encoding="utf-8").split())
        rows = [r for r in rows if r["id"] in wanted]

    if args.probes:
        gold = {r["lineage_id"] for r in rows}
        chains = collections.defaultdict(list)
        for v in versions(args.data, gold, set()):
            chains[v["provision_id"]].append(v)
        runs = {name: probe(name, rows, chains) for name in PROBES}
    else:
        runs = {args.predictions.stem: {p["id"]: p for p in map(json.loads, args.predictions.open(encoding="utf-8"))}}
    cited = {u for preds in runs.values() for p in preds.values() for u in (p.get("citations") or []) + (p.get("retrieved") or [])}
    ids = {u for u in cited if u.startswith(UNIT_PREFIXES)}
    texts = cited - ids
    written = {}
    if texts:
        documents, trees = citation_index(args.data, texts)
        written = {t: pid for t in texts if (pid := resolve_written(t, documents, trees))}
    units = resolve(args.data, ids, written)
    results = {name: report(rows, preds, units, split) for name, preds in runs.items()}
    print(table(f"ViLexTime · {len(rows):,} dòng · split {split or 'tất cả (chưa chia)'} · "
                f"{len(ids - units.keys())} mã đơn vị không có trong corpus · "
                f"{len(texts) - len(written)}/{len(texts)} trích dẫn chữ không phân giải được", results))
    if args.out:
        args.out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
