#!/usr/bin/env python3
"""Chẩn đoán T6 trên DEV (chỉ đọc): bảng từng dòng + đếm loại lỗi. Không gọi API, không đọc versions.jsonl.

    python scripts/check/t6_diag.py [--run runs/rebuild_20261110_dev] [--out docs/reports/chan-doan-t6-dev-20261111.tsv]

Recall của scorer dùng tiền tố mã đơn vị (version:<id>:n, asis:provision:<id>) để nhận lineage, nên
bản này tính lại không cần versions.jsonl; cột `recall@10 tính lại` phải khớp all.score.json (có kiểm).
Phân loại là quy tắc cơ học trên bằng chứng prompt, ghi ở classify().
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
import score_vilextime as sv  # noqa: E402

REL = "data/vilextime_dataset_h6"
SYS = ("b7", "b7plus", "b7pp", "proposed2", "proposed3")


def jl(path):
    return [json.loads(line) for line in open(path, encoding="utf-8")]


def in_lineage(unit, lineage):
    pid = lineage.split(":", 1)[1]
    return unit.startswith((f"version:{pid}:", f"asis:provision:{pid}"))


def hit_at(row, retrieved, k):
    acc = set(row["accepted_evidence"])
    return any(u in acc or in_lineage(u, row["lineage_id"]) for u in retrieved[:k])


def classify(row, twin, p2, pr2):
    """Trả (nhãn, lý do). Nhãn: ok | a | b | c | d | e (xem báo cáo).

    a: bộ lọc loại đơn vị gold ở dòng CÓ đáp án (gold có trong top10 của b7 mà không có trong prompt P)
    b: truy xuất/đồ thị không đưa căn cứ cần thiết vào prompt
    c: căn cứ có trong prompt nhưng mô hình trả lời sai
    d: câu trả lời của P chứa đúng lời văn gold của điều khoản (dòng đối ứng có đáp án) dù đơn vị gold không
       có trong prompt: văn bản khác có cùng lời văn, nhãn "không đáp án" bị nghi
    """
    ok = sv.correct(row, p2)
    if ok:
        return "ok", ""
    ev = row["accepted_evidence"][0]
    if not row["answerable"] and twin and p2.get("answerable") is not False and sv.contains(p2.get("answer") or "", twin["short_answer"]):
        return "d", "câu trả lời chứa đúng lời văn gold của điều khoản bị bãi bỏ (nguồn khác cùng lời văn)"
    if row["answerable"]:
        if not any(in_lineage(u, row["lineage_id"]) for u in pr2["ids"]):
            return "b", "đơn vị gold không có trong prompt"
        return "c", "đơn vị gold có trong prompt, mô hình không trích đúng/ từ chối"
    # không đáp án: mô hình trả lời có đáp án
    if ev not in pr2["ids"]:
        return "b", "lệnh bãi bỏ không vào prompt (đồ thị không đưa tới)"
    return "c", "lệnh bãi bỏ có trong prompt nhưng mô hình vẫn trả lời"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/rebuild_20261110_dev")
    ap.add_argument("--out", default="docs/reports/chan-doan-t6-dev-20261111.tsv")
    a = ap.parse_args()
    run = Path(a.run)
    meta = {m["id"]: m for m in jl(f"{REL}/vilextime_meta.jsonl")}
    rows = [r for r in jl(f"{REL}/vilextime.jsonl")
            if r["group"] == "T6" and r["split"] == "dev" and r["as_of_strategy"] == "giua_khoang"]
    for r in rows:
        r["short_answer"], r["answer"] = r["answer"], r["context"]
    preds = {s: {p["id"]: p for p in jl(run / "dev" / f"{s}.jsonl")} for s in SYS}
    prompts = {s: {p["id"]: p for p in jl(run / "prompts" / f"{s}.jsonl")} for s in ("proposed2", "proposed3")}
    twins = {r["lineage_id"]: r for r in rows if r["answerable"]}
    out, counts, rec = [], {}, {s: [0, 0] for s in SYS}
    for r in rows:
        i, m = r["id"], meta[r["id"]]
        by = m.get("repealed_by") or {}
        pr2, pr3 = prompts["proposed2"][i], prompts["proposed3"][i]
        ev = r["accepted_evidence"][0]
        d = {"id": i.replace("vilextime:T6:", ""), "dap_an": "có" if r["answerable"] else "không",
             "as_of": r["as_of"], "repeal_mode": m.get("repeal_mode"), "gold_lineage": r["lineage_id"],
             "gold_unit": ev if not r["answerable"] else r["version_id"],
             "bai_bo_boi": f"{by.get('event_id', '')} | tổ tiên {by.get('ancestor_id', '')}" if by else ""}
        for s in SYS:
            ret = preds[s][i].get("retrieved") or []
            h = hit_at(r, ret, 10)
            d[f"{s}_top10"] = int(h)
            rec[s][0] += h
            rec[s][1] += 1
            d[f"{s}_dung"] = int(sv.correct(r, preds[s][i]))
        p2 = preds["proposed2"][i]
        ret = p2.get("retrieved") or []
        d["p2_lineage_trong_top20"] = int(any(in_lineage(u, r["lineage_id"]) for u in ret[:20]))
        d["p2_event_gold_trong_retrieved"] = int(ev in ret)
        d["p2_event_gold_hang"] = ret.index(ev) + 1 if ev in ret else ""
        d["p2_prompt_so_doan"] = len(pr2["ids"])
        d["p2_prompt_co_lineage"] = int(any(in_lineage(u, r["lineage_id"]) for u in pr2["ids"]))
        d["p2_prompt_co_event_gold"] = int(ev in pr2["ids"])
        d["p2_tra_loi"] = (p2.get("answer") or "").replace("\n", " ")[:160]
        d["p2_answerable"] = p2.get("answerable")
        d["p2_citations"] = ",".join(p2.get("citations") or [])
        notes = [x for x in pr3["user"].split("\n") if "BÃI BỎ |" in x]
        targets = {by.get("ancestor_id"), r["lineage_id"]} - {None}
        d["p3_so_ghi_chu_bai_bo"] = len(notes)
        d["p3_ghi_chu_dung_dich"] = int(any(f"({t})" in n.split("đích bị bãi bỏ:")[1] for n in notes for t in targets))
        p3 = preds["proposed3"][i]
        d["p3_answerable"] = p3.get("answerable")
        d["p3_tra_loi"] = (p3.get("answer") or "").replace("\n", " ")[:160]
        d["loai_loi"], d["ly_do"] = classify(r, twins.get(r["lineage_id"]), p2, pr2)
        out.append(d)
        counts[(d["dap_an"], d["loai_loi"])] = counts.get((d["dap_an"], d["loai_loi"]), 0) + 1
    # kiểm với scorer
    score = json.load(open(run / "all.score.json"))
    for s in SYS:
        want = score[s]["giua_khoang"]["T6"]["recall@10"]
        got = rec[s][0] / rec[s][1]
        assert abs(want - got) < 1e-9, (s, want, got)
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter="\t")
        w.writeheader()
        w.writerows(out)
    print("recall@10 tính lại khớp all.score.json:", {s: f"{v[0]}/{v[1]}" for s, v in rec.items()})
    for k in sorted(counts):
        print(k, counts[k])
    for dap in ("có", "không"):
        sub = [d for d in out if d["dap_an"] == dap]
        print(dap, "n=", len(sub), {s: sum(d[f"{s}_top10"] for d in sub) for s in SYS},
              "đúng:", {s: sum(d[f"{s}_dung"] for d in sub) for s in SYS})


if __name__ == "__main__":
    main()
