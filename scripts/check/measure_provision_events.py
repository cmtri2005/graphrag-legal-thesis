#!/usr/bin/env python3
"""P3.13 — how good are the L2 provision events (`extract_provision_events.py`)?

Three measurements, none of which trusts the extractor's own output:

1. Recall against the portal's own ground truth. `expiry_targets.jsonl` holds
   the (document, provision) pairs whose expiry the portal recorded and the
   resolver pinned to one node. A pair is recovered when some event that ends
   a version (see ENDING) covers that provision, itself or an ancestor. The
   portal's status suffix also says which kind of operation it recorded;
   section 2b checks the extracted operation against it.
2. Agreement on the gold set. Where only one document acts on the target,
   the actor is known without reading any text (backfill T5.4); an event that
   covers such a pair must name that same actor.
3. Precision by hand. `data/derived/provision_events_sample.tsv` is a fixed-seed
   stratified sample of applicable (verified + auto_accepted) events with their evidence, to be judged by a
   reader (column `correct`).
4. The new wording, by hand. `data/derived/provision_wording_sample.tsv` samples
   applicable events carrying `text_updates`: is that the provision's text after
   the act, cut at the right markers?

It also reports the point of the exercise: pairs in documents with several
actors — undatable from metadata — that now have exactly one actor.

Usage:
    python scripts/check/measure_provision_events.py
"""
from __future__ import annotations

import argparse
import collections
import json
import random
from pathlib import Path

from legal_crawler.index import TemporalIndex
from legal_crawler.temporal import make_document_id, make_provision_id

