"""Turn the crawl in `data/` into the temporal domain objects and store them.

This is the only place that knows vbpl.vn's JSON shape *and* the domain model,
which is what keeps the crawler free of interpretation and the domain free of
the portal's quirks. It is one-way and idempotent: drop the SQLite file and
run it again.

Three facts from `docs/audit_dataset.md` shape what it does, and none of them
may be papered over — each is a silent wrong answer if it is:

* 724 documents publish no `effFrom`. Their provisions are stored with no
  validity interval, so a point-in-time query never returns them, rather than
  being dated by guesswork.
* 103 documents publish an `effTo` that is not after their `effFrom` (29
  earlier, 74 equal — an empty half-open interval). The interval is unusable,
  so the `effTo` is dropped and counted; the text and structure stay. Same
  rule as `data_status.py`: `vocab.status_codes.anchor_problem`.
* 17 documents have a provision tree but no body text. They yield provisions
  and no versions, which is the honest representation of "we know this Điều
  exists and we do not hold its words".
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path

from .index import TemporalIndex
from .storage.documents import DocumentStore
from .vocab.status_codes import EMPTY_INTERVAL, anchor_problem
from .temporal import (
    LegalDocument,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
)

DOCUMENT_URL = "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID="


def _as_date(value: str | None) -> date | None:
    return date.fromisoformat(value[:10]) if value else None


class IngestReport(dict):
    """Counters worth printing; a plain dict so callers can just read it."""

    def bump(self, key: str, by: int = 1) -> None:
        self[key] = self.get(key, 0) + by


def build_document(doc_id: str, raw: dict, report: IngestReport) -> LegalDocument:
    effective_from = _as_date(raw.get("effFrom"))
    effective_to = _as_date(raw.get("effTo"))
    if anchor_problem(raw, date.today()) == EMPTY_INTERVAL:
        # The portal's own data contradicts itself here. Keep the document,
        # lose only the field that cannot be true.
        effective_to = None
        report.bump("effective_to_dropped")
    if not effective_from:
        report.bump("documents_without_effective_from")
    return LegalDocument(
        id=doc_id,
        number=str(raw.get("docNum") or ""),
        title=str(raw.get("title") or ""),
        issued_on=_as_date(raw.get("issueDate")),
        effective_from=effective_from,
        effective_to=effective_to,
        issuer=raw.get("agencyName"),
        rank=(raw.get("docType") or {}).get("name"),
        source_url=f"{DOCUMENT_URL}{doc_id}",
        raw_status_code=(raw.get("effStatus") or {}).get("code"),
    )


def walk_tree(nodes: list[dict], document_id: str) -> Iterator[Provision]:
    """Depth-first, parents before children, which is what the index wants.

    `order_index` is the position in this walk, not the portal's `orderIndex`:
    that field is a signed 16-bit counter and wraps negative past 32,767 nodes
    (30/2004/TT-BTNMT has 21,652 nodes ordered -32,768 upward). The tree's own
    nesting order is the document order, and it cannot overflow.
    """
    position = 0

    def walk(children: list[dict], parent_id: str | None) -> Iterator[Provision]:
        nonlocal position
        for node in children:
            yield Provision(
                id=node["id"],
                document_id=document_id,
                level=ProvisionLevel(node["level"]),
                title=node.get("title") or "",
                parent_id=parent_id,
                order_index=position,
            )
            position += 1
            yield from walk(node.get("children") or [], node["id"])

    yield from walk(nodes, None)


def build_versions(
    provisions: list[Provision], texts: dict[str, dict], document: LegalDocument
) -> list[ProvisionVersion]:
    """One version per provision that has text.

    ponytail: the validity comes from the document's own effective window,
    because the corpus holds only the current consolidated text. Real version
    chains appear once L2 extracts amendment operations — until then every
    chain is length 1, and pretending otherwise would invent history.
    """
    validity = (
        TemporalInterval(document.effective_from, document.effective_to)
        if document.effective_from
        else None
    )
    versions = []
    for provision in provisions:
        text = (texts.get(provision.id) or {}).get("text")
        if not text:
            continue
        versions.append(
            ProvisionVersion(
                id=f"{provision.id}:1",
                provision_id=provision.id,
                ordinal=1,
                text=text,
                validity=validity,
            )
        )
    return versions


def ingest(data_dir: Path, store: TemporalIndex, limit: int | None = None) -> IngestReport:
    source = DocumentStore(data_dir)
    report = IngestReport()
    doc_ids = sorted(source.ids("raw"))
    if limit:
        doc_ids = doc_ids[:limit]

    tree_ids = set(source.ids("trees"))
    text_ids = set(source.ids("provisions"))

    for n, doc_id in enumerate(doc_ids, 1):
        if n % 1000 == 0:
            store.commit()  # an interrupted build keeps what it did
            print(f"  {n:,}/{len(doc_ids):,} documents", flush=True)
        document = build_document(doc_id, source.load("raw", doc_id), report)
        store.put_documents([document])
        report.bump("documents")

        if doc_id not in tree_ids:
            report.bump("documents_without_tree")
            continue
        provisions = list(walk_tree(source.load("trees", doc_id), doc_id))
        if not provisions:
            report.bump("documents_without_structure")
            continue
        store.put_provisions(provisions)
        report.bump("provisions", len(provisions))

        texts = source.load("provisions", doc_id)["nodes"] if doc_id in text_ids else {}
        if not texts:
            report.bump("documents_without_text")
            continue
        versions = build_versions(provisions, texts, document)
        store.put_versions(versions)
        report.bump("versions", len(versions))
        if document.effective_from is None:
            report.bump("versions_undated", len(versions))

    store.commit()
    return report
