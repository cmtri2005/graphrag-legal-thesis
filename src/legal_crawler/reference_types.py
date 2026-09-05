"""Ground-truth `referenceType` mapping (docs/crawling-plan.md §3b).

The numeric codes in `references[].referenceType` have no client-side label
mapping anywhere on vbpl.vn (checked: not in any JS bundle, no labelled
endpoint) — the mapping must be built by hand, once, before the graph
builder runs. This module only loads and enforces that hand-built table; it
never guesses a label itself.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DEFAULT_MAP_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "reference_type_map.json"


class EdgeGroup(Enum):
    """How a reference type is used when expanding the crawl graph.

    GENEALOGY edges (amends/replaces/repeals/consolidates/implements) form a
    naturally finite lineage per law, so Stage 2 BFS expands through them
    with no hop limit. OPEN_CITATION edges (cites/applies/basis) can point
    anywhere and are recorded but never expanded through.
    """

    GENEALOGY = "genealogy"
    OPEN_CITATION = "open_citation"


class UnknownReferenceTypeError(RuntimeError):
    """A referenceType code with no verified entry in the mapping table.

    Raised instead of silently defaulting, so a mislabelled edge never
    reaches the graph — see docs/crawling-plan.md §3b point 5.
    """


@dataclass(frozen=True, slots=True)
class ReferenceTypeInfo:
    code: int
    label_vi: str
    group: EdgeGroup
    verified: bool


class ReferenceTypeMap:
    """Loaded, verified `referenceType` -> label/group table."""

    def __init__(self, entries: dict[int, ReferenceTypeInfo]) -> None:
        self._entries = entries

    @classmethod
    def load(cls, path: Path = DEFAULT_MAP_PATH) -> "ReferenceTypeMap":
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = {}
        for code_str, info in raw.get("codes", {}).items():
            if not info.get("verified"):
                continue
            entries[int(code_str)] = ReferenceTypeInfo(
                code=int(code_str),
                label_vi=info["label_vi"],
                group=EdgeGroup(info["group"]),
                verified=True,
            )
        return cls(entries)

    @property
    def codes(self) -> frozenset[int]:
        """Every verified code, for checking a corpus against the table."""
        return frozenset(self._entries)

    def classify(self, reference_type: int) -> ReferenceTypeInfo:
        try:
            return self._entries[reference_type]
        except KeyError:
            raise UnknownReferenceTypeError(
                f"referenceType={reference_type} has no verified entry in "
                f"{DEFAULT_MAP_PATH.name}; add it via scripts/collect_reference_types.py "
                "and manual verification before running the graph builder."
            ) from None

    def is_expandable(self, reference_type: int) -> bool:
        """Whether Stage 2 BFS should follow this edge to new documents."""
        return self.classify(reference_type).group is EdgeGroup.GENEALOGY
