"""Build the Data in Brief release of ViLexTime from the locked final test set.

Inputs are read-only: the T1-fixed release (ADR 0006 amendment 19/11) and the
labelling provenance under data/review. Output: data/vilextime_dib/.

Changes versus data/vilextime_final (all listed in CHANGES.md of the output):
  1. T1 answers: leading enumeration marker removed (runs/posthoc_g4_20261113/t1_fix).
  2. F019 gold corrected per ADR 0006 §7 (lawyer blind read; TT 36/2026/TT-BXD).
  3. meta.review rewritten per lineage from the real provenance files.
  4. meta.question_source: Codex model recorded as author-reported gpt-6.1-sol.
  5. meta.domain / domain_source dropped (69% 'khac'); issuer_code added from law_id.
  6. meta.schema_version 3.0.0.
  7. meta.review.labelers per run (real runtime/model), and annotation/ exported:
     raw AI labels, adjudication records, worksheets shown to the agents, blind-reading sheets.

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


CLAUDE_OPUS = "Claude Code / claude-opus-5-5"
CODEX_CLI = "Codex CLI / " + CODEX_MODEL
CODEX_NATIVE = "Codex native subagent / " + CODEX_MODEL
# Production label runs (same a.jsonl/b.jsonl as scripts/check/audit_g2_statistics.py, plus T1).
RUNS = [
    ("silver01", AI / "2026-11-07_adjudication_all/snapshots/silver01", CLAUDE_OPUS, CLAUDE_OPUS),
    ("round2_codex", AI / "2026-11-06_silver/round2_codex", CODEX_NATIVE, CODEX_NATIVE),
    ("round3_mixed", AI / "2026-11-06_silver/round3_mixed", CLAUDE_OPUS, CODEX_CLI),
    ("lo2", AI / "2026-11-08_lo2/schema_validated", CLAUDE_OPUS, CODEX_CLI),
    ("supp18", AI / "2026-11-08_supp18", CLAUDE_OPUS, CODEX_CLI),
    ("t1", AI / "2026-11-11_t1_labels", "Claude Code / claude-sonnet-5-5", CODEX_CLI),
]
ADJUDICATION = [AI / "2026-11-07_adjudication_all/results", AI / "2026-11-08_lo2/schema_validated/adjudication.jsonl",
                AI / "2026-11-08_lo2/open_cases_for_CMT.jsonl", AI / "2026-11-08_supp18/adjudication.jsonl", AI / "2026-11-11_t1_labels/adjudication.jsonl"]
GOLD_DROP = {"ly_do", "ghi_chu_mo", "phut", "ghi_chu", "stage1_sha256"}  # free notes and timing: not released

# Verbatim prompts, agent definitions and guideline (initials such as CMT = the reviewing author are kept).
PROMPTS = [
    ("data/review/ai_research/2026-11-06_silver/prompts", "labelling/silver"),
    ("data/review/ai_research/2026-11-08_lo2/prompts", "labelling/lo2"),
    ("data/review/ai_research/2026-11-08_supp18/prompts", "labelling/supp18"),
    ("data/review/ai_research/2026-11-11_t1_labels/prompts", "labelling/t1"),
    ("data/review/ai_research/codex_b_wrapper.md", "labelling/codex_b_wrapper.md"),
    ("data/review/ai_research/2026-11-07_adjudication_all/prompts", "adjudication/silver"),
    ("data/review/ai_research/2026-11-08_lo2/adjudication/prompts", "adjudication/lo2"),
    (".claude/agents/legal-annotator-a.md", "agents/legal-annotator-a.md"),
    (".claude/agents/legal-annotator-b.md", "agents/legal-annotator-b.md"),
    (".claude/agents/legal-adjudicator.md", "agents/legal-adjudicator.md"),
    (".claude/skills/vilextime-ai-labeling/SKILL.md", "agents/skill-vilextime-ai-labeling.md"),
    (".claude/skills/vn-legal-research/SKILL.md", "agents/skill-vn-legal-research.md"),
    ("docs/vilextime-annotation.md", "../guideline_v4.0_vi.md"),
    ("docs/vilextime-dinh-nghia.md", "../dataset_definition_vi.md"),
]

YES_NO = {"có": True, "co": True, "không": False, "khong": False}  # "" (not recorded) -> None


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


def extra_ai_checks():
    """lineage -> AI adjudicator re-checks after the author's review (legal-adjudicator agent, author-delegated)."""
    out = {}
    for step, d, what in (("H7", "2026-11-11_h7", "re-check of lineages the author marked unsure or corrected"),
                          ("R2", "2026-11-11_t6_r2", "relocation check of repealed content (T6)")):
        for f in sorted((AI / d).glob("out_batch*.jsonl")):
            for r in jl(f):
                out.setdefault(r["lineage_id"], []).append({"step": step, "what": what, "agent": "legal-adjudicator / " + CLAUDE_OPUS})
    return out


