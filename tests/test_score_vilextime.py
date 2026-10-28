"""ViLexTime scorer on hand-made rows: formulas 6–9 of the proposal and the 28/09 choices."""
import json

from score_vilextime import load_rows, nearest, probe, resolve, score

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


def test_published_release_restores_lead_in_and_written_citation(tmp_path):
    release = tmp_path / "vilextime.jsonl"
    release.write_text(json.dumps({**ROWS[0], "answer": "Phạt tiền từ 1 đến 2 triệu đồng",
                                   "context": "1. Phạt tiền từ 1 đến 2 triệu đồng.",
                                   "citation": "Khoản 1 Điều 5"}) + "\n")
    (tmp_path / "vilextime_meta.jsonl").write_text(json.dumps({
        "id": "r1", "target": {"lead_in": "1. Phạt tiền từ 1 đến 2 triệu đồng.",
                               "citation": "Khoản 1 Điều 5", "doc_type": "Luật",
                               "law_id": "1/2019/QH14"}, "near_identical": True,
        "repeal_mode": None}) + "\n")
    row = load_rows(release)[0]
    assert row["near_identical"] is True
    chain = {"provision:P": [{"id": "version:P:1", "ordinal": 1,
                               "text": "1. Phạt tiền từ 1 đến 2 triệu đồng.",
                               "effective_intervals": [{"start": "2019-01-01", "end": "2021-01-01"}]}]}
    assert score([row], probe("oracle", [row], chain), UNITS)["accuracy"] == 1
    assert probe("text_cite", [row], chain)["r1"]["citations"] == ["Khoản 1 Điều 5 Luật 1/2019/QH14"]


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


def test_only_test_is_scored_by_default_once_the_release_is_split():
    from score_vilextime import default_split

    assert default_split(ROWS) is None                       # not split yet: every row
    assert default_split([{**ROWS[0], "split": "dev"}, {**ROWS[1], "split": "test"}]) == "test"


def _contrast(rows):
    from score_vilextime import distractors

    extra = distractors(rows)
    return [{**r, "_distractors": extra.get(r["id"], [])} for r in rows]


def test_an_answer_that_recites_every_version_is_wrong_and_breaks_the_pair():
    rows = _contrast([{**r, "answer": a} for r, a in zip(ROWS, ("từ 1 đến 2 triệu đồng", "3 triệu đồng", None))])
    assert rows[0]["_distractors"] == ["3 triệu đồng"] and rows[1]["_distractors"] == ["2 triệu đồng", "từ 1"]
    hedge = _pred("Trước 2021: từ 1 đến 2 triệu đồng; sau đó 3 triệu đồng.", ["version:P:1", "version:P:2"])
    s = score(rows[:2], {"r1": hedge, "r2": hedge}, UNITS)
    assert (s["accuracy"], s["tcs"]) == (0, 0)
    assert (s["accuracy_lenient"], s["tcs_lenient"], s["contrast_rows"]) == (1, 1, 2)
    right = score(rows[:2], {"r1": _pred("từ 1 đến 2 triệu đồng"), "r2": _pred("3 triệu đồng")}, UNITS)
    assert (right["accuracy"], right["tcs"]) == (1, 1)


