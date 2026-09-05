#!/usr/bin/env python3
"""Stage 2-3: BFS-expand from seed ids, fetch every discovered document, and
persist raw JSON + edges + the crawl manifest (docs/crawling-plan.md).

Usage:
    python scripts/pipeline/build_graph.py --seeds data/seeds.json --out data/raw
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import requests

from legal_crawler.sources.api_client import ApiClient
from legal_crawler.graph.expand import expand
from legal_crawler.storage.manifest import CrawlManifest
from legal_crawler.vocab.reference_types import DEFAULT_MAP_PATH, ReferenceTypeMap
from legal_crawler.sources.sitemap import fetch_central_entries
from legal_crawler.storage.documents import read_json, write_json


def load_seed_ids(seeds_path: Path, extra_seeds_path: Path | None = None) -> list[str]:
    seeds = read_json(seeds_path)
    ids = {entry["doc_id"] for entries in seeds.values() for entry in entries}
    if extra_seeds_path:
        # Stage 2b's finds (data/reverse_seeds.json): documents that acted on
        # the corpus and so were unreachable by forward-only BFS. They must
        # enter as seeds or their own references[] never reach edges.jsonl,
        # even though their JSON is already on disk.
        ids |= set(read_json(extra_seeds_path))
    return sorted(ids)


def build_lastmod_index() -> dict[str, str]:
    """id -> sitemap lastmod, across every central-government shard.

    Needed so documents discovered via BFS (not in the keyword-filtered
    seed list) still get a manifest entry for future delta runs.
    """
    with requests.Session() as session:
        return {entry.doc_id: entry.lastmod for entry in fetch_central_entries(session)}


def persist_document(out_dir: Path, doc_id: str, document: dict) -> str:
    """Write the document and return the hash of exactly what landed on disk."""
    written = write_json(out_dir / f"{doc_id}.json", document)
    return sha256(written.encode("utf-8")).hexdigest()


def make_checkpointing_fetcher(
    out_dir: Path, manifest: CrawlManifest, client: ApiClient, lastmod_by_id: dict[str, str]
):
    """Wraps ApiClient.get_document with a disk cache keyed by doc_id.

    This is what makes a run resumable: a doc already on disk from a prior
    (possibly interrupted) run is loaded instead of re-fetched, and every
    freshly-fetched doc is persisted immediately — not batched until the
    whole BFS finishes — so a kill/crash never loses already-done work.
    """
    fetched_count = 0

    def fetch(doc_id: str) -> dict:
        nonlocal fetched_count
        cache_path = out_dir / f"{doc_id}.json"
        if cache_path.exists():
            return read_json(cache_path)

        document = client.get_document(doc_id)
        content_hash = persist_document(out_dir, doc_id, document)
        manifest.upsert(
            doc_id,
            sitemap_lastmod=lastmod_by_id.get(doc_id, ""),
            content_hash=content_hash,
            eff_status=(document.get("effStatus") or {}).get("name"),
            eff_to=document.get("effTo"),
            crawled_at=datetime.now(timezone.utc).isoformat(),
        )
        fetched_count += 1
        if fetched_count % 50 == 0:
            print(f"  ...{fetched_count} newly fetched (rest served from cache)", file=sys.stderr)
        return document

    return fetch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=Path("data/seeds.json"))
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    parser.add_argument("--edges-out", type=Path, default=Path("data/edges.jsonl"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.sqlite"))
    parser.add_argument("--map-path", type=Path, default=DEFAULT_MAP_PATH)
    parser.add_argument(
        "--extra-seeds",
        type=Path,
        default=None,
        help="extra seed ids as a JSON list, e.g. data/reverse_seeds.json from Stage 2b",
    )
    parser.add_argument("--max-documents", type=int, default=5000)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    seed_ids = load_seed_ids(args.seeds, args.extra_seeds)
    reference_types = ReferenceTypeMap.load(args.map_path)
    manifest = CrawlManifest(args.manifest)
    client = ApiClient()

    already_cached = sum(1 for _ in args.out.glob("*.json"))
    print(f"seeds: {len(seed_ids)}; {already_cached} document(s) already cached from a prior run")
    print("building sitemap lastmod index...")
    lastmod_by_id = build_lastmod_index()

    fetch = make_checkpointing_fetcher(args.out, manifest, client, lastmod_by_id)
    print("expanding through verified genealogy edges (resumable — safe to interrupt)...")
    result = expand(seed_ids, fetch, reference_types, max_documents=args.max_documents)
    if result.truncated:
        print(
            f"WARNING: hit the {args.max_documents}-document circuit breaker; "
            "graph is incomplete — investigate before trusting it.",
            file=sys.stderr,
        )
    print(f"total documents in graph: {len(result.documents)}")
    if result.failed:
        failed_path = args.out.parent / "failed_ids.txt"
        failed_path.write_text(
            "\n".join(f"{doc_id}\t{error}" for doc_id, error in result.failed.items()),
            encoding="utf-8",
        )
        print(
            f"WARNING: {len(result.failed)} document(s) could not be fetched "
            f"(dangling reference or transient error) — see {failed_path}",
            file=sys.stderr,
        )
        # Confirmed-gone ids (server says "không tồn tại", not a transient
        # error) get marked removed so future delta runs stop re-requesting
        # them (docs/crawling-plan.md §6b).
        confirmed_gone = [
            doc_id for doc_id, error in result.failed.items() if "không tồn tại" in error
        ]
        if confirmed_gone:
            manifest.mark_removed(confirmed_gone, datetime.now(timezone.utc).isoformat())
            print(f"  {len(confirmed_gone)} of those confirmed permanently gone, marked removed in manifest")

    # edges.jsonl is fully regenerated from result.documents every run (cheap,
    # no network) rather than appended incrementally, so a resumed run can't
    # end up with duplicate or stale edge rows.
    with args.edges_out.open("w", encoding="utf-8") as f:
        for edge in result.edges:
            info = reference_types.classify(edge.reference_type)
            f.write(
                json.dumps(
                    {
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "reference_type": edge.reference_type,
                        "label_vi": info.label_vi,
                        "group": info.group.value,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"documents: {args.out}/  edges: {args.edges_out}  manifest: {args.manifest}")


if __name__ == "__main__":
    main()
