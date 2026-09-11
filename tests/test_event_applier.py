from datetime import date

import pytest

from legal_crawler.temporal import (
    EventApplicationError,
    EventApplier,
    EventStatus,
    ExtractionMethod,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    Provenance,
    Provision,
    ProvisionInsertion,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
    TemporalState,
    TextUpdate,
    UnsupportedEventError,
)


TARGET_DOCUMENT = "document:original"
SOURCE_DOCUMENT = "document:amending"


def make_state() -> TemporalState:
    state = TemporalState()
    state.add_document(
        LegalDocument(
            id=TARGET_DOCUMENT,
            number="01/2020/QH",
            title="Văn bản gốc",
            effective_from=date(2020, 1, 1),
        )
    )
    state.add_document(
        LegalDocument(
            id=SOURCE_DOCUMENT,
            number="02/2024/QH",
            title="Văn bản sửa đổi",
            effective_from=date(2024, 7, 1),
        )
    )
    provisions = (
        Provision(
            "chapter-1", TARGET_DOCUMENT, ProvisionLevel.CHAPTER, "Chương I", None, 1
        ),
        Provision(
            "article-6",
            TARGET_DOCUMENT,
            ProvisionLevel.ARTICLE,
            "Điều 6",
            "chapter-1",
            1,
        ),
        Provision(
            "clause-3",
            TARGET_DOCUMENT,
            ProvisionLevel.CLAUSE,
            "Khoản 3",
            "article-6",
            3,
        ),
        Provision(
            "point-d",
            TARGET_DOCUMENT,
            ProvisionLevel.POINT,
            "Điểm d",
            "clause-3",
            4,
        ),
    )
    for provision in provisions:
        state.add_provision(provision)
        state.add_version(
            ProvisionVersion(
                id=f"version:{provision.id}:1",
                provision_id=provision.id,
                ordinal=1,
                text=f"Nội dung ban đầu của {provision.title}",
                validity=TemporalInterval(date(2020, 1, 1)),
            )
        )
    return state


def evidence() -> tuple[Provenance, ...]:
    return (
        Provenance(
            source_document_id=SOURCE_DOCUMENT,
            source_provision_id="article-1-source",
            method=ExtractionMethod.RULE,
            evidence_text="Khoản 3 Điều 6 được sửa đổi như sau...",
            confidence=1.0,
        ),
    )


def event(
    event_id: str,
    operation: LegalOperation,
    **changes,
) -> LegalEvent:
    return LegalEvent(
        id=event_id,
        operation=operation,
        source_document_id=SOURCE_DOCUMENT,
        target_document_id=TARGET_DOCUMENT,
        effective_on=date(2024, 7, 1),
        status=EventStatus.VERIFIED,
        provenance=evidence(),
        **changes,
    )


@pytest.mark.parametrize(
    "operation", [LegalOperation.AMEND, LegalOperation.REPLACE, LegalOperation.CORRECT]
)
def test_text_operation_closes_old_version_and_creates_auditable_version(operation):
    state = make_state()
    legal_event = event(
        f"event:{operation.value}",
        operation,
        target_provision_ids=("clause-3",),
        new_text="Nội dung hợp nhất mới của Khoản 3.",
    )

    result = EventApplier().apply(legal_event, state)
    chain = state.chain("clause-3")

    assert result.applied
    assert result.closed_version_ids == ("version:clause-3:1",)
    assert result.created_version_ids == ("version:clause-3:2",)
    assert chain is not None
    assert chain.at(date(2024, 6, 30)).ended_by_event_id == legal_event.id
    assert chain.at(date(2024, 7, 1)).text == "Nội dung hợp nhất mới của Khoản 3."
    assert chain.at(date(2024, 7, 1)).created_by_event_id == legal_event.id
    assert chain.at(date(2024, 7, 1)).provenance == evidence()


def test_one_event_can_apply_distinct_text_to_multiple_targets():
    state = make_state()
    legal_event = event(
        "event:multi-target",
        LegalOperation.AMEND,
        text_updates=(
            TextUpdate("clause-3", "Khoản 3 sau sửa đổi."),
            TextUpdate("point-d", "Điểm d sau sửa đổi."),
        ),
    )

    result = EventApplier().apply(legal_event, state)

    assert len(result.created_version_ids) == 2
    assert state.chain("clause-3").current().text == "Khoản 3 sau sửa đổi."
    assert state.chain("point-d").current().text == "Điểm d sau sửa đổi."


def test_repeal_closes_target_without_creating_a_new_text_version():
    state = make_state()
    legal_event = event(
        "event:repeal",
        LegalOperation.REPEAL,
        target_provision_ids=("clause-3",),
    )

    result = EventApplier().apply(legal_event, state)

    assert result.created_version_ids == ()
    assert result.directly_repealed_provision_ids == ("clause-3",)
    assert state.chain("clause-3").current() is None
    assert state.chain("clause-3").versions[-1].ended_by_event_id == legal_event.id


