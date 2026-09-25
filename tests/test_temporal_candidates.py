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


def _doc(eff_from, issued, clause):
    return {"effFrom": eff_from, "issueDate": issued,
            "documentContent": {"content": f"<p>Điều 3. Thông tư này có hiệu lực thi hành từ ngày {clause}.</p>"}}


def test_an_effective_date_before_signing_that_the_text_contradicts_is_proposed():
    """41/2021/TT-BGTVT: signed 31/12/2021, portal effFrom 2021-02-15, text 15/02/2022."""
    from build_temporal_candidates import effective_from_candidate

    record = effective_from_candidate("D", _doc("2021-02-15T00:00:00", "2021-12-31T00:00:00", "15 tháng 02 năm 2022"))
    assert record["field"] == "effective_from" and record["value"] == "2022-02-15"
    assert record["status"] == "needs_review" and "15 tháng 02 năm 2022" in record["evidence"]["clause"]


def test_a_document_that_says_it_is_retroactive_keeps_its_date():
    """119/2026/NĐ-CP: signed 03/04/2026 and its own text says 01/01/2026."""
    from build_temporal_candidates import effective_from_candidate

    assert effective_from_candidate("D", _doc("2026-01-01", "2026-04-03", "01 tháng 01 năm 2026")) is None
    assert effective_from_candidate("D", _doc("2022-02-15", "2021-12-31", "15 tháng 02 năm 2022")) is None  # not early
    assert effective_from_candidate("D", {"effFrom": "2021-02-15", "issueDate": "2021-12-31"}) is None      # no text
