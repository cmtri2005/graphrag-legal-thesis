from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from legal_crawler.adapters.memory import (
    MemoryLexicalRepository,
    MemoryUnitOfWork,
    MemoryVectorRepository,
)
from legal_crawler.ports import LexicalRecord, VersionEmbedding
from legal_crawler.query import RetrievalMethod, TemporalQuery, TemporalResolution
from legal_crawler.retrieval import (
    RetrievalConfig,
    RetrievalError,
    RetrievalWarningCode,
    TemporalHybridRetriever,
)
from legal_crawler.temporal import (
    ExtractionMethod,
    GraphEdge,
    LegalDocument,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
)


class Encoder:
    model = "dense-model"

    def encode(self, text: str) -> tuple[float, ...]:
        return (1.0, 0.0)


class ReverseReranker:
    def score(self, query, candidates):
        return tuple(float(index) for index, _ in enumerate(candidates))


class BrokenReranker:
    def score(self, query, candidates):
        return (float("nan"),)


def setup_repositories():
    uow = MemoryUnitOfWork()
    lexical = MemoryLexicalRepository()
    vectors = MemoryVectorRepository()
    uow.documents.put(LegalDocument("doc", "01/2020", "Luật", effective_from=date(2020, 1, 1)))
    provenance = (
        Provenance("doc", ExtractionMethod.SOURCE_METADATA, evidence_text="nguồn"),
    )
    provisions = (
        Provision("a", "doc", ProvisionLevel.ARTICLE, "Điều 1", None, 1),
        Provision("b", "doc", ProvisionLevel.ARTICLE, "Điều 2", None, 2),
        Provision("c", "doc", ProvisionLevel.ARTICLE, "Điều 3", None, 3),
    )
    texts = {
        "a": "xử phạt giao thông đường bộ",
        "b": "giao thông và giấy phép lái xe",
        "c": "quy định liên quan được dẫn chiếu",
    }
    for provision in provisions:
        uow.provisions.put(provision)
        version = ProvisionVersion(
            f"version:{provision.id}:1",
            provision.id,
            1,
            texts[provision.id],
            TemporalInterval(date(2020, 1, 1)),
            provenance=provenance,
        )
        uow.versions.put(version)
        lexical.put(
            LexicalRecord(
                f"lexical:{provision.id}",
                version.id,
                provision.id,
                "doc",
                version.text,
                version.validity,
                provision.level,
            )
        )
    vectors.put(
        VersionEmbedding(
            "embedding:b",
            "version:b:1",
            "b",
            "doc",
            "dense-model",
            (1.0, 0.0),
            TemporalInterval(date(2020, 1, 1)),
            ProvisionLevel.ARTICLE,
            provenance,
        )
    )
    uow.graph.put(GraphEdge("a", "c", RelationType.REFERS_TO))
    return uow, lexical, vectors


def query() -> TemporalQuery:
    return TemporalQuery(
        "query:1",
        "xử phạt giao thông",
        date(2023, 1, 1),
        TemporalResolution.EXPLICIT,
        document_ids=("doc",),
        levels=frozenset({ProvisionLevel.ARTICLE}),
    )


def test_hybrid_retrieval_preserves_signals_and_auditable_graph_path():
    uow, lexical, vectors = setup_repositories()
    retriever = TemporalHybridRetriever(
        uow.snapshots,
        lexical=lexical,
        vectors=vectors,
        encoder=Encoder(),
        graph=uow.graph,
        config=RetrievalConfig(final_limit=3, fusion_limit=3),
    )

    run = retriever.retrieve(query())

    by_provision = {item.provision_id: item for item in run.evidence}
    assert not run.warnings
    assert set(by_provision) == {"a", "b", "c"}
    assert {signal.method for signal in by_provision["b"].signals} == {
        RetrievalMethod.LEXICAL,
        RetrievalMethod.DENSE,
    }
    graph_evidence = by_provision["c"]
    assert graph_evidence.graph_path[0].source_id == "a"
    assert graph_evidence.graph_path[-1].target_id == "c"
    assert graph_evidence.signals[0].method is RetrievalMethod.GRAPH


