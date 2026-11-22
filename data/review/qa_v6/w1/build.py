"""W1: blind reading that covers every (lineage, answer state) of release 6.0.0 (pre-registration §1).

State = version_id, or NO_ANSWER for rows with no provision in force. Covered = a state some earlier blind round
read (meta.review.blind_gold.as_of_read). Two earlier reads sit on dates that build_dib_release.py later moved
(interval fixes); MOVED maps them to the row's new date, same version.

W1a: one row per lineage nobody has read, random.Random("20261122:w1a:<lineage>").choice(rows by as_of).
W1b: every state still uncovered after W1a, the row with the latest as_of in that state.
Order: random.Random("20261122:w1:order") shuffles W1a, then W1b, redrawing until no two rows of one lineage sit
next to each other inside a lot. Lot 1 = W1a; W1b is cut into lots of about 55.

Writes w1/lo<k>/ with release_joined.jsonl, gold_sample.tsv (NOT for readers), gold_{A,B}.tsv and .xlsx.
Refuses to overwrite a sheet that already has answers. Run from repo root: python3 data/review/qa_v6/w1/build.py
Import a returned lot:  python3 scripts/review/independent_gold.py import A --review data/review/qa_v6/w1/lo1 --require-minutes
"""
import collections
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REL = ROOT / "data/vilextime_dib"
sys.path.insert(0, str(ROOT / "scripts/review"))
import independent_gold as ig  # noqa: E402

MOVED = {("provision:7ba9e014-eb7b-11f0-954d-af330569649d", "2020-04-04"): "2015-08-13",
         ("provision:a16089ba-2d53-11f1-87d7-6598c119b283", "2017-04-29"): "2015-12-23"}
LOT = 55


def state(r):
    return r["version_id"] or "NO_ANSWER"


def draw(rows, meta):
    by = collections.defaultdict(list)
    for r, m in zip(rows, meta):
        by[r["lineage_id"]].append((r, m))
    covered = collections.defaultdict(set)
    for lid, l in by.items():
        for g in l[0][1]["review"]["blind_gold"]:
            day = MOVED.get((lid, g["as_of_read"]), g["as_of_read"])
            hit = [r for r, _ in l if r["as_of"] == day]
            assert hit, (lid, day)
            covered[lid].add(state(hit[0]))
    before = sum(len(v) for v in covered.values())
    w1a = []
    for lid in sorted(l for l in by if not covered[l]):
        r, m = random.Random(f"20261122:w1a:{lid}").choice(sorted(by[lid], key=lambda x: x[0]["as_of"]))
        w1a.append((r, m))
        covered[lid].add(state(r))
    w1b = []
    for lid, l in by.items():
        for st in sorted({state(r) for r, _ in l} - covered[lid]):
            w1b.append(max([(r, m) for r, m in l if state(r) == st], key=lambda x: x[0]["as_of"]))
    total = sum(len({state(r) for r, _ in l}) for l in by.values())
    return w1a, w1b, before, total


def lots(w1a, w1b):
    rng = random.Random("20261122:w1:order")

    def shuffled(items, size):
        while True:
            rng.shuffle(items)
            parts = [items[i:i + size] for i in range(0, len(items), size)]
            if all(a[0]["lineage_id"] != b[0]["lineage_id"] for p in parts for a, b in zip(p, p[1:])):
                return parts
    n = -(-len(w1b) // LOT)  # lots of about LOT rows, sizes differ by at most one
    size = -(-len(w1b) // n)
    return shuffled(list(w1a), len(w1a)) + shuffled(list(w1b), size)


def main():
    rows = [json.loads(x) for x in open(REL / "vilextime.jsonl", encoding="utf-8")]
    meta = [json.loads(x) for x in open(REL / "vilextime_meta.jsonl", encoding="utf-8")]
    w1a, w1b, before, total = draw(rows, meta)
    # Expected numbers are the pre-registered ones (§1); a mismatch means the release or the rule changed.
    assert (total, before, len(w1a), len(w1b)) == (362, 135, 64, 163), (total, before, len(w1a), len(w1b))
    assert collections.Counter(r["group"] for r, _ in w1a) == {"two_versions": 35, "control": 29}
    assert collections.Counter(r["group"] for r, _ in w1b) == {"two_versions": 128, "repealed": 23, "multi_versions": 12}
    for sheet in "AB":
        for k in range(1, 6):
            ig.refuse_if_labelled(HERE / f"lo{k}/gold_{sheet}.tsv", ig.FILLED)
    summary = []
    for k, part in enumerate(lots(w1a, w1b), 1):
        out = HERE / f"lo{k}"
        out.mkdir(exist_ok=True)
        joined = [{**r, **{f: m[f] for f in ("target", "source_url", "valid_from", "valid_to", "no_answer_reason")},
                   "answer": r["context"], "short_answer": r["answer"]} for r, m in part]
        with open(out / "release_joined.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(p, ensure_ascii=False) + "\n" for p in joined)
        keys = [f"L{k}-{i:03d}" for i in range(1, len(part) + 1)]
        ig.write(out / "gold_sample.tsv", ["khoa", "id", "lineage_id", "group", "as_of_strategy", "wave", "state"],
                 [{"khoa": key, "id": p["id"], "lineage_id": p["lineage_id"], "group": p["group"],
                   "as_of_strategy": p["as_of_strategy"], "wave": "W1a" if k == 1 else "W1b", "state": state(p)}
                  for key, p in zip(keys, joined)])
        sheet_rows = [{"khoa": key, "cau_hoi": p["question"], "ngay_hoi": p["as_of"],
                       "van_ban": " ".join(p["target"]["document_title"].split()), "dieu_khoan": p["target"]["citation"],
                       "link": p["source_url"],
                       "van_ban_tac_dong_theo_cong": ig.actors(ROOT / "data", p["target"]["document_id"])}
                      for key, p in zip(keys, joined)]
        ig.REVIEW = out
        for sheet in "AB":
            ig.write(out / f"gold_{sheet}.tsv", ig.SHEET, sheet_rows)
            ig.export(ROOT / "data", sheet)
        summary.append((k, len(part), dict(collections.Counter(p["group"] for p in joined)),
                        sum(not p["answerable"] for p in joined)))
    for s in summary:
        print("lô %d: %d dòng, nhóm %s, không đáp án %d" % s)


if __name__ == "__main__":
    main()
