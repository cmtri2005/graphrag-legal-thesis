from datetime import date

import pytest

from legal_crawler.extraction import (
    EventMaterializationError,
    ExtractionModelError,
    ExtractionResult,
    ExtractionStatus,
    ExtractionWarning,
    PhraseReplacement,
    ProvisionLocator,
    ProvisionReferencePart,
    RawAmendmentMention,
    ResolutionStatus,
    ResolvedTarget,
    SourceSpan,
    TargetReference,
    TargetScope,
    WarningCode,
    WarningSeverity,
)
from legal_crawler.temporal import (
    EventStatus,
    ExtractionMethod,
    LegalOperation,
    Provenance,
    ProvisionInsertion,
    ProvisionLevel,
    TextUpdate,
)


SOURCE_DOCUMENT = "document:amending-law"
TARGET_DOCUMENT = "document:original-law"


def locator(
    *,
    article: str | None = None,
    clause: str | None = None,
    point: str | None = None,
    chapter: str | None = None,
) -> ProvisionLocator:
    parts = []
    if chapter is not None:
        parts.append(ProvisionReferencePart(ProvisionLevel.CHAPTER, chapter))
    if article is not None:
        parts.append(ProvisionReferencePart(ProvisionLevel.ARTICLE, article))
    if clause is not None:
        parts.append(ProvisionReferencePart(ProvisionLevel.CLAUSE, clause))
    if point is not None:
        parts.append(ProvisionReferencePart(ProvisionLevel.POINT, point))
    return ProvisionLocator(tuple(parts))


def mention() -> RawAmendmentMention:
    evidence = "Bãi bỏ khoản 3 Điều 6 của Luật này."
    return RawAmendmentMention(
        id="mention-1",
        source_document_id=SOURCE_DOCUMENT,
        source_provision_id="source-article-2",
        text=evidence,
        span=SourceSpan(10, 26),
        provenance=(
            Provenance(
                source_document_id=SOURCE_DOCUMENT,
                source_provision_id="source-article-2",
                method=ExtractionMethod.RULE,
                evidence_text=evidence,
                confidence=0.98,
            ),
        ),
    )


def exact_reference(
    reference_id: str = "reference-1",
    *,
    article: str = "6",
    clause: str = "3",
) -> TargetReference:
    return TargetReference(
        id=reference_id,
        raw_text=f"khoản {clause} Điều {article} của Luật này",
        document_reference="Luật này",
        locator=locator(article=article, clause=clause),
        scope=TargetScope.EXACT,
    )


def resolved(
    reference_id: str = "reference-1",
    provision_id: str = "provision:article-6:clause-3",
    *,
    document_id: str = TARGET_DOCUMENT,
) -> ResolvedTarget:
    return ResolvedTarget(
        reference_id=reference_id,
        scope=TargetScope.EXACT,
        status=ResolutionStatus.RESOLVED,
        target_document_id=document_id,
        target_provision_ids=(provision_id,),
        candidate_provision_ids=(provision_id,),
        method=ExtractionMethod.EXACT_NODE_ID,
        confidence=1.0,
    )


def ready_result(
    operation: LegalOperation,
    *,
    references: tuple[TargetReference, ...] | None = None,
    resolutions: tuple[ResolvedTarget, ...] | None = None,
    text_updates: tuple[TextUpdate, ...] = (),
    insertions: tuple[ProvisionInsertion, ...] = (),
    phrase_replacements: tuple[PhraseReplacement, ...] = (),
) -> ExtractionResult:
    references = references or (exact_reference(),)
    resolutions = resolutions or (resolved(),)
    return ExtractionResult(
        id=f"extraction:{operation.value}",
        mention=mention(),
        status=ExtractionStatus.READY,
        operation=operation,
        effective_on=date(2024, 7, 1),
        target_references=references,
        resolved_targets=resolutions,
        text_updates=text_updates,
        insertions=insertions,
        phrase_replacements=phrase_replacements,
        extraction_confidence=0.95,
    )


def test_source_span_is_half_open_and_extracts_verbatim_text():
    source = "0123456789Nội dung sửa đổi"
    span = SourceSpan(10, len(source))

    assert span.extract_from(source) == "Nội dung sửa đổi"

    with pytest.raises(ExtractionModelError, match="later than start"):
        SourceSpan(2, 2)
    with pytest.raises(ExtractionModelError, match="exceeds"):
        SourceSpan(0, 100).extract_from(source)


