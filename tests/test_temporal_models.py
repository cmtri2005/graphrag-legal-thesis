from datetime import date

import pytest

from legal_crawler.temporal.models import (
    EventStatus,
    ExtractionMethod,
    LegalEvent,
    LegalOperation,
    Provenance,
    ProvisionVersion,
    TemporalInterval,
)


def test_interval_is_half_open_at_version_transition():
    old = TemporalInterval(date(2024, 1, 1), date(2025, 1, 1))
    new = TemporalInterval(date(2025, 1, 1))

    assert old.contains(date(2024, 12, 31))
    assert not old.contains(date(2025, 1, 1))
    assert new.contains(date(2025, 1, 1))
    assert not old.overlaps(new)


def test_invalid_interval_is_rejected():
    with pytest.raises(ValueError, match="later than start"):
        TemporalInterval(date(2025, 1, 1), date(2025, 1, 1))


def test_version_delegates_point_in_time_check_to_interval():
    version = ProvisionVersion(
        id="provision-1:v1",
        provision_id="provision-1",
        ordinal=1,
        text="Nội dung phiên bản đầu tiên.",
        validity=TemporalInterval(date(2020, 7, 1), date(2024, 8, 1)),
    )

    assert version.is_valid_at(date(2020, 7, 1))
    assert not version.is_valid_at(date(2024, 8, 1))


def test_unresolved_event_is_retained_but_not_applicable():
    event = LegalEvent(
        id="event-1",
        operation=LegalOperation.AMEND,
        source_document_id="amending-document",
        target_document_id="original-document",
        effective_on=None,
    )

    assert event.status is EventStatus.NEEDS_REVIEW
    assert not event.is_applicable


def test_verified_event_requires_a_date_and_resolved_target():
    with pytest.raises(ValueError, match="effective_on"):
        LegalEvent(
            id="event-1",
            operation=LegalOperation.REPEAL,
            source_document_id="repealer",
            target_document_id="original",
            effective_on=None,
            target_provision_ids=("article-1",),
            status=EventStatus.VERIFIED,
        )

    with pytest.raises(ValueError, match="resolved target"):
        LegalEvent(
            id="event-2",
            operation=LegalOperation.REPEAL,
            source_document_id="repealer",
            target_document_id="original",
            effective_on=date(2025, 1, 1),
            status=EventStatus.VERIFIED,
        )


def test_provenance_confidence_is_bounded():
    with pytest.raises(ValueError, match="between 0 and 1"):
        Provenance(
            source_document_id="doc-1",
            method=ExtractionMethod.LLM,
            confidence=1.1,
        )

