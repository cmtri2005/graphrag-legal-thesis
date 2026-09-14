"""Stage 5b — attach body text to the provision-tree nodes (docs/plans/completed/2026-09-04-truoc-stage-6.md §B).

The plan assumed this was a text-alignment problem. It mostly is not: for ~60%
of the corpus the server's own HTML already tags each paragraph with the tree
node's uuid::

    <p id="078fd8b7-..." class="prov-article">Điều 1. Phạm vi điều chỉnh</p>
    <p id="cdad2135-..." class="prov-clause">1. Thông tư này quy định ...</p>

so those documents are an exact join, not a guess. The rest are older records
stored as plain HTML with no ids at all, and only those need marker matching
("Điều 5", "3.", "b)") — walked in tree order so a mismatch stops that node
instead of shifting every node after it.

Two rules, both §3b:

* A node is either matched or **left out and counted**. Nothing is assigned on a
  hunch, and `coverage` is reported per document so a bad parse is visible.
* Text is stored verbatim apart from Unicode NFC. Old-style tone placement
  (`thuỷ` vs `thủy`) is deliberately NOT normalised — this is the legal text
  itself, and rewriting it would make quotes differ from the source.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser

# Below this share of tree nodes with text, a document goes to the review queue
# (`data/provision_review.txt`) and the id join is topped up with markers.
REVIEW_THRESHOLD = 0.5

# Layout noise that must never reach the text.
_SKIP_TAGS = {"style", "script", "head"}

# What counts as one chunk of text. The new-format HTML puts the node id on
# `<p>`, but the older records wrap each paragraph in a bare `<div>` instead —
# splitting on `<p>` alone silently returned nothing for those.
_BLOCK_TAGS = {"p", "div", "li", "td", "h1", "h2", "h3", "h4", "h5", "h6"}

# level -> how that node's title appears at the start of its paragraph.
# Chapter/Section/Article repeat the title; Clause and Point are renumbered
# into the running text ("Khoản 3" is written "3.", "Điểm b" is "b)").
_MARKER_BUILDERS = {
    "Part": lambda n: rf"Phần\s+{re.escape(n)}\b",
    "Chapter": lambda n: rf"Chương\s+{re.escape(n)}\b",
    "Section": lambda n: rf"Mục\s+{re.escape(n)}\b",
    "Subsection": lambda n: rf"Tiểu\s*mục\s+{re.escape(n)}\b",
    "Article": lambda n: rf"Điều\s+{re.escape(n)}\s*[.:\-–]?",
    "Clause": lambda n: rf"{re.escape(n)}\s*[.)\-–]",
    "Point": lambda n: rf"{re.escape(n)}\s*[.)\-–]",
}

# "Điều 12" -> "12", "Điểm b" -> "b". A bare "Điều" (≈37 nodes corpus-wide)
# yields None and is skipped rather than matched to the next thing that looks
# close.
_TITLE_NUMBER = re.compile(
    r"^(?:Phần|Chương|Mục|Tiểu\s*mục|Điều|Khoản|Điểm)\s+(\S+)\s*$", re.IGNORECASE
)


@dataclass(frozen=True, slots=True)
class Paragraph:
    node_id: str | None
    text: str


@dataclass(slots=True)
class Alignment:
    """Result of attaching text to one document's tree."""

    method: str  # "id" | "marker" | "id+marker"
    texts: dict[str, str] = field(default_factory=dict)
    total_nodes: int = 0

    @property
    def coverage(self) -> float:
        return len(self.texts) / self.total_nodes if self.total_nodes else 0.0