def test_mention_preserves_verbatim_evidence_span_and_provenance():
    raw = mention()

    assert raw.text == "Bãi bỏ khoản 3 Điều 6 của Luật này."
    assert raw.span == SourceSpan(10, 26)
    assert raw.provenance[0].evidence_text == raw.text


def test_mention_rejects_provenance_from_another_document():
    with pytest.raises(ExtractionModelError, match="source document"):
        RawAmendmentMention(
            id="mention",
            source_document_id=SOURCE_DOCUMENT,
            text="Sửa đổi Điều 1.",
            provenance=(
                Provenance("document:other", ExtractionMethod.MANUAL),
            ),
        )


def test_locator_represents_article_clause_point_in_canonical_order():
    reference = locator(article="6", clause="3", point="d")

    assert reference.leaf == ProvisionReferencePart(ProvisionLevel.POINT, "d")
    assert reference.label_for(ProvisionLevel.ARTICLE) == "6"
    assert reference.label_for(ProvisionLevel.CLAUSE) == "3"


def test_locator_rejects_duplicate_or_inner_to_outer_parts():
    with pytest.raises(ExtractionModelError, match="unique"):
        ProvisionLocator(
            (
                ProvisionReferencePart(ProvisionLevel.ARTICLE, "6"),
                ProvisionReferencePart(ProvisionLevel.ARTICLE, "7"),
            )
        )
    with pytest.raises(ExtractionModelError, match="outer to inner"):
        ProvisionLocator(
            (
                ProvisionReferencePart(ProvisionLevel.CLAUSE, "3"),
                ProvisionReferencePart(ProvisionLevel.ARTICLE, "6"),
            )
        )


def test_document_reference_is_distinct_from_provision_reference():
    document = TargetReference(
        id="document-reference",
        raw_text="Luật này",
        document_reference="Luật này",
        scope=TargetScope.DOCUMENT,
    )

    assert document.locator is None
    with pytest.raises(ExtractionModelError, match="cannot contain"):
        TargetReference(
            id="invalid-document-reference",
            raw_text="Điều 6 của Luật này",
            document_reference="Luật này",
            locator=locator(article="6"),
            scope=TargetScope.DOCUMENT,
        )


def test_reference_can_represent_a_subtree_and_an_insertion_anchor():
    subtree = TargetReference(
        id="chapter-2-reference",
        raw_text="Chương II",
        locator=locator(chapter="II"),
        scope=TargetScope.SUBTREE,
    )
    insertion = TargetReference(
        id="new-point-reference",
        raw_text="bổ sung điểm đ sau điểm d khoản 2 Điều 5",
        locator=locator(article="5", clause="2", point="đ"),
        is_insertion=True,
        insert_after=locator(article="5", clause="2", point="d"),
        scope=TargetScope.EXACT,
    )

    assert subtree.locator.leaf.level is ProvisionLevel.CHAPTER
    assert insertion.insert_after.leaf.label == "d"


def test_insertion_anchor_requires_an_explicit_insertion_reference():
    with pytest.raises(ExtractionModelError, match="is_insertion=True"):
        TargetReference(
            id="invalid-anchor",
            raw_text="sau điểm d khoản 2 Điều 5",
            locator=locator(article="5", clause="2", point="đ"),
            insert_after=locator(article="5", clause="2", point="d"),
            scope=TargetScope.EXACT,
        )


def test_ambiguous_resolution_keeps_candidates_without_choosing_one():
    target = ResolvedTarget(
        reference_id="reference-1",
        scope=TargetScope.EXACT,
        status=ResolutionStatus.NEEDS_REVIEW,
        candidate_document_ids=(TARGET_DOCUMENT,),
        candidate_provision_ids=("candidate-1", "candidate-2"),
        method=ExtractionMethod.RULE,
        confidence=0.5,
    )

    assert not target.is_resolved
    assert target.target_document_id is None
    assert target.target_provision_ids == ()