def blind_gold():
    """lineage -> list of blind-reader records (round 1: annotators A/B; round 2: NMT + lawyer)."""
    g = {}
    for rnd, d in (("round1", GOLD), ("round2", GOLD / "gold_final")):
        key2lid = {r["khoa"]: r["lineage_id"] for r in tsv(d / "gold_sample.tsv")}
        readers = {"A": "annotator_A", "B": "annotator_B"} if rnd == "round1" else {"A": "coauthor_reader", "B": "lawyer"}  # roles only, no names (schema rule)
        for side, who in readers.items():
            p = d / f"gold_{side}.reveal.tsv"
            for r in tsv(p):
                lid = key2lid.get(r["khoa"])
                if lid:
                    agree, basis = YES_NO.get(r.get("dong_y", "").strip()), "reader_judgement"
                    if agree is None and r.get("kg_hieu_luc", "").strip():  # lawyer sheet: compare in-force status only
                        agree, basis = r["hieu_luc"].strip() == r["kg_hieu_luc"].strip(), "in_force_status_only"
                    g.setdefault(lid, []).append({"round": rnd, "reader": who, "agrees_with_store": agree, "basis": basis})
    return g


def raw_labels(final):
    """Raw pre-adjudication AI labels of the final lineages, tagged with run and agent."""
    out, run_of = [], {}
    for run, d, agent_a, agent_b in RUNS:
        for side, agent in (("a", agent_a), ("b", agent_b)):
            for r in jl(d / f"{side}.jsonl"):
                if r["lineage_id"] in final:
                    assert run_of.setdefault(r["lineage_id"], run) == run, r["lineage_id"]
                    out.append({"run": run, "agent": agent, **r})
    agents = {run: [a, b] for run, _, a, b in RUNS}
    return out, {lid: agents[run] for lid, run in run_of.items()}


