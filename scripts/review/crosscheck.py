#!/usr/bin/env python3
"""ViLexTime D4 — the independent cross-check and its Cohen κ.

Scope, decided 20/09 (plan phase-4, Q2) and re-cut 11/10: 300 rows drawn by
lineage, so a pair or chain is judged whole —
  * every T5 row, and T6 up to CORE rows together with T5, split between its
    "ancestor" and "direct" parts in the release's own proportion (T6 grew from
    112 to 388 rows on 07/10, so "every T6 row" no longer fits in 300);
  * T2 50 + 50: the half that was T2 and the half that was T4, now T2's
    `near_identical` slice;
  * T3 50.
Labels follow docs/vilextime-annotation.md (version GUIDELINE).

Both files live in data/review/ — the directory .gitignore whitelists because
losing a human label means labelling it again by hand — and every reader
(labels.py, check_validity.py, crosscheck_evidence.py, check_release.py's
manifest) expects them there. A labelled copy kept anywhere else is outside
version control and makes `kappa` read the empty originals.

    build   writes data/review/crosscheck_A.tsv and crosscheck_B.tsv: the same
            rows, lineages in a shuffled order, `verdict`, `reasons`, `note`
            (and `adjudicated` on A) empty except on a row labelled in the
            earlier draw whose question and answer are unchanged, which keeps
            its labels. A file that carries labels is first copied to
            crosscheck_X.<YYYYMMDD>.tsv; build stops if that copy exists.
    kappa   reads both files and reports, over the rows both annotators
            filled: raw agreement, Cohen κ and Gwet's AC1 on `verdict` (κ drops
            when nearly every row is `dat` even if the two agree; AC1 does not),
            overall, per group and per lineage (a lineage is `khong_dat` when any
            of its rows is), plus the rows they disagree on, and the rows that
            already carry a label from outside D4 (data/review/labels.tsv: the
            Excel preview, or a model label from before the row joined the set)
            — they were not blind to whoever labelled them, and the record of D5
            must say so. Writes data/review/crosscheck_result.json.
            `--set pilot_T6` reads the pilot files instead and writes pilot_T6_result.json.
    pilot   writes data/review/pilot_T6_A.tsv and pilot_T6_B.tsv: PILOT_ROWS T6
            boundary rows outside D4 that carry no label anywhere, whole
            lineages, split ancestor/direct in the release's proportion (B8,
            MASTER_RESEARCH_GUIDE §5.3.4). Calibrates guideline 2.0 on T6 before
            the 92 T6 rows of D4 are labelled; the gate is PILOT_GATE of 20 agreeing.
            Stops if either file exists.

Rows come from release.jsonl (enrich_vilextime.py), boundary rows only: a
mid-interval twin shares its row's question and gold version, so it is judged
with it.

Usage:
    python scripts/review/crosscheck.py build
    python scripts/review/crosscheck.py kappa [--set pilot_T6]
    python scripts/review/crosscheck.py pilot
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from sample_vilextime import select  # noqa: E402  exact row totals without splitting a lineage

SEED = 20260925
# T4 is no longer a group (build_question_pool.QUOTA): its rows are T2's, told
# apart by the `near_identical` facet, so T2 takes the 50 that were T4's.
# Rows per stratum; T5 is taken whole and T6 sized from it (CORE), see `strata`.
SAMPLED = {("T2", "regular"): 50, ("T2", "near"): 50, ("T3", None): 50}
CORE = 150   # T5 + T6 rows (Q2: T6 absorbs T5's shortfall)
# Pre-registered before the production overlap batch, which is what makes them
# usable as a pass/fail (ARR checklist D). AC1 is the primary measure and kappa is
# reported beside it, never instead of it — see `agreement_needed` for why kappa
# cannot be the gate at this label distribution. p_neg is the one specific
# agreement that matters: `khong_dat` is the verdict that removes a row.
AC1_TARGET = 0.80
PNEG_TARGET = 0.60
KAPPA_PROPOSAL = 0.60          # the figure the submitted de cuong names, reported as-is
BOOTSTRAP_DRAWS = 1000
PILOT_ROWS, PILOT_GATE = 20, 17   # B8: >= 17/20 agree, else revise the guideline and try 10 more
GUIDELINE = "2.0"   # docs/vilextime-annotation.md; labels.py and check_release.py read it from here
VERDICTS = {"dat", "khong_dat"}
REASONS = {"question_ambiguous", "question_leaks", "gold_wrong", "group_mismatch",
           "unanswerable_as_asked", "transitional_rule", "other"}   # transitional_rule: guideline v1.1
COLUMNS = ["id", "group", "lineage_id", "question", "as_of", "lead_in", "answer", "changed_span", "citation",
           "law_id", "valid_from", "valid_to", "source_url", "note_for_annotator", "verdict", "reasons", "note",
           "suggestion", "guideline_version"]   # guideline_version: the one the row was labelled under (B8)


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


def specific_agreement(a: list[str], b: list[str]) -> dict[str, float | None]:
    """Agreement within each verdict on its own (Cicchetti & Feinstein 1990).

    One number cannot say *which* category two raters agree on, and here that is
    the whole question: `dat` holds ~85% of the rows, so p_pos is nearly free while
    p_neg — agreement on the verdict that drops a row from the release — is the
    claim the dataset's quality rests on.
    """
    out: dict[str, float | None] = {}
    for c in sorted(set(a) | set(b)):
        total = a.count(c) + b.count(c)
        out[c] = (2 * sum(x == c == y for x, y in zip(a, b)) / total) if total else None
    return out


def agreement_needed(a: list[str], b: list[str], target: float) -> float | None:
    """The p_o these marginals would need for kappa to reach `target`.

    kappa = (p_o - p_e) / (1 - p_e), so p_o = target * (1 - p_e) + p_e. Measured on
    the D4 set (07/10): A called 84.3% of rows `dat`, and reaching kappa 0.60 there
    takes p_o >= 0.843; two raters who both settle near 85% `dat` need p_o >= 0.898,
    at most ~30 disagreements in 300. That is a property of the label distribution,
    not of how carefully anyone labelled — no amount of extra calibration moves it —
    which is why AC1 is the pre-registered gate (Gwet 2008, the prevalence paradox).
    Printed next to kappa so the choice of measure carries its own justification.
    """
    n = len(a)
    if n == 0:
        return None
    ca, cb = collections.Counter(a), collections.Counter(b)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if expected >= 1 else target * (1 - expected) + expected


def bootstrap_ci(a: list[str], b: list[str], stat, draws: int = BOOTSTRAP_DRAWS) -> list[float] | None:
    """Percentile bootstrap over items, seeded so a rerun reproduces the interval.

    Resampling is by *row* here because that is the unit the two annotators judged.
    The release-level figures resample by lineage instead (scorer `--ci`), since
    rows of one lineage share a question and are not independent.
    """
    if len(a) < 2:
        return None
    rng = random.Random(SEED)
    size = len(a)
    values = []
    for _ in range(draws):
        idx = [rng.randrange(size) for _ in range(size)]
        value = stat([a[i] for i in idx], [b[i] for i in idx])
        if value is not None:
            values.append(value)
    if not values:
        return None
    values.sort()
    return [round(values[int(0.025 * len(values))], 3),
            round(values[min(len(values) - 1, int(0.975 * len(values)))], 3)]


def pair_scores(va: list[str], vb: list[str]) -> dict:
    """Every agreement figure for one pair of label vectors, AC1 first."""
    specific = specific_agreement(va, vb)
    return {
        "n": len(va),
        "agreement": sum(x == y for x, y in zip(va, vb)) / len(va) if va else None,
        "ac1": gwet_ac1(va, vb),
        "ac1_ci95": bootstrap_ci(va, vb, gwet_ac1),
        "p_pos": specific.get("dat"),
        "p_neg": specific.get("khong_dat"),
        "kappa": cohen_kappa(va, vb),
        "kappa_ci95": bootstrap_ci(va, vb, cohen_kappa),
        "agreement_needed_for_kappa_target": agreement_needed(va, vb, KAPPA_PROPOSAL),
    }


def stratum(rows: list[dict]) -> tuple[str, str | None]:
    """A lineage's stratum: its group, and T2's or T6's part."""
    group = rows[0]["group"]
    if group == "T2":
        return group, "near" if any(r.get("near_identical") for r in rows) else "regular"
    if group == "T6":
        return group, rows[0].get("repeal_mode") or "direct"
    return group, None