def test_unaccepted_resolution_cannot_store_a_tentative_final_target():
    with pytest.raises(ExtractionModelError, match="as candidates"):
        ResolvedTarget(
            reference_id="reference-1",
            scope=TargetScope.EXACT,
            status=ResolutionStatus.NEEDS_REVIEW,
            target_document_id=TARGET_DOCUMENT,
            target_provision_ids=("candidate-1",),
        )


def test_exact_subtree_and_document_resolution_cardinality_is_checked():
    with pytest.raises(ExtractionModelError, match="exactly one"):
        ResolvedTarget(
            "reference",
            TargetScope.EXACT,
            ResolutionStatus.RESOLVED,
            TARGET_DOCUMENT,
            ("provision-1", "provision-2"),
            method=ExtractionMethod.RULE,
            confidence=0.9,
        )
    with pytest.raises(ExtractionModelError, match="exactly one root id"):
        ResolvedTarget(
            "reference",
            TargetScope.SUBTREE,
            ResolutionStatus.RESOLVED,
            TARGET_DOCUMENT,
            method=ExtractionMethod.RULE,
            confidence=0.9,
        )
    document = ResolvedTarget(
        "reference",
        TargetScope.DOCUMENT,
        ResolutionStatus.RESOLVED,
        TARGET_DOCUMENT,
        method=ExtractionMethod.RULE,
        confidence=0.9,
    )
    assert document.is_resolved


def test_subtree_resolution_requires_a_complete_affected_set_with_its_root():
    with pytest.raises(ExtractionModelError, match="requires affected"):
        ResolvedTarget(
            "chapter-reference",
            TargetScope.SUBTREE,
            ResolutionStatus.RESOLVED,
            TARGET_DOCUMENT,
            ("chapter-2",),
            method=ExtractionMethod.RULE,
            confidence=0.9,
        )
    with pytest.raises(ExtractionModelError, match="include its root"):
        ResolvedTarget(
            "chapter-reference",
            TargetScope.SUBTREE,
            ResolutionStatus.RESOLVED,
            TARGET_DOCUMENT,
            ("chapter-2",),
            ("article-7", "clause-1"),
            method=ExtractionMethod.RULE,
            confidence=0.9,
        )


def test_multiple_non_contiguous_targets_are_preserved_in_reference_order():
    references = (
        exact_reference("article-6-ref", article="6", clause="1"),
        exact_reference("article-10-ref", article="10", clause="1"),
    )
    resolutions = (
        resolved("article-6-ref", "provision:article-6:clause-1"),
        resolved("article-10-ref", "provision:article-10:clause-1"),
    )
    result = ready_result(
        LegalOperation.REPEAL,
        references=references,
        resolutions=resolutions,
    )

    assert result.resolved_provision_ids() == (
        "provision:article-6:clause-1",
        "provision:article-10:clause-1",
    )


def test_subtree_resolution_can_retain_root_and_all_descendant_ids():
    reference = TargetReference(
        "chapter-ref",
        "Chương II",
        TargetScope.SUBTREE,
        locator=locator(chapter="II"),
    )
    resolution = ResolvedTarget(
        "chapter-ref",
        TargetScope.SUBTREE,
        ResolutionStatus.RESOLVED,
        TARGET_DOCUMENT,
        ("chapter-2",),
        ("chapter-2", "article-7", "clause-1"),
        method=ExtractionMethod.EXACT_NODE_ID,
        confidence=1.0,
    )

    result = ready_result(
        LegalOperation.REPEAL,
        references=(reference,),
        resolutions=(resolution,),
    )

    assert result.resolved_provision_ids() == ("chapter-2",)
    assert result.affected_provision_ids() == (
        "chapter-2",
        "article-7",
        "clause-1",
    )
    event = result.to_legal_event(
        "event:repeal-chapter", event_status=EventStatus.VERIFIED
    )
    assert event.target_provision_ids == ("chapter-2",)


def test_phrase_replacement_can_refer_to_multiple_legal_units():
    replacement = PhraseReplacement(
        reference_ids=("article-6-ref", "article-10-ref"),
        old_text="cơ quan có thẩm quyền",
        new_text="cơ quan nhà nước có thẩm quyền",
    )

    assert replacement.reference_ids == ("article-6-ref", "article-10-ref")
    assert replacement.old_text in "thay cụm từ cơ quan có thẩm quyền"