class _Paragraphs(HTMLParser):
    """Flattens the body into paragraph-sized chunks, keeping any `id`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[Paragraph] = []
        self._buf: list[str] = []
        self._id: str | None = None
        self._open = False
        self._muted = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._muted += 1
        elif tag in _BLOCK_TAGS:
            self._flush()
            self._id = dict(attrs).get("id")
            self._open = True
        elif tag in ("br", "tr"):
            self._buf.append(" ")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._muted = max(0, self._muted - 1)
        elif tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if not self._muted:
            self._buf.append(data)

    def _flush(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
        # \xa0 survives the \s+ collapse on some Python builds; NFC folds it.
        text = unicodedata.normalize("NFC", text).replace("\xa0", " ").strip()
        if self._open and (text or self._id):
            self.out.append(Paragraph(self._id, text))
        self._buf.clear()
        self._id = None
        self._open = False

    def close(self):  # noqa: D102
        self._flush()
        super().close()


def parse_paragraphs(html: str) -> list[Paragraph]:
    p = _Paragraphs()
    p.feed(html)
    p.close()
    return p.out


def flatten(tree: list[dict]) -> list[dict]:
    """Tree nodes in document order, each carrying `parent_id`."""
    out: list[dict] = []

    def walk(nodes: list[dict], parent: str | None) -> None:
        for n in nodes:
            out.append({**n, "parent_id": parent})
            walk(n.get("children") or [], n["id"])

    walk(tree, None)
    return out


def align_by_id(
    nodes: list[dict], paragraphs: list[Paragraph], stops: frozenset[int] = frozenset()
) -> dict[str, str]:
    """Exact join. Untagged paragraphs continue the node that precedes them.

    `stops` are paragraph indices another method already assigned to a node;
    a continuation ends there instead of absorbing that node's text.
    """
    known = {n["id"] for n in nodes}
    texts: dict[str, str] = {}
    current: str | None = None
    for index, para in enumerate(paragraphs):
        if para.node_id in known:
            current = para.node_id
            texts[current] = para.text
        elif index in stops:
            current = None
        elif current and para.text and para.node_id is None:
            texts[current] = f"{texts[current]} {para.text}".strip()
        elif para.node_id is not None:
            current = None  # a tagged paragraph we don't hold ends the run
    return {k: v for k, v in texts.items() if v}


def _marker(node: dict) -> re.Pattern[str] | None:
    build = _MARKER_BUILDERS.get(node.get("level") or "")
    match = _TITLE_NUMBER.match(unicodedata.normalize("NFC", node.get("title") or ""))
    if not build or not match:
        return None
    return re.compile(rf"^{build(match.group(1))}", re.IGNORECASE)


def align_by_marker(
    nodes: list[dict],
    paragraphs: list[Paragraph],
    anchors: dict[str, int] | None = None,
) -> dict[str, str]:
    """Sequential match for id-less HTML; see `marker_matches`."""
    return {nid: paragraphs[i].text for nid, i in marker_matches(nodes, paragraphs, anchors).items()}


def marker_matches(
    nodes: list[dict],
    paragraphs: list[Paragraph],
    anchors: dict[str, int] | None = None,
) -> dict[str, int]:
    """Node id -> index of the paragraph its marker matched.

    Both sides are already in document order, so this only ever scans forward:
    a node whose marker never turns up is skipped, and the search resumes for
    the next node from the same place rather than sliding the whole document.

    `anchors` (node id -> paragraph index) are nodes already placed by an exact
    id join. They are not re-matched; they move the cursor, and a node between
    two anchors is only searched for before the next one — so a missing "1."
    can never be taken from a later article whose paragraphs are tagged.
    """
    anchors = anchors or {}
    limits = [len(paragraphs)] * len(nodes)
    next_anchor = len(paragraphs)
    for i in range(len(nodes) - 1, -1, -1):
        limits[i] = next_anchor
        if nodes[i]["id"] in anchors:
            next_anchor = anchors[nodes[i]["id"]]

    matches: dict[str, int] = {}
    cursor = 0
    for i, node in enumerate(nodes):
        if node["id"] in anchors:
            cursor = anchors[node["id"]] + 1
            continue
        pattern = _marker(node)
        if pattern is None:
            continue
        for j in range(cursor, limits[i]):
            if pattern.match(paragraphs[j].text):
                matches[node["id"]] = j
                cursor = j + 1
                break
    return matches


def align(tree: list[dict], html: str) -> Alignment:
    """Attach `html`'s text to `tree`, picking the method the document allows.

    The id join is used only when some paragraph id really is a tree node id:
    several hundred bodies tag paragraphs with ids of their own, and choosing
    the join on "any id at all" wrote those out with zero nodes. When the join
    covers less than `REVIEW_THRESHOLD` of the tree, markers fill the nodes it
    missed, anchored between the joined ones. A joined node keeps its tagged
    paragraph; its untagged continuation now stops at a paragraph a marker gave
    to another node, instead of swallowing the next article whole.
    """
    nodes = flatten(tree)
    paragraphs = parse_paragraphs(html)
    known = {n["id"] for n in nodes}
    if not any(p.node_id in known for p in paragraphs):
        return Alignment("marker", align_by_marker(nodes, paragraphs), len(nodes))

    texts = align_by_id(nodes, paragraphs)
    if len(texts) >= REVIEW_THRESHOLD * len(nodes):
        return Alignment("id", texts, len(nodes))
    anchors: dict[str, int] = {}
    for index, para in enumerate(paragraphs):
        if para.node_id in texts:
            anchors.setdefault(para.node_id, index)
    matches = marker_matches(nodes, paragraphs, anchors)
    if not matches:
        return Alignment("id", texts, len(nodes))
    joined = align_by_id(nodes, paragraphs, stops=frozenset(matches.values()))
    filled = {nid: paragraphs[i].text for nid, i in matches.items()}
    return Alignment("id+marker", {**filled, **joined}, len(nodes))
