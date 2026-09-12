"""Shared authoritative state for all in-memory temporal repositories."""
from __future__ import annotations

from dataclasses import dataclass

from legal_crawler.temporal.models import GraphEdge, LegalEvent
from legal_crawler.temporal.state import TemporalState


@dataclass(frozen=True, slots=True)
class MemoryStoreSnapshot:
    state: TemporalState
    events: dict[str, LegalEvent]
    edges: dict[str, GraphEdge]


class MemoryStore:
    """One shared store; repository instances are lightweight views over it."""

    def __init__(self) -> None:
        self.state = TemporalState()
        self.events: dict[str, LegalEvent] = {}
        self.edges: dict[str, GraphEdge] = {}

    def snapshot(self) -> MemoryStoreSnapshot:
        return MemoryStoreSnapshot(
            state=self.state.copy(),
            events=self.events.copy(),
            edges=self.edges.copy(),
        )

    def restore(self, snapshot: MemoryStoreSnapshot) -> None:
        """Restore contents in place so every repository keeps a live view."""
        self.state.replace_with(snapshot.state)
        self.events.clear()
        self.events.update(snapshot.events)
        self.edges.clear()
        self.edges.update(snapshot.edges)

