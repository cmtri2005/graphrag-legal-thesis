"""Storage-neutral contracts for lexical retrieval and model scoring."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Protocol, Sequence, runtime_checkable

from legal_crawler.query.models import RetrievedEvidence, TemporalQuery
from legal_crawler.temporal.models import ProvisionLevel, TemporalInterval

from .repositories import WriteResult


@dataclass(frozen=True, slots=True)
class LexicalRecord:
    """Searchable text tied to one exact provision version."""

    id: str
    version_id: str
    provision_id: str
    document_id: str
    text: str
    validity: TemporalInterval
    level: ProvisionLevel

    def __post_init__(self) -> None:
        for value, name in (
            (self.id, "lexical record id"),
            (self.version_id, "lexical record version_id"),
            (self.provision_id, "lexical record provision_id"),
            (self.document_id, "lexical record document_id"),
            (self.text, "lexical record text"),
        ):
            _required_text(value, name)
        if not isinstance(self.validity, TemporalInterval):
            raise ValueError("lexical record validity must be a TemporalInterval")
        if not isinstance(self.level, ProvisionLevel):
            raise ValueError("lexical record level must be a ProvisionLevel")


@dataclass(frozen=True, slots=True)
class LexicalSearchQuery:
    text: str
    at: date
    limit: int = 10
    document_ids: tuple[str, ...] = ()
    levels: frozenset[ProvisionLevel] = frozenset()

    def __post_init__(self) -> None:
        _required_text(self.text, "lexical query text")
        if type(self.at) is not date:
            raise ValueError("lexical query at must be a date")
        if isinstance(self.limit, bool) or not isinstance(self.limit, int) or self.limit < 1:
            raise ValueError("lexical query limit must be a positive integer")
        if not isinstance(self.document_ids, tuple):
            raise ValueError("lexical query document_ids must be a tuple")
        for item in self.document_ids:
            _required_text(item, "lexical query document_id")
        if len(self.document_ids) != len(set(self.document_ids)):
            raise ValueError("lexical query document_ids must not contain duplicates")
        if not isinstance(self.levels, frozenset) or any(
            not isinstance(item, ProvisionLevel) for item in self.levels
        ):
            raise ValueError("lexical query levels must contain ProvisionLevel values")


@dataclass(frozen=True, slots=True)
class LexicalMatch:
    record: LexicalRecord
    score: float

    def __post_init__(self) -> None:
        if not isinstance(self.record, LexicalRecord):
            raise ValueError("lexical match record must be a LexicalRecord")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise ValueError("lexical match score must be a number")
        if not math.isfinite(float(self.score)) or self.score < 0:
            raise ValueError("lexical match score must be finite and non-negative")


@runtime_checkable
class LexicalRepository(Protocol):
    def put(self, record: LexicalRecord) -> WriteResult:
        """Insert a record using the common idempotent write contract."""
        ...

    def delete(self, record_id: str) -> bool:
        ...

    def search(self, query: LexicalSearchQuery) -> tuple[LexicalMatch, ...]:
        ...


@runtime_checkable
class QueryEncoder(Protocol):
    @property
    def model(self) -> str:
        ...

    def encode(self, text: str) -> tuple[float, ...]:
        ...


@runtime_checkable
class EvidenceReranker(Protocol):
    def score(
        self,
        query: TemporalQuery,
        candidates: Sequence[RetrievedEvidence],
    ) -> Sequence[float]:
        """Return one finite score for every candidate in input order."""
        ...


def _required_text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
