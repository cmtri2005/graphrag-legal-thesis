#!/usr/bin/env python3
"""L2 (master plan P3.11) — provision-level events read from acting documents.

For every document that acts on another through a genealogy edge, read its
own text for "Bãi bỏ khoản 2 Điều 11 Nghị định số X" / "Điều 1. Sửa đổi …
Nghị định số X như sau: 1. Sửa đổi khoản 2 Điều 5 …" (see
`extraction.provision_ops`), then resolve the cited number and locator
through the same `TargetResolver` the expiry strings use. Nothing is guessed:
an unresolved or ambiguous reference is written with its code, not dropped.

Each row is an event in the store of docs/plans/active/l2-event-store.md: a
stable `id`, and a `status` (`EventStatus`) that decides whether P3.15 may
apply it:

* `verified` — the portal's own `expiryProvisions` lists the provision this
  ending operation hits (`expiry_targets.jsonl`, resolved exactly);
* `auto_accepted` — resolved, dated and carrying what `EventApplier` needs:
  nothing for a repeal, the new text per node for an amendment
  (`extraction.wording`);
* `needs_review` — everything else, with `status_reason`.

Reads `data/raw`, `data/edges.jsonl`, `data/expiry_targets.jsonl` and the index
from `build_store.py --with-subtrees` (derived Khoản/Điểm must be resolvable).
Writes `data/derived/provision_events.jsonl`, one line per (mention, locator).
Offline, a pure function of `data/` — delete and re-run.

Usage:
    python scripts/pipeline/extract_provision_events.py
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from datetime import date

from vilexgraph.build.extraction import TargetReference, TargetResolver, TargetScope
from vilexgraph.build.extraction.provision_ops import extract_mentions, normalize_number, title_document
from vilexgraph.build.extraction.wording import apply_phrase, fit, parse_items, phrase_edits, wording_blocks
from vilexgraph.build.index import TemporalIndex
from vilexgraph.build.ingest import document_number
from vilexgraph.build.provisions.text import parse_paragraphs
from vilexgraph.build.storage.documents import DocumentStore
from vilexgraph.build.temporal.ids import make_document_id, make_event_id, make_provision_id


def evidence_of(mention, paragraphs: list[str], limit: int = 400) -> str:
    """The sentence this event was read from, with its quoted runs intact.

    `extract_mentions` masks every curly-quoted run as «Q» so that quoted new
    wording is never read as an instruction. For a phrase edit the quoted runs
    *are* the payload ("thay thế cụm từ A bằng cụm từ B"), so the masked
    sentence proves nothing and the original paragraph stands as evidence.
    The masked text still keys the event id, which must not move.
    """
    text = mention.evidence or ""
    if "«Q»" not in text:
        return text
    return " ".join(paragraphs[mention.paragraph].split())[:limit]


# Operations that end the version the portal calls expired (see measure_provision_events.py).
ENDING = {"repeal", "replace", "amend", "correct", "suspend"}
TEXT_OPS = {"amend", "replace", "correct"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--index", type=Path, default=None, help="default: <data>/temporal.sqlite")
    args = parser.parse_args()
    data = args.data
    store = DocumentStore(data)
    index = TemporalIndex(args.index or data / "temporal.sqlite")
    resolver = TargetResolver(index)
    by_number: dict[str, list[str]] = collections.defaultdict(list)
    for doc in index.documents():
        if doc.number:
            by_number[normalize_number(doc.number)].append(doc.id)

    stats_title_actors: set[str] = set()   # read because of their title, not of a portal relation
    targets_of: dict[str, set[str]] = collections.defaultdict(set)
    actors: dict[str, str] = {}  # domain id -> portal id, which names the file under data/raw
    for line in (data / "edges.jsonl").read_text(encoding="utf-8").splitlines():
        edge = json.loads(line)
        source = make_document_id(edge["source_id"])
        targets_of[source].add(make_document_id(edge["target_id"]))
        if edge["group"] == "genealogy":
            actors[source] = edge["source_id"]

    # Only a central normative act can amend one (ADR 0002 scope): a provincial
    # resolution or a consolidated text that cites "Điều 4 Nghị định số X" is
    # quoting it, not changing it.
    central_rows = [row for row in map(json.loads, (data / "derived/eligibility.jsonl").read_text(encoding="utf-8").splitlines())
                    if row.get("doc_class") == "qppl"]
    central = {make_document_id(row["doc_id"]) for row in central_rows}
    # The portal's Lược đồ misses some amending acts altogether: NĐ 115/2016/NĐ-CP, titled
    # "Sửa đổi, bổ sung một số điều của Nghị định số 163/2013/NĐ-CP", lists only "Căn cứ ban
    # hành", so none of its amendments were read (D5 §5.6). A title that opens on the act
    # of amending is evidence enough to read the body: 562 such documents (20/10/2026).
    for row in central_rows:
        doc_id = make_document_id(row["doc_id"])
        if doc_id not in actors and (doc := index.document(doc_id)) and _ACTS_ON_ANOTHER.search(doc.title or ""):
            actors[doc_id] = row["doc_id"]
            stats_title_actors.add(doc_id)

    gold: set[tuple[str, str]] = set()
    for line in (data / "expiry_targets.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("code") == "resolved_exact":
            gold.update(
                (make_document_id(row["doc_id"]), make_provision_id(pid))
                for pid in row.get("provision_ids", [])
            )
    tree_cache: dict[str, dict] = {}
    text_cache: dict[str, dict[str, str]] = {}
    subtree_of = {make_document_id(i): i for i in store.ids("derived/subtrees")}

    def provision(doc_id: str, pid: str):
        if doc_id not in tree_cache:
            tree_cache.clear()  # ponytail: one document at a time is enough, rows come grouped by actor
            tree_cache[doc_id] = {p.id: p for p in index.document_order(doc_id)}
        return tree_cache[doc_id].get(pid)

    def node_text(doc_id: str, pid: str) -> str | None:
        """Current text of one node: the index for tree nodes, the T5 split for the rest."""
        if doc_id not in text_cache:
            text_cache.clear()
            derived = {}
            if doc_id in subtree_of:
                derived = {make_provision_id(n["id"]): n.get("text")
                           for n in store.load("derived/subtrees", subtree_of[doc_id])["nodes"]}
            text_cache[doc_id] = derived
        stored = index.versions_of(pid)
        return stored[0].text if stored else text_cache[doc_id].get(pid)

    def phrase_updates(doc_id: str, pid: str, edits: list[tuple[str, str]]) -> dict[str, str]:
        """Apply the edits to the target and every descendant that carries the phrase.

        "thay thế cụm từ A tại Điều 7" reaches the whole article, not only its
        heading, so the subtree is searched — but a node whose text does not
        contain A verbatim is left alone rather than rewritten on a hunch.
        """
        root = provision(doc_id, pid)
        if root is None:
            return {}
        out: dict[str, str] = {}
        for node in (root, *index.descendants_of(pid)):
            current = node_text(doc_id, node.id)
            if not current:
                continue
            new_text = apply_phrase(current, edits)
            if new_text is not None:
                out[node.id] = new_text
        return out

    stats: collections.Counter[str] = collections.Counter()
    rows: collections.Counter[str] = collections.Counter()
    skipped_mismatch: list[str] = []
    seen: dict[str, int] = {}  # event id -> hash of its row
    out_path = data / "derived" / "provision_events.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out:
        for actor_id, portal_id in sorted(actors.items()):
            if actor_id not in central:
                stats["actor out of scope"] += 1
                continue
            raw = store.load("raw", portal_id)
            html = ((raw or {}).get("documentContent") or {}).get("content") or ""
            if not html:
                stats["actor without body"] += 1
                continue
            paragraphs = [p.text for p in parse_paragraphs(html)]
            if not _body_is_own(paragraphs, raw.get("docNum") or ""):
                skipped_mismatch.append(actor_id)
                continue
            stats["actors read"] += 1
            actor = index.document(actor_id)
            effective_on = actor.effective_from.isoformat() if actor and actor.effective_from else None
            effect_dates = effective_clause_dates(paragraphs)
            mentions = extract_mentions(paragraphs, title_document(raw.get("title") or ""))
            blocks = wording_blocks(paragraphs)
            quoted = {j for k, b in blocks.items() for j in range(b.start, b.end + 1) if j != k}
            deferred = deferred_dates(paragraphs, quoted)
            positions = paragraph_positions(paragraphs, quoted) if deferred else []
            for n, mention in enumerate(mentions):
                on = effective_on
                if deferred:
                    article, clause = positions[mention.paragraph]
                    later = deferred.get((article, clause)) or deferred.get((article, None))
                    if later:
                        on = later.isoformat()
                        stats["deferred effective date"] += 1
                candidates = [c for c in by_number.get(normalize_number(mention.document_number), []) if c != actor_id]
                narrowed = [c for c in candidates if c in targets_of[actor_id]]
                candidates = narrowed or candidates
                base = {
                    "actor_id": actor_id,
                    "actor_number": document_number(raw.get("docNum")),
                    "operation": mention.operation.value,
                    "method": mention.method,
                    "document_number": mention.document_number,
                    "candidate_document_ids": candidates,
                    "effective_on": on,
                    "evidence": evidence_of(mention, paragraphs),
                }
                references = (
                    [TargetReference(f"{actor_id}:{n}", mention.evidence or "?", TargetScope.DOCUMENT,
                                     document_reference=mention.document_number)]
                    if not mention.locators else
                    [TargetReference(f"{actor_id}:{n}:{k}", mention.evidence or "?", TargetScope.SUBTREE,
                                     document_reference=mention.document_number, locator=loc)
                     for k, loc in enumerate(mention.locators)]
                )
                for ref in references:
                    row = dict(base, locator=[[p.level.value, p.label] for p in ref.locator.parts] if ref.locator else None)
                    if not candidates:
                        row.update(code="document_not_in_corpus", target_document_id=None,
                                   target_provision_id=None, affected_provision_ids=[])
                    else:
                        res = resolver.resolve(ref, candidates)
                        target = res.target
                        row.update(
                            code=res.code.value,
                            target_document_id=target.target_document_id,
                            target_provision_id=target.target_provision_ids[0] if target.target_provision_ids else None,
                            affected_provision_ids=list(target.affected_provision_ids),
                        )
                    updates = None
                    edits = []
                    phrase_missing = False
                    block = blocks.get(mention.paragraph)
                    if row["operation"] in TEXT_OPS and block and row["target_provision_id"]:
                        items = parse_items(block.lines)
                        root = provision(row["target_document_id"], row["target_provision_id"])
                        if items and root:
                            updates = fit(items, {p.level: p.label for p in ref.locator.parts}, root,
                                          index.descendants_of(root.id))
                    # B4: a phrase edit carries its payload in the instruction itself, so
                    # it needs the original paragraph — `mention.evidence` has already had
                    # its curly-quoted runs masked out.
                    if not updates and row["operation"] in TEXT_OPS and row["target_provision_id"]:
                        edits = phrase_edits(paragraphs[mention.paragraph])
                        if edits:
                            updates = phrase_updates(row["target_document_id"],
                                                     row["target_provision_id"], edits)
                            phrase_missing = not updates
                    row["text_updates"] = [{"target_provision_id": k, "new_text": v} for k, v in (updates or {}).items()]
                    if edits:
                        # resolved here against the as-published text; build_versions
                        # re-resolves them against the text in force on effective_on —
                        # also when they miss here, since an earlier amendment may be
                        # what put the phrase in (phrase_not_found, plan phase-4 J3)
                        row["phrase_edits"] = [list(edit) for edit in edits]
                    scope = None
                    if (row["locator"] is None and row["code"] == "resolved_document" and row["target_document_id"]
                            and row["operation"] in ("repeal", "replace")):
                        target = index.document(row["target_document_id"])
                        scope = document_scope_verdict(paragraphs, row["evidence"], row["effective_on"],
                                                       target.effective_to if target else date.min, len(candidates), effect_dates)
                    row["status"], row["status_reason"] = _status(row, block is not None, gold,
                                                                  phrase_missing=phrase_missing, scope=scope)
                    row["id"] = make_event_id(
                        actor_id, row["operation"],
                        [row["target_provision_id"]] if row["target_provision_id"] else [],
                        date.fromisoformat(on) if on else None,
                        target_document_id=row["target_document_id"],
                        evidence_text=f"{mention.evidence}|{row['locator']}|{mention.document_number}",
                    )
                    fingerprint = hash(json.dumps(row, sort_keys=True))
                    if row["id"] in seen:
                        if seen[row["id"]] != fingerprint:  # an id must never merge two events
                            raise ValueError(f"two different events share the id {row['id']}")
                        stats["duplicate mention"] += 1  # the same sentence, repeated in the body
                        continue
                    seen[row["id"]] = fingerprint
                    stats[f"status {row['status']:<13} {row['status_reason'] or ''}"] += 1
                    rows[f"{row['operation']:<10} {'document' if ref.locator is None else 'provision':<9} {row['code']}"] += 1
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"{stats['actors read']:,} acting documents read -> {out_path}")
    print(f"  skipped: {stats['actor out of scope']:,} not central normative, {stats['actor without body']:,} without body, "
          f"{len(skipped_mismatch):,} whose body carries another document's number: {skipped_mismatch[:12]}")
    print(f"  {stats['duplicate mention']:,} repeated mentions written once")
    print(f"  {len(stats_title_actors):,} acting documents read because of their title (no portal relation)")
    print(f"  {stats['deferred effective date']:,} mentions dated by a part of the act starting later")
    for key, count in sorted(rows.items()):
        print(f"  {count:>7,}  {key}")
    for key, count in sorted((k, v) for k, v in stats.items() if k.startswith("status ")):
        print(f"  {count:>7,}  {key}")


def _status(row: dict, quoted: bool, gold: set[tuple[str, str]],
            *, phrase_missing: bool = False,
            scope: tuple[str, str | None] | None = None) -> tuple[str, str | None]:
    """(EventStatus value, reason) — the gate P3.15 reads before applying.

    `scope` is `document_scope_verdict` for an event on the whole document: without one,
    the document's own effTo is taken to date it.
    """
    op = row["operation"]
    if not row["code"].startswith("resolved"):
        return "needs_review", row["code"]
    if row["locator"] is None:
        return scope or ("needs_review", "document_scope")
    if row["effective_on"] is None:
        return "needs_review", "missing_effective_date"
    if op in TEXT_OPS and not row["text_updates"]:
        if phrase_missing:
            # The instruction was read, but the phrase it replaces is not in the
            # target verbatim: the wrong node, or text the corpus never got.
            return "needs_review", "phrase_not_found"
        return "needs_review", "structure_mismatch" if quoted else "missing_resulting_text"
    if op not in ENDING or op == "suspend":
        return "needs_review", f"{op}_not_materializable"
    if op == "repeal" and (_PARTIAL_REPEAL.search(row["evidence"] or "")
                           or partial_branch(row["evidence"] or "", row["locator"])):
        # deleting a phrase, a row of a table or a dash is not ending the node (D5 §5)
        return "needs_review", "partial_repeal"
    if any((row["target_document_id"], pid) in gold for pid in row["affected_provision_ids"]):
        return "verified", None
    return "auto_accepted", None


# "Bãi bỏ nội dung sau tại khoản 3", "bãi bỏ đoạn “…” tại điểm d", "bãi bỏ số thứ tự 19 tại Biểu
# phí", "bãi bỏ tiết c điểm 3.2": only part of the located node goes. "Bãi bỏ nội dung (quy định)
# tại khoản 5" and "bãi bỏ từ khoản 1 đến khoản 11" still end whole nodes.
_PARTIAL_REPEAL = re.compile(
    r"(?i)bãi bỏ\s+(?:các\s+)?(?:nội dung\s+(?:sau|dưới đây|về|liên quan)|quy định\s+(?!tại)"
    r"|(?:nội dung\s+(?:quy định\s+)?tại\s+)?(?:đoạn|câu|cụm từ|chữ|dòng|số thứ tự|tiết|gạch đầu dòng|ý)\b"
    r"|từ\s+(?!khoản|điều|điểm|chương|mục))")
# H5 L1 (10/11/2026). A list item loses its verb: "Các nội dung liên quan đến … tại Điều 1, Điều 2",
# "gạch đầu dòng thứ hai điểm d khoản 3 Điều 20", "“…” tại khoản 9 Điều 4". Such a sentence is read
# locator by locator: "Khoản 4 Điều 19 và quy định “…” tại Khoản 3 Điều 19" ends khoản 4 and only
# trims khoản 3. A qualifier written in front of its locator ("gạch đầu dòng thứ 3 điểm a khoản 5
# Điều 5b", "đoạn 3 khoản 4 Điều 5") trims the next locator named; a lead-in ("Các nội dung liên
# quan đến … tại", "“…” tại") trims every locator named after it.
_ATTACHED = re.compile(r"(?i)gạch đầu dòng|\bđoạn\s+(?:\d|thứ)|\bcụm từ\b")
_LEAD_IN = re.compile(r"(?i)^\W*(?:\d+\s*[.)]\s*)?(?:các\s+)?nội dung\s+(?:sau|dưới đây|về|liên quan)|[“\"'‘][^”\"’]*[”\"’]\s*tại\s")
_LETTERS = r"[a-zđ](?:\s*(?:,|và)\s*(?:điểm\s+|tiết\s+)?[a-zđ]\b)*"
_NUMBERS = r"\d+(?:\s*(?:,|và)\s*(?:khoản\s+)?\d+\b)*"
_BRANCH_LOCATOR = re.compile(
    rf"(?i)(?:(?:điểm|tiết)\s+({_LETTERS})\s*,?\s*)?(?:khoản\s+({_NUMBERS})\s*,?\s*)?điều\s+(\d+[a-zđ]?)")
_LEVELS = {"Article": 2, "Clause": 1, "Point": 0}


def _mentions(text: str, offset: int = 0):
    """((point, clause, article) as lower-case strings or None, start) for every locator in `text`."""
    for m in _BRANCH_LOCATOR.finditer(text):
        points = re.findall(r"(?<![\wđ])[a-zđ](?![\wđ])", (m.group(1) or "").lower()) or [None]
        clauses = re.findall(r"\d+", m.group(2) or "") or [None]
        for point in points:
            for clause in clauses:
                yield (point, clause, m.group(3).lower()), offset + m.start()


def partial_branch(evidence: str, locator) -> bool:
    """True when the sentence trims only part of the node `locator` (a list of [level, label])."""
    if not locator or any(level not in _LEVELS for level, _ in locator):
        return False
    want = [None, None, None]
    for level, label in locator:
        want[_LEVELS[level]] = str(label).lower()
    want = tuple(want)
    for sentence in evidence.split(";"):
        named = list(_mentions(sentence))
        for q in _ATTACHED.finditer(sentence):
            nxt = min((start for _, start in named if start >= q.end()), default=None)
            if nxt is not None and any(key == want for key, start in named if start == nxt):
                return True
        lead = _LEAD_IN.search(sentence)
        if lead and any(key == want for key, start in named if start >= lead.end()):
            return True
    return False


# H5 L2 (10/11/2026). vbpl leaves `effTo` empty on some documents a later act repealed whole
# (TT 15/2012/TT-BNV by TT 12/2023/TT-BNV). The event is applied when the lead-in of the list in the
# acting document — not kept in `evidence` — says the whole text goes, and the date is the act's own.
_DOC_NAME = re.compile(r"(?i)^\W*(?:thông tư(?: liên tịch)?|nghị định|luật|bộ luật|pháp lệnh|quyết định|nghị quyết)\s+(?:số\s+)?\d")
_REPEAL_VERB = re.compile(r"(?i)\b(?:bãi bỏ|thay thế)\b")
_WHOLE_LEAD = re.compile(
    r"(?i)bãi bỏ toàn bộ|\bthay thế\b"
    r"|bãi bỏ\s+(?:các\s+)?(?:thông tư(?: liên tịch)?|nghị định|quyết định|nghị quyết|văn bản|pháp lệnh|luật|chỉ thị)\b")
_SELF_ENDS = re.compile(r"(?i)hết hiệu lực(?: thi hành)?\s+(?:kể\s+)?từ ngày\s+\S+(?:\s+\S+)?\s+này\s+có hiệu lực")
_PART_LEAD = re.compile(r"(?i)quy định\s+(?:về|vế)\b|nội dung|một phần|một số điều|\bkhoản\b|\bđiểm\b")
_NOT_WHOLE = re.compile(r"(?i)các quy định|quy định\s+(?:về|vế)\b|nội dung|một phần|một số quy định|một số điều|\bkhoản\b|\bđiểm\b|\btrừ\b")
_FIRST_DOC = re.compile(
    r"(?i)(?:thông tư|nghị định|quyết định|nghị quyết|pháp lệnh|luật|bộ luật)(?=\s+(?:liên tịch\s+)?(?:số\s+)?\d)")
_LIST_NUMBER = re.compile(r"^\s*(?:\d+\s*[.)]|[a-zđ]\)|[-–•])\s*")
_ARTICLE_LINE = re.compile(r"(?i)^\s*Điều\s+\d+[a-z]?\s*[.:\-–]")
_DATE_IN_TEXT = re.compile(r"(?i)(\d{1,2})\s*(?:tháng|/)\s*(\d{1,2})\s*(?:năm|/)\s*(\d{4})")


def _flat(text: str) -> str:
    return " ".join((text or "").split())


def lead_in(paragraphs: list[str], evidence: str) -> tuple[str, bool] | None:
    """(the words that say what happens to the listed documents, whether they stand in the
    same paragraph as the mention), or None when no such words are found."""
    key = _flat(evidence)[:60]
    flat = [_flat(p) for p in paragraphs]
    idx = next((i for i, p in enumerate(flat) if key and key in p), None)
    if idx is None:
        return None
    para = flat[idx]
    head = _LIST_NUMBER.sub("", para[:para.find(key)])
    if _REPEAL_VERB.search(head):
        first = _FIRST_DOC.search(head)  # earlier items of the same paragraph are not part of the lead-in
        return (head[:first.end()] if first else head), True
    if _SELF_ENDS.search(para[para.find(key):]):
        return "hết hiệu lực", True
    if head.strip():
        return None
    for j in range(idx - 1, max(idx - 150, -1), -1):  # list intro: "Bãi bỏ các Thông tư sau:"
        text = flat[j]
        if _REPEAL_VERB.search(text) or "hết hiệu lực" in text:
            if text.rstrip().endswith(":") or re.search(r"(?i)sau đây|sau:|dưới đây|cụ thể", text):
                return _LIST_NUMBER.sub("", text), False
        if _ARTICLE_LINE.match(text):
            return None
    return None


def document_scope_verdict(paragraphs: list[str], evidence: str, effective_on: str | None,
                           target_effective_to, n_candidates: int, effective_dates: set[str]):
    """(status, reason) for a repeal/replace of a whole document whose `effTo` the portal left empty,
    or None to keep the default `needs_review/document_scope`."""
    if n_candidates != 1 or not effective_on or target_effective_to is not None or not _DOC_NAME.search(evidence or ""):
        return None
    found = lead_in(paragraphs, evidence)
    if found is None:
        return None
    lead, same_paragraph = found
    if _NOT_WHOLE.search(lead):
        return ("needs_review", "partial_repeal") if same_paragraph and _PART_LEAD.search(lead) else None
    if not (lead == "hết hiệu lực" or _WHOLE_LEAD.search(lead)):
        return None
    on = date.fromisoformat(effective_on)
    # the act's own date only: a clause dated otherwise or counted from the Công báo stays with a person
    if any(d != on for d in (_to_date(m) for m in _DATE_IN_TEXT.finditer(lead))):
        return None
    if any(d != effective_on for d in effective_dates) or any(re.search(r"(?i)hiệu lực[^.]*Công báo", p) for p in paragraphs):
        return None
    return "auto_accepted", None


def _to_date(match) -> date | None:
    try:
        return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
    except ValueError:
        return None


_EFFECT_DATE = re.compile(
    r"(?i)hiệu lực(?: thi hành)?(?:\s+kể)?\s+từ ngày\s+(\d{1,2})\s*(?:tháng|/)\s*(\d{1,2})\s*(?:năm|/)\s*(\d{4})")


def effective_clause_dates(paragraphs: list[str]) -> set[str]:
    """Every date the act itself says it takes effect on ("có hiệu lực từ ngày …"), ISO."""
    out = set()
    for p in paragraphs:
        out.update(d.isoformat() for m in _EFFECT_DATE.finditer(p) if (d := _to_date(m)))
    return out


_SELF = r"(?:Bộ luật|Luật|Pháp lệnh|Nghị định|Nghị quyết|Thông tư(?: liên tịch)?|Quyết định)\s+này"
# "Các khoản 4, khoản 5 và khoản 12 Điều 1 Thông tư này có hiệu lực thi hành từ ngày 01 tháng 01
# năm 2024": part of an act starting later than the act (TT 17/2023/TT-BGTVT, D5 §5.1)
# The sentence must open on the provisions themselves: "Thẩm quyền … quy định tại Điều 1" or
# "… từ ngày 01/6/2022 đối với thủ tục …" dates only part of what those provisions say.
_DEFERRED = re.compile(
    r"(?i)^(?:\d+\s*\.\s*)?(?:riêng\s+)?(?:(?:các\s+)?(?:quy định|nội dung quy định)\s+tại\s+)?"
    rf"((?:các\s+)?(?:khoản|điều|điểm)\s+[^.;]*?)\s+(?:của\s+)?{_SELF}\s+"
    r"(?:sẽ\s+)?có hiệu lực(?: thi hành)?(?: kể)? từ ngày (\d{1,2})\s*(?:tháng|/)\s*(\d{1,2})\s*(?:năm|/)\s*(\d{4})"
    r"(?!\s*,?\s*đối với)")
_RANGE = re.compile(r"(?i)từ\s+Điều\s+(\d+)\s+đến\s+Điều\s+(\d+)")
_PART = re.compile(r"(?i)(khoản|điều|điểm)?\s*\b(\d+[a-zđ]?)\b")
_ARTICLE_HEAD = re.compile(r"(?i)^Điều\s+(\d+[a-zđ]?)\s*[.:\-–]")
_CLAUSE_HEAD = re.compile(r"^(\d+)\s*\.\s")


def deferred_dates(paragraphs: list[str], quoted: set[int]) -> dict[tuple[str, str | None], date]:
    """(Điều, khoản or None for the whole Điều) of the act -> the later date it takes effect on.

    Read only outside quoted wording, where "Khoản 2 Điều 24 Thông tư này có hiệu lực…"
    belongs to the act being amended. A sentence naming an Điểm is skipped: a date for
    part of a khoản cannot be told apart at khoản level, so the act's date stays.
    """
    out: dict[tuple[str, str | None], date] = {}
    for i, text in enumerate(paragraphs):
        if i in quoted:
            continue
        for sentence in re.split(r"(?<=[.;])\s+", text):
            m = _DEFERRED.match(sentence.strip())
            if not m or re.search(r"(?i)\bđiểm\b", m.group(1)):
                continue
            try:
                when = date(int(m[4]), int(m[3]), int(m[2]))
            except ValueError:
                continue
            subject = _RANGE.sub(lambda r: "Điều " + ", ".join(
                str(n) for n in range(int(r[1]), int(r[2]) + 1)), m.group(1))
            pending, kind = [], None
            for word, number in _PART.findall(subject):
                kind = (word or kind or "").lower()
                if kind == "khoản":
                    pending.append(number)
                elif kind == "điều":
                    for clause in pending or [None]:
                        out[(number, clause)] = when
                    pending = []
    return out


def paragraph_positions(paragraphs: list[str], quoted: set[int]) -> list[tuple[str | None, str | None]]:
    """(Điều, khoản) of the act each paragraph sits in; quoted wording keeps its instruction's."""
    article = clause = None
    out = []
    for i, text in enumerate(paragraphs):
        if i not in quoted:
            if m := _ARTICLE_HEAD.match(text.strip()):
                article, clause = m[1], None
            elif m := _CLAUSE_HEAD.match(text.strip()):
                clause = m[1]
        out.append((article, clause))
    return out


