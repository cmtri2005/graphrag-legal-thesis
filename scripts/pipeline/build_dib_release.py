"""Build the Data in Brief release of ViLexTime from the locked final test set.

Inputs are read-only: the T1-fixed release (ADR 0006 amendment 19/11) and the
labelling provenance under data/review. Output: data/vilextime_dib/.

Changes versus data/vilextime_final (all listed in CHANGES.md of the output):
  1. T1 answers: leading enumeration marker removed (runs/posthoc_g4_20261113/t1_fix).
  2. F019 gold corrected per ADR 0006 §7 (lawyer blind read; TT 36/2026/TT-BXD).
  3. meta.review rewritten per lineage from the real provenance files.
  4. meta.question_source: Codex model recorded as author-reported gpt-6.1-sol.
  5. meta.domain / domain_source dropped (69% 'khac'); issuer_code added from law_id.
  6. meta.schema_version 4.0.0.
  8. Descriptive group names replace the thesis codes T1/T2/T3/T6 (GROUP_NAMES), also inside ids and twin_of;
     date modes ranh_gioi/giua_khoang become boundary/mid_interval (DATE_MODES).
  9. Store errors of the missed-amendment class corrected (STORE_FIXES; audit: scripts/check/audit_missed_amendments.py,
     runs/audit_missed_amendments/NOTE.md). A version that ended earlier than the store recorded gets its true end; a
     row dated after that end moves to the middle of its version's true interval (same answer, same labels).
  7. meta.review.labelers per run (real runtime/model), and annotation/ exported:
     raw AI labels, adjudication records, worksheets shown to the agents, blind-reading sheets.
 10. 6.0.0: review.high_risk_lawyer_check renamed review.high_risk_ai_author_check (no lawyer took part);
     blind_gold records name the date read (as_of_read) and include round 3 (random 30, compared by machine);
     annotation/excluded_lineages.jsonl lists the 175 labelled-but-removed lineages with step and reason codes.

Run: python3 scripts/pipeline/build_dib_release.py   (prints counts, writes SHA256SUMS)
"""
import csv
import re
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "runs/posthoc_g4_20261113/t1_fix/release"
AI = ROOT / "data/review/ai_research"
GOLD = ROOT / "data/review"
GOLD_DOT3 = GOLD / "gold_dot3_highrisk"  # high-risk augmentation (AI-proposed, CMT-verified; not blind)
OUT = ROOT / "data/vilextime_dib"

F019_ID = "vilextime:T2:provision:4cee6a60-eb71-11f0-ac45-154b0d915a56:2026-08-06"
# Missed amendments/repeals (the store kept a version beyond its real end). Source: official text cached from
# the vbpl gateway (data/raw/<actor>.json). Fields: lineage, true end of the version the store kept too long,
# actor, rows to move {old as_of: version ordinal}; F060 also re-dates the change itself (store had 2019-03-01,
# a re-enactment with the same wording by TT 02/2019).
STORE_FIXES = [
    dict(lineage="provision:7ba9e014-eb7b-11f0-954d-af330569649d", ordinal=2, end="2017-09-25",  # F016
         actor=("92/2017/NĐ-CP", "document:146942"), basis="khoản 9 Điều 2 NĐ 92/2017/NĐ-CP sửa Điều 20 NĐ 20/2008/NĐ-CP",
         move={"2020-04-04": 2}),
    dict(lineage="provision:e9f1fcba-eb70-11f0-ae55-77d3c9eccbbe#k1#%C4%91", ordinal=1, end="2012-08-10",
         actor=("53/2012/NĐ-CP", "document:27642"), basis="khoản 4 Điều 3 NĐ 53/2012/NĐ-CP sửa Điều 7 NĐ 33/2010/NĐ-CP",
         move={"2015-12-30": 1}),
    dict(lineage="provision:b69cb980-2c7b-11f1-8056-01cda9906453", ordinal=2, end="2021-02-01",
         actor=("145/2020/NĐ-CP", "document:152668"), basis="khoản 2 Điều 114 NĐ 145/2020/NĐ-CP: NĐ 05/2015/NĐ-CP hết hiệu lực",
         move={"2022-05-12": 2}),
    dict(lineage="provision:e23c54c0-3634-11f1-9175-9b33751e108f", ordinal=2, end="2014-02-15",
         actor=("221/2013/NĐ-CP", "document:32938"), basis="khoản 4 Điều 42 NĐ 221/2013/NĐ-CP bãi bỏ Chương IV NĐ 135/2004/NĐ-CP",
         move={"2017-10-20": 2}),
]
F060 = dict(lineage="provision:a16089ba-2d53-11f1-87d7-6598c119b283", change="2017-03-01",
            actor=("32/2016/TT-NHNN", "document:117004", "2016-12-26"),
            basis="khoản 2 Điều 1 TT 32/2016/TT-NHNN sửa khoản 1 Điều 4 TT 23/2014/TT-NHNN",
            move={"2019-02-28": "2017-02-28", "2019-03-01": "2017-03-01", "2017-04-29": None})  # None: middle of v1
