"""Build the Data in Brief release of ViLexTime from the locked final test set.

Inputs are read-only: the T1-fixed release (ADR 0006 amendment 19/11) and the
labelling provenance under data/review. Output: data/vilextime_dib/.

Changes versus data/vilextime_final (all listed in CHANGES.md of the output):
  1. T1 answers: leading enumeration marker removed (runs/posthoc_g4_20261113/t1_fix).
  2. F019 gold corrected per ADR 0006 §7 (lawyer blind read; TT 36/2026/TT-BXD).
  3. meta.review rewritten per lineage from the real provenance files.
  4. meta.question_source: Codex model recorded as author-reported gpt-6.1-sol.
  5. meta.domain / domain_source dropped (69% 'khac'); issuer_code added from law_id.

Run: python3 scripts/pipeline/build_dib_release.py   (prints counts, writes SHA256SUMS)
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "runs/posthoc_g4_20261113/t1_fix/release"
AI = ROOT / "data/review/ai_research"
GOLD = ROOT / "data/review"
OUT = ROOT / "data/vilextime_dib"

F019_ID = "vilextime:T2:provision:4cee6a60-eb71-11f0-ac45-154b0d915a56:2026-08-06"
CODEX_MODEL = "gpt-6.1-sol (author-reported; Codex CLI logs do not record the model)"


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


def tsv(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))


def ai_resolution():
    """lineage -> (batch, 'ai_agree' | 'ai_adjudicated' | 'author_override', author_review_channel)."""
    res = {}
    flips = json.load(open(AI / "2026-11-10_cmt_confirmed/cmt_confirmed.json"))["silver_flips"]
    for r in jl(AI / "2026-11-08_adjudication_final/silver_ai_final.jsonl"):
        src = "author_override" if r["lineage_id"] in flips else r["source"]
        res[r["lineage_id"]] = ("silver", src, "worksheet")
    for r in jl(AI / "2026-11-08_lo2/cmt_accepted_labels.jsonl"):
        res[r["lineage_id"]] = ("lo2", r["ai_decision_source"], "worksheet")
    for r in jl(AI / "2026-11-08_lo2/open_cases_for_CMT.jsonl"):
        res.setdefault(r["lineage_id"], ("lo2", "author_decided_open_case", "worksheet"))
    for r in jl(AI / "2026-11-08_supp18/cmt_accepted_labels.jsonl"):
        res[r["lineage_id"]] = ("supp", r["ai_decision_source"], "conversation")
    t1_adj = {r["lineage_id"] for r in jl(AI / "2026-11-11_t1_labels/adjudication.jsonl")}
    for lid in json.load(open(AI / "2026-11-11_t1_labels/cmt_confirmed_t1.json"))["t1_dat"]:
        res[lid] = ("t1", "ai_adjudicated" if lid in t1_adj else "ai_agree", "conversation")
    return res


def blind_gold():
    """lineage -> list of blind-reader records (round 1: annotators A/B; round 2: NMT + lawyer)."""
    g = {}
    for rnd, d in (("round1", GOLD), ("round2", GOLD / "gold_final")):
        key2lid = {r["khoa"]: r["lineage_id"] for r in tsv(d / "gold_sample.tsv")}
        readers = {"A": "annotator_A", "B": "annotator_B"} if rnd == "round1" else {"A": "NMT", "B": "lawyer"}
        for side, who in readers.items():
            p = d / f"gold_{side}.reveal.tsv"
            for r in tsv(p):
                lid = key2lid.get(r["khoa"])
                if lid:
                    g.setdefault(lid, []).append({"round": rnd, "reader": who, "agrees_with_store": r.get("dong_y", "").strip()})
    return g


def issuer_code(law_id):
    tail = law_id.split("/")[-1]
    return tail.split("-")[-1] if "-" in tail else tail.rstrip("0123456789") or tail


def main():
    rows = jl(BASE / "vilextime.jsonl")
    meta = jl(BASE / "vilextime_meta.jsonl")
    assert len(rows) == len(meta) == 722 and all(r["id"] == m["id"] for r, m in zip(rows, meta))
    prov, gold = ai_resolution(), blind_gold()

    missing = sorted({r["lineage_id"] for r in rows} - set(prov))
    assert not missing, f"no labelling provenance for {len(missing)} lineages: {missing[:3]}"

    for r, m in zip(rows, meta):
        lid = r["lineage_id"]
        batch, res, channel = prov[lid]
        m["review"] = {
            "status": "checked",
            "verdict": "dat",
            "guideline_version": "4.0",
            "labelers": ["AI-A (Claude Code)", "AI-B (Codex CLI)"],
            "ai_resolution": res,
            "author_review": f"every lineage reviewed by the first author ({channel})",
            "blind_gold": gold.get(lid, []),
            "batch": batch,
        }
        qs = m.get("question_source") or {}
        if "codex" in str(qs.get("provider", "")):
            qs["model"] = CODEX_MODEL
        m.pop("domain", None)
        m.pop("domain_source", None)
        m["issuer_code"] = issuer_code(m["target"]["law_id"])

        if r["id"] == F019_ID:
            assert r["answerable"] is True, "F019 already corrected?"
            r.update(answer=None, context=None, answerable=False, version_id=None, accepted_evidence=[])
            m.update(no_answer_reason="provision_repealed", in_force=False, repeal_mode="direct",
                     repealed_by="Thông tư 36/2026/TT-BXD, khoản 2 Điều 16 (hiệu lực 01/07/2026)")
            m.setdefault("flags", []).append("gold_corrected_by_blind_gold")

    OUT.mkdir(exist_ok=True)
    for name, data in (("vilextime.jsonl", rows), ("vilextime_meta.jsonl", meta)):
        with open(OUT / name, "w", encoding="utf-8") as f:
            for x in data:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    sums = "".join(f"{hashlib.sha256((OUT / n).read_bytes()).hexdigest()}  {n}\n"
                   for n in ("vilextime.jsonl", "vilextime_meta.jsonl"))
    (OUT / "SHA256SUMS").write_text(sums)

    lin = {}
    for r, m in zip(rows, meta):
        lin[r["lineage_id"]] = m["review"]
    print("rows", len(rows), "lineages", len(lin), "answerable", sum(r["answerable"] for r in rows))
    print("ai_resolution", Counter(v["ai_resolution"] for v in lin.values()))
    print("batch", Counter(v["batch"] for v in lin.values()))
    print("lineages with blind gold", sum(bool(v["blind_gold"]) for v in lin.values()),
          Counter(g["round"] + ":" + g["reader"] for v in lin.values() for g in v["blind_gold"]))
    print("issuer", Counter(m["issuer_code"] for m in meta).most_common(6))
    print(sums, end="")


if __name__ == "__main__":
    main()
