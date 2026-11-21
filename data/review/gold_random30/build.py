"""Random blind check of the released ViLexTime (21/11/2026).

Why: the 105 lineages read blind so far were not a random sample of the release, so their error rate does
not stand for the whole dataset. Here 30 of the 94 lineages nobody has read blind are drawn at random (fixed
seed), one row each, drawn at random among the lineage's rows (both date modes), so the error rate is an
unbiased estimate for those 94 rows' population; combined with the 105 it gives a whole-release estimate.
The same 30 rows go to three readers (A, B, C) independently, which also allows an Alternative Annotator
Test of the AI labels (Calderon et al.) and human-human agreement with three readers.

Reads the release built by scripts/pipeline/build_dib_release.py. Writes, in this directory:
  release_joined.jsonl  the 30 rows, row + meta joined in the shape independent_gold.py reveal expects
  gold_sample.tsv       key -> row id (NOT for the readers)
  gold_A.tsv, gold_B.tsv, gold_C.tsv   identical blind sheets
then exports gold_{A,B,C}.xlsx. Refuses to overwrite a sheet that already has answers.

Run from the repository root:  python3 data/review/gold_random30/build.py
After a reader returns a file:  python3 scripts/review/independent_gold.py import A --review data/review/gold_random30
                                python3 scripts/review/independent_gold.py reveal A --review data/review/gold_random30 \
                                    --release data/review/gold_random30/release_joined.jsonl
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/review"))
import independent_gold as ig  # noqa: E402

OUT = Path(__file__).resolve().parent
REL = ROOT / "data/vilextime_dib"
SEED = "20261121:random30"
N = 30
READERS = "ABC"


def main():
    rows = [json.loads(x) for x in open(REL / "vilextime.jsonl", encoding="utf-8")]
    meta = [json.loads(x) for x in open(REL / "vilextime_meta.jsonl", encoding="utf-8")]
    by_lineage = {}
    for r, m in zip(rows, meta):
        if not m["review"]["blind_gold"]:
            by_lineage.setdefault(r["lineage_id"], []).append((r, m))
    pool = sorted(by_lineage)
    assert len(pool) == 94, f"expected 94 unread lineages, found {len(pool)}"
    random.Random(SEED).shuffle(pool)
    picked = []
    for lid in pool[:N]:
        r, m = random.Random(f"{SEED}:{lid}").choice(sorted(by_lineage[lid], key=lambda x: x[0]["as_of"]))
        picked.append({**r, **{k: m[k] for k in ("target", "source_url", "valid_from", "valid_to", "no_answer_reason")},
                       "answer": r["context"], "short_answer": r["answer"]})
    random.Random(SEED).shuffle(picked)  # sheet order unrelated to group or date
    for sheet in READERS:
        ig.refuse_if_labelled(OUT / f"gold_{sheet}.tsv", ig.FILLED)
    with open(OUT / "release_joined.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(p, ensure_ascii=False) + "\n" for p in picked)
    keys = [f"R{i:02d}" for i in range(1, N + 1)]
    ig.write(OUT / "gold_sample.tsv", ["khoa", "id", "lineage_id", "group", "as_of_strategy", "annotators"],
             [{"khoa": k, "id": p["id"], "lineage_id": p["lineage_id"], "group": p["group"],
               "as_of_strategy": p["as_of_strategy"], "annotators": READERS} for k, p in zip(keys, picked)])
    sheet_rows = [{"khoa": k, "cau_hoi": p["question"], "ngay_hoi": p["as_of"],
                   "van_ban": " ".join(p["target"]["document_title"].split()), "dieu_khoan": p["target"]["citation"],
                   "link": p["source_url"], "van_ban_tac_dong_theo_cong": ig.actors(ROOT / "data", p["target"]["document_id"])}
                  for k, p in zip(keys, picked)]
    ig.REVIEW = OUT
    for sheet in READERS:
        ig.write(OUT / f"gold_{sheet}.tsv", ig.SHEET, sheet_rows)
        ig.export(ROOT / "data", sheet)
    from collections import Counter
    print("groups", dict(Counter(p["group"] for p in picked)), "modes", dict(Counter(p["as_of_strategy"] for p in picked)),
          "answerable", sum(p["answerable"] for p in picked))


if __name__ == "__main__":
    main()