def targets(by_lineage: dict[str, list[dict]]) -> dict[tuple[str, str | None], int | None]:
    """Rows per stratum; None takes the stratum whole (T5)."""
    size = collections.Counter()
    for rows in by_lineage.values():
        size[stratum(rows)] += len(rows)
    t6 = CORE - size[("T5", None)]
    share = size[("T6", "ancestor")] / ((size[("T6", "ancestor")] + size[("T6", "direct")]) or 1)
    ancestor = 2 * round(t6 * share / 2)   # T6 lineages are pairs
    return {**SAMPLED, ("T5", None): None, ("T6", "ancestor"): ancestor, ("T6", "direct"): t6 - ancestor}


def pick(rows: list[dict], prior: set[str] = frozenset()) -> list[dict]:
    """The cross-check rows; lineages of an earlier draw (`prior`) still in the release come first.

    A seeded shuffle of a list that gained or lost lineages draws a different
    sample, and a lineage new to the set would arrive carrying the model labels
    it got outside D4 (29/09 rebuild: 35 of 141 lineages moved). Keeping the
    earlier draw and topping it up keeps D4 human-only, and keeps its labels.
    """
    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_lineage[r["lineage_id"]].append(r)
    chosen = []
    for (group, part), need in targets(by_lineage).items():
        lineages = sorted(lid for lid, rs in by_lineage.items() if stratum(rs) == (group, part))
        if need is None:
            chosen += lineages
            continue
        random.Random(f"{SEED}:{group}" + (f":{part}" if part else "")).shuffle(lineages)
        lineages = [lid for lid in lineages if lid in prior] + [lid for lid in lineages if lid not in prior]
        ranked = [{"rank": i, "lineage_id": lid, "rows": len(by_lineage[lid])} for i, lid in enumerate(lineages)]
        chosen += select(ranked, set(lineages), need)
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
            r["valid_from"] or "", r["valid_to"] or "", r["source_url"], hint, "", "", "", "", ""]


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# A label made before guideline_version existed was made under 1.2: D4 started on 1.2 and stopped
# there until 2.0 (12/10).
LABEL_CELLS = ("verdict", "reasons", "note", "suggestion", "guideline_version", "adjudicated")


