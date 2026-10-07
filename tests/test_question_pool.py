from datetime import date

from build_question_pool import (
    ask_dates, classify, in_force_at, min_repr, norm_continuity, repealed_by_ancestor, stable_sample,
)


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


def test_T3_is_asked_the_day_before_each_switch_and_on_the_last():
    chain = [_v(1, "2019-01-01", "2021-01-01"), _v(2, "2021-01-01", "2024-01-01"), _v(3, "2024-01-01")]
    dates = ask_dates("T3", chain, date(2026, 9, 20))
    assert dates == [date(2020, 12, 31), date(2023, 12, 31), date(2024, 1, 1)]
    assert [in_force_at(chain, d)["ordinal"] for d in dates] == [1, 2, 3]      # one date inside each version


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


def test_T6_records_the_date_the_provision_stopped():
    """T6's transition is the ending, not a later version's start: 984 of the
    1,000 T6 candidates have a single version, so `versions[-1].effective_from`
    left the column empty and forced downstream to read it off `as_of_2`."""
    from build_question_pool import build_row

    provision = {"id": "provision:x", "document_id": "document:d", "level": "Clause", "title": "Khoản 1"}
    ended = [_v(1, "2015-01-01", "2020-01-01", ended_by="event:x")]
    row = build_row("T6", provision, ended, date(2026, 9, 20), {})

    assert row["transition_on"] == "2020-01-01"
    assert row["gold"][-1]["as_of"] == row["transition_on"]
    assert row["gold"][-1]["in_force"] is False

    # An amended-then-repealed Khoản still reports the ending, not the amendment.
    amended = [_v(1, "2015-01-01", "2018-01-01"), _v(2, "2018-01-01", "2020-01-01", ended_by="event:x")]
    assert build_row("T6", provision, amended, date(2026, 9, 20), {})["transition_on"] == "2020-01-01"
    # Every other group keeps the date its last version opened.
    assert build_row("T2", provision, amended, date(2026, 9, 20), {})["transition_on"] == "2018-01-01"
    assert build_row("T1", provision, [_v(1, "2015-01-01")], date(2026, 9, 20), {})["transition_on"] is None


def test_a_provision_that_fell_with_its_ancestor_is_told_apart_from_one_repealed_itself():
    """H3: out of force with no event of its own, inside a document still in force."""
    today = date(2026, 9, 20)
    fell = {"effective_to": "2025-01-01", "valid_to": None, "ended_by_event_id": None}
    assert repealed_by_ancestor(fell, "Point", None, today)
    assert not repealed_by_ancestor({**fell, "ended_by_event_id": "event:x", "valid_to": "2025-01-01"},
                                    "Point", None, today)                       # repealed itself: direct
    assert not repealed_by_ancestor(fell, "Point", date(2025, 1, 1), today)     # the whole document ended
    assert not repealed_by_ancestor(fell, "Article", None, today)               # T6 asks about Khoản/Điểm
    assert not repealed_by_ancestor({**fell, "effective_to": "2027-01-01"}, "Clause", None, today)


def test_a_capped_group_keeps_its_ranked_lineages_when_the_candidates_change():
    rows = [{"id": f"r{i:02}", "provision_id": f"p{i:02}"} for i in range(40)]
    ranked = {"p03", "p17", "p31"}
    before = stable_sample(rows, 10, ranked)
    after = stable_sample([r for r in rows if r["id"] != "r05"], 10, ranked)   # one candidate left the group
    assert len(before) == len(after) == 10
    assert ranked <= {r["provision_id"] for r in before} and ranked <= {r["provision_id"] for r in after}


def test_a_clause_whose_sibling_gained_a_rule_the_same_day_is_kept_out_of_T6():
    """The 05/10 adviser ruling: T6 gold asserts the content is gone, not just the clause.

    Measured on the pool the same day: 645/1,000 T6 "direct" candidates and
    1,045/2,000 "ancestor" ones have an amend, supplement or replace landing in
    their own document on the day they ended, and annotator B rejected 45 of the
    54 contested T6 rows for exactly this. Such a chain still ships — asked inside
    a version's window, where its gold is the text — just not as T6.
    """
    today = date(2026, 9, 20)
    repealed = [_v(1, "2015-01-01", "2020-01-01", ended_by="event:x")]

    assert classify(repealed, None, "Clause", today) == "T6"
    assert classify(repealed, None, "Clause", today, moved=True) == "T1"
    pair = [_v(1, "2015-01-01", "2020-01-01"), _v(2, "2020-01-01", "2022-01-01", ended_by="event:x")]
    assert classify(pair, None, "Clause", today, moved=True) == "T2"


def test_norm_continuity_flags_only_a_change_co_dated_in_the_same_document():
    co_dated = {("document:7", "2020-01-01")}

    assert norm_continuity("document:7", "2020-01-01", co_dated) == "unclear"
    assert norm_continuity("document:7", "2021-06-01", co_dated) == "none"   # another day
    assert norm_continuity("document:8", "2020-01-01", co_dated) == "none"   # another document
    assert norm_continuity("document:7", None, co_dated) == "none"           # never ended


def _repr_row(n_versions, in_force=True, as_of="2020-01-01", events=(), **extra):
    return {"n_versions": n_versions, "event_ids": list(events),
            "gold": [{"as_of": as_of, "in_force": in_force}], **extra}


def test_min_repr_names_the_weakest_representation_that_can_decide_the_row():
    """graph_justification.md §3: I1 the version chain, I2 the ancestors, I3 the closure."""
    assert min_repr(_repr_row(1), {}) == "doc_metadata"          # B7's reach
    assert min_repr(_repr_row(2), {}) == "clause_version"        # I1
    assert min_repr(_repr_row(1, in_force=False), {}) == "clause_version"
    assert min_repr(_repr_row(1, repeal_mode="ancestor"), {}) == "ancestor_chain"   # I2
    # I3 either way: a successor may hold the rule, or the acting document has
    # itself been amended before the date asked, so its text is not what applies.
    assert min_repr(_repr_row(2, norm_continuity="unclear"), {}) == "cross_document"
    acted = _repr_row(2, as_of="2020-01-01", events=["event:d9:aa"])
    assert min_repr(acted, {"document:d9": "2019-01-01"}) == "cross_document"
    assert min_repr(acted, {"document:d9": "2021-01-01"}) == "clause_version"   # acted on later
    # precedence: the ancestor case is I2 only while nothing crossed a document
    assert min_repr(_repr_row(1, repeal_mode="ancestor", norm_continuity="unclear"),
                    {}) == "cross_document"
