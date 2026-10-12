"""ADR 0005's confirmatory tests: Holm, the verdict rule, and the three kinds of resampling."""
from confirm_vilextime import TESTS, holm, run, verdict


def test_holm_multiplies_by_the_tests_left_and_stays_monotone():
    assert holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06}


def test_a_hypothesis_is_supported_only_in_its_predicted_direction():
    assert verdict(0.2, 0.01, +1) == "ủng hộ"
    assert verdict(0.2, 0.01, -1) == "bác"           # significant, but the wrong way
    assert verdict(0.2, 0.06, +1) == "không đủ bằng chứng"


def _row(lineage, group, near=False, answerable=True):
    return {"id": f"{lineage}:{group}", "lineage_id": lineage, "group": group, "near_identical": near,
            "repeal_mode": None, "answerable": answerable, "version_id": f"version:{lineage}:1",
            "as_of": "2020-01-01", "as_of_strategy": "giua_khoang", "accepted_evidence": [], "short_answer": "x",
            "target": {}}


def test_each_kind_of_test_runs_on_its_slices():
    rows = [_row(f"L{i}", g, near=i % 2 == 0) for i, g in enumerate(["T2", "T2", "T3", "T6"] * 5)]
    right = {r["id"]: {"answer": "x", "retrieved": [r["version_id"]], "citations": [r["version_id"]]} for r in rows}
    wrong = {r["id"]: {"answer": "y", "retrieved": [], "citations": []} for r in rows}
    by = {t[0]: t for t in TESTS}
    xn1 = run(by["XN1"], rows, {"b7": wrong, "b7pp": right}, {}, draws=200)
    assert xn1["estimate"] == 1 and xn1["ci95"] == [1, 1] and xn1["p"] == 0
    xn7 = run(by["XN7"], rows, {"b7": wrong, "proposed": right}, {}, draws=200)
    assert xn7["estimate"] == 0 and xn7["rows"] == {"t6": 5, "t2_t3": 15}   # the same gain on both slices
