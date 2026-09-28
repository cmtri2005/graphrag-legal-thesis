"""ViLexTime scorer on hand-made rows: formulas 6–9 of the proposal and the 28/09 choices."""
import json

from score_vilextime import nearest, probe, resolve, score

# provision P: v1 in force 2019-01-01..2021-01-01, v2 from then (written by event E2);
# provision Q: v1 until 2021-06-01, when instruction R repealed it.
UNITS = {
    "version:P:1": [("provision:P", 1, [("2019-01-01", "2021-01-01")])],
    "asis:provision:P": [("provision:P", 1, [("2019-01-01", "2021-01-01")])],
    "version:P:2": [("provision:P", 2, [("2021-01-01", None)])],
    "asis:event:E2": [("provision:P", 2, [("2021-01-01", None)])],
    "version:Q:1": [("provision:Q", 1, [("2019-01-01", "2021-06-01")])],
    "asis:event:R": [("provision:Q", None, [("2021-06-01", None)])],
}


def _row(id_, group, lineage, version, as_of, accepted, short, strategy="giua_khoang"):
    return {"id": id_, "group": group, "lineage_id": lineage, "version_id": version, "as_of": as_of,
            "as_of_strategy": strategy, "accepted_evidence": accepted, "answerable": version is not None,
            "short_answer": short, "split": None, "target": {"lead_in": "1. Phạt tiền:"}}


ROWS = [
    _row("r1", "T2", "provision:P", "version:P:1", "2020-01-01", ["asis:provision:P"], "từ 1 … 2 triệu đồng"),
    _row("r2", "T2", "provision:P", "version:P:2", "2021-06-01", ["asis:event:E2"], "3 triệu đồng"),
    _row("r3", "T6", "provision:Q", None, "2022-01-01", ["asis:event:R"], None),
]


def _pred(answer=None, cites=(), retrieved=None, answerable=True):
    return {"answer": answer, "answerable": answerable, "citations": list(cites),
            "retrieved": list(cites if retrieved is None else retrieved)}


def test_the_gold_scores_perfectly():
    preds = {"r1": _pred("Phạt tiền từ 1 đến 2 triệu đồng.", ["version:P:1"]),
             "r2": _pred("3 triệu đồng", ["asis:event:E2"]),
             "r3": _pred(None, ["asis:event:R"], answerable=False)}
    s = score(ROWS, preds, UNITS)
    assert (s["recall@1"], s["tv_recall@1"], s["mrr"], s["accuracy"], s["tcs"]) == (1, 1, 1, 1, 1)
    assert (s["tver"], s["vcr"], s["cited_rows"]) == (0, 0, 3)
    assert s["em"] == 0.5          # r2 exact after normalisation; r1 has words between the spans


def test_the_right_provision_at_the_wrong_version():
    s = score(ROWS[:1], {"r1": _pred("3 triệu đồng", ["version:P:2"], ["version:P:2", "asis:provision:P"])}, UNITS)
    assert (s["recall@1"], s["mrr"]) == (1, 1)            # the unit, any version
    assert (s["tv_recall@1"], s["tv_recall@5"]) == (0, 1)  # the version in force only at rank 2
    assert (s["tver"], s["vcr"], s["accuracy"]) == (1, 1, 0)


def test_a_repealed_provision_is_right_only_when_the_system_abstains():
    cited_dead = score(ROWS[2:], {"r3": _pred("văn bản cũ", ["version:Q:1"])}, UNITS)
    assert (cited_dead["accuracy"], cited_dead["tver"], cited_dead["vcr"]) == (0, 1, 1)
    assert cited_dead["em"] is None                        # no EM/F1 on rows without an answer
    abstained = score(ROWS[2:], {"r3": _pred(None, ["asis:event:R"], answerable=False)}, UNITS)
    assert (abstained["accuracy"], abstained["tv_recall@1"], abstained["tver"]) == (1, 1, 0)


def test_a_citation_the_corpus_does_not_have_is_not_in_force_and_uncited_rows_are_not_counted():
    s = score(ROWS, {"r1": _pred("từ 1 đến 2 triệu đồng", ["version:Z:9"]), "r2": _pred("3 triệu đồng")}, UNITS)
    assert (s["cited_rows"], s["tver"], s["vcr"]) == (1, 1, 0)


def test_tcs_needs_both_dates_of_a_pair():
    right = _pred("từ 1 đến 2 triệu đồng", ["version:P:1"])
    assert score(ROWS[:2], {"r1": right, "r2": _pred("1 đến 2 triệu", ["version:P:1"])}, UNITS)["tcs"] == 0
    assert score(ROWS[:2], {"r1": right, "r2": _pred("3 triệu đồng")}, UNITS)["tcs"] == 1


def test_an_amendment_stands_for_the_version_it_wrote_and_a_repeal_for_the_repeal(tmp_path):
    lines = [
        {"id": "version:P:1", "provision_id": "provision:P", "ordinal": 1, "created_by_event_id": None,
         "ended_by_event_id": "event:E2", "effective_intervals": [{"start": "2019-01-01", "end": "2021-01-01"}]},
        {"id": "version:P:2", "provision_id": "provision:P", "ordinal": 2, "created_by_event_id": "event:E2",
         "ended_by_event_id": None, "effective_intervals": [{"start": "2021-01-01", "end": None}]},
        {"id": "version:Q:1", "provision_id": "provision:Q", "ordinal": 1, "created_by_event_id": None,
         "ended_by_event_id": "event:R", "effective_intervals": [{"start": "2019-01-01", "end": "2021-06-01"}]},
    ]
    (tmp_path / "derived").mkdir()
    (tmp_path / "derived/versions.jsonl").write_text("".join(json.dumps(v, separators=(",", ":")) + "\n" for v in lines))
    units = resolve(tmp_path, {"asis:provision:P", "asis:event:E2", "asis:event:R", "version:P:2", "version:X:1"})
    assert units["asis:provision:P"] == [("provision:P", 1, [("2019-01-01", "2021-01-01")])]
    assert units["asis:event:E2"] == [("provision:P", 2, [("2021-01-01", None)])]
    assert units["asis:event:R"] == [("provision:Q", None, [("2021-06-01", None)])]
    assert "version:X:1" not in units


def test_probes_choose_versions_by_their_rule():
    chain = [{"id": "version:P:1", "ordinal": 1, "text": "từ 1 đến 2 triệu đồng",
              "effective_intervals": [{"start": "2019-01-01", "end": "2021-01-01"}]},
             {"id": "version:P:2", "ordinal": 2, "text": "3 triệu đồng",
              "effective_intervals": [{"start": "2021-01-01", "end": None}]}]
    assert nearest(chain, "2020-12-31")["id"] == "version:P:2"   # a day before the change: the trap
    rows = ROWS[:1] + ROWS[2:]
    chains = {"provision:P": chain, "provision:Q": [{**chain[0], "id": "version:Q:1"}]}
    oracle, latest = probe("oracle", rows, chains), probe("latest", rows, chains)
    assert oracle["r1"]["citations"] == ["version:P:1"] and oracle["r3"]["answerable"] is False
    assert latest["r1"]["citations"] == ["version:P:2"] and latest["r3"]["answerable"] is True
    assert score(rows, oracle, UNITS)["accuracy"] == 1
