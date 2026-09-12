"""Deterministic verifier for temporal evidence and answer citations."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from typing import Iterable

from .models import (
    AnswerClaim,
    Citation,
    CitationLevel,
    RetrievedEvidence,
    TemporalQuery,
    VerificationDecision,
    VerificationIssue,
    VerificationIssueCode,
    VerificationResult,
    VerificationSeverity,
    citation_level_for,
)


class TemporalVerifier:
    """Check that every claim cites the exact evidence valid at query time."""

    def verify(
        self,
        query: TemporalQuery,
        evidence: Iterable[RetrievedEvidence],
        citations: Iterable[Citation],
        claims: Iterable[AnswerClaim],
    ) -> VerificationResult:
        evidence_items = tuple(evidence)
        citation_items = tuple(citations)
        claim_items = tuple(claims)
        _require_unique_ids(evidence_items, "evidence")
        _require_unique_ids(citation_items, "citation")
        _require_unique_ids(claim_items, "claim")

        evidence_by_id = {item.id: item for item in evidence_items}
        citation_by_id = {item.id: item for item in citation_items}
        issues: list[VerificationIssue] = []
        invalid_evidence: set[str] = set()
        invalid_evidence_codes: dict[str, set[VerificationIssueCode]] = defaultdict(set)
        rejected_citations: set[str] = set()

        if query.at is None:
            issues.append(
                _issue(
                    VerificationIssueCode.QUERY_TIME_UNRESOLVED,
                    "query time is unresolved",
                )
            )

        versions_by_provision: dict[str, set[str]] = {}
        for item in evidence_items:
            versions_by_provision.setdefault(item.provision_id, set()).add(item.version_id)
            if (
                query.at is None
                or item.query_id != query.id
                or item.snapshot.at != query.at
                or not item.validity.contains(query.at)
            ):
                invalid_evidence.add(item.id)
                invalid_evidence_codes[item.id].add(
                    VerificationIssueCode.EVIDENCE_OUTSIDE_QUERY_TIME
                )
                issues.append(
                    _issue(
                        VerificationIssueCode.EVIDENCE_OUTSIDE_QUERY_TIME,
                        "evidence does not belong to the query's point-in-time snapshot",
                        evidence_id=item.id,
                    )
                )
            if not item.provenance:
                invalid_evidence.add(item.id)
                invalid_evidence_codes[item.id].add(
                    VerificationIssueCode.EVIDENCE_MISSING_PROVENANCE
                )
                issues.append(
                    _issue(
                        VerificationIssueCode.EVIDENCE_MISSING_PROVENANCE,
                        "evidence has no source provenance",
                        evidence_id=item.id,
                    )
                )
        for provision_id, version_ids in sorted(versions_by_provision.items()):
            if len(version_ids) > 1:
                affected = sorted(
                    item.id for item in evidence_items if item.provision_id == provision_id
                )
                invalid_evidence.update(affected)
                for evidence_id in affected:
                    invalid_evidence_codes[evidence_id].add(
                        VerificationIssueCode.CONFLICTING_EVIDENCE
                    )
                    issues.append(
                        _issue(
                            VerificationIssueCode.CONFLICTING_EVIDENCE,
                            "multiple versions of one provision appear in the same answer",
                            evidence_id=evidence_id,
                        )
                    )

        for item in citation_items:
            source = evidence_by_id.get(item.evidence_id)
            if source is None:
                rejected_citations.add(item.id)
                issues.append(
                    _issue(
                        VerificationIssueCode.CITATION_EVIDENCE_NOT_FOUND,
                        "citation refers to missing evidence",
                        citation_id=item.id,
                        evidence_id=item.evidence_id,
                    )
                )
                continue
            citation_issues = self._verify_citation(item, source)
            if source.id in invalid_evidence:
                for code in sorted(
                    invalid_evidence_codes[source.id], key=lambda value: value.value
                ):
                    citation_issues.append(
                        _issue(
                            code,
                            "citation relies on evidence that failed verification",
                            citation_id=item.id,
                            evidence_id=source.id,
                        )
                    )
            if citation_issues:
                rejected_citations.add(item.id)
                issues.extend(citation_issues)

        for claim in claim_items:
            if not claim.citation_ids:
                issues.append(
                    _issue(
                        VerificationIssueCode.CLAIM_WITHOUT_CITATION,
                        "claim has no citation",
                        claim_id=claim.id,
                    )
                )
                continue
            for citation_id in claim.citation_ids:
                if citation_id not in citation_by_id:
                    issues.append(
                        _issue(
                            VerificationIssueCode.CITATION_EVIDENCE_NOT_FOUND,
                            "claim refers to a missing citation",
                            claim_id=claim.id,
                            citation_id=citation_id,
                        )
                    )

        verified_citations = tuple(
            item.id for item in citation_items if item.id not in rejected_citations
        )
        verified_evidence = tuple(
            item.id for item in evidence_items if item.id not in invalid_evidence
        )
        rejected = tuple(item.id for item in citation_items if item.id in rejected_citations)
        if any(item.severity is VerificationSeverity.ERROR for item in issues):
            decision = VerificationDecision.FAILED
        elif issues:
            decision = VerificationDecision.NEEDS_REVIEW
        else:
            decision = VerificationDecision.PASSED
        return VerificationResult(
            query.id,
            decision,
            tuple(issues),
            verified_evidence,
            verified_citations,
            rejected,
        )

    @staticmethod
    def _verify_citation(
        citation: Citation, evidence: RetrievedEvidence
    ) -> list[VerificationIssue]:
        issues: list[VerificationIssue] = []
        checks = (
            (
                citation.document_id != evidence.document_id,
                VerificationIssueCode.CITATION_DOCUMENT_MISMATCH,
                "citation document does not match its evidence",
            ),
            (
                citation.level is not CitationLevel.DOCUMENT
                and citation.provision_id != evidence.provision_id,
                VerificationIssueCode.CITATION_PROVISION_MISMATCH,
                "citation provision does not match its evidence",
            ),
            (
                citation.level is not CitationLevel.DOCUMENT
                and citation.version_id != evidence.version_id,
                VerificationIssueCode.CITATION_VERSION_MISMATCH,
                "citation version does not match its evidence",
            ),
            (
                citation.level is not CitationLevel.DOCUMENT
                and citation.level is not citation_level_for(evidence.level),
                VerificationIssueCode.CITATION_LEVEL_MISMATCH,
                "citation granularity does not match its evidence",
            ),
            (
                citation.supporting_text is not None
                and _normalize(citation.supporting_text) not in _normalize(evidence.text),
                VerificationIssueCode.CITATION_TEXT_UNSUPPORTED,
                "citation supporting text is absent from its exact version",
            ),
        )
        for failed, code, message in checks:
            if failed:
                issues.append(
                    _issue(
                        code,
                        message,
                        citation_id=citation.id,
                        evidence_id=evidence.id,
                    )
                )
        return issues


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def _issue(
    code: VerificationIssueCode,
    message: str,
    *,
    claim_id: str | None = None,
    citation_id: str | None = None,
    evidence_id: str | None = None,
) -> VerificationIssue:
    return VerificationIssue(
        code,
        VerificationSeverity.ERROR,
        message,
        claim_id,
        citation_id,
        evidence_id,
    )


def _require_unique_ids(items: tuple[object, ...], name: str) -> None:
    identifiers = [getattr(item, "id", None) for item in items]
    duplicates = sorted(item for item, count in Counter(identifiers).items() if count > 1)
    if duplicates:
        raise ValueError(f"{name} IDs must be unique: {duplicates}")
