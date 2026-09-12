"""Point-in-time hybrid retrieval with auditable graph expansion."""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field, replace
from enum import Enum
from legal_crawler.ports.repositories import SnapshotRepository, TemporalGraphRepository
from legal_crawler.ports.retrieval import (
    EvidenceReranker,
    LexicalRepository,
    LexicalSearchQuery,
    QueryEncoder,
)
from legal_crawler.ports.vector import VectorRepository, VectorSearchQuery
from legal_crawler.query.models import (
    GraphTraversalStep,
    RetrievedEvidence,
    RetrievalMethod,
    RetrievalSignal,
    TemporalQuery,
)
from legal_crawler.temporal.ids import make_edge_id
from legal_crawler.temporal.models import (
    Provenance,
    ProvisionLevel,
    RelationType,
    TemporalInterval,
)
from legal_crawler.temporal.snapshot import SnapshotResult


class RetrievalError(ValueError):
    """A retrieval run cannot be executed safely."""


class RetrievalWarningCode(str, Enum):
    STALE_LEXICAL_RECORD = "stale_lexical_record"
    STALE_VECTOR_RECORD = "stale_vector_record"
    INVALID_GRAPH_TARGET = "invalid_graph_target"
    MISSING_PROVENANCE = "missing_provenance"


@dataclass(frozen=True, slots=True)
class RetrievalWarning:
    code: RetrievalWarningCode
    message: str
    entity_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, RetrievalWarningCode):
            raise ValueError("retrieval warning code must be a RetrievalWarningCode")
        _required_text(self.message, "retrieval warning message")
        _required_text(self.entity_id, "retrieval warning entity_id")


@dataclass(frozen=True, slots=True)
class RetrievalRun:
    query_id: str
    evidence: tuple[RetrievedEvidence, ...]
    warnings: tuple[RetrievalWarning, ...] = ()

    def __post_init__(self) -> None:
        _required_text(self.query_id, "retrieval run query_id")
        if not isinstance(self.evidence, tuple) or any(
            not isinstance(item, RetrievedEvidence) for item in self.evidence
        ):
            raise ValueError("retrieval run evidence must contain RetrievedEvidence")
        if not isinstance(self.warnings, tuple) or any(
            not isinstance(item, RetrievalWarning) for item in self.warnings
        ):
            raise ValueError("retrieval run warnings must contain RetrievalWarning")
        if any(item.query_id != self.query_id for item in self.evidence):
            raise ValueError("retrieval evidence must belong to the run query")