def test_reranker_adds_signal_and_reassigns_final_ranks():
    uow, lexical, _ = setup_repositories()
    retriever = TemporalHybridRetriever(
        uow.snapshots,
        lexical=lexical,
        reranker=ReverseReranker(),
        config=RetrievalConfig(graph_depth=0, final_limit=2, fusion_limit=3, rerank_weight=1),
    )

    evidence = retriever.retrieve(query()).evidence

    assert [item.rank for item in evidence] == [1, 2]
    assert all(item.signals[-1].method is RetrievalMethod.RERANK for item in evidence)
    assert evidence[0].signals[-1].score > evidence[1].signals[-1].score


def test_graph_expansion_supports_multiple_auditable_hops():
    uow, lexical, _ = setup_repositories()
    provenance = (
        Provenance("doc", ExtractionMethod.SOURCE_METADATA, evidence_text="nguồn"),
    )
    provision = Provision("d", "doc", ProvisionLevel.ARTICLE, "Điều 4", None, 4)
    uow.provisions.put(provision)
    uow.versions.put(
        ProvisionVersion(
            "version:d:1",
            "d",
            1,
            "quy định được dẫn chiếu hai bước",
            TemporalInterval(date(2020, 1, 1)),
            provenance=provenance,
        )
    )
    uow.graph.put(GraphEdge("c", "d", RelationType.REFERS_TO))
    retriever = TemporalHybridRetriever(
        uow.snapshots,
        lexical=lexical,
        graph=uow.graph,
        config=RetrievalConfig(graph_depth=2, final_limit=4, fusion_limit=4),
    )

    result = retriever.retrieve(query())
    item = next(evidence for evidence in result.evidence if evidence.provision_id == "d")

    assert [step.source_id for step in item.graph_path] == ["a", "c"]
    assert [step.target_id for step in item.graph_path] == ["c", "d"]


def test_reranker_rejects_invalid_output_instead_of_hiding_it():
    uow, lexical, _ = setup_repositories()
    retriever = TemporalHybridRetriever(
        uow.snapshots,
        lexical=lexical,
        reranker=BrokenReranker(),
        config=RetrievalConfig(graph_depth=0),
    )

    with pytest.raises(RetrievalError, match="one score|finite"):
        retriever.retrieve(query())


def test_stale_derived_record_is_rejected_after_snapshot_revalidation():
    uow, lexical, _ = setup_repositories()
    stale = LexicalRecord(
        "stale",
        "version:a:old",
        "a",
        "doc",
        "xử phạt",
        TemporalInterval(date(2020, 1, 1)),
        ProvisionLevel.ARTICLE,
    )
    lexical.put(stale)
    retriever = TemporalHybridRetriever(uow.snapshots, lexical=lexical)

    run = retriever.retrieve(query())

    assert "version:a:old" not in {item.version_id for item in run.evidence}
    assert any(item.code is RetrievalWarningCode.STALE_LEXICAL_RECORD for item in run.warnings)


def test_unresolved_time_and_incomplete_dense_configuration_fail_loudly():
    uow, lexical, vectors = setup_repositories()
    with pytest.raises(ValueError, match="together"):
        TemporalHybridRetriever(uow.snapshots, lexical=lexical, vectors=vectors)
    retriever = TemporalHybridRetriever(uow.snapshots, lexical=lexical)
    unresolved = replace(query(), at=None, temporal_resolution=TemporalResolution.UNRESOLVED)
    with pytest.raises(RetrievalError, match="resolved"):
        retriever.retrieve(unresolved)


def test_retrieval_config_validates_ablation_parameters():
    with pytest.raises(ValueError, match="final_limit"):
        RetrievalConfig(final_limit=11, fusion_limit=10)
    with pytest.raises(ValueError, match="graph_depth"):
        RetrievalConfig(graph_depth=-1)