_ACTS_ON_ANOTHER = re.compile(
    r"(?i)^(?:Bộ luật|Luật|Pháp lệnh|Nghị định|Nghị quyết|Thông tư(?: liên tịch)?|Quyết định|Chỉ thị|Sắc lệnh)"
    r"\s+(?:số\s*:?\s*)?\S+\s+(?:về việc\s+|về\s+)?(?:sửa đổi|bổ sung|bãi bỏ|thay thế|đính chính|ngưng hiệu lực|hủy bỏ|huỷ bỏ)")


_BODY_NUMBER = re.compile(r"Số\s*:?\s*(\d[^\s,;]*(?:\s?[/\-]\s?[^\s,;]+)*)")


def _body_is_own(paragraphs: list[str], doc_num: str) -> bool:
    """False when the "Số: …" header in the body names a different document.

    The portal occasionally serves another document's body under an id (e.g.
    26/2025/QĐ-TTg carrying a joint resolution amending 72/2025/NQLT); every
    event read from it would be dated by the wrong act. No header: trust it.
    """
    for text in paragraphs[:8]:
        m = _BODY_NUMBER.search(text)
        if m:
            body, own = normalize_number(m.group(1)), normalize_number(doc_num)
            return body == own or body.startswith(own) or own.startswith(body)
    return True


if __name__ == "__main__":
    main()
