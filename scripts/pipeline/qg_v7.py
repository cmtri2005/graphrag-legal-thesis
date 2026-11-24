#!/usr/bin/env python3
"""ViLexTime 7.0 — question pipeline: analyse the change, write 3 candidates, check them round-trip, keep one.

Design and sources: docs/reports/thiet-ke-sinh-cau-hoi-v7.md.

  1 analyse   one call, JSON: is each transition substantive (§R1 codes when not), the changed aspect, the shared
              part, a situation whose outcome differs. A lineage with no substantive transition stops here (T1 skips).
  2 generate  one call, JSON: 3 candidates, each with the answer it expects at every version.
  3 validate  generate_questions.validate (form, leaks, names_one_version).
  4 verify    separate calls that never see steps 1–2: answer the question from each version alone and from the 3
              siblings closest to it; then one judge call compares. Pass: answers differ across versions (T3: at least
              3 distinct), no sibling answers it, the question does not carry its own answer, T6 does not ask only
              yes/no. Candidates are checked in order; the first that passes is kept.

The model never writes the gold answer: that is the store's. Every call is logged (`<out>.calls.jsonl`).

    python scripts/pipeline/qg_v7.py --sample data/vilextime_v7/pilot/pilot_sample.jsonl \
        --out data/vilextime_v7/pilot/questions_v4.jsonl
    python scripts/pipeline/qg_v7.py --calibrate data/vilextime_v7/pilot/pilot_cham_filled.xlsx ...   # step 4 only
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import csv
import hashlib
import json
import re
import sqlite3
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_questions as g  # noqa: E402
from vilexgraph.llm import LLMError, complete  # noqa: E402

NONE = "KHONG_TRA_LOI"
REPEALED = "(Từ mốc này điều khoản không còn hiệu lực.)"
SIBLINGS_CHECKED = 3
_lock = threading.Lock()

ANALYSE = """Bạn là chuyên gia pháp luật Việt Nam. Đọc các phiên bản của một điều khoản và phân tích từng lần thay đổi.

Thay đổi KHÔNG thực chất (theo định nghĩa ViLexTime §R1):
- cosmetic_only: chỉ đổi hình thức, câu chữ, dấu câu, cách viết, không đổi quyền, nghĩa vụ, điều kiện, thời hạn, mức
  tiền, chủ thể hay phạm vi;
- rename_only: chỉ đổi tên cơ quan, đơn vị do sắp xếp bộ máy mà nhiệm vụ giữ nguyên;
- auto_reference_update: chỉ cập nhật dẫn chiếu mà văn bản đã quy định tự áp.
Chuyển sang cơ quan khác về chức năng, hay thay danh sách đơn vị hành chính không tương ứng 1-1, là thay đổi thực chất.

Chỉ in JSON, không thêm chữ nào khác:
{"chuyen": [{"tu": 1, "den": 2, "thuc_chat": true, "ma_neu_khong": null,
             "khia_canh_doi": "...", "noi_dung_doi": "bản trước ... ; bản sau ..."}],
 "phan_chung": "phần giống nhau ở mọi phiên bản, dùng để khoanh vùng câu hỏi",
 "tinh_huong_khac_ket_qua": "một tình huống điển hình mà mỗi phiên bản cho kết quả khác",
 "khia_canh_nen_hoi": "khía cạnh câu hỏi nên nhắm vào"}"""

GENERATE_FORMAT = """
---
ĐỊNH DẠNG ĐẦU RA CHO LƯỢT NÀY (thay cho quy định "đúng một dòng" ở trên): viết 3 câu hỏi khác nhau, mỗi câu tuân
thủ mọi ràng buộc ở trên, cùng DẠNG CÂU HỎI và MỞ ĐẦU được giao. Chỉ in JSON:
{"ung_vien": [{"cau_hoi": "...?", "dap_an_du_kien": ["đáp án ở bản 1", "đáp án ở bản 2"],
               "vi_sao_muc_anh_em_khong_tra_loi": "..."}]}
