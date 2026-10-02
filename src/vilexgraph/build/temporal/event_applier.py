"""Apply verified legal events to provision identities and version chains."""
from __future__ import annotations

from dataclasses import dataclass

from .ids import make_version_id
from .models import (
    EventStatus,
    LegalEvent,
    LegalOperation,
    Provision,
    ProvisionVersion,
    TemporalInterval,
    TextUpdate,
)
from .state import TemporalState, TemporalStateError
from .version_chain import VersionChain


class EventApplicationError(ValueError):
    """A legal event cannot be applied without violating domain rules."""


class UnsupportedEventError(EventApplicationError):
    """The event operation is recognized but not implemented yet."""


@dataclass(frozen=True, slots=True)
class ApplyResult:
    event_id: str
    applied: bool
    already_applied: bool = False
    created_provision_ids: tuple[str, ...] = ()
    created_version_ids: tuple[str, ...] = ()
    closed_version_ids: tuple[str, ...] = ()
    directly_repealed_provision_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class EventApplier:
    """Apply one event atomically to an in-memory temporal state."""

    _TEXT_OPERATIONS = {
        LegalOperation.AMEND,
        LegalOperation.REPLACE,
        LegalOperation.CORRECT,
    }

    def apply(self, event: LegalEvent, state: TemporalState) -> ApplyResult:
        if event.id in state.applied_event_ids:
            existing = state.event(event.id)
            if existing != event:
                raise EventApplicationError(
                    f"event id {event.id} was already applied with different content"
                )
            return ApplyResult(event.id, applied=False, already_applied=True)

        self._validate_common(event, state)
        working = state.copy()
        result = self._apply_to_working_copy(event, working)
        working.record_applied_event(event)
        state.replace_with(working)
        return result

    def _validate_common(self, event: LegalEvent, state: TemporalState) -> None:
        if event.status not in {EventStatus.VERIFIED, EventStatus.AUTO_ACCEPTED}:
            raise EventApplicationError(
                f"event {event.id} is {event.status.value} and cannot be applied"
            )
        if not event.is_applicable or event.effective_on is None:
            raise EventApplicationError(f"event {event.id} is missing a date or resolved target")
        if state.document(event.target_document_id) is None:
            raise EventApplicationError(
                f"event target document does not exist: {event.target_document_id}"
            )
        if state.document(event.source_document_id) is None:
            raise EventApplicationError(
                f"event source document does not exist: {event.source_document_id}"
            )

    def _apply_to_working_copy(
        self, event: LegalEvent, state: TemporalState
    ) -> ApplyResult:
        if event.operation in self._TEXT_OPERATIONS:
            updates = self._text_updates(event)
            if not updates or event.insertions:
                raise EventApplicationError(
                    f"{event.operation.value} requires text updates and cannot create provisions"
                )
            return self._apply_text_updates(event, updates, state)

        if event.operation is LegalOperation.REPEAL:
            if event.text_updates or event.new_text or event.insertions:
                raise EventApplicationError("repeal cannot carry replacement text or insertions")
            return self._apply_repeal(event, state)

        if event.operation is LegalOperation.SUPPLEMENT:
            updates = self._text_updates(event)
            if not updates and not event.insertions:
                raise EventApplicationError("supplement requires a text update or insertion")
            updated = self._apply_text_updates(event, updates, state) if updates else None
            inserted = self._apply_insertions(event, state) if event.insertions else None
            return ApplyResult(
                event_id=event.id,
                applied=True,
                created_provision_ids=(inserted.created_provision_ids if inserted else ()),
                created_version_ids=(
                    (updated.created_version_ids if updated else ())
                    + (inserted.created_version_ids if inserted else ())
                ),
                closed_version_ids=(updated.closed_version_ids if updated else ()),
            )

        raise UnsupportedEventError(
            f"operation {event.operation.value} is not implemented in the first event-applier base"
        )

    @staticmethod
    def _text_updates(event: LegalEvent) -> tuple[TextUpdate, ...]:
        if event.text_updates:
            if event.new_text is not None:
                raise EventApplicationError("use either text_updates or legacy new_text, not both")
            explicit = set(event.target_provision_ids)
            update_targets = {update.target_provision_id for update in event.text_updates}
            if explicit and explicit != update_targets:
                raise EventApplicationError(
                    "target_provision_ids must match text_updates when both are provided"
                )
            return event.text_updates
        if event.new_text is None:
            return ()
        return tuple(
            TextUpdate(target_provision_id=target, new_text=event.new_text)
            for target in event.target_provision_ids
        )

    def _apply_text_updates(
        self,
        event: LegalEvent,
        updates: tuple[TextUpdate, ...],
        state: TemporalState,
    ) -> ApplyResult:
        chains: list[tuple[TextUpdate, VersionChain]] = []
        for update in updates:
            provision = self._target_provision(event, update.target_provision_id, state)
            chain = state.chain(provision.id)
            self._validate_open_chain(event, provision.id, chain)
            assert chain is not None
            chains.append((update, chain))

        closed_ids: list[str] = []
        created_ids: list[str] = []
        assert event.effective_on is not None
        for update, chain in chains:
            closed = chain.close_current(
                event.effective_on, ended_by_event_id=event.id
            )
            ordinal = len(chain.versions) + 1
            version = ProvisionVersion(
                id=make_version_id(chain.provision_id, ordinal),
                provision_id=chain.provision_id,
                ordinal=ordinal,
                text=update.new_text,
                validity=TemporalInterval(event.effective_on),
                created_by_event_id=event.id,
                provenance=event.provenance,
            )
            chain.add(version)
            closed_ids.append(closed.id)
            created_ids.append(version.id)

        return ApplyResult(
            event_id=event.id,
            applied=True,
            created_version_ids=tuple(created_ids),
            closed_version_ids=tuple(closed_ids),
        )

    def _apply_repeal(self, event: LegalEvent, state: TemporalState) -> ApplyResult:
        targets: list[tuple[str, VersionChain]] = []
        for target_id in event.target_provision_ids:
            provision = self._target_provision(event, target_id, state)
            chain = state.chain(provision.id)
            self._validate_open_chain(event, provision.id, chain)
            assert chain is not None
            targets.append((provision.id, chain))

        assert event.effective_on is not None
        closed = tuple(
            chain.close_current(event.effective_on, ended_by_event_id=event.id).id
            for _, chain in targets
        )
        return ApplyResult(
            event_id=event.id,
            applied=True,
            closed_version_ids=closed,
            directly_repealed_provision_ids=tuple(target for target, _ in targets),
        )

    def _apply_insertions(self, event: LegalEvent, state: TemporalState) -> ApplyResult:
        assert event.effective_on is not None
        created_provisions: list[str] = []
        created_versions: list[str] = []
        pending_ids = {insertion.provision_id for insertion in event.insertions}

        # Insertions may depend on another node created by the same event. Apply
        # them in resolvable rounds instead of relying on input order.
        remaining = list(event.insertions)
        while remaining:
            progressed = False
            for insertion in remaining.copy():
                parent_ready = insertion.parent_id is None or state.provision(insertion.parent_id)
                anchor_ready = (
                    insertion.after_provision_id is None
                    or state.provision(insertion.after_provision_id)
                )
                if not parent_ready or not anchor_ready:
                    continue
                if state.provision(insertion.provision_id) is not None:
                    raise EventApplicationError(
                        f"inserted provision already exists: {insertion.provision_id}"
                    )
                provision = Provision(
                    id=insertion.provision_id,
                    document_id=event.target_document_id,
                    level=insertion.level,
                    title=insertion.title,
                    parent_id=insertion.parent_id,
                    order_index=insertion.order_index,
                    inserted_after_id=insertion.after_provision_id,
                )
                try:
                    state.add_provision(provision)
                except TemporalStateError as exc:
                    raise EventApplicationError(str(exc)) from exc
                version = ProvisionVersion(
                    id=make_version_id(provision.id, 1),
                    provision_id=provision.id,
                    ordinal=1,
                    text=insertion.text,
                    validity=TemporalInterval(event.effective_on),
                    created_by_event_id=event.id,
                    provenance=event.provenance,
                )
                state.add_version(version)
                created_provisions.append(provision.id)
                created_versions.append(version.id)
                remaining.remove(insertion)
                pending_ids.discard(insertion.provision_id)
                progressed = True
            if not progressed:
                unresolved = sorted(pending_ids)
                raise EventApplicationError(
                    f"unresolved or cyclic insertion dependencies: {unresolved}"
                )

        return ApplyResult(
            event_id=event.id,
            applied=True,
            created_provision_ids=tuple(created_provisions),
            created_version_ids=tuple(created_versions),
        )

    @staticmethod
    def _target_provision(
        event: LegalEvent, provision_id: str, state: TemporalState
    ) -> Provision:
        provision = state.provision(provision_id)
        if provision is None:
            raise EventApplicationError(f"target provision does not exist: {provision_id}")
        if provision.document_id != event.target_document_id:
            raise EventApplicationError(
                f"target provision {provision_id} belongs to {provision.document_id}, "
                f"not {event.target_document_id}"
            )
        return provision

    @staticmethod
    def _validate_open_chain(
        event: LegalEvent,
        provision_id: str,
        chain: VersionChain | None,
    ) -> None:
        if chain is None:
            raise EventApplicationError(f"target provision has no version: {provision_id}")
        current = chain.current()
        if current is None:
            raise EventApplicationError(
                f"target provision has no open version: {provision_id}"
            )
        assert event.effective_on is not None
        if event.effective_on <= current.validity.start:
            raise EventApplicationError(
                f"event {event.id} must be later than current version start "
                f"{current.validity.start.isoformat()}"
            )
