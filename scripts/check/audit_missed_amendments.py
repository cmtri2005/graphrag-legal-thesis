#!/usr/bin/env python3
"""Find amendments/repeals the versioned store may have missed (the F016/F060 error class).

For every released lineage: take every document that vbpl's "Lược đồ" lists as amending, repealing,
replacing, suspending or correcting the target document (cached data/diagrams/<id>.json). An amender
whose effective date is not a boundary the store already knows for that lineage, and that takes effect
before the lineage's last as_of, is a candidate if its official text (cached data/raw/<id>.json) cites
the target Article. Offline, no network, no LLM. Candidates need a source check; they are not errors.

Usage: python3 scripts/check/audit_missed_amendments.py [RELEASE_DIR] [OUT_TSV]
"""
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REL = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/vilextime_dib"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "runs/audit_missed_amendments/candidates.tsv"
# documentNamesBySource codes: the source acts on the target (data/reference_type_map.json)
ACTING = {"10": "amend", "1": "repeal", "12": "replace", "5": "suspend", "11": "suspend", "6": "correct"}
TAG = re.compile(r"<[^>]+>")
NUM = r"(\d{1,4}\s*/\s*\d{4}\s*/\s*[A-ZĐ][A-ZĐ0-9\-]*)"
HEAD = re.compile(rf"Điều\s+\d+[a-z]?\s*\.\s[^“\"]{{0,250}}?{NUM}")
OF_DOC = re.compile(rf"\s*(?:của|tại|trong)\s+(?:Luật|Bộ luật|Nghị định|Thông tư(?: liên tịch)?|Quyết định|Nghị quyết)\s+(?:số\s+)?{NUM}")


def docnum(s):
    """Number/year/first letter of type: robust to "TT- BNNPTNT" spacing and typos in the issuer code."""
    n = re.sub(r"\s+", "", s).upper()
    return "/".join(n.split("/")[:2]) + "/" + n.split("/")[2][:1]


def text_of(doc_id):
    p = ROOT / "data/raw" / f"{doc_id}.json"
    if not p.exists():
        return None, None, None
    d = json.loads(p.read_text(encoding="utf-8"))
    c = d.get("documentContent") or ""
    if isinstance(c, dict):
        c = c.get("content") or ""
    body = " ".join(html.unescape(TAG.sub(" ", c)).split())
    return body, (d.get("effFrom") or "")[:10], d.get("docNum") or ""


def cites(body, law_id, art, clause, point):
    """Strength of the best citation of the target provision in the amender's text, with a snippet.
    'article' needs the target law number somewhere before it (multi-document amenders)."""
    num = law_id.split("/")[0]
    target = docnum(law_id)
    # amender Articles that name the document they act on ("Điều 29. ... Thông tư số 52/2022/TT-BGTVT")
    heads = [(h.start(), docnum(h.group(1))) for h in HEAD.finditer(body)]
    best = (None, "")
    for m in re.finditer(rf"Điều\s+{re.escape(art)}(?![\d\w])", body, re.I):
        if law_id.lower() not in body[:m.start()].lower() and num not in body[:m.start()]:
            continue
        after = OF_DOC.match(body, m.end())
        if after and docnum(after.group(1)) != target:
            continue  # "Điều 7 của Nghị định số 59/2005/NĐ-CP": another document
        prev = [d for pos, d in heads if pos < m.start()]
        if not after and prev and prev[-1] != target:
            continue  # inside the amender's Article for another document
        # the citation phrase right before "Điều A", back to the last sentence break
        before = re.split(r"[.;:]", body[max(0, m.start() - 120):m.start()].lower())[-1]
        clauses = re.findall(r"khoản\s+(\d+[a-zđ]?)", before)
        clauses += [c for g in re.findall(r"khoản\s+\d+[a-zđ]?((?:\s*(?:,|và)\s*\d+[a-zđ]?)+)", before)
                    for c in re.findall(r"\d+[a-zđ]?", g)]
        points = [p for g in re.findall(r"điểm\s+([a-zđ](?:\s*(?:,|và)\s*[a-zđ](?![\w]))*)", before)
                  for p in re.findall(r"[a-zđ]", g)]
        if clauses and clause not in clauses:
            continue  # cites another clause of the same Article
        level = "article"
        if clauses:
            level = "clause"
            if points and point not in points:
                continue  # another point of the same clause
            if points:
                level = "point"
        rank = {"article": 1, "clause": 2, "point": 3}[level]
        if best[0] is None or rank > {"article": 1, "clause": 2, "point": 3}[best[0]]:
            best = (level, body[max(0, m.start() - 250):m.end() + 350])
    return best


