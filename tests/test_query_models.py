from dataclasses import FrozenInstanceError, replace
from datetime import date

import pytest

from legal_crawler.query import (
    AnswerClaim,
    AnswerResult,
    AnswerStatus,
    Citation,
    CitationLevel,
    GraphTraversalStep,
    QueryModelError,
    RetrievedEvidence,
    RetrievalMethod,
    RetrievalSignal,
    TemporalQuery,
    TemporalResolution,
    VerificationDecision,
    VerificationIssue,
    VerificationIssueCode,
    VerificationResult,
    VerificationSeverity,
    citation_level_for,
)
from legal_crawler.temporal import (
    ExtractionMethod,
    LegalDocument,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    SnapshotResult,
    SnapshotService,
    TemporalInterval,
    TemporalState,
    RelationType,
)


QUERY_DATE = date(2023, 6, 1)


def temporal_query(
    *,
    identifier: str = "query:1",
    at: date | None = QUERY_DATE,
    resolution: TemporalResolution = TemporalResolution.EXPLICIT,
) -> TemporalQuery:
    return TemporalQuery(
        identifier,
        "Khoản 1 Điều 2 có hiệu lực vào ngày 01/06/2023 không?",
        at,
        resolution,
        temporal_expression="ngày 01/06/2023",
        temporal_confidence=(
            0.9 if resolution is TemporalResolution.INFERRED else None
        ),
        document_ids=("document:law",),
        levels=frozenset({ProvisionLevel.CLAUSE}),
    )


def valid_snapshot(
    *,
    at: date = QUERY_DATE,
    with_provenance: bool = True,
    level: ProvisionLevel = ProvisionLevel.CLAUSE,
) -> SnapshotResult:
    state = TemporalState()
    state.add_document(
        LegalDocument(
            "document:law",
            "01/2020/QH",
            "Luật kiểm thử",
            effective_from=date(2020, 1, 1),
        )
    )
    item = Provision(
        "provision:clause-1",
        "document:law",
        level,
        "Khoản 1 Điều 2",
        None,
    )
    provenance = (
        Provenance(
            "document:law",
            ExtractionMethod.SOURCE_METADATA,
            source_provision_id=item.id,
            evidence_text="Nội dung có hiệu lực.",
            source_url="https://example.test/law",
        ),
    )
    state.add_provision(item)
    state.add_version(
        ProvisionVersion(
            "version:clause-1:1",
            item.id,
            1,
            "Nội dung có hiệu lực.",
            TemporalInterval(date(2020, 1, 1), date(2024, 1, 1)),
            provenance=provenance if with_provenance else (),
        )
    )
    return SnapshotService(state).snapshot(item.id, at)


def evidence(
    *,
    identifier: str = "evidence:1",
    query_id: str = "query:1",
    snapshot: SnapshotResult | None = None,
    signals: tuple[RetrievalSignal, ...] | None = None,
    graph_path: tuple[GraphTraversalStep, ...] = (),
) -> RetrievedEvidence:
    return RetrievedEvidence(
        identifier,
        query_id,
        snapshot or valid_snapshot(),
        signals
        or (
            RetrievalSignal(RetrievalMethod.LEXICAL, 12.5, rank=2),
            RetrievalSignal(RetrievalMethod.DENSE, 0.82, rank=1),
            RetrievalSignal(RetrievalMethod.RERANK, 0.91, rank=1),
        ),
        rank=1,
        final_score=0.91,
        graph_path=graph_path,
    )


def citation(
    *,
    identifier: str = "citation:1",
    evidence_id: str = "evidence:1",
    document_id: str = "document:law",
    provision_id: str = "provision:clause-1",
    version_id: str = "version:clause-1:1",
    level: CitationLevel = CitationLevel.CLAUSE,
) -> Citation:
    return Citation(
        identifier,
        evidence_id,
        document_id,
        level,
        "Khoản 1 Điều 2 Luật kiểm thử",
        provision_id,
        version_id,
        supporting_text="Nội dung có hiệu lực.",
    )


def passed_verification() -> VerificationResult:
    return VerificationResult(
        "query:1",
        VerificationDecision.PASSED,
        verified_evidence_ids=("evidence:1",),
        verified_citation_ids=("citation:1",),
    )


def answered_result(**changes) -> AnswerResult:
    values = {
        "id": "answer:1",
        "query": temporal_query(),
        "text": "Khoản 1 Điều 2 còn hiệu lực tại ngày được hỏi.",
        "status": AnswerStatus.ANSWERED,
        "evidence": (evidence(),),
        "citations": (citation(),),
        "claims": (
            AnswerClaim(
                "claim:1",
                "Khoản 1 Điều 2 còn hiệu lực.",
                ("citation:1",),
            ),
        ),
        "verification": passed_verification(),
    }
    values.update(changes)
    return AnswerResult(**values)


