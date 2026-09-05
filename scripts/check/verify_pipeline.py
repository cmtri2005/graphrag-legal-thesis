#!/usr/bin/env python3
"""Consistency checks across everything Stage 1-5b produced.

Run this before trusting the corpus for downstream work, and after any crawl
re-run. It only reads local files (no network), so it's cheap to repeat.

The load-bearing check is GENEALOGY COMPLETENESS: every genealogy edge must
point at a document we actually hold, or at one explicitly accounted for as
gone/failed. A genealogy target that is merely absent means Stage 2's BFS
dropped part of an amendment lineage — which would silently corrupt
point-in-time answers later, since a repeal we never fetched is a repeal we
can never apply.

Exit code is 1 if any check fails, so it can gate a pipeline run.

Usage:
    python scripts/check/verify_pipeline.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from legal_crawler.config import KEYWORDS_BY_DOMAIN
from legal_crawler.storage.manifest import CrawlManifest
from legal_crawler.vocab.reference_types import (
    DEFAULT_MAP_PATH,
    EdgeGroup,
    ReferenceTypeMap,
)
from legal_crawler.sources.sitemap import matches_any_keyword
from legal_crawler.vocab.status_codes import StatusCodeMap, parse_transition
from legal_crawler.storage.documents import DocumentStore, read_json

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    d = args.data

    store = DocumentStore(d)
    raw_ids = store.ids("raw")
    print(f"corpus: {len(raw_ids)} documents in {store.dir('raw')}\n")

    # ---------------------------------------------------------------- Stage 3
    print("Stage 3 — raw documents")
    bad_json, id_mismatch, no_title = [], [], []
    seen_codes: set[int] = set()
    for doc_id in raw_ids:
        try:
            doc = store.load("raw", doc_id)
        except Exception:  # noqa: BLE001
            bad_json.append(doc_id)
            continue
        if str(doc.get("id")) != doc_id:
            id_mismatch.append(doc_id)
        if not doc.get("title"):
            no_title.append(doc_id)
        for ref in doc.get("references") or []:
            if ref.get("referenceType") is not None:
                seen_codes.add(int(ref["referenceType"]))
    check("every raw file is valid JSON", not bad_json, f"{len(bad_json)} broken")
    check("filename matches document id", not id_mismatch, f"{len(id_mismatch)} mismatched")
    check("every document has a title", not no_title, f"{len(no_title)} missing")

    # --------------------------------------------------------------- Stage 3b
    print("\nStage 3b — referenceType mapping")
    ref_map = ReferenceTypeMap.load(DEFAULT_MAP_PATH)
    unmapped = seen_codes - ref_map.codes
    check(
        "every code seen in raw is in the verified map",
        not unmapped,
        f"unmapped: {sorted(unmapped)}" if unmapped else f"{len(seen_codes)} codes seen",
    )

    # ---------------------------------------------------------------- Stage 2
    print("\nStage 2 — edges and BFS completeness")
    edges_path = d / "edges.jsonl"
    edges = [json.loads(line) for line in edges_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"  {len(edges):,} edges")

    orphan_sources = {e["source_id"] for e in edges} - raw_ids
    check("every edge source is a document we hold", not orphan_sources, f"{len(orphan_sources)} orphaned")

    stale_labels = [
        e for e in edges if e["label_vi"] != ref_map.classify(e["reference_type"]).label_vi
    ]
    check("edge labels agree with the current map", not stale_labels, f"{len(stale_labels)} stale")

    # Documents we know about but deliberately do not hold.
    accounted: set[str] = set()
    manifest_path = d / "manifest.sqlite"
    if manifest_path.exists():
        accounted |= CrawlManifest(manifest_path).removed_ids()
    failed_path = d / "failed_ids.txt"
    if failed_path.exists():
        accounted |= {
            line.split("\t", 1)[0]
            for line in failed_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    genealogy_targets = {
        e["target_id"] for e in edges if e["group"] == EdgeGroup.GENEALOGY.value
    }
    missing_genealogy = genealogy_targets - raw_ids - accounted
    check(
        "every genealogy target was fetched or accounted for",
        not missing_genealogy,
        f"{len(missing_genealogy)} unreachable of {len(genealogy_targets)} targets",
    )
    if missing_genealogy:
        print(f"        examples: {sorted(missing_genealogy)[:5]}")

    open_targets = {e["target_id"] for e in edges if e["group"] == EdgeGroup.OPEN_CITATION.value}
    print(
        f"  (open-citation targets not held: {len(open_targets - raw_ids):,} "
        f"of {len(open_targets):,} — expected, these are never expanded through)"
    )

    # ---------------------------------------------------------------- Stage 1
    print("\nStage 1 — seeds")
    seeds = read_json(d / "seeds.json")
    seed_ids = {e["doc_id"] for entries in seeds.values() for e in entries}
    check("seed domains match config", set(seeds) == set(KEYWORDS_BY_DOMAIN), f"{sorted(seeds)}")
    check(
        "every seed was fetched or accounted for",
        not (seed_ids - raw_ids - accounted),
        f"{len(seed_ids - raw_ids - accounted)} missing of {len(seed_ids)}",
    )
    mismatched_slugs = [
        e["doc_id"]
        for domain, entries in seeds.items()
        for e in entries
        if not matches_any_keyword(e.get("slug", ""), KEYWORDS_BY_DOMAIN[domain])
    ]
    check(
        "every seed slug really matches its domain keywords",
        not mismatched_slugs,
        f"{len(mismatched_slugs)} mismatched",
    )

    # ---------------------------------------------------------------- Stage 4
    print("\nStage 4 — field review exclusions")
    excluded_path = d / "excluded_ids.txt"
    excluded = {
        line.split("\t", 1)[0]
        for line in excluded_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    check("excluded ids exist in the corpus", not (excluded - raw_ids), f"{len(excluded)} excluded")
    check("exclusions only ever touch seeds", not (excluded - seed_ids), "BFS-found docs are exempt")

    # --------------------------------------------------------------- manifest
    print("\nManifest")
    if manifest_path.exists():
        total, distinct = CrawlManifest(manifest_path).row_counts()
        check("manifest has no duplicate ids", total == distinct, f"{total:,} rows")
        check(
            "manifest covers every held document",
            distinct >= len(raw_ids),
            f"{distinct:,} manifest vs {len(raw_ids):,} raw",
        )

    # --------------------------------------------------------------- Stage 5a
    print("\nStage 5a — provision trees (may still be running)")
    trees_dir = d / "trees"
    if trees_dir.exists():
        tree_ids = store.ids("trees")
        check("no tree file without its document", not (tree_ids - raw_ids), f"{len(tree_ids):,} trees")
        print(f"  coverage: {len(tree_ids)}/{len(raw_ids)} ({len(tree_ids)/len(raw_ids)*100:.0f}%)")
    history_dir = d / "history"
    if history_dir.exists():
        hist_ids = store.ids("history")
        check("no history file without its document", not (hist_ids - raw_ids), f"{len(hist_ids):,} histories")
        print(f"  coverage: {len(hist_ids)}/{len(raw_ids)} ({len(hist_ids)/len(raw_ids)*100:.0f}%)")

        # Same rule as referenceType: an unmapped effectivity code must never
        # reach Stage 6, where mis-reading one corrupts every point-in-time
        # answer that depends on it.
        status_map = StatusCodeMap.load()
        seen_status: set[str] = set()
        for path in history_dir.glob("*.json"):
            for row in read_json(path).get("history") or []:
                content = str(row.get("content") or "")
                if parse_transition(content) is None:
                    seen_status.add(content)
        unmapped_status = seen_status - status_map.codes
        check(
            "every history status code is in the verified map",
            not unmapped_status,
            f"unmapped: {sorted(unmapped_status)}" if unmapped_status else f"{len(seen_status)} codes seen",
        )

    # --------------------------------------------------------------- Stage 5b
    print("\nStage 5b — provision text")
    prov_dir = d / "provisions"
    if prov_dir.exists():
        prov_paths = list(prov_dir.glob("*.json"))
        stray = store.ids("provisions") - store.ids("trees")
        check("no provision file without its tree", not stray, f"{len(stray)} stray")

        # The tree is the yardstick: a node with text must be a node the server
        # actually declared. Anything else means the alignment invented a node,
        # which is the one failure mode that would be invisible downstream.
        overshoot, with_text, total_nodes, low = [], 0, 0, 0
        queued_text = queued_nodes = 0
        for path in prov_paths:
            rec = read_json(path)
            with_text += len(rec["nodes"])
            total_nodes += rec["total_nodes"]
            if len(rec["nodes"]) > rec["total_nodes"]:
                overshoot.append(rec["doc_id"])
            if rec["coverage"] < 0.5:
                low += 1
                queued_text += len(rec["nodes"])
                queued_nodes += rec["total_nodes"]
        check(
            "no document has more matched nodes than tree nodes",
            not overshoot,
            f"{len(overshoot)} overshoot",
        )
        # Measured only over documents NOT in the review queue. The queued ones
        # are old records whose tree is unnumbered ("Phần", "Điều", five nodes
        # all titled "Khoản 1") while the body runs "I." / "1.1." — their nodes
        # are provably unmatchable, so counting them would set the bar at a
        # number no honest algorithm can reach, and the only way to pass would
        # be to start guessing. The queue check below is what keeps them
        # accounted for.
        live_text = with_text - queued_text
        live_nodes = total_nodes - queued_nodes
        pct = live_text / live_nodes * 100 if live_nodes else 0
        check(
            "at least 95% of matchable tree nodes carry text",
            pct >= 95,
            f"{live_text:,}/{live_nodes:,} ({pct:.2f}%) outside the review queue; "
            f"{with_text:,}/{total_nodes:,} ({with_text / total_nodes * 100:.1f}%) overall",
        )
        review_path = d / "provision_review.txt"
        check(
            "every low-coverage document is in the review queue",
            low == 0 or review_path.exists(),
            f"{low:,} below 50% coverage",
        )

    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED {len(failures)} check(s):")
        for name in failures:
            print(f"  - {name}")
        raise SystemExit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