FIX_FLAG = "store_corrected_missed_amendment"


def mid(start, end):
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    return (a + (b - a) / 2).isoformat()


def apply_store_fixes(rows, meta):
    """Correct rows of STORE_FIXES and F060 in place (thesis ids); return {old id: new id}."""
    renamed = {}

    def move(r, m, new):
        old = r["id"]
        r["as_of"] = new
        r["id"] = m["id"] = old.rsplit(":", 1)[0] + ":" + new
        m["derivation"]["query"] = f"as_of({r['lineage_id']}, {new})"
        renamed[old] = r["id"]

    for fx in STORE_FIXES:
        hit = 0
        for r, m in zip(rows, meta):
            if r["lineage_id"] != fx["lineage"]:
                continue
            m.setdefault("flags", []).append(FIX_FLAG)
            m["store_correction"] = f"version ends {fx['end']} ({fx['basis']}); store had {m['valid_to']}"
            if r["version_id"] and r["version_id"].endswith(f":{fx['ordinal']}"):
                m["valid_to"] = fx["end"]
            if r["as_of"] in fx["move"]:
                assert r["version_id"].endswith(f":{fx['move'][r['as_of']]}"), r["id"]
                move(r, m, mid(m["valid_from"], fx["end"]))
                hit += 1
        assert hit == len(fx["move"]), f"{fx['lineage']}: moved {hit}"

    p, (law, doc, signed) = F060["lineage"], F060["actor"]
    tr = {"on": F060["change"], "from_version": 1, "to_version": 2, "event_id": None,
          "actor": {"law_id": law, "document_id": doc, "effective_from": F060["change"]}, "op": "amend"}
    hit = 0
    for r, m in zip(rows, meta):
        if r["lineage_id"] != p:
            continue
        m.setdefault("flags", []).append(FIX_FLAG)
        m["store_correction"] = (f"change on {F060['change']} ({F060['basis']}); store had 2019-03-01, "
                                 "a re-enactment with the same wording (TT 02/2019/TT-NHNN)")
        m["derivation"]["transitions"] = [tr]
        v1 = r["version_id"].endswith(":1")
        m["valid_from"], m["valid_to"] = ("2014-10-15", F060["change"]) if v1 else (F060["change"], None)
        if r["as_of"] in F060["move"]:
            new = F060["move"][r["as_of"]] or mid("2014-10-15", F060["change"])
            if m.get("pending"):
                m["pending"].update(actor_document_id=doc, signed_on=signed, effective_from=F060["change"],
                                    days_until_effect=(date.fromisoformat(F060["change"]) - date.fromisoformat(new)).days)
            move(r, m, new)
            hit += 1
    assert hit == len(F060["move"]), f"F060: moved {hit}"
    for m in meta:
        if m.get("twin_of") in renamed:
            m["twin_of"] = renamed[m["twin_of"]]
    return renamed


CODEX_MODEL = "gpt-6.1-sol (author-reported; Codex CLI logs do not record the model)"