def test_warning_has_stable_code_severity_and_review_context():
    warning = ExtractionWarning(
        code=WarningCode.AMBIGUOUS_TARGET,
        message="Tìm thấy hai Khoản 3 phù hợp.",
        severity=WarningSeverity.ERROR,
        mention_id="mention-1",
        reference_id="reference-1",
        details={"candidates": ["candidate-1", "candidate-2"]},
    )

    assert warning.code.value == "ambiguous_target"
    assert warning.details["candidates"] == ["candidate-1", "candidate-2"]


def test_pending_result_reports_all_major_readiness_issues():
    result = ExtractionResult(id="pending", mention=mention())

    assert result.readiness_issues() == (
        "status is needs_review",
        "operation is unresolved",
        "effective date is unresolved",
        "extraction confidence is missing",
        "no target references",
    )
    assert not result.is_event_ready


def test_ambiguous_target_and_error_warning_block_event_materialization():
    reference = exact_reference()
    ambiguity = ResolvedTarget(
        reference_id=reference.id,
        scope=reference.scope,
        status=ResolutionStatus.NEEDS_REVIEW,
        candidate_provision_ids=("candidate-1", "candidate-2"),
        confidence=0.4,
    )
    warning = ExtractionWarning(
        WarningCode.AMBIGUOUS_TARGET,
        "Không thể chọn duy nhất một target.",
        WarningSeverity.ERROR,
        mention_id="mention-1",
        reference_id=reference.id,
    )
    result = ExtractionResult(
        id="ambiguous",
        mention=mention(),
        operation=LegalOperation.REPEAL,
        effective_on=date(2024, 7, 1),
        target_references=(reference,),
        resolved_targets=(ambiguity,),
        extraction_confidence=0.9,
        warnings=(warning,),
    )

    assert "reference reference-1 is not resolved" in result.readiness_issues()
    assert "result contains error warnings" in result.readiness_issues()
    with pytest.raises(EventMaterializationError, match="cannot create"):
        result.to_legal_event("event-1", event_status=EventStatus.VERIFIED)


def test_ready_status_is_rejected_when_required_information_is_missing():
    with pytest.raises(ExtractionModelError, match="ready extraction result is incomplete"):
        ExtractionResult(
            id="incorrectly-ready",
            mention=mention(),
            status=ExtractionStatus.READY,
            operation=LegalOperation.REPEAL,
            target_references=(exact_reference(),),
            extraction_confidence=0.9,
        )


def test_resolutions_from_multiple_documents_must_be_split_into_events():
    references = (
        exact_reference("reference-1"),
        exact_reference("reference-2", article="7"),
    )
    resolutions = (
        resolved("reference-1", "provision-1", document_id="document-1"),
        resolved("reference-2", "provision-2", document_id="document-2"),
    )

    with pytest.raises(ExtractionModelError, match="multiple documents"):
        ready_result(
            LegalOperation.REPEAL,
            references=references,
            resolutions=resolutions,
        )


@pytest.mark.parametrize(
    ("operation", "updates", "insertions"),
    (
        (
            LegalOperation.AMEND,
            (TextUpdate("provision:article-6:clause-3", "Khoản 3 mới."),),
            (),
        ),
        (
            LegalOperation.REPLACE,
            (TextUpdate("provision:article-6:clause-3", "Khoản 3 thay thế."),),
            (),
        ),
        (LegalOperation.REPEAL, (), ()),
        (
            LegalOperation.SUPPLEMENT,
            (),
            (
                ProvisionInsertion(
                    "provision:new-point",
                    ProvisionLevel.POINT,
                    "Điểm đ",
                    "Nội dung Điểm đ.",
                    "provision:article-6:clause-3",
                    after_provision_id="provision:point-d",
                ),
            ),
        ),
    ),
)
def test_four_core_operations_materialize_to_legal_event(
    operation,
    updates,
    insertions,
):
    if operation is LegalOperation.SUPPLEMENT:
        insertion_reference = TargetReference(
            id="new-point-reference",
            raw_text="bổ sung điểm đ sau điểm d khoản 3 Điều 6",
            scope=TargetScope.EXACT,
            locator=locator(article="6", clause="3", point="đ"),
            is_insertion=True,
            insert_under=locator(article="6", clause="3"),
            insert_after=locator(article="6", clause="3", point="d"),
        )
        insertion_resolution = ResolvedTarget(
            reference_id=insertion_reference.id,
            scope=TargetScope.EXACT,
            status=ResolutionStatus.RESOLVED,
            target_document_id=TARGET_DOCUMENT,
            method=ExtractionMethod.EXACT_NODE_ID,
            confidence=1.0,
            resolves_insertion=True,
            introduced_provision_id="provision:new-point",
            insertion_parent_id="provision:article-6:clause-3",
            insertion_after_provision_id="provision:point-d",
        )
        result = ready_result(
            operation,
            references=(insertion_reference,),
            resolutions=(insertion_resolution,),
            insertions=insertions,
        )
    else:
        result = ready_result(
            operation,
            text_updates=updates,
            insertions=insertions,
        )

    event = result.to_legal_event(
        f"event:{operation.value}", event_status=EventStatus.VERIFIED
    )

    assert event.operation is operation
    assert event.source_document_id == SOURCE_DOCUMENT
    assert event.target_document_id == TARGET_DOCUMENT
    assert event.effective_on == date(2024, 7, 1)
    assert event.status is EventStatus.VERIFIED
    assert event.provenance == mention().provenance
    assert event.is_applicable