# 20260918–20 and 20260922 drew the samples the error classes were found on; 20260921
# measured v4 (56/60, all resolved events). From 20260923 section 3 samples only the
# applicable events (verified + auto_accepted), the ones P3.15 writes into version chains.
SAMPLE_SEED = 20260923
# Every operation that ends the version the portal calls expired. An amended
# Khoản is "hết hiệu lực một phần" too: its old wording stops applying.
# Supplement only adds nodes, so it ends nothing.
ENDING = {"repeal", "replace", "amend", "correct", "suspend"}
# The portal's partial-expiry suffix, read against the operation the acting
# text states (2026-09-18: 1→repeal 81%, 3→amend 86%, 4→replace, 2→correct).
STATUS_OP = {"HHL1P1": "repeal", "HHL1P2": "correct", "HHL1P3": "amend", "HHL1P4": "replace"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--sample", type=int, default=60)
    args = parser.parse_args()
    data = args.data

    events = [json.loads(l) for l in (data / "derived/provision_events.jsonl").read_text(encoding="utf-8").splitlines()]
    raw_ids = {p.stem for p in (data / "raw").glob("*.json")}
    actors_of: dict[str, set[str]] = collections.defaultdict(set)
    for line in (data / "edges.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e["group"] == "genealogy" and e["source_id"] in raw_ids:
            actors_of[make_document_id(e["target_id"])].add(
                make_document_id(e["source_id"])
            )

    gold: set[tuple[str, str]] = set()
    gold_status: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for line in (data / "expiry_targets.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("code") == "resolved_exact":
            for pid in row.get("provision_ids", []):
                pair = (make_document_id(row["doc_id"]), make_provision_id(pid))
                gold.add(pair)
                gold_status[pair].add(row.get("status"))

    covering: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    covering_ops: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    any_op: set[tuple[str, str]] = set()
    for ev in events:
        if not ev.get("target_document_id") or not ev.get("affected_provision_ids"):
            continue
        for pid in ev["affected_provision_ids"]:
            pair = (ev["target_document_id"], pid)
            if pair in gold:
                any_op.add(pair)
                if ev["operation"] in ENDING:
                    covering[pair].add(ev["actor_id"])
                    covering_ops[pair].add(ev["operation"])

    def bucket(doc: str) -> str:
        n = len(actors_of.get(doc, ()))
        return "single-actor" if n == 1 else ("multi-actor" if n > 1 else "no actor")

    print("== Events ==")
    codes = collections.Counter((ev["operation"], "doc" if ev["locator"] is None else "prov", ev["code"]) for ev in events)
    for (op, scope, code), n in sorted(codes.items()):
        print(f"  {n:>7,}  {op:<10} {scope:<4} {code}")
    methods = collections.Counter(ev["method"] for ev in events if ev["code"] == "resolved_subtree")
    print("  resolved provision events by method:", dict(methods.most_common()))

    print("\n== Event store status (applicable: verified + auto_accepted) ==")
    for (status, reason), n in sorted(collections.Counter(
            (ev["status"], ev["status_reason"]) for ev in events).items(), key=lambda kv: -kv[1]):
        print(f"  {n:>7,}  {status:<13} {reason or ''}")
    by_op = collections.defaultdict(collections.Counter)
    for ev in events:
        if ev["code"] == "resolved_subtree":
            by_op[ev["operation"]][ev["status"] != "needs_review"] += 1
    for op, c in sorted(by_op.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"  {op:<10} resolved {sum(c.values()):>6,} | applicable {c[True]:>6,} ({c[True] / sum(c.values()):.1%})")

    print("\n== 1. Recall against portal expiryProvisions (resolved pairs) ==")
    table = collections.defaultdict(lambda: collections.Counter())
    for pair in gold:
        b = bucket(pair[0])
        table[b]["pairs"] += 1
        table[b]["covered (ending op)"] += pair in covering
        table[b]["covered (any op)"] += pair in any_op
        table[b]["exactly one actor"] += len(covering.get(pair, ())) == 1
    total = collections.Counter()
    for b in ("single-actor", "multi-actor", "no actor"):
        c = table[b]
        total.update(c)
        if c["pairs"]:
            print(f"  {b:<13} {c['pairs']:>6,} pairs | covered {c['covered (ending op)']:>6,} "
                  f"({c['covered (ending op)'] / c['pairs']:.1%}) | any op {c['covered (any op)'] / c['pairs']:.1%} "
                  f"| dated by one actor {c['exactly one actor']:>6,}")
    print(f"  {'all':<13} {total['pairs']:>6,} pairs | covered {total['covered (ending op)']:>6,} "
          f"({total['covered (ending op)'] / total['pairs']:.1%})")

    print("\n== 2. Agreement with the single-actor gold (actor known from metadata) ==")
    agree = disagree = 0
    for pair, acts in covering.items():
        known = actors_of.get(pair[0], set())
        if len(known) == 1:
            if acts == known:
                agree += 1
            else:
                disagree += 1
    print(f"  covered single-actor pairs: {agree + disagree:,} | same actor {agree:,} | different {disagree:,}"
          + (f" | agreement {agree / (agree + disagree):.1%}" if agree + disagree else ""))

    print("\n== 2b. Operation type vs the portal's status suffix ==")
    match = total_typed = 0
    for pair, ops in covering_ops.items():
        expected = {STATUS_OP[s] for s in gold_status[pair] if s in STATUS_OP}
        if expected:
            total_typed += 1
            match += bool(ops & expected)
    print(f"  covered pairs with a typed status: {total_typed:,} | extracted operation agrees {match:,}"
          + (f" ({match / total_typed:.1%})" if total_typed else ""))

    print("\n== What L2 adds ==")
    multi = [p for p in gold if bucket(p[0]) == "multi-actor"]
    newly = [p for p in multi if len(covering.get(p, ())) == 1]
    print(f"  multi-actor pairs (undatable from metadata): {len(multi):,}")
    print(f"  of these, now attributed to exactly one actor: {len(newly):,} ({len(newly) / max(1, len(multi)):.1%})")
    gold_docs = {d for d, _ in gold}
    extra = {(ev["target_document_id"], ev["target_provision_id"]) for ev in events
             if ev["operation"] in ENDING and ev["code"] == "resolved_subtree"
             and ev["target_document_id"] not in gold_docs}
    print(f"  resolved provision-ending events in documents the portal gives NO provision list for: {len(extra):,}")

    agree_docs = [ev for ev in events if ev["operation"] in ENDING and ev["code"] == "resolved_subtree"
                  and ev["target_document_id"] in gold_docs]
    hit = sum(1 for ev in agree_docs
              if any((ev["target_document_id"], pid) in gold for pid in ev["affected_provision_ids"]))
    print(f"  provision-ending events on documents with a portal list: {len(agree_docs):,}, "
          f"matching that list {hit:,} ({hit / max(1, len(agree_docs)):.1%}) — a lower bound on precision, "
          "the portal list is often incomplete")

    index = TemporalIndex(data / "temporal.sqlite")
    titles: dict[str, dict[str, str]] = {}

    def title_of(doc: str, pid: str) -> str:
        if doc not in titles:
            titles[doc] = {p.id: p.title for p in index.document_order(doc)}
        return titles[doc].get(pid, "?")

    resolved = [ev for ev in events if ev["code"] == "resolved_subtree" and ev["status"] != "needs_review"]
    strata = collections.defaultdict(list)
    for ev in resolved:
        strata["explicit" if ev["method"] == "explicit" else ("intro" if ev["method"] == "intro" else "other")].append(ev)
    rng = random.Random(SAMPLE_SEED)
    quota = {"explicit": args.sample // 2, "intro": args.sample // 4, "other": args.sample - args.sample // 2 - args.sample // 4}
    sample = [ev for name, q in quota.items() for ev in rng.sample(strata[name], min(q, len(strata[name])))]
    out = data / "derived" / "provision_events_sample.tsv"
    with out.open("w", encoding="utf-8") as f:
        f.write("correct\tstatus\tactor_id\tactor_number\toperation\tmethod\ttarget_number\ttarget_document_id\tlocator\tresolved_title\tevidence\n")
        for ev in sample:
            loc = " > ".join(f"{lvl} {lab}" for lvl, lab in ev["locator"])
            evidence = " ".join(ev["evidence"].split())
            f.write(f"\t{ev['status']}\t{ev['actor_id']}\t{ev['actor_number']}\t{ev['operation']}\t{ev['method']}\t{ev['document_number']}\t"
                    f"{ev['target_document_id']}\t{loc}\t{title_of(ev['target_document_id'], ev['target_provision_id'])}\t{evidence}\n")
    print(f"\n== 3. Hand check: {len(sample)} sampled events -> {out} ==")

    worded = [ev for ev in events if ev["text_updates"] and ev["status"] != "needs_review"]
    picked = rng.sample(worded, min(args.sample // 2, len(worded)))
    out = data / "derived" / "provision_wording_sample.tsv"
    with out.open("w", encoding="utf-8") as f:
        f.write("correct\tactor_id\tactor_number\toperation\ttarget_document_id\tlocator\tnodes\tinstruction\tnew_text\n")
        for ev in picked:
            loc = " > ".join(f"{lvl} {lab}" for lvl, lab in ev["locator"])
            new = " ‖ ".join(u["new_text"] for u in ev["text_updates"])
            f.write(f"\t{ev['actor_id']}\t{ev['actor_number']}\t{ev['operation']}\t{ev['target_document_id']}\t{loc}\t"
                    f"{len(ev['text_updates'])}\t{' '.join(ev['evidence'].split())}\t{' '.join(new.split())[:1500]}\n")
    print(f"== 4. New wording: {len(picked)} of {len(worded):,} applicable events with text -> {out} ==")


if __name__ == "__main__":
    main()
