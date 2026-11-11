#!/usr/bin/env python3
"""H6 step 2: what the one rebuild changed. Reads only; writes diff.json and diff.md next to itself.

  graph      versions.jsonl and provision_events.jsonl, before (runs/rebuild_20261110/before) and after (data/derived)
  rows       the release files rebuilt into data/vilextime_dataset_h6 against runs/rebuild_20261110/before/release
             (dev, v1.0 test, silver 859), joined on row id
  recomputed test2, lo1/lo2 worksheets: not rebuilt by the chain, so each row's gold is read again from the new
             versions.jsonl (version whose [effective_from, effective_to) holds as_of)
  gold       the 150 + 45 blind-gold rows (data/review/gold_sample.tsv) as found in the rebuilt release

Usage: PYTHONPATH=src .venv/bin/python runs/rebuild_20261110/h6_diff.py
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "runs/rebuild_20261110"
BEFORE = HERE / "before"
NEWREL = ROOT / "data/vilextime_dataset_h6"
sys.path.insert(0, str(ROOT / "scripts/pipeline"))
import export_release  # noqa: E402


def rd(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def dig(*parts) -> bytes:
    return hashlib.md5(json.dumps(parts, ensure_ascii=False, sort_keys=True).encode()).digest()[:8]


def stream_versions(path, keep=None):
    """id -> (text digest, window digest); with `keep` (provision ids) also the rows of those lineages."""
    sig, rows = {}, collections.defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            v = json.loads(line)
            sig[v["id"]] = (dig(v["text"]), dig(v["effective_intervals"], v["created_by_event_id"], v["ended_by_event_id"]))
            if keep is not None and v["provision_id"] in keep:
                rows[v["provision_id"]].append({k: v[k] for k in ("id", "text", "effective_from", "effective_to", "ordinal")})
    return sig, rows


def graph_diff(keep):
    old, _ = stream_versions(BEFORE / "versions.jsonl")
    new, rows = stream_versions(ROOT / "data/derived/versions.jsonl", keep)
    only_old, only_new = old.keys() - new.keys(), new.keys() - old.keys()
    both = old.keys() & new.keys()
    text = sum(old[i][0] != new[i][0] for i in both)
    window = sum(old[i][1] != new[i][1] for i in both)
    ev_old = {e["id"]: e for e in map(json.loads, open(BEFORE / "provision_events.jsonl", encoding="utf-8"))}
    ev_new = {e["id"]: e for e in map(json.loads, open(ROOT / "data/derived/provision_events.jsonl", encoding="utf-8"))}
    moves = collections.Counter()
    moved = collections.defaultdict(list)
    for i in ev_old.keys() & ev_new.keys():
        a, b = ev_old[i], ev_new[i]
        ka, kb = (a["status"], a["status_reason"]), (b["status"], b["status_reason"])
        if ka != kb:
            moves[f"{ka[0]}/{ka[1]} -> {kb[0]}/{kb[1]}"] += 1
            moved[f"{ka[0]}/{ka[1]} -> {kb[0]}/{kb[1]}"].append(i)
        elif a.get("text_updates") != b.get("text_updates"):
            moves["same status, text_updates changed"] += 1
    return {
        "versions": {"old": len(old), "new": len(new), "only_old": len(only_old), "only_new": len(only_new),
                     "text_changed": text, "window_changed": window},
        "events": {"old": len(ev_old), "new": len(ev_new), "only_old": len(ev_old.keys() - ev_new.keys()),
                   "only_new": len(ev_new.keys() - ev_old.keys()), "status_moves": dict(moves.most_common())},
        "moved_samples": {k: v[:12] for k, v in moved.items()},
    }, rows


def row_key(r):
    return (r.get("answerable"), r.get("answer"), r.get("context"), r.get("version_id"), tuple(r.get("accepted_evidence") or ()))


def split_context(r, lead):
    """(lead-in text, the version's own text): `context` is the parent's lead-in, a newline, the answer."""
    ctx = r.get("context") or ""
    return (lead, ctx[len(lead) + 1:]) if lead and ctx.startswith(lead + "\n") else ("", ctx)


def compare_rows(old_rows, new_rows, excluded, label, old_lead=None, new_lead=None):
    """old/new: id -> published row. Returns counts and id lists."""
    out = collections.defaultdict(list)
    for i, o in old_rows.items():
        n = new_rows.get(i)
        if n is None:
            out["excluded:" + excluded[i]["code"] if i in excluded else "missing_from_new"].append(i)
        elif row_key(o) == row_key(n):
            out["same"].append(i)
        else:
            if o["answerable"] != n["answerable"]:
                out["answerable_flipped" + (":has->none" if o["answerable"] else ":none->has")].append(i)
            elif o["answer"] != n["answer"]:
                out["short_answer_changed"].append(i)
            elif o["context"] != n["context"]:
                a = split_context(o, (old_lead or {}).get(i, ""))
                b = split_context(n, (new_lead or {}).get(i, ""))
                out["version_text_changed" if a[1] != b[1] else "lead_in_only_changed"].append(i)
            elif o["version_id"] != n["version_id"]:
                out["version_id_changed_only"].append(i)
            else:
                out["evidence_changed_only"].append(i)
    out["new_only"] = [i for i in new_rows if i not in old_rows]
    return out


def main():
    out = {}
    sets, lead = {}, {}
    for name, fname, pick in (("dev", "vilextime.jsonl", lambda r: r["split"] == "dev"),
                              ("v1.0_test", "vilextime.jsonl", lambda r: r["split"] == "test"),
                              ("silver_old859", "vilextime_silver.jsonl", lambda r: True)):
        old = {r["id"]: r for r in rd(BEFORE / "release" / fname) if pick(r)}
        new = {r["id"]: r for r in rd(NEWREL / fname) if pick(r)}
        sets[name] = (old, new)
        lead[name] = ({m["id"]: (m["target"].get("lead_in") or "") for m in rd(BEFORE / "release/vilextime_meta.jsonl")},
                      {m["id"]: (m["target"].get("lead_in") or "") for m in rd(NEWREL / "vilextime_meta.jsonl")})
    excluded = {r["row_id"]: r for r in rd(NEWREL / "excluded_rows.jsonl")}
    # lineages of the recomputed sets
    wsets = {}
    for name, path in (("lo1_silver", "lo1_silver_worksheet.jsonl"), ("lo2", "lo2_moi_worksheet.jsonl"), ("lo0", "lo0_worksheet.jsonl")):
        rows = [dict(r, lineage_id=w["lineage_id"], group=w["group"]) for w in rd(BEFORE / "release" / path) for r in w["rows"]]
        wsets[name] = rows
    t2 = rd(BEFORE / "release/test2_release_v2.jsonl")
    wsets["test2"] = t2
    keep = {r["lineage_id"] for rows in wsets.values() for r in rows}
    out["graph"], vrows = graph_diff(keep)

    report = {}
    for name, (old, new) in sets.items():
        res = compare_rows(old, new, excluded, name, *lead[name])
        modes = collections.Counter(old[i]["as_of_strategy"] for i in old)
        mid = {i for i in old if old[i]["as_of_strategy"] == "giua_khoang"}
        report[name] = {"old_rows": len(old), "new_rows": len(new), "modes_old": dict(modes),
                        "counts": {k: len(v) for k, v in sorted(res.items())},
                        "counts_giua_khoang": {k: len([i for i in v if i in mid]) for k, v in sorted(res.items())},
                        "ids": {k: v for k, v in res.items() if k != "same"}}
    out["rebuilt_sets"] = report

    # recomputed sets
    recomputed = {}
    for name, rows in wsets.items():
        excl = export_release.row_exclusions(ROOT / "data", [dict(r, twin_of=r.get("twin_of")) for r in rows])
        c, ids = collections.Counter(), collections.defaultdict(list)
        for r in rows:
            vs = vrows.get(r["lineage_id"], [])
            hit = next((v for v in vs if v["effective_from"] and v["effective_from"] <= r["as_of"]
                        and (v["effective_to"] is None or r["as_of"] < v["effective_to"])), None)
            now_ans = hit is not None
            if r["id"] in excl:
                key = "excluded:" + excl[r["id"]]["code"]
            elif bool(r["answerable"]) != now_ans:
                key = "answerable_flipped:" + ("has->none" if r["answerable"] else "none->has")
            elif now_ans and (hit["id"] != r["version_id"]):
                key = "version_changed"
            elif now_ans and " ".join(hit["text"].split()) != " ".join((r.get("answer") or "").split()):
                key = "version_text_changed"
            else:
                key = "same"
            c[key] += 1
            if key != "same":
                ids[key].append(r["id"])
        recomputed[name] = {"rows": len(rows), "counts": dict(sorted(c.items())), "ids": dict(ids)}
    out["recomputed_sets"] = recomputed

    # derived release.jsonl (all 2,383 rows, including rows the published files leave out)
    od = {r["id"]: r for r in rd(BEFORE / "release/release.jsonl")}
    nd = {r["id"]: r for r in rd(ROOT / "data/derived/vilextime/release.jsonl")}
    dkey = lambda r: (r["answerable"], r["answer"], r["version_id"], tuple(r["accepted_evidence"]), r["split"])
    cnt, lins = collections.Counter(), collections.defaultdict(set)
    for i, o in od.items():
        sp = (o["split"], o["as_of_strategy"])
        if i not in nd:
            cnt[(*sp, "only_old")] += 1; lins[("only_old", o["split"], o["group"])].add(o["lineage_id"])
        elif dkey(o) != dkey(nd[i]):
            cnt[(*sp, "changed")] += 1
        else:
            cnt[(*sp, "same")] += 1
    for i, n in nd.items():
        if i not in od:
            cnt[(n["split"], n["as_of_strategy"], "only_new")] += 1; lins[("only_new", n["split"], n["group"])].add(n["lineage_id"])
    out["derived_release"] = {"rows_old": len(od), "rows_new": len(nd),
                              "counts": {"/".join(k): v for k, v in sorted(cnt.items())},
                              "lineages_only_old": {"/".join(k): sorted(v) for k, v in lins.items() if k[0] == "only_old"},
                              "lineages_only_new": {"/".join(k): sorted(v) for k, v in lins.items() if k[0] == "only_new"}}
    # gold
    gold = [x for path in ("data/review/gold_sample.tsv", "data/review/gold_dot2/gold_sample.tsv")
            for x in csv.DictReader(open(ROOT / path, encoding="utf-8"), delimiter="\t")]
    g = collections.Counter()
    gids = collections.defaultdict(list)
    where = {}
    for name, (old, new) in sets.items():
        for i in old:
            where.setdefault(i, name)
    for x in gold:
        i = x["id"]
        res = next((k for k, v in report.items() if i in v["ids"].get("missing_from_new", []) or any(i in ids for kk, ids in v["ids"].items())), None)
        status = "same"
        for name, rep in report.items():
            for kk, ids in rep["ids"].items():
                if i in ids:
                    status = kk
        g[status] += 1
        if status != "same":
            gids[status].append((x["khoa"], i))
    out["gold"] = {"rows": len(gold), "counts": dict(sorted(g.items())), "ids": {k: v for k, v in gids.items()}}
    (HERE / "diff.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    md = ["# H6 diff sau khi dựng lại (NHÁP, chưa kiểm độc lập)", "", "Sinh bởi `runs/rebuild_20261110/h6_diff.py`; số liệu đầy đủ ở `diff.json`.", ""]
    gr = out["graph"]
    md += ["## Đồ thị", "", f"- Phiên bản: {gr['versions']}", f"- Sự kiện: số dòng {gr['events']['old']} -> {gr['events']['new']}; chỉ có ở bản cũ {gr['events']['only_old']}, chỉ có ở bản mới {gr['events']['only_new']}",
           "- Chuyển trạng thái sự kiện (cùng id):", ""]
    md += [f"  - {k}: {v}" for k, v in gr["events"]["status_moves"].items()]
    md += ["", "## Theo tập (dòng đã dựng lại, so theo id)", "", "| Tập | dòng cũ | dòng mới | " + " | ".join(sorted({k for r in report.values() for k in r["counts"]})) + " |", ""]
    keys = sorted({k for r in report.values() for k in r["counts"]})
    md[-1:] = ["|---|---|---|" + "---|" * len(keys)]
    for name, r in report.items():
        md.append(f"| {name} | {r['old_rows']} | {r['new_rows']} | " + " | ".join(str(r["counts"].get(k, 0)) for k in keys) + " |")
    md += ["", "Chế độ `giua_khoang` (dòng được chấm ở tiêu đề):", ""]
    for name, r in report.items():
        md.append(f"- {name}: " + ", ".join(f"{k}={v}" for k, v in r["counts_giua_khoang"].items() if v))
    md += ["", "## Theo tập (tính lại từ versions.jsonl mới, không dựng lại file)", ""]
    for name, r in recomputed.items():
        md.append(f"- {name} ({r['rows']} dòng): " + ", ".join(f"{k}={v}" for k, v in r["counts"].items()))
    dr = out["derived_release"]
    md += ["", f"## release.jsonl dẫn xuất ({dr['rows_old']} -> {dr['rows_new']} dòng, so theo id)", ""]
    md += [f"- {k}: {v}" for k, v in dr["counts"].items() if not k.endswith("/same")]
    md += [f"- lineage rời release {k}: {len(v)}" for k, v in dr["lineages_only_old"].items()]
    md += [f"- lineage vào release {k}: {len(v)}" for k, v in dr["lineages_only_new"].items()]
    md += ["", f"## Gold mù ({out['gold']['rows']} dòng)", "", ", ".join(f"{k}={v}" for k, v in out["gold"]["counts"].items()), ""]
    md += ["## Id dòng dev đổi (mọi chế độ)", ""]
    for k, v in report["dev"]["ids"].items():
        md.append(f"- {k} ({len(v)}): " + "; ".join(v[:40]))
    (HERE / "diff.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md)[:6000])


if __name__ == "__main__":
    main()