def test_a_written_citation_resolves_to_its_provision_even_when_numbers_repeat():
    from score_vilextime import parse_citation, resolve_written

    documents = {"109/2026/NĐ/CP": [("document:A", "2026-05-01")],
                 "81/CP": [("document:B93", "1993-01-01"), ("document:B95", "1995-11-01")]}
    trees = {"document:A": [("provision:D16", None, "Article", "16"), ("provision:K3", "provision:D16", "Clause", "3"),
                            ("provision:s", "provision:K3", "Point", "s"), ("provision:K4", "provision:D16", "Clause", "4")],
             "document:B93": [("provision:B93.2", None, "Article", "2")],
             "document:B95": [("provision:B95.2", None, "Article", "2"), ("provision:B95.2.1", "provision:B95.2", "Clause", "1")]}
    assert resolve_written("Điểm s Khoản 3 Điều 16 Nghị định 109/2026/NĐ-CP", documents, trees) == ["provision:s"]
    assert resolve_written("khoản 3 điều 16 Nghị định số 109/2026/NĐ-CP.", documents, trees) == ["provision:K3"]
    assert resolve_written("Điều 2 Nghị định 81-CP", documents, trees) is None          # 1993 or 1995?
    assert resolve_written("Điều 2 Nghị định 81-CP năm 1995", documents, trees) == ["provision:B95.2"]
    assert resolve_written("Khoản 1 Điều 2 Nghị định 81/CP", documents, trees) == ["provision:B95.2.1"]   # one path
    assert resolve_written("Nghị định 109/2026/NĐ-CP", documents, trees) is None        # no Điều: no provision
    assert resolve_written("Điều 99 Nghị định 109/2026/NĐ-CP", documents, trees) is None
    documents["19/2012/QH13"] = [("document:L1", "2012-11-20"), ("document:L2", "2012-11-20")]   # the portal twice
    trees |= {"document:L1": [("provision:L1.13", None, "Article", "13")],
              "document:L2": [("provision:L2.13", None, "Article", "13")]}
    assert resolve_written("Điều 13 Luật 19/2012/QH13", documents, trees) == ["provision:L1.13", "provision:L2.13"]
    assert resolve_written("Điểm a Khoản 1 Điều 16 Thông tư 08 /2024/TT-BTNMT", documents, trees) is None
    assert parse_citation("Điểm a Khoản 1 Điều 6 Thông tư 08 /2024/TT-BTNMT")[0] == "08/2024/TT/BTNMT"


def test_a_written_citation_is_checked_for_force_but_names_no_version():
    units = {**UNITS, "Khoản 1 Điều 5 Luật P": [("provision:P", "any", [("2019-01-01", "2021-01-01")]),
                                                ("provision:P", "any", [("2021-01-01", None)])],
             "Điều 9 Luật Q": [("provision:Q", "any", [("2019-01-01", "2021-06-01")])]}
    s = score(ROWS, {"r1": _pred("từ 1 đến 2 triệu đồng", ["Khoản 1 Điều 5 Luật P"]),
                     "r2": _pred("3 triệu đồng", ["Điều 7 Luật Không Có"]),
                     "r3": _pred(None, ["Điều 9 Luật Q"], answerable=False)}, units)
    assert (s["tver"], s["cited_rows"]) == (0.5, 2)       # r1 in force, r3 cites a repealed provision; r2 unresolved
    assert s["vcr"] is None                                # no citation names a version
    assert s["tver_strict"] == 2 / 3 and s["citation_coverage"] == 2 / 3


def test_no_citation_escapes_tver_but_not_tver_strict():
    s = score(ROWS[:2], {"r1": _pred("từ 1 đến 2 triệu đồng"), "r2": _pred("3 triệu đồng")}, UNITS)
    assert (s["tver"], s["vcr"], s["tver_strict"], s["citation_coverage"]) == (None, None, 1, 0)


def test_scorer_check_probes():
    chain = [{"id": "version:P:1", "ordinal": 1, "text": "Phạt tiền từ 1 đến 2 triệu đồng",
              "effective_intervals": [{"start": "2019-01-01", "end": "2021-01-01"}]},
             {"id": "version:P:2", "ordinal": 2, "text": "Phạt tiền 3 triệu đồng",
              "effective_intervals": [{"start": "2021-01-01", "end": None}]}]
    rows = _contrast([{**r, "answer": a, "target": {**r["target"], "citation": c, "doc_type": "Luật", "law_id": "1/2019/QH14"}}
                      for r, a, c in zip(ROWS, (chain[0]["text"], chain[1]["text"], None),
                                         ("Khoản 1 Điều 5", "Khoản 1 Điều 5", "Điều 9"))])
    chains = {"provision:P": chain, "provision:Q": [{**chain[0], "id": "version:Q:1"}]}
    hedge = score(rows, probe("hedge", rows, chains), UNITS)
    assert (hedge["accuracy"], hedge["tcs"], hedge["accuracy_lenient"]) == (0, 0, 2 / 3)
    no_cite = score(rows, probe("no_cite", rows, chains), UNITS)
    assert (no_cite["accuracy"], no_cite["tver"], no_cite["tver_strict"]) == (1, None, 1)
    text = probe("text_cite", rows, chains)
    assert text["r1"]["citations"] == ["Khoản 1 Điều 5 Luật 1/2019/QH14"] and text["r3"]["answerable"] is False
    assert score(rows, probe("oracle", rows, chains), UNITS)["accuracy"] == 1


