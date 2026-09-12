from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.memory import MemoryLexicalRepository
from legal_crawler.ports import (
    LexicalRecord,
    LexicalRepository,
    LexicalSearchQuery,
    RepositoryConflictError,
    WriteDisposition,
)
from legal_crawler.temporal import ProvisionLevel, TemporalInterval


def record(
    identifier: str,
    text: str,
    *,
    start: date = date(2020, 1, 1),
    end: date | None = None,
    document_id: str = "doc",
    level: ProvisionLevel = ProvisionLevel.ARTICLE,
) -> LexicalRecord:
    return LexicalRecord(
        identifier,
        f"version:{identifier}",
        f"provision:{identifier}",
        document_id,
        text,
        TemporalInterval(start, end),
        level,
    )


def test_memory_lexical_repository_is_idempotent_and_conflict_safe():
    repository = MemoryLexicalRepository()
    item = record("a", "Xử phạt giao thông")

    assert isinstance(repository, LexicalRepository)
    assert repository.put(item).disposition is WriteDisposition.CREATED
    assert repository.put(item).disposition is WriteDisposition.UNCHANGED
    with pytest.raises(RepositoryConflictError):
        repository.put(replace(item, text="Nội dung khác"))
    assert repository.delete(item.id)
    assert not repository.delete(item.id)


def test_bm25_filters_time_document_and_level_before_ranking():
    repository = MemoryLexicalRepository()
    expected = record("expected", "mức xử phạt giao thông đường bộ")
    expired = record("expired", "xử phạt giao thông", end=date(2022, 1, 1))
    wrong_document = record("other-doc", "xử phạt giao thông", document_id="other")
    wrong_level = record("clause", "xử phạt giao thông", level=ProvisionLevel.CLAUSE)
    repository.put(expected)
    repository.put(expired)
    repository.put(wrong_document)
    repository.put(wrong_level)

    matches = repository.search(
        LexicalSearchQuery(
            "XỬ PHẠT giao thông",
            date(2023, 1, 1),
            document_ids=("doc",),
            levels=frozenset({ProvisionLevel.ARTICLE}),
        )
    )

    assert [item.record.id for item in matches] == ["expected"]
    assert matches[0].score > 0


def test_bm25_is_deterministic_and_excludes_zero_score_records():
    repository = MemoryLexicalRepository()
    repository.put(record("b", "thuế giá trị gia tăng"))
    repository.put(record("a", "thuế giá trị gia tăng"))
    repository.put(record("irrelevant", "giao thông đường bộ"))

    matches = repository.search(LexicalSearchQuery("thuế", date(2023, 1, 1)))

    assert [item.record.id for item in matches] == ["a", "b"]


@pytest.mark.parametrize("changes", ({"limit": 0}, {"at": "2023-01-01"}))
def test_lexical_query_rejects_invalid_boundaries(changes):
    values = {"text": "query", "at": date(2023, 1, 1)}
    values.update(changes)
    with pytest.raises(ValueError):
        LexicalSearchQuery(**values)
