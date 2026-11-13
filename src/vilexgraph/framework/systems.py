"""Every system in the experiments, as one row of one table (plan phase-5-6).

A baseline here is not a separate implementation — it is the proposed system
with something switched off. That is the point: B4, B7, B7+ and the proposed
system share one retriever, one generator, one prompt and one `k`, so the only
thing that differs between two rows is what the question asks about. It also
removes the standing objection that a baseline was handicapped.

The decisive axis is `temporal`, the representation ladder of `temporal.py`.
Measured on this corpus (plan, 01/10), the other graph roles have little
surface to win on — ancestor repeal reaches 24 of 1.150 main-table rows, and
the acting document is itself still in force on 970 of the 974 rows that cite
an amending instruction — so `expand` is carried for A2 and for B5/B6, and is
reported as what it measures rather than as a contribution.

`context` is on for every retrieval baseline on purpose. The header lifts
question-token coverage of the gold unit from 0,555 to 0,740, but it is an
ordinary chunk-header gain, not a graph result; giving it only to the proposed
system would buy a win that belongs to anyone who prepends a heading. B2 is
registered both ways so the size of that gain is itself reported.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .temporal import LAYER_B_ONLY, TIERS

LAYERS = ("asis", "version")
EXPAND_EDGES = ("none", "rel", "part", "rel_up")
VERIFY_MODES = ("off", "warn", "reject")


class SystemError_(ValueError):
    """A configuration that cannot mean what it says."""


@dataclass(frozen=True, slots=True)
class SystemSpec:
    """One row of the experiment table."""

    name: str
    layer: str | None = None          # None = no retrieval at all (B1)
    lexical: bool = False
    dense: bool = False
    rerank: bool = False
    temporal: str = "none"            # a tier of temporal.TIERS
    context: bool = False
    expand: int = 0                   # hops
    expand_edges: str = "none"        # which edge set those hops follow
    verify: str = "off"               # off | warn | reject
    k: int = 20
    note: str = ""
    repeal_note: bool = False         # graph-derived repeal links in the user prompt (X2)
    validity_note: bool = False       # each unit's propagated windows printed in the prompt (post hoc, 13/11)

    def __post_init__(self) -> None:
        if self.temporal not in TIERS:
            raise SystemError_(f"{self.name}: unknown tier {self.temporal!r}")
        if self.layer is not None and self.layer not in LAYERS:
            raise SystemError_(f"{self.name}: unknown layer {self.layer!r}")
        if self.verify not in VERIFY_MODES:
            raise SystemError_(f"{self.name}: unknown verify mode {self.verify!r}")
        if self.expand_edges not in EXPAND_EDGES:
            raise SystemError_(f"{self.name}: unknown edge set {self.expand_edges!r}")
        if self.retrieves and not (self.lexical or self.dense):
            raise SystemError_(f"{self.name}: a retrieving system needs lexical or dense")
        if not self.retrieves and (self.lexical or self.dense or self.temporal != "none"):
            raise SystemError_(f"{self.name}: layer=None cannot retrieve or filter")
        # A version window describes a version, so it says nothing about a layer-A unit.
        if self.temporal in LAYER_B_ONLY and self.layer != "version":
            raise SystemError_(
                f"{self.name}: tier {self.temporal!r} needs layer 'version' — layer A units "
                f"carry no version window, so the filter would reject every candidate")
        if self.validity_note and self.layer != "version":
            raise SystemError_(f"{self.name}: validity_note needs layer 'version' — only versions carry windows")
        if self.expand_edges == "rel_up" and self.temporal != "propagated":
            raise SystemError_(f"{self.name}: rel_up needs tier propagated")
        if self.expand and self.expand_edges == "none":
            raise SystemError_(f"{self.name}: expand={self.expand} needs an edge set")

    @property
    def retrieves(self) -> bool:
        return self.layer is not None

    def variant(self, name: str, **changes) -> "SystemSpec":
        return replace(self, name=name, **changes)


_PROPOSED = SystemSpec(
    name="proposed", layer="version", lexical=True, dense=True, rerank=True,
    temporal="propagated", context=True, expand=1, expand_edges="rel", verify="reject",
    note="L4–L5: 𝒰ₜ by formula (3), hybrid ranking, citation-constrained answer, Verifier")
_B7 = SystemSpec(name="b7", layer="asis", lexical=True, dense=True, rerank=True,
                 temporal="document", context=True,
                 note="B7 — document-level date filter, no graph (the main control)")
_B7PLUS = SystemSpec(name="b7plus", layer="version", lexical=True, dense=True, rerank=True,
                     temporal="version", context=True,
                     note="B7+ — version-level filter; the proposed system minus the online graph")

_PROPOSED2 = _PROPOSED.variant("proposed2", rerank=False, expand_edges="rel_up")
# Post hoc, after the final test was seen (REFACTOR_PLAN 2.6): a flat RAG that reads the same version
# store. `bvnone` gets the consolidated wordings but no filter; `bvdate` also shows each unit's
# windows and leaves the choice to the generator. Exploratory only, never part of FINAL_GENERATION.
_BVNONE = SystemSpec(name="bvnone", layer="version", lexical=True, dense=True, context=True,
                     note="post hoc — layer B, no temporal filter: flat RAG over the version store")

REGISTRY: dict[str, SystemSpec] = {s.name: s for s in (
    SystemSpec(name="b1", note="B1 — the generator alone, no retrieval"),
    SystemSpec(name="b2", layer="asis", lexical=True,
               note="B2 — BM25 over the unit's own text"),
    SystemSpec(name="b2ctx", layer="asis", lexical=True, context=True,
               note="B2 with the hierarchy header: isolates the ordinary chunk-header gain"),
    SystemSpec(name="b3", layer="asis", dense=True, context=True, note="B3 — dense"),
    SystemSpec(name="b4", layer="asis", lexical=True, dense=True, context=True,
               note="B4 — BM25 + dense by reciprocal rank fusion (k=60), no reranker"),
    SystemSpec(name="b5", layer="asis", lexical=True, dense=True, context=True,
               expand=1, expand_edges="rel",
               note="B5 — non-temporal GraphRAG; reduced corpus, see the plan"),
    SystemSpec(name="b6", layer="asis", lexical=True, dense=True, context=True,
               expand=1, expand_edges="part",
               note="B6 — hierarchical legal KG, structure only"),
    _B7,
    _B7.variant("b7v", layer="version",
                note="B7 over layer B: consolidated version texts, still the document filter. "
                     "Separates the wording L3 consolidated from the version window (K-07)"),
    _B7PLUS,
    _B7PLUS.variant("b7pp", temporal="propagated",
                    note="B7+ with propagated windows: the ladder's top rung, no online graph (K-07)"),
    _PROPOSED,
    _PROPOSED2,
    _PROPOSED2.variant("proposed3", repeal_note=True),
    _PROPOSED2.variant("p2a2", expand=0, expand_edges="none"),
    _PROPOSED2.variant("p2a3", verify="off"),
    _BVNONE,
    _BVNONE.variant("bvdate", validity_note=True,
                    note="post hoc — bvnone with each unit's validity windows printed in the prompt"),
    _PROPOSED.variant("a1", temporal="none", note="A1 — drop the effectivity constraint"),
    _PROPOSED.variant("a2", expand=0, expand_edges="none", note="A2 — drop graph expansion"),
    _PROPOSED.variant("a3", verify="off", note="A3 — drop the Temporal Verifier"),
    _PROPOSED.variant("a4", temporal="version",
                      note="A4 — drop propagation: the recursive clause of (3). This is the "
                           "variant H3 actually needs; the proposal's A4 is only a proxy"),
)}

#: The main table: one retriever, one generator, and each rung changes exactly one thing
#: (decided 11/10, K-07): the tier, then the layer, then the tier twice. That holds on
#: lexical retrieval (`--no-dense`, which also drops the reranker); with dense retrieval
#: the first rung is b4, not b2ctx. `proposed` = b7pp + the online graph (expansion,
#: Verifier), reported on its own line.
LADDER = ("b2ctx", "b7", "b7v", "b7plus", "b7pp")

#: ADR 0006 §2: what the final test set generates answers with, besides the one proposed
#: system P (`proposed2` or `proposed3`, chosen on dev). This is the list; documents point
#: here. The two oracles are built from gold by `colab_b1`, so they are not in REGISTRY.
ORACLES = ("oracle", "oracle_now")
FINAL_GENERATION = ("b1", "b2ctx", "b3", "b4", "b5", "b6", "b7", "b7plus", "b7pp", *ORACLES)
#: Dev only: the two candidates for P, and the two descriptive component drops.
DEV_ONLY = ("proposed2", "proposed3", "p2a2", "p2a3")
#: Exploratory baselines added after the final test was seen; reported apart from the locked table.
POSTHOC = ("bvnone", "bvdate")


def get(name: str) -> SystemSpec:
    try:
        return REGISTRY[name]
    except KeyError:
        raise SystemError_(
            f"unknown system {name!r}; known: {', '.join(sorted(REGISTRY))}") from None


def table() -> str:
    """The final configuration as markdown, as run: hybrid, so no reranker (cut 05/11)."""
    lines = ["| Hệ | Lớp | Từ vựng | Dense | Lọc thời gian | Mở rộng | Verifier | Thông báo bãi bỏ | Chạy ở |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name, where in ((n, "dev, test") for n in FINAL_GENERATION if n not in ORACLES):
        lines.append(_row(REGISTRY[name], where))
    lines += [_row(REGISTRY[n], "dev; hệ được chọn làm P chạy test" if n.startswith("proposed") else "dev")
              for n in DEV_ONLY]
    lines += [f"| `{n}` | căn cứ gold | — | — | — | — | — | — | dev, test |" for n in ORACLES]
    return "\n".join(lines)


def _row(s: SystemSpec, where: str) -> str:
    yes = {True: "có", False: "không"}
    expand = f"{s.expand_edges}, {s.expand} bước" if s.expand else "không"
    return (f"| `{s.name}` | {s.layer or 'không truy xuất'} | {yes[s.lexical]} | {yes[s.dense]} | {s.temporal} "
            f"| {expand} | {s.verify} | {yes[s.repeal_note]} | {where} |")


if __name__ == "__main__":
    print(table())
