"""Transactional application of legal events through repository ports."""
from __future__ import annotations

from legal_crawler.ports import TemporalUnitOfWork, TransactionError
from legal_crawler.temporal import (
    ApplyResult,
    EventApplier,
    GraphEdge,
    LegalEvent,
    LegalOperation,
    Provision,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
    TemporalState,
)


class RepositoryEventApplicationService:
    """Bridge pure event semantics to an authoritative storage transaction.

    The service reconstructs only the target document aggregate needed by the
    domain applier, computes the validated next state, and persists its delta.
    Vector embeddings are intentionally absent because they are derived after
    the authoritative transaction commits.
    """

    _OPERATION_RELATIONS = {
        LegalOperation.AMEND: RelationType.AMENDS,
        LegalOperation.SUPPLEMENT: RelationType.SUPPLEMENTS,
        LegalOperation.REPEAL: RelationType.REPEALS,
        LegalOperation.REPLACE: RelationType.REPLACES,
        LegalOperation.CORRECT: RelationType.CORRECTS,
    }

    def __init__(
        self,
        unit_of_work: TemporalUnitOfWork,
        *,
        applier: EventApplier | None = None,
    ) -> None:
        if not isinstance(unit_of_work, TemporalUnitOfWork):
            raise TypeError("unit_of_work must satisfy TemporalUnitOfWork")
        self._uow = unit_of_work
        self._applier = applier or EventApplier()

    def apply(self, event: LegalEvent) -> ApplyResult:
        """Apply and persist one event atomically, returning domain changes."""
        if not isinstance(event, LegalEvent):
            raise TypeError("event must be a LegalEvent")
        with self._uow.transaction():
            # Persist first so a conflicting reuse of the deterministic event
            # ID is detected even when an event was already marked as applied.
            self._uow.events.put(event)
            if self._uow.events.is_applied(event.id):
                return ApplyResult(event.id, applied=False, already_applied=True)

            before = self._load_target_state(event)
            after = before.copy()
            result = self._applier.apply(event, after)
            self._persist_delta(event, result, before, after)
            if not self._uow.events.mark_applied(event.id):
                raise TransactionError(
                    f"event {event.id} became applied inside its own transaction"
                )
            return result

    def _load_target_state(self, event: LegalEvent) -> TemporalState:
        state = TemporalState()
        for document_id in dict.fromkeys(
            (event.source_document_id, event.target_document_id)
        ):
            document = self._uow.documents.get(document_id)
            if document is not None:
                state.add_document(document)

        for provision in self._uow.provisions.document_order(
            event.target_document_id
        ):
            state.add_provision(provision)
            chain = self._uow.versions.chain_for(provision.id)
            for version in chain.versions if chain else ():
                state.add_version(version)
        return state

    def _persist_delta(
        self,
        event: LegalEvent,
        result: ApplyResult,
        before: TemporalState,
        after: TemporalState,
    ) -> None:
        created_provisions = tuple(
            self._required_provision(after, provision_id)
            for provision_id in result.created_provision_ids
        )
        if created_provisions:
            self._uow.provisions.put_many(created_provisions)

        for version_id in result.closed_version_ids:
            expected = self._required_version(before, version_id)
            closed = self._required_version(after, version_id)
            self._uow.versions.replace_closed(expected, closed)

        created_versions = tuple(
            self._required_version(after, version_id)
            for version_id in result.created_version_ids
        )
        if created_versions:
            self._uow.versions.put_many(created_versions)

        edges = self._graph_edges(
            event,
            created_provisions=created_provisions,
            created_versions=created_versions,
        )
        if edges:
            self._uow.graph.put_many(edges)

    def _graph_edges(
        self,
        event: LegalEvent,
        *,
        created_provisions: tuple[Provision, ...],
        created_versions: tuple[ProvisionVersion, ...],
    ) -> tuple[GraphEdge, ...]:
        if event.effective_on is None:
            raise TransactionError(
                f"applied event {event.id} unexpectedly has no effective date"
            )
        relation = self._OPERATION_RELATIONS.get(event.operation)
        edges: list[GraphEdge] = []
        if relation is not None:
            edges.append(
                GraphEdge(
                    event.id,
                    event.target_document_id,
                    relation,
                    TemporalInterval(event.effective_on),
                    provenance=event.provenance,
                )
            )
        for provision in created_provisions:
            edges.append(
                GraphEdge(
                    provision.parent_id or provision.document_id,
                    provision.id,
                    RelationType.CONTAINS,
                    TemporalInterval(event.effective_on),
                    provenance=event.provenance,
                )
            )
        for version in created_versions:
            edges.extend(
                (
                    GraphEdge(
                        version.id,
                        version.provision_id,
                        RelationType.VERSION_OF,
                        version.validity,
                        provenance=version.provenance,
                    ),
                    GraphEdge(
                        version.id,
                        event.id,
                        RelationType.CAUSED_BY,
                        TemporalInterval(event.effective_on),
                        provenance=event.provenance,
                    ),
                )
            )
        return tuple(edges)

    @staticmethod
    def _required_provision(
        state: TemporalState, provision_id: str
    ) -> Provision:
        provision = state.provision(provision_id)
        if provision is None:
            raise TransactionError(
                f"event result refers to missing provision: {provision_id}"
            )
        return provision

    @staticmethod
    def _required_version(
        state: TemporalState, version_id: str
    ) -> ProvisionVersion:
        version = state.version(version_id)
        if version is None:
            raise TransactionError(
                f"event result refers to missing version: {version_id}"
            )
        return version
