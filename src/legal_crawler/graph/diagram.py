"""Stage 2b — inbound ("who acted on me") relations from /doc/{id}/diagram.

Why this exists
---------------
`references[]` on /doc/{id} records relations in ONE direction only. If
document B amends document A, that edge lives in **B's** references, never in
A's. Stage 2's BFS only ever walks outward from documents it already holds,
so if B was never discovered some other way, the crawl never learns that A was
amended at all — and a repeal we never fetched is a repeal Stage 6 can never
apply.

Measured on a random sample of 150 crawled documents: 27% had at least one
genealogy neighbour that the corpus did not contain, and in a hand-checked
batch 7 of 7 amending documents were missing outright.

`/doc/{id}/diagram` returns two maps keyed by the same `referenceType` codes:

    documentNamesByType   -> outbound, i.e. what references[] already gives us
    documentNamesBySource -> INBOUND, the direction we were blind to

Edge direction
--------------
Reverse edges are normalised to the same orientation as forward ones — the
*acting* document is always `source_id`. So an inbound code-10 entry on
document Y becomes `Edge(source=the amender, target=Y, type=10)`, exactly the
shape `references[]` would have produced from the amender's side. Downstream
code therefore needs no notion of "reverse" at all.
"""
from __future__ import annotations

from typing import Any

from ..models import Edge

JsonDict = dict[str, Any]

# Which inbound relations justify fetching a document we don't have yet.
#
# Kept here as crawl POLICY, deliberately not in reference_type_map.json —
# that file is hand-verified ground truth about what each code means, and
# should not carry decisions about what we choose to crawl.
#
# Included: the relations that change whether, or from when, a provision is in
# force. Each is naturally bounded — a document has a handful of amenders, not
# an open-ended list.
#   1  bị bãi bỏ            5  bị đình chỉ thi hành     6  được đính chính
#  10  được sửa đổi bổ sung 11 bị tạm ngưng hiệu lực   12  được thay thế
#
# Excluded on purpose:
#   9 (được quy định chi tiết, hướng dẫn thi hành) — inbound, this means
#     "every decree and circular implementing me". For a Law that is dozens of
#     documents spanning unrelated fields; it accounted for 453 of the 494
#     missing neighbours in the sample above and would blow the crawl out to
#     the full 172k-document database. Recorded as an edge, never expanded —
#     the same rule §5 already applies to open-citation edges.
#   7 (được hợp nhất) — consolidated documents are derived, out of §4 scope,
#     and 85% of the ones already crawled have no text at all.
REVERSE_EXPANDABLE: frozenset[int] = frozenset({1, 5, 6, 10, 11, 12})


def parse_reverse_edges(doc_id: str, diagram: JsonDict) -> list[Edge]:
    """Inbound relations for `doc_id`, oriented like a forward edge."""
    edges: list[Edge] = []
    for code, items in (diagram.get("documentNamesBySource") or {}).items():
        for item in items or []:
            other_id = item.get("id")
            if not other_id:
                continue
            edges.append(
                Edge(source_id=str(other_id), target_id=doc_id, reference_type=int(code))
            )
    return edges


def expandable_targets(edges: list[Edge], held: set[str]) -> set[str]:
    """Documents we should fetch: an acting document we don't have yet."""
    return {
        edge.source_id
        for edge in edges
        if edge.reference_type in REVERSE_EXPANDABLE and edge.source_id not in held
    }