def test_event_acceptance_must_be_explicit_during_materialization():
    result = ready_result(LegalOperation.REPEAL)

    with pytest.raises(EventMaterializationError, match="requires verified"):
        result.to_legal_event(
            "event:unsafe", event_status=EventStatus.NEEDS_REVIEW
        )


def test_text_update_must_point_to_a_resolved_provision():
    with pytest.raises(ExtractionModelError, match="unresolved target ids"):
        ready_result(
            LegalOperation.AMEND,
            text_updates=(TextUpdate("provision:other", "Nội dung khác."),),
        )


def test_text_operation_must_consolidate_every_resolved_target():
    references = (
        exact_reference("reference-1"),
        exact_reference("reference-2", article="7"),
    )
    resolutions = (
        resolved("reference-1", "provision:article-6:clause-3"),
        resolved("reference-2", "provision:article-7:clause-3"),
    )

    with pytest.raises(ExtractionModelError, match="every resolved provision"):
        ready_result(
            LegalOperation.AMEND,
            references=references,
            resolutions=resolutions,
            text_updates=(
                TextUpdate("provision:article-6:clause-3", "Nội dung mới."),
            ),
        )


def test_insertion_payload_requires_a_matching_resolved_position():
    insertion = ProvisionInsertion(
        "provision:new-point",
        ProvisionLevel.POINT,
        "Điểm đ",
        "Nội dung Điểm đ.",
        "provision:article-6:clause-3",
        after_provision_id="provision:point-d",
    )

    with pytest.raises(ExtractionModelError, match="resolved positions"):
        ready_result(LegalOperation.SUPPLEMENT, insertions=(insertion,))


def test_extraction_result_validates_runtime_date_and_enum_types():
    with pytest.raises(ExtractionModelError, match="effective_on must be a date"):
        ExtractionResult(
            id="wrong-date",
            mention=mention(),
            effective_on="2024-07-01",
        )
    with pytest.raises(ExtractionModelError, match="TargetScope"):
        TargetReference(
            id="wrong-scope",
            raw_text="Điều 6",
            scope="exact",
            locator=locator(article="6"),
        )


def test_phrase_instruction_does_not_replace_consolidated_resulting_text():
    replacement = PhraseReplacement(
        ("reference-1",),
        "cụm từ cũ",
        "cụm từ mới",
    )

    with pytest.raises(ExtractionModelError, match="no consolidated text updates"):
        ready_result(
            LegalOperation.AMEND,
            phrase_replacements=(replacement,),
        )


def test_confidence_values_are_independently_validated():
    with pytest.raises(ExtractionModelError, match="resolution confidence"):
        ResolvedTarget(
            "reference",
            TargetScope.EXACT,
            ResolutionStatus.UNRESOLVED,
            confidence=1.1,
        )
    with pytest.raises(ExtractionModelError, match="extraction confidence"):
        ExtractionResult(
            id="result",
            mention=mention(),
            extraction_confidence=-0.1,
        )