def test_explicit_and_inferred_queries_retain_temporal_interpretation():
    explicit = temporal_query()
    inferred = temporal_query(resolution=TemporalResolution.INFERRED)

    assert explicit.temporal_ready
    assert explicit.at == QUERY_DATE
    assert inferred.temporal_confidence == pytest.approx(0.9)
    assert inferred.document_ids == ("document:law",)


def test_unresolved_query_does_not_silently_receive_a_date():
    query = TemporalQuery(
        "query:unresolved",
        "Quy định này có còn hiệu lực không?",
        None,
        TemporalResolution.UNRESOLVED,
    )

    assert not query.temporal_ready
    assert query.at is None


@pytest.mark.parametrize(
    "changes",
    (
        {"at": None},
        {"at": "2023-06-01"},
        {"resolution": TemporalResolution.INFERRED},
    ),
)
def test_resolved_query_rejects_missing_untyped_or_unexplained_time(changes):
    values = {
        "id": "query:invalid",
        "text": "Câu hỏi",
        "at": QUERY_DATE,
        "temporal_resolution": TemporalResolution.EXPLICIT,
    }
    values["temporal_resolution"] = changes.get(
        "resolution", values["temporal_resolution"]
    )
    values.update({key: value for key, value in changes.items() if key != "resolution"})

    with pytest.raises(QueryModelError):
        TemporalQuery(**values)


def test_unresolved_query_rejects_a_date_or_confidence():
    with pytest.raises(QueryModelError, match="unresolved"):
        TemporalQuery(
            "query:invalid",
            "Câu hỏi",
            QUERY_DATE,
            TemporalResolution.UNRESOLVED,
        )
    with pytest.raises(QueryModelError, match="confidence"):
        TemporalQuery(
            "query:invalid",
            "Câu hỏi",
            None,
            TemporalResolution.UNRESOLVED,
            temporal_confidence=0.5,
        )


def test_inferred_query_requires_the_source_temporal_expression():
    with pytest.raises(QueryModelError, match="temporal expression"):
        TemporalQuery(
            "query:inferred",
            "Quy định hiện hành là gì?",
            QUERY_DATE,
            TemporalResolution.INFERRED,
            temporal_confidence=0.8,
        )


def test_query_rejects_duplicate_document_filters_and_invalid_levels():
    with pytest.raises(QueryModelError, match="duplicates"):
        replace(temporal_query(), document_ids=("document:law", "document:law"))
    with pytest.raises(QueryModelError, match="ProvisionLevel"):
        replace(temporal_query(), levels=frozenset({"Clause"}))


@pytest.mark.parametrize("score", (True, float("nan"), float("inf"), "0.8"))
def test_retrieval_signal_rejects_non_finite_or_untyped_scores(score):
    with pytest.raises(QueryModelError, match="score"):
        RetrievalSignal(RetrievalMethod.DENSE, score)


def test_evidence_is_bound_to_exact_snapshot_version_and_provenance():
    item = evidence()

    assert item.document_id == "document:law"
    assert item.provision_id == "provision:clause-1"
    assert item.version_id == "version:clause-1:1"
    assert item.level is ProvisionLevel.CLAUSE
    assert item.validity.contains(QUERY_DATE)
    assert item.text == "Nội dung có hiệu lực."
    assert item.provenance[0].source_provision_id == item.provision_id


def test_evidence_rejects_invalid_snapshot_and_missing_provenance():
    expired = valid_snapshot(at=date(2024, 1, 1))
    assert not expired.validity.valid
    with pytest.raises(QueryModelError, match="must be valid"):
        evidence(snapshot=expired)
    with pytest.raises(QueryModelError, match="provenance"):
        evidence(snapshot=valid_snapshot(with_provenance=False))


def test_graph_signal_requires_an_auditable_path():
    graph_signal = (RetrievalSignal(RetrievalMethod.GRAPH, 0.7, rank=1),)
    valid_path = (
        GraphTraversalStep(
            "edge:1",
            "provision:source",
            RelationType.REFERS_TO,
            "provision:clause-1",
        ),
    )

    with pytest.raises(QueryModelError, match="graph_path"):
        evidence(signals=graph_signal)

    item = evidence(
        signals=graph_signal,
        graph_path=valid_path,
    )
    assert item.graph_path[-1].target_id == item.provision_id

    with pytest.raises(QueryModelError, match="end at"):
        evidence(
            signals=graph_signal,
            graph_path=(
                GraphTraversalStep(
                    "edge:other", "a", RelationType.REFERS_TO, "provision:other"
                ),
            ),
        )

    with pytest.raises(QueryModelError, match="contiguous"):
        evidence(
            signals=graph_signal,
            graph_path=(
                GraphTraversalStep("edge:1", "a", RelationType.REFERS_TO, "b"),
                GraphTraversalStep(
                    "edge:2", "c", RelationType.REFERS_TO, "provision:clause-1"
                ),
            ),
        )