def test_citing_accepted_evidence_is_never_a_validity_error():
    ended_actor = {**UNITS, "asis:provision:S": [("provision:S", 1, [("2018-01-01", "2020-01-01")])]}
    row = {**ROWS[2], "id": "late", "as_of": "2022-06-01", "accepted_evidence": ["asis:provision:S"]}
    s = score([row], {"late": _pred(None, ["asis:provision:S"], answerable=False)}, ended_actor)
    assert (s["tver"], s["accuracy"]) == (0, 1)       # the sentence that ended it, though its own document ended


def test_t5_is_scored_on_its_own_row_and_left_out_of_all():
    from score_vilextime import report

    t5 = {**ROWS[0], "id": "r5", "group": "T5"}
    preds = {"r1": _pred("từ 1 … 2 triệu đồng", ["asis:provision:P"]), "r5": _pred("sai", [])}
    rep = report([ROWS[0], t5], preds, UNITS, None)["giua_khoang"]
    assert rep["all"] == rep["T2"] and rep["all"]["accuracy"] == 1.0
    assert rep["T5"]["accuracy"] == 0.0
    assert report([t5], preds, UNITS, None)["giua_khoang"]["T5"]["accuracy"] == 0.0   # a T5-only strategy


def test_wrong_version_reads_another_versions_content_from_the_text():
    rows = _contrast([{**r, "answer": a} for r, a in zip(ROWS, ("từ 1 đến 2 triệu đồng", "3 triệu đồng", None))])
    hedge = _pred("Trước 2021: từ 1 đến 2 triệu đồng; sau đó 3 triệu đồng.")   # no citation: VCR cannot see it
    s = score(rows, {"r1": hedge, "r2": hedge, "r3": _pred(None, answerable=False)}, UNITS)
    assert (s["wrong_version"], s["vcr"]) == (1, None)
    s = score(rows, {"r1": _pred("từ 1 đến 2 triệu đồng"), "r2": _pred(None, answerable=False)}, UNITS)
    assert s["wrong_version"] == 0         # the right version, and an abstention, recite no other version


def test_intervals_resample_whole_lineages_and_two_systems_are_paired():
    from score_vilextime import difference

    rows = [_row(f"{p}{d}", "T1", f"provision:{p}", f"version:{p}:1", "2020-01-01", [], "x") for p in "AB" for d in "12"]
    right = {r["id"]: _pred("x") for r in rows}
    half = {r["id"]: _pred("x" if r["lineage_id"] == "provision:A" else "y") for r in rows}
    a, b = score(rows, right, {}, draws=300), score(rows, half, {}, draws=300)
    assert {d["accuracy"] for d in b["_draws"]} == {0, 0.5, 1}   # never 0.25 or 0.75: a lineage moves whole
    assert (a["ci95"]["accuracy"], b["ci95"]["accuracy"]) == ([1, 1], [0, 1])
    d = difference(a, b)
    assert (d["accuracy"], d["ci95"]["accuracy"]) == (-0.5, [-1, 0])
    assert 0.3 < d["p"]["accuracy"] < 0.7               # a quarter of the resamples draw lineage A twice
    same = difference(b, score(rows, half, {}, draws=300))
    assert (same["ci95"]["accuracy"], same["p"]["accuracy"]) == ([0, 0], 1)   # the same resamples
