#!/usr/bin/env python3
"""ViLexTime — trang gán nhãn cục bộ cho phiếu `kiem` (thay Excel khi mỏi mắt).

Mỗi lần một dòng, chữ to, chữ đổi tô đỏ, phím tắt, tự đo phút, tự lưu về TSV sau mỗi dòng.
TSV vẫn là bản ghi chính: `crosscheck.py kappa --set kiem` và `adjudicate.py` đọc nguyên như cũ.
Luật kiểm nhãn giống `crosscheck_xlsx.py import` (từ vựng, note bắt buộc, bốn ô hướng dẫn 3.0).

    python scripts/review/label_ui.py --who A          # mở http://127.0.0.1:8765
    python scripts/review/label_ui.py --who B --ids data/review/kiem_cheo.txt   # B: chỉ các dòng gán chéo

Sửa câu chữ (CMT 21/10): câu hỏi (cả lineage) và đáp án ngắn (cả phiên bản) sửa được ngay trên trang. Lưu thì
ghi vào data/vilextime/questions.jsonl, short_answers.jsonl (giữ bản model ở `model_question`,
`model_short_answer`, ghi `edited_by`, `edited_at`) và vào phiếu TSV, để lần dựng lại sau mang chúng vào bản
phát hành mà nhãn vẫn khớp. Lời văn luật, ngày, phiên bản do đồ thị suy ra thì không sửa tay: sai là khong_dat.
Đáp án ngắn phải là đoạn trích của đáp án hoặc câu dẫn (enrich_vilextime.check_short_answer).

Dòng thời gian phiên bản (một ô mỗi phiên bản, ghim ở mốc hỏi) đọc lại cột `cac_phien_ban`; ô so sánh hai
phiên bản cạnh nhau (cũ trái, mới phải, chữ khác nhau tô ở cả hai bên) lấy lời văn từ các dòng cùng lineage của
chính phiếu, nên trùng chữ với cột `answer`.

Dòng thuộc lineage trong phiếu gold độc lập của người đó (gold_X.tsv) bị ẩn tới khi phiếu gold điền xong:
gold phải gán mù, còn trang này cho thấy đáp án của máy.

Phím (khi không đang gõ trong ô): D = dat · K = khong_dat · 1-9,0,q,w,e,r,t = mã lý do ·
Enter = lưu và sang dòng chưa gán kế tiếp · ←/→ = lùi/tới (không lưu) · N = vào ô note.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import sys
import threading
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crosscheck import GUIDELINE, KIEM_FIELDS, REASONS, VERDICTS  # noqa: E402
from crosscheck_xlsx import DECISION, REASON_HELP, changed_spans, missing_fields  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from enrich_vilextime import check_short_answer  # noqa: E402

LABELS = ("verdict", "reasons", "note", "suggestion", *KIEM_FIELDS)
KEYS = "1234567890qwert"
LOCK = threading.Lock()
FAMILIES = [("Đáp án sai", ("gold_wrong", "transitional_rule")),
            ("Câu hỏi tệ", ("question_ambiguous", "question_leaks", "unanswerable_as_asked")),
            ("Không đáng làm test", ("group_mismatch", "rename_only", "cosmetic_only", "auto_reference_update",
                                     "reference_only")),
            ("Pháp lý phức tạp", ("relocated", "relocation_unclear", "superseded_by_other_norm",
                                  "restructuring_2025", "other"))]
KEY_ORDER = [c for _, cs in FAMILIES for c in cs]
assert set(KEY_ORDER) == REASONS


def load(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        return list(r.fieldnames), list(r)


def spans_for(rows: list[dict]) -> dict[str, list[list[int]]]:
    """id -> changed spans of its answer against the other versions of the lineage (as the xlsx does)."""
    versions = collections.defaultdict(set)
    for r in rows:
        if r["answer"] and not r["answer"].startswith("(không có đáp án"):
            versions[r["lineage_id"]].add(r["answer"])
    return {r["id"]: [list(s) for s in changed_spans(r["answer"], sorted(versions[r["lineage_id"]] - {r["answer"]}))]
            for r in rows if r["answer"] and len(versions[r["lineage_id"]]) > 1}


# kiem_hints.timeline writes one line per version and, for T6, one for the repeal
TL_VERSION = re.compile(r"^\[(\d+)\] (\S+) → (\S+)(?: · (.*?))?(\s+◀ đáp án của dòng này)?$")
TL_REPEAL = re.compile(r"^Hết hiệu lực từ (\S+) \((.+?)\) bởi (.+)$")


def timeline(row: dict) -> dict:
    """The row's version chain for the timeline bar: `cac_phien_ban` read back, or for a row without one (T1) its
    single version. A provision repealed through its ancestor keeps an open window of its own; the repeal ends it."""
    versions, repeal = [], None
    for line in (row.get("cac_phien_ban") or "").splitlines():
        if m := TL_VERSION.match(line):
            n, start, end, by, mine = m.groups()
            versions.append({"n": int(n), "from": None if start == "?" else start,
                             "to": None if end == "nay" else end, "by": by or "", "mine": bool(mine)})
        elif m := TL_REPEAL.match(line):
            repeal = {"on": m[1], "mode": m[2], "by": m[3]}
    if not versions:
        versions = [{"n": 1, "from": row.get("valid_from") or None, "to": row.get("valid_to") or None,
                     "by": "bản duy nhất", "mine": not row["answer"].startswith("(không có đáp án")}]
    if repeal:
        for v in versions:
            if v["to"] is None or v["to"] > repeal["on"]:
                v["to"] = repeal["on"]
    return {"versions": versions, "repeal": repeal}


def version_id(row: dict) -> str | None:
    """The row's answer version as the release names it: kiem_hints writes ◀ from that id (T1: version 1)."""
    mine = next((v for v in timeline(row)["versions"] if v["mine"]), None)
    return f"version:{row['lineage_id'].split(':', 1)[1]}:{mine['n']}" if mine else None


