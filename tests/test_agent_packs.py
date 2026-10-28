import json

from agent_packs import calibration_verdict, score


def test_calibration_keeps_lot_zero_but_excludes_later_adjudication():
    a = {"lo": "0", "verdict": "dat", "guideline_version": "3.0"}
    b = {"verdict": "khong_dat", "guideline_version": "3.0"}
    lawyer = {"verdict": "khong_dat"}
    assert calibration_verdict(a, b, lawyer) == "khong_dat"
    assert calibration_verdict({**a, "lo": "1"}, b, lawyer) is None
    assert calibration_verdict({**a, "lo": "1"}, {**b, "verdict": "dat"}, lawyer) == "dat"


def test_score_reads_an_explicit_key_outside_the_pack_tree(tmp_path, capsys):
    packs = tmp_path / "packs"
    packs.mkdir()
    (packs / "pack_01.jsonl").write_text(json.dumps({"id": "r1"}) + "\n", encoding="utf-8")
    key = tmp_path / "separate" / "key_calib.tsv"
    key.parent.mkdir()
    key.write_text("id\tgroup\tverdict\nr1\tT1\tdat\n", encoding="utf-8")
    result = tmp_path / "result.tsv"
    result.write_text("id\tverdict\nr1\tdat\n", encoding="utf-8")

    score(packs, result, key)
    assert "hiệu chuẩn 1/1; id lạ: 0" in capsys.readouterr().out
