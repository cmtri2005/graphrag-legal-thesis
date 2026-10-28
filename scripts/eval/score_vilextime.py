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
  wrong_version answerable rows whose lineage has another version with spans of its own:
                the answer contains one of those spans. Version confusion read from the
                text, so it is defined for a system that cites in writing (B1), where VCR
                is not (decided 11/10, B5)
  TCS           T2 pairs (same lineage, same as_of_strategy): Accuracy on both
                (formula 8); tcs_lenient uses accuracy_lenient

`--ci DRAWS` adds a 95% percentile interval to each headline metric, resampling whole
lineages: the rows of a lineage share their question and evidence, so resampling rows
would overstate the precision (datasheet §4). Given several prediction files, each is
also compared with the one before it: the difference of each metric, and its interval
over the same resamples, so the comparison is paired.

Every metric is reported per `as_of_strategy` (giua_khoang is the main table,
ranh_gioi the boundary test) and per group. "all" leaves out the diagnostic groups
(DIAGNOSTIC): T5 is 19 lineages from 3 amending documents, so it is reported on its
own row and never averaged in (decided 11/10). Only `test` is scored by default
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
    python scripts/eval/score_vilextime.py predictions.jsonl [more.jsonl ...] [--split test] [--ids ids.txt]
        [--ci 2000] [--out report.json]
    python scripts/eval/score_vilextime.py --probes
