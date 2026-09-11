"""Backend-neutral behavior suite; extend UOW_FACTORIES for each new adapter."""
from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.memory import MemoryUnitOfWork
from legal_crawler.ports import RepositoryConflictError, WriteDisposition
from legal_crawler.temporal import (
    LegalDocument,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
)

UOW_FACTORIES = (pytest.param(MemoryUnitOfWork, id="memory"),)


@pytest.fixture(params=UOW_FACTORIES)
def uow(request):
    """Create a clean unit of work for every backend contract assertion."""
    return request.param()


def law() -> LegalDocument:
    return LegalDocument(
        "document:law",
        "01/2020/QH",
        "Luật kiểm thử",
        effective_from=date(2020, 1, 1),
    )


def article() -> Provision:
    return Provision(
        "provision:article-1",
        "document:law",
        ProvisionLevel.ARTICLE,
        "Điều 1",
        None,
    )


def initial_version() -> ProvisionVersion:
    return ProvisionVersion(
        "version:article-1:1",
        "provision:article-1",
        1,
        "Nội dung có hiệu lực",
        TemporalInterval(date(2020, 1, 1)),
    )


def test_contract_exact_replay_is_unchanged_and_conflict_is_explicit(uow):
    item = law()

    assert uow.documents.put(item).disposition is WriteDisposition.CREATED
    assert uow.documents.put(item).disposition is WriteDisposition.UNCHANGED
    with pytest.raises(RepositoryConflictError):
        uow.documents.put(replace(item, title="Không được ghi đè"))
    assert uow.documents.get(item.id) == item


def test_contract_batch_failure_publishes_no_partial_state(uow):
    existing = law()
    uow.documents.put(existing)

    with pytest.raises(RepositoryConflictError):
        uow.documents.put_many(
            (
                replace(existing, id="document:new", number="02/2020/QH"),
                replace(existing, title="Xung đột"),
            )
        )

    assert uow.documents.get("document:new") is None
    assert uow.documents.get(existing.id) == existing


def test_contract_transaction_commit_is_visible_to_snapshot_reads(uow):
    with uow.transaction():
        uow.documents.put(law())
        uow.provisions.put(article())
        uow.versions.put(initial_version())

    result = uow.snapshots.snapshot("provision:article-1", date(2021, 1, 1))
    assert result.text == "Nội dung có hiệu lực"


def test_contract_exception_rolls_back_every_write(uow):
    with pytest.raises(RuntimeError):
        with uow.transaction():
            uow.documents.put(law())
            uow.provisions.put(article())
            raise RuntimeError("rollback")

    assert uow.documents.get("document:law") is None
    assert uow.provisions.get("provision:article-1") is None
