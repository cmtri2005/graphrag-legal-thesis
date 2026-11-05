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


def test_xn5_to_xn7_are_outside_the_holm_family():
    from confirm_vilextime import EXPLORATORY, FAMILY
    assert [t[0] for t in FAMILY] == ["XN1", "XN2", "XN3", "XN4", "XN8", "XN9"]
    assert EXPLORATORY == {"XN5", "XN6", "XN7"} and len(TESTS) == 9


import pytest


@pytest.mark.parametrize('lineages, expected_size', [(19, 6), (20, 7)])
def test_final_family_holm_counts_and_exploratory_threshold(tmp_path, monkeypatch, lineages, expected_size):
    import json
    import sys
    import confirm_vilextime as confirm
    from report_results import confirm_section
    rows = [_row(f'L{i}', 'T6', answerable=False) for i in range(lineages)]
    tests, exploratory = confirm.final_family(rows, 'P')
    assert len(tests) == 8 and len(tests) - len(exploratory) == expected_size
    assert 'F8' in exploratory and tests[2][3] == 'wrong_version' and tests[2][7] == -1
    assert tests[0][6] == ('b4', 'P') and tests[6][6] == ('b7pp', 'P')
    release = tmp_path / 'release.jsonl'
    release.write_text('[]')
    for system in {s for t in tests for s in t[6]}:
        (tmp_path / f'{system}.jsonl').write_text('')
    monkeypatch.setattr(confirm, 'load_rows', lambda p: [{**r, 'split': 'dev'} for r in rows])
    monkeypatch.setattr(confirm, 'distractors', lambda rows: {})
    monkeypatch.setattr(confirm, 'units_of', lambda *a: ({}, set(), set()))
    def result(test, *args):
        return dict(estimate=0.1, ci95=[0.01, 0.2], p=int(test[0][1:]) / 1000,
                    rows={s: lineages for s in test[4]}, lineages={s: lineages for s in test[4]})
    monkeypatch.setattr(confirm, 'run', result)
    out = tmp_path / 'confirm.json'
    monkeypatch.setattr(sys, 'argv', ['confirm', '--split', 'dev', '--family', 'final', '--proposed', 'P',
        '--release', str(release), '--generation', str(tmp_path), '--retrieval', str(tmp_path), '--out', str(out)])
    confirm.main()
    data = json.loads(out.read_text())
    assert data['tests_run'] == data['family_size'] == expected_size
    assert data['results']['F1']['p_holm'] == pytest.approx(expected_size * .001)
    assert data['results']['F2']['p_holm'] == pytest.approx((expected_size - 1) * .002)
    assert data['results']['F7']['p_holm'] is None if lineages < 20 else data['results']['F7']['p_holm'] is not None
    text = '\n'.join(confirm_section(out))
    assert f'Holm trên {expected_size}/{expected_size}' in text
    assert 'F1–F8' in text and ('F7 thăm dò' in text) == (lineages < 20)
