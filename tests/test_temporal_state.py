from datetime import date

import pytest

from legal_crawler.temporal import (
    LegalDocument,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
    TemporalState,
    TemporalStateError,
)


def test_state_rejects_unknown_document_parent_and_cross_document_parent():
    state = TemporalState()
    state.add_document(LegalDocument("doc-1", "01", "Văn bản 1"))
    state.add_document(LegalDocument("doc-2", "02", "Văn bản 2"))
    state.add_provision(
        Provision("chapter", "doc-1", ProvisionLevel.CHAPTER, "Chương I", None)
    )

    with pytest.raises(TemporalStateError, match="unknown document"):
        state.add_provision(
            Provision("orphan-doc", "missing", ProvisionLevel.ARTICLE, "Điều 1", None)
        )
    with pytest.raises(TemporalStateError, match="unknown parent"):
        state.add_provision(
            Provision("orphan", "doc-1", ProvisionLevel.ARTICLE, "Điều 2", "missing")
        )
    with pytest.raises(TemporalStateError, match="share a document"):
        state.add_provision(
            Provision("cross-doc", "doc-2", ProvisionLevel.ARTICLE, "Điều 3", "chapter")
        )


def test_insertion_anchor_must_be_an_existing_sibling():
    state = TemporalState()
    state.add_document(LegalDocument("doc", "01", "Văn bản"))
    state.add_provision(
        Provision("article-1", "doc", ProvisionLevel.ARTICLE, "Điều 1", None, 1)
    )
    state.add_provision(
        Provision("clause-1", "doc", ProvisionLevel.CLAUSE, "Khoản 1", "article-1", 1)
    )

    with pytest.raises(TemporalStateError, match="unknown insertion anchor"):
        state.add_provision(
            Provision(
                "clause-2",
                "doc",
                ProvisionLevel.CLAUSE,
                "Khoản 2",
                "article-1",
                inserted_after_id="missing",
            )
        )
    with pytest.raises(TemporalStateError, match="must be a sibling"):
        state.add_provision(
            Provision(
                "article-2",
                "doc",
                ProvisionLevel.ARTICLE,
                "Điều 2",
                None,
                inserted_after_id="clause-1",
            )
        )


def test_version_requires_existing_provision_and_exact_duplicate_is_idempotent():
    state = TemporalState()
    state.add_document(LegalDocument("doc", "01", "Văn bản"))
    version = ProvisionVersion(
        "version:article:1",
        "article",
        1,
        "Nội dung",
        TemporalInterval(date(2020, 1, 1)),
    )

    with pytest.raises(TemporalStateError, match="unknown provision"):
        state.add_version(version)

    state.add_provision(
        Provision("article", "doc", ProvisionLevel.ARTICLE, "Điều 1", None)
    )
    assert state.add_version(version)
    assert state.add_version(version) is False
