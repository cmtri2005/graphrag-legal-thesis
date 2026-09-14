#!/usr/bin/env python3
"""Measure what each data representation keeps, loses and costs on the real corpus.

Evidence for docs/graph_justification.md. Every number in that document comes
from this script, so the argument can be re-checked instead of trusted.

It compares representations *logically*, on one engine (SQLite), so that a
speed difference is attributable to the representation and not to a product:

* flat      — one row/vector per text chunk, no structure, no relations
* relational— adjacency list (parent_id, edges table), answered by recursive SQL
* graph     — materialized tree paths + in-memory adjacency lists (traversal)
* matrix    — adjacency matrix; costed analytically, since the dense form
              does not fit in memory at this size (shown below)

Needs data/temporal.sqlite (build_store.py) and data/expiry_targets.jsonl
(resolve_expiry_targets.py). Adds one index on provisions(parent_id) to the
derived SQLite file so the relational baseline is not handicapped.

Usage:
    python scripts/explore/compare_representations.py
"""
from __future__ import annotations

import collections
import hashlib
import json
import random
import re
import sqlite3
import statistics
import time
from datetime import date
from pathlib import Path

DATA = Path("data")
SEED, SAMPLE = 42, 1000
AS_OF = (date(2026, 9, 12), date(2020, 1, 1))
out: dict = {}


def pct(values: list[float], q: float) -> float:
    return sorted(values)[min(len(values) - 1, int(q * len(values)))]


def timed(fn, args_list) -> dict:
    """Median and p95 latency in milliseconds over a list of query arguments."""
    for args in args_list[:50]:  # warm-up, not measured
        fn(*args)
    samples = []
    for args in args_list:
        start = time.perf_counter()
        fn(*args)
        samples.append((time.perf_counter() - start) * 1000)
    return {"median_ms": round(statistics.median(samples), 4),
            "p95_ms": round(pct(samples, 0.95), 4), "n": len(samples)}


db = sqlite3.connect(DATA / "temporal.sqlite")
db.execute("CREATE INDEX IF NOT EXISTS provisions_parent ON provisions(parent_id)")
rng = random.Random(SEED)

