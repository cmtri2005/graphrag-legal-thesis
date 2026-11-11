#!/usr/bin/env python3
"""H6: the named regression cases of the brief, read from the rebuilt data (before = runs/rebuild_20261110/before).
Usage: PYTHONPATH=src .venv/bin/python runs/rebuild_20261110/regress.py"""
import json, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "runs/rebuild_20261110/before"
res = {}

def events(path):
    return {e["id"]: e for e in map(json.loads, open(path, encoding="utf-8"))}

old, new = events(B / "provision_events.jsonl"), events(ROOT / "data/derived/provision_events.jsonl")
def state(i):
    return (new[i]["status"], new[i]["status_reason"]) if i in new else None
bad = "c55a1c5bbffc66ecdd9819ca ac3635a1c938aeced07b4d48 a06cec87147e46da14c23765 1b558f6621353f56d711c557 5fe19fa279959c4784aee27e 2393948ffe64058d09e27a86 5886cd07ca13d21218cdfcc8 33508b74d8235979792f1cae 2895e0f823ba7a105100f596 c1894c695d47db0a87a281d0".split()
good = "9afaf51289952078b330129d 0fe6f6d966d8f2988f97d5b8 3a25da91c8871a628fb13624 2960d18b566d003a673fd3f9".split()
by_suffix = lambda s: [i for i in new if i.endswith(s)]
g108 = [i for i, e in new.items() if e["actor_number"] == "16/2026/TT-BXD" and e["document_number"] == "12/2017/TT-BXD"]
res["L1_g108_8"] = {i[-8:]: state(i) for i in g108}
res["L1_tableA_10_wrong"] = {s: [state(i) for i in by_suffix(s)] for s in bad}
res["L1_tableA_4_right"] = {s: [state(i) for i in by_suffix(s)] for s in good}
res["L1_pass"] = (len(g108) == 8 and all(state(i) == ("needs_review", "partial_repeal") for i in g108)
                  and all(state(i) == ("needs_review", "partial_repeal") for s in bad for i in by_suffix(s))
                  and all(state(i)[0] in ("auto_accepted", "verified") for s in good for i in by_suffix(s)))
q2_24 = [i for i in new if i.endswith("07383c7e512b") or ("113/2005/TT-BTC" == new[i]["actor_number"] and new[i]["document_number"] == "86/2000/TT-BTC")]
res["L2_Q2_24"] = {i: state(i) for i in q2_24}
res["L2_Q2_29"] = state("event:139887:a57354e9663d01604e3f58da")
db = sqlite3.connect(f"file:{ROOT}/data/temporal.sqlite?mode=ro", uri=True)
res["L2_31760_effective_to"] = db.execute("select number,effective_to from documents where id='document:31760'").fetchone()
tt12 = [i for i, e in new.items() if e["actor_number"] == "12/2023/TT-BNV" and e["target_document_id"] == "document:31760"]
res["L2_31760_events"] = {i: (state(i), new[i]["effective_on"]) for i in tt12}
nd161 = [i for i, e in new.items() if e["document_number"] == "161/2004/NĐ-CP" and e["locator"] is None]
res["L2_161_2004_events"] = {i: (state(i), new[i]["effective_on"], new[i]["actor_number"]) for i in nd161}
res["L2_161_2004_effective_to"] = db.execute("select number,effective_to,raw_status_code from documents where number like '161/2004%'").fetchall()
res["L2_applied_count"] = sum(1 for e in new.values() if e["locator"] is None and e["status"] == "auto_accepted" and old.get(e["id"], {}).get("status") == "needs_review")
res["L2_still_review_document_scope"] = sum(1 for e in new.values() if e["locator"] is None and e["status_reason"] == "document_scope")
res["L2_to_partial_repeal"] = sum(1 for e in new.values() if e["locator"] is None and e["status_reason"] == "partial_repeal")
# L4: first-version wording
def v1(lineage, path):
    want = f"version:{lineage.split(':',1)[1]}:1"
    with open(path, encoding="utf-8") as f:
        for line in f:
            if want in line[:80]:
                v = json.loads(line)
                if v["id"] == want:
                    return v["text"]
cases = {"NĐ209/2013 Đ3 k11": ("provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0", "Bộ Tài chính chủ trì"),
         "BLTTHS Đ212 k1": ("provision:5003ac4e-eb7e-11f0-a0a3-c9aae40c2eb7", "Khi cần thiết, Hội đồng xét xử"),
         "NĐ218/2013 Đ4 k2a": ("provision:ce3f81c0-2d53-11f1-8e98-9d68213c7640", "Danh mục loại hình"),
         "QĐ737/2001 Đ46 k1 (không đổi)": ("provision:ed6be7ba-2807-11f1-b919-d73281fdb594", None),
         "TTLT01/2001 mục 4.2 (không đổi)": ("provision:dfeea17c-e16c-11f0-ab71-f3424eab00a5", None)}
res["L4"] = {}
for name, (lin, phrase) in cases.items():
    a, b = v1(lin, B / "versions.jsonl"), v1(lin, ROOT / "data/derived/versions.jsonl")
    res["L4"][name] = {"has_phrase_before": bool(phrase and a and phrase in a), "has_phrase_after": bool(phrase and b and phrase in b),
                       "unchanged": a == b, "len_before": len(a or ""), "len_after": len(b or "")}
(ROOT / "runs/rebuild_20261110/regress.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
