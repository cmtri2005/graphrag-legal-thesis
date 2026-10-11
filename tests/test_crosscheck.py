"""Agreement on the D4 cross-check: AC1 as the gate, Cohen κ reported beside it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))
from crosscheck import (  # noqa: E402
    AC1_TARGET, PNEG_TARGET, agreement_needed, bootstrap_ci, cohen_kappa, gwet_ac1, pair_scores,
    specific_agreement,
)


def test_kappa_matches_a_hand_computed_case():
    # 10 items, 7 agree -> po = 0.7; A has 6 dat, B has 7 -> pe = 0.6*0.7 + 0.4*0.3 = 0.54
    a = ["dat"] * 5 + ["khong_dat"] * 2 + ["dat", "khong_dat", "khong_dat"]
    b = ["dat"] * 5 + ["khong_dat"] * 2 + ["khong_dat", "dat", "dat"]
    assert abs(cohen_kappa(a, b) - (0.7 - 0.54) / (1 - 0.54)) < 1e-9


def test_kappa_edges():
    assert cohen_kappa(["dat", "khong_dat"], ["dat", "khong_dat"]) == 1.0
    assert cohen_kappa(["dat", "dat"], ["dat", "dat"]) is None       # all chance: undefined
    assert cohen_kappa([], []) is None


def test_ac1_stays_high_when_both_raters_say_dat_almost_always():
    # 20 items, both say dat on 18, disagree on 2: raw agreement 0.9, κ collapses, AC1 does not.
    a = ["dat"] * 19 + ["khong_dat"]
    b = ["dat"] * 18 + ["khong_dat", "dat"]
    assert cohen_kappa(a, b) < 0                       # the κ paradox on a skewed sample
    assert gwet_ac1(a, b) > 0.85
    assert gwet_ac1(["dat", "khong_dat"], ["dat", "khong_dat"]) == 1.0


def test_p_neg_reports_agreement_on_the_verdict_that_drops_a_row():
    """`dat` agreement is nearly free at this prevalence; `khong_dat` is the claim."""
    a = ["dat"] * 17 + ["khong_dat"] * 3
    b = ["dat"] * 18 + ["khong_dat"] * 2          # they overlap on 2 of the khong_dat rows

    got = specific_agreement(a, b)
    assert got["dat"] > 0.9                        # the easy half
    assert got["khong_dat"] == 2 * 2 / (3 + 2)     # 2 * both / (A's + B's)
    assert specific_agreement(["dat"], ["khong_dat"]) == {"dat": 0.0, "khong_dat": 0.0}


def test_kappa_carries_the_agreement_its_target_would_need():
    """The prevalence paradox, as a number rather than as an argument.

    At the D4 marginals κ ≥ 0.60 needs p_o ≥ 0.843, and raters who both settle
    near 85% `dat` need p_o ≥ 0.898 — at most ~30 disagreements in 300. No extra
    calibration moves that, which is why AC1 is the pre-registered gate.
    """
    skewed = (["dat"] * 85 + ["khong_dat"] * 15, ["dat"] * 85 + ["khong_dat"] * 15)
    needed = agreement_needed(*skewed, 0.60)
    assert 0.89 < needed < 0.91

    balanced = agreement_needed(["dat"] * 50 + ["khong_dat"] * 50,
                                ["dat"] * 50 + ["khong_dat"] * 50, 0.60)
    assert needed > balanced, "biên lệch phải đòi p_o cao hơn biên cân"
    assert agreement_needed([], [], 0.60) is None


def test_the_bootstrap_interval_is_seeded_and_brackets_the_point_estimate():
    a = ["dat"] * 40 + ["khong_dat"] * 10
    b = ["dat"] * 38 + ["khong_dat"] * 12

    low, high = bootstrap_ci(a, b, gwet_ac1, draws=200)
    assert low <= gwet_ac1(a, b) <= high
    assert bootstrap_ci(a, b, gwet_ac1, draws=200) == [low, high]   # seeded: reruns match
    assert bootstrap_ci(["dat"], ["dat"], gwet_ac1) is None         # one item: no interval


def test_perfect_agreement_passes_the_preregistered_gate_and_a_skewed_split_does_not():
    perfect = ["dat"] * 40 + ["khong_dat"] * 10
    scored = pair_scores(perfect, list(perfect))
    assert scored["ac1"] >= AC1_TARGET and scored["p_neg"] >= PNEG_TARGET

    # agree on every `dat`, never on `khong_dat`: p_o 0.80 yet the gate must fail
    missed = pair_scores(["dat"] * 40 + ["khong_dat"] * 10, ["dat"] * 50)
    assert missed["agreement"] == 0.8 and missed["p_neg"] == 0.0
    assert missed["p_neg"] < PNEG_TARGET


def _release_row(lid, group, as_of, question="Hỏi?", **extra):
    return {"id": f"vilextime:{group}:{lid}:{as_of}", "group": group, "lineage_id": lid, "question": question,
            "as_of": as_of, "as_of_strategy": "ranh_gioi", "answer": "Đáp.", "no_answer_reason": None,
            "changed_span": "", "valid_from": "2020-01-01", "valid_to": None, "source_url": "u",
            "target": {"lead_in": "", "citation": "Điều 1", "law_id": "1/2020/TT"}, **extra}


def test_t6_takes_what_t5_leaves_of_150_in_the_release_proportion():
    from crosscheck import targets

    rows = {"t5": [{"group": "T5"}] * 38,
            **{f"a{i}": [{"group": "T6", "repeal_mode": "ancestor"}] * 2 for i in range(150)},
            **{f"d{i}": [{"group": "T6", "repeal_mode": "direct"}] * 2 for i in range(44)}}
    t = targets(rows)
    assert (t[("T6", "ancestor")], t[("T6", "direct")]) == (86, 26) and t[("T5", None)] is None


def test_build_keeps_a_label_only_with_its_question_and_answer_and_saves_the_old_files(tmp_path):
    import csv
    import json

    import pytest
    from crosscheck import COLUMNS, build

    (tmp_path / "derived/vilextime").mkdir(parents=True)
    (tmp_path / "review").mkdir()
    rows = [_release_row("p", "T2", "2021-01-01"), _release_row("p", "T2", "2021-01-02"),
            _release_row("q", "T3", "2021-01-01", question="Mới?")]
    (tmp_path / "derived/vilextime/release.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    for name, extra in (("crosscheck_A.tsv", ["adjudicated"]), ("crosscheck_B.tsv", [])):
        with (tmp_path / "review" / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, COLUMNS + extra, delimiter="\t", lineterminator="\n", restval="")
            w.writeheader()
            # p was T4 when it was labelled: the id changed, the lineage and date did not
            w.writerow({"id": "vilextime:T4:p:2021-01-01", "lineage_id": "p", "as_of": "2021-01-01",
                        "question": "Hỏi?", "answer": "Đáp.", "verdict": "dat"})
            w.writerow({"id": rows[2]["id"], "lineage_id": "q", "as_of": "2021-01-01", "question": "Cũ?",
                        "answer": "Đáp.", "verdict": "khong_dat"})
    build(tmp_path, today="20261011")
    for name in ("crosscheck_A", "crosscheck_B"):
        assert (tmp_path / f"review/{name}.20261011.tsv").exists()
        got = {r["id"]: r["verdict"] for r in csv.DictReader((tmp_path / f"review/{name}.tsv").open(), delimiter="\t")}
        assert got == {rows[0]["id"]: "dat", rows[1]["id"]: "", rows[2]["id"]: ""}   # q's question changed
    with pytest.raises(SystemExit):
        build(tmp_path, today="20261011")                                             # never overwrite a saved copy


def test_export_refuses_only_when_the_workbook_holds_labels_not_yet_imported(tmp_path):
    import csv

    import pytest
    from openpyxl import load_workbook

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))
    from crosscheck import COLUMNS
    from crosscheck_xlsx import SHEET, export

    (tmp_path / "review").mkdir()
    for who, extra in (("A", ["adjudicated"]), ("B", [])):
        with (tmp_path / f"review/crosscheck_{who}.tsv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, COLUMNS + extra, delimiter="\t", lineterminator="\n", restval="")
            w.writeheader()
            w.writerow({"id": "r1", "lineage_id": "p", "question": "Hỏi?", "verdict": "dat"})   # carried over
            w.writerow({"id": "r2", "lineage_id": "q", "question": "Hỏi?"})
    export(tmp_path)                                   # a label in the TSV alone does not block
    path = tmp_path / "review/crosscheck_A.xlsx"
    wb = load_workbook(path)
    ws = wb[SHEET]
    col = [c.value for c in ws[1]].index("verdict") + 1
    rows = {ws.cell(r, 1).value: r for r in range(2, ws.max_row + 1)}
    assert ws.cell(rows["r1"], col).protection.locked and not ws.cell(rows["r2"], col).protection.locked
    ws.cell(rows["r2"], col, "khong_dat")             # labelled in the workbook, not imported yet
    wb.save(path)
    with pytest.raises(SystemExit):
        export(tmp_path)