def main():
    rows = [json.loads(x) for x in open(REL / "vilextime.jsonl", encoding="utf-8")]
    meta = [json.loads(x) for x in open(REL / "vilextime_meta.jsonl", encoding="utf-8")]
    lin = defaultdict(list)
    for r, m in zip(rows, meta):
        lin[r["lineage_id"]].append((r, m))
    out, stats = [], defaultdict(int)
    for lid, items in lin.items():
        t = items[0][1]["target"]
        doc = t["document_id"].split(":", 1)[1]
        known = {d for _, m in items for d in (m["valid_from"], m["valid_to"]) if d}
        known |= {tr["actor"]["effective_from"] for _, m in items for tr in m["derivation"]["transitions"]}
        known_docs = {tr["actor"]["document_id"].split(":", 1)[1] for _, m in items for tr in m["derivation"]["transitions"]}
        last = max(r["as_of"] for r, _ in items)
        first = min(m["valid_from"] or r["as_of"] for r, m in items)
        diag = json.loads((ROOT / "data/diagrams" / f"{doc}.json").read_text(encoding="utf-8"))
        for code, op in ACTING.items():
            for x in diag.get("documentNamesBySource", {}).get(code, []):
                xid = x["id"]
                stats["acting_pairs"] += 1
                if xid in known_docs:
                    continue
                body, eff, num = text_of(xid)
                base = {"lineage_id": lid, "group": items[0][0]["group"], "law_id": t["law_id"],
                        "citation": t["citation"], "relation": op, "actor_id": xid, "actor": x["name"][:90],
                        "actor_eff": eff or "", "first_as_of": min(r["as_of"] for r, _ in items), "last_as_of": last}
                if body is None:
                    stats["no_text"] += 1
                    out.append({**base, "strength": "no_text", "snippet": ""})
                    continue
                if eff and (eff > last or eff < first):
                    stats["outside_window"] += 1
                    continue
                if eff in known:
                    stats["explained_by_known_date"] += 1
                    continue
                level, snip = cites(body, t["law_id"], t["article_id"], t["clause_id"], t["point_id"])
                if level is None:
                    if op in ("repeal", "replace") and len(body) < 400_000:
                        stats["doc_level_no_article_cite"] += 1
                        out.append({**base, "strength": "doc_level", "snippet": body[:400]})
                    continue
                stats[f"cite_{level}"] += 1
                out.append({**base, "strength": level, "snippet": snip})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = ["strength", "lineage_id", "group", "law_id", "citation", "relation", "actor_id", "actor",
            "actor_eff", "first_as_of", "last_as_of", "snippet"]
    order = {"point": 0, "clause": 1, "article": 2, "doc_level": 3, "no_text": 4}
    out.sort(key=lambda o: (order[o["strength"]], o["lineage_id"]))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for o in out:
            f.write("\t".join(str(o[c]).replace("\t", " ").replace("\n", " ") for c in cols) + "\n")
    print("lineages", len(lin), dict(stats))
    print("candidates", len(out), "lineages", len({o["lineage_id"] for o in out}),
          {k: sum(o["strength"] == k for o in out) for k in order})
    return out


if __name__ == "__main__":
    res = main()
    # self-check on the uncorrected thesis release: the known F016 miss (NĐ 92/2017 on NĐ 20/2008 Điều 20)
    # must be caught. Run: audit_missed_amendments.py runs/posthoc_g4_20261113/t1_fix/release /tmp/x.tsv
    if REL.resolve() == ROOT / "runs/posthoc_g4_20261113/t1_fix/release":
        assert any(o["lineage_id"].endswith("7ba9e014-eb7b-11f0-954d-af330569649d") and o["actor_id"] == "146942"
                   and o["strength"] in ("point", "clause", "article") for o in res), "F016 not caught"
        print("self-check: F016 caught")