`dap_an_du_kien` có đúng một phần tử cho mỗi phiên bản, trích ngắn từ lời văn phiên bản đó. Nếu các phần tử giống
nhau thì câu hỏi đã hỏi chệch: viết lại câu đó. Nếu không viết được câu nào, in {"ung_vien": []}."""

# --fast (24/11, CMT: 12–15 USD for the full pipeline is too much): analysis and candidates in ONE call; a candidate
# is kept when it passes validate() and its own expected answers differ across versions. Round-trip verification
# only for the scarce groups (--verify-groups, default T3,T5), where a lost lineage cannot be replaced.
FAST_FORMAT = """
---
ĐỊNH DẠNG ĐẦU RA CHO LƯỢT NÀY (thay cho quy định "đúng một dòng" ở trên). Trước hết tự phân tích, rồi viết 3 câu hỏi
khác nhau, mỗi câu tuân thủ mọi ràng buộc ở trên, cùng DẠNG CÂU HỎI và MỞ ĐẦU được giao. Chỉ in JSON:
{"phan_tich": {"thay_doi_thuc_chat": true, "ma_neu_khong": null,
               "khia_canh_doi": "khía cạnh pháp lý đã đổi", "phan_chung": "phần giống nhau ở mọi phiên bản"},
 "ung_vien": [{"cau_hoi": "...?", "dap_an_du_kien": ["đáp án ở bản 1", "đáp án ở bản 2"]}]}
- `thay_doi_thuc_chat` = false khi mọi lần đổi chỉ là hình thức, câu chữ (`cosmetic_only`), chỉ đổi tên cơ quan do
  sắp xếp bộ máy mà nhiệm vụ giữ nguyên (`rename_only`), hay chỉ cập nhật dẫn chiếu tự áp (`auto_reference_update`);
  ghi mã vào `ma_neu_khong` và để `ung_vien` rỗng. Chỉ có một phiên bản thì bỏ qua phân tích (để true).
- `dap_an_du_kien` có đúng một phần tử cho mỗi phiên bản, trích ngắn từ lời văn phiên bản đó. Các phần tử phải khác
  nhau về nội dung; nếu giống nhau, câu hỏi đã hỏi chệch: viết lại.
- Nếu lời văn dẫn chiếu một khoản, điều khác ("quy định tại khoản 5"), đừng nêu số: gọi đúng chủ đề."""

ANSWER = """Trả lời câu hỏi CHỈ dựa vào đoạn văn được cho, không dùng hiểu biết nào khác. Trả lời ngắn, trích ý từ đoạn
văn. Nếu đoạn văn không chứa câu trả lời cho đúng điều được hỏi, chỉ in: KHONG_TRA_LOI"""

ANSWER_SIBLING = """Đọc đoạn văn và câu hỏi. Đoạn văn này có trả lời được câu hỏi, dù chỉ MỘT PHẦN, không? Nếu có, in phần
trả lời rút từ đoạn văn. Nếu đoạn văn không liên quan đến điều được hỏi, chỉ in: KHONG_TRA_LOI"""

JUDGE = """Bạn kiểm tra chất lượng một câu hỏi trong bộ dữ liệu hỏi đáp pháp luật theo thời gian. Cùng một câu hỏi được
hỏi ở nhiều mốc; mỗi mốc áp dụng một phiên bản của điều khoản. Bạn nhận câu hỏi, lời văn các phiên bản, chỗ thay đổi
do máy tính, các câu trả lời mà một người đọc độc lập rút ra từ từng phiên bản và từ từng mục anh em (khoản, điểm
khác cùng đơn vị cha).

