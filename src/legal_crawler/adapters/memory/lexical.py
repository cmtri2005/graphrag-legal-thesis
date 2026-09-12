"""Deterministic in-memory BM25 index for local retrieval tests."""
from __future__ import annotations

import math
import re
from collections import Counter

from legal_crawler.ports.repositories import (
    RepositoryConflictError,
    WriteDisposition,
    WriteResult,
)
from legal_crawler.ports.retrieval import (
    LexicalMatch,
    LexicalRecord,
    LexicalSearchQuery,
)

_TOKEN = re.compile(r"\w+", re.UNICODE)


class MemoryLexicalRepository:
    """Small BM25 implementation with point-in-time filtering before ranking."""

    def __init__(self, *, k1: float = 1.2, b: float = 0.75) -> None:
        if isinstance(k1, bool) or not isinstance(k1, (int, float)) or not math.isfinite(k1) or k1 <= 0:
            raise ValueError("BM25 k1 must be finite and positive")
        if isinstance(b, bool) or not isinstance(b, (int, float)) or not math.isfinite(b) or not 0 <= b <= 1:
            raise ValueError("BM25 b must be finite and between zero and one")
        self._k1 = k1
        self._b = b
        self._records: dict[str, LexicalRecord] = {}

    def put(self, record: LexicalRecord) -> WriteResult:
        existing = self._records.get(record.id)
        if existing is not None:
            if existing != record:
                raise RepositoryConflictError(
                    f"lexical record id {record.id} already has different content"
                )
            return WriteResult(record.id, WriteDisposition.UNCHANGED)
        self._records[record.id] = record
        return WriteResult(record.id, WriteDisposition.CREATED)

    def delete(self, record_id: str) -> bool:
        return self._records.pop(record_id, None) is not None

    def search(self, query: LexicalSearchQuery) -> tuple[LexicalMatch, ...]:
        document_filter = set(query.document_ids)
        eligible = tuple(
            record
            for record in self._records.values()
            if record.validity.contains(query.at)
            and (not document_filter or record.document_id in document_filter)
            and (not query.levels or record.level in query.levels)
        )
        query_terms = tuple(dict.fromkeys(_tokenize(query.text)))
        if not eligible or not query_terms:
            return ()

        tokenized = {record.id: _tokenize(record.text) for record in eligible}
        average_length = sum(map(len, tokenized.values())) / len(eligible)
        document_frequency = {
            term: sum(term in terms for terms in tokenized.values())
            for term in query_terms
        }
        matches: list[LexicalMatch] = []
        for record in eligible:
            terms = tokenized[record.id]
            frequencies = Counter(terms)
            score = sum(
                self._term_score(
                    frequencies[term],
                    document_frequency[term],
                    len(terms),
                    average_length,
                    len(eligible),
                )
                for term in query_terms
                if frequencies[term]
            )
            if score > 0:
                matches.append(LexicalMatch(record, score))
        matches.sort(key=lambda item: (-item.score, item.record.id))
        return tuple(matches[: query.limit])

    def _term_score(
        self,
        frequency: int,
        document_frequency: int,
        length: int,
        average_length: float,
        corpus_size: int,
    ) -> float:
        inverse_frequency = math.log(
            1 + (corpus_size - document_frequency + 0.5) / (document_frequency + 0.5)
        )
        length_ratio = length / average_length if average_length else 0.0
        denominator = frequency + self._k1 * (1 - self._b + self._b * length_ratio)
        return inverse_frequency * frequency * (self._k1 + 1) / denominator


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(match.group(0).casefold() for match in _TOKEN.finditer(text))
