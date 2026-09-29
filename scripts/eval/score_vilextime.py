#!/usr/bin/env python3
"""ViLexTime — the official scorer, and the version-choice probes (plan phase-4, V7).

A submission is JSONL, one line per release row it answers:

    {"id": "<row id>", "answer": "...", "answerable": true,
     "citations": ["<unit id>", ...],       # what the answer cites
     "retrieved": ["<unit id>", ...]}       # ranked, best first

Unit ids are the corpus's (build_corpus.py): layer B `version:<provision>:<n>`;
layer A `asis:provision:<id>` (the original wording, i.e. version 1) and
`asis:event:<id>` (an amending instruction stands for the versions it wrote; a
repeal for the repeal itself, in force from the day it takes effect). A row the
submission has no line for scores as an empty answer.

Metrics: the proposal's evaluation framework and its formulas 6–9, with the
choices it leaves open decided 28/09 (CMT, plan phase-4 V7). E* is the gold unit
alone, the row's provision, so |E*| = 1:

  Recall@k      a top-k unit is that provision (any version) or in accepted_evidence
  MRR           1 / rank of the first such unit
  TV-Recall@k   a top-k unit is the version in force at as_of or in accepted_evidence;
                for a repealed provision that is the repeal instruction (formula 9)
  Accuracy      answerable row: the normalised answer contains every span of
                short_answer (" … " separates spans) and answerable is not false;
                unanswerable row: answerable is false
  EM / F1       against short_answer (spans joined), syllable tokens, answerable rows only
  TVER          rows with a citation: one of them is not in force at as_of; a unit the
                corpus does not have is not in force (formula 6)
  VCR           rows with a citation: it cites the gold provision but never at the gold
                version; for a repealed provision every version is wrong (formula 7)
  TCS           T2 pairs (same lineage, same as_of_strategy): Accuracy on both (formula 8)

Every metric is reported per `as_of_strategy` (giua_khoang is the main table,
ranh_gioi the boundary test) and per group. Only `test` is scored by default
(ADR 0003 §7); until the release is split, every row is, and the header says so.
Rows whose split is "excluded" are never scored.

`--probes` scores four systems that are handed the gold provision and only
choose its version: oracle (in force at as_of), latest, first, and nearest (the
version whose start is closest to as_of, either side). Each answers with the
row's lead-in and the chosen version's text, cites and retrieves that version,
and never abstains, except oracle on a repealed provision, which abstains and
cites the repeal instruction.

Usage:
    python scripts/eval/score_vilextime.py predictions.jsonl [--split test] [--out report.json]
    python scripts/eval/score_vilextime.py --probes
"""
from __future__ import annotations

import argparse
import collections
import json
import unicodedata
from datetime import date
from pathlib import Path

KS = (1, 5, 10)
PROBES = ("oracle", "latest", "first", "nearest")


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


def correct(row: dict, pred: dict) -> bool:
    if not row["answerable"]:
        return pred.get("answerable") is False
    return pred.get("answerable") is not False and contains(pred.get("answer") or "", row["short_answer"] or "")


def row_scores(row: dict, pred: dict, units: dict, ks=KS) -> dict:
    """One row's contribution to every metric; None where the row is outside that metric's denominator.

    `units` maps a unit id to what it stands for: [(provision, ordinal or None for a
    repeal, [(start, end or None)])]. An id missing from it is not in the corpus.
    """
    gold_p, gold_n = row["lineage_id"], ordinal(row["version_id"])
    accepted = set(row["accepted_evidence"])
    retrieved = pred.get("retrieved") or []
    hit = [u in accepted or any(p == gold_p for p, _, _ in units.get(u, ())) for u in retrieved]
    tv_hit = [u in accepted or (u == row["version_id"] and row["version_id"] is not None) for u in retrieved]
    first = next((i for i, h in enumerate(hit, 1) if h), None)
    out = {"accuracy": float(correct(row, pred)), "mrr": 1 / first if first else 0.0}
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
    if cites:
        stands = [units.get(u) for u in cites]
        out["tver"] = float(any(s is None or not any(in_force(iv, row["as_of"]) for _, _, iv in s) for s in stands))
        mine = {(p, n) for s in stands if s for p, n, _ in s if p == gold_p}
        out["vcr"] = float(bool(mine) and (gold_p, gold_n) not in mine)
    else:
        out["tver"] = out["vcr"] = None
    return out