def compare(rows: list[dict]) -> dict[str, dict]:
    """lineage -> the versions it answers with, in order, and each change between two of them with the words that
    differ marked on both sides (T2, T4, T3, also T5a). A lineage with a single answer has nothing to compare."""
    found: dict[str, dict[int, dict]] = collections.defaultdict(dict)
    for r in rows:
        mine = next((v for v in timeline(r)["versions"] if v["mine"]), None)
        if mine and r["answer"] and not r["answer"].startswith("(không có đáp án"):
            found[r["lineage_id"]].setdefault(mine["n"], {**mine, "text": r["answer"], "lead_in": r.get("lead_in") or ""})
    out = {}
    for lid, by_n in found.items():
        vs = [by_n[n] for n in sorted(by_n)]
        if len(vs) > 1:
            out[lid] = {"versions": vs, "pairs": [{"a": x["n"], "b": y["n"],
                                                  "sa": changed_spans(x["text"], [y["text"]]),
                                                  "sb": changed_spans(y["text"], [x["text"]])}
                                                 for x, y in zip(vs, vs[1:])]}
    return out


def held_back(review: Path, who: str) -> set[str]:
    """Lineages of this annotator's independent gold sheet, out of sight until that sheet is filled: this page
    shows the KG's answer, and the gold must be read blind (independent_gold.py)."""
    gold, sample = review / f"gold_{who}.tsv", review / "gold_sample.tsv"
    if not gold.exists() or not sample.exists() or all(r["hieu_luc"] for r in load(gold)[1]):
        return set()
    return {r["lineage_id"] for r in load(sample)[1] if who in r["annotators"]}


def validate(row: dict, new: dict, who: str = "A") -> list[str]:
    verdict, note = new["verdict"], new["note"]
    codes = [c.strip() for c in new["reasons"].split(",") if c.strip()]
    errors = [] if verdict in VERDICTS else ["chưa chọn dat / khong_dat"]
    errors += [f"mã `{c}` ngoài từ vựng" for c in codes if c not in REASONS]
    if verdict == "khong_dat" and not codes:
        errors.append("khong_dat nhưng chưa chọn mã lý do")
    if verdict == "dat" and codes:
        errors.append("dat nhưng vẫn còn mã lý do")
    needs = {"gold_wrong", "other", "relocated", "superseded_by_other_norm"} & set(codes)
    if needs and not note:
        errors.append(f"{'/'.join(sorted(needs))} bắt buộc có note")
    return errors + missing_fields(row["group"], new, who)   # saving here is labelling now, under GUIDELINE


def rewrite_jsonl(path: Path, match, change) -> int:
    """Apply `change` to every line `match` picks; the number changed."""
    items = [json.loads(line) for line in path.open(encoding="utf-8")]
    hits = [x for x in items if match(x)]
    for x in hits:
        change(x)
    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in items), encoding="utf-8")
    os.replace(tmp, path)
    return len(hits)


def check_edits(row: dict, edits: dict) -> list[str]:
    question, short = edits.get("question"), edits.get("short_answer")
    errors = ["câu hỏi không được để trống"] if question is not None and not question else []
    if short is not None:
        if row["answer"].startswith("(không có đáp án"):
            errors.append("dòng không có đáp án thì không có đáp án ngắn")
        elif not check_short_answer(short, row["answer"], row["lead_in"]):
            errors.append("đáp án ngắn phải là đoạn trích nguyên văn của đáp án hoặc câu dẫn (nhiều đoạn cách nhau …)")
    return errors