CLAUDE_OPUS = "Claude Code / claude-opus-5-5"
CODEX_SOL = "Codex CLI / gpt-6.1-sol (CLI log)"
CODEX_LUNA = "Codex CLI / gpt-6-luna (CLI log)"
CODEX_UNRECORDED = "Codex / model not recorded (agent self-report: GPT-6 family)"
CODEX_NATIVE = "Codex native subagent / model not recorded (inherited)"
# Production label runs (same a.jsonl/b.jsonl as scripts/check/audit_g2_statistics.py, plus T1).
RUNS = [  # first run holding a lineage wins; later ones are kept as superseded
    ("uniform_20261119", AI / "2026-11-19_uniform", None, None),  # agents per job: UNIFORM_AGENTS
    ("silver01", AI / "2026-11-07_adjudication_all/snapshots/silver01", CLAUDE_OPUS, CLAUDE_OPUS),
    ("round2_codex", AI / "2026-11-06_silver/round2_codex", CODEX_NATIVE, CODEX_NATIVE),
    ("round3_mixed", AI / "2026-11-06_silver/round3_mixed", CLAUDE_OPUS, CODEX_SOL),
    ("lo2", AI / "2026-11-08_lo2/schema_validated", CLAUDE_OPUS, CODEX_UNRECORDED),
    ("supp18", AI / "2026-11-08_supp18", CLAUDE_OPUS, CODEX_LUNA),
    ("t1", AI / "2026-11-11_t1_labels", "Claude Code / claude-sonnet-5-5", CODEX_LUNA),
]
ADJUDICATION = [AI / "2026-11-07_adjudication_all/results", AI / "2026-11-08_lo2/schema_validated/adjudication.jsonl",
                AI / "2026-11-08_lo2/open_cases_for_CMT.jsonl", AI / "2026-11-08_supp18/adjudication.jsonl", AI / "2026-11-11_t1_labels/adjudication.jsonl"]
GOLD_COLS = {"khoa": "item_key", "cau_hoi": "question", "ngay_hoi": "as_of", "van_ban": "document",
             "dieu_khoan": "provision", "link": "source_url", "van_ban_tac_dong_theo_cong": "acting_documents_listed_by_portal",
             "hieu_luc": "in_force", "noi_dung": "content", "van_ban_ap_dung": "applicable_document",
             "kg_hieu_luc": "store_in_force", "kg_noi_dung": "store_content", "kg_hieu_luc_tu": "store_valid_from",
             "kg_hieu_luc_den": "store_valid_to", "dong_y": "agrees_with_store"}
GOLD_VALUES = {"có": "yes", "co": "yes", "không": "no", "khong": "no"}
GOLD_DROP = {"ly_do", "ghi_chu_mo", "phut", "ghi_chu", "stage1_sha256"}  # free notes and timing: not released

# Verbatim prompts, agent definitions and guideline (initials such as CMT = the reviewing author are kept).
PROMPTS = [
    ("data/review/ai_research/2026-11-06_silver/prompts", "labelling/silver"),
    ("data/review/ai_research/2026-11-08_lo2/prompts", "labelling/lo2"),
    ("data/review/ai_research/2026-11-08_supp18/prompts", "labelling/supp18"),
    ("data/review/ai_research/2026-11-11_t1_labels/prompts", "labelling/t1"),
    ("data/review/ai_research/2026-11-19_uniform/prompts", "labelling/uniform_20261119"),
    ("data/review/ai_research/codex_b_wrapper.md", "labelling/codex_b_wrapper.txt"),
    ("data/review/ai_research/2026-11-07_adjudication_all/prompts", "adjudication/silver"),
    ("data/review/ai_research/2026-11-08_lo2/adjudication/prompts", "adjudication/lo2"),
    (".claude/agents/legal-annotator-a.md", "agents/legal-annotator-a.txt"),
    (".claude/agents/legal-annotator-b.md", "agents/legal-annotator-b.txt"),
    (".claude/agents/legal-adjudicator.md", "agents/legal-adjudicator.txt"),
    (".claude/skills/vilextime-ai-labeling/SKILL.md", "agents/skill-vilextime-ai-labeling.txt"),
    (".claude/skills/vn-legal-research/SKILL.md", "agents/skill-vn-legal-research.txt"),
    ("docs/vilextime-annotation.md", "context/annotation_guideline_v4.0_vi.txt"),
    ("docs/vilextime-dinh-nghia.md", "context/dataset_definition_vi.txt"),
]

# Thesis codes -> public names (CMT 19/11). T4/T5 never existed as released groups, so codes looked gapped.
GROUP_NAMES = {"T1": "control", "T2": "two_versions", "T3": "multi_versions", "T6": "repealed"}
SUBGROUP_NAMES = {"T1": "control", "T2": "two_versions", "T4": "near_identical", "T3": "multi_versions",
                  "T6a": "repealed_by_name", "T6b": "repealed_via_parent"}


DATE_MODES = {"ranh_gioi": "boundary", "giua_khoang": "mid_interval"}


