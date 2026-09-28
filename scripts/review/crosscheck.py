#!/usr/bin/env python3
"""ViLexTime D4 — the independent cross-check and its Cohen κ.

Scope, decided 20/09 (plan phase-4, Q2): 300 rows = every T5 and T6 row of the
release (T6 absorbs T5's shortfall, so together they stay 150) plus a random
50 rows from each of T2, T3 and T4, drawn by lineage so a pair or chain is
judged whole. Labels follow docs/vilextime-annotation.md v1.0.

    build   writes data/review/crosscheck_A.tsv and crosscheck_B.tsv: the same
            rows, lineages in a shuffled order, empty `verdict`, `reasons`,
            `note` (and `adjudicated` on A). Refuses to overwrite a file that
            already carries labels.
    kappa   reads both files and reports, over the rows both annotators
            filled: raw agreement, Cohen κ and Gwet's AC1 on `verdict` (κ drops
            when nearly every row is `dat` even if the two agree; AC1 does not),
            overall, per group and per lineage (a lineage is `khong_dat` when any
            of its rows is), plus the rows they disagree on. Writes
            data/review/crosscheck_result.json.

Rows come from release.jsonl (enrich_vilextime.py), boundary rows only: a
mid-interval twin shares its row's question and gold version, so it is judged
with it.

Usage:
    python scripts/review/crosscheck.py build
    python scripts/review/crosscheck.py kappa
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from sample_vilextime import select  # noqa: E402  exact row totals without splitting a lineage

SEED = 20260925
SAMPLED = {"T2": 50, "T3": 50, "T4": 50}
WHOLE = ("T5", "T6")
VERDICTS = {"dat", "khong_dat"}
REASONS = {"question_ambiguous", "question_leaks", "gold_wrong", "group_mismatch",
           "unanswerable_as_asked", "transitional_rule", "other"}   # transitional_rule: guideline v1.1
COLUMNS = ["id", "group", "lineage_id", "question", "as_of", "lead_in", "answer", "changed_span", "citation",
           "law_id", "valid_from", "valid_to", "source_url", "note_for_annotator", "verdict", "reasons", "note"]


def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    """κ for two raters over the same items; None when chance agreement is total."""
    n = len(a)
    if n == 0:
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def gwet_ac1(a: list[str], b: list[str]) -> float | None:
    """Gwet's AC1 for two raters: chance agreement from the mean category share."""
    n = len(a)
    if n == 0:
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    cats = set(a) | set(b)
    if len(cats) < 2:
        return 1.0
    share = {c: (a.count(c) + b.count(c)) / (2 * n) for c in cats}
    expected = sum(p * (1 - p) for p in share.values()) / (len(cats) - 1)
    return (observed - expected) / (1 - expected)


def pick(rows: list[dict]) -> list[dict]:
    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_lineage[r["lineage_id"]].append(r)
    chosen = []
    for group in ("T2", "T3", "T4", *WHOLE):
        lineages = sorted(lid for lid, rs in by_lineage.items() if rs[0]["group"] == group)
        if group in WHOLE:
            chosen += lineages
            continue
        random.Random(f"{SEED}:{group}").shuffle(lineages)
        ranked = [{"rank": i, "lineage_id": lid, "rows": len(by_lineage[lid])} for i, lid in enumerate(lineages)]
        chosen += select(ranked, set(lineages), SAMPLED[group])
    random.Random(SEED).shuffle(chosen)                    # groups interleaved, pairs kept together
    return [r for lid in chosen for r in sorted(by_lineage[lid], key=lambda r: r["as_of"])]