def save(path: Path, rid: str, new: dict, edits: dict | None = None, data: Path | None = None,
         version_of: dict[str, str] | None = None, who: str = "A") -> tuple[list[dict], list[str]]:
    """Save one row's label, and its question / short answer edits; the rows changed, or the errors."""
    with LOCK:
        columns, rows = load(path)
        row = next((r for r in rows if r["id"] == rid), None)
        if row is None:
            return [], [f"không có dòng {rid}"]
        new = {c: str(new.get(c) or "").strip() for c in LABELS}
        edits = {k: str(v).strip() for k, v in (edits or {}).items() if v is not None}
        edits = {k: v for k, v in edits.items() if v != (row.get(k) or "").strip()}
        errors = validate(row, new, who) + check_edits(row, edits)
        if errors:
            return [], errors
        changed = [row]
        stamp = {"edited_by": f"human:{who}", "edited_at": date.today().isoformat()}
        lid = row["lineage_id"]
        if "question" in edits:              # one question per lineage: every row of it, and its source
            def change(x, q=edits["question"]):
                x["model_question"] = x.get("model_question") or x["question"]
                x.update(question=q, **stamp)
            if not rewrite_jsonl(data / "vilextime/questions.jsonl",
                                 lambda x: x["lineage_id"] == lid and x["question"], change):
                return [], [f"không thấy câu hỏi của {lid} trong questions.jsonl"]
            changed += [r for r in rows if r["lineage_id"] == lid]
            for r in rows:
                if r["lineage_id"] == lid:
                    r["question"] = edits["question"]
        if "short_answer" in edits:          # one short answer per (lineage, version)
            vid = version_of[rid]
            def change(x, s=edits["short_answer"]):
                x["model_short_answer"] = x.get("model_short_answer") or x["short_answer"]
                x.update(short_answer=s, **stamp)
            if not rewrite_jsonl(data / "vilextime/short_answers.jsonl",
                                 lambda x: x["lineage_id"] == lid and x["version_id"] == vid, change):
                return [], [f"không thấy đáp án ngắn của {vid} trong short_answers.jsonl"]
            same = [r for r in rows if version_of.get(r["id"]) == vid]
            changed += same
            for r in same:
                r["short_answer"] = edits["short_answer"]
        row.update(new)
        row["guideline_version"] = GUIDELINE   # a carried D4 label becomes a 3.0 one only by being saved here
        tmp = path.with_suffix(".tsv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, columns, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
        return list({r["id"]: r for r in changed}.values()), []


def handler(path: Path, who: str, data: Path, version_of: dict[str, str], only: set[str] | None = None):
    class H(BaseHTTPRequestHandler):
        def send(self, body: bytes, ctype: str, code: int = 200):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/api/state":
                with LOCK:
                    _, rows = load(path)
                held = held_back(path.parent, who)
                shown = [{**r, "tl": timeline(r)} for r in rows
                         if r["lineage_id"] not in held and (only is None or r["id"] in only)]
                ids, lineages = {r["id"] for r in shown}, {r["lineage_id"] for r in shown}
                state = {"who": who, "guideline": GUIDELINE, "rows": shown,
                         "held": sum(1 for r in rows if r["lineage_id"] in held and (only is None or r["id"] in only)),
                         # from the whole sheet: with --ids, a row's other version may sit outside the shown rows
                         "spans": {k: v for k, v in spans_for(rows).items() if k in ids},
                         "compare": {k: v for k, v in compare(rows).items() if k in lineages},
                         "labels": list(LABELS),
                         "families": [{"name": n, "codes": [{"code": c, "help": dict(REASON_HELP)[c], "key": KEYS[KEY_ORDER.index(c)]}
                                                      for c in cs]} for n, cs in FAMILIES],
                         "decision": DECISION}
                self.send(json.dumps(state, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            else:
                self.send(PAGE.encode(), "text/html; charset=utf-8")

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            rows, errors = save(path, body["id"], body["label"], body.get("edits"), data, version_of, who)
            self.send(json.dumps({"rows": rows, "errors": errors}, ensure_ascii=False).encode(),
                      "application/json; charset=utf-8")

        def log_message(self, *a):
            pass
    return H


PAGE = (Path(__file__).with_suffix(".html")).read_text(encoding="utf-8")



def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--who", choices=("A", "B"), required=True)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--port", type=int)
    ap.add_argument("--ids", type=Path, help="show only the row ids in this file, one per line (B's cross-check sample)")
    args = ap.parse_args()
    path = args.data / f"review/kiem_{args.who}.tsv"
    port = args.port or (8765 if args.who == "A" else 8766)
    version_of = {r["id"]: version_id(r) for r in load(path)[1]}   # from the sheet: no gitignored release.jsonl
    only = set(args.ids.read_text(encoding="utf-8").split()) if args.ids else None
    server = ThreadingHTTPServer(("127.0.0.1", port), handler(path, args.who, args.data, version_of, only))
    url = f"http://127.0.0.1:{port}"
    print(f"{path}: mở {url} (Ctrl+C để dừng; nhãn lưu vào TSV sau mỗi dòng)")
    webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