def export_annotation(final, labels):
    ann = OUT / "annotation"
    ann.mkdir(parents=True, exist_ok=True)
    adj = [r for p in ADJUDICATION for f in ([p] if p.is_file() else sorted(p.glob("*.jsonl")))
           for r in jl(f) if r.get("lineage_id") in final]
    ws = {}
    for run, d, *_ in RUNS:
        src = d if (d / "input").exists() else d.parent
        for f in sorted((src / "input").glob("chunk*.jsonl")):
            for r in jl(f):
                lid = r.get("lineage_id") or r.get("record", {}).get("lineage_id")
                if lid in final:
                    ws.setdefault(lid, {"run": run, **r})
    post = [{"step": step, **r} for step, d in (("H7", "2026-11-11_h7"), ("R2", "2026-11-11_t6_r2"))
            for f in sorted((AI / d).glob("out_batch*.jsonl")) for r in jl(f) if r["lineage_id"] in final]
    for name, data in (("ai_labels_raw.jsonl", labels), ("adjudication.jsonl", adj), ("post_review_ai_checks.jsonl", post),
                       ("worksheets.jsonl", list(ws.values()))):
        with open(ann / name, "w", encoding="utf-8") as f:
            for x in data:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    for rnd, d, readers in (("round1", GOLD, ("annotator_A", "annotator_B")),
                            ("round2", GOLD / "gold_final", ("coauthor_reader", "lawyer"))):
        key2lid = {r["khoa"]: r["lineage_id"] for r in tsv(d / "gold_sample.tsv")}
        for side, who in zip("AB", readers):
            rows = [{"lineage_id": key2lid[r["khoa"]], **{k: v for k, v in r.items() if k not in GOLD_DROP}}
                    for r in tsv(d / f"gold_{side}.reveal.tsv") if key2lid.get(r["khoa"]) in final]
            with open(ann / f"blind_reading_{rnd}_{who}.tsv", "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
                w.writeheader()
                w.writerows(rows)
    import shutil
    for src, dst in PROMPTS:
        src = ROOT / src
        target = ann / "prompts" / dst
        if src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
    return len(adj), len(ws)


def issuer_code(law_id):
    tail = law_id.split("/")[-1]
    code = tail.split("-")[-1]
    return code.rstrip("0123456789") or code  # QH15, UBTVQH11 -> QH, UBTVQH


def main():
    rows = jl(BASE / "vilextime.jsonl")
    meta = jl(BASE / "vilextime_meta.jsonl")
    assert len(rows) == len(meta) == 722 and all(r["id"] == m["id"] for r, m in zip(rows, meta))
    prov, gold, extra = ai_resolution(), blind_gold(), extra_ai_checks()
    final = {r["lineage_id"] for r in rows}
    labels, agents = raw_labels(final)

    missing = sorted({r["lineage_id"] for r in rows} - set(prov))
    assert not missing, f"no labelling provenance for {len(missing)} lineages: {missing[:3]}"
    assert set(agents) == final, f"no raw AI labels for {len(final - set(agents))} lineages"

    for r, m in zip(rows, meta):
        lid = r["lineage_id"]
        batch, res, channel = prov[lid]
        m["review"] = {
            "status": "checked",
            "verdict": "dat",
            "guideline_version": "4.0",
            "labelers": agents[lid],
            "ai_resolution": res,
            "author_review": f"every lineage reviewed by one author ({channel})",
            "post_review_ai_checks": extra.get(lid, []),
            "blind_gold": gold.get(lid, []),
            "batch": batch,
        }
        qs = m.get("question_source") or {}
        if "codex" in str(qs.get("provider", "")):
            qs["model"] = CODEX_MODEL
        sas = m.get("short_answer_source") or {}
        if "codex" in str(sas.get("by", "")).lower():
            sas["by"] = CODEX_MODEL
        m["schema_version"] = "3.0.0"  # gold (F019) and schema changed: MAJOR per ADR 0003 §8
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

    n_adj, n_ws = export_annotation(final, labels)
    print("annotation: raw labels", len(labels), "adjudication records", n_adj, "worksheets", n_ws)
    lin = {}
    for r, m in zip(rows, meta):
        lin[r["lineage_id"]] = m["review"]
    print("rows", len(rows), "lineages", len(lin), "answerable", sum(r["answerable"] for r in rows))
    print("ai_resolution", Counter(v["ai_resolution"] for v in lin.values()))
    print("post-review AI checks", Counter(c["step"] for v in lin.values() for c in v["post_review_ai_checks"]))
    print("batch", Counter(v["batch"] for v in lin.values()))
    print("lineages with blind gold", sum(bool(v["blind_gold"]) for v in lin.values()),
          Counter(g["round"] + ":" + g["reader"] for v in lin.values() for g in v["blind_gold"]))
    print("issuer", Counter(m["issuer_code"] for m in meta).most_common(6))
    print(sums, end="")


if __name__ == "__main__":
    main()