def test_evidence_rejects_duplicate_methods_rank_and_score_errors():
    duplicate = (
        RetrievalSignal(RetrievalMethod.DENSE, 0.8),
        RetrievalSignal(RetrievalMethod.DENSE, 0.7),
    )
    with pytest.raises(QueryModelError, match="unique"):
        evidence(signals=duplicate)
    with pytest.raises(QueryModelError, match="rank"):
        replace(evidence(), rank=0)
    with pytest.raises(QueryModelError, match="final_score"):
        replace(evidence(), final_score=float("nan"))
    with pytest.raises(QueryModelError, match="graph retrieval signal"):
        replace(
            evidence(),
            graph_path=(
                GraphTraversalStep(
                    "edge:1", "a", RelationType.REFERS_TO, "provision:clause-1"
                ),
            ),
        )


@pytest.mark.parametrize("level", tuple(ProvisionLevel))
def test_every_provision_level_has_a_citation_granularity(level):
    assert citation_level_for(level).value == level.value.lower()


def test_document_and_provision_citations_have_distinct_identity_rules():
    document_citation = Citation(
        "citation:document",
        "evidence:1",
        "document:law",
        CitationLevel.DOCUMENT,
        "Luật kiểm thử",
    )
    assert document_citation.provision_id is None

    with pytest.raises(QueryModelError, match="cannot claim"):
        replace(document_citation, provision_id="provision:clause-1")
    with pytest.raises(QueryModelError, match="version_id"):
        Citation(
            "citation:invalid",
            "evidence:1",
            "document:law",
            CitationLevel.CLAUSE,
            "Khoản 1 Điều 2",
            provision_id="provision:clause-1",
        )


def test_verification_preserves_ordered_typed_issues():
    warning = VerificationIssue(
        VerificationIssueCode.CITATION_TEXT_UNSUPPORTED,
        VerificationSeverity.WARNING,
        "Trích đoạn chưa đủ hỗ trợ kết luận.",
        claim_id="claim:1",
        citation_id="citation:1",
        evidence_id="evidence:1",
    )
    conflict = VerificationIssue(
        VerificationIssueCode.CONFLICTING_EVIDENCE,
        VerificationSeverity.WARNING,
        "Hai bằng chứng cần được đối chiếu thủ công.",
    )
    result = VerificationResult(
        "query:1",
        VerificationDecision.NEEDS_REVIEW,
        issues=(warning, conflict),
        verified_evidence_ids=("evidence:1",),
    )

    assert tuple(item.code for item in result.issues) == (
        VerificationIssueCode.CITATION_TEXT_UNSUPPORTED,
        VerificationIssueCode.CONFLICTING_EVIDENCE,
    )


def test_verification_decision_rejects_inconsistent_outcomes():
    error = VerificationIssue(
        VerificationIssueCode.CITATION_VERSION_MISMATCH,
        VerificationSeverity.ERROR,
        "Sai phiên bản.",
        citation_id="citation:1",
    )
    with pytest.raises(QueryModelError, match="passed"):
        VerificationResult(
            "query:1", VerificationDecision.PASSED, issues=(error,)
        )
    with pytest.raises(QueryModelError, match="failed"):
        VerificationResult("query:1", VerificationDecision.FAILED)
    with pytest.raises(QueryModelError, match="disjoint"):
        VerificationResult(
            "query:1",
            VerificationDecision.FAILED,
            rejected_citation_ids=("citation:1",),
            verified_citation_ids=("citation:1",),
        )


def test_complete_answer_links_query_evidence_claim_citation_and_verification():
    result = answered_result()

    assert result.status is AnswerStatus.ANSWERED
    assert result.evidence[0].snapshot.at == result.query.at
    assert result.claims[0].citation_ids == (result.citations[0].id,)
    assert result.verification.decision is VerificationDecision.PASSED


def test_answer_rejects_foreign_query_date_and_missing_references():
    with pytest.raises(QueryModelError, match="answer query"):
        answered_result(evidence=(evidence(query_id="query:other"),))
    with pytest.raises(QueryModelError, match="resolved query date"):
        answered_result(
            evidence=(evidence(snapshot=valid_snapshot(at=date(2023, 5, 31))),)
        )
    with pytest.raises(QueryModelError, match="unknown evidence"):
        answered_result(citations=(citation(evidence_id="evidence:missing"),))
    with pytest.raises(QueryModelError, match="unknown citations"):
        answered_result(
            claims=(AnswerClaim("claim:1", "Kết luận", ("citation:missing",)),)
        )


