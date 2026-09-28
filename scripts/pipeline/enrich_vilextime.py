#!/usr/bin/env python3
"""ViLexTime — the release file: the selected rows, their mid-interval twins, schema 1.1.

Runs after `sample_vilextime.py --select` and leaves it alone: selection counts
and picks boundary rows as before; this step reads `selected.jsonl` and writes
`data/derived/vilextime/release.jsonl` (plan phase-4, decisions of 28/09).

  as_of_strategy, twin_of
      Every selected row keeps its date on a version boundary ("ranh_gioi") and
      gets a twin ("giua_khoang"): same question, same gold version, asked on a
      seeded date at least MARGIN days from both ends of the gold window (its
      midpoint when the window is shorter). A date on a boundary gives the
      answer's document away — knowing t alone narrows 17,091 documents to a
      median of 7 whose effect started the day before — so the headline score is
      the twin's. T5's later date stays inside the retroactive window; a
      repealed provision's twin stays after the repeal and before the document
      ends; windows are capped at the snapshot. The twin's gold is recomputed
      from the version chain and must equal its boundary row's, or no twin.
  changed_span
      The words this version has and its neighbouring versions do not.
  evidence_set
      The gold unit, the parent's lead-in and the same-document provisions the
      answer cites ("khoản 2 Điều này", "Điều 5 Nghị định này"), each with the
      version in force at as_of.
  accepted_evidence
      As-published units of corpus layer A that also count as the right
      evidence: the provision itself ("asis:<provision id>") when the gold is its
      original wording; the instruction that wrote the gold wording, or repealed
      a repealed provision ("asis:<event id>"). Instructions are their own units
      because the provision tree of an amending document drops the quoted wording
      in about a third of cases (`build_corpus.py`).
  derivation.transitions[].op
      The event's operation (amend, supplement, replace, repeal, ...).
  domain, domain_source
      The proposal's four fields from the seed keyword search; a document the
      crawl reached through relations inherits the fields of the nearest seed
      documents; otherwise "khac".
  legal_markers
      Heuristics for the checker, not errors: the amending document has a
      transitional article; its effect clause names more than one date.
  short_answer
      From `data/vilextime/short_answers.jsonl`, written and audited by hand,
      keyed by (lineage, version); it must be a span of the answer or lead-in.

Usage:
    python scripts/pipeline/enrich_vilextime.py
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import random
import re
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from legal_crawler.extraction.models import (  # noqa: E402
    ProvisionLocator, ProvisionReferencePart, TargetReference, TargetScope)
from legal_crawler.extraction.provision_ops import parse_locators  # noqa: E402
from legal_crawler.extraction.target_resolver import TargetResolver  # noqa: E402
from legal_crawler.index import TemporalIndex  # noqa: E402
from legal_crawler.temporal.models import ProvisionLevel as L  # noqa: E402

SCHEMA_VERSION = "1.1.0"
SNAPSHOT = date(2026, 9, 17)   # corpus snapshot v2, frozen at M1
MARGIN = 30                    # days a mid-interval date keeps from either boundary
SEED = "vilextime-twin-v1"
DOMAIN_DEPTH = 3
_ORDER = (L.ARTICLE, L.CLAUSE, L.POINT)
_WORD = re.compile(r"\w+", re.UNICODE)
_DOC_TYPES = r"(?:Bộ luật|Luật|Pháp lệnh|Nghị định|Nghị quyết|Thông tư liên tịch|Thông tư|Quyết định|Quy chế|Quy định|Điều lệ)"
# "... tại khoản 2 Điều này", "... điểm a khoản này", "... Điều 5 của Luật này"
_REF = re.compile(rf"(?i)(Điều|khoản)\s+này\b|(?:của\s+)?{_DOC_TYPES}\s+này\b")
_REF_START = re.compile(r"(?i)\b(?:tại|theo|ở|trong|thuộc|như|quy định)\s+")
_DATE = re.compile(r"ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}")


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def norm(text: str) -> str:
    return " ".join(_WORD.findall((text or "").casefold()))


# ------------------------------------------------------------------ dates

def mid_date(start: date, end: date | None, key: str, cap: date = SNAPSHOT) -> date | None:
    """A seeded date in [start + MARGIN, end - MARGIN), or the midpoint of a short window."""
    end = min(end, cap) if end else cap
    span = (end - start).days
    if span < 2:
        return None            # a window that opens at or after the snapshot has no inside
    if span <= 2 * MARGIN:
        return start + timedelta(days=span // 2)
    return start + timedelta(days=MARGIN + random.Random(f"{SEED}:{key}").randrange(span - 2 * MARGIN))


def in_force_at(versions: list[dict], at: date) -> dict | None:
    for v in versions:
        start, end = _d(v["effective_from"]), _d(v["effective_to"])
        if start and start <= at and (end is None or at < end):
            return v
    return None


def window(record: dict, versions: list[dict], document_end: date | None) -> tuple[date, date | None] | None:
    """The stretch of time over which this row's gold stays the same."""
    if record["version_id"] is None:                         # repealed: after the repeal
        ends = [_d(v["effective_to"]) for v in versions if v["effective_to"]]
        return (max(ends), document_end) if ends else None
    version = next((v for v in versions if v["id"] == record["version_id"]), None)
    if version is None or not version["effective_from"]:
        return None
    start, end = _d(version["effective_from"]), _d(version["effective_to"])
    retro = record.get("retroactive")
    if retro and version["effective_from"] == retro["effective_from"]:
        end = min(filter(None, (end, _d(retro["issued_on"]))))   # stay inside the retroactive window
    return start, end


