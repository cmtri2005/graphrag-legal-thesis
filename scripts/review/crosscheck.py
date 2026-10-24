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
    kiem    writes data/review/kiem_A.tsv and kiem_B.tsv: every boundary row of the
            release, the check of docs/vilextime-dinh-nghia.md §8 that decides the test
            split. KIEM_OVERLAP of each group's rows, whole lineages, go to both files
            (labelled blind, `kappa --set kiem`); the rest alternate A/B. Before them, batch
            `lo` 0 is the calibration both people label and then discuss (CALIB lineages per
            stratum, never D4, never counted in the agreement); the overlap is spread
            evenly over batches 1.. with the same batch number in both files, so agreement
            can be read after any batch. A D4 lineage
            goes to one file with its final D4 label (adjudicated, or agreed) when the
            question and answer are unchanged — both have seen its adjudication, so it
            cannot measure agreement. Each row carries the cut of the raw text
            (`kiem_evidence.jsonl` from crosscheck_evidence.py --ids), the version chain and,
            on T6, where the content may have gone (`kiem_goi_y.jsonl` from kiem_hints.py), the
            machine's flags, a batch number `lo`, and the guideline 3.0 fields KIEM_FIELDS. A
            re-run keeps who has which lineage and every label still on an unchanged
            row; a file carrying labels is first copied to kiem_X.<YYYYMMDD>.tsv.
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
    python scripts/review/crosscheck.py kiem
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
from enrich_vilextime import norm  # noqa: E402  the span comparison check_short_answer uses
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
AC1_CHOSEN = "AC1 chọn sau pilot 07/10/2026 (nghịch lý prevalence của κ), không đăng ký trước"   # MASTER_RESEARCH_GUIDE A3, DL-12
KAPPA_PROPOSAL = 0.60          # the figure the submitted de cuong names, reported as-is
BOOTSTRAP_DRAWS = 1000
PILOT_ROWS, PILOT_GATE = 20, 17   # B8: >= 17/20 agree, else revise the guideline and try 10 more
GUIDELINE = "3.0"   # docs/vilextime-annotation.md; labels.py and check_release.py read it from here
VERDICTS = {"dat", "khong_dat"}
# Codes a person may write (docs/vilextime-dinh-nghia.md §7). transitional_rule: guideline 1.1;
# the rest after `other`: 3.0. The machine-only codes (single_change, pending_event,
# after_snapshot, not_verified) are not labels.
REASONS = {"question_ambiguous", "question_leaks", "gold_wrong", "group_mismatch",
           "unanswerable_as_asked", "transitional_rule", "other",
           "relocated", "relocation_unclear", "superseded_by_other_norm", "restructuring_2025",
           "reference_only", "rename_only", "cosmetic_only", "auto_reference_update"}
COLUMNS = ["id", "group", "lineage_id", "question", "as_of", "lead_in", "answer", "changed_span", "citation",
           "law_id", "valid_from", "valid_to", "source_url", "note_for_annotator", "verdict", "reasons", "note",
           "suggestion", "guideline_version"]   # guideline_version: the one the row was labelled under (B8)


# The 100% check (definition §8): 25% of rows labelled by both, batches of 30-50 rows.
KIEM_OVERLAP = 0.25
KIEM_BATCH = 40
# Batch 0: lineages both people label first and then discuss with the lawyer, so a reading the
# guideline leaves open is settled before the independent batches, not in them. Weighted to where
# D4 split (D5 §2): T6 and the T2 near-identical slice.
CALIB = {("T6", "ancestor"): 2, ("T6", "direct"): 2, ("T2", "near"): 2, ("T2", "regular"): 2,
         ("T3", None): 1, ("T1", None): 2}
# guideline 3.0 §5: required besides verdict/reasons/note (`cham_lan_sua` on T2/T3, `noi_dung_con_o_dau` on T6)
KIEM_FIELDS = ["da_xem_van_ban_tac_dong", "cham_lan_sua", "noi_dung_con_o_dau", "phut"]
KIEM_COLUMNS = ["lo", "id", "group", "subgroup", "lineage_id", "question", "as_of", "lead_in", "answer",
                "short_answer", "changed_span", "citation", "law_id", "valid_from", "valid_to", "source_url",
                "trich_van_ban_goc", "trich_van_ban_tac_dong", "cac_phien_ban", "goi_y_cho_moi", "note_for_annotator",
                "verdict", "reasons", "note", "suggestion", *KIEM_FIELDS, "guideline_version"]
