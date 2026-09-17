"""Backfill T5 — Khoản/Điểm the portal's tree leaves out, split from the body.

For 7,620 `expiryProvisions` strings the tree stops at the Điều the string
names a Khoản or Điểm of, while 89.4% of those articles do number their
paragraphs "1.", "2." and "a)", "b)". This reads those markers back out of
the body — deterministically, keeping the words verbatim — and never touches
`data/trees/`: the result is a separate, derived artifact (ADR 0002) that is
only promoted once a hand check reaches the agreed 95%.

Only a leaf is split: an Article with no children gets Clauses (and their
Points), a Clause with no children gets Points. A declared node is never
second-guessed. Rules that make a split refuse rather than guess:

* Clauses must be numbered 1, 2, 3 … without a gap or repeat; Points a, b, c,
  d, đ, e … in the Vietnamese order. Anything else skips that parent.
* A paragraph inside a quotation is text, never a marker: an amending
  article's own "1." and the "2." of the provision it rewrites between “ and ”
  are different things.
* The search for a leaf's paragraphs stops at the next anchored node and at
  any Điều/Chương/Mục/Phần heading, so it cannot run into the next article.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text import Paragraph, align_by_id, flatten, marker_matches, parse_paragraphs

METHOD = "article_text_split"

_CLAUSE = re.compile(r"^(\d{1,3})\s*\.\s+\S")
_POINT = re.compile(r"^([a-zđ])\s*\)\s+\S")
_HEADING = re.compile(r"^(Điều|Chương|Mục|Phần)\s+\S", re.IGNORECASE)
_POINT_ORDER = "abcdđeghiklmnopqrstuvxy"
_QUOTES = "“\"'"


@dataclass(slots=True)
class Split:
    nodes: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    # Text between a split parent's own heading and its first Khoản/Điểm
    # marker ("Học sinh phải có đủ các điều kiện sau:") belongs to the parent,
    # not to Khoản 1 — kept separate from `nodes` so it is never mistaken for
    # clause/point content by a consumer that only expects those two levels.
    preambles: list[dict] = field(default_factory=list)


def anchors_for(nodes: list[dict], paragraphs: list[Paragraph]) -> dict[str, int]:
    """Node id -> paragraph index, from the exact id join, then markers between."""
    known = {n["id"] for n in nodes}
    joined = align_by_id(nodes, paragraphs)
    anchors: dict[str, int] = {}
    for index, para in enumerate(paragraphs):
        if para.node_id in known and para.node_id in joined:
            anchors.setdefault(para.node_id, index)
    return {**marker_matches(nodes, paragraphs, anchors), **anchors}


def _unquoted_flags(paragraphs: list[Paragraph]) -> list[bool]:
    """For each paragraph, whether it starts outside any quotation.

    ponytail: depth follows curly quotes only, which is how vbpl bodies quote
    amended text; a straight quote only marks the paragraph it opens. A body
    that quotes across paragraphs with straight quotes would be split — T5.2's
    hand check is what catches that.
    """
    flags, depth = [], 0
    for para in paragraphs:
        flags.append(depth == 0 and para.text[:1] not in _QUOTES)
        depth = max(0, depth + para.text.count("“") - para.text.count("”"))
    return flags


def _children(parent_id: str, level: str, span: list[Paragraph], unquoted: list[bool]) -> tuple[list[dict], str | None]:
    """Clauses ("Clause") or Points ("Point") directly under one parent."""
    pattern = _CLAUSE if level == "Clause" else _POINT
    starts = [i for i, para in enumerate(span) if unquoted[i] and pattern.match(para.text)]
    if not starts:
        return [], None
    labels = [pattern.match(span[i].text).group(1) for i in starts]
    expected = [str(n) for n in range(1, len(labels) + 1)] if level == "Clause" else list(_POINT_ORDER[: len(labels)])
    if labels != expected:
        return [], f"{level.lower()} numbering {labels[:6]} is not {expected[:6]}"
    children = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(span)
        label = labels[position]
        children.append({
            "id": f"{parent_id}#{'k' + label if level == 'Clause' else label}",
            "parent_id": parent_id,
            "level": level,
            "title": f"Khoản {label}" if level == "Clause" else f"Điểm {label}",
            "span": (start, end),
        })
    return children, None


def split_document(tree: list[dict], html: str) -> Split:
    nodes = flatten(tree)
    paragraphs = parse_paragraphs(html)
    anchors = anchors_for(nodes, paragraphs)
    unquoted = _unquoted_flags(paragraphs)
    order = sorted(anchors.values())
    result = Split()

    def text_of(first: int, last: int, stop: re.Pattern[str] | None) -> str:
        # The marker paragraph plus its continuation, up to the next point marker.
        parts = [paragraphs[first].text]
        for i in range(first + 1, last):
            if stop is not None and unquoted[i] and stop.match(paragraphs[i].text):
                break
            parts.append(paragraphs[i].text)
        return " ".join(p for p in parts if p)

    for node in nodes:
        if node.get("children") or node.get("level") not in {"Article", "Clause"} or node["id"] not in anchors:
            continue
        start = anchors[node["id"]] + 1
        end = next((i for i in order if i >= start), len(paragraphs))
        end = next(
            (i for i in range(start, end) if unquoted[i] and _HEADING.match(paragraphs[i].text)),
            end,
        )
        span, flags = paragraphs[start:end], unquoted[start:end]

        if node["level"] == "Article":
            clauses, reason = _children(node["id"], "Clause", span, flags)
            if reason:
                result.skipped.append({"node_id": node["id"], "reason": reason})
                continue
            first_start = clauses[0]["span"][0] if clauses else 0
            if first_start > 0:
                preamble = text_of(start, start + first_start, None)
                if preamble.strip():
                    result.preambles.append({"parent_id": node["id"], "text": preamble})
            for clause in clauses:
                c_start, c_end = clause.pop("span")
                result.nodes.append({**clause, "text": text_of(start + c_start, start + c_end, _POINT)})
                clause_span, clause_flags = span[c_start + 1:c_end], flags[c_start + 1:c_end]
                points, reason = _children(clause["id"], "Point", clause_span, clause_flags)
                if reason:
                    result.skipped.append({"node_id": clause["id"], "reason": reason})
                    continue
                point_first_start = points[0]["span"][0] if points else 0
                if point_first_start > 0:
                    preamble = text_of(start + c_start + 1, start + c_start + 1 + point_first_start, None)
                    if preamble.strip():
                        result.preambles.append({"parent_id": clause["id"], "text": preamble})
                for point in points:
                    p_start, p_end = point.pop("span")
                    first = start + c_start + 1 + p_start
                    result.nodes.append({**point, "text": text_of(first, start + c_start + 1 + p_end, None)})
        else:
            points, reason = _children(node["id"], "Point", span, flags)
            if reason:
                result.skipped.append({"node_id": node["id"], "reason": reason})
                continue
            first_start = points[0]["span"][0] if points else 0
            if first_start > 0:
                preamble = text_of(start, start + first_start, None)
                if preamble.strip():
                    result.preambles.append({"parent_id": node["id"], "text": preamble})
            for point in points:
                p_start, p_end = point.pop("span")
                result.nodes.append({**point, "text": text_of(start + p_start, start + p_end, None)})
    return result