def twin_of(record: dict, versions: list[dict], document_end: date | None) -> dict | None:
    span = window(record, versions, document_end)
    at = mid_date(*span, record["id"]) if span else None
    if at is None or at.isoformat() == record["as_of"]:
        return None
    hit = in_force_at(versions, at)
    if (hit["id"] if hit else None) != record["version_id"]:
        return None                                           # the chain says otherwise: no twin
    twin = json.loads(json.dumps(record))
    twin.update(id=f"{record['id'].rsplit(':', 1)[0]}:{at.isoformat()}", as_of=at.isoformat(),
                as_of_strategy="giua_khoang", twin_of=record["id"])
    twin["derivation"]["query"] = f"as_of({record['lineage_id']}, {at.isoformat()})"
    return twin


# ------------------------------------------------------------------ text

def changed_span(texts: list[str], k: int) -> str | None:
    """Words of version k that its neighbouring versions do not have, in order."""
    if len(texts) < 2:
        return None
    mine = _WORD.findall(texts[k])
    keep = [False] * len(mine)
    for j in (k - 1, k + 1):
        if 0 <= j < len(texts):
            other = _WORD.findall(texts[j])
            for tag, _, _, b1, b2 in difflib.SequenceMatcher(None, other, mine, autojunk=False).get_opcodes():
                if tag in ("replace", "insert"):
                    for i in range(b1, b2):
                        keep[i] = True
    spans, run = [], []
    for word, flag in zip(mine, keep):
        if flag:
            run.append(word)
        elif run:
            spans.append(" ".join(run))
            run = []
    if run:
        spans.append(" ".join(run))
    return " … ".join(spans) or None


def references(answer: str, target: dict) -> list[dict]:
    """Same-document provisions an answer cites, as {level: label} with the relative parts filled."""
    found = []
    for m in _REF.finditer(answer or ""):
        before = answer[max(0, m.start() - 160):m.start()]
        starts = list(_REF_START.finditer(before))
        segment = before[starts[-1].end():] if starts else before
        suffix = (m.group(1) or "").casefold()
        for parts in parse_locators(segment):
            if suffix == "điều":                                # "khoản 2 Điều này"
                if L.ARTICLE in parts or not target.get("article_id"):
                    continue
                parts[L.ARTICLE] = target["article_id"]
            elif suffix == "khoản":                             # "điểm a khoản này"
                if L.CLAUSE in parts or not (target.get("article_id") and target.get("clause_id")):
                    continue
                parts.update({L.ARTICLE: target["article_id"], L.CLAUSE: target["clause_id"]})
            elif L.ARTICLE not in parts:                        # "Điều 5 Nghị định này" must name the Điều
                continue
            parts = {lvl: lab for lvl, lab in parts.items() if lvl in _ORDER}
            mine = {L.ARTICLE: target.get("article_id"), L.CLAUSE: target.get("clause_id"),
                    L.POINT: target.get("point_id")}
            if parts and parts != {lvl: lab for lvl, lab in mine.items() if lvl in parts and lab}:
                found.append(parts)
    unique = []
    for parts in found:
        if parts not in unique:
            unique.append(parts)
    return unique


def check_short_answer(short: str, answer: str | None, lead_in: str | None) -> bool:
    return bool(short) and norm(short) in norm(f"{answer or ''} {lead_in or ''}")


# ------------------------------------------------------------------ corpus lookups

def load_nodes(data: Path, portal_id: str) -> list[dict]:
    nodes = []
    for path in (data / f"provisions/{portal_id}.json", data / f"derived/subtrees/{portal_id}.json"):
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))["nodes"]
            nodes += raw if isinstance(raw, list) else [dict(v, id=k) for k, v in raw.items()]
    return nodes