def test_supplement_can_update_existing_text_and_insert_nested_nodes():
    state = make_state()
    legal_event = event(
        "event:supplement",
        LegalOperation.SUPPLEMENT,
        text_updates=(TextUpdate("clause-3", "Khoản 3 có thêm nội dung."),),
        insertions=(
            # Child comes first deliberately; application must not depend on input order.
            ProvisionInsertion(
                "point-a-new",
                ProvisionLevel.POINT,
                "Điểm a",
                "Nội dung điểm mới.",
                "clause-4-new",
                order_index=1,
            ),
            ProvisionInsertion(
                "clause-4-new",
                ProvisionLevel.CLAUSE,
                "Khoản 4",
                "Nội dung khoản mới.",
                "article-6",
                after_provision_id="clause-3",
            ),
        ),
    )

    result = EventApplier().apply(legal_event, state)

    assert result.created_provision_ids == ("clause-4-new", "point-a-new")
    assert state.chain("clause-4-new").current().validity.start == date(2024, 7, 1)
    assert state.chain("point-a-new").current().created_by_event_id == legal_event.id
    assert [item.id for item in state.children_of("article-6", TARGET_DOCUMENT)] == [
        "clause-3",
        "clause-4-new",
    ]
    assert state.chain("clause-3").current().text == "Khoản 3 có thêm nội dung."


def test_event_application_is_idempotent():
    state = make_state()
    legal_event = event(
        "event:idempotent",
        LegalOperation.AMEND,
        target_provision_ids=("clause-3",),
        new_text="Nội dung mới.",
    )

    first = EventApplier().apply(legal_event, state)
    second = EventApplier().apply(legal_event, state)

    assert first.applied
    assert not second.applied
    assert second.already_applied
    assert len(state.chain("clause-3")) == 2


def test_reusing_applied_event_id_with_different_content_is_rejected():
    state = make_state()
    first = event(
        "event:same-id",
        LegalOperation.AMEND,
        target_provision_ids=("clause-3",),
        new_text="Nội dung thứ nhất.",
    )
    conflicting = event(
        "event:same-id",
        LegalOperation.AMEND,
        target_provision_ids=("clause-3",),
        new_text="Nội dung khác.",
    )

    EventApplier().apply(first, state)
    with pytest.raises(EventApplicationError, match="different content"):
        EventApplier().apply(conflicting, state)


def test_explicit_targets_must_match_structured_text_updates():
    state = make_state()
    legal_event = event(
        "event:mismatched-targets",
        LegalOperation.AMEND,
        target_provision_ids=("clause-3",),
        text_updates=(TextUpdate("point-d", "Điểm d mới."),),
    )

    with pytest.raises(EventApplicationError, match="must match"):
        EventApplier().apply(legal_event, state)


def test_failed_multi_target_event_is_atomic():
    state = make_state()
    before = state.chain("clause-3").versions
    legal_event = event(
        "event:atomic",
        LegalOperation.AMEND,
        text_updates=(
            TextUpdate("clause-3", "Nội dung không được công bố."),
            TextUpdate("missing", "Target không tồn tại."),
        ),
    )

    with pytest.raises(EventApplicationError, match="does not exist"):
        EventApplier().apply(legal_event, state)

    assert state.chain("clause-3").versions == before
    assert legal_event.id not in state.applied_event_ids


def test_unaccepted_event_and_unknown_source_document_are_rejected():
    state = make_state()
    pending = LegalEvent(
        id="event:pending",
        operation=LegalOperation.AMEND,
        source_document_id=SOURCE_DOCUMENT,
        target_document_id=TARGET_DOCUMENT,
        effective_on=date(2024, 7, 1),
        target_provision_ids=("clause-3",),
        new_text="Chưa được kiểm duyệt.",
    )
    unknown_source = LegalEvent(
        id="event:unknown-source",
        operation=LegalOperation.REPEAL,
        source_document_id="document:missing",
        target_document_id=TARGET_DOCUMENT,
        effective_on=date(2024, 7, 1),
        target_provision_ids=("clause-3",),
        status=EventStatus.VERIFIED,
    )

    with pytest.raises(EventApplicationError, match="needs_review"):
        EventApplier().apply(pending, state)
    with pytest.raises(EventApplicationError, match="source document"):
        EventApplier().apply(unknown_source, state)


def test_same_day_events_on_one_provision_require_prior_consolidation():
    state = make_state()
    first = event(
        "event:first",
        LegalOperation.AMEND,
        target_provision_ids=("clause-3",),
        new_text="Kết quả thứ nhất.",
    )
    second = event(
        "event:second",
        LegalOperation.REPLACE,
        target_provision_ids=("clause-3",),
        new_text="Kết quả thứ hai.",
    )

    EventApplier().apply(first, state)
    with pytest.raises(EventApplicationError, match="later than current version start"):
        EventApplier().apply(second, state)

    assert state.chain("clause-3").current().text == "Kết quả thứ nhất."


def test_same_day_events_on_different_provisions_are_allowed():
    state = make_state()
    clause_event = event(
        "event:clause",
        LegalOperation.AMEND,
        target_provision_ids=("clause-3",),
        new_text="Khoản mới.",
    )
    point_event = event(
        "event:point",
        LegalOperation.AMEND,
        target_provision_ids=("point-d",),
        new_text="Điểm mới.",
    )

    EventApplier().apply(clause_event, state)
    EventApplier().apply(point_event, state)

    assert state.chain("clause-3").current().created_by_event_id == clause_event.id
    assert state.chain("point-d").current().created_by_event_id == point_event.id


def test_suspend_and_resume_are_explicitly_deferred():
    state = make_state()
    legal_event = event(
        "event:suspend",
        LegalOperation.SUSPEND,
        target_provision_ids=("clause-3",),
    )

    with pytest.raises(UnsupportedEventError, match="not implemented"):
        EventApplier().apply(legal_event, state)
