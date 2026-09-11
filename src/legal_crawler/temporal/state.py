"""In-memory aggregate used to validate temporal logic without infrastructure."""
from __future__ import annotations

from collections import defaultdict

from .models import LegalDocument, LegalEvent, Provision, ProvisionVersion
from .version_chain import VersionChain


class TemporalStateError(ValueError):
    """The aggregate would become structurally inconsistent."""


class TemporalState:
    """Documents, provision trees, version chains and applied legal events.

    This is intentionally an in-memory domain object rather than a repository.
    It provides an executable specification for later storage adapters.
    """

    def __init__(self) -> None:
        self._documents: dict[str, LegalDocument] = {}
        self._provisions: dict[str, Provision] = {}
        self._chains: dict[str, VersionChain] = {}
        self._events: dict[str, LegalEvent] = {}
        self._applied_event_ids: set[str] = set()

    @property
    def applied_event_ids(self) -> frozenset[str]:
        return frozenset(self._applied_event_ids)

    def add_document(self, document: LegalDocument) -> bool:
        existing = self._documents.get(document.id)
        if existing is not None:
            if existing == document:
                return False
            raise TemporalStateError(f"conflicting document id: {document.id}")
        self._documents[document.id] = document
        return True

    def add_provision(self, provision: Provision) -> bool:
        existing = self._provisions.get(provision.id)
        if existing is not None:
            if existing == provision:
                return False
            raise TemporalStateError(f"conflicting provision id: {provision.id}")
        if provision.document_id not in self._documents:
            raise TemporalStateError(
                f"provision {provision.id} refers to unknown document {provision.document_id}"
            )
        if provision.parent_id is not None:
            parent = self._provisions.get(provision.parent_id)
            if parent is None:
                raise TemporalStateError(
                    f"provision {provision.id} refers to unknown parent {provision.parent_id}"
                )
            if parent.document_id != provision.document_id:
                raise TemporalStateError("a provision and its parent must share a document")
        if provision.inserted_after_id is not None:
            anchor = self._provisions.get(provision.inserted_after_id)
            if anchor is None:
                raise TemporalStateError(
                    f"provision {provision.id} refers to unknown insertion anchor "
                    f"{provision.inserted_after_id}"
                )
            if (
                anchor.document_id != provision.document_id
                or anchor.parent_id != provision.parent_id
            ):
                raise TemporalStateError(
                    "an insertion anchor must be a sibling in the same document"
                )
        self._provisions[provision.id] = provision
        self._assert_acyclic(provision.id)
        return True

    def add_version(self, version: ProvisionVersion) -> bool:
        if version.provision_id not in self._provisions:
            raise TemporalStateError(
                f"version {version.id} refers to unknown provision {version.provision_id}"
            )
        chain = self._chains.setdefault(
            version.provision_id, VersionChain(version.provision_id)
        )
        return chain.add(version)

    def document(self, document_id: str) -> LegalDocument | None:
        return self._documents.get(document_id)

    def provision(self, provision_id: str) -> Provision | None:
        return self._provisions.get(provision_id)

    def chain(self, provision_id: str) -> VersionChain | None:
        return self._chains.get(provision_id)

    def event(self, event_id: str | None) -> LegalEvent | None:
        return self._events.get(event_id) if event_id else None

    def provisions_for_document(self, document_id: str) -> tuple[Provision, ...]:
        return tuple(
            provision
            for provision in self._provisions.values()
            if provision.document_id == document_id
        )

    def children_of(self, parent_id: str | None, document_id: str) -> tuple[Provision, ...]:
        siblings = [
            provision
            for provision in self._provisions.values()
            if provision.document_id == document_id and provision.parent_id == parent_id
        ]
        return tuple(self._order_siblings(siblings))

    def descendants_of(self, provision_id: str) -> tuple[Provision, ...]:
        root = self._provisions.get(provision_id)
        if root is None:
            return ()
        out: list[Provision] = []
        queue = list(self.children_of(root.id, root.document_id))
        while queue:
            child = queue.pop(0)
            out.append(child)
            queue[0:0] = list(self.children_of(child.id, root.document_id))
        return tuple(out)

    def document_order(self, document_id: str) -> tuple[Provision, ...]:
        """Depth-first legal-text order, respecting explicit insertion anchors."""
        out: list[Provision] = []

        def walk(parent_id: str | None) -> None:
            for provision in self.children_of(parent_id, document_id):
                out.append(provision)
                walk(provision.id)

        walk(None)
        return tuple(out)

    def copy(self) -> "TemporalState":
        duplicate = TemporalState()
        duplicate._documents = self._documents.copy()
        duplicate._provisions = self._provisions.copy()
        duplicate._chains = {
            provision_id: VersionChain(provision_id, chain.versions)
            for provision_id, chain in self._chains.items()
        }
        duplicate._events = self._events.copy()
        duplicate._applied_event_ids = self._applied_event_ids.copy()
        return duplicate

    def replace_with(self, other: "TemporalState") -> None:
        """Atomically publish a fully validated working copy."""
        self._documents = other._documents
        self._provisions = other._provisions
        self._chains = other._chains
        self._events = other._events
        self._applied_event_ids = other._applied_event_ids

    def record_applied_event(self, event: LegalEvent) -> None:
        existing = self._events.get(event.id)
        if existing is not None and existing != event:
            raise TemporalStateError(f"conflicting event id: {event.id}")
        self._events[event.id] = event
        self._applied_event_ids.add(event.id)

    def _assert_acyclic(self, start_id: str) -> None:
        seen: set[str] = set()
        current = self._provisions.get(start_id)
        while current is not None:
            if current.id in seen:
                self._provisions.pop(start_id, None)
                raise TemporalStateError(f"cycle in provision tree at {current.id}")
            seen.add(current.id)
            current = self._provisions.get(current.parent_id) if current.parent_id else None

    @staticmethod
    def _order_siblings(siblings: list[Provision]) -> list[Provision]:
        by_anchor: dict[str, list[Provision]] = defaultdict(list)
        base: list[Provision] = []
        sibling_ids = {item.id for item in siblings}
        for item in siblings:
            if item.inserted_after_id in sibling_ids:
                by_anchor[item.inserted_after_id].append(item)
            else:
                base.append(item)

        key = lambda item: (  # noqa: E731 - compact shared ordering key
            item.order_index is None,
            item.order_index if item.order_index is not None else 0,
            item.id,
        )
        base.sort(key=key)
        for anchored in by_anchor.values():
            anchored.sort(key=key)

        ordered: list[Provision] = []
        emitted: set[str] = set()

        def emit(item: Provision) -> None:
            if item.id in emitted:
                raise TemporalStateError("cycle in insertion anchors")
            emitted.add(item.id)
            ordered.append(item)
            for follower in by_anchor.get(item.id, []):
                emit(follower)

        for item in base:
            emit(item)
        if len(emitted) != len(siblings):
            raise TemporalStateError("unresolvable insertion-anchor ordering")
        return ordered