def markers(nodes: list[dict]) -> set[str]:
    out = set()
    by_parent = collections.defaultdict(list)
    for n in nodes:
        by_parent[n.get("parent_id")].append(n)
    for n in nodes:
        if n.get("level") != "Article":
            continue
        head = (n.get("text") or "")[:120].casefold()
        if "chuyển tiếp" in head:
            out.add("actor_has_transitional")
        if "hiệu lực" in head:
            stack, text = [n], []
            while stack:
                cur = stack.pop()
                text.append(cur.get("text") or "")
                stack += by_parent.get(cur["id"], [])
            sentences = [s for s in re.split(r"[.;]", " ".join(text)) if "có hiệu lực" in s]
            if len({d for s in sentences for d in _DATE.findall(s)}) > 1:
                out.add("split_effective_date")
    return out


def domains(data: Path, documents: set[str]) -> dict[str, tuple[list[str], str]]:
    """document -> (fields, source) — seed fields, else the nearest seeds' over document relations."""
    seed: dict[str, set[str]] = collections.defaultdict(set)
    for field, rows in json.loads((data / "seeds.json").read_text(encoding="utf-8")).items():
        for row in rows:
            seed[row["doc_id"]].add(field)
    near: dict[str, set[str]] = collections.defaultdict(set)
    for line in (data / "edges.jsonl").open(encoding="utf-8"):
        edge = json.loads(line)
        if edge["group"] == "genealogy":
            near[edge["source_id"]].add(edge["target_id"])
            near[edge["target_id"]].add(edge["source_id"])
    out = {}
    for doc in documents:
        portal = doc.split(":", 1)[1]
        if portal in seed:
            out[doc] = (sorted(seed[portal]), "seed")
            continue
        frontier, seen, votes, depth = {portal}, {portal}, collections.Counter(), 0
        while frontier and not votes and depth < DOMAIN_DEPTH:
            frontier = {n for d in frontier for n in near.get(d, ()) if n not in seen}
            seen |= frontier
            depth += 1
            votes = collections.Counter(f for d in frontier for f in seed.get(d, ()))
        top = max(votes.values(), default=0)   # the fields most of the nearest seeds share
        out[doc] = (sorted(f for f, n in votes.items() if n == top), f"quan_he_{depth}") if votes \
            else (["khac"], "khong_ro")
    return out