KIEM_A_COLUMNS = [*KIEM_COLUMNS, "adjudicated"]    # nhãn chốt của bước hoà giải, chỉ ở phiếu A (như D4)
CELL_MAX = 32000   # an Excel cell holds 32,767 characters


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


def evidence_cells(e: dict | None) -> tuple[str, str]:
    """(trich_van_ban_goc, trich_van_ban_tac_dong) from one crosscheck_evidence.py record."""
    if not e:
        return "", ""
    b = e.get("base") or {}
    base = (f"{b.get('document')} · ký {b.get('issued')} · hiệu lực {b.get('effective_from')} đến "
            f"{b.get('effective_to') or 'nay'} · {b.get('status_today')}\n{b.get('passage') or '(không tìm thấy đoạn)'}")
    acts = []
    for a in e.get("actors") or ():
        parts = [f"[{a.get('op')}] {a.get('document')} · ký {a.get('issued')} · hiệu lực {a.get('effective_from')}",
                 a.get("passage") or "(không tìm thấy đoạn tác động)"]
        parts += [f"— Chuyển tiếp: {a['transitional']}"] if a.get("transitional") else []
        parts += [f"— Hiệu lực: {a['in_force']}"] if a.get("in_force") else []
        acts.append("\n".join(parts))
    missing = f"\n(thiếu: {', '.join(e['missing'])})" if e.get("missing") else ""
    return base[:CELL_MAX], ("\n\n".join(acts) + missing)[:CELL_MAX]


def d4_final(data: Path) -> dict[tuple[str, str], dict]:
    """(lineage_id, as_of) -> the D4 row with its final label: adjudicated, else the label both gave."""
    a = {r["id"]: r for r in read(data / "review/crosscheck_A.tsv")}
    b = {r["id"]: r for r in read(data / "review/crosscheck_B.tsv")}
    adj = {r["id"]: r for r in read(data / "review/hoa_giai_D4.tsv")} if (data / "review/hoa_giai_D4.tsv").exists() else {}
    out = {}
    for i, ra in a.items():
        rb = b.get(i, {})
        if i in adj and adj[i]["verdict"]:
            label = {c: adj[i][c] for c in ("verdict", "reasons", "note")}
            label["note"] = f"[D4 hoà giải, {adj[i].get('adjudicator')}] {label['note']}".strip()
        elif ra["verdict"] and ra["verdict"] == rb.get("verdict"):
            label = {"verdict": ra["verdict"], "reasons": ra["reasons"] or rb.get("reasons", ""),
                     "note": ("[D4: A và B cùng nhãn] " + " | ".join(filter(None, (ra["note"], rb.get("note"))))).strip()}
        else:
            continue
        label["guideline_version"] = ra.get("guideline_version") or rb.get("guideline_version") or "1.2"
        out[(ra["lineage_id"], ra["as_of"])] = {**ra, **label}
    return out


def calibration(by_lineage: dict[str, list[dict]], assign: dict[str, set[str]], d4: set[str]) -> set[str]:
    """CALIB lineages per stratum for batch 0: not D4 (both have seen its adjudication), not overlap."""
    chosen: set[str] = set()
    for (group, part), n in CALIB.items():
        pool = sorted(lid for lid, rs in by_lineage.items() if stratum(rs) == (group, part)
                      and lid not in d4 and assign.get(lid) != {"A", "B"})
        random.Random(f"{SEED}:kiem:calib:{group}:{part}").shuffle(pool)
        chosen.update(pool[:n])
    return chosen


