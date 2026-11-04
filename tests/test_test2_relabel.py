"""Gán lại test 2 (lời dặn v2): chỉ các phép dễ sai có hậu quả."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/review"))
import test2_relabel as R  # noqa: E402


def human(verdict="dat", who="A+B", reasons=()):
    return {"status": "checked", "source": "human", "labeler": who, "verdict": verdict, "reasons": list(reasons)}


def test_truth_needs_every_row_and_independent_people():
    assert R.truth_of([human(), human()], 2) == "dat"
    assert R.truth_of([human(), human("khong_dat", reasons=["question_leaks"])], 2) == "khong_dat"
    assert R.truth_of([human()], 2) is None                                       # thiếu một mốc
    assert R.truth_of([human(), human(who="A")], 2) is None                       # nhãn một người
    assert R.truth_of([human(), human(who="luật sư X, có phiếu Claude hỗ trợ")], 2) is None


def test_silver_refuses_unadjudicated_split():
    a = {"x": {"q1": "dung", "q2": "co", "q3": "co", "q4": "khong", "verdict": "dat"}}
    b = {"x": {**a["x"], "q3": "khong", "verdict": "khong_dat"}}
    with pytest.raises(SystemExit):
        R.silver(a, b, {})
    assert R.silver(a, a, {})["x"]["labeler"].endswith("(A=B)")
    assert R.silver(a, b, {"x": b["x"]})["x"]["verdict"] == "khong_dat"


def test_subset_keeps_only_dat_lineages_and_counts_those_without_predictions(tmp_path):
    release = tmp_path / "r.jsonl"
    release.write_text("".join(json.dumps({"id": i, "lineage_id": l}) + "\n" for i, l in (("1", "a"), ("2", "a"), ("3", "b"))))
    labels = {"a": {"verdict": "dat"}, "b": {"verdict": "khong_dat"}, "c": {"verdict": "dat"}}
    out = tmp_path / "s.jsonl"
    got = R.subset(release, labels, out)
    assert (got["giu"], got["bo"], got["dong_giu"], got["dat_v2_ngoai_release"]) == (1, 1, 2, 1)
    assert [json.loads(s)["id"] for s in out.read_text().splitlines()] == ["1", "2"]
    with pytest.raises(SystemExit):
        R.subset(release, {"a": {"verdict": "dat"}}, out)                         # lineage thiếu nhãn


def test_agreement_gate_uses_both_thresholds():
    assert R.agreement(["dat", "khong_dat"] * 10, ["dat", "khong_dat"] * 10)["dat_chuan"]
    assert not R.agreement(["dat"] * 19 + ["khong_dat"], ["dat"] * 20)["dat_chuan"]   # AC1 cao, p_neg 0
