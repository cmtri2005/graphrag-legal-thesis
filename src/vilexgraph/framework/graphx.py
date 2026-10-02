"""One-hop graph expansion of retrieved units (plan phase-5-6, P5; B5, B6, proposed, A2).

Two edge sets of Definition 2 (`docs/graph_justification.md` §4), each used by
a different system:

    part   𝓔_part  the legal hierarchy: a unit's parent and its direct children
                   (Điều → Khoản → Điểm). B6, the Vietnamese hierarchical KG.
    rel    𝓔_rel   the typed relation that matters to *what a unit says at t*:
                   the amending or repealing instruction aimed at its provision.
                   B5 and the proposed system.

Both read the stores that already exist — `provisions` in `data/temporal.sqlite`
for the tree, and the `instruction` units of the retrieval index for the
commands — so there is no graph database to run and nothing to reload. ADR 0001
makes Neo4j the derived store for these edges; at one hop with these two edge
kinds a SQL join returns the same neighbours, and Neo4j stays the place for the
multi-hop closure of formula (2) if a later experiment needs it.

**Expansion honours the system's tier.** Formula (4) narrows the search space
to 𝒰ₜ before ranking, and a neighbour is part of the search space, so a
temporal system only admits neighbours that pass its own predicate. A
non-temporal system (tier `none`, B5/B6) admits all of them — that is exactly
what makes it the non-temporal baseline. An instruction unit has no version
window, so under a temporal tier it is judged by its acting document alone: a
command is in force once the document that issues it is.

Parameters are deliberately small and fixed; they are not part of any result and
may be tuned on `dev` only (ADR 0003 §7):

    SEEDS    expand only the top-ranked hits, so the prompt stays bounded
    FANOUT   neighbours taken per seed per edge kind
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .retrieve import Hit
from .systems import SystemSpec
from .temporal import predicate

SEEDS = 5
FANOUT = 3
TEMPORAL_DB = Path("data/temporal.sqlite")
SIGNAL = "graph"


class Graph:
    """Neighbour lookup over `part` and `rel`."""

    def __init__(self, corpus, temporal_db: Path | str = TEMPORAL_DB) -> None:
        self.corpus = corpus
        path = Path(temporal_db)
        if not path.exists():
            raise FileNotFoundError(f"no provision tree at {path}; `part` expansion reads it")
        self.tree = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

    def close(self) -> None:
        self.tree.close()

    # -- edges ---------------------------------------------------------------------------

    def part(self, provision_id: str) -> list[str]:
        """The parent, then the direct children, of one provision."""
        row = self.tree.execute(
            "SELECT parent_id FROM provisions WHERE id=?", (provision_id,)).fetchone()
        out = [row[0]] if row and row[0] else []
        out += [r[0] for r in self.tree.execute(
            "SELECT id FROM provisions WHERE parent_id=? ORDER BY order_index LIMIT ?",
            (provision_id, FANOUT))]
        return out[:FANOUT + 1]

    def rel(self, provision_id: str) -> list[str]:
        """Instruction units whose resolved target is this provision."""
        return [r[0] for r in self.corpus.db.execute(
            "SELECT unit_id FROM units WHERE kind='instruction' AND provision_id=?"
            " ORDER BY unit_id LIMIT ?", (provision_id, FANOUT))]

    # -- units ---------------------------------------------------------------------------

    def _units_of(self, provision_ids: list[str], layer: str) -> list[str]:
        """The units that stand for these provisions in `layer`."""
        if not provision_ids:
            return []
        marks = ",".join("?" * len(provision_ids))
        kind = "provision" if layer == "asis" else "version"
        return [r[0] for r in self.corpus.db.execute(
            f"SELECT unit_id FROM units WHERE layer=? AND kind=? AND provision_id IN ({marks})",
            [layer, kind, *provision_ids])]

    def _admit(self, unit_ids: list[str], tier: str, as_of: str) -> list[str]:
        """Keep the units this tier admits at `as_of`, in the order given."""
        if not unit_ids or tier == "none":
            return unit_ids
        marks = ",".join("?" * len(unit_ids))
        kept = set()
        for kind, use in (("instruction", "document"), (None, tier)):
            clause, params = predicate(use, as_of)
            rows = self.corpus.db.execute(
                "SELECT u.unit_id FROM units u"
                " LEFT JOIN documents d ON d.document_id = u.document_id"
                f" WHERE u.unit_id IN ({marks}) AND u.kind {'=' if kind else '!='} ?"
                f" AND {clause}", [*unit_ids, kind or "instruction", *params])
            kept.update(r[0] for r in rows)
        return [u for u in unit_ids if u in kept]


def expand(graph: Graph, spec: SystemSpec, hits: list[Hit], as_of: str) -> list[Hit]:
    """`hits` followed by their admitted neighbours, each with a `graph` signal.

    A neighbour already among the hits is not added again, and its first
    appearance keeps the signal it was ranked with.
    """
    if not spec.expand or spec.expand_edges == "none" or not hits:
        return hits
    corpus = graph.corpus
    seen = {h.unit_id for h in hits}
    extra: list[Hit] = []
    for rank, hit in enumerate(hits[:SEEDS]):
        unit = corpus.unit(hit.unit_id)
        if unit is None or unit.provision_id is None:
            continue
        found: list[str] = []
        if spec.expand_edges == "part":
            found += graph._units_of(graph.part(unit.provision_id), spec.layer)
        if spec.expand_edges == "rel":
            found += graph.rel(unit.provision_id)
        for unit_id in graph._admit(found, spec.temporal, as_of):
            if unit_id not in seen:
                seen.add(unit_id)
                extra.append(Hit(unit_id, {SIGNAL: 1.0 / (1 + rank)}))
    return hits + extra
