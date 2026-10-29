import csv
import json

import pytest

import export_release
from crosscheck import GUIDELINE, KIEM_A_COLUMNS, KIEM_COLUMNS


def _row(lid, as_of, strategy="ranh_gioi", twin_of=None, group="T2", split="dev"):
    return {"id": f"{lid}:{as_of}", "lineage_id": lid, "group": group, "split": split, "as_of_strategy": strategy,
            "twin_of": twin_of, "question": "Hỏi?", "as_of": as_of, "answer": "s) Không kiểm tra.",
            "short_answer": "Phạt tiền 7 triệu", "answerable": True, "version_id": f"version:{lid}:1",
            "target": {"citation": "Điểm s Khoản 3 Điều 16", "lead_in": "3. Phạt tiền 7 triệu với:"},
            "accepted_evidence": [f"asis:{lid}"], "review": {"status": "unchecked"}, "domain": ["x"]}


def _sheet(path, columns, labels):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, columns, delimiter="\t", lineterminator="\n", restval="")
        w.writeheader()
        for rid, verdict, reasons, version in labels:
            w.writerow({"id": rid, "verdict": verdict, "reasons": reasons, "guideline_version": version})


def test_export_publishes_passed_lineages_with_twins_and_counts_the_dropped(tmp_path):
    rel = tmp_path / "derived/vilextime"
    rel.mkdir(parents=True)
    rows = [_row("ok", "2024-01-01"), _row("ok", "2024-01-02"), _row("ok", "2024-03-01", "giua_khoang", "ok:2024-01-01"),
            _row("bad", "2024-01-01"), _row("bad", "2024-01-02"),
            _row("old", "2024-01-01", group="T1"), _row("split", "2024-01-01", group="T1"),
            _row("solo", "2024-01-01", group="T1"), _row("mix", "2024-01-01", group="T1")]
    rel.joinpath("release.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (tmp_path / "review").mkdir()
    g = GUIDELINE
    _sheet(tmp_path / "review/kiem_A.tsv", KIEM_A_COLUMNS,
           [("ok:2024-01-01", "dat", "", g), ("ok:2024-01-02", "dat", "", g), ("bad:2024-01-01", "dat", "", g),
            ("old:2024-01-01", "dat", "", "1.2"), ("split:2024-01-01", "dat", "", g),
            ("solo:2024-01-01", "dat", "", g), ("mix:2024-01-01", "dat", "", g)])
    _sheet(tmp_path / "review/kiem_B.tsv", KIEM_COLUMNS,      # one person is enough; B's D4-era label is not a vote
           [("ok:2024-01-02", "dat", "", g), ("bad:2024-01-02", "khong_dat", "rename_only", g),
            ("split:2024-01-01", "khong_dat", "question_leaks", g), ("solo:2024-01-01", "", "", ""),
            ("mix:2024-01-01", "khong_dat", "other", "1.2")])
    out = tmp_path / "publish"
    m = export_release.export(tmp_path, out)
    main = [json.loads(x) for x in (out / "vilextime.jsonl").open(encoding="utf-8")]
    silver = [json.loads(x) for x in (out / "vilextime_silver.jsonl").open(encoding="utf-8")]
    meta = {json.loads(x)["id"]: json.loads(x) for x in (out / "vilextime_meta.jsonl").open(encoding="utf-8")}
    assert [r["id"] for r in main] == ["ok:2024-01-01", "ok:2024-01-02", "ok:2024-03-01",          # twin goes along
                                       "solo:2024-01-01", "mix:2024-01-01"]
    assert list(main[0]) == list(export_release.MAIN)
    with (out / "vilextime.csv").open(encoding="utf-8-sig", newline="") as f:
        table = list(csv.DictReader(f))
    assert [r["id"] for r in table] == [r["id"] for r in main] and list(table[0]) == list(export_release.MAIN)
    assert table[0]["context"] == main[0]["context"] and table[0]["accepted_evidence"] == "asis:ok"
    assert main[0]["answer"] == "Phạt tiền 7 triệu" and main[0]["context"].startswith("3. Phạt tiền 7 triệu với:\n")
    assert {r["id"] for r in silver} == {"old:2024-01-01", "split:2024-01-01"}   # D4-era label; A/B unsettled
    assert m["dropped_lineages_by_reason"] == {"rename_only": 1} and m["dropped_rows_by_group"] == {"T2": 2}
    assert not meta["mix:2024-01-01"]["review"]["double_labelled"]
    draft = export_release.export(tmp_path, tmp_path / "draft", draft=True)
    assert draft["rows"] == {"main": 7, "silver": 0}                   # everything but the failed lineage
    assert meta["ok:2024-01-02"]["review"]["double_labelled"] and meta["ok:2024-03-01"]["review"]["label_of"] == "ok:2024-01-01"
    assert "answer" not in meta["ok:2024-01-01"] and meta["ok:2024-01-01"]["schema_version"] == "2.0.0"
    with pytest.raises(SystemExit):
        export_release.export(tmp_path, tmp_path / "final", final=True)
    assert not (tmp_path / "final").exists()

    # the lawyer settles the A/B split and the carried label is confirmed: nothing left unchecked
    (tmp_path / "review/hoa_giai_kiem.tsv").write_text(
        "id\tverdict\treasons\tnote\tadjudicator\nsplit:2024-01-01\tdat\t\t\tluật sư\n", encoding="utf-8")
    _sheet(tmp_path / "review/kiem_A.tsv", KIEM_A_COLUMNS,
           [("ok:2024-01-01", "dat", "", g), ("ok:2024-01-02", "dat", "", g), ("bad:2024-01-01", "dat", "", g),
            ("old:2024-01-01", "dat", "", g), ("split:2024-01-01", "dat", "", g),
            ("solo:2024-01-01", "dat", "", g), ("mix:2024-01-01", "dat", "", g)])
    m = export_release.export(tmp_path, tmp_path / "final", final=True)
    assert m["rows"] == {"main": 7, "silver": 0}


def test_agent_priority_q2_and_review_counts(tmp_path):
    rel = tmp_path / "derived/vilextime"
    rel.mkdir(parents=True)
    ids = ("agent_only", "lawyer", "a_dat", "agent_dat", "agree", "sample")
    rel.joinpath("release.jsonl").write_text(
        "".join(json.dumps(_row(i, "2024-01-01", group="T1", split="test")) + "\n" for i in ids), encoding="utf-8")
    review = tmp_path / "review"
    review.mkdir()
    g = GUIDELINE
    _sheet(review / "kiem_A.tsv", KIEM_A_COLUMNS,
           [("lawyer:2024-01-01", "khong_dat", "gold_wrong", g),
            ("a_dat:2024-01-01", "dat", "", g),
            ("agent_dat:2024-01-01", "khong_dat", "question_leaks", g),
            ("agree:2024-01-01", "dat", "", g),
            ("sample:2024-01-01", "dat", "", g)])
    _sheet(review / "kiem_B.tsv", KIEM_COLUMNS, [("agree:2024-01-01", "dat", "", g)])
    (review / "hoa_giai_kiem.tsv").write_text(
        "id\tverdict\treasons\tadjudicator\n"
        "lawyer:2024-01-01\tdat\t\tluật sư\n", encoding="utf-8")
    (review / "luat_su_kiem_agent.tsv").write_text(
        "id\tverdict\treasons\tnote\tadjudicator\n"
        "sample:2024-01-01\tdat\t\t\tluật sư (mẫu agent)\n", encoding="utf-8")
    with (review / "kiem_agent.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["id", "verdict", "reasons", "labeler", "guideline_version"], delimiter="\t")
        w.writeheader()
        for rid, verdict, reasons in [
            ("agent_only", "dat", ""), ("lawyer", "khong_dat", "rename_only"),
            ("a_dat", "khong_dat", "rename_only"), ("agent_dat", "dat", ""),
            ("agree", "khong_dat", "gold_wrong"), ("sample", "khong_dat", "rename_only"),
        ]:
            w.writerow({"id": f"{rid}:2024-01-01", "verdict": verdict, "reasons": reasons,
                        "labeler": "Codex test", "guideline_version": g})

    scope = {f"{i}:2024-01-01": ("T1", "test") for i in ids}
    labels = export_release.final_labels(review, scope)
    # an A/agent disagreement takes the agent's label (29/10, the lawyer's sample); the lawyer still wins
    assert {i: labels[f"{i}:2024-01-01"]["verdict"] for i in ids} == {**dict.fromkeys(ids, "dat"),
                                                                       "a_dat": "khong_dat"}
    assert labels["lawyer:2024-01-01"]["labeler"] == "luật sư"
    assert labels["sample:2024-01-01"]["labeler"] == "luật sư (mẫu agent)"
    assert labels["agree:2024-01-01"]["labeler"] == "A+B"
    assert labels["a_dat:2024-01-01"]["reasons"] == ["rename_only"]
    assert labels["agent_dat:2024-01-01"]["reasons"] == ["question_leaks"]
    assert labels["a_dat:2024-01-01"]["labeler"] == "Codex test"
    assert labels["agent_dat:2024-01-01"]["labeler"] == "Codex test"
    out = tmp_path / "publish"
    manifest = export_release.export(tmp_path, out)
    assert manifest["rows"] == {"main": 5, "silver": 0}
    assert manifest["review_counts"] == {"human_checked": 3, "agent_checked": 3,
                                          "a_agent_disagreement": 2}
    meta = {r["id"]: r for r in map(json.loads, (out / "vilextime_meta.jsonl").open(encoding="utf-8"))}
    assert meta["agent_only:2024-01-01"]["review"]["labeler"] == "Codex test"
    assert "a_dat:2024-01-01" not in meta


def test_agent_counts_only_for_t1_t6_and_one_human_is_not_enough_on_test(tmp_path):
    rel = tmp_path / "derived/vilextime"
    rel.mkdir(parents=True)
    spec = [("t1_agent", "T1", "test"), ("t1_none", "T1", "test"), ("t2_agent", "T2", "test"),
            ("t2_a", "T2", "test"), ("t2_dev_a", "T2", "dev")]
    rel.joinpath("release.jsonl").write_text(
        "".join(json.dumps(_row(i, "2024-01-01", group=g, split=sp)) + "\n" for i, g, sp in spec), encoding="utf-8")
    review = tmp_path / "review"
    review.mkdir()
    g = GUIDELINE
    _sheet(review / "kiem_A.tsv", KIEM_A_COLUMNS, [("t2_a:2024-01-01", "dat", "", g), ("t2_dev_a:2024-01-01", "dat", "", g),
                                                    ("t1_none:2024-01-01", "dat", "", g)])
    _sheet(review / "kiem_B.tsv", KIEM_COLUMNS, [])
    with (review / "kiem_agent.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["id", "verdict", "reasons", "labeler", "guideline_version"], delimiter="\t")
        w.writeheader()
        for rid in ("t1_agent", "t2_agent"):
            w.writerow({"id": f"{rid}:2024-01-01", "verdict": "dat", "reasons": "", "labeler": "Codex", "guideline_version": g})
    scope = {f"{i}:2024-01-01": (gr, sp) for i, gr, sp in spec}
    labels = export_release.final_labels(review, scope)
    status = {i: (labels[f"{i}:2024-01-01"]["status"], labels[f"{i}:2024-01-01"].get("why")) for i, _, _ in spec}
    assert status["t1_agent"][0] == "checked" and labels["t1_agent:2024-01-01"]["source"] == "agent"
    assert status["t1_none"] == ("not_verified", "chờ nhãn agent")            # A alone, T1 waits for the agent
    assert status["t2_agent"] == ("not_verified", export_release.OUT_OF_SCOPE)  # agent label ignored outside T1, T6
    assert status["t2_a"] == ("not_verified", export_release.OUT_OF_SCOPE)      # one person on test is not a check
    assert status["t2_dev_a"][0] == "checked"                                   # dev keeps the one-person rule
    with pytest.raises(SystemExit):                                              # t1_none is still pending
        export_release.export(tmp_path, tmp_path / "final", final=True)
    _sheet(review / "kiem_B.tsv", KIEM_COLUMNS, [("t1_none:2024-01-01", "dat", "", g)])
    m = export_release.export(tmp_path, tmp_path / "final", final=True)         # out-of-scope rows may stay in silver
    assert m["rows"]["silver"] == 2 and m["rows"]["main"] == 3