Đánh giá, chỉ in JSON:
{"so_dap_an_khac_nhau": <số câu trả lời khác nhau giữa các phiên bản. Hai câu trả lời KHÁC nhau khi người hỏi nhận
                         được nội dung khác: thêm hay bớt một thời hạn, một chủ thể, một điều kiện, một khoản tiền,
                         một mục trong danh sách, hay phạm vi rộng hẹp khác nhau. Chỉ tính là MỘT khi hai câu trả lời
                         cùng nghĩa, chỉ khác câu chữ, dấu câu, hay tên gọi cùng một thứ>,
 "phien_ban_khong_tra_loi_duoc": [<số thứ tự phiên bản có câu trả lời KHONG_TRA_LOI hoặc không đúng điều được hỏi>],
 "muc_anh_em_tra_loi_duoc": [<số thứ tự mục anh em trả lời được câu hỏi, dù chỉ một phần: khi đó câu hỏi chưa ghim
                              riêng điều khoản đích>],
 "cau_hoi_chua_san_dap_an": <true nếu câu hỏi đã nêu sẵn nội dung trả lời, HOẶC dùng một cụm từ nằm trong phần bị
                             thêm, bị bỏ hay bị đổi ở mục CHỖ THAY ĐỔI (cụm từ chỉ một phiên bản có)>,
 "chi_hoi_co_khong": <true nếu câu hỏi chỉ hỏi có/không>,
 "ghi_chu": "một câu"}"""


# Step-4 failures in the words the model needs to fix them (Self-Refine style revision round).
JUDGE_HINTS = {
    "versions_agree": "Các phiên bản cho cùng một câu trả lời: câu hỏi đã hỏi vào phần không đổi. Hãy hỏi vào chỗ "
                      "đã thay đổi.",
    "version_unanswerable": "Có phiên bản không trả lời được điều được hỏi: hỏi vào khía cạnh mà mọi phiên bản đều "
                            "quy định, với chỗ thay đổi nằm trong khía cạnh đó.",
    "sibling_answers": "Một khoản, điểm anh em cũng trả lời được (một phần): câu hỏi còn quá rộng, thêm một chi tiết "
                       "riêng của điều khoản được giao.",
    "leaks": "Câu hỏi đã nêu sẵn nội dung trả lời hoặc dùng cụm từ chỉ một phiên bản có.",
    "yes_no_only": "Không hỏi dạng có/không; hỏi nội dung quy định.",
}
ROUNDS = 2


def feedback(tried):
    lines = ["", "---", "Các câu bạn vừa viết đều không đạt:"]
    for t in tried:
        hints = [g.RETRY_HINTS.get(r.split(":")[0]) or JUDGE_HINTS.get(r) or r for r in t["fail"]]
        lines.append(f"«{t['cau_hoi']}» — " + " ".join(hints))
    lines.append("Viết lại 3 câu hỏi khác, sửa đúng các lỗi trên, giữ nguyên mọi ràng buộc và định dạng JSON. Lượt này "
                 "BẮT BUỘC có 3 câu, không được trả danh sách rỗng. Nếu lời văn dẫn chiếu một khoản, điều khác (\"quy "
                 "định tại khoản 5\"), đừng nêu số: gọi đúng chủ đề của đáp án và hỏi vào chỗ đổi.")
    return "\n".join(lines)


def call(system, user, args, log, step, lid, max_tokens=2048):
    c = complete(system, user, provider=args.provider, model=args.model, temperature=0.0, max_tokens=max_tokens,
                 seed=args.seed, timeout=180)
    with _lock:
        log.write(json.dumps({"lineage_id": lid, "step": step, "system_sha": sha(system), "user_sha": sha(user),
                              "user": user, "reply": c.text, "served_model": c.served_model,
                              "prompt_tokens": c.prompt_tokens, "completion_tokens": c.completion_tokens},
                             ensure_ascii=False) + "\n")
        log.flush()
    return c


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON")
    return json.loads(m.group(0))


def version_texts(records):
    """Every distinct state in time order; a repealed state is shown as such."""
    out = []
    for r in sorted(records, key=lambda r: r["as_of"]):
        t = r["answer"] or REPEALED
        if t not in out:
            out.append(t)
    return out


def nearest(question, sibs, k=SIBLINGS_CHECKED):
    q = set(g.words(question))
    return sorted(sibs, key=lambda s: -len(q & set(g.words(s))))[:k]


def verify(question, records, sibs, args, log, lid):
    """Step 4. Returns (passed, reasons, judge)."""
    group = records[0]["group"]
    lead = records[0]["target"]["lead_in"] or ""
    texts = version_texts(records)
    frame = f"TÊN VĂN BẢN: {records[0]['target']['document_title']}\nCÂU DẪN: {lead}\n"
    answers = []
    for t in texts:
        answers.append(NONE if t == REPEALED else
                       call(ANSWER, f"{frame}ĐOẠN VĂN: {t}\n\nCÂU HỎI: {question}", args, log, "answer_version",
                            lid, 512).text)
    checked = nearest(question, sibs)
    sib_answers = [call(ANSWER_SIBLING, f"{frame}ĐOẠN VĂN: {s}\n\nCÂU HỎI: {question}", args, log,
                        "answer_sibling", lid, 512).text for s in checked]
    body = [f"CÂU HỎI: {question}", ""]
    body += [f"PHIÊN BẢN {n}: {t}\n  → trả lời: {a}" for n, (t, a) in enumerate(zip(texts, answers), 1)]
    worded = [t for t in texts if t != REPEALED]
    if len(worded) > 1:
        body += ["CHỖ THAY ĐỔI (máy tính):"] + [f"  [{n}→{n + 1}] {g.changes(worded[n - 1], worded[n])}"
                                              for n in range(1, len(worded))]
    body += [f"MỤC ANH EM {n}: {s}\n  → trả lời: {a}" for n, (s, a) in enumerate(zip(checked, sib_answers), 1)]
    j = parse_json(call(JUDGE, "\n".join(body), args, log, "judge", lid, 1024).text)
    reasons = []
    need = 1 if group == "T1" else 3 if group == "T3" else 2
    distinct = int(j.get("so_dap_an_khac_nhau") or 0)
    if REPEALED in texts and any(a.strip() != NONE for a in answers):
        distinct = max(distinct, 1) + 1   # "no longer in force" is an answer of its own; the judge counts worded ones
    if distinct < need:
        reasons.append("versions_agree")
    if [v for v in j.get("phien_ban_khong_tra_loi_duoc") or [] if texts[int(v) - 1:int(v)] != [REPEALED]]:
        reasons.append("version_unanswerable")
    if j.get("muc_anh_em_tra_loi_duoc"):
        reasons.append("sibling_answers")
    if j.get("cau_hoi_chua_san_dap_an"):
        reasons.append("leaks")
    if group == "T6" and j.get("chi_hoi_co_khong"):
        reasons.append("yes_no_only")
    return not reasons, reasons, {**j, "answers": answers, "sibling_answers": sib_answers}


def run_lineage(lid, records, sibs, args, log):
    group = records[0]["group"]
    near = any(r.get("near_identical") for r in records)
    message, context, versions = g.user_prompt(records, sibs)
    row = {"lineage_id": lid, "group": group, "question": None, "rejected_reason": None, "raw": None,
           "provider": args.provider, "model": args.model, "seed": args.seed, "pipeline": "qg_v7",
           "generated_at": datetime.now(timezone.utc).date().isoformat()}
    try:
        analysis = None
        if len(versions) > 1 and group != "T6":
            analysis = parse_json(call(ANALYSE, message, args, log, "analyse", lid).text)
            if not any(c.get("thuc_chat") for c in analysis.get("chuyen", [])):
                codes = sorted({c.get("ma_neu_khong") or "cosmetic_only" for c in analysis.get("chuyen", [])})
                return {**row, "rejected_reason": "no_substantive_change:" + ",".join(codes), "analysis": analysis}
        system = g.system_prompt(group, near) + GENERATE_FORMAT
        user = message + (f"\n\nPHÂN TÍCH THAY ĐỔI (do chuyên gia lập, dùng để chọn khía cạnh hỏi):\n"
                          f"{json.dumps(analysis, ensure_ascii=False)}" if analysis else "")
        tried, prompt = [], user
        for rnd in range(1, ROUNDS + 1):
            try:
                cands = parse_json(call(system, prompt, args, log, f"generate_r{rnd}", lid, 3072).text)["ung_vien"]
            except (ValueError, KeyError, json.JSONDecodeError):
                cands = []
            this = []
            for c in cands[:3]:
                q = (c.get("cau_hoi") or "").strip()
                reason = g.validate(q, context, versions)
                if reason:
                    this.append({"round": rnd, "cau_hoi": q, "fail": [reason]})
                    continue
                ok, reasons, judge = verify(q, records, sibs, args, log, lid)
                this.append({"round": rnd, "cau_hoi": q, "fail": reasons, "judge": judge})
                if ok:
                    return {**row, "question": q, "analysis": analysis, "candidates": tried + this,
                            "rounds": rnd, "system_sha": sha(system)}
            tried += this
            if not this:
                break
            prompt = user + feedback(this)
        return {**row, "rejected_reason": "qg_failed:" + ";".join(",".join(t["fail"]) for t in tried) if tried
                else "qg_failed:no_candidate", "raw": tried[0]["cau_hoi"] if tried else None,
                "analysis": analysis, "candidates": tried, "system_sha": sha(system)}
    except (LLMError, ValueError, json.JSONDecodeError) as e:
        return {**row, "rejected_reason": f"error:{type(e).__name__}", "raw": str(e)[:300]}


def distinct_answers(cand):
    return len({" ".join(g.words(a)) for a in cand.get("dap_an_du_kien") or [] if a})


def run_fast(lid, records, sibs, args, log):
    group = records[0]["group"]
    near = any(r.get("near_identical") for r in records)
    message, context, versions = g.user_prompt(records, sibs)
    need = 3 if group == "T3" else 2 if len(versions) > 1 else 1
    row = {"lineage_id": lid, "group": group, "question": None, "rejected_reason": None, "raw": None,
           "provider": args.provider, "model": args.model, "seed": args.seed, "pipeline": "qg_v7_fast",
           "generated_at": datetime.now(timezone.utc).date().isoformat()}
    system = g.system_prompt(group, near) + FAST_FORMAT
    row["system_sha"] = sha(system)
    tried, prompt, analysis = [], message, None
    try:
        for rnd in range(1, ROUNDS + 1):
            try:
                out = parse_json(call(system, prompt, args, log, f"fast_r{rnd}", lid, 2048).text)
            except (ValueError, json.JSONDecodeError):
                out = {}
            analysis = analysis or out.get("phan_tich")
            if (rnd == 1 and len(versions) > 1 and group != "T6" and analysis
                    and analysis.get("thay_doi_thuc_chat") is False):
                return {**row, "rejected_reason": f"no_substantive_change:{analysis.get('ma_neu_khong')}",
                        "analysis": analysis}
            this = []
            for c in (out.get("ung_vien") or [])[:3]:
                q = (c.get("cau_hoi") or "").strip()
                reason = g.validate(q, context, versions) or (
                    "versions_agree" if group not in ("T1", "T6") and distinct_answers(c) < need else None)
                if reason:
                    this.append({"round": rnd, "cau_hoi": q, "fail": [reason]})
                    continue
                if group in args.verify_groups:
                    ok, reasons, judge = verify(q, records, sibs, args, log, lid)
                    this.append({"round": rnd, "cau_hoi": q, "fail": reasons, "judge": judge})
                    if not ok:
                        continue
                else:
                    this.append({"round": rnd, "cau_hoi": q, "fail": []})
                return {**row, "question": q, "analysis": analysis, "candidates": tried + this, "rounds": rnd}
            tried += this
            prompt = message + (feedback(this) if this else "\n\n(Lượt trước không in được JSON hợp lệ. Chỉ in JSON.)")
        return {**row, "rejected_reason": "qg_failed:" + ";".join(",".join(t["fail"]) for t in tried),
                "raw": tried[0]["cau_hoi"] if tried else None, "analysis": analysis, "candidates": tried}
    except (LLMError, ValueError, json.JSONDecodeError) as e:
        return {**row, "rejected_reason": f"error:{type(e).__name__}", "raw": str(e)[:300], "candidates": tried}


def load(sample_path):
    sample = [json.loads(x) for x in open(sample_path, encoding="utf-8")]
    want = {s["lineage_id"] for s in sample}
    recs = collections.defaultdict(list)
    for grp in sorted({s["group"] for s in sample}):
        for x in open(ROOT / f"data/derived/vilextime/{grp}.jsonl", encoding="utf-8"):
            r = json.loads(x)
            if r["lineage_id"] in want:
                recs[r["lineage_id"]].append(r)
    db = sqlite3.connect(f"file:{ROOT / 'data/temporal.sqlite'}?mode=ro", uri=True)
    sibs = g.sibling_index(db, [rs[0]["target"] for rs in recs.values()], ROOT / "data/derived/versions.jsonl")
    order = [s["lineage_id"] for s in sorted(sample, key=lambda s: (s["group"], s["rank"]))]
    return order, recs, sibs


def calibrate(args, order, recs, sibs, log):
    """Step 4 on the questions a person already graded: does the machine agree with the person?"""
    from openpyxl import load_workbook
    ws = load_workbook(args.calibrate, read_only=True)["Chấm"]
    rows = list(ws.iter_rows(values_only=True))
    graded = [dict(zip(rows[0], r)) for r in rows[1:]]
    key = {r["khoa"]: r for r in csv.DictReader(open(Path(args.calibrate).with_name("pilot_cham_key.tsv"),
                                                     encoding="utf-8"), delimiter="\t")}
    graded = [d for d in graded if d["tu_nhien"] is not None]

    def one(d):
        lid = key[d["khoa"]]["lineage_id"]
        ok, reasons, _ = verify(d["cau_hoi"], recs[lid], sibs.get(recs[lid][0]["target"]["provision_id"], []),
                                args, log, lid)
        human = d["hoi_vao_cho_doi"] == "có" and d["tra_loi_duy_nhat"] == "có" and d["lo_dap_an"] == "không"
        return {"khoa": d["khoa"], "human_ok": human, "machine_ok": ok, "reasons": reasons,
                "human": [d["hoi_vao_cho_doi"], d["tra_loi_duy_nhat"], d["lo_dap_an"]]}

    with cf.ThreadPoolExecutor(args.workers) as ex:
        res = list(ex.map(one, graded))
    out = Path(args.out).with_suffix(".calibration.jsonl")
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in res), encoding="utf-8")
    t = collections.Counter((r["human_ok"], r["machine_ok"]) for r in res)
    print(f"người đạt & máy đạt {t[True, True]} · người đạt, máy loại {t[True, False]} · "
          f"người loại, máy đạt {t[False, True]} · cả hai loại {t[False, False]}")
    for name, col, bad, rs in (("hỏi chệch", 0, "không", "versions_agree"), ("không duy nhất", 1, "không",
                               "sibling_answers"), ("lộ", 2, "có", "leaks")):
        c = collections.Counter((r["human"][col] == bad, rs in r["reasons"]) for r in res)
        print(f"  {name}: người nói lỗi {c[True, True] + c[True, False]}, máy bắt {c[True, True]}; "
              f"máy báo nhầm {c[False, True]}")
    print("->", out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--provider", default="chutes")
    ap.add_argument("--model")
    ap.add_argument("--seed", type=int, default=20261124)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--fast", action="store_true", help="one call per round; round-trip only for --verify-groups")
    ap.add_argument("--verify-groups", default="T3,T5")
    ap.add_argument("--calibrate", type=Path, help="graded pilot sheet: run step 4 on its questions only")
    args = ap.parse_args()
    args.verify_groups = set(args.verify_groups.split(",")) if args.verify_groups else set()
    order, recs, sibs = load(args.sample)
    with open(args.out.with_suffix(".calls.jsonl"), "a", encoding="utf-8") as log:
        if args.calibrate:
            return calibrate(args, order, recs, sibs, log)
        done = {json.loads(x)["lineage_id"] for x in open(args.out, encoding="utf-8")} if args.out.exists() else set()
        todo = [lid for lid in order if lid not in done]
        print(f"{len(order)} lineage · {len(done)} đã có · {len(todo)} sẽ chạy")
        stats = collections.Counter()
        with open(args.out, "a", encoding="utf-8") as out, cf.ThreadPoolExecutor(args.workers) as ex:
            futs = {ex.submit(run_fast if args.fast else run_lineage, lid, recs[lid], sibs.get(recs[lid][0]["target"]["provision_id"], []),
                              args, log): lid for lid in todo}
            for n, f in enumerate(cf.as_completed(futs), 1):
                row = f.result()
                with _lock:
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                    out.flush()
                stats["ok" if row["question"] else row["rejected_reason"].split(":")[0]] += 1
                if n % 10 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)} " + " ".join(f"{k}={v}" for k, v in stats.most_common()), flush=True)


if __name__ == "__main__":
    main()