def rename_id(row_id):
    head, group, rest = row_id.split(":", 2)
    return f"{head}:{GROUP_NAMES[group]}:{rest}"


BATCH_NAMES = {"silver": "round_1", "new": "round_2", "supp": "round_3", "t1": "control"}

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
    # 19/11 relabel of same-family pairs: agreement re-measured on the new Claude+Codex pair; the 2 disputes are
    # the same objection already settled by the earlier adjudication record of that lineage (reused, not re-run).
    disputed = {json.loads(x)["lineage_id"] for x in open(AI / "2026-11-19_uniform/disagreements.jsonl")}
    for x in open(AI / "2026-11-19_uniform/pairs.jsonl"):
        lid = json.loads(x)["lineage_id"]
        batch, _, channel = res[lid]
        res[lid] = (batch, "ai_adjudicated" if lid in disputed else "ai_agree", channel)
    return res


def extra_ai_checks():
    """lineage -> AI adjudicator re-checks after the author's review (legal-adjudicator agent, author-delegated)."""
    out = {}
    for step, d, what in (("author_flagged_recheck", "2026-11-11_h7", "re-check of lineages the author marked unsure or corrected"),
                          ("relocation_check", "2026-11-11_t6_r2", "for a repealed provision, check whether its content moved elsewhere")):
        for f in sorted((AI / d).glob("out_batch*.jsonl")):
            for r in jl(f):
                out.setdefault(r["lineage_id"], []).append({"step": step, "what": what, "agent": "legal-adjudicator / " + CLAUDE_OPUS})
    return out


RANDOM30 = GOLD / "gold_random30"  # round 3: random 30 of the 94 unread lineages, two readers (21–22/11/2026)


def _norm(text):
    import unicodedata
    return " ".join(re.sub(r"[^\w]+", " ", unicodedata.normalize("NFC", text or "").lower()).split())


def machine_agrees(r):
    """Reader vs store, compared by machine (not by the reader): same in-force status and, when in force, the
    reader's pasted wording lies inside the store's wording after normalisation."""
    if r["hieu_luc"].strip() != r["kg_hieu_luc"].strip():
        return False
    return r["hieu_luc"].strip() != "còn" or (bool(_norm(r["noi_dung"])) and _norm(r["noi_dung"]) in _norm(r["kg_noi_dung"]))


def blind_gold():
    """lineage -> list of blind-reader records. Round 1: annotators A/B; round 2: co-author reader + lawyer;
    round 3: random 30, annotators A/B, compared by machine. Each record names the date that was read."""
    g = {}
    rounds = (("round1", GOLD, {"A": "annotator_A", "B": "annotator_B"}),
              ("round2", GOLD / "gold_final", {"A": "coauthor_reader", "B": "lawyer"}),
              ("round3_random", RANDOM30, {"A": "annotator_A", "B": "annotator_B"}))  # roles only, no names (schema rule)
    adjudicated = {(a["khoa"], a["reader"]): a for a in jl(RANDOM30 / "adjudication.jsonl")}
    for rnd, d, readers in rounds:
        sample = {r["khoa"]: r for r in tsv(d / "gold_sample.tsv")}
        for side, who in readers.items():
            for r in tsv(d / f"gold_{side}.reveal.tsv"):
                s = sample.get(r["khoa"])
                if not s:
                    continue
                rec = {"round": rnd, "reader": who, "as_of_read": r["ngay_hoi"]}
                if rnd == "round3_random":
                    rec.update(agrees_with_store=machine_agrees(r), basis="machine_compare")
                    a = adjudicated.get((r["khoa"], side))
                    if a:
                        rec["adjudication"] = a["outcome"]
                else:
                    agree, basis = YES_NO.get(r.get("dong_y", "").strip()), "reader_judgement"
                    if agree is None and r.get("kg_hieu_luc", "").strip():  # lawyer sheet: compare in-force status only
                        agree, basis = r["hieu_luc"].strip() == r["kg_hieu_luc"].strip(), "in_force_status_only"
                    rec.update(agrees_with_store=agree, basis=basis)
                g.setdefault(s["lineage_id"], []).append(rec)
    return g


UNIFORM_AGENTS = {"r2codex": [CLAUDE_OPUS + " (new, 19/11)", CODEX_NATIVE + " (kept)"],
                  "silver01": [CLAUDE_OPUS + " (kept)", CODEX_LUNA + " (new, 19/11)"]}