# ------------------------------------------------------------------ M1 structure
print("M1 — relational structure of the corpus")
lines = [l for l in (DATA / "edges.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
raw_edges = [json.loads(l) for l in lines]
distinct = {(e["source_id"], e["target_id"], e["reference_type"]): e for e in raw_edges}
by_label = collections.Counter(e["label_vi"] for e in distinct.values())
genealogy = [e for e in distinct.values() if e["group"] == "genealogy"]
n_docs = db.execute("SELECT count(*) FROM documents").fetchone()[0]
n_prov = db.execute("SELECT count(*) FROM provisions").fetchone()[0]
tree_edges = db.execute("SELECT count(*) FROM provisions WHERE parent_id IS NOT NULL").fetchone()[0]

inbound = collections.defaultdict(set)
for e in genealogy:
    inbound[e["target_id"]].add(e["source_id"])
in_deg = sorted(len(v) for v in inbound.values())
depths = collections.Counter(
    row[0].count("/") for row in db.execute("SELECT path FROM provisions"))

doc_pairs = n_docs * (n_docs - 1)
out["M1"] = {
    "documents": n_docs, "provisions": n_prov, "tree_edges": tree_edges,
    "edge_lines_in_file": len(raw_edges), "edges_distinct": len(distinct),
    "edge_duplicates": len(raw_edges) - len(distinct),
    "relation_types": len(by_label), "edges_by_label": dict(by_label.most_common()),
    "genealogy_edges_distinct": len(genealogy),
    "amended_documents": len(in_deg),
    "amenders_per_document": {"median": statistics.median(in_deg), "p90": pct(in_deg, .9),
                              "p99": pct(in_deg, .99), "max": in_deg[-1],
                              "share_with_2_or_more": round(sum(d >= 2 for d in in_deg) / len(in_deg), 4)},
    "tree_depth_distribution": dict(sorted(depths.items())),
    "adjacency_density_documents": len(distinct) / doc_pairs,
    "dense_matrix_bytes_documents_1byte_cell": n_docs * n_docs,
    "dense_matrix_bytes_provisions_1bit_cell": n_prov * n_prov // 8,
    "sparse_csr_bytes_documents": (n_docs + 1) * 8 + len(distinct) * 4,
}
print(json.dumps({k: v for k, v in out["M1"].items() if k != "edges_by_label"}, indent=1))

# ---------------------------------------------------- M2 information a flat index loses
print("\nM2a — identical provision text in different documents, conflicting validity")
ranks = dict(db.execute("SELECT id, rank FROM documents"))
groups: dict[bytes, list] = collections.defaultdict(list)
query = ("SELECT p.document_id, v.text, v.valid_from, v.valid_to FROM versions v "
         "JOIN provisions p ON p.id = v.provision_id WHERE length(v.text) >= 100")
for doc_id, text, vf, vt in db.execute(query):
    key = hashlib.blake2b(re.sub(r"\s+", " ", text).strip().casefold().encode(), digest_size=12).digest()
    groups[key].append((doc_id, vf, vt))
multi = [g for g in groups.values() if len({d for d, _, _ in g}) >= 2]


def valid(vf: str | None, vt: str | None, at: str) -> bool | None:
    if not vf:
        return None
    return vf <= at and (vt is None or at < vt)


m2a = {"text_groups_min100chars": len(groups), "groups_in_2plus_documents": len(multi),
       "versions_in_those_groups": sum(len(g) for g in multi)}
for at in AS_OF:
    iso = at.isoformat()
    conflicting, versions, invalid, with_vbhn = 0, 0, 0, 0
    for g in multi:
        states = [valid(vf, vt, iso) for _, vf, vt in g]
        dated = [s for s in states if s is not None]
        if True in dated and False in dated:
            conflicting += 1
            versions += len(dated)
            invalid += dated.count(False)
            with_vbhn += any(ranks.get(d) == "Văn bản hợp nhất" for d, _, _ in g)
    m2a[iso] = {"conflicting_groups": conflicting, "dated_versions_in_them": versions,
                "expected_error_if_flat_picks_uniformly": round(invalid / versions, 4) if versions else 0,
                "conflicting_groups_involving_consolidated_doc": with_vbhn}
out["M2a"] = m2a
print(json.dumps(m2a, indent=1))

print("\nM2b — provisions invalidated only through an ancestor (formula 3)")
targets = set()
for l in (DATA / "expiry_targets.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(l)
    if r["code"] == "resolved_exact":
        targets.update(r["provision_ids"])
db.execute("CREATE TEMP TABLE targets(id TEXT PRIMARY KEY)")
db.executemany("INSERT OR IGNORE INTO targets VALUES (?)", [(t,) for t in targets])
levels = dict(db.execute("SELECT p.level, count(*) FROM provisions p JOIN targets t ON t.id = p.id GROUP BY p.level"))
only_via_ancestor = db.execute("""
    SELECT count(DISTINCT d.id) FROM targets t
    JOIN provisions a ON a.id = t.id
    JOIN provisions d ON d.path > a.path || '/' AND d.path < a.path || '0'
    WHERE d.id NOT IN (SELECT id FROM targets)""").fetchone()[0]
out["M2b"] = {"distinct_repealed_nodes": len(targets), "repealed_nodes_by_level": levels,
              "descendants_invalid_only_via_ancestor": only_via_ancestor}
print(json.dumps(out["M2b"], indent=1))

print("\nM2c — provisions a document-level validity filter cannot decide (B7)")
partial = db.execute("SELECT count(*) FROM documents WHERE raw_status_code LIKE 'HHL1P%'").fetchone()[0]
partial_prov = db.execute("""SELECT count(*) FROM provisions p JOIN documents d ON d.id = p.document_id
                             WHERE d.raw_status_code LIKE 'HHL1P%'""").fetchone()[0]
repealed_by_status = dict(db.execute("""
    WITH invalid AS (SELECT id FROM targets UNION
        SELECT d.id FROM targets t JOIN provisions a ON a.id = t.id
        JOIN provisions d ON d.path > a.path || '/' AND d.path < a.path || '0')
    SELECT doc.raw_status_code, count(*) FROM invalid i JOIN provisions p ON p.id = i.id
    JOIN documents doc ON doc.id = p.document_id GROUP BY 1"""))
out["M2c"] = {"partially_expired_documents": partial, "provisions_inside_them": partial_prov,
              "share_of_all_provisions": round(partial_prov / n_prov, 4),
              "repealed_units_by_document_status": repealed_by_status}
print(json.dumps(out["M2c"], indent=1))

# ------------------------------------------------------------------ M3 query cost
print("\nM3 — query latency, same engine, different representation")
nodes = db.execute("SELECT id, path FROM provisions WHERE level IN ('Chapter','Article') "
                   "AND id IN (SELECT DISTINCT parent_id FROM provisions WHERE parent_id IS NOT NULL)").fetchall()
sample_nodes = rng.sample(nodes, SAMPLE)


def subtree_path(_id, path):
    return db.execute("SELECT count(*) FROM provisions WHERE path > ? AND path < ?",
                      (path + "/", path + "0")).fetchone()


def subtree_recursive(_id, _path):
    return db.execute("""WITH RECURSIVE sub(id) AS (SELECT id FROM provisions WHERE parent_id = ?
                         UNION ALL SELECT p.id FROM provisions p JOIN sub ON p.parent_id = sub.id)
                         SELECT count(*) FROM sub""", (_id,)).fetchone()


leaves = [r[0] for r in db.execute("SELECT id FROM provisions WHERE level IN ('Point','Clause') LIMIT 200000")]
sample_leaves = [(i,) for i in rng.sample(leaves, SAMPLE)]


def ancestors_path(_id):
    return db.execute("SELECT path FROM provisions WHERE id = ?", (_id,)).fetchone()[0].split("/")[1:-1]


def ancestors_recursive(_id):
    return db.execute("""WITH RECURSIVE up(id, parent_id) AS (
                         SELECT id, parent_id FROM provisions WHERE id = ?
                         UNION ALL SELECT p.id, p.parent_id FROM provisions p JOIN up ON p.id = up.parent_id)
                         SELECT id FROM up""", (_id,)).fetchall()


mem = sqlite3.connect(":memory:")
mem.execute("CREATE TABLE edges(source_id TEXT, target_id TEXT)")
mem.executemany("INSERT INTO edges VALUES (?,?)", [(e["source_id"], e["target_id"]) for e in genealogy])
mem.execute("CREATE INDEX edges_target ON edges(target_id)")
adjacency = collections.defaultdict(list)
for e in genealogy:
    adjacency[e["target_id"]].append(e["source_id"])
roots = [(d,) for d in rng.sample(sorted(inbound), SAMPLE)]


def lineage_recursive(doc):
    return mem.execute("""WITH RECURSIVE up(id) AS (SELECT ?
                          UNION SELECT e.source_id FROM edges e JOIN up ON e.target_id = up.id)
                          SELECT count(*) FROM up""", (doc,)).fetchone()


def lineage_bfs(doc):
    seen, queue = {doc}, collections.deque([doc])
    while queue:
        for nxt in adjacency.get(queue.popleft(), ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return len(seen)


assert all(subtree_path(*a)[0] == subtree_recursive(*a)[0] for a in sample_nodes[:100])
assert all(lineage_recursive(*a)[0] == lineage_bfs(*a) for a in roots[:100])
closure = sorted(lineage_bfs(*a) - 1 for a in roots)
out["M3"] = {
    "Q1_subtree": {"graph_materialized_path": timed(subtree_path, sample_nodes),
                   "relational_recursive_cte": timed(subtree_recursive, sample_nodes),
                   "flat": "not answerable: no parent relation stored"},
    "Q2_ancestors_for_propagation": {"graph_materialized_path": timed(ancestors_path, sample_leaves),
                                     "relational_recursive_cte": timed(ancestors_recursive, sample_leaves),
                                     "flat": "not answerable: no parent relation stored"},
    "Q3_transitive_amendment_lineage": {"relational_recursive_cte": timed(lineage_recursive, roots),
                                        "graph_adjacency_bfs": timed(lineage_bfs, roots),
                                        "matrix_dense": "not materializable (see M1)",
                                        "lineage_size": {"median": statistics.median(closure),
                                                         "p90": pct(closure, .9), "max": closure[-1]}},
}
print(json.dumps(out["M3"], indent=1))

(DATA / "representation_benchmark.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwrote data/representation_benchmark.json")
