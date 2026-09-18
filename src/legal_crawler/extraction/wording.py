"""L2 — the new wording an amending instruction quotes, fitted onto the target tree.

"1. Sửa đổi, bổ sung điểm a, điểm b khoản 4 Điều 3 như sau:" is followed by
the provision as it now reads, between quotes:

    "4. Đơn vị thực hiện dán tem điện tử
    a) Doanh nghiệp, tổ chức nhập khẩu …
    b) Trường hợp doanh nghiệp …".

`EventApplier` needs that text per node, because a node's stored text is its
own paragraph only (the Điều its heading, the Khoản its lead, each Điểm its
own node). So the block is cut at its markers into a small Điều > Khoản > Điểm
tree and laid over the target's subtree. It is accepted only when every label
lines up; a block that adds or drops a Khoản changes the structure, which is an
insertion or a repeal, not a text update, and is left for review.

Only quoted blocks are read. Unquoted wording cannot be told apart from the
instruction list that follows a "… như sau:" intro.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from legal_crawler.temporal.models import Provision, ProvisionLevel

_INTRO = re.compile(r"(?i:như sau)\s*:\s*(?P<tail>.*)$")
_OPEN = ("“", '"')
_STRAIGHT_CLOSE = re.compile(r"\"[\s.;,]*$")
_ITEM = re.compile(
    r"^(?:(?P<Article>Điều\s+\d+[a-zđ]?)(?:\s*[.:\-–]|\s*$)"
    r"|(?P<Clause>\d+[a-zđ]?)\s*\.(?=\s)"
    r"|(?P<Point>[a-zđ])\s*\)"
    r"|(?P<outer>(?:Phần|Chương|Mục)\s+\S+))"
)
_LEVEL_ORDER = {ProvisionLevel.ARTICLE: 0, ProvisionLevel.CLAUSE: 1, ProvisionLevel.POINT: 2}


@dataclass(frozen=True, slots=True)
class Block:
    """A quoted block: paragraphs `start`..`end` (inclusive), quotes stripped."""

    start: int
    end: int
    lines: tuple[str, ...]
    inline_at: int | None = None  # where the quote opens when it shares the instruction's paragraph


def wording_blocks(paragraphs: list[str]) -> dict[int, Block]:
    """Instruction paragraph index -> the quoted wording that its "như sau:" opens."""
    blocks: dict[int, Block] = {}
    i = 0
    while i < len(paragraphs):
        m = _INTRO.search(paragraphs[i])
        tail = m.group("tail") if m else ""
        if m and tail.startswith(_OPEN):
            block = _close(paragraphs, i, tail, inline_at=m.start("tail"))
        elif m and not tail and i + 1 < len(paragraphs) and paragraphs[i + 1].lstrip().startswith(_OPEN):
            block = _close(paragraphs, i + 1, paragraphs[i + 1].strip())
        else:
            block = None
        if block is None:
            i += 1
            continue
        blocks[i] = block
        i = block.end + 1  # a quoted block may itself say "như sau:"; it is text
    return blocks


def _close(paragraphs: list[str], start: int, first: str, inline_at: int | None = None) -> Block | None:
    """Scan to the matching close quote; None when it never cleanly closes."""
    lines: list[str] = []
    if first[0] == "“":
        depth = 0
        for j in range(start, len(paragraphs)):
            text = first if j == start else paragraphs[j].strip()
            for k, ch in enumerate(text):
                if ch == "“":
                    depth += 1
                elif ch == "”":
                    depth -= 1
                    if depth == 0:
                        if text[k + 1:].strip(" .;,"):
                            return None  # "…”; bổ sung …": the instruction goes on, not a block
                        lines.append(text[:k])
                        return _block(start, j, lines, inline_at)
            lines.append(text)
        return None
    # Straight quotes cannot nest: the block closes where the count turns even
    # on a paragraph that ends in a quote, so "thay cụm từ "A" bằng "B"." inside it
    # does not close it.
    count = 0
    for j in range(start, len(paragraphs)):
        text = first if j == start else paragraphs[j].strip()
        count += text.count('"')
        if count % 2 == 0 and _STRAIGHT_CLOSE.search(text):
            lines.append(_STRAIGHT_CLOSE.sub("", text))
            return _block(start, j, lines, inline_at)
        lines.append(text)
    return None


def _block(start: int, end: int, lines: list[str], inline_at: int | None) -> Block:
    lines[0] = lines[0][1:]
    return Block(start, end, tuple(s for s in (line.strip() for line in lines) if s), inline_at)


@dataclass(slots=True)
class Item:
    level: ProvisionLevel | None  # None: a Phần/Chương/Mục heading, never fitted
    label: str
    text: str
    children: list["Item"] = field(default_factory=list)


def parse_items(lines: tuple[str, ...]) -> list[Item] | None:
    """Top-level items of a block; None when text precedes its first marker."""
    roots: list[Item] = []
    stack: list[Item] = []
    for line in lines:
        m = _ITEM.match(line)
        if not m:
            if not stack:
                return None
            stack[-1].text = f"{stack[-1].text} {line}"
            continue
        kind = m.lastgroup
        level = None if kind == "outer" else ProvisionLevel(kind)
        label = m.group(kind).split()[-1]
        item = Item(level, label, line)
        rank = -1 if level is None else _LEVEL_ORDER[level]
        while stack and stack[-1].level is not None and _LEVEL_ORDER[stack[-1].level] >= rank:
            stack.pop()
        (stack[-1].children if stack else roots).append(item)
        stack.append(item)
    return roots


def fit(
    items: list[Item],
    locator: dict[ProvisionLevel, str],
    root: Provision,
    descendants: tuple[Provision, ...],
) -> dict[str, str] | None:
    """Node id -> new text for `root` and its subtree, or None if they do not line up.

    The block item for `root` is the one at the locator's leaf level and label
    whose block ancestors agree with the locator ("điểm a khoản 4": the "a)"
    under "4.", not an "a)" under "5.").
    """
    leaf = max(locator, key=lambda lvl: _LEVEL_ORDER.get(lvl, -1))
    found: list[Item] = []

    def search(nodes: list[Item], path: dict[ProvisionLevel, str]) -> None:
        for node in nodes:
            if node.level is None:
                continue
            here = {**path, node.level: node.label}
            if node.level is leaf and node.label == locator[leaf] and all(
                locator.get(lvl, lab) == lab for lvl, lab in here.items()
            ):
                found.append(node)
            search(node.children, here)

    search(items, {})
    if len(found) != 1:
        return None
    children_of: dict[str, list[Provision]] = {}
    for p in descendants:
        children_of.setdefault(p.parent_id, []).append(p)
    updates: dict[str, str] = {}

    def lay(item: Item, node: Provision) -> bool:
        if node.id not in children_of:
            # A leaf's stored text runs on through whatever it contains
            # (`align_by_id`), so the new one does too.
            updates[node.id] = _flat(item)
            return True
        kids = {(k.level, _label(k.title)): k for k in children_of[node.id]}
        if len(kids) != len(children_of.get(node.id, [])) or set(kids) != {(c.level, c.label) for c in item.children}:
            return False
        if len(item.children) != len(kids):
            return False  # a label repeated inside the block
        updates[node.id] = item.text
        return all(lay(child, kids[(child.level, child.label)]) for child in item.children)

    return updates if lay(found[0], root) else None


def _flat(item: Item) -> str:
    return " ".join([item.text, *(_flat(child) for child in item.children)])


def _label(title: str) -> str:
    return title.split()[-1] if title.split() else ""
