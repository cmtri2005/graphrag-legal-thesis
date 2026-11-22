"""W3: compare an AI-made amendment list (made without seeing the store) with the store's events (pre-registration §3).

An actor listed by the agent becomes a CANDIDATE for human review when the agent says it touches the target
(touches_target yes or unclear, or no resting only on a third-party hint: deviation S8) and the store has no APPLIED event from that actor on the target lineage's chain
(the lineage, its ancestors up to the document, or its descendants). Kinds:
  actor_not_in_store   no document with that number in the store
  no_event             the actor is in the store but has no event aimed at this document
  rejected:<reason>    events aimed at this document exist, none applied to the chain (rejection reasons listed)
  applied_elsewhere    events applied to this document, but none to the chain
Not a candidate either (added 22/11 after the gate run, deviation S7): a version of the lineage (or of its
article, for clause lineages without own versions) or the document itself starts or ends exactly on the actor's effective_on, i.e. the
store already shows a change on that day (typically a whole-document replacement handled by document expiry).
Store = data/temporal.sqlite + data/derived/event_log.jsonl as built on 17/09/2026, i.e. BEFORE any dataset fix,
which is the state the recall gate needs.

python3 data/review/qa_v6/w3/compare.py <batch.jsonl> <agent.jsonl> [...]   ->  prints candidates, writes
<batch>.candidates.jsonl next to the batch file.
"""
import collections
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def number_key(s):
    return re.sub(r"\s+", "", (s or "")).upper().replace("Đ", "D")


def load_store():
    db = sqlite3.connect(ROOT / "data/temporal.sqlite")
    docs = collections.defaultdict(list)
    for did, num in db.execute("select id, number from documents"):
        docs[number_key(num)].append(did)
    parent = dict(db.execute("select id, parent_id from provisions"))
    bounds = collections.defaultdict(set)
    for pid, a, b in db.execute("select provision_id, valid_from, valid_to from versions"):
        bounds[pid] |= {a, b} - {None}
    for did, a, b in db.execute("select id, effective_from, effective_to from documents"):
        bounds[did] |= {a, b} - {None}
    events = collections.defaultdict(list)
    for line in open(ROOT / "data/derived/event_log.jsonl", encoding="utf-8"):
        e = json.loads(line)
        events[e["actor_id"]].append(e)
    return docs, parent, events, bounds


def chain(lineage, parent):
    """The lineage, its '#'-prefixes, and their parents up the tree."""
    parts = lineage.split("#")
    out = {"#".join(parts[:i]) for i in range(1, len(parts) + 1)}
    for p in list(out):
        while parent.get(p):
            p = parent[p]
            out.add(p)
    return out


def on_chain(e, ch, lineage):
    for v in e["closed_version_ids"] + e["created_version_ids"]:
        p = "provision:" + v.split(":", 1)[1].rsplit(":", 1)[0]
        if p in ch or p.startswith(lineage + "#"):
            return True
    return any(p in ch or p.startswith(lineage + "#") for p in e["created_provision_ids"])


def judge(target, actor, store):
    docs, parent, events, bounds = store
    lid = target["lineage_id"]
    days = (bounds.get(lid) or bounds.get(lid.split("#")[0], set())) | bounds.get(target["document_id"], set())
    if actor.get("effective_on") in days:
        return None
    ids = docs.get(number_key(actor["actor_number"]), [])
    if not ids:
        return "actor_not_in_store"
    ch = chain(target["lineage_id"], parent)
    mine = [e for d in ids for e in events[d] if e["target_document_id"] == target["document_id"]]
    if any(e["outcome"] == "applied" and on_chain(e, ch, target["lineage_id"]) for e in mine):
        return None
    if not mine:
        return "no_event"
    if any(e["outcome"] == "applied" for e in mine):
        return "applied_elsewhere"
    return "rejected:" + ",".join(sorted({e["reason"] for e in mine}))


def main(batch, *agent_files):
    targets = {t["key"]: t for t in map(json.loads, open(batch, encoding="utf-8"))}
    actors = [json.loads(x) for f in agent_files for x in open(f, encoding="utf-8") if x.strip()]
    unknown = {a["key"] for a in actors} - set(targets)
    assert not unknown, f"agent keys not in batch: {unknown}"
    missing = set(targets) - {a["key"] for a in actors}
    store, out = load_store(), []
    for a in actors:
        weak_no = a.get("touches_target") == "no" and a.get("source_kind") == "third_party_hint"  # deviation S8
        if not a.get("actor_number") or (a.get("touches_target") == "no" and not weak_no):
            continue
        kind = judge(targets[a["key"]], a, store)
        kind = kind and ("weak_no:" + kind if weak_no else kind)
        if kind:
            out.append({**{k: targets[a["key"]][k] for k in ("key", "lineage_id", "document_id", "law_id", "citation")},
                        "actor_number": a["actor_number"], "relation": a.get("relation"),
                        "effective_on": a.get("effective_on"), "touches_target": a["touches_target"],
                        "source_kind": a.get("source_kind"), "source_url": a.get("source_url"),
                        "quote": a.get("quote"), "candidate_kind": kind})
    dest = Path(batch).with_suffix(".candidates.jsonl")
    with open(dest, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(o, ensure_ascii=False) + "\n" for o in out)
    for o in out:
        print(o["key"], o["law_id"], o["citation"], "<-", o["actor_number"], o["relation"], o["candidate_kind"])
    print(f"{len(out)} ứng viên / {len(targets)} văn bản; agent không trả lời: {sorted(missing) or 'không'} -> {dest.name}")
    return out


if __name__ == "__main__":
    main(*sys.argv[1:])
