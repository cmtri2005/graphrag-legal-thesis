#!/usr/bin/env python3
"""Stage 2b: close the graph over inbound genealogy relations.

Stage 2's BFS walks `references[]`, which only points outward — so documents
that acted ON our corpus (amended, repealed, replaced it) were never
discovered. This fetches /doc/{id}/diagram for everything we hold, reads the
inbound relations, pulls in the missing actors, and repeats until nothing new
turns up. See src/legal_crawler/diagram.py for the direction rules and for
which relations are deliberately NOT followed.

Writes:
    data/diagrams/{id}.json   raw diagram payload, one per document
    data/raw/{id}.json        newly discovered documents (same store as Stage 3)
    data/reverse_seeds.json   ids discovered here, to feed build_graph.py

Afterwards, re-run build_graph.py with --extra-seeds data/reverse_seeds.json so
edges.jsonl is regenerated including the new documents' own references — the
diagram is only used for DISCOVERY, edges still come from references[].

Resumable: existing diagram/raw files are the checkpoint. Safe to interrupt.

Usage:
    python scripts/pipeline/expand_reverse.py
    python scripts/pipeline/expand_reverse.py --max-new 3000
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from legal_crawler.sources.api_client import ApiClient, DocumentNotFoundError
from legal_crawler.graph.diagram import (
    REVERSE_EXPANDABLE,
    expandable_targets,
    parse_reverse_edges,
)
from legal_crawler.storage.manifest import CrawlManifest
from legal_crawler.storage.documents import read_json


def fetch_diagram_cached(client: ApiClient, out_dir: Path, doc_id: str) -> dict | None:
    """Diagram for one document, served from disk when already fetched."""
    path = out_dir / f"{doc_id}.json"
    if path.exists():
        return read_json(path)
    try:
        payload = client.get_diagram(doc_id)
    except DocumentNotFoundError:
        return None
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--diagrams", type=Path, default=Path("data/diagrams"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.sqlite"))
    parser.add_argument("--seeds-out", type=Path, default=Path("data/reverse_seeds.json"))
    parser.add_argument(
        "--max-new",
        type=int,
        default=20000,
        help="circuit breaker on newly fetched documents, not a scope limit",
    )
    args = parser.parse_args()

    args.diagrams.mkdir(parents=True, exist_ok=True)
    client = ApiClient()
    manifest = CrawlManifest(args.manifest)

    held = {p.stem for p in args.raw.glob("*.json")}
    print(f"documents held: {len(held):,}")

    # Everything whose diagram we still need. Grows as new documents arrive.
    queue = collections.deque(sorted(held - {p.stem for p in args.diagrams.glob("*.json")}))
    print(f"diagrams to fetch: {len(queue):,}\n")

    discovered: set[str] = set()
    inbound_by_code: collections.Counter[int] = collections.Counter()
    skipped_by_code: collections.Counter[int] = collections.Counter()
    diagrams_done = gone = new_failed = 0

    while queue:
        doc_id = queue.popleft()
        diagram = fetch_diagram_cached(client, args.diagrams, doc_id)
        diagrams_done += 1
        if diagram is None:
            gone += 1
            continue

        edges = parse_reverse_edges(doc_id, diagram)
        for edge in edges:
            if edge.reference_type in REVERSE_EXPANDABLE:
                inbound_by_code[edge.reference_type] += 1
            else:
                skipped_by_code[edge.reference_type] += 1

        for new_id in sorted(expandable_targets(edges, held)):
            if len(discovered) >= args.max_new:
                print(
                    f"\nWARNING: hit the {args.max_new}-document circuit breaker — "
                    "closure is incomplete, investigate before trusting it.",
                    file=sys.stderr,
                )
                queue.clear()
                break
            try:
                document = client.get_document(new_id)
            except DocumentNotFoundError:
                # Cited by someone but removed upstream: permanent, and already
                # how build_graph.py treats a dangling reference.
                manifest.mark_removed([new_id], datetime.now(timezone.utc).isoformat())
                gone += 1
                continue
            except Exception as exc:  # noqa: BLE001 — one bad id must not kill the run
                new_failed += 1
                print(f"  [{new_id}] failed: {type(exc).__name__}: {exc}")
                continue

            raw_text = json.dumps(document, ensure_ascii=False)
            (args.raw / f"{new_id}.json").write_text(raw_text, encoding="utf-8")
            manifest.upsert(
                new_id,
                sitemap_lastmod="",
                content_hash=sha256(raw_text.encode("utf-8")).hexdigest(),
                eff_status=(document.get("effStatus") or {}).get("name"),
                eff_to=document.get("effTo"),
                crawled_at=datetime.now(timezone.utc).isoformat(),
            )
            held.add(new_id)
            discovered.add(new_id)
            # A newly pulled-in document has its own inbound relations, so it
            # joins the diagram queue: the closure is what makes an amendment
            # chain complete rather than one hop deep.
            queue.append(new_id)

        if diagrams_done % 250 == 0:
            print(
                f"  diagrams {diagrams_done:,} | queue {len(queue):,} | "
                f"new documents {len(discovered):,}"
            )

    args.seeds_out.write_text(
        json.dumps(sorted(discovered), ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(f"\ndiagrams fetched: {diagrams_done:,} | gone (4xx): {gone} | fetch failures: {new_failed}")
    print(f"NEW documents discovered: {len(discovered):,} -> {args.seeds_out}")
    print("\ninbound relations followed:")
    for code, count in inbound_by_code.most_common():
        print(f"  code {code:>2}: {count:>7,}")
    print("inbound relations recorded but NOT followed (see graph/diagram.py):")
    for code, count in skipped_by_code.most_common():
        print(f"  code {code:>2}: {count:>7,}")
    print(
        "\nNext: python scripts/pipeline/build_graph.py --max-documents 40000 "
        f"--extra-seeds {args.seeds_out}\n  (regenerates edges.jsonl including the new documents)"
    )


if __name__ == "__main__":
    main()
