from datetime import date

from build_question_pool import ask_dates, classify, in_force_at


def _v(ordinal, start, end=None, ended_by=None):
    return {"id": f"v{ordinal}", "ordinal": ordinal, "text": f"nội dung {ordinal}",
            "effective_from": start, "effective_to": end,
            "created_by_event_id": None, "ended_by_event_id": ended_by}


def test_gold_answer_follows_the_half_open_effective_window():
    versions = [_v(1, "2020-01-01", "2024-01-01"), _v(2, "2024-01-01")]

    assert in_force_at(versions, date(2023, 12, 31))["ordinal"] == 1
    assert in_force_at(versions, date(2024, 1, 1))["ordinal"] == 2
    assert in_force_at(versions, date(2019, 12, 31)) is None


def test_a_long_chain_goes_to_T3_even_when_it_also_fits_T6():
    """T3 keeps 2x its quota, T6 keeps 22x, so the scarce group wins."""
    chain = [_v(1, "2015-01-01", "2018-01-01"), _v(2, "2018-01-01", "2020-01-01"),
             _v(3, "2020-01-01", "2022-01-01", ended_by="event:x")]

    assert classify(chain, None, "Clause", date(2026, 9, 20)) == "T3"


def test_group_depends_on_how_the_chain_ends():
    today = date(2026, 9, 20)
    repealed = [_v(1, "2015-01-01", "2020-01-01", ended_by="event:x")]
    assert classify(repealed, None, "Clause", today) == "T6"
    # same chain, but its document has itself expired: not a partial expiry
    assert classify(repealed, date(2021, 1, 1), "Clause", today) == "T1"
    assert classify([_v(1, "2015-01-01")], None, "Article", today) == "T1"
    # an undated version can never be an answer
    assert classify([_v(1, None)], None, "Article", today) is None


def test_T2_is_asked_either_side_of_the_switch():
    versions = [_v(1, "2020-01-01", "2024-01-01"), _v(2, "2024-01-01")]

    assert ask_dates("T2", versions, date(2026, 9, 20)) == [date(2023, 12, 31), date(2024, 1, 1)]


def test_a_chain_whose_amendment_changed_nothing_cannot_be_a_contrast_pair():
    """11.1% of consecutive pairs are textually identical; asking either side
    of that switch has one answer, not two."""
    from build_question_pool import build_row, in_force_at

    unchanged = [_v(1, "2020-01-01", "2024-01-01"), _v(2, "2024-01-01")]
    unchanged[1]["text"] = unchanged[0]["text"]
    provision = {"id": "provision:x", "document_id": "document:d", "level": "Clause", "title": "Khoản 1"}
    row = build_row("T2", provision, unchanged, date(2026, 9, 20), {})

    answers = [(g["in_force"], g["text"]) for g in row["gold"]]
    assert len(set(answers)) == 1  # the gate in main() drops exactly this shape
    assert in_force_at(unchanged, date(2023, 12, 31))["ordinal"] == 1
