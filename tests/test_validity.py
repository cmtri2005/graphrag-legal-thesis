from dataclasses import replace
from datetime import date

from legal_crawler.temporal import (
    EventApplier,
    EventStatus,
    InvalidityReason,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
    TemporalState,
    ValidityService,
)


def make_tree_state(*, document_end: date | None = None) -> TemporalState:
    state = TemporalState()
    state.add_document(
        LegalDocument(
            "doc",
            "01/2020/QH",
            "Văn bản thử nghiệm",
            effective_from=date(2020, 1, 1),
            effective_to=document_end,
        )
    )
    state.add_document(
        LegalDocument(
            "source", "02/2024/QH", "Văn bản tác động", effective_from=date(2024, 1, 1)
        )
    )
    definitions = (
        ("chapter", ProvisionLevel.CHAPTER, None),
        ("article", ProvisionLevel.ARTICLE, "chapter"),
        ("clause", ProvisionLevel.CLAUSE, "article"),
        ("point", ProvisionLevel.POINT, "clause"),
    )
    for index, (provision_id, level, parent_id) in enumerate(definitions, 1):
        state.add_provision(
            Provision(provision_id, "doc", level, provision_id, parent_id, index)
        )
        state.add_version(
            ProvisionVersion(
                f"version:{provision_id}:1",
                provision_id,
                1,
                f"text:{provision_id}",
                TemporalInterval(date(2020, 1, 1)),
            )
        )
    return state


def repeal(state: TemporalState, provision_id: str) -> LegalEvent:
    legal_event = LegalEvent(
        id=f"event:repeal:{provision_id}",
        operation=LegalOperation.REPEAL,
        source_document_id="source",
        target_document_id="doc",
        effective_on=date(2024, 1, 1),
        target_provision_ids=(provision_id,),
        status=EventStatus.VERIFIED,
    )
    EventApplier().apply(legal_event, state)
    return legal_event


def test_validity_obeys_document_interval_and_local_version_start():
    state = make_tree_state(document_end=date(2025, 1, 1))
    validity = ValidityService(state)

    assert validity.check("chapter", date(2019, 12, 31)).reason is (
        InvalidityReason.DOCUMENT_NOT_YET_EFFECTIVE
    )
    assert validity.check("chapter", date(2025, 1, 1)).reason is (
        InvalidityReason.DOCUMENT_EXPIRED
    )
    assert validity.is_valid("chapter", date(2024, 12, 31))


def test_repealing_chapter_invalidates_every_descendant():
    state = make_tree_state()
    legal_event = repeal(state, "chapter")
    validity = ValidityService(state)

    chapter = validity.check("chapter", date(2024, 1, 1))
    assert chapter.reason is InvalidityReason.PROVISION_REPEALED
    assert chapter.caused_by_event_id == legal_event.id
    for provision_id in ("article", "clause", "point"):
        result = validity.check(provision_id, date(2024, 1, 1))
        assert result.reason is InvalidityReason.PARENT_INVALID
        assert result.invalid_ancestor_id == "chapter"
        assert result.caused_by_event_id == legal_event.id


def test_repealing_clause_does_not_invalidate_parent_but_invalidates_point():
    state = make_tree_state()
    repeal(state, "clause")
    validity = ValidityService(state)

    assert validity.is_valid("article", date(2024, 1, 1))
    assert validity.check("clause", date(2024, 1, 1)).reason is (
        InvalidityReason.PROVISION_REPEALED
    )
    point = validity.check("point", date(2024, 1, 1))
    assert point.reason is InvalidityReason.PARENT_INVALID
    assert point.invalid_ancestor_id == "clause"


def test_pre_creation_and_unexplained_gap_have_distinct_reasons():
    state = make_tree_state()
    state.add_provision(
        Provision("later", "doc", ProvisionLevel.ARTICLE, "Điều mới", "chapter", 2)
    )
    state.add_version(
        ProvisionVersion(
            "version:later:1",
            "later",
            1,
            "Nội dung có hiệu lực sau.",
            TemporalInterval(date(2023, 1, 1), date(2024, 1, 1)),
        )
    )
    validity = ValidityService(state)

    assert validity.check("later", date(2022, 1, 1)).reason is (
        InvalidityReason.PROVISION_NOT_YET_EFFECTIVE
    )
    assert validity.check("later", date(2024, 1, 1)).reason is (
        InvalidityReason.INACTIVE_GAP
    )


def test_valid_descendants_filters_the_whole_variable_depth_tree():
    state = make_tree_state()
    repeal(state, "clause")

    assert ValidityService(state).valid_descendants("chapter", date(2024, 1, 1)) == (
        "article",
    )


def test_unknown_provision_returns_typed_reason_instead_of_raising():
    result = ValidityService(make_tree_state()).check("missing", date(2024, 1, 1))

    assert not result.valid
    assert result.reason is InvalidityReason.UNKNOWN_PROVISION


def test_validity_defensively_detects_a_cycle_from_corrupted_storage():
    state = make_tree_state()
    # Public state operations reject invalid parents. This deliberately mimics
    # a malformed record loaded by a future storage adapter.
    chapter = state.provision("chapter")
    state._provisions["chapter"] = replace(chapter, parent_id="point")

    result = ValidityService(state).check("point", date(2024, 1, 1))

    assert not result.valid
    assert result.reason is InvalidityReason.STRUCTURE_CYCLE
    assert result.invalid_ancestor_id == "point"