# ------------------------------------------------------------------ main

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    data = args.data
    base = data / "derived/vilextime"
    rows = [json.loads(line) for line in (base / "selected.jsonl").open(encoding="utf-8")]
    lineages = {r["lineage_id"] for r in rows}
    stats: collections.Counter[str] = collections.Counter()

    pool = {}
    for line in (data / "derived/vilextime_pool.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        if row["provision_id"] in lineages:
            pool[row["provision_id"]] = sorted(row["versions"], key=lambda v: v["ordinal"])
    db = sqlite3.connect(data / "temporal.sqlite")
    document_end = {doc: _d(end) for doc, end in db.execute("SELECT id, effective_to FROM documents")}

    # Same-document references, resolved once per (document, locator).
    resolver = TargetResolver(TemporalIndex(data / "temporal.sqlite"))
    cited: dict[str, list[str]] = {}
    for r in rows:
        ids = []
        for parts in references(r["answer"] or "", r["target"]):
            locator = ProvisionLocator(tuple(ProvisionReferencePart(lvl, parts[lvl]) for lvl in _ORDER if lvl in parts))
            result = resolver.resolve(TargetReference(f"{r['id']}:{parts}", str(parts), TargetScope.EXACT,
                                                      locator=locator), (r["target"]["document_id"],))
            if result.code.value.startswith("resolved"):
                ids += list(result.target.target_provision_ids)
                stats["dẫn chiếu: phân giải được"] += 1
            else:
                stats[f"dẫn chiếu: {result.code.value}"] += 1
        cited[r["id"]] = ids

    # One pass over the ~1 GB versions file for everything a row points at.
    wanted = {r["target"]["parent_id"] for r in rows if r["target"].get("parent_id")}
    wanted |= {pid for ids in cited.values() for pid in ids} | lineages
    chains: dict[str, list[dict]] = collections.defaultdict(list)
    pattern = re.compile(r'"provision_id"\s*:\s*"([^"]+)"')
    for line in (data / "derived/versions.jsonl").open(encoding="utf-8"):
        found = pattern.search(line)
        if found and found.group(1) in wanted:
            v = json.loads(line)
            chains[v["provision_id"]].append(v)
    for chain in chains.values():
        chain.sort(key=lambda v: v["ordinal"])

    events = {}
    want_events = {t["event_id"] for r in rows for t in r["derivation"]["transitions"]}
    want_events |= {chains[lid][-1]["ended_by_event_id"] for lid in lineages if chains.get(lid)} - {None}
    want_events |= {r["repealed_by"]["event_id"] for r in rows if r.get("repealed_by")}
    for line in (data / "derived/provision_events.jsonl").open(encoding="utf-8"):
        e = json.loads(line)
        if e["id"] in want_events:
            events[e["id"]] = e
    actors = {e["actor_id"] for e in events.values()}
    actor_nodes = {a: load_nodes(data, a.split(":", 1)[1]) for a in actors}
    actor_markers = {a: markers(nodes) for a, nodes in actor_nodes.items()}
    fields = domains(data, {r["target"]["document_id"] for r in rows})

    shorts = {}
    path = data / "vilextime/short_answers.jsonl"
    if path.exists():
        for line in path.open(encoding="utf-8"):
            s = json.loads(line)
            shorts[(s["lineage_id"], s["version_id"])] = s

    def at(pid: str, when: str) -> str | None:
        hit = in_force_at(chains.get(pid, []), date.fromisoformat(when))
        return hit["id"] if hit else None

    def enrich(r: dict) -> dict:
        lid, versions = r["lineage_id"], pool[r["lineage_id"]]
        parent = r["target"].get("parent_id")
        r["schema_version"] = SCHEMA_VERSION
        r.setdefault("as_of_strategy", "ranh_gioi")
        r.setdefault("twin_of", None)
        if parent and r["as_of_strategy"] == "giua_khoang":         # the lead-in in force at the twin's date
            hit = in_force_at(chains.get(parent, []), date.fromisoformat(r["as_of"]))
            r["target"]["lead_in"] = hit["text"] if hit else None
        texts = [v["text"] for v in versions]
        k = next((i for i, v in enumerate(versions) if v["id"] == r["version_id"]), None)
        r["changed_span"] = changed_span(texts, k) if k is not None else None
        evidence = []
        if r["version_id"]:
            evidence.append({"provision_id": lid, "version_id": r["version_id"], "role": "gold"})
        if parent and r["target"].get("lead_in") and (pv := at(parent, r["as_of"])):
            evidence.append({"provision_id": parent, "version_id": pv, "role": "lead_in"})
        for pid in cited[r["twin_of"] or r["id"]]:
            evidence.append({"provision_id": pid, "version_id": at(pid, r["as_of"]), "role": "reference"})
        r["evidence_set"] = evidence
        accepted = []
        if k == 0:
            accepted.append(f"asis:{lid}")
        for t in r["derivation"]["transitions"]:
            e = events.get(t["event_id"])
            t["op"] = e["operation"] if e else None
            if e and k is not None and t["to_version"] == versions[k]["ordinal"]:
                accepted.append(f"asis:{e['id']}")
        if r["version_id"] is None:     # the repeal: of the provision itself, or of the ancestor it fell with
            ended = (r.get("repealed_by") or {}).get("event_id") or (chains[lid][-1]["ended_by_event_id"]
                                                                      if chains.get(lid) else None)
            if ended in events:
                accepted.append(f"asis:{ended}")
        stats["accepted_evidence: " + ("có" if accepted else "rỗng")] += 1
        r["accepted_evidence"] = accepted
        r["domain"], r["domain_source"] = fields[r["target"]["document_id"]]
        acts = {events[t["event_id"]]["actor_id"] for t in r["derivation"]["transitions"] if t["event_id"] in events}
        r["legal_markers"] = sorted({m for a in acts for m in actor_markers.get(a, ())})
        s = shorts.get((lid, r["version_id"]))
        if s and not check_short_answer(s["short_answer"], r["answer"], r["target"].get("lead_in")):
            raise SystemExit(f"{r['id']}: short_answer không phải một đoạn của đáp án/câu dẫn: {s['short_answer']!r}")
        r["short_answer"] = s["short_answer"] if s else None
        return r

    out = []
    for r in rows:
        twin = twin_of(r, pool[r["lineage_id"]], document_end.get(r["target"]["document_id"]))
        stats["dòng anh em: có" if twin else "dòng anh em: không (cửa sổ rỗng hoặc chuỗi lệch)"] += 1
        out.append(enrich(r))
        if twin:
            out.append(enrich(twin))
    ids = [r["id"] for r in out]
    if len(ids) != len(set(ids)):
        raise SystemExit("id trùng trong release.jsonl")
    target = base / "release.jsonl"
    with target.open("w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(out):,} dòng ({len(rows):,} ranh giới + {len(out) - len(rows):,} giữa khoảng) -> {target}")
    for key, value in sorted(stats.items()):
        print(f"  {key}: {value:,}")
    print("  domain_source:", dict(collections.Counter(r["domain_source"].split("_")[0] for r in out[::1])))
    print("  legal_markers:", dict(collections.Counter(m for r in out for m in r["legal_markers"])))
    print(f"  short_answer: {sum(1 for r in out if r['short_answer'])}/{len(out)}")


if __name__ == "__main__":
    main()
