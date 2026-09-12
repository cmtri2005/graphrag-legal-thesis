"""In-memory implementations of the authoritative repository ports."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from datetime import date
from typing import TypeVar

from legal_crawler.ports.repositories import (
    BatchWriteResult,
    EntityNotFoundError,
    RepositoryConflictError,
    RepositoryIntegrityError,
    WriteDisposition,
    WriteResult,
    VersionTransitionResult,
)
from legal_crawler.temporal.ids import make_edge_id
from legal_crawler.temporal.models import (
    GraphEdge,
    LegalDocument,
    LegalEvent,
    Provenance,
    Provision,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
)
from legal_crawler.temporal.state import TemporalStateError
from legal_crawler.temporal.version_chain import VersionChain, VersionChainError

from .store import MemoryStore

ItemT = TypeVar("ItemT")


class MemoryDocumentRepository:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def get(self, document_id: str) -> LegalDocument | None:
        return self._store.state.document(document_id)

    def get_many(self, document_ids: Sequence[str]) -> dict[str, LegalDocument]:
        return _get_many(document_ids, self.get)

    def exists(self, document_id: str) -> bool:
        return self.get(document_id) is not None

    def list_effective_at(self, at: date) -> tuple[LegalDocument, ...]:
        _require_date(at, "document effective date")
        return tuple(
            sorted(
                (
                    document
                    for document in self._store.state.documents
                    if (
                        document.effective_from is None
                        or document.effective_from <= at
                    )
                    and (document.effective_to is None or at < document.effective_to)
                ),
                key=lambda item: item.id,
            )
        )

    def put(self, document: LegalDocument) -> WriteResult:
        existing = self.get(document.id)
        if existing is not None:
            return _existing_result(document.id, existing, document)
        try:
            self._store.state.add_document(document)
        except TemporalStateError as exc:
            raise RepositoryIntegrityError(str(exc)) from exc
        return WriteResult(document.id, WriteDisposition.CREATED)

    def put_many(self, documents: Iterable[LegalDocument]) -> BatchWriteResult:
        return _atomic_batch(
            self._store,
            documents,
            lambda item: item.id,
            self.put,
            "document",
        )


class MemoryProvisionRepository:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def get(self, provision_id: str) -> Provision | None:
        return self._store.state.provision(provision_id)

    def get_many(self, provision_ids: Sequence[str]) -> dict[str, Provision]:
        return _get_many(provision_ids, self.get)

    def list_by_document(self, document_id: str) -> tuple[Provision, ...]:
        return self._store.state.document_order(document_id)

    def children_of(
        self, parent_id: str | None, document_id: str
    ) -> tuple[Provision, ...]:
        return self._store.state.children_of(parent_id, document_id)

    def descendants_of(self, provision_id: str) -> tuple[Provision, ...]:
        return self._store.state.descendants_of(provision_id)

    def document_order(self, document_id: str) -> tuple[Provision, ...]:
        return self._store.state.document_order(document_id)

    def put(self, provision: Provision) -> WriteResult:
        existing = self.get(provision.id)
        if existing is not None:
            return _existing_result(provision.id, existing, provision)
        try:
            self._store.state.add_provision(provision)
        except TemporalStateError as exc:
            raise RepositoryIntegrityError(str(exc)) from exc
        return WriteResult(provision.id, WriteDisposition.CREATED)

    def put_many(self, provisions: Iterable[Provision]) -> BatchWriteResult:
        items = _unique_items(provisions, lambda item: item.id, "provision")
        snapshot = self._store.snapshot()
        pending = list(items)
        results: dict[str, WriteResult] = {}
        try:
            while pending:
                progressed = False
                for provision in pending.copy():
                    if self.get(provision.id) is None:
                        if provision.parent_id and self.get(provision.parent_id) is None:
                            continue
                        if (
                            provision.inserted_after_id
                            and self.get(provision.inserted_after_id) is None
                        ):
                            continue
                    results[provision.id] = self.put(provision)
                    pending.remove(provision)
                    progressed = True
                if not progressed:
                    unresolved = ", ".join(sorted(item.id for item in pending))
                    raise RepositoryIntegrityError(
                        f"unresolved provision dependencies: {unresolved}"
                    )
        except BaseException:
            self._store.restore(snapshot)
            raise
        return BatchWriteResult(tuple(results[item.id] for item in items))


class MemoryVersionRepository:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def get(self, version_id: str) -> ProvisionVersion | None:
        return self._store.state.version(version_id)

    def get_many(
        self, version_ids: Sequence[str]
    ) -> dict[str, ProvisionVersion]:
        return _get_many(version_ids, self.get)

    def chain_for(self, provision_id: str) -> VersionChain | None:
        chain = self._store.state.chain(provision_id)
        return VersionChain(provision_id, chain.versions) if chain else None

    def version_at(self, provision_id: str, at: date) -> ProvisionVersion | None:
        _require_date(at, "version query date")
        chain = self._store.state.chain(provision_id)
        return chain.at(at) if chain else None

    def current_for(self, provision_id: str) -> ProvisionVersion | None:
        chain = self._store.state.chain(provision_id)
        return chain.current() if chain else None

    def put(self, version: ProvisionVersion) -> WriteResult:
        existing = self.get(version.id)
        if existing is not None:
            return _existing_result(version.id, existing, version)
        try:
            self._store.state.add_version(version)
        except (TemporalStateError, VersionChainError) as exc:
            raise RepositoryIntegrityError(str(exc)) from exc
        return WriteResult(version.id, WriteDisposition.CREATED)

    def put_many(self, versions: Iterable[ProvisionVersion]) -> BatchWriteResult:
        items = _unique_items(versions, lambda item: item.id, "version")
        snapshot = self._store.snapshot()
        results: dict[str, WriteResult] = {}
        try:
            for version in sorted(
                items,
                key=lambda item: (
                    item.provision_id,
                    item.ordinal,
                    item.validity.start,
                    item.id,
                ),
            ):
                results[version.id] = self.put(version)
        except BaseException:
            self._store.restore(snapshot)
            raise
        return BatchWriteResult(tuple(results[item.id] for item in items))

    def replace_closed(
        self,
        expected: ProvisionVersion,
        closed: ProvisionVersion,
    ) -> VersionTransitionResult:
        _validate_closed_transition(expected, closed)
        existing = self.get(expected.id)
        if existing is None:
            raise EntityNotFoundError(f"version does not exist: {expected.id}")
        if existing == closed:
            return VersionTransitionResult(expected, closed, changed=False)
        if existing != expected:
            raise RepositoryConflictError(
                f"version {expected.id} changed since it was read"
            )
        chain = self._store.state.chain(expected.provision_id)
        if chain is None or chain.current() != expected:
            raise RepositoryConflictError(
                f"version {expected.id} is no longer the current open version"
            )
        assert closed.validity.end is not None
        actual = chain.close_current(
            closed.validity.end,
            ended_by_event_id=closed.ended_by_event_id,
        )
        if actual != closed:
            raise RepositoryIntegrityError(
                "closed version does not match the repository transition"
            )
        return VersionTransitionResult(expected, closed, changed=True)


class MemoryEventRepository:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def get(self, event_id: str) -> LegalEvent | None:
        return self._store.events.get(event_id)

    def get_many(self, event_ids: Sequence[str]) -> dict[str, LegalEvent]:
        return _get_many(event_ids, self.get)

    def list_by_source_document(
        self,
        document_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        return self._filter_events(
            lambda event: event.source_document_id == document_id,
            effective_during,
        )

    def list_by_target_document(
        self,
        document_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        return self._filter_events(
            lambda event: event.target_document_id == document_id,
            effective_during,
        )

    def list_for_provision(
        self,
        provision_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        return self._filter_events(
            lambda event: provision_id in event.resolved_target_ids,
            effective_during,
        )

    def put(self, event: LegalEvent) -> WriteResult:
        existing = self.get(event.id)
        if existing is not None:
            return _existing_result(event.id, existing, event)
        if self._store.state.document(event.source_document_id) is None:
            raise RepositoryIntegrityError(
                f"event source document does not exist: {event.source_document_id}"
            )
        if self._store.state.document(event.target_document_id) is None:
            raise RepositoryIntegrityError(
                f"event target document does not exist: {event.target_document_id}"
            )
        self._store.events[event.id] = event
        return WriteResult(event.id, WriteDisposition.CREATED)

    def put_many(self, events: Iterable[LegalEvent]) -> BatchWriteResult:
        return _atomic_batch(
            self._store, events, lambda item: item.id, self.put, "event"
        )

    def is_applied(self, event_id: str) -> bool:
        return event_id in self._store.state.applied_event_ids

    def mark_applied(self, event_id: str) -> bool:
        event = self.get(event_id)
        if event is None:
            raise EntityNotFoundError(f"event does not exist: {event_id}")
        if self.is_applied(event_id):
            return False
        try:
            self._store.state.record_applied_event(event)
        except TemporalStateError as exc:
            raise RepositoryIntegrityError(str(exc)) from exc
        return True

    def _filter_events(
        self,
        predicate: Callable[[LegalEvent], bool],
        effective_during: TemporalInterval | None,
    ) -> tuple[LegalEvent, ...]:
        if effective_during is not None and not isinstance(
            effective_during, TemporalInterval
        ):
            raise ValueError("effective_during must be a TemporalInterval")
        return tuple(
            sorted(
                (
                    event
                    for event in self._store.events.values()
                    if predicate(event)
                    and (
                        effective_during is None
                        or (
                            event.effective_on is not None
                            and effective_during.contains(event.effective_on)
                        )
                    )
                ),
                key=lambda item: (item.effective_on or date.max, item.id),
            )
        )


class MemoryTemporalGraphRepository:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    @staticmethod
    def edge_id(edge: GraphEdge) -> str:
        return make_edge_id(
            edge.source_id,
            edge.relation,
            edge.target_id,
            edge.validity.start if edge.validity else None,
        )

    def get(self, edge_id: str) -> GraphEdge | None:
        return self._store.edges.get(edge_id)

    def get_many(self, edge_ids: Sequence[str]) -> dict[str, GraphEdge]:
        return _get_many(edge_ids, self.get)

    def put(self, edge: GraphEdge) -> WriteResult:
        edge_id = self.edge_id(edge)
        existing = self.get(edge_id)
        if existing is not None:
            return _existing_result(edge_id, existing, edge)
        self._store.edges[edge_id] = edge
        return WriteResult(edge_id, WriteDisposition.CREATED)

    def put_many(self, edges: Iterable[GraphEdge]) -> BatchWriteResult:
        return _atomic_batch(
            self._store, edges, self.edge_id, self.put, "graph edge"
        )

    def outgoing(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        return self._filter_edges(
            lambda edge: edge.source_id == node_id, relations, at
        )

    def incoming(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        return self._filter_edges(
            lambda edge: edge.target_id == node_id, relations, at
        )

    def neighbors(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        return self._filter_edges(
            lambda edge: edge.source_id == node_id or edge.target_id == node_id,
            relations,
            at,
        )

    def _filter_edges(
        self,
        predicate: Callable[[GraphEdge], bool],
        relations: frozenset[RelationType] | None,
        at: date | None,
    ) -> tuple[GraphEdge, ...]:
        if relations is not None:
            if not isinstance(relations, frozenset) or any(
                not isinstance(item, RelationType) for item in relations
            ):
                raise ValueError("relations must contain RelationType values")
        if at is not None:
            _require_date(at, "graph query date")
        matches = (
            (edge_id, edge)
            for edge_id, edge in self._store.edges.items()
            if predicate(edge)
            and (relations is None or edge.relation in relations)
            and (at is None or edge.validity is None or edge.validity.contains(at))
        )
        return tuple(edge for _, edge in sorted(matches, key=lambda item: item[0]))


class MemoryProvenanceRepository:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def for_entity(self, entity_id: str) -> tuple[Provenance, ...]:
        collected: list[Provenance] = []
        version = self._store.state.version(entity_id)
        if version is not None:
            collected.extend(version.provenance)
        event = self._store.events.get(entity_id)
        if event is not None:
            collected.extend(event.provenance)
        edge = self._store.edges.get(entity_id)
        if edge is not None:
            collected.extend(edge.provenance)
        provision = self._store.state.provision(entity_id)
        if provision is not None:
            chain = self._store.state.chain(provision.id)
            for item in chain.versions if chain else ():
                collected.extend(item.provenance)
        unique: list[Provenance] = []
        for item in collected:
            if item not in unique:
                unique.append(item)
        return tuple(unique)


def _existing_result(entity_id: str, existing: ItemT, incoming: ItemT) -> WriteResult:
    if existing != incoming:
        raise RepositoryConflictError(
            f"entity id {entity_id} already exists with different content"
        )
    return WriteResult(entity_id, WriteDisposition.UNCHANGED)


def _get_many(ids: Sequence[str], getter: Callable[[str], ItemT | None]) -> dict[str, ItemT]:
    result: dict[str, ItemT] = {}
    for entity_id in ids:
        item = getter(entity_id)
        if item is not None:
            result[entity_id] = item
    return result


def _unique_items(
    items: Iterable[ItemT],
    id_of: Callable[[ItemT], str],
    entity_name: str,
) -> tuple[ItemT, ...]:
    materialized = tuple(items)
    ids = tuple(id_of(item) for item in materialized)
    if len(ids) != len(set(ids)):
        raise RepositoryIntegrityError(
            f"{entity_name} batch contains duplicate deterministic IDs"
        )
    return materialized


def _atomic_batch(
    store: MemoryStore,
    items: Iterable[ItemT],
    id_of: Callable[[ItemT], str],
    writer: Callable[[ItemT], WriteResult],
    entity_name: str,
) -> BatchWriteResult:
    materialized = _unique_items(items, id_of, entity_name)
    snapshot = store.snapshot()
    try:
        results = tuple(writer(item) for item in materialized)
    except BaseException:
        store.restore(snapshot)
        raise
    return BatchWriteResult(results)


def _require_date(value: object, name: str) -> None:
    if type(value) is not date:
        raise ValueError(f"{name} must be a date")


def _validate_closed_transition(
    expected: ProvisionVersion,
    closed: ProvisionVersion,
) -> None:
    if not isinstance(expected, ProvisionVersion) or not isinstance(
        closed, ProvisionVersion
    ):
        raise RepositoryIntegrityError(
            "version closure requires ProvisionVersion values"
        )
    try:
        VersionTransitionResult(expected, closed, changed=False)
    except ValueError as exc:
        raise RepositoryIntegrityError(str(exc)) from exc