def raw_labels(final):
    """Raw pre-adjudication AI labels of the final lineages, tagged with run and agent."""
    uniform = {json.loads(x)["lineage_id"]: json.loads(x)["job"] for x in open(AI / "2026-11-19_uniform/pairs.jsonl")}
    out, run_of = [], {}
    for run, d, agent_a, agent_b in RUNS:
        seen_here = set()
        for side, agent in (("a", agent_a), ("b", agent_b)):
            for r in jl(d / f"{side}.jsonl"):
                lid = r["lineage_id"]
                if lid not in final:
                    continue
                first = run_of.setdefault(lid, run) == run
                seen_here.add(lid)
                status = "used" if first else f"superseded by {run_of[lid]} (same-family pair relabelled)"
                who = agent or UNIFORM_AGENTS[uniform[lid]]["ab".index(side)]
                out.append({"run": run, "agent": who, "status": status, **r})
    agents = {run: [a, b] for run, _, a, b in RUNS}
    res = {}
    for lid, run in run_of.items():
        if run == "uniform_20261119":
            res[lid] = [a.rsplit(" (", 1)[0] for a in UNIFORM_AGENTS[uniform[lid]]]
        else:
            res[lid] = agents[run]
    return out, res


def high_risk_aug():
    """(lineage_id, as_of) -> high-risk augmentation record.
    These 29 hardest rows (repealed / multi-version) were labelled blind by two AI
    annotators, reconciled, then verified by one author who saw the AI labels
    (not blind; no lawyer). A verification layer, kept separate from blind_gold."""
    p = GOLD_DOT3 / "gold_dot3_verified.jsonl"
    if not p.exists():
        return {}
    return {(r["lineage_id"], r["as_of"]): {
        "method": "ai_proposed_cmt_verified", "group": r["group"],
        "final_label": r["final_label"], "verdict_cmt": r["duyet_CMT"], "note": r.get("cmt_ghi_chu"),
    } for r in jl(p)}


