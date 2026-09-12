from datetime import date

from legal_crawler.temporal import (
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
    SnapshotService,
    TemporalInterval,
    TemporalState,
)


def make_state() -> TemporalState:
    state = TemporalState()
    state.add_document(
        LegalDocument("doc", "01/2020/QH", "Văn bản", effective_from=date(2020, 1, 1))
    )
    state.add_document(
        LegalDocument(
            "source", "02/2024/QH", "Văn bản sửa đổi", effective_from=date(2024, 1, 1)
        )
    )
    items = (
        Provision("chapter", "doc", ProvisionLevel.CHAPTER, "Chương I", None, 1),
        Provision("article", "doc", ProvisionLevel.ARTICLE, "Điều 1", "chapter", 1),
        Provision("clause-1", "doc", ProvisionLevel.CLAUSE, "Khoản 1", "article", 1),
        Provision("clause-2", "doc", ProvisionLevel.CLAUSE, "Khoản 2", "article", 2),
    )
    for item in items:
        state.add_provision(item)
        state.add_version(
            ProvisionVersion(
                f"version:{item.id}:1",
                item.id,
                1,
                f"Nội dung {item.title}",
                TemporalInterval(date(2020, 1, 1)),
            )
        )
    return state


def test_snapshot_selects_exact_half_open_version_and_its_provenance():
    state = make_state()
    provenance = (
        Provenance(
            "source",
            ExtractionMethod.RULE,
            evidence_text="Khoản 1 được sửa đổi như sau...",
        ),
    )
    legal_event = LegalEvent(
        "event:amend",
        LegalOperation.AMEND,
        "source",
        "doc",
        date(2024, 1, 1),
        target_provision_ids=("clause-1",),
        new_text="Nội dung Khoản 1 đã sửa đổi",
        status=EventStatus.VERIFIED,
        provenance=provenance,
    )
    EventApplier().apply(legal_event, state)
    snapshots = SnapshotService(state)

    before = snapshots.snapshot("clause-1", date(2023, 12, 31))
    after = snapshots.snapshot("clause-1", date(2024, 1, 1))

    assert before.version.ordinal == 1
    assert after.version.ordinal == 2
    assert after.text == "Nội dung Khoản 1 đã sửa đổi"
    assert after.created_by_event == legal_event
    assert after.provenance == provenance
    assert after.warnings == ()


def test_invalid_snapshot_hides_text_but_keeps_the_ending_event_for_audit():
    state = make_state()
    legal_event = LegalEvent(
        "event:repeal",
        LegalOperation.REPEAL,
        "source",
        "doc",
        date(2024, 1, 1),
        target_provision_ids=("article",),
        status=EventStatus.VERIFIED,
    )
    EventApplier().apply(legal_event, state)
    snapshots = SnapshotService(state)

    article = snapshots.snapshot("article", date(2024, 1, 1))
    child = snapshots.snapshot("clause-1", date(2024, 1, 1))

    assert not article.validity.valid
    assert article.version is None
    assert article.text is None
    assert article.ended_by_event == legal_event
    assert article.caused_by_event == legal_event
    assert not child.validity.valid
    assert child.version is None
    assert child.text is None
    assert child.ended_by_event is None
    assert child.caused_by_event == legal_event


def test_document_snapshot_is_deterministic_and_respects_insertion_anchor():
    state = make_state()
    legal_event = LegalEvent(
        "event:supplement",
        LegalOperation.SUPPLEMENT,
        "source",
        "doc",
        date(2024, 1, 1),
        insertions=(
            ProvisionInsertion(
                "clause-1a",
                ProvisionLevel.CLAUSE,
                "Khoản 1a",
                "Nội dung Khoản 1a",
                "article",
                after_provision_id="clause-1",
            ),
        ),
        status=EventStatus.VERIFIED,
    )
    EventApplier().apply(legal_event, state)
    snapshots = SnapshotService(state)

    first = snapshots.snapshot_document("doc", date(2024, 1, 1))
    second = snapshots.snapshot_document("doc", date(2024, 1, 1))

    assert first == second
    assert [item.provision.id for item in first] == [
        "chapter",
        "article",
        "clause-1",
        "clause-1a",
        "clause-2",
    ]


def test_document_snapshot_filters_levels_and_invalid_nodes():
    state = make_state()
    legal_event = LegalEvent(
        "event:repeal-clause",
        LegalOperation.REPEAL,
        "source",
        "doc",
        date(2024, 1, 1),
        target_provision_ids=("clause-1",),
        status=EventStatus.VERIFIED,
    )
    EventApplier().apply(legal_event, state)

    results = SnapshotService(state).valid_provisions(
        "doc",
        date(2024, 1, 1),
        levels=frozenset({ProvisionLevel.CLAUSE}),
    )

    assert [result.provision.id for result in results] == ["clause-2"]


def test_snapshot_warns_when_valid_version_has_no_provenance():
    result = SnapshotService(make_state()).snapshot("article", date(2023, 1, 1))

    assert result.validity.valid
    assert result.warnings == ("version_has_no_provenance",)