def row_cells(r: dict) -> list[str]:
    hint = ""
    if r.get("retroactive"):
        x = r["retroactive"]
        hint = f"T5: {x['actor_law_id']} ký {x['issued_on']}, hiệu lực {x['effective_from']}"
    answer = r["answer"] if r["answer"] is not None else f"(không có đáp án: {r['no_answer_reason']})"
    return [r["id"], r["group"], r["lineage_id"], r["question"], r["as_of"], r["target"].get("lead_in") or "",
            answer, r.get("changed_span") or "", r["target"]["citation"], r["target"]["law_id"],
            r["valid_from"] or "", r["valid_to"] or "", r["source_url"], hint, "", "", ""]


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def build(data: Path) -> None:
    out = data / "review"
    for name in ("crosscheck_A.tsv", "crosscheck_B.tsv"):
        path = out / name
        if path.exists() and any(r.get("verdict") for r in read(path)):
            raise SystemExit(f"{path} already carries labels; refusing to overwrite")
    rows = pick([r for r in map(json.loads, (data / "derived/vilextime/release.jsonl").open(encoding="utf-8"))
                 if r["as_of_strategy"] == "ranh_gioi"])
    for name, extra in (("crosscheck_A.tsv", ["adjudicated"]), ("crosscheck_B.tsv", [])):
        with (out / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(COLUMNS + extra)
            for r in rows:
                w.writerow(row_cells(r) + [""] * len(extra))
    counts = collections.Counter(r["group"] for r in rows)
    print(f"{len(rows)} dòng -> {out}/crosscheck_A.tsv, crosscheck_B.tsv  {dict(sorted(counts.items()))}")


def kappa(data: Path) -> None:
    a = {r["id"]: r for r in read(data / "review/crosscheck_A.tsv")}
    b = {r["id"]: r for r in read(data / "review/crosscheck_B.tsv")}
    bad = [(who, r["id"], r["verdict"]) for who, rows in (("A", a), ("B", b)) for r in rows.values()
           if r["verdict"] and r["verdict"] not in VERDICTS]
    bad += [(who, r["id"], code) for who, rows in (("A", a), ("B", b)) for r in rows.values()
            for code in filter(None, (c.strip() for c in r["reasons"].split(","))) if code not in REASONS]
    if bad:
        raise SystemExit(f"nhãn ngoài từ vựng (docs/vilextime-annotation.md §2): {bad[:10]}")
    both = [i for i in a if i in b and a[i]["verdict"] and b[i]["verdict"]]
    def scores(ids: list[str]) -> dict:
        va, vb = [a[i]["verdict"] for i in ids], [b[i]["verdict"] for i in ids]
        return {"n": len(ids), "agreement": sum(x == y for x, y in zip(va, vb)) / len(ids) if ids else None,
                "kappa": cohen_kappa(va, vb), "ac1": gwet_ac1(va, vb)}

    lineage: dict[str, list[str]] = collections.defaultdict(list)
    for i in both:
        lineage[a[i]["lineage_id"]].append(i)
    worst = lambda rows, lid: "khong_dat" if any(rows[i]["verdict"] == "khong_dat" for i in lineage[lid]) else "dat"
    lids = sorted(lineage)
    lva, lvb = [worst(a, lid) for lid in lids], [worst(b, lid) for lid in lids]
    result = {
        "guideline_version": "1.1",
        "labelled_by_both": len(both), "total": len(a),
        **scores(both),
        "per_group": {g: scores([i for i in both if a[i]["group"] == g]) for g in sorted({a[i]["group"] for i in both})},
        "per_lineage": {"n": len(lids), "agreement": sum(x == y for x, y in zip(lva, lvb)) / len(lids) if lids else None,
                        "kappa": cohen_kappa(lva, lvb), "ac1": gwet_ac1(lva, lvb)},
        "disagreements": [i for i in both if a[i]["verdict"] != b[i]["verdict"]],
    }
    (data / "review/crosscheck_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                                                        encoding="utf-8")
    fmt = lambda x: f"{x:.3f}" if x is not None else "—"
    print(f"{len(both)}/{len(a)} dòng cả hai đã gán · đồng ý {fmt(result['agreement'])} · "
          f"κ {fmt(result['kappa'])} · AC1 {fmt(result['ac1'])}")
    for g, v in result["per_group"].items():
        print(f"  {g}: n={v['n']:>3}  đồng ý={fmt(v['agreement'])}  κ={fmt(v['kappa'])}  AC1={fmt(v['ac1'])}")
    v = result["per_lineage"]
    print(f"  theo lineage: n={v['n']}  đồng ý={fmt(v['agreement'])}  κ={fmt(v['kappa'])}  AC1={fmt(v['ac1'])}")
    print(f"  {len(result['disagreements'])} dòng lệch cần hoà giải · mục tiêu κ ≥ 0,6")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("build", "kappa"))
    ap.add_argument("--data", type=Path, default=Path("data"))
    args = ap.parse_args()
    (build if args.command == "build" else kappa)(args.data)


if __name__ == "__main__":
    main()
