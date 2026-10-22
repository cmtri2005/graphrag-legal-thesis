import csv
import json

import pytest

import export_release
from crosscheck import GUIDELINE, KIEM_A_COLUMNS, KIEM_COLUMNS


def _row(lid, as_of, strategy="ranh_gioi", twin_of=None, group="T2"):
    return {"id": f"{lid}:{as_of}", "lineage_id": lid, "group": group, "split": "test", "as_of_strategy": strategy,
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