def build(data: Path, today: str | None = None) -> None:
    out = data / "review"
    stamp = today or date.today().strftime("%Y%m%d")
    earlier = {}
    for name in ("crosscheck_A.tsv", "crosscheck_B.tsv"):
        path = out / name
        rows = read(path) if path.exists() else []
        earlier[name] = {(r["lineage_id"], r["as_of"]): r for r in rows}   # T4 rows became T2: id changed
        if any(r.get("verdict") for r in rows):
            keep = path.with_name(f"{path.stem}.{stamp}.tsv")
            if keep.exists():
                raise SystemExit(f"{keep} đã có; không ghi đè bản lưu nhãn cũ")
            shutil.copyfile(path, keep)
            print(f"lưu nhãn cũ -> {keep}")
    prior = {r["lineage_id"] for r in earlier["crosscheck_A.tsv"].values()}
    rows = pick([r for r in map(json.loads, (data / "derived/vilextime/release.jsonl").open(encoding="utf-8"))
                 if r["as_of_strategy"] == "ranh_gioi"], prior)
    kept = collections.Counter()
    for name, extra in (("crosscheck_A.tsv", ["adjudicated"]), ("crosscheck_B.tsv", [])):
        columns = COLUMNS + extra
        with (out / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(columns)
            for r in rows:
                cells = dict(zip(columns, row_cells(r) + [""] * len(extra)))
                old = earlier[name].get((r["lineage_id"], r["as_of"]))
                # a label judged a question and an answer; it travels only with both unchanged
                if old and old.get("verdict") and all(old[c] == cells[c] for c in ("question", "answer")):
                    cells.update({c: old.get(c, "") for c in LABEL_CELLS if c in cells})
                    cells["guideline_version"] = cells["guideline_version"] or "1.2"
                    kept[name] += 1
                w.writerow([cells[c] for c in columns])
    counts = collections.Counter(stratum([r]) for r in rows)
    print(f"{len(rows)} dòng -> {out}/crosscheck_A.tsv, crosscheck_B.tsv  "
          f"{ {f'{g}/{p}' if p else g: n for (g, p), n in sorted(counts.items(), key=str)} }")
    print(f"giữ nhãn cũ: A {kept['crosscheck_A.tsv']} dòng, B {kept['crosscheck_B.tsv']} dòng")


def pilot(data: Path) -> None:
    out = [data / f"review/pilot_T6_{who}.tsv" for who in "AB"]
    if any(p.exists() for p in out):
        raise SystemExit(f"{out[0].parent}/pilot_T6_*.tsv đã có; không ghi đè nhãn pilot")
    d4 = {r["id"] for r in read(data / "review/crosscheck_A.tsv")}
    labels = data / "review/labels.tsv"
    labelled = {r["id"] for r in read(labels)} if labels.exists() else set()
    t6 = [r for r in map(json.loads, (data / "derived/vilextime/release.jsonl").open(encoding="utf-8"))
          if r["group"] == "T6" and r["as_of_strategy"] == "ranh_gioi"]
    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for r in t6:
        by_lineage[r["lineage_id"]].append(r)
    free = {lid: rs for lid, rs in by_lineage.items() if not any(r["id"] in d4 | labelled for r in rs)}
    size = collections.Counter(stratum(rs) for rs in free.values() for _ in rs)
    ancestor = 2 * round(PILOT_ROWS * size[("T6", "ancestor")] / (sum(size.values()) or 1) / 2)   # pairs
    chosen = []
    for part, need in (("ancestor", ancestor), ("direct", PILOT_ROWS - ancestor)):
        lineages = sorted(lid for lid, rs in free.items() if stratum(rs) == ("T6", part))
        random.Random(f"{SEED}:pilot:{part}").shuffle(lineages)
        got = 0
        for lid in lineages:
            if got >= need:
                break
            chosen.append(lid)
            got += len(free[lid])
    random.Random(f"{SEED}:pilot").shuffle(chosen)
    rows = [r for lid in chosen for r in sorted(free[lid], key=lambda r: r["as_of"])]
    for path in out:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(COLUMNS)
            w.writerows(row_cells(r) for r in rows)
    print(f"{len(rows)} dòng T6 ({collections.Counter(r.get('repeal_mode') or 'direct' for r in rows)}) "
          f"trong {sum(map(len, free.values()))} dòng chưa có nhãn -> {out[0]}, {out[1].name}")


def kappa(data: Path, name: str = "crosscheck") -> None:
    a = {r["id"]: r for r in read(data / f"review/{name}_A.tsv")}
    b = {r["id"]: r for r in read(data / f"review/{name}_B.tsv")}
    bad = [(who, r["id"], r["verdict"]) for who, rows in (("A", a), ("B", b)) for r in rows.values()
           if r["verdict"] and r["verdict"] not in VERDICTS]
    bad += [(who, r["id"], code) for who, rows in (("A", a), ("B", b)) for r in rows.values()
            for code in filter(None, (c.strip() for c in r["reasons"].split(","))) if code not in REASONS]
    if bad:
        raise SystemExit(f"nhãn ngoài từ vựng (docs/vilextime-annotation.md §2): {bad[:10]}")
    both = [i for i in a if i in b and a[i]["verdict"] and b[i]["verdict"]]
    if not both:
        # Writing a result file of nulls looks like a finished run and is worse than
        # stopping: the labelled copies have lived outside `--data` before, and a
        # silent zero is how that goes unnoticed.
        raise SystemExit(
            f"0/{len(a)} dòng có nhãn ở cả hai phía trong {data}/review/{name}_{{A,B}}.tsv — "
            "chưa gán nhãn, hoặc bản có nhãn nằm ở thư mục khác (truyền --data)")
    def version(i: str) -> str:
        va, vb = (x[i].get("guideline_version") or "1.2" for x in (a, b))
        return va if va == vb else "mixed"

    def scores(ids: list[str]) -> dict:
        return pair_scores([a[i]["verdict"] for i in ids], [b[i]["verdict"] for i in ids])

    lineage: dict[str, list[str]] = collections.defaultdict(list)
    for i in both:
        lineage[a[i]["lineage_id"]].append(i)
    worst = lambda rows, lid: "khong_dat" if any(rows[i]["verdict"] == "khong_dat" for i in lineage[lid]) else "dat"
    lids = sorted(lineage)
    lva, lvb = [worst(a, lid) for lid in lids], [worst(b, lid) for lid in lids]
    labels = data / "review/labels.tsv"
    outside = read(labels) if labels.exists() else []
    result = {
        "guideline_version": GUIDELINE,
        "labelled_by_both": len(both), "total": len(a),
        **scores(both),
        "per_group": {g: scores([i for i in both if a[i]["group"] == g]) for g in sorted({a[i]["group"] for i in both})},
        "per_lineage": pair_scores(lva, lvb),
        # A row labelled under two versions by A and B is "mixed": neither version's agreement.
        "per_guideline": {v: scores([i for i in both if version(i) == v]) for v in sorted({version(i) for i in both})},
        "preregistered": {"primary": "ac1", "ac1_target": AC1_TARGET, "p_neg_target": PNEG_TARGET,
                          "kappa_reported_target": KAPPA_PROPOSAL},
        "disagreements": [i for i in both if a[i]["verdict"] != b[i]["verdict"]],
        "labelled_before_d4": {i: sorted({x["labeler"] for x in outside if x["id"] == i})
                               for i in sorted({x["id"] for x in outside if x["id"] in a})},
    }
    (data / f"review/{name}_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                                                        encoding="utf-8")
    fmt = lambda x: f"{x:.3f}" if x is not None else "—"
    ci = lambda x: f"[{x[0]:.3f}; {x[1]:.3f}]" if x else "—"
    line = lambda label, v: (f"{label}  n={v['n']:>3}  AC1={fmt(v['ac1'])} {ci(v['ac1_ci95'])}  "
                             f"p_neg={fmt(v['p_neg'])}  đồng ý={fmt(v['agreement'])}  κ={fmt(v['kappa'])}")
    print(f"{len(both)}/{len(a)} dòng cả hai đã gán · chỉ số chính AC1 (đăng ký trước)")
    print(line("  toàn tập:   ", result))
    for g, v in result["per_group"].items():
        print(line(f"  {g}:         "[:14], v))
    print(line("  lineage:    ", result["per_lineage"]))
    for v, s in result["per_guideline"].items():
        print(line(f"  v{v}:".ljust(14), s))
    ok = result["ac1"] is not None and result["ac1"] >= AC1_TARGET and (
        result["p_neg"] is not None and result["p_neg"] >= PNEG_TARGET)
    need = result["agreement_needed_for_kappa_target"]
    print(f"  ngưỡng đăng ký trước: AC1 >= {AC1_TARGET:.2f} và p_neg >= {PNEG_TARGET:.2f} -> "
          f"{'ĐẠT' if ok else 'CHƯA ĐẠT'}")
    print(f"  κ chỉ báo kèm: ở biên nhãn này κ >= {KAPPA_PROPOSAL:.2f} đòi p_o >= {fmt(need)}"
          f" (tối đa {round((1 - need) * result['n']) if need else '—'} dòng lệch / {result['n']})")
    print(f"  {len(result['disagreements'])} dòng lệch cần hoà giải")
    if name == "pilot_T6":
        agree = result["n"] - len(result["disagreements"])
        print(f"  cổng pilot: trùng {agree}/{result['n']}, cần >= {PILOT_GATE}/{PILOT_ROWS} -> "
              f"{'ĐẠT' if result['n'] == PILOT_ROWS and agree >= PILOT_GATE else 'CHƯA ĐẠT'}")
    seen = collections.Counter(lab for labs in result["labelled_before_d4"].values() for lab in labs)
    print(f"  {len(result['labelled_before_d4'])} dòng đã có nhãn ngoài D4 trước khi gán (ghi vào biên bản D5): {dict(seen)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("build", "kappa", "pilot"))
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--set", default="crosscheck", choices=("crosscheck", "pilot_T6"), help="kappa only")
    args = ap.parse_args()
    if args.command == "kappa":
        kappa(args.data, args.set)
    else:
        (build if args.command == "build" else pilot)(args.data)


if __name__ == "__main__":
    main()
