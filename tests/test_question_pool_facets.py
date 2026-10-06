"""The pool's difficulty covariates, and the dates a one-version lineage is asked at."""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))
from build_question_pool import (  # noqa: E402
    MARGIN, SNAPSHOT, ask_dates, facets_of, pending_version, spread_as_of, why_no_answer,
)


def version(ordinal, effective_from, effective_to=None, created_by=None, text="x"):
    return {"id": f"v{ordinal}", "ordinal": ordinal, "text": text, "valid_to": None,
            "effective_from": effective_from, "effective_to": effective_to,
            "created_by_event_id": created_by, "ended_by_event_id": None, "provision_id": "p"}


def test_similarity_is_written_for_a_pair_and_a_list_for_a_chain():
    pair = facets_of([version(1, "2020-01-01", text="a b c"), version(2, "2021-01-01", text="a b d")])
    assert pair["n_versions"] == 2 and pair["similarity"] == pair["similarities"][0]

    chain = facets_of([version(1, "2020-01-01", text="a"), version(2, "2021-01-01", text="b"),
                       version(3, "2022-01-01", text="c")])
    assert chain["similarity"] is None, "only a two-version chain has one ratio"
    assert len(chain["similarities"]) == 2


def test_a_transition_that_only_changes_case_or_punctuation_is_not_substantive():
    # the 2025 agency renames and "hành." -> "hành;" are 18.4% of T3's transitions
    cosmetic = facets_of([version(1, "2020-01-01", text="Trung ương."),
                          version(2, "2021-01-01", text="trung ương;")])
    assert cosmetic["substantive_transitions"] == 0

    real = facets_of([version(1, "2020-01-01", text="năm triệu đồng"),
                      version(2, "2021-01-01", text="mười triệu đồng"),
                      version(3, "2022-01-01", text="hai mươi triệu đồng")])
    assert real["substantive_transitions"] == 2, "R2 needs two changes that carry a question"


def test_the_one_version_as_of_is_spread_but_stays_a_boundary_row():
    start = date(2020, 1, 1)
    asked = {spread_as_of(f"provision:{i}", start, date(2029, 12, 31)) for i in range(200)}
    assert len(asked) > 10, "every lineage asked on the same offset leaks through the margin"
    assert all(start < day <= start + timedelta(days=MARGIN) for day in asked), (
        "past MARGIN it would collide with the mid-interval twin enrich builds")


def test_the_spread_is_seeded_so_a_rebuild_reproduces_it():
    args = ("provision:abc", date(2020, 1, 1), date(2029, 12, 31))
    assert spread_as_of(*args) == spread_as_of(*args)
    assert spread_as_of("p", date(2020, 1, 1), date(2020, 1, 1)) == date(2020, 1, 1)


def test_a_one_version_row_is_never_asked_after_the_corpus_snapshot():
    (asked,) = ask_dates("T1", [version(1, "2026-09-10")], date(2026, 9, 20), "p", None)
    assert asked <= SNAPSHOT


def test_a_one_version_row_stops_at_the_document_end_not_only_the_version_end():
    # effective_to null inside a document that already ended is JUDGE C1's gap
    (asked,) = ask_dates("T1", [version(1, "2020-01-01")], date(2026, 9, 20), "p", date(2020, 1, 10))
    assert date(2020, 1, 1) < asked <= date(2020, 1, 9)


def test_pending_names_a_version_already_signed_but_not_yet_in_force():
    versions = [version(1, "2020-01-01", "2026-01-01"),
                version(2, "2026-01-01", created_by="event:9:aa")]
    signed_early = {"document:9": "2025-03-01"}

    got = pending_version(versions, date(2025, 6, 1), signed_early)
    assert got["actor_document_id"] == "document:9" and got["days_until_effect"] == 214

    assert pending_version(versions, date(2025, 6, 1), {"document:9": "2025-12-01"}) is None, (
        "not signed yet at as_of, so nothing points at the wrong answer")
    assert pending_version(versions, date(2026, 6, 1), signed_early) is None, "already in force"


def test_the_two_kinds_of_missing_answer_are_told_apart():
    versions = [version(1, "2020-01-01", "2021-01-01")]
    assert why_no_answer(versions, date(2019, 1, 1)) == "not_yet_in_force"
    assert why_no_answer(versions, date(2022, 1, 1)) == "provision_repealed"