def score(rows: list[dict], preds: dict[str, dict], units: dict, ks=KS) -> dict:
    """Mean of each metric over the rows in its denominator, plus TCS over T2 pairs and the counts."""
    per_row = {r["id"]: row_scores(r, preds.get(r["id"], {}), units, ks) for r in rows}
    out: dict = {"rows": len(rows), "cited_rows": sum(s["tver"] is not None for s in per_row.values())}
    for metric in next(iter(per_row.values()), {}):
        values = [s[metric] for s in per_row.values() if s[metric] is not None]
        out[metric] = sum(values) / len(values) if values else None
    pairs = collections.defaultdict(list)
    for r in rows:
        if r["group"] == "T2":
            pairs[(r["lineage_id"], r["as_of_strategy"])].append(r["id"])
    both = [ids for ids in pairs.values() if len(ids) == 2]
    out["tcs"] = sum(all(per_row[i]["accuracy"] for i in ids) for ids in both) / len(both) if both else None
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


def resolve(data: Path, ids: set[str]) -> dict:
    """Unit id -> [(provision, ordinal or None for a repeal, intervals)] for every id the corpus has."""
    events = {u.removeprefix("asis:") for u in ids if u.startswith("asis:event:")}
    provisions = {"provision:" + u.split(":", 1)[1].rsplit(":", 1)[0] for u in ids if u.startswith("version:")}
    provisions |= {u.removeprefix("asis:") for u in ids if u.startswith("asis:provision:")}
    out: dict[str, list] = collections.defaultdict(list)
    created, ended = collections.defaultdict(dict), collections.defaultdict(dict)
    for v in versions(data, provisions, events):
        iv = [(i["start"], i["end"]) for i in v["effective_intervals"]]
        n, pid, maker = int(v["ordinal"]), v["provision_id"], v.get("created_by_event_id")
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
    return {u: s for u, s in out.items() if s}


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
        if name == "oracle" and not r["answerable"]:
            preds[r["id"]] = {"answerable": False, "citations": r["accepted_evidence"],
                              "retrieved": r["accepted_evidence"]}
            continue
        pick = {"oracle": lambda: next(v for v in chain if v["id"] == r["version_id"]),
                "latest": lambda: chain[-1], "first": lambda: chain[0],
                "nearest": lambda: nearest(chain, r["as_of"])}[name]()
        lead = r["target"].get("lead_in") or ""
        preds[r["id"]] = {"answer": f"{lead}\n{pick['text']}".strip(), "answerable": True,
                          "citations": [pick["id"]], "retrieved": [pick["id"]]}
    return preds


def table(title: str, results: dict[str, dict]) -> str:
    cols = ("recall@1", "tv_recall@1", "mrr", "accuracy", "em", "f1", "tver", "vcr", "tcs")
    fmt = lambda x: "   —  " if x is None else f"{x:6.3f}"
    lines = [title, f"{'':<24}" + "".join(f"{c:>12}" for c in cols)]
    for name, rep in results.items():
        for strategy, groups in rep.items():
            lines.append(f"{name + ' · ' + strategy:<24}" + "".join(f"{fmt(groups['all'][c]):>12}" for c in cols))
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predictions", type=Path, nargs="?")
    ap.add_argument("--probes", action="store_true", help="score the four version-choice probes")
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--split", help="score only this split (default: test, or every row before the split)")
    ap.add_argument("--out", type=Path, help="write the full report (per strategy and group) as JSON")
    args = ap.parse_args()
    if bool(args.predictions) == args.probes:
        ap.error("give a predictions file or --probes")
    rows = [json.loads(line) for line in (args.data / "derived/vilextime/release.jsonl").open(encoding="utf-8")]
    split = args.split or default_split(rows)

    if args.probes:
        gold = {r["lineage_id"] for r in rows}
        chains = collections.defaultdict(list)
        for v in versions(args.data, gold, set()):
            chains[v["provision_id"]].append(v)
        runs = {name: probe(name, rows, chains) for name in PROBES}
    else:
        runs = {args.predictions.stem: {p["id"]: p for p in map(json.loads, args.predictions.open(encoding="utf-8"))}}
    ids = {u for preds in runs.values() for p in preds.values() for u in (p.get("citations") or []) + (p.get("retrieved") or [])}
    units = resolve(args.data, ids)
    results = {name: report(rows, preds, units, split) for name, preds in runs.items()}
    print(table(f"ViLexTime · {len(rows):,} dòng · split {split or 'tất cả (chưa chia)'} · "
                f"{len(ids - units.keys())} mã đơn vị không có trong corpus", results))
    if args.out:
        args.out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
