"""Concrete Neo4j repositories for the temporal legal domain."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import nullcontext
from datetime import date
from typing import Generic, TypeVar
from uuid import uuid4

from legal_crawler.ports import (
    BatchWriteResult,
    EntityNotFoundError,
    RepositoryConflictError,
    RepositoryIntegrityError,
    TransactionError,
    VersionTransitionResult,
    WriteDisposition,
    WriteResult,
)
from legal_crawler.temporal import (
    GraphEdge,
    LegalDocument,
    LegalEvent,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    SnapshotResult,
    SnapshotService,
    TemporalInterval,
    TemporalState,
)
from legal_crawler.temporal.version_chain import VersionChain, VersionChainError

from .codec import decode_edge, decode_node, encode_edge, encode_node
from .driver import Neo4jExecutor
from .schema import initialize_schema, validate_relation

NodeT = TypeVar(
    "NodeT",
    LegalDocument,
    Provision,
    ProvisionVersion,
    LegalEvent,
)
ItemT = TypeVar("ItemT")

_GET_NODE = """
// node.get
MATCH (n:DomainEntity {id: $id, kind: $kind})
RETURN properties(n) AS node
"""

_GET_NODES = """
// node.get_many
UNWIND $ids AS requested_id
MATCH (n:DomainEntity {id: requested_id, kind: $kind})
RETURN properties(n) AS node
"""

_PUT_NODE = """
// node.put
MERGE (n:DomainEntity {id: $id})
ON CREATE SET n.kind = $kind,
              n.payload = $payload,
              n += $properties,
              n._write_token = $write_token
WITH n,
     n._write_token = $write_token AS created,
     n.kind AS persisted_kind,
     n.payload AS persisted_payload
REMOVE n._write_token
RETURN created, persisted_kind, persisted_payload
"""

_LIST_NODES = """
// node.list
MATCH (n:DomainEntity {kind: $kind})
WHERE all(item IN $filters WHERE n[item.name] = item.value)
RETURN properties(n) AS node
"""

_LIST_DOCUMENTS_AT = """
// document.list_effective_at
MATCH (n:DomainEntity {kind: $kind})
WHERE (n.eff_from IS NULL OR n.eff_from <= $at)
  AND (n.eff_to IS NULL OR $at < n.eff_to)
RETURN properties(n) AS node
ORDER BY n.id
"""

_LIST_EVENTS = """
// event.list
MATCH (n:DomainEntity {kind: $kind})
WHERE n[$field] = $value
  AND ($start IS NULL OR n.effective_on >= $start)
  AND ($end IS NULL OR n.effective_on < $end)
RETURN properties(n) AS node
ORDER BY n.effective_on, n.id
"""

_LIST_EVENTS_FOR_PROVISION = """
// event.list_for_provision
MATCH (n:DomainEntity {kind: $kind})
WHERE $provision_id IN n.resolved_target_ids
  AND ($start IS NULL OR n.effective_on >= $start)
  AND ($end IS NULL OR n.effective_on < $end)
RETURN properties(n) AS node
ORDER BY n.effective_on, n.id
"""

_MARK_EVENT_APPLIED = """
// event.mark_applied
MATCH (n:DomainEntity {id: $id, kind: $kind})
WITH n, coalesce(n.applied, false) AS was_applied
SET n.applied = true
RETURN NOT was_applied AS changed
"""

_EVENT_APPLIED = """
// event.is_applied
MATCH (n:DomainEntity {id: $id, kind: $kind})
RETURN coalesce(n.applied, false) AS applied
"""

_REPLACE_VERSION = """
// version.replace_closed
MATCH (n:DomainEntity {id: $id, kind: $kind})
WHERE n.payload = $expected_payload
SET n.payload = $closed_payload,
    n += $properties
RETURN n.payload AS payload
"""

_LOCK_VERSION_CHAIN = """
// version.lock_chain
MATCH (n:DomainEntity {id: $provision_id, kind: $provision_kind})
SET n._version_write_token = $write_token
REMOVE n._version_write_token
RETURN n.id AS provision_id
"""

_GET_EDGE = """
// edge.get
MATCH ()-[r]->()
WHERE r.id = $id
RETURN properties(r) AS edge
"""

_LIST_EDGES = """
// edge.list
MATCH (source:DomainEntity)-[r]->(target:DomainEntity)
WHERE CASE $direction
    WHEN 'outgoing' THEN source.id = $node_id
    WHEN 'incoming' THEN target.id = $node_id
    ELSE source.id = $node_id OR target.id = $node_id
