from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.query import (
    AnswerClaim,
    Citation,
    CitationLevel,
    RetrievedEvidence,
    RetrievalMethod,
    RetrievalSignal,
    TemporalQuery,
    TemporalResolution,
    TemporalVerifier,
    VerificationDecision,
    VerificationIssueCode,
)
from legal_crawler.temporal import (
    ExtractionMethod,
    LegalDocument,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    SnapshotService,
    TemporalInterval,
    TemporalState,
)


AT = date(2023, 1, 1)


def artifacts():
    state = TemporalState()
    state.add_document(LegalDocument("doc", "01/2020", "Luật", effective_from=date(2020, 1, 1)))
    provision = Provision("article", "doc", ProvisionLevel.ARTICLE, "Điều 1", None)
    state.add_provision(provision)
    state.add_version(
        ProvisionVersion(
            "version:article:1",
            provision.id,
            1,
            "Người tham gia giao thông phải chấp hành tín hiệu.",
            TemporalInterval(date(2020, 1, 1)),
            provenance=(
                Provenance(
                    "doc",
                    ExtractionMethod.SOURCE_METADATA,
                    evidence_text="Người tham gia giao thông",
                ),
            ),
        )
    )
    query = TemporalQuery("query", "quy định giao thông", AT, TemporalResolution.EXPLICIT)
    evidence = RetrievedEvidence(
        "evidence",
        query.id,
        SnapshotService(state).snapshot(provision.id, AT),
        (RetrievalSignal(RetrievalMethod.LEXICAL, 1.0, 1),),
        1,
        1.0,
    )
    citation = Citation(
        "citation",
        evidence.id,
        "doc",
        CitationLevel.ARTICLE,
        "Điều 1",
        "article",
        "version:article:1",
        "NGƯỜI tham gia giao thông",
    )
    claim = AnswerClaim("claim", "Phải chấp hành tín hiệu.", (citation.id,))
    return query, evidence, citation, claim


def test_verifier_passes_exact_temporal_citation_and_unicode_text_support():
    query, evidence, citation, claim = artifacts()

    result = TemporalVerifier().verify(query, (evidence,), (citation,), (claim,))

    assert result.decision is VerificationDecision.PASSED
    assert result.verified_evidence_ids == ("evidence",)
    assert result.verified_citation_ids == ("citation",)
    assert not result.issues


@pytest.mark.parametrize(
    ("change", "code"),
    (
        ({"document_id": "wrong"}, VerificationIssueCode.CITATION_DOCUMENT_MISMATCH),
        ({"provision_id": "wrong"}, VerificationIssueCode.CITATION_PROVISION_MISMATCH),
        ({"version_id": "wrong"}, VerificationIssueCode.CITATION_VERSION_MISMATCH),
        ({"level": CitationLevel.CLAUSE}, VerificationIssueCode.CITATION_LEVEL_MISMATCH),
        ({"supporting_text": "nội dung không tồn tại"}, VerificationIssueCode.CITATION_TEXT_UNSUPPORTED),
    ),
)
def test_verifier_rejects_each_citation_mismatch(change, code):
    query, evidence, citation, claim = artifacts()
    changed = replace(citation, **change)

    result = TemporalVerifier().verify(query, (evidence,), (changed,), (claim,))

    assert result.decision is VerificationDecision.FAILED
    assert result.rejected_citation_ids == (citation.id,)
    assert code in {item.code for item in result.issues}


def test_verifier_reports_missing_evidence_and_uncited_claim():
    query, evidence, citation, _ = artifacts()
    missing = replace(citation, evidence_id="missing")
    claim = AnswerClaim("claim", "Khẳng định không nguồn")

    result = TemporalVerifier().verify(query, (evidence,), (missing,), (claim,))

    assert result.decision is VerificationDecision.FAILED
    assert {item.code for item in result.issues} == {
        VerificationIssueCode.CITATION_EVIDENCE_NOT_FOUND,
        VerificationIssueCode.CLAIM_WITHOUT_CITATION,
    }


def test_verifier_rejects_evidence_from_a_different_query_time():
    query, evidence, citation, claim = artifacts()
    other_time = replace(query, at=date(2024, 1, 1))

    result = TemporalVerifier().verify(other_time, (evidence,), (citation,), (claim,))

    assert result.decision is VerificationDecision.FAILED
    assert VerificationIssueCode.EVIDENCE_OUTSIDE_QUERY_TIME in {
        item.code for item in result.issues
    }
    assert not result.verified_evidence_ids
    assert result.rejected_citation_ids == (citation.id,)


def test_verifier_fails_unresolved_query_without_silently_choosing_a_date():
    query, evidence, citation, claim = artifacts()
    unresolved = replace(query, at=None, temporal_resolution=TemporalResolution.UNRESOLVED)

    result = TemporalVerifier().verify(unresolved, (evidence,), (citation,), (claim,))

    assert result.decision is VerificationDecision.FAILED
    assert result.issues[0].code is VerificationIssueCode.QUERY_TIME_UNRESOLVED


def test_verifier_rejects_duplicate_input_ids():
    query, evidence, citation, claim = artifacts()
    with pytest.raises(ValueError, match="unique"):
        TemporalVerifier().verify(query, (evidence, evidence), (citation,), (claim,))
