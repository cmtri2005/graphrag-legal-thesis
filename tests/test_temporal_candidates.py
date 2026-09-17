from build_temporal_candidates import _tsv_cell, effective_to_candidate

TARGET = {"effFrom": "2015-01-01T00:00:00", "effTo": None}


def actor(eff_from):
    return {"effFrom": eff_from}


def test_a_single_later_actor_yields_a_candidate_awaiting_review():
    record = effective_to_candidate("T", TARGET, {"A": (actor("2020-07-01T00:00:00"), {12})})
    assert record["value"] == "2020-07-01"
    assert record["evidence_document_ids"] == ["A"]
    assert record["evidence_relation_codes"] == [12]
    assert record["status"] == "needs_review"


def test_no_candidate_without_one_unambiguous_later_actor():
    assert effective_to_candidate("T", TARGET, {})["skip"] == "no ending actor"
    two = {"A": (actor("2020-07-01T00:00:00"), {1}), "B": (actor("2021-01-01T00:00:00"), {12})}
    assert effective_to_candidate("T", TARGET, two)["skip"] == "several ending actors"
    assert effective_to_candidate("T", TARGET, {"A": (actor(None), {1})})["skip"] == "actor has no effFrom"
    # An actor effective no later than the target cannot be the moment it ended.
    same_day = {"A": (actor("2015-01-01T00:00:00"), {1})}
    assert effective_to_candidate("T", TARGET, same_day)["skip"] == "actor takes effect before the target"


def test_tsv_cell_collapses_embedded_newlines_and_tabs():
    # An untouched newline/tab would split one record across TSV rows/columns.
    assert _tsv_cell("Thông tư số 1\nsửa đổi\tĐiều 2") == "Thông tư số 1 sửa đổi Điều 2"
    assert _tsv_cell(None) == ""
    assert _tsv_cell("  đã có khoảng trắng thừa  ") == "đã có khoảng trắng thừa"