def test_answered_status_cannot_hide_failed_or_partial_verification():
    error = VerificationIssue(
        VerificationIssueCode.CITATION_VERSION_MISMATCH,
        VerificationSeverity.ERROR,
        "Citation trỏ sai phiên bản.",
        citation_id="citation:1",
        evidence_id="evidence:1",
    )
    failed = VerificationResult(
        "query:1",
        VerificationDecision.FAILED,
        issues=(error,),
        verified_evidence_ids=("evidence:1",),
        rejected_citation_ids=("citation:1",),
    )
    with pytest.raises(QueryModelError, match="passed verification"):
        answered_result(verification=failed)

    partial = VerificationResult(
        "query:1",
        VerificationDecision.PASSED,
        verified_evidence_ids=("evidence:1",),
    )
    with pytest.raises(QueryModelError, match="every citation"):
        answered_result(verification=partial)

    with pytest.raises(QueryModelError, match="every claim"):
        answered_result(
            claims=(AnswerClaim("claim:1", "Kết luận chưa có citation"),)
        )

    uncited = citation(identifier="citation:unused")
    all_verified = replace(
        passed_verification(),
        verified_citation_ids=("citation:1", "citation:unused"),
    )
    with pytest.raises(QueryModelError, match="support a claim"):
        answered_result(
            citations=(citation(), uncited), verification=all_verified
        )

    unverified_evidence = replace(
        passed_verification(), verified_evidence_ids=()
    )
    with pytest.raises(QueryModelError, match="cited evidence"):
        answered_result(verification=unverified_evidence)


def test_wrong_claimed_version_can_be_retained_with_a_verifier_issue():
    wrong_citation = citation(version_id="version:clause-1:old")
    issue = VerificationIssue(
        VerificationIssueCode.CITATION_VERSION_MISMATCH,
        VerificationSeverity.WARNING,
        "Citation không trỏ đến phiên bản đã được truy xuất.",
        claim_id="claim:1",
        citation_id=wrong_citation.id,
        evidence_id="evidence:1",
    )
    review = VerificationResult(
        "query:1",
        VerificationDecision.NEEDS_REVIEW,
        issues=(issue,),
        verified_evidence_ids=("evidence:1",),
        rejected_citation_ids=(wrong_citation.id,),
    )

    result = answered_result(
        status=AnswerStatus.NEEDS_REVIEW,
        citations=(wrong_citation,),
        verification=review,
    )

    assert result.citations[0].version_id == "version:clause-1:old"
    assert (
        result.verification.issues[0].code
        is VerificationIssueCode.CITATION_VERSION_MISMATCH
    )


@pytest.mark.parametrize(
    ("changes", "message"),
    (
        ({"document_id": "document:wrong"}, "document"),
        ({"provision_id": "provision:wrong"}, "provision"),
        ({"version_id": "version:wrong"}, "version"),
        ({"level": CitationLevel.ARTICLE}, "level"),
        ({"supporting_text": "Đoạn không có trong bằng chứng."}, "text"),
    ),
)
def test_passed_answer_rejects_citation_claims_that_disagree_with_evidence(
    changes, message
):
    with pytest.raises(QueryModelError, match=message):
        answered_result(citations=(replace(citation(), **changes),))


def test_unresolved_query_can_only_produce_an_auditable_review_result():
    query = TemporalQuery(
        "query:unresolved",
        "Quy định này còn hiệu lực không?",
        None,
        TemporalResolution.UNRESOLVED,
    )
    issue = VerificationIssue(
        VerificationIssueCode.QUERY_TIME_UNRESOLVED,
        VerificationSeverity.WARNING,
        "Không xác định được mốc thời gian cần kiểm tra.",
    )
    verification = VerificationResult(
        query.id,
        VerificationDecision.NEEDS_REVIEW,
        issues=(issue,),
    )

    result = AnswerResult(
        "answer:unresolved",
        query,
        "Cần cung cấp mốc thời gian để xác định hiệu lực.",
        AnswerStatus.NEEDS_REVIEW,
        (),
        (),
        (),
        verification,
    )

    assert not result.query.temporal_ready
    assert (
        result.verification.issues[0].code
        is VerificationIssueCode.QUERY_TIME_UNRESOLVED
    )


def test_answer_rejects_unknown_verification_references():
    unknown = VerificationResult(
        "query:1",
        VerificationDecision.PASSED,
        verified_evidence_ids=("evidence:missing",),
        verified_citation_ids=("citation:1",),
    )
    with pytest.raises(QueryModelError, match="unknown evidence"):
        answered_result(verification=unknown)


def test_query_models_are_frozen_and_preserve_vietnamese_text():
    result = answered_result()

    assert "hiệu lực" in result.text
    with pytest.raises(FrozenInstanceError):
        result.text = "Nội dung khác"