def batches(overlap: list[str], singles: list[str], size: dict[str, int], batch: int) -> list[list[str]]:
    """Lineages per batch: the overlap spread evenly in its given order, singles filling each to `batch` rows.

    Both files receive the overlap in the same order, so a shared lineage lands in the same batch for A
    and B and agreement can be read after any batch, not only at the end.
    """
    total = sum(size[lid] for lid in overlap + singles)
    n = max(1, -(-total // batch))
    even = -(-total // n)          # rows per batch, so the last one is not left with the overlap alone
    lots: list[list[str]] = [[] for _ in range(n)]
    for i, lid in enumerate(overlap):
        lots[i * n // len(overlap)].append(lid)
    rest = iter(singles)
    for lot in lots:
        while sum(size[lid] for lid in lot) < even and (lid := next(rest, None)):
            lot.append(lid)
    lots[-1] += list(rest)
    return lots


def kiem(data: Path, today: str | None = None) -> None:
    out = data / "review"
    stamp = today or date.today().strftime("%Y%m%d")
    released = [json.loads(line) for line in (data / "derived/vilextime/release.jsonl").open(encoding="utf-8")]
    rows = [r for r in released if r["as_of_strategy"] == "ranh_gioi"]
    wordings = collections.defaultdict(dict)   # lineage -> version -> answer, for the contrast hint
    for r in released:
        if r["answer"]:
            wordings[r["lineage_id"]][r["version_id"]] = r["answer"]
    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_lineage[r["lineage_id"]].append(r)
    earlier, who_had, calibrated = {}, collections.defaultdict(set), set()
    for who in "AB":
        path = out / f"kiem_{who}.tsv"
        old = read(path) if path.exists() else []
        earlier[who] = {(r["lineage_id"], r["as_of"]): r for r in old}
        for r in old:
            who_had[r["lineage_id"]].add(who)
            if r.get("lo") == "0":
                calibrated.add(r["lineage_id"])
        if any(r.get("verdict") for r in old):
            keep = path.with_name(f"{path.stem}.{stamp}.tsv")
            if keep.exists():
                raise SystemExit(f"{keep} đã có; không ghi đè bản lưu nhãn cũ")
            shutil.copyfile(path, keep)
            print(f"lưu nhãn cũ -> {keep}")
    d4 = d4_final(data)
    d4_lineages = {lid for lid, _ in d4} & set(by_lineage)

    # who labels which lineage: kept from the last run, else D4 to one person, else overlap/alternate
    assign: dict[str, set[str]] = {lid: who_had[lid] for lid in by_lineage if who_had.get(lid)}
    calib = (calibrated & set(by_lineage)) or calibration(by_lineage, assign, d4_lineages)
    for lid in calib:
        assign[lid] = {"A", "B"}
    free_d4 = sorted(d4_lineages - set(assign))
    random.Random(f"{SEED}:kiem:d4").shuffle(free_d4)
    for k, lid in enumerate(free_d4):
        assign[lid] = {"AB"[k % 2]}
    for group in sorted({r["group"] for r in rows}):
        lineages = sorted(lid for lid, rs in by_lineage.items() if rs[0]["group"] == group)
        need = round(KIEM_OVERLAP * sum(len(by_lineage[lid]) for lid in lineages))
        have = sum(len(by_lineage[lid]) for lid in lineages if assign.get(lid) == {"A", "B"} and lid not in calib)
        free = [lid for lid in lineages if lid not in assign]
        random.Random(f"{SEED}:kiem:{group}").shuffle(free)
        for k, lid in enumerate(free):
            if have < need:
                assign[lid], have = {"A", "B"}, have + len(by_lineage[lid])
            else:
                assign[lid] = {"AB"[k % 2]}

    evidence_path, hints_path = out / "kiem_evidence.jsonl", out / "kiem_goi_y.jsonl"
    evidence = ({e["id"]: e for e in map(json.loads, evidence_path.open(encoding="utf-8"))}
                if evidence_path.exists() else {})
    hints = ({h["id"]: h for h in map(json.loads, hints_path.open(encoding="utf-8"))}
             if hints_path.exists() else {})
    flags = collections.defaultdict(set)
    if (out / "validity_queue.tsv").exists():
        for q in read(out / "validity_queue.tsv"):
            if q["active"] == "co" and q["decision"] != "bao_dong_gia":
                flags[q["id"]].add(f"{q['kind']} {q['ref']}".strip())
    if (out / "pending_events.tsv").exists():   # rule R6: undecided, the row stays out of test
        for q in read(out / "pending_events.tsv"):
            if not q["decision"]:
                flags[q["id"]].add(f"R6 sự kiện chưa áp: {q['actor_number']} {q['operation']} {q['effective_on']}")
    for r in rows:   # definition §4 T2: a version's short answer must not sit inside another version
        spans = [f" {norm(x)} " for x in (r.get("short_answer") or "").split("…") if x.strip()]
        for vid, text in wordings[r["lineage_id"]].items():
            if spans and vid != r["version_id"] and all(x in f" {norm(text)} " for x in spans):
                flags[r["id"]].add(f"đáp án ngắn cũng nằm trong phiên bản {vid.rsplit(':', 1)[1]}: câu hỏi có tách được hai mốc?")

    def row_for(r: dict, lo: int) -> dict:
        cells = dict(zip(COLUMNS, row_cells(r)))
        goc, tac = evidence_cells(evidence.get(r["id"]))
        hint = "; ".join(filter(None, [cells["note_for_annotator"], *sorted(flags.get(r["id"], ()))]))
        h = hints.get(r["id"], {})
        cells.update(lo=str(lo), subgroup=r.get("subgroup") or "", short_answer=r.get("short_answer") or "",
                     trich_van_ban_goc=goc, trich_van_ban_tac_dong=tac, note_for_annotator=hint,
                     cac_phien_ban=h.get("cac_phien_ban", "")[:CELL_MAX], goi_y_cho_moi=h.get("goi_y_cho_moi", "")[:CELL_MAX])
        return cells

    kept, carried, sizes = collections.Counter(), collections.Counter(), collections.Counter()
    size = {lid: len(rs) for lid, rs in by_lineage.items()}
    overlap = sorted(lid for lid, w in assign.items() if w == {"A", "B"} and lid not in calib)
    random.Random(f"{SEED}:kiem:overlap").shuffle(overlap)          # one order: the same batch in both files
    for who in "AB":
        singles = sorted(lid for lid, w in assign.items() if w == {who})
        random.Random(f"{SEED}:kiem:order:{who}").shuffle(singles)
        order = [(0, sorted(calib))] + list(enumerate(batches(overlap, singles, size, KIEM_BATCH), 1))
        lines = []
        for lo, lot in order:
            random.Random(f"{SEED}:kiem:lo:{who}:{lo}").shuffle(lot)   # A and B read a batch in different orders
            for lid in lot:
                for r in sorted(by_lineage[lid], key=lambda r: r["as_of"]):
                    lines.append(row_for(r, lo))
        for cells in lines:
            key = (cells["lineage_id"], cells["as_of"])
            old = earlier[who].get(key)
            same = lambda x: x and all(x[c] == cells[c] for c in ("question", "answer"))
            if old and old.get("verdict") and same(old):
                cells.update({c: old.get(c, "") for c in ("verdict", "reasons", "note", "suggestion",
                                                          *KIEM_FIELDS, "guideline_version", "adjudicated")})
                kept[who] += 1
            elif key in d4 and len(assign[cells["lineage_id"]]) == 1 and same(d4[key]):
                cells.update({c: d4[key][c] for c in ("verdict", "reasons", "note", "guideline_version")})
                carried[who] += 1
        sizes[who] = len(lines)
        with (out / f"kiem_{who}.tsv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, KIEM_A_COLUMNS if who == "A" else KIEM_COLUMNS, delimiter="\t",
                               lineterminator="\n", extrasaction="ignore")
            w.writeheader()
            w.writerows(lines)
    both = sum(size[lid] for lid in overlap)
    print(f"{len(rows)} dòng ranh_gioi: A {sizes['A']}, B {sizes['B']}, gán đôi {both} ({both / len(rows):.0%}), "
          f"lô 0 hiệu chuẩn {sum(size[lid] for lid in calib)} dòng -> {out}/kiem_A.tsv, kiem_B.tsv")
    print(f"  nhãn D4 mang sang (câu hỏi, đáp án không đổi): A {carried['A']}, B {carried['B']}; "
          f"giữ nhãn đợt kiểm trước: A {kept['A']}, B {kept['B']}")
    print(f"  {sum(1 for r in rows if r['id'] in evidence)}/{len(rows)} dòng có trích văn bản gốc ({evidence_path.name}), "
          f"{sum(1 for r in rows if r['id'] in hints)} có gợi ý máy ({hints_path.name})")


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
    labelled = [i for i in a if i in b and a[i]["verdict"] and b[i]["verdict"]]
    if name == "kiem":   # a D4 label sits in both files since A's sheet took B's rows (21/10): not two judgements
        labelled = [i for i in labelled if a[i].get("guideline_version") == b[i].get("guideline_version") == GUIDELINE]
    # batch 0 of `kiem` is labelled by both and then discussed: calibration, not agreement
    calib = [i for i in labelled if a[i].get("lo") == "0"]
    both = [i for i in labelled if a[i].get("lo") != "0"]
    if not both and not calib:
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
        "gate": {"primary": "ac1", "chosen": AC1_CHOSEN, "ac1_target": AC1_TARGET, "p_neg_target": PNEG_TARGET,
                          "kappa_reported_target": KAPPA_PROPOSAL},
        "disagreements": [i for i in both if a[i]["verdict"] != b[i]["verdict"]],
        "calibration": {"n": len(calib), "disagreements": [i for i in calib if a[i]["verdict"] != b[i]["verdict"]]},
        "labelled_before_d4": {i: sorted({x["labeler"] for x in outside if x["id"] == i})
                               for i in sorted({x["id"] for x in outside if x["id"] in a})},
    }
    (data / f"review/{name}_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                                                        encoding="utf-8")
    fmt = lambda x: f"{x:.3f}" if x is not None else "—"
    ci = lambda x: f"[{x[0]:.3f}; {x[1]:.3f}]" if x else "—"
    line = lambda label, v: (f"{label}  n={v['n']:>3}  AC1={fmt(v['ac1'])} {ci(v['ac1_ci95'])}  "
                             f"p_neg={fmt(v['p_neg'])}  đồng ý={fmt(v['agreement'])}  κ={fmt(v['kappa'])}")
    print(f"{len(both)}/{len(a)} dòng cả hai đã gán · chỉ số chính AC1 (chọn sau pilot 07/10/2026)")
    print(line("  toàn tập:   ", result))
    for g, v in result["per_group"].items():
        print(line(f"  {g}:         "[:14], v))
    print(line("  lineage:    ", result["per_lineage"]))
    for v, s in result["per_guideline"].items():
        print(line(f"  v{v}:".ljust(14), s))
    ok = result["ac1"] is not None and result["ac1"] >= AC1_TARGET and (
        result["p_neg"] is not None and result["p_neg"] >= PNEG_TARGET)
    need = result["agreement_needed_for_kappa_target"]
    print(f"  ngưỡng: AC1 >= {AC1_TARGET:.2f} và p_neg >= {PNEG_TARGET:.2f} -> "
          f"{'ĐẠT' if ok else 'CHƯA ĐẠT'}")
    print(f"  κ chỉ báo kèm: ở biên nhãn này κ >= {KAPPA_PROPOSAL:.2f} đòi p_o >= {fmt(need)}"
          f" (tối đa {round((1 - need) * result['n']) if need else '—'} dòng lệch / {result['n']})")
    print(f"  {len(result['disagreements'])} dòng lệch cần hoà giải")
    if calib:
        print(f"  lô 0 hiệu chuẩn: {len(calib)} dòng cả hai đã gán, {len(result['calibration']['disagreements'])} "
              "dòng lệch — không tính vào AC1, đem ra thảo luận cùng luật sư (hướng dẫn §5)")
    if name == "pilot_T6":
        agree = result["n"] - len(result["disagreements"])
        print(f"  cổng pilot: trùng {agree}/{result['n']}, cần >= {PILOT_GATE}/{PILOT_ROWS} -> "
              f"{'ĐẠT' if result['n'] == PILOT_ROWS and agree >= PILOT_GATE else 'CHƯA ĐẠT'}")
    seen = collections.Counter(lab for labs in result["labelled_before_d4"].values() for lab in labs)
    print(f"  {len(result['labelled_before_d4'])} dòng đã có nhãn ngoài D4 trước khi gán (ghi vào biên bản D5): {dict(seen)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("build", "kappa", "pilot", "kiem"))
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--set", default="crosscheck", choices=("crosscheck", "pilot_T6", "kiem"), help="kappa only")
    args = ap.parse_args()
    if args.command == "kappa":
        kappa(args.data, args.set)
    else:
        {"build": build, "pilot": pilot, "kiem": kiem}[args.command](args.data)


if __name__ == "__main__":
    main()
