#!/usr/bin/env python3
"""ViLexTime — the published files (docs/vilextime-schema-phat-hanh.md), from the release and the labels.

Reads data/derived/vilextime/release.jsonl and the 100% check (data/review/kiem_{A,B}.tsv,
optional kiem_agent.tsv, and hoa_giai_kiem.tsv once the lawyer has settled disagreements), and writes to
data/vilextime_dataset/ (its own folder, apart from the build inputs in data/vilextime/):

    vilextime.jsonl          13 columns, the rows a person checked and passed: what a user needs
    vilextime_silver.jsonl   same columns, rows nobody has checked yet (definition §8, `not_verified`)
    vilextime_meta.jsonl     every other field of those rows, joined on `id`, with `review` filled
    vilextime.csv            the 13 columns again, for a spreadsheet (and vilextime_silver.csv): UTF-8 with
                             a BOM so Excel reads the diacritics; `accepted_evidence` joined by ";"
    manifest.json            schema version, row counts, rows dropped per reason code, agreement, sha256

A row's final label: lawyer (hoa_giai_kiem.tsv, then the lawyer's check of the agent sample,
luat_su_kiem_agent.tsv), matching A/B under 3.0, then agent (the agent's label winning an A/agent
disagreement: the lawyer sided with the agent on 8 of the 12 such rows of the sample, 29/10). Without an agent label, one current human label suffices; disagreeing A/B wait for
the lawyer. A label made under an older guideline (carried from D4) counts only once confirmed under
the current one. A lineage passes when every boundary row of it passes, fails
when one fails (as `adjudicate.py drop` does for D4: a T2 pair without one of its rows is no pair).
Its twins (`giua_khoang`, `truoc_hieu_luc`: same question, same gold version) go with it. A failed
lineage is not published; the manifest counts it per reason code.

Usage:
    python scripts/pipeline/export_release.py            # candidate: unchecked rows go to silver
    python scripts/pipeline/export_release.py --final    # refuses while a row is unchecked or unsettled
    python scripts/pipeline/export_release.py --draft    # every row not failed in the main file, to read through
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "review"))
from crosscheck import GUIDELINE, read  # noqa: E402

SCHEMA_VERSION = "2.0.0"   # ADR 0003 §8: the rebuild changes gold and moves rows between splits
# published name -> internal field (None: computed in `published`). Read as (question, answer, context):
# `answer` is the short answer the scorer checks; `context` the wording in force with the parent's lead-in,
# which often holds the answer ("3. Phạt tiền từ … đối với một trong các hành vi sau:" over a point).
MAIN = {"id": "id", "split": "split", "group": "group", "as_of_strategy": "as_of_strategy",
        "question": "question", "as_of": "as_of", "context": None, "answer": "short_answer",
        "answerable": "answerable", "citation": None, "lineage_id": "lineage_id", "version_id": "version_id",
        "accepted_evidence": "accepted_evidence"}
# 28/10 (CMT): the agent passed its blind calibration on T1 and T6 only (AC1 0,970 and 0,681; T2 0,704 with
# p_neg 0,211, T3 0,473 with p_neg 0,200; docs/plans/active/codex-chot-du-lieu-va-thuc-nghiem.md A3), so its
# labels count only there. On the test split one person's label alone no longer counts as a check (A's pass
# took about 5 s a row); dev keeps it, dev only picks a configuration.
AGENT_GROUPS = ("T1", "T6")
OUT_OF_SCOPE = "ngoài phạm vi agent, chưa đủ hai người kiểm"
CODES = lambda s: sorted({c.strip() for c in (s or "").split(",") if c.strip()})


def final_labels(review: Path, scope: dict[str, tuple[str, str]] | None = None) -> dict[str, dict]:
    """Boundary row id -> review: status checked (verdict, reasons) or not_verified (why).

    `scope` maps a boundary id to (group, split). Without it every group and split follows the old rules."""
    a = {r["id"]: r for r in read(review / "kiem_A.tsv")}
    b = {r["id"]: r for r in read(review / "kiem_B.tsv")}
    adj_path = review / "hoa_giai_kiem.tsv"
    adj = {r["id"]: r for p in (review / "luat_su_kiem_agent.tsv", adj_path) if p.exists() for r in read(p)}
    agent_path = review / "kiem_agent.tsv"
    agent = {r["id"]: r for r in read(agent_path)} if agent_path.exists() else {}
    out = {}
    for i in a.keys() | b.keys() | adj.keys() | agent.keys():
        labelled = {w: r for w, r in (("A", a.get(i)), ("B", b.get(i))) if r and r["verdict"]}
        # a label carried from D4 (1.2/2.0) has none of 3.0's evidence fields nor its codes (definition §8)
        current = {w: r for w, r in labelled.items() if r.get("guideline_version") == GUIDELINE}
        rev = {"double_labelled": len(current) == 2, "adjudicated": False}
        if len(current) == 2:
            rev["raw"] = {w: {"verdict": r["verdict"], "reasons": CODES(r["reasons"])} for w, r in current.items()}
        if i in adj and adj[i]["verdict"]:
            rev.update(status="checked", verdict=adj[i]["verdict"], reasons=CODES(adj[i]["reasons"]),
                       adjudicated=True, labeler=adj[i].get("adjudicator") or "luật sư", source="human")
        elif len(current) == 2 and current["A"]["verdict"] == current["B"]["verdict"]:
            rev.update(status="checked", verdict=current["A"]["verdict"],
                       reasons=sorted({c for r in current.values() for c in CODES(r["reasons"])}),
                       labeler="A+B", source="human")
        elif (i in agent and agent[i]["verdict"] and agent[i].get("guideline_version") == GUIDELINE
              and (scope is None or scope[i][0] in AGENT_GROUPS)):
            ar = agent[i]
            av = current.get("A")
            conflict = bool(av and av["verdict"] != ar["verdict"])
            reasons = (CODES(av["reasons"] if av["verdict"] == "khong_dat" else ar["reasons"])
                       if conflict else CODES(ar["reasons"]))
            rev.update(status="checked", verdict=ar["verdict"], reasons=reasons,
                       labeler=ar.get("labeler") or "agent", source="agent", a_agent_disagreement=conflict)
        elif scope is not None and scope[i][1] == "test" and len(current) < 2 and (current or not labelled):
            rev.update(status="not_verified", why=OUT_OF_SCOPE if scope[i][0] not in AGENT_GROUPS else "chờ nhãn agent")
        elif not labelled:
            rev.update(status="not_verified", why="chưa gán")
        elif not current:
            rev.update(status="not_verified", why=f"nhãn theo hướng dẫn cũ, cần xác nhận lại theo {GUIDELINE}")
        elif len({r["verdict"] for r in current.values()}) > 1:
            rev.update(status="not_verified", why="A và B lệch, chưa hòa giải")
        else:
            rev.update(status="checked", verdict=next(iter(current.values()))["verdict"],
                       reasons=sorted({c for r in current.values() for c in CODES(r["reasons"])}),
                       labeler="+".join(sorted(current)), source="human")
        if rev["status"] == "checked":
            rev["guideline_version"] = GUIDELINE
        out[i] = rev
    return out


def lineage_status(rows: list[dict], labels: dict[str, dict]) -> dict[str, str]:
    """lineage -> dat / khong_dat / not_verified, from its boundary rows."""
    by = collections.defaultdict(list)
    for r in rows:
        if r["as_of_strategy"] == "ranh_gioi":
            by[r["lineage_id"]].append(labels.get(r["id"], {"status": "not_verified"}))
    out = {}
    for lid, revs in by.items():
        if any(x.get("verdict") == "khong_dat" for x in revs):
            out[lid] = "khong_dat"
        elif all(x["status"] == "checked" for x in revs):
            out[lid] = "dat"
        else:
            out[lid] = "not_verified"
    return out


def published(r: dict) -> dict:
    out = {k: r[src] for k, src in MAIN.items() if src}
    out["citation"] = r["target"]["citation"]
    out["context"] = None if r["answer"] is None else "\n".join(filter(None, (r["target"].get("lead_in"), r["answer"])))
    return {k: out[k] for k in MAIN}


def meta(r: dict, review: dict) -> dict:
    moved = ({src for src in MAIN.values() if src} | {"answer"}) - {"id"}
    m = {k: v for k, v in r.items() if k not in moved and k != "review"}
    m["schema_version"] = SCHEMA_VERSION
    m["review"] = review
    return m


def export(data: Path, out: Path, final: bool = False, draft: bool = False) -> dict:
    rows = [json.loads(line) for line in (data / "derived/vilextime/release.jsonl").open(encoding="utf-8")]
    scope = {r["id"]: (r["group"], r["split"]) for r in rows if r["as_of_strategy"] == "ranh_gioi"}
    labels = final_labels(data / "review", scope)
    status = lineage_status(rows, labels)
    boundary = {r["lineage_id"]: [] for r in rows}
    for r in rows:
        if r["as_of_strategy"] == "ranh_gioi":
            boundary[r["lineage_id"]].append(r["id"])
    main, silver, metas = [], [], []
    dropped = collections.Counter()
    dropped_rows = collections.Counter()
    for r in rows:
        own = labels.get(r["id"]) if r["as_of_strategy"] == "ranh_gioi" else labels.get(r["twin_of"])
        st = status[r["lineage_id"]]
        if st == "khong_dat":
            dropped_rows[r["group"]] += 1
            continue
        review = dict(own or {"status": "not_verified", "why": "chưa gán"})
        if r["as_of_strategy"] != "ranh_gioi":
            review["label_of"] = r["twin_of"]
        if st == "not_verified":
            review["status"] = "not_verified"
        (main if st == "dat" or draft else silver).append(published(r))
        metas.append(meta(r, review))
    for lid, st in status.items():
        if st == "khong_dat":
            failed = [labels[i] for i in boundary[lid] if labels.get(i, {}).get("verdict") == "khong_dat"]
            codes = {c for x in failed for c in x["reasons"]}
            dropped.update(codes or {"(không mã)"})
    ids = [r["id"] for r in main + silver]
    assert len(ids) == len(set(ids)) == len(metas), "id trùng hoặc lệch số dòng meta"
    unsettled = sum(1 for x in labels.values() if x.get("why") == "A và B lệch, chưa hòa giải")
    unchecked = sum(1 for x in labels.values() if x["status"] == "not_verified")
    pending = sum(1 for x in labels.values() if x["status"] == "not_verified" and x.get("why") != OUT_OF_SCOPE)
    if final and pending:
        raise SystemExit(f"--final: còn {pending} dòng ranh giới chưa có nhãn cuối ({unsettled} dòng A/B lệch chưa "
                         f"hòa giải) ngoài các dòng ngoài phạm vi agent — KHÔNG ghi gì")
    out.mkdir(parents=True, exist_ok=True)
    files = {"vilextime.jsonl": main, "vilextime_silver.jsonl": silver, "vilextime_meta.jsonl": metas}
    for name, items in files.items():
        with (out / name).open("w", encoding="utf-8") as f:
            for x in items:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    for name, items in (("vilextime.csv", main), ("vilextime_silver.csv", silver)):
        with (out / name).open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, list(MAIN))
            w.writeheader()
            w.writerows({**x, "accepted_evidence": ";".join(x["accepted_evidence"])} for x in items)
        files[name] = items
    count = lambda items: dict(sorted(collections.Counter(
        f"{x['group']} · {x['as_of_strategy']} · {x['split']}" for x in items).items()))
    agreement = data / "review/kiem_result.json"
    manifest = {
        "schema_version": SCHEMA_VERSION, "final": final, "draft": draft,
        "rows": {"main": len(main), "silver": len(silver)},
        "counts_main": count(main), "counts_silver": count(silver),
        "lineages": dict(collections.Counter(status.values())),
        "dropped_lineages_by_reason": dict(dropped.most_common()),
        "dropped_rows_by_group": dict(sorted(dropped_rows.items())),
        "boundary_rows": {"checked": len(labels) - unchecked, "not_verified": unchecked, "unsettled": unsettled},
        "review_counts": {
            "human_checked": sum(x.get("source") == "human" for x in labels.values()),
            "agent_checked": sum(x.get("source") == "agent" for x in labels.values()),
            "a_agent_disagreement": sum(x.get("a_agent_disagreement", False) for x in labels.values()),
        },
        "agreement": json.loads(agreement.read_text(encoding="utf-8")) if agreement.exists() else None,
        "sha256": {n: hashlib.sha256((out / n).read_bytes()).hexdigest() for n in files},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, help="default: <data>/vilextime_dataset")
    ap.add_argument("--final", action="store_true", help="refuse unless every boundary row has a final label")
    ap.add_argument("--draft", action="store_true", help="every row not failed into vilextime.jsonl, to read through "
                                                          "(`review.status` still says which are unchecked)")
    args = ap.parse_args()
    if args.final and args.draft:
        ap.error("--final or --draft, not both")
    m = export(args.data, args.out or args.data / "vilextime_dataset", args.final, args.draft)
    print(f"schema {m['schema_version']}: {m['rows']['main']} dòng chính, {m['rows']['silver']} dòng silver; "
          f"lineage {m['lineages']}")
    print(f"  dòng ranh giới: {m['boundary_rows']}")
    print(f"  lineage bị loại theo mã: {m['dropped_lineages_by_reason'] or 'chưa có'}")


if __name__ == "__main__":
    main()