END
  AND ($relations IS NULL OR type(r) IN $relations)
  AND (
    $at IS NULL
    OR r.eff_from IS NULL
    OR (r.eff_from <= $at AND (r.eff_to IS NULL OR $at < r.eff_to))
  )
RETURN properties(r) AS edge
ORDER BY r.id
"""

_GET_ANY_ENTITY = """
// provenance.get_entity
OPTIONAL MATCH (n:DomainEntity {id: $id})
OPTIONAL MATCH ()-[r]->() WHERE r.id = $id
RETURN properties(n) AS node, properties(r) AS edge
"""


class _Neo4jNodeRepository(Generic[NodeT]):
    def __init__(
        self,
        executor: Neo4jExecutor,
        model_type: type[NodeT],
    ) -> None:
        self._executor = executor
        self._model_type = model_type
        self._kind = _kind_for(model_type)

    def get(self, entity_id: str) -> NodeT | None:
        _required_id(entity_id)
        rows = self._executor.read(
            _GET_NODE,
            {"id": entity_id, "kind": self._kind},
        )
        if not rows:
            return None
        if len(rows) != 1:
            raise RepositoryIntegrityError(f"duplicate domain ID: {entity_id}")
        return self._decode(rows[0].get("node"))

    def get_many(self, entity_ids: Sequence[str]) -> dict[str, NodeT]:
        ids = _ids(entity_ids)
        if not ids:
            return {}
        rows = self._executor.read(
            _GET_NODES,
            {"ids": list(ids), "kind": self._kind},
        )
        result: dict[str, NodeT] = {}
        for row in rows:
            item = self._decode(row.get("node"))
            if item.id in result:
                raise RepositoryIntegrityError(f"duplicate domain ID: {item.id}")
            result[item.id] = item
        return result

    def _put_unchecked(self, value: NodeT) -> WriteResult:
        if not isinstance(value, self._model_type):
            raise TypeError(f"value must be a {self._model_type.__name__}")
        record = encode_node(value)
        parameters = record.parameters()
        parameters["write_token"] = str(uuid4())
        rows = self._executor.write(_PUT_NODE, parameters)
        if len(rows) != 1:
            raise TransactionError(f"Neo4j did not return write state for {value.id}")
        row = rows[0]
        if row.get("persisted_kind") != record.kind.value:
            raise RepositoryConflictError(
                f"domain ID {value.id} already belongs to another entity kind"
            )
        if row.get("persisted_payload") != record.payload:
            raise RepositoryConflictError(
                f"domain ID {value.id} already exists with different content"
            )
        disposition = (
            WriteDisposition.CREATED
            if row.get("created") is True
            else WriteDisposition.UNCHANGED
        )
        return WriteResult(value.id, disposition)

    def _list(self, **filters: str) -> tuple[NodeT, ...]:
        rows = self._executor.read(
            _LIST_NODES,
            {
                "kind": self._kind,
                "filters": [
                    {"name": name, "value": value}
                    for name, value in filters.items()
                ],
            },
        )
        return tuple(self._decode(row.get("node")) for row in rows)

    def _decode(self, value: object) -> NodeT:
        if not isinstance(value, Mapping):
            raise RepositoryIntegrityError("Neo4j node result is not a mapping")
        try:
            decoded = decode_node(value, expected_type=self._model_type)
        except (TypeError, ValueError) as exc:
            raise RepositoryIntegrityError(str(exc)) from exc
        return decoded


class Neo4jDocumentRepository(_Neo4jNodeRepository[LegalDocument]):
    def __init__(self, executor: Neo4jExecutor) -> None:
        super().__init__(executor, LegalDocument)

    def exists(self, document_id: str) -> bool:
        return self.get(document_id) is not None

    def list_effective_at(self, at: date) -> tuple[LegalDocument, ...]:
        _require_date(at, "document effective date")
        rows = self._executor.read(
            _LIST_DOCUMENTS_AT,
            {"kind": self._kind, "at": at.isoformat()},
        )
        return tuple(self._decode(row.get("node")) for row in rows)

    def put(self, document: LegalDocument) -> WriteResult:
        return self._put_unchecked(document)

    def put_many(
        self, documents: Iterable[LegalDocument]
    ) -> BatchWriteResult:
        return _atomic_put_many(self._executor, documents, self.put, "document")


class Neo4jProvisionRepository(_Neo4jNodeRepository[Provision]):
    def __init__(
        self,
        executor: Neo4jExecutor,
        documents: Neo4jDocumentRepository,
    ) -> None:
        super().__init__(executor, Provision)
        self._documents = documents

    def list_by_document(self, document_id: str) -> tuple[Provision, ...]:
        _required_id(document_id)
        return _order_provisions(self._list(document_id=document_id), document_id)

    def children_of(
        self,
        parent_id: str | None,
        document_id: str,
    ) -> tuple[Provision, ...]:
        return tuple(
            item
            for item in self.list_by_document(document_id)
            if item.parent_id == parent_id
        )

    def descendants_of(self, provision_id: str) -> tuple[Provision, ...]:
        root = self.get(provision_id)
        if root is None:
            return ()
        descendants: list[Provision] = []
        ancestor_ids = {root.id}
        for item in self.list_by_document(root.document_id):
            if item.parent_id in ancestor_ids:
                descendants.append(item)
                ancestor_ids.add(item.id)
        return tuple(descendants)

    def document_order(self, document_id: str) -> tuple[Provision, ...]:
        return self.list_by_document(document_id)

    def put(self, provision: Provision) -> WriteResult:
        if not isinstance(provision, Provision):
            raise TypeError("value must be a Provision")
        with _atomic(self._executor):
            if not self._documents.exists(provision.document_id):
                raise RepositoryIntegrityError(
                    f"provision document does not exist: {provision.document_id}"
                )
            self._validate_links(provision)
            return self._put_unchecked(provision)

    def put_many(self, provisions: Iterable[Provision]) -> BatchWriteResult:
        items = _unique_items(provisions, "provision")
        results: dict[str, WriteResult] = {}
        pending = list(items)
        with _atomic(self._executor):
            while pending:
                progressed = False
                for item in pending.copy():
                    if item.parent_id and self.get(item.parent_id) is None:
                        if item.parent_id in {value.id for value in pending}:
                            continue
                    if item.inserted_after_id and self.get(item.inserted_after_id) is None:
                        if item.inserted_after_id in {value.id for value in pending}:
                            continue
                    results[item.id] = self.put(item)
                    pending.remove(item)
                    progressed = True
                if not progressed:
                    unresolved = ", ".join(sorted(item.id for item in pending))
                    raise RepositoryIntegrityError(
                        f"unresolved provision dependencies: {unresolved}"
                    )
        return BatchWriteResult(tuple(results[item.id] for item in items))

    def _validate_links(self, provision: Provision) -> None:
        parent = self.get(provision.parent_id) if provision.parent_id else None
        if provision.parent_id and parent is None:
            raise RepositoryIntegrityError(
                f"provision parent does not exist: {provision.parent_id}"
            )
        if parent and parent.document_id != provision.document_id:
            raise RepositoryIntegrityError(
                "a provision and its parent must share a document"
            )
        anchor = (
            self.get(provision.inserted_after_id)
            if provision.inserted_after_id
            else None
        )
        if provision.inserted_after_id and anchor is None:
            raise RepositoryIntegrityError(
                f"insertion anchor does not exist: {provision.inserted_after_id}"
            )
        if anchor and (
            anchor.document_id != provision.document_id
            or anchor.parent_id != provision.parent_id
        ):
            raise RepositoryIntegrityError(
                "an insertion anchor must be a sibling in the same document"
            )


class Neo4jVersionRepository(_Neo4jNodeRepository[ProvisionVersion]):
    def __init__(
        self,
        executor: Neo4jExecutor,
        provisions: Neo4jProvisionRepository,
    ) -> None:
        super().__init__(executor, ProvisionVersion)
        self._provisions = provisions

    def chain_for(self, provision_id: str) -> VersionChain | None:
        _required_id(provision_id)
        versions = self._list(provision_id=provision_id)
        if not versions:
            return None
        try:
            return VersionChain(provision_id, versions)
        except VersionChainError as exc:
            raise RepositoryIntegrityError(str(exc)) from exc

    def version_at(
        self, provision_id: str, at: date
    ) -> ProvisionVersion | None:
        _require_date(at, "version query date")
        chain = self.chain_for(provision_id)
        return chain.at(at) if chain else None

    def current_for(self, provision_id: str) -> ProvisionVersion | None:
        chain = self.chain_for(provision_id)
        return chain.current() if chain else None

    def put(self, version: ProvisionVersion) -> WriteResult:
        if not isinstance(version, ProvisionVersion):
            raise TypeError("value must be a ProvisionVersion")
        with _atomic(self._executor):
            if self._provisions.get(version.provision_id) is None:
                raise RepositoryIntegrityError(
                    f"version provision does not exist: {version.provision_id}"
                )
            self._lock_chain(version.provision_id)
            chain = self.chain_for(version.provision_id)
            if chain is not None:
                try:
                    chain.add(version)
                except VersionChainError as exc:
                    raise RepositoryIntegrityError(str(exc)) from exc
            return self._put_unchecked(version)

    def put_many(
        self, versions: Iterable[ProvisionVersion]
    ) -> BatchWriteResult:
        items = _unique_items(versions, "version")
        results: dict[str, WriteResult] = {}
        with _atomic(self._executor):
            for item in sorted(
                items,
                key=lambda value: (
                    value.provision_id,
                    value.ordinal,
                    value.validity.start,
                    value.id,
                ),
            ):
                results[item.id] = self.put(item)
        return BatchWriteResult(tuple(results[item.id] for item in items))

    def replace_closed(
        self,
        expected: ProvisionVersion,
        closed: ProvisionVersion,
    ) -> VersionTransitionResult:
        try:
            requested = VersionTransitionResult(expected, closed, changed=False)
        except ValueError as exc:
            raise RepositoryIntegrityError(str(exc)) from exc
        with _atomic(self._executor):
            current = self.get(expected.id)
            if current is None:
                raise EntityNotFoundError(f"version does not exist: {expected.id}")
            if current == closed:
                return requested
            if current != expected:
                raise RepositoryConflictError(
                    f"version {expected.id} changed since it was read"
                )
            self._lock_chain(expected.provision_id)
            chain = self.chain_for(expected.provision_id)
            if chain is None or chain.current() != expected:
                raise RepositoryConflictError(
                    f"version {expected.id} is no longer the current open version"
                )
            record = encode_node(closed)
            rows = self._executor.write(
                _REPLACE_VERSION,
                {
                    "id": expected.id,
                    "kind": self._kind,
                    "expected_payload": encode_node(expected).payload,
                    "closed_payload": record.payload,
                    "properties": dict(record.indexed_properties),
                },
            )
            if len(rows) != 1 or rows[0].get("payload") != record.payload:
                raise RepositoryConflictError(
                    f"version {expected.id} changed during closure"
                )
            return VersionTransitionResult(expected, closed, changed=True)

    def _lock_chain(self, provision_id: str) -> None:
        rows = self._executor.write(
            _LOCK_VERSION_CHAIN,
            {
                "provision_id": provision_id,
                "provision_kind": _kind_for(Provision),
                "write_token": str(uuid4()),
            },
        )
        if len(rows) != 1 or rows[0].get("provision_id") != provision_id:
            raise RepositoryIntegrityError(
                f"version provision does not exist: {provision_id}"
            )


class Neo4jEventRepository(_Neo4jNodeRepository[LegalEvent]):
    def __init__(
        self,
        executor: Neo4jExecutor,
        documents: Neo4jDocumentRepository,
    ) -> None:
        super().__init__(executor, LegalEvent)
        self._documents = documents

    def list_by_source_document(
        self,
        document_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        return self._list_events("source_document_id", document_id, effective_during)

    def list_by_target_document(
        self,
        document_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        return self._list_events("target_document_id", document_id, effective_during)

    def list_for_provision(
        self,
        provision_id: str,
        *,
        effective_during: TemporalInterval | None = None,
    ) -> tuple[LegalEvent, ...]:
        start, end = _interval_bounds(effective_during)
        rows = self._executor.read(
            _LIST_EVENTS_FOR_PROVISION,
            {
                "kind": self._kind,
                "provision_id": _required_id(provision_id),
                "start": start,
                "end": end,
            },
        )
        return tuple(self._decode(row.get("node")) for row in rows)

    def put(self, event: LegalEvent) -> WriteResult:
        if not isinstance(event, LegalEvent):
            raise TypeError("value must be a LegalEvent")
        with _atomic(self._executor):
            for document_id, role in (
                (event.source_document_id, "source"),
                (event.target_document_id, "target"),
            ):
                if not self._documents.exists(document_id):
                    raise RepositoryIntegrityError(
                        f"event {role} document does not exist: {document_id}"
                    )
            return self._put_unchecked(event)

    def put_many(self, events: Iterable[LegalEvent]) -> BatchWriteResult:
        return _atomic_put_many(self._executor, events, self.put, "event")

    def is_applied(self, event_id: str) -> bool:
        rows = self._executor.read(
            _EVENT_APPLIED,
            {"id": _required_id(event_id), "kind": self._kind},
        )
        return bool(rows and rows[0].get("applied") is True)

    def mark_applied(self, event_id: str) -> bool:
        rows = self._executor.write(
            _MARK_EVENT_APPLIED,
            {"id": _required_id(event_id), "kind": self._kind},
        )
        if not rows:
            raise EntityNotFoundError(f"event does not exist: {event_id}")
        return rows[0].get("changed") is True

    def _list_events(
        self,
        field: str,
        value: str,
        interval: TemporalInterval | None,
    ) -> tuple[LegalEvent, ...]:
        start, end = _interval_bounds(interval)
        rows = self._executor.read(
            _LIST_EVENTS,
            {
                "kind": self._kind,
                "field": field,
                "value": _required_id(value),
                "start": start,
                "end": end,
            },
        )
        return tuple(self._decode(row.get("node")) for row in rows)


class Neo4jTemporalGraphRepository:
    def __init__(self, executor: Neo4jExecutor) -> None:
        self._executor = executor

    @staticmethod
    def edge_id(edge: GraphEdge) -> str:
        return encode_edge(edge).id

    def get(self, edge_id: str) -> GraphEdge | None:
        rows = self._executor.read(_GET_EDGE, {"id": _required_id(edge_id)})
        if not rows:
            return None
        if len(rows) != 1:
            raise RepositoryIntegrityError(f"duplicate graph edge ID: {edge_id}")
        return _decode_edge_result(rows[0].get("edge"))

    def get_many(self, edge_ids: Sequence[str]) -> dict[str, GraphEdge]:
        result: dict[str, GraphEdge] = {}
        for edge_id in _ids(edge_ids):
            edge = self.get(edge_id)
            if edge is not None:
                result[edge_id] = edge
        return result

    def put(self, edge: GraphEdge) -> WriteResult:
        if not isinstance(edge, GraphEdge):
            raise TypeError("value must be a GraphEdge")
        record = encode_edge(edge)
        relation = validate_relation(record.relation)
        query = f"""
