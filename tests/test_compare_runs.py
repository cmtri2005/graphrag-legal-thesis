import compare_runs


def _row(i, group="T2"):
    return {"id": f"r{i}", "lineage_id": f"L{i}", "group": group, "answerable": True, "short_answer": "đúng",
            "qsource": "silver", "near_identical": False, "repeal_mode": None}


def test_stability_needs_the_same_verdict_in_both_runs():
    c = lambda **v: {"results": {k: {"verdict": x} for k, x in v.items()}}  # noqa: E731
    out = compare_runs.stability(c(F1="ủng hộ", F2="ủng hộ", F3="bác"), c(F1="ủng hộ", F2="không đủ bằng chứng", F3="bác"))
    assert out["F1"]["stable"] and out["F1"]["final"] == "ủng hộ"
    assert not out["F2"]["stable"] and "không đủ bằng chứng" in out["F2"]["final"]
    assert out["F3"]["final"] == "bác"
    assert out["F4"]["final"] == "chưa đủ dữ liệu"


def test_flips_count_right_to_wrong_and_back():
    rows = [_row(i) for i in range(4)]
    mk = lambda *ans: {r["id"]: {"answer": a, "answerable": True} for r, a in zip(rows, ans)}  # noqa: E731
    out = compare_runs.flips(rows, mk("đúng", "đúng", "sai", "đúng"), mk("đúng", "sai", "đúng", "đúng ạ"))["all"]
    assert (out["rows"], out["answer_changed"], out["right_to_wrong"], out["wrong_to_right"]) == (4, 3, 1, 1)
