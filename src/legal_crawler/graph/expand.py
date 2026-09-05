"""Stage 2: BFS graph expansion (docs/crawling-plan.md §"Stage 2").

Expands from a set of seed document ids by following `references[]` edges,
but only recurses through edges classified as GENEALOGY (amends/replaces/
repeals/consolidates/implements — a naturally finite lineage per law).
OPEN_CITATION edges (cites/applies/basis) are still recorded as edges, just
never used to discover new documents to fetch, so the crawl can't wander
into an unrelated legal domain through a citation chain.

Decoupled from ApiClient (takes a plain `fetch_document` callable) so the
BFS logic itself can be unit-tested with an in-memory fake instead of a
mocked HTTP stack.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from ..models import Edge
from ..vocab.reference_types import ReferenceTypeMap

JsonDict = dict[str, Any]
FetchDocument = Callable[[str], JsonDict]

DEFAULT_MAX_DOCUMENTS = 5000


@dataclass
class ExpansionResult:
    documents: dict[str, JsonDict] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    truncated: bool = False
    failed: dict[str, str] = field(default_factory=dict)


def expand(
    seed_ids: Iterable[str],
    fetch_document: FetchDocument,
    reference_types: ReferenceTypeMap,
    *,
    max_documents: int = DEFAULT_MAX_DOCUMENTS,
) -> ExpansionResult:
    """Breadth-first expansion from `seed_ids` through genealogy edges.

    `max_documents` is a circuit breaker against bugs/unexpected cycles, not
    the intended scope-limiting mechanism (see docs/crawling-plan.md).

    A `fetch_document` failure (network error, dangling/removed target id —
    expected when crawling a live external site) is recorded in
    `result.failed` and that node is skipped, but the rest of the BFS
    continues: one bad id must not abort a multi-hour crawl. This is
    deliberately different from an `UnknownReferenceTypeError` raised by
    `reference_types.is_expandable` below, which is a data-integrity bug in
    *our* mapping table and is left to propagate and stop the run.
    """
    result = ExpansionResult()
    visited: set[str] = set()
    queue: deque[str] = deque(dict.fromkeys(seed_ids))

    while queue:
        doc_id = queue.popleft()
        if doc_id in visited:
            continue
        if len(visited) >= max_documents:
            result.truncated = True
            break
        visited.add(doc_id)

        try:
            document = fetch_document(doc_id)
        except Exception as exc:  # noqa: BLE001 — see docstring: fetch failures are expected
            result.failed[doc_id] = str(exc)
            continue
        result.documents[doc_id] = document

        for reference in document.get("references") or []:
            edge = _parse_edge(doc_id, reference)
            if edge is None:
                continue
            result.edges.append(edge)
            if edge.target_id not in visited and reference_types.is_expandable(edge.reference_type):
                queue.append(edge.target_id)

    return result


def _parse_edge(source_id: str, reference: JsonDict) -> Edge | None:
    reference_type = reference.get("referenceType")
    target_id = (reference.get("targetDocument") or {}).get("id")
    if reference_type is None or not target_id:
        return None
    return Edge(source_id=source_id, target_id=str(target_id), reference_type=int(reference_type))
