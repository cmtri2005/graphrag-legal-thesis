#!/usr/bin/env python3
"""E1: audit point-in-time snapshots against crawled consolidated legal texts.

This is an automatic, source-dependent diagnostic, not the 100 manually
adjudicated cases required by E2.  It examines every CONSOLIDATES source,
reports why a source cannot be compared, and never counts unmatched structure
as a text match or silently chooses an amending act as the base document.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from compare_neo4j_snapshots import load_states
from legal_crawler.graph.consolidation_validation import (
    article_marker, normalized_text, select_base_target, source_units, target_units,
)
from legal_crawler.index import TemporalIndex
from legal_crawler.provisions.text import has_visible_text, parse_paragraphs
from legal_crawler.storage.documents import DocumentStore
from legal_crawler.temporal import SnapshotService, make_document_id


def consolidation_edges(path: Path) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            if row.get("reference_type") != 7:
                continue
            source_id, target_id = row.get("source_id"), row.get("target_id")
            if not isinstance(source_id, str) or not isinstance(target_id, str):
                raise ValueError(f"CONSOLIDATES edge {line_number} has no endpoint ID")
            grouped[source_id].add(target_id)
    if not grouped:
        raise ValueError("no CONSOLIDATES edges in source graph")
    return {key: tuple(sorted(grouped[key])) for key in sorted(grouped)}


def _date(value: Any) -> date | None:
    try:
        return date.fromisoformat(value[:10]) if isinstance(value, str) else None
    except ValueError:
        return None


def _raw(store: DocumentStore, source_id: str) -> dict[str, Any] | None:
    path = store.path("raw", source_id)
    return store.load("raw", source_id) if path.is_file() else None


def discover(data_dir: Path, groups: dict[str, tuple[str, ...]]) -> list[dict[str, Any]]:
    """Declare eligibility without loading snapshots or making any graph writes."""
    store = DocumentStore(data_dir)
    discovered: list[dict[str, Any]] = []
    with TemporalIndex(data_dir / "temporal.sqlite") as index:
        for source_id, target_ids in groups.items():
            record: dict[str, Any] = {
                "consolidated_document_id": make_document_id(source_id),
                "target_ids": [make_document_id(item) for item in target_ids],
            }
            raw = _raw(store, source_id)
            if raw is None:
                record["status"] = "source_raw_missing"
                discovered.append(record)
                continue
            record["number"] = raw.get("docNum")
            record["title"] = raw.get("title")
            record["source_raw_sha256"] = hashlib.sha256(
                store.path("raw", source_id).read_bytes()
            ).hexdigest()
            indexed_source = index.document(make_document_id(source_id))
            if indexed_source is None:
                record["status"] = "source_not_indexed"
                discovered.append(record)
                continue
            record["source_url"] = indexed_source.source_url
            if not raw.get("isConsolidatedDocument"):
                record["status"] = "source_not_marked_consolidated"
                discovered.append(record)
                continue
            html = (raw.get("documentContent") or {}).get("content") or ""
            if not has_visible_text(html):
                record["status"] = "source_body_empty"
                discovered.append(record)
                continue
            issued_on = _date(raw.get("issueDate"))
            if issued_on is None:
                record["status"] = "source_issue_date_missing"
                discovered.append(record)
                continue
            record["at"] = issued_on.isoformat()
            paragraphs = parse_paragraphs(html)
            first_article = next(
                (i for i, paragraph in enumerate(paragraphs)
                 if article_marker(paragraph.text) is not None), None,
            )
            if first_article is None:
                record["status"] = "source_has_no_article_marker"
                discovered.append(record)
                continue
            preamble = " ".join(item.text for item in paragraphs[:first_article])
            targets = {target_id: _raw(store, target_id) for target_id in target_ids}
            if any(item is None for item in targets.values()):
                record["status"] = "target_raw_missing"
                discovered.append(record)
                continue
            selected, method = select_base_target(
                {target_id: item.get("docNum") or "" for target_id, item in targets.items()},
                preamble,
            )
            record["selection_method"] = method
            if selected is None:
                record["status"] = "base_target_unresolved"
                discovered.append(record)
                continue
            record["base_document_id"] = make_document_id(selected)
            base = targets[selected]
            if base.get("isConsolidatedDocument"):
                record["status"] = "selected_target_is_consolidated"
                discovered.append(record)
                continue
            base_issued = _date(base.get("issueDate"))
            if base_issued and base_issued > issued_on:
                record["status"] = "base_issued_after_consolidation"
                discovered.append(record)
                continue
            if not index.document_order(make_document_id(selected)):
                record["status"] = "base_has_no_tree"
                discovered.append(record)
                continue
            units, source_stats = source_units(paragraphs[first_article:])
            record["source_marker_counts"] = dict(source_stats)
            record["source_unit_count"] = len(units)
            if not units:
                record["status"] = "source_has_no_unique_units"
                discovered.append(record)
                continue
            record["status"] = "ready"
            record["_units"] = units
            discovered.append(record)
    return discovered


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare(data_dir: Path) -> dict[str, Any]:
    edges = data_dir / "edges.jsonl"
    groups = consolidation_edges(edges)
    documents = discover(data_dir, groups)
    base_ids = tuple(sorted({row["base_document_id"] for row in documents
                             if row["status"] == "ready"}))
    states = load_states(data_dir, base_ids) if base_ids else {}
    with TemporalIndex(data_dir / "temporal.sqlite") as index:
        for row in documents:
            if row["status"] != "ready":
                continue
            base_id = row["base_document_id"]
            keys, ambiguous = target_units(index.document_order(base_id))
            source_keys = {unit.key for unit in row["_units"]}
            cases = []
            snapshotter = SnapshotService(states[base_id])
            at = date.fromisoformat(row["at"])
            for unit in row.pop("_units"):
                case = {"level": unit.level, "article": unit.article,
                        "clause": unit.clause, "source_sha256": _sha(unit.text),
                        "source_preview": unit.text[:160]}
                if unit.key in ambiguous:
                    case["status"] = "ambiguous_base_key"
                elif unit.key not in keys:
                    case["status"] = "base_unit_missing"
                else:
                    provision_id = keys[unit.key]
                    case["provision_id"] = provision_id
                    result = snapshotter.snapshot(provision_id, at)
                    case["version_id"] = result.version.id if result.version else None
                    case["validity_reason"] = (
                        result.validity.reason.value if result.validity.reason else None
                    )
                    source_repealed = "(được bãi bỏ)" in unit.text.casefold()
                    if source_repealed:
                        case["status"] = (
                            "repeal_state_match" if not result.validity.valid
                            else "repeal_state_mismatch"
                        )
                    elif result.text is None:
                        case["status"] = "snapshot_has_no_valid_text"
                    else:
                        expected = normalized_text(result.text)
                        case["snapshot_sha256"] = _sha(expected)
                        case["snapshot_preview"] = expected[:160]
                        if normalized_text(unit.text) == expected:
                            case["status"] = "exact_text_match"
                        elif unit.body_text and unit.body_text == expected:
                            case["status"] = "article_heading_only_difference"
                        else:
                            case["status"] = "text_mismatch"
                cases.append(case)
            row["status"] = "compared"
            row["cases"] = cases
            row["base_unit_count"] = len(keys)
            row["base_only_unit_count"] = len(set(keys) - source_keys)
            row["case_counts"] = dict(Counter(case["status"] for case in cases))

    statuses = Counter(row["status"] for row in documents)
    case_counts = Counter(case["status"] for row in documents for case in row.get("cases", []))
    comparable = sum(case_counts[status] for status in (
        "exact_text_match", "article_heading_only_difference", "text_mismatch",
    ))
    by_level = {
        level: dict(Counter(case["status"] for row in documents
                            for case in row.get("cases", []) if case["level"] == level))
        for level in ("Article", "Clause")
    }
    mismatch_version_ordinals = dict(Counter(
        case["version_id"].rsplit(":", 1)[-1]
        for row in documents for case in row.get("cases", [])
        if case["status"] == "text_mismatch" and case.get("version_id")
    ))
    return {
        "schema_version": 1,
        "check": "E1 consolidated source text vs offline SnapshotService at issueDate",
        "source_edges_sha256": _file_sha(edges),
        "derived_versions_sha256": _file_sha(data_dir / "derived/versions.jsonl"),
        "source_events_sha256": _file_sha(data_dir / "derived/provision_events.jsonl"),
        "consolidation_documents": len(groups),
        "consolidates_edges": sum(len(items) for items in groups.values()),
        "document_statuses": dict(statuses),
        "case_statuses": dict(case_counts),
        "excluded_duplicate_source_keys": sum(
            row.get("source_marker_counts", {}).get("duplicate_unit_keys", 0)
            for row in documents
        ),
        "case_statuses_by_level": by_level,
        "text_mismatch_version_ordinals": mismatch_version_ordinals,
        "comparable_text_units": comparable,
        "exact_text_matches": case_counts["exact_text_match"],
        "exact_match_rate": case_counts["exact_text_match"] / comparable if comparable else None,
        "documents": documents,
        "limitations": [
            "issueDate is the consolidation snapshot date; missing dates are not imputed",
            "only uniquely numbered Articles and Clauses under Articles are aligned",
            "text equality normalizes Unicode NFC and whitespace only",
            "unmatched structure and absent source bodies are not counted as text matches",
            "article heading-only differences are reported separately, not exact matches",
            "automatic agreement is not the manually adjudicated E2 legal accuracy score",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--report", type=Path,
                        default=Path("data/derived/consolidated_snapshot_report.json"))
    args = parser.parse_args()
    report = compare(args.data)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.report.with_name(args.report.name + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    temporary.replace(args.report)
    print(
        f"E1: {report['consolidation_documents']} consolidated documents; "
        f"{report['document_statuses'].get('compared', 0)} comparable documents; "
        f"{report['exact_text_matches']}/{report['comparable_text_units']} "
        f"exact text units; report={args.report}"
    )
    return 0 if report["comparable_text_units"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