def export_annotation(final, labels):
    import shutil
    ann = OUT / "annotation"
    shutil.rmtree(ann, ignore_errors=True)
    for sub in ("labels", "worksheets", "blind_reading", "prompts"):
        (ann / sub).mkdir(parents=True)
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
    post = [{"step": step, **r} for step, d in (("author_flagged_recheck", "2026-11-11_h7"), ("relocation_check", "2026-11-11_t6_r2"))
            for f in sorted((AI / d).glob("out_batch*.jsonl")) for r in jl(f) if r["lineage_id"] in final]
    for name, data in (("labels/ai_labels_raw.jsonl", labels), ("labels/adjudication.jsonl", adj),
                       ("labels/post_review_ai_checks.jsonl", post), ("worksheets/worksheets.jsonl", list(ws.values()))):
        with open(ann / name, "w", encoding="utf-8") as f:
            for x in data:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    aug = GOLD_DOT3 / "gold_dot3_verified.jsonl"
    if aug.exists():
        import shutil as _sh
        _sh.copy2(aug, ann / "high_risk_augmentation.jsonl")
    for rnd, d, readers in (("round1", GOLD, ("annotator_A", "annotator_B")),
                            ("round2", GOLD / "gold_final", ("coauthor_reader", "lawyer")),
                            ("round3_random", RANDOM30, ("annotator_A", "annotator_B"))):
        key2lid = {r["khoa"]: r["lineage_id"] for r in tsv(d / "gold_sample.tsv")}
        for side, who in zip("AB", readers):
            src_rows = [r for r in tsv(d / f"gold_{side}.reveal.tsv") if key2lid.get(r["khoa"]) in final]
            if rnd == "round3_random":  # compared by machine, as in blind_gold()
                for r in src_rows:
                    r["dong_y"] = "có" if machine_agrees(r) else "không"
            rows = [{"lineage_id": key2lid[r["khoa"]],
                     **{GOLD_COLS[k]: GOLD_VALUES.get(v.strip(), v) if k in ("hieu_luc", "kg_hieu_luc", "dong_y") else v
                        for k, v in r.items() if k not in GOLD_DROP}}
                    for r in src_rows]
            for row in rows:  # lawyer sheet has no reader verdict: same in-force-only rule as blind_gold()
                if not row["agrees_with_store"].strip() and row["store_in_force"].strip():
                    row["agrees_with_store"] = "yes" if row["in_force"].strip() == row["store_in_force"].strip() else "no"
            with open(ann / "blind_reading" / f"{rnd}_{who}.tsv", "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
                w.writeheader()
                w.writerows(rows)
    for src, dst in PROMPTS:
        src = ROOT / src
        target = ann / "prompts" / dst
        if src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
    # Prompts are plain text sent to the agents, not Markdown documents: .txt keeps them verbatim and readable.
    for f in [*(ann / "prompts" / "labelling").rglob("*.md"), *(ann / "prompts" / "adjudication").rglob("*.md")]:
        f.rename(f.with_suffix(".txt"))
    return len(adj), len(ws)


GOOD = {"q1": "dung", "q2": "co", "q3": "co", "q4": "khong"}
CODES = {"cosmetic_only", "rename_only", "auto_reference_update", "single_change", "relocated", "relocation_unclear",
         "superseded_by_other_norm", "restructuring_2025", "reference_only", "pending_event", "after_snapshot",
         "group_mismatch", "question_ambiguous", "question_leaks", "unanswerable_as_asked", "gold_wrong",
         "transitional_rule", "other", "not_verified"}  # closed list, docs/vilextime-dinh-nghia.md §7
AI_LABEL = re.compile(r"Q(\d): (\w+)(?: \((\w+)\))?")


def _reasons(labels):
    """Reason codes of the unfavourable answers of one final label {q1: (value, reason), ...}."""
    out = sorted({reason or "other" for q, (value, reason) in labels.items() if value and value != GOOD[q]})
    assert set(out) <= CODES, out
    return out


def _apply_author_edit(labels, text):
    """Silver sheet `cmt_sua`: the author's edits to the AI label, written as 'Q2 → khong; q2_reason = X',
    'q2_reason: A → B', 'Q4 → co/X', 'xóa q3_reason'."""
    for q, new in re.findall(r"q(\d)_reason: ?\w+ ?→ ?(\w+)", text):
        labels["q" + q] = (labels["q" + q][0], new)
    for q, value, reason in re.findall(r"Q(\d) ?→ ?(dung|sai|co|khong)(?:/(\w+))?", text):
        labels["q" + q] = (value, reason or (labels["q" + q][1] if value != GOOD["q" + q] else ""))
    for q, reason in re.findall(r"q(\d)_reason ?= ?(\w+)", text):
        labels["q" + q] = (labels["q" + q][0], reason)
    for q in re.findall(r"(?:xóa|bỏ) q(\d)_reason", text):
        labels["q" + q] = (labels["q" + q][0], "")
    return labels


def _sheet(path):
    import openpyxl
    r = list(openpyxl.load_workbook(path, data_only=True)["Duyệt"].iter_rows(values_only=True))
    return [dict(zip(r[0], x)) for x in r[1:] if x and x[0]]


def excluded_lineages(final):
    """The 175 lineages labelled for the final set but not released, with the step that removed them and the
    reason codes of the final label (docs/vilextime-dinh-nghia.md §7). Reproduces the funnel of
    data/review/ai_research/2026-11-11_final_count/count_final.py: silver 168 → 75, lo2 128 → 70, supp 18 → 11,
    control 60 → 43."""
    out = {}

    def add(lid, group, batch, question, step, decided_by, reasons):
        assert lid not in final and lid not in out, lid
        group = {"T4": "T2"}.get(group, group)
        out[lid] = {"lineage_id": lid, "group": GROUP_NAMES[group], "source_batch": BATCH_NAMES[batch],
                    "question": question, "removed_at": step, "decided_by": decided_by, "reason_codes": reasons}

    conf = json.load(open(AI / "2026-11-10_cmt_confirmed/cmt_confirmed.json"))
    h7 = {r["lineage_id"]: r for f in sorted((AI / "2026-11-11_h7").glob("out_batch*.jsonl")) for r in jl(f)}
    r2 = {r["lineage_id"]: r["ket_luan"] for f in sorted((AI / "2026-11-11_t6_r2").glob("out_batch*.jsonl")) for r in jl(f)}
    author_drop = {"provision:e9ffd3da-eb7a-11f0-9830-4feb5d5132b5": "reference_only"}  # count_final.py CMT_DROP
    seen = Counter()

    for r in _sheet(AI / "2026-11-08_adjudication_final/duyet_CMT_final.xlsx"):  # silver
        lid = r["lineage_id"]
        seen["silver"] += 1
        labels = _apply_author_edit({q: (r[q], r[q + "_reason"] or "") for q in GOOD}, r["cmt_sua"] or "")
        verdict = conf["silver_flips"].get(lid, "->" + r["verdict"]).split("->")[1]
        if lid in h7:  # the re-check's label is the final one; removed there only if it overturned an accept
            h = h7[lid]
            if h["verdict"] == "khong_dat":
                step = "author_flagged_recheck" if verdict == "dat" else "label_review"
                add(lid, r["group"], "silver", r["question"], step, "ai_adjudicator",
                    _reasons({q: (h[q], h[q + "_reason"]) for q in GOOD}))
            continue
        if verdict == "khong_dat":
            reasons = _reasons(labels) if any(v != GOOD[q] for q, (v, _) in labels.items()) else ["other"]
            add(lid, r["group"], "silver", r["question"], "label_review",
                "author" if lid in conf["silver_flips"] else r["source"], reasons)

    lo2_sheet = _sheet(AI / "2026-11-08_lo2/duyet_CMT_after_adjudication.xlsx")
    t1_sheet = _sheet(AI / "2026-11-11_t1_labels/duyet_CMT.xlsx")
    t1_dat = set(json.load(open(AI / "2026-11-11_t1_labels/cmt_confirmed_t1.json"))["t1_dat"])
    for batch, sheet in (("new", lo2_sheet), ("t1", t1_sheet)):
        for r in sheet:
            lid = r["lineage_id"]
            seen[batch] += 1
            if r["chot_q1"] is None:  # no final label: at least one AI said not acceptable, never reconciled
                assert batch == "t1" and lid not in t1_dat
                labels = [{"q" + q: (v, c or "") for q, v, c in AI_LABEL.findall(r[side] or "")} for side in ("AI_A_nhan", "AI_B_nhan")]
                add(lid, r["group"], batch, r["question"], "label_unresolved", "ai_labels",
                    sorted(set(_reasons(labels[0])) | set(_reasons(labels[1]))))
                continue
            labels = {q: (r["chot_" + q], r["chot_" + q + "_reason"] or "") for q in GOOD}
            if any(v != GOOD[q] for q, (v, _) in labels.items()):
                add(lid, r["group"], batch, r["question"], "label_review", "ai_labels_author_review", _reasons(labels))
            elif lid in r2 and r2[lid] != "giu":
                add(lid, r["group"], batch, r["question"], "relocation_check", "ai_adjudicator", [r2[lid]])
            elif lid in author_drop:
                add(lid, r["group"], batch, r["question"], "author_decision", "author", [author_drop[lid]])
            elif batch == "t1":
                assert lid in t1_dat, lid

    supp_in = {x["record"]["lineage_id"]: x["record"] for f in sorted((AI / "2026-11-08_supp18/input").glob("*.jsonl"))
               for x in jl(f)}
    accepted = {r["lineage_id"]: r["label"] for r in jl(AI / "2026-11-08_supp18/cmt_accepted_labels.jsonl")}
    raw = {side: {r["lineage_id"]: r for r in jl(AI / f"2026-11-08_supp18/{side}.jsonl")} for side in "ab"}
    for lid, rec in supp_in.items():
        seen["supp"] += 1
        if lid in final:
            continue
        if lid not in accepted:
            reasons = sorted({c for side in "ab" if lid in raw[side]
                              for c in _reasons({q: (raw[side][lid][q], raw[side][lid][q + "_reason"]) for q in GOOD})})
            add(lid, rec["group"], "supp", rec["question"], "label_unresolved", "ai_labels", reasons)
            continue
        lab = {q: (accepted[lid][q], accepted[lid][q + "_reason"]) for q in GOOD}
        if any(v != GOOD[q] for q, (v, _) in lab.items()):
            add(lid, rec["group"], "supp", rec["question"], "label_review", "ai_labels_author_review", _reasons(lab))
        elif lid in r2 and r2[lid] != "giu":
            add(lid, rec["group"], "supp", rec["question"], "relocation_check", "ai_adjudicator", [r2[lid]])
        elif lid in author_drop:
            add(lid, rec["group"], "supp", rec["question"], "author_decision", "author", [author_drop[lid]])

    by_batch = Counter(x["source_batch"] for x in out.values())
    assert dict(seen) == {"silver": 168, "new": 128, "t1": 60, "supp": 18}, seen
    assert by_batch == {"round_1": 93, "round_2": 58, "round_3": 7, "control": 17}, by_batch
    assert len(out) + len(final) == 374
    return sorted(out.values(), key=lambda x: x["lineage_id"])


def issuer_code(law_id):
    tail = law_id.split("/")[-1]
    code = tail.split("-")[-1]
    return code.rstrip("0123456789") or code  # QH15, UBTVQH11 -> QH, UBTVQH


def main():
    rows = jl(BASE / "vilextime.jsonl")
    meta = jl(BASE / "vilextime_meta.jsonl")
    assert len(rows) == len(meta) == 722 and all(r["id"] == m["id"] for r, m in zip(rows, meta))
    prov, gold, extra = ai_resolution(), blind_gold(), extra_ai_checks()
    aug = high_risk_aug()
    print("high-risk augmentation (CMT-verified) rows", len(aug))
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
        }
        hr = aug.get((lid, r["as_of"]))
        if hr:
            m["review"]["high_risk_ai_author_check"] = hr
        qs = m.get("question_source") or {}
        if "codex" in str(qs.get("provider", "")):
            qs["model"] = CODEX_MODEL
        sas = m.get("short_answer_source") or {}
        if "codex" in str(sas.get("by", "")).lower():
            sas["by"] = CODEX_MODEL
        m["schema_version"] = "6.0.0"  # 6.0.0 review.high_risk_ai_author_check (renamed), blind_gold.as_of_read; 4.0.0 group names/ids; 5.0.0 store fixes re-date rows (ids) + store_correction: MAJOR per ADR 0003 §8
        m.pop("domain", None)
        m.pop("domain_source", None)
        m["issuer_code"] = issuer_code(m["target"]["law_id"])
        m["source_batch"] = BATCH_NAMES[m.pop("qsource")]
        if m.get("repeal_mode") == "ancestor":
            m["repeal_mode"] = "via_parent"

        if r["id"] == F019_ID:
            assert r["answerable"] is True, "F019 already corrected?"
            r.update(answer=None, context=None, answerable=False, version_id=None, accepted_evidence=[])
            m.update(no_answer_reason="provision_repealed", in_force=False, repeal_mode="direct",
                     repealed_by="Thông tư 36/2026/TT-BXD, khoản 2 Điều 16 (hiệu lực 01/07/2026)")
            m.setdefault("flags", []).append("gold_corrected_by_blind_gold")

    renamed = apply_store_fixes(rows, meta)
    print("store fixes: rows re-dated", len(renamed), *sorted(renamed.items()), sep="\n  ")
    assert len({r["id"] for r in rows}) == len(rows), "duplicate id after store fixes"

    for r, m in zip(rows, meta):  # after F019 (matched by the thesis id)
        r["id"] = m["id"] = rename_id(r["id"])
        r["group"] = GROUP_NAMES[r["group"]]
        r["as_of_strategy"] = DATE_MODES[r["as_of_strategy"]]
        m["subgroup"] = SUBGROUP_NAMES[m["subgroup"]]
        if m.get("twin_of"):
            m["twin_of"] = rename_id(m["twin_of"])
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
    excluded = excluded_lineages(final)
    with open(OUT / "annotation/excluded_lineages.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in excluded)
    print("excluded lineages", len(excluded), Counter((x["source_batch"], x["removed_at"]) for x in excluded))
    lin = {}
    for r, m in zip(rows, meta):
        lin[r["lineage_id"]] = m["review"]
    print("rows", len(rows), "lineages", len(lin), "answerable", sum(r["answerable"] for r in rows))
    print("ai_resolution", Counter(v["ai_resolution"] for v in lin.values()))
    print("post-review AI checks", Counter(c["step"] for v in lin.values() for c in v["post_review_ai_checks"]))

    print("lineages with blind gold", sum(bool(v["blind_gold"]) for v in lin.values()),
          Counter(g["round"] + ":" + g["reader"] for v in lin.values() for g in v["blind_gold"]))
    print("issuer", Counter(m["issuer_code"] for m in meta).most_common(6))
    print(sums, end="")


if __name__ == "__main__":
    main()