// edge.put
MATCH (source:DomainEntity {{id: $source_id}})
MATCH (target:DomainEntity {{id: $target_id}})
MERGE (source)-[r:{relation} {{id: $id}}]->(target)
ON CREATE SET r.source_id = $source_id,
              r.target_id = $target_id,
              r.relation = $relation,
              r.payload = $payload,
              r += $properties,
              r._write_token = $write_token
WITH r,
     r._write_token = $write_token AS created,
     r.payload AS persisted_payload
REMOVE r._write_token
RETURN created, persisted_payload
"""
        parameters = record.parameters()
        parameters["write_token"] = str(uuid4())
        rows = self._executor.write(query, parameters)
        if not rows:
            raise EntityNotFoundError(
                f"graph edge endpoint does not exist: {edge.source_id} -> {edge.target_id}"
            )
        if len(rows) != 1:
            raise RepositoryIntegrityError(f"duplicate graph edge ID: {record.id}")
        if rows[0].get("persisted_payload") != record.payload:
            raise RepositoryConflictError(
                f"graph edge ID {record.id} exists with different content"
            )
        disposition = (
            WriteDisposition.CREATED
            if rows[0].get("created") is True
            else WriteDisposition.UNCHANGED
        )
        return WriteResult(record.id, disposition)

    def put_many(self, edges: Iterable[GraphEdge]) -> BatchWriteResult:
        return _atomic_put_many(
            self._executor,
            edges,
            self.put,
            "graph edge",
            identity=self.edge_id,
        )

    def outgoing(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        return self._list("outgoing", node_id, relations, at)

    def incoming(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        return self._list("incoming", node_id, relations, at)

    def neighbors(
        self,
        node_id: str,
        *,
        relations: frozenset[RelationType] | None = None,
        at: date | None = None,
    ) -> tuple[GraphEdge, ...]:
        return self._list("neighbors", node_id, relations, at)

    def _list(
        self,
        direction: str,
        node_id: str,
        relations: frozenset[RelationType] | None,
        at: date | None,
    ) -> tuple[GraphEdge, ...]:
        relation_values = _relations(relations)
        if at is not None:
            _require_date(at, "graph query date")
        rows = self._executor.read(
            _LIST_EDGES,
            {
                "direction": direction,
                "node_id": _required_id(node_id),
                "relations": relation_values,
                "at": at.isoformat() if at else None,
            },
        )
        return tuple(_decode_edge_result(row.get("edge")) for row in rows)


class Neo4jProvenanceRepository:
    def __init__(
        self,
        executor: Neo4jExecutor,
        versions: Neo4jVersionRepository,
    ) -> None:
        self._executor = executor
        self._versions = versions

    def for_entity(self, entity_id: str) -> tuple[Provenance, ...]:
        rows = self._executor.read(
            _GET_ANY_ENTITY,
            {"id": _required_id(entity_id)},
        )
        if not rows:
            return ()
        row = rows[0]
        if isinstance(row.get("node"), Mapping):
            value = _decode_any_node(row["node"])
            if isinstance(value, Provision):
                chain = self._versions.chain_for(value.id)
                return _deduplicate_provenance(
                    item
                    for version in (chain.versions if chain else ())
                    for item in version.provenance
                )
            return tuple(getattr(value, "provenance", ()))
        if isinstance(row.get("edge"), Mapping):
            return _decode_edge_result(row["edge"]).provenance
        return ()


class Neo4jSnapshotRepository:
    def __init__(
        self,
        documents: Neo4jDocumentRepository,
        provisions: Neo4jProvisionRepository,
        versions: Neo4jVersionRepository,
        events: Neo4jEventRepository,
    ) -> None:
        self._documents = documents
        self._provisions = provisions
        self._versions = versions
        self._events = events

    def snapshot(self, provision_id: str, at: date) -> SnapshotResult:
        provision = self._provisions.get(provision_id)
        if provision is None:
            return SnapshotService(TemporalState()).snapshot(provision_id, at)
        state = self._load_document(provision.document_id)
        return SnapshotService(state).snapshot(provision_id, at)

    def snapshot_document(
        self,
        document_id: str,
        at: date,
        *,
        levels: frozenset[ProvisionLevel] | None = None,
        valid_only: bool = False,
    ) -> tuple[SnapshotResult, ...]:
        state = self._load_document(document_id)
        return SnapshotService(state).snapshot_document(
            document_id,
            at,
            levels=levels,
            valid_only=valid_only,
        )

    def valid_provisions(
        self,
        document_id: str,
        at: date,
        *,
        levels: frozenset[ProvisionLevel] | None = None,
    ) -> tuple[SnapshotResult, ...]:
        return self.snapshot_document(
            document_id,
            at,
            levels=levels,
            valid_only=True,
        )

    def _load_document(self, document_id: str) -> TemporalState:
        state = TemporalState()
        document = self._documents.get(document_id)
        if document is None:
            return state
        state.add_document(document)
        for provision in self._provisions.document_order(document_id):
            state.add_provision(provision)
            chain = self._versions.chain_for(provision.id)
            for version in chain.versions if chain else ():
                state.add_version(version)
        for event in self._events.list_by_target_document(document_id):
            if self._events.is_applied(event.id):
                state.record_applied_event(event)
        return state


class Neo4jUnitOfWork:
    """Compose every authoritative Neo4j repository over one executor."""

    def __init__(self, executor: Neo4jExecutor) -> None:
        if not isinstance(executor, Neo4jExecutor):
            raise TypeError("executor must be a Neo4jExecutor")
        self.executor = executor
        self.documents = Neo4jDocumentRepository(executor)
        self.provisions = Neo4jProvisionRepository(executor, self.documents)
        self.versions = Neo4jVersionRepository(executor, self.provisions)
        self.events = Neo4jEventRepository(executor, self.documents)
        self.graph = Neo4jTemporalGraphRepository(executor)
        self.provenance = Neo4jProvenanceRepository(executor, self.versions)
        self.snapshots = Neo4jSnapshotRepository(
            self.documents,
            self.provisions,
            self.versions,
            self.events,
        )

    @classmethod
    def from_uri(
        cls,
        uri: str,
        username: str,
        password: str,
        *,
        database: str = "neo4j",
    ) -> "Neo4jUnitOfWork":
        return cls(
            Neo4jExecutor.from_uri(
                uri,
                username,
                password,
                database=database,
            )
        )

    def transaction(self):
        return self.executor.transaction()

    def initialize_schema(self) -> None:
        initialize_schema(self.executor)

    def close(self) -> None:
        self.executor.close()


def _kind_for(model_type: type[object]) -> str:
    return {
        LegalDocument: "Document",
        Provision: "Provision",
        ProvisionVersion: "ProvisionVersion",
        LegalEvent: "LegalEvent",
    }[model_type]


def _atomic(executor: Neo4jExecutor):
    return nullcontext() if executor.in_transaction else executor.transaction()


def _atomic_put_many(
    executor: Neo4jExecutor,
    values: Iterable[ItemT],
    put: Callable[[ItemT], WriteResult],
    name: str,
    *,
    identity: Callable[[ItemT], str] | None = None,
) -> BatchWriteResult:
    items = _unique_items(values, name, identity=identity)
    with _atomic(executor):
        results = tuple(put(item) for item in items)
    return BatchWriteResult(results)


def _unique_items(
    values: Iterable[ItemT],
    name: str,
    *,
    identity: Callable[[ItemT], str] | None = None,
) -> tuple[ItemT, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} batch must be iterable domain objects")
    items = tuple(values)
    get_id = identity or (lambda item: getattr(item, "id", None))
    ids = tuple(_required_id(get_id(item)) for item in items)
    if len(ids) != len(set(ids)):
        raise RepositoryIntegrityError(f"duplicate {name} ID in batch")
    return items


def _ids(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("IDs must be a sequence")
    ids = tuple(_required_id(value) for value in values)
    if len(ids) != len(set(ids)):
        raise ValueError("IDs must not contain duplicates")
    return ids


def _required_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("domain ID must not be empty")
    return value


def _require_date(value: object, name: str) -> None:
    if type(value) is not date:
        raise ValueError(f"{name} must be a date")


def _interval_bounds(
    interval: TemporalInterval | None,
) -> tuple[str | None, str | None]:
    if interval is None:
        return None, None
    if not isinstance(interval, TemporalInterval):
        raise ValueError("effective_during must be a TemporalInterval")
    return interval.start.isoformat(), (
        interval.end.isoformat() if interval.end else None
    )


def _relations(
    values: frozenset[RelationType] | None,
) -> list[str] | None:
    if values is None:
        return None
    if not isinstance(values, frozenset) or any(
        not isinstance(item, RelationType) for item in values
    ):
        raise ValueError("relations must be a frozenset of RelationType")
    return sorted(item.value for item in values)


def _decode_edge_result(value: object) -> GraphEdge:
    if not isinstance(value, Mapping):
        raise RepositoryIntegrityError("Neo4j edge result is not a mapping")
    try:
        return decode_edge(value)
    except (TypeError, ValueError) as exc:
        raise RepositoryIntegrityError(str(exc)) from exc


def _decode_any_node(value: Mapping[str, object]):
    try:
        return decode_node(value)
    except (TypeError, ValueError) as exc:
        raise RepositoryIntegrityError(str(exc)) from exc


def _order_provisions(
    provisions: tuple[Provision, ...],
    document_id: str,
) -> tuple[Provision, ...]:
    state = TemporalState()
    state.add_document(LegalDocument(document_id, document_id, document_id))
    pending = list(provisions)
    while pending:
        progressed = False
        for item in pending.copy():
            known = {value.id for value in state.provisions}
            if item.parent_id and item.parent_id not in known:
                continue
            if item.inserted_after_id and item.inserted_after_id not in known:
                continue
            try:
                state.add_provision(item)
            except ValueError as exc:
                raise RepositoryIntegrityError(str(exc)) from exc
            pending.remove(item)
            progressed = True
        if not progressed:
            unresolved = ", ".join(sorted(item.id for item in pending))
            raise RepositoryIntegrityError(
                f"unresolved provision structure: {unresolved}"
            )
    return state.document_order(document_id)


def _deduplicate_provenance(
    values: Iterable[Provenance],
) -> tuple[Provenance, ...]:
    result: list[Provenance] = []
    for value in values:
        if value not in result:
            result.append(value)
    return tuple(result)