@dataclass(frozen=True, slots=True)
class RetrievalConfig:
    """Explicit knobs used by baselines, ablations and the proposed system."""

    lexical_limit: int = 50
    dense_limit: int = 50
    fusion_limit: int = 30
    final_limit: int = 10
    rrf_k: int = 60
    lexical_weight: float = 1.0
    dense_weight: float = 1.0
    graph_weight: float = 0.35
    graph_depth: int = 1
    graph_relations: frozenset[RelationType] = field(
        default_factory=lambda: frozenset(
            {RelationType.AMENDS, RelationType.REFERS_TO}
        )
    )
    rerank_weight: float = 0.5

    def __post_init__(self) -> None:
        for value, name in (
            (self.lexical_limit, "lexical_limit"),
            (self.dense_limit, "dense_limit"),
            (self.fusion_limit, "fusion_limit"),
            (self.final_limit, "final_limit"),
            (self.rrf_k, "rrf_k"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if isinstance(self.graph_depth, bool) or not isinstance(self.graph_depth, int):
            raise ValueError("graph_depth must be a non-negative integer")
        if self.graph_depth < 0:
            raise ValueError("graph_depth must be a non-negative integer")
        for value, name in (
            (self.lexical_weight, "lexical_weight"),
            (self.dense_weight, "dense_weight"),
            (self.graph_weight, "graph_weight"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a finite non-negative number")
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if (
            isinstance(self.rerank_weight, bool)
            or not isinstance(self.rerank_weight, (int, float))
            or not math.isfinite(self.rerank_weight)
            or not 0 <= self.rerank_weight <= 1
        ):
            raise ValueError("rerank_weight must be between zero and one")
        if not isinstance(self.graph_relations, frozenset) or any(
            not isinstance(item, RelationType) for item in self.graph_relations
        ):
            raise ValueError("graph_relations must contain RelationType values")
        if self.final_limit > self.fusion_limit:
            raise ValueError("final_limit cannot exceed fusion_limit")


@dataclass(slots=True)
class _Candidate:
    snapshot: SnapshotResult
    signals: dict[RetrievalMethod, RetrievalSignal]
    score: float
    graph_path: tuple[GraphTraversalStep, ...] = ()


class TemporalHybridRetriever:
    """Fuse lexical and dense hits, then optionally expand and rerank them."""

    def __init__(
        self,
        snapshots: SnapshotRepository,
        *,
        lexical: LexicalRepository | None = None,
        vectors: VectorRepository | None = None,
        encoder: QueryEncoder | None = None,
        graph: TemporalGraphRepository | None = None,
        reranker: EvidenceReranker | None = None,
        config: RetrievalConfig | None = None,
    ) -> None:
        if (vectors is None) != (encoder is None):
            raise ValueError("vectors and encoder must be configured together")
        if lexical is None and vectors is None:
            raise ValueError("at least one lexical or dense retriever is required")
        self._snapshots = snapshots
        self._lexical = lexical
        self._vectors = vectors
        self._encoder = encoder
        self._graph = graph
        self._reranker = reranker
        self._config = config or RetrievalConfig()

    def retrieve(self, query: TemporalQuery) -> RetrievalRun:
        if query.at is None:
            raise RetrievalError("query time must be resolved before retrieval")
        candidates: dict[str, _Candidate] = {}
        warnings: list[RetrievalWarning] = []
        if self._lexical is not None:
            matches = self._lexical.search(
                LexicalSearchQuery(
                    query.text,
                    query.at,
                    self._config.lexical_limit,
                    query.document_ids,
                    query.levels,
                )
            )
            for rank, match in enumerate(matches, 1):
                snapshot = self._validated_snapshot(
                    match.record.provision_id,
                    match.record.version_id,
                    query,
                    RetrievalWarningCode.STALE_LEXICAL_RECORD,
                    match.record.id,
                    warnings,
                    document_id=match.record.document_id,
                    level=match.record.level,
                    validity=match.record.validity,
                    text=match.record.text,
                )
                if snapshot is not None:
                    self._merge(
                        candidates,
                        snapshot,
                        RetrievalSignal(RetrievalMethod.LEXICAL, match.score, rank),
                        self._config.lexical_weight / (self._config.rrf_k + rank),
                    )
        if self._vectors is not None and self._encoder is not None:
            vector = self._encoder.encode(query.text)
            matches = self._vectors.search(
                VectorSearchQuery(
                    vector,
                    query.at,
                    self._encoder.model,
                    self._config.dense_limit,
                    query.document_ids,
                    query.levels,
                )
            )
            for rank, match in enumerate(matches, 1):
                snapshot = self._validated_snapshot(
                    match.record.provision_id,
                    match.record.version_id,
                    query,
                    RetrievalWarningCode.STALE_VECTOR_RECORD,
                    match.record.id,
                    warnings,
                    document_id=match.record.document_id,
                    level=match.record.level,
                    validity=match.record.validity,
                    provenance=match.record.provenance,
                )
                if snapshot is not None:
                    self._merge(
                        candidates,
                        snapshot,
                        RetrievalSignal(RetrievalMethod.DENSE, match.score, rank),
                        self._config.dense_weight / (self._config.rrf_k + rank),
                    )

        candidates = self._top_candidates(candidates, self._config.fusion_limit)
        if self._graph is not None and self._config.graph_depth:
            self._expand_graph(query, candidates, warnings)
            candidates = self._top_candidates(candidates, self._config.fusion_limit)
        evidence = self._materialize(query.id, candidates)
        if self._reranker is not None and evidence:
            evidence = self._rerank(query, evidence)
        return RetrievalRun(query.id, evidence[: self._config.final_limit], tuple(warnings))

    def _validated_snapshot(
        self,
        provision_id: str,
        version_id: str,
        query: TemporalQuery,
        stale_code: RetrievalWarningCode,
        record_id: str,
        warnings: list[RetrievalWarning],
        *,
        document_id: str,
        level: ProvisionLevel,
        validity: TemporalInterval,
        text: str | None = None,
        provenance: tuple[Provenance, ...] | None = None,
    ) -> SnapshotResult | None:
        assert query.at is not None
        snapshot = self._snapshots.snapshot(provision_id, query.at)
        if (
            not snapshot.validity.valid
            or snapshot.provision is None
            or snapshot.version is None
            or snapshot.version.id != version_id
            or snapshot.provision.document_id != document_id
            or snapshot.provision.level != level
            or snapshot.version.validity != validity
            or (text is not None and snapshot.text != text)
            or (provenance is not None and snapshot.provenance != provenance)
        ):
            warnings.append(
                RetrievalWarning(
                    stale_code,
                    "derived retrieval record does not match the authoritative snapshot",
                    record_id,
                )
            )
            return None
        if query.document_ids and snapshot.provision.document_id not in query.document_ids:
            warnings.append(RetrievalWarning(stale_code, "record violates document filter", record_id))
            return None
        if query.levels and snapshot.provision.level not in query.levels:
            warnings.append(RetrievalWarning(stale_code, "record violates level filter", record_id))
            return None
        if not snapshot.provenance:
            warnings.append(
                RetrievalWarning(
                    RetrievalWarningCode.MISSING_PROVENANCE,
                    "valid snapshot cannot become evidence without provenance",
                    provision_id,
                )
            )
            return None
        return snapshot
    @staticmethod
    def _merge(
        candidates: dict[str, _Candidate],
        snapshot: SnapshotResult,
        signal: RetrievalSignal,
        score: float,
    ) -> None:
        assert snapshot.provision is not None
        existing = candidates.get(snapshot.provision.id)
        if existing is None:
            candidates[snapshot.provision.id] = _Candidate(
                snapshot, {signal.method: signal}, score
            )
            return
        if existing.snapshot.version != snapshot.version:
            raise RetrievalError("one provision resolved to conflicting versions")
        existing.signals[signal.method] = signal
        existing.score += score

    @staticmethod
    def _top_candidates(
        candidates: dict[str, _Candidate], limit: int
    ) -> dict[str, _Candidate]:
        ordered = sorted(candidates.items(), key=lambda item: (-item[1].score, item[0]))
        return dict(ordered[:limit])

    def _expand_graph(
        self,
        query: TemporalQuery,
        candidates: dict[str, _Candidate],
        warnings: list[RetrievalWarning],
    ) -> None:
        assert query.at is not None and self._graph is not None
        seeds = sorted(candidates.items(), key=lambda item: (-item[1].score, item[0]))
        for seed_id, seed in seeds:
            frontier = [(seed_id, ())]
            visited = {seed_id}
            for depth in range(1, self._config.graph_depth + 1):
                next_frontier: list[tuple[str, tuple[GraphTraversalStep, ...]]] = []
                for node_id, path in frontier:
                    for edge in self._graph.outgoing(
                        node_id, relations=self._config.graph_relations, at=query.at
                    ):
                        target_id = edge.target_id
                        if target_id in visited:
                            continue
                        visited.add(target_id)
                        step = GraphTraversalStep(
                            make_edge_id(
                                edge.source_id,
                                edge.relation,
                                edge.target_id,
                                edge.validity.start if edge.validity else None,
                            ),
                            edge.source_id,
                            edge.relation,
                            edge.target_id,
                        )
                        target_path = (*path, step)
                        snapshot = self._snapshots.snapshot(target_id, query.at)
                        allowed = self._graph_snapshot_allowed(snapshot, query)
                        if not allowed:
                            warnings.append(
                                RetrievalWarning(
                                    RetrievalWarningCode.INVALID_GRAPH_TARGET,
                                    "graph target is not valid evidence for the query",
                                    target_id,
                                )
                            )
                        elif not snapshot.provenance:
                            warnings.append(
                                RetrievalWarning(
                                    RetrievalWarningCode.MISSING_PROVENANCE,
                                    "graph target cannot become evidence without provenance",
                                    target_id,
                                )
                            )
                        else:
                            contribution = self._config.graph_weight * seed.score / depth
                            graph_signal = RetrievalSignal(
                                RetrievalMethod.GRAPH, contribution, depth
                            )
                            existing = candidates.get(target_id)
                            if existing is None:
                                candidates[target_id] = _Candidate(
                                    snapshot,
                                    {RetrievalMethod.GRAPH: graph_signal},
                                    contribution,
                                    target_path,
                                )
                            elif RetrievalMethod.GRAPH not in existing.signals:
                                existing.signals[RetrievalMethod.GRAPH] = graph_signal
                                existing.score += contribution
                                existing.graph_path = target_path
                        if allowed:
                            next_frontier.append((target_id, target_path))
                frontier = next_frontier

    @staticmethod
    def _graph_snapshot_allowed(snapshot: SnapshotResult, query: TemporalQuery) -> bool:
        if not snapshot.validity.valid or snapshot.provision is None or snapshot.version is None:
            return False
        if query.document_ids and snapshot.provision.document_id not in query.document_ids:
            return False
        return not query.levels or snapshot.provision.level in query.levels

    @staticmethod
    def _materialize(
        query_id: str, candidates: dict[str, _Candidate]
    ) -> tuple[RetrievedEvidence, ...]:
        ordered = sorted(candidates.items(), key=lambda item: (-item[1].score, item[0]))
        return tuple(
            RetrievedEvidence(
                _evidence_id(query_id, candidate.snapshot.version.id),
                query_id,
                candidate.snapshot,
                tuple(candidate.signals[method] for method in RetrievalMethod if method in candidate.signals),
                rank,
                candidate.score,
                candidate.graph_path,
            )
            for rank, (_, candidate) in enumerate(ordered, 1)
        )

    def _rerank(
        self, query: TemporalQuery, evidence: tuple[RetrievedEvidence, ...]
    ) -> tuple[RetrievedEvidence, ...]:
        assert self._reranker is not None
        scores = tuple(self._reranker.score(query, evidence))
        if len(scores) != len(evidence):
            raise RetrievalError("reranker must return one score per candidate")
        if any(isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) for score in scores):
            raise RetrievalError("reranker scores must be finite numbers")
        maximum = max(item.final_score or 0.0 for item in evidence)
        ranked: list[RetrievedEvidence] = []
        for item, rerank_score in zip(evidence, scores):
            fused = (item.final_score or 0.0) / maximum if maximum > 0 else 0.0
            normalized_rerank = 1.0 / (1.0 + math.exp(-max(-700.0, min(700.0, float(rerank_score)))))
            final_score = (
                (1 - self._config.rerank_weight) * fused
                + self._config.rerank_weight * normalized_rerank
            )
            ranked.append(
                replace(
                    item,
                    signals=(*item.signals, RetrievalSignal(RetrievalMethod.RERANK, float(rerank_score))),
                    final_score=final_score,
                )
            )
        ranked.sort(key=lambda item: (-float(item.final_score), item.id))
        return tuple(replace(item, rank=rank) for rank, item in enumerate(ranked, 1))


def _evidence_id(query_id: str, version_id: str) -> str:
    digest = hashlib.sha256(f"{query_id}\x1f{version_id}".encode("utf-8")).hexdigest()[:24]
    return f"evidence:{digest}"


def _required_text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