"""
from __future__ import annotations

import argparse
import collections
import json
import operator
import random
import re
import sqlite3
import statistics
import unicodedata
import zlib
from datetime import date
from pathlib import Path

KS = (1, 5, 10)
PROBES = ("oracle", "latest", "first", "nearest", "hedge", "no_cite", "text_cite")
UNIT_PREFIXES = ("version:", "asis:")
ANY_VERSION = "any"      # what a written citation stands for: the provision, no version
HEADLINE = ("recall@1", "tv_recall@1", "mrr", "accuracy", "accuracy_lenient", "f1", "tver", "tver_strict",
            "vcr", "citation_coverage", "wrong_version", "tcs")


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


def load_rows(path: Path) -> list[dict]:
    """Load an internal release or join a published release to its companion metadata."""
    rows = [json.loads(line) for line in path.open(encoding="utf-8")]
    if not rows or "context" not in rows[0]:
        return rows
    meta_path = path.with_name("vilextime_meta.jsonl")
    metadata = {m["id"]: m for m in map(json.loads, meta_path.open(encoding="utf-8"))}
    if not {r["id"] for r in rows} <= set(metadata):
        raise ValueError("published release has IDs missing from vilextime_meta.jsonl")
    for r in rows:
        m = metadata[r["id"]]
        r["short_answer"], r["answer"] = r["answer"], r["context"]
        r["target"] = m["target"]
        r["near_identical"] = m.get("near_identical")
        r["repeal_mode"] = m.get("repeal_mode")
    return rows


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
    if row["answerable"] and row.get("_distractors"):
        said = f" {norm(pred.get('answer') if pred.get('answerable') is not False else '')} "
        out["wrong_version"] = float(any(f" {s} " in said for s in row["_distractors"]))
    else:
        out["wrong_version"] = None
    versioned = [s for s in stands if s is None or any(n != ANY_VERSION for _, n, _ in s)]
    if versioned:
        mine = {(p, n) for s in versioned if s for p, n, _ in s if p == gold_p}
        out["vcr"] = float(bool(mine) and (gold_p, gold_n) not in mine)
    else:
        out["vcr"] = None
    return out


def pairs(rows: list[dict]) -> dict[tuple[str, str], list[str]]:
    """T2 pairs: (lineage, as_of_strategy) -> the ids of its two dates (formula 8)."""
    out = collections.defaultdict(list)
    for r in rows:
        if r["group"] == "T2":
            out[(r["lineage_id"], r["as_of_strategy"])].append(r["id"])
    return {key: ids for key, ids in out.items() if len(ids) == 2}


def score(rows: list[dict], preds: dict[str, dict], units: dict, ks=KS, draws: int = 0, seed: int = 0) -> dict:
    """Mean of each metric over the rows in its denominator, plus TCS over T2 pairs and the counts.

    With `draws`, also each headline metric's 95% interval (`ci95`) and the resamples
    behind it (`_draws`, for `difference`).
    """
    per_row = {r["id"]: row_scores(r, preds.get(r["id"], {}), units, ks) for r in rows}
    out: dict = {"rows": len(rows), "cited_rows": sum(s["tver"] is not None for s in per_row.values()),
                 "contrast_rows": sum(bool(r.get("_distractors")) for r in rows)}
    for metric in next(iter(per_row.values()), {}):
        values = [s[metric] for s in per_row.values() if s[metric] is not None]
        out[metric] = sum(values) / len(values) if values else None
    both = list(pairs(rows).values())
    for name, metric in (("tcs", "accuracy"), ("tcs_lenient", "accuracy_lenient")):
        out[name] = sum(all(per_row[i][metric] for i in ids) for ids in both) / len(both) if both else None
    out["tcs_pairs"] = len(both)
    if draws:
        out["_draws"] = bootstrap(rows, per_row, draws, seed)
        out["ci95"] = {m: interval([d[m] for d in out["_draws"] if d[m] is not None]) for m in HEADLINE}
    return out


def bootstrap(rows: list[dict], per_row: dict[str, dict], draws: int, seed: int = 0) -> list[dict]:
    """Each headline metric on `draws` resamples of whole lineages, drawn with replacement.

    Seeded, and drawn over the sorted lineages of `rows` alone: two systems scored on the
    same rows see the same resamples, so their difference is paired.
    """
    lineages = sorted({r["lineage_id"] for r in rows})
    at = {lineage: i for i, lineage in enumerate(lineages)}
    sums = {m: ([0.0] * len(lineages), [0] * len(lineages)) for m in HEADLINE}   # per lineage: sum, count
    for r in rows:
        for m, v in per_row[r["id"]].items():
            if m in sums and v is not None:
                sums[m][0][at[r["lineage_id"]]] += v
                sums[m][1][at[r["lineage_id"]]] += 1
    for (lineage, _), ids in pairs(rows).items():
        sums["tcs"][0][at[lineage]] += all(per_row[i]["accuracy"] for i in ids)
        sums["tcs"][1][at[lineage]] += 1
    rng, out = random.Random(seed), []
    for _ in range(draws):
        weight = [0] * len(lineages)
        for i in rng.choices(range(len(lineages)), k=len(lineages)):
            weight[i] += 1
        draw = {}
        for m, (total, count) in sums.items():
            n = sum(map(operator.mul, weight, count))
            draw[m] = sum(map(operator.mul, weight, total)) / n if n else None
        out.append(draw)
    return out


def interval(values: list[float]) -> list[float] | None:
    """The 2.5th and 97.5th percentiles."""
    if len(values) < 2:
        return None
    q = statistics.quantiles(values, n=40, method="inclusive")
    return [q[0], q[-1]]


def difference(base: dict, other: dict) -> dict:
    """other − base on each headline metric: the interval of the paired resamples, and the
    two-sided bootstrap p (twice the share of resamples on the far side of 0), for Holm."""
    out: dict = {"ci95": {}, "p": {}}
    for m in HEADLINE:
        both = base[m] is not None and other[m] is not None
        out[m] = other[m] - base[m] if both else None
        d = [o[m] - b[m] for b, o in zip(base["_draws"], other["_draws"]) if b[m] is not None and o[m] is not None]
        out["ci95"][m] = interval(d) if both else None
        out["p"][m] = min(1.0, 2 * min(sum(x <= 0 for x in d), sum(x >= 0 for x in d)) / len(d)) if both and d else None
    return out


DIAGNOSTIC = ("T5",)   # named diagnostic sets: scored per group, never in "all"


def default_split(rows: list[dict]) -> str | None:
    """`test` once the release is split (ADR 0003 §7: only test is seen by default); before that, everything."""
    return "test" if any(r.get("split") for r in rows) else None


def report(rows: list[dict], preds: dict[str, dict], units: dict, split: str | None, ks=KS,
           draws: int = 0) -> dict:
    """Every metric per as_of_strategy and per group. Each (strategy, group) draws from its own
    seed: the same cell of two systems is paired, two cells are independent samples, so a
    difference between groups (H2) is a two-sample comparison."""
    rows = [r for r in rows if r.get("split") != "excluded" and (split is None or r.get("split") == split)]
    seed = lambda strategy, group: zlib.crc32(f"{strategy}/{group}".encode())  # noqa: E731
    out = {}
    for strategy in sorted({r["as_of_strategy"] for r in rows}):
        these = [r for r in rows if r["as_of_strategy"] == strategy]
        out[strategy] = {"all": score([r for r in these if r["group"] not in DIAGNOSTIC], preds, units, ks,
                                      draws, seed(strategy, "all"))}
        for group in sorted({r["group"] for r in these}):
            out[strategy][group] = score([r for r in these if r["group"] == group], preds, units, ks,
                                         draws, seed(strategy, group))
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


def units_of(data: Path, runs: dict[str, dict[str, dict]]) -> tuple[dict, set[str], set[str]]:
    """What every unit id and written citation of these runs stands for (`resolve`), and the
    unit ids and written citations themselves. Read once for all runs: it scans ~1 GB."""
    cited = {u for preds in runs.values() for p in preds.values()
             for u in (p.get("citations") or []) + (p.get("retrieved") or [])}
    ids = {u for u in cited if u.startswith(UNIT_PREFIXES)}
    texts = cited - ids
    written = {}
    if texts:
        documents, trees = citation_index(data, texts)
        written = {t: pid for t in texts if (pid := resolve_written(t, documents, trees))}
    return resolve(data, ids, written), ids, texts


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
    heads = ("R@1", "TV-R@1", "MRR", "Acc", "Acc(lỏng)", "F1", "TVER", "TVER(ng)", "VCR", "phủ tr.d",
             "sai b.bản", "TCS")
    fmt = lambda x: "—" if x is None else f"{x:.3f}"
    span = lambda iv: "—" if iv is None else f"{iv[0]:.2f}…{iv[1]:.2f}"
    lines = [title, f"{'':<34}" + "".join(f"{h:>12}" for h in heads)]
    for name, rep in results.items():
        for strategy, groups in rep.items():
            row = groups["all"]
            lines.append(f"{name + ' · ' + strategy:<34}" + "".join(f"{fmt(row[c]):>12}" for c in HEADLINE))
            if "ci95" in row:
                lines.append(f"{'  95%':<34}" + "".join(f"{span(row['ci95'][c]):>12}" for c in HEADLINE))
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predictions", type=Path, nargs="*")
    ap.add_argument("--probes", action="store_true", help="score the version-choice and scorer-check probes")
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--split", help="score only this split (default: test, or every row before the split)")
    ap.add_argument("--ids", type=Path, help="score only the row ids listed in this file, one per line")
    ap.add_argument("--out", type=Path, help="write the full report (per strategy and group) as JSON")
    ap.add_argument("--release", type=Path, help="score against a published vilextime.jsonl (export_release.py) "
                                                 "instead of <data>/derived/vilextime/release.jsonl")
    ap.add_argument("--ci", type=int, default=0, metavar="DRAWS",
                    help="95%% intervals from DRAWS lineage resamples; several prediction files are "
                         "also compared, each with the one before it")
    args = ap.parse_args()
    if bool(args.predictions) == args.probes:
        ap.error("give prediction files or --probes")
    if len({p.stem for p in args.predictions}) < len(args.predictions):
        ap.error("prediction files are named by their stem, so the stems must differ")
    path = args.release or args.data / "derived/vilextime/release.jsonl"
    rows = load_rows(path)
    if args.probes and "target" not in rows[0]:
        ap.error("--probes needs the internal release (it reads `target`)")
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
        runs = {path.stem: {p["id"]: p for p in map(json.loads, path.open(encoding="utf-8"))}
                for path in args.predictions}
    units, ids, texts = units_of(args.data, runs)
    results = {name: report(rows, preds, units, split, draws=args.ci) for name, preds in runs.items()}
    if args.ci and args.predictions:
        names = list(results)
        for base, other in zip(names, names[1:]):
            results[f"{other} − {base}"] = {s: {g: difference(results[base][s][g], results[other][s][g])
                                               for g in results[base][s]} for s in results[base]}
    for rep in results.values():
        for groups in rep.values():
            for scores in groups.values():
                scores.pop("_draws", None)
    print(table(f"ViLexTime · {len(rows):,} dòng · split {split or 'tất cả (chưa chia)'} · "
                f"{len(ids - units.keys())} mã đơn vị không có trong corpus · "
                f"{len(texts - units.keys())}/{len(texts)} trích dẫn chữ không phân giải được", results))
    if args.out:
        args.out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
