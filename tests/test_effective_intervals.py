from datetime import date

from build_versions import _version_row
from legal_crawler.temporal import (
    LegalDocument,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
    TemporalState,
    ValidityService,
)
from legal_crawler.temporal.effective_intervals import effective_intervals_by_version


def _version(id, provision_id, ordinal, start, end=None):
    return ProvisionVersion(
        id, provision_id, ordinal, id,
        TemporalInterval(date.fromisoformat(start), date.fromisoformat(end) if end else None),
    )


def test_parent_amendment_preserves_child_but_repeal_ends_it():
    state = TemporalState()
    state.add_document(LegalDocument("doc", "1", "Law", effective_from=date(2020, 1, 1)))
    state.add_provision(Provision("article", "doc", ProvisionLevel.ARTICLE, "Article", None))
    state.add_provision(Provision("clause", "doc", ProvisionLevel.CLAUSE, "Clause", "article"))
    state.add_version(_version("parent-1", "article", 1, "2020-01-01", "2022-01-01"))
    state.add_version(_version("parent-2", "article", 2, "2022-01-01", "2023-01-01"))
    state.add_version(_version("child", "clause", 1, "2020-01-01"))

    result = effective_intervals_by_version(state, "doc")
    assert result["child"] == (TemporalInterval(date(2020, 1, 1), date(2023, 1, 1)),)
    assert ValidityService(state).is_valid("clause", date(2022, 1, 1))
    assert not ValidityService(state).is_valid("clause", date(2023, 1, 1))


def test_document_end_clips_descendants_and_a_text_less_parent_is_transparent():
    """Master plan §11: a node we hold no text for says nothing about its children.

    A Chương/Mục heading carries no words of its own, and an Điều the corpus
    lacks text for is missing data, not data to the contrary. Treating it as a
    repeal would silence every provision beneath it.
    """
    state = TemporalState()
    state.add_document(
        LegalDocument("doc", "1", "Law", effective_from=date(2020, 1, 1),
                      effective_to=date(2024, 1, 1))
    )
    state.add_provision(Provision("article", "doc", ProvisionLevel.ARTICLE, "Article", None))
    state.add_provision(Provision("clause", "doc", ProvisionLevel.CLAUSE, "Clause", "article"))
    state.add_version(_version("child", "clause", 1, "2020-01-01"))
    document_window = (TemporalInterval(date(2020, 1, 1), date(2024, 1, 1)),)

    assert effective_intervals_by_version(state, "doc")["child"] == document_window
    assert ValidityService(state).is_valid("clause", date(2021, 1, 1))
    assert not ValidityService(state).is_valid("clause", date(2024, 1, 1))

    # Text for the parent changes nothing here: it opens with the document too.
    state.add_version(_version("parent", "article", 1, "2020-01-01"))
    assert effective_intervals_by_version(state, "doc")["child"] == document_window


def test_disjoint_parent_coverage_is_not_broadened():
    state = TemporalState()
    state.add_document(LegalDocument("doc", "1", "Law", effective_from=date(2020, 1, 1)))
    state.add_provision(Provision("article", "doc", ProvisionLevel.ARTICLE, "Article", None))
    state.add_provision(Provision("clause", "doc", ProvisionLevel.CLAUSE, "Clause", "article"))
    state.add_version(_version("parent-1", "article", 1, "2020-01-01", "2021-01-01"))
    state.add_version(_version("parent-2", "article", 2, "2022-01-01"))
    state.add_version(_version("child", "clause", 1, "2020-01-01"))
    assert effective_intervals_by_version(state, "doc")["child"] == (
        TemporalInterval(date(2020, 1, 1), date(2021, 1, 1)),
        TemporalInterval(date(2022, 1, 1)),
    )
    assert not ValidityService(state).is_valid("clause", date(2021, 6, 1))

    row = _version_row(state.chain("clause").versions[0],
                       effective_intervals_by_version(state, "doc")["child"])
    assert row["effective_interval_count"] == 2
    assert row["effective_from"] is None
    assert row["effective_to"] is None


def test_undated_text_has_no_effective_window():
    version = ProvisionVersion("undated", "clause", 1, "text")
    row = _version_row(version, ())
    assert row["valid_from"] is None
    assert row["effective_intervals"] == []
    assert row["effective_interval_count"] == 0
