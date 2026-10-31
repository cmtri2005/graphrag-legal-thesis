from test2_packs import lineage_truth, score, stratum

AB = {"status": "checked", "source": "human", "labeler": "A+B"}


def test_truth_uses_only_independent_labels_and_lineage_level_reasons():
    ok = {**AB, "verdict": "dat", "reasons": []}
    moved = {**AB, "verdict": "khong_dat", "reasons": ["relocation_unclear"]}
    asked = {**AB, "verdict": "khong_dat", "reasons": ["question_leaks"]}
    assert lineage_truth([ok, ok]) == ("tot", [])
    assert lineage_truth([ok, moved]) == ("xau", ["relocation_unclear"])
    assert lineage_truth([ok, asked]) is None                  # a question flaw the filter cannot see
    helped = {**moved, "labeler": "luật sư X, có phiếu Claude hỗ trợ"}
    assert lineage_truth([ok, helped]) is None                 # not blind to Claude
    assert lineage_truth([ok, {**ok, "labeler": "A"}]) is None  # one person is not a final label
    assert lineage_truth([ok, {**moved, "labeler": "luật sư (mẫu agent)"}])[0] == "xau"


def test_stratum_tags():
    assert stratum({"group": "T2", "near_identical": True}) == "T2 gần giống"
    assert stratum({"group": "T6", "repeal_mode": "ancestor"}) == "T6 cấp trên"
    assert stratum({"group": "T6", "repeal_mode": "direct"}) == "T6 đích danh"


def test_score_gate(tmp_path, capsys):
    key = tmp_path / "key.tsv"
    key.write_text("item\tnhom\tvai_tro\tsu_that\tma\n"
                   "x1\tT2\thieu_chuan\txau\tcosmetic_only\nx2\tT2\thieu_chuan\txau\trename_only\n"
                   "g1\tT2\thieu_chuan\ttot\t\nc1\tT3\tung_vien\t\t\n", encoding="utf-8")
    res = tmp_path / "result.tsv"
    res.write_text("item\tquyet_dinh\tma\tcan_cu\tghi_chu\n"
                   "x1\tloai\tcosmetic_only\t\t\nx2\tloai\trename_only\t\t\ng1\tgiu\t\t\t\nc1\tgiu\t\t\t\n",
                   encoding="utf-8")
    assert score(tmp_path, res, key)
    res.write_text(res.read_text(encoding="utf-8").replace("x2\tloai", "x2\tgiu"), encoding="utf-8")
    assert not score(tmp_path, res, key)                       # caught 1/2 < 0.80
    assert "ứng viên được giữ: {'T3': 1}" in capsys.readouterr().out
