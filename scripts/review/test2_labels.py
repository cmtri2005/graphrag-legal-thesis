#!/usr/bin/env python3
"""ViLexTime test2 — question-level labels under the approved annotation card 4.0.

    python scripts/review/test2_labels.py serve --worksheet FILE --labels-dir DIR --who A
    python scripts/review/test2_labels.py report --worksheet FILE --a DIR/test2_A.tsv --b DIR/test2_B.tsv

The worksheet contains one object per lineage with question, group, batch, rows
(all boundary dates), and sources {base, actors}. Sources are raw passages, not
model judgements. Serving reads only the selected person's TSV. Reports are a
separate command for the coordinator after both people finish independently.
Authority: docs/vilextime-the-gan-nhan.md (Q1–Q4, evidence and agreement).
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import html
import json
import os
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from crosscheck import AC1_TARGET, PNEG_TARGET, gwet_ac1, specific_agreement

GUIDELINE = "4.0"
GOOD = {"q1": "dung", "q2": "co", "q3": "co", "q4": "khong"}
OPTIONS = {"q1": ("dung", "sai"), "q2": ("co", "khong"), "q3": ("co", "khong"),
           "q4": ("khong", "co", "khong_chac")}
REASONS = {
    "q1": {"sai": ("gold_wrong", "reference_only", "other")},
    "q2": {"khong": ("group_mismatch", "cosmetic_only", "rename_only", "auto_reference_update")},
    "q3": {"khong": ("question_ambiguous", "unanswerable_as_asked", "question_leaks")},
    "q4": {"co": ("superseded_by_other_norm", "restructuring_2025", "transitional_rule", "relocated"),
           "khong_chac": ("relocation_unclear",)},
}
FIELDS = ["lineage_id", *[k for q in GOOD for k in (q, q + "_reason")], "quote", "search_log", "note",
          "quote_in_provided_sources", "verdict", "labeler", "guideline_version", "worksheet_sha256", "updated_at"]
LOCK = threading.Lock()


def load_worksheet(path: Path) -> list[dict]:
    records = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]
    seen = set()
    for r in records:
        lid = r["lineage_id"]
        if lid in seen:
            raise ValueError(f"{lid}: câu hỏi trùng trong phiếu test2")
        seen.add(lid)
        if r.get("group") not in ("T2", "T3", "T6") or not str(r.get("question") or "").strip() or not r.get("rows"):
            raise ValueError(f"{lid}: phiếu test2 thiếu nhóm, câu hỏi hoặc các mốc")
    return records


def read_labels(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out = {}
    for r in rows:
        if r["lineage_id"] in out:
            raise ValueError(f"{path}: nhãn trùng {r['lineage_id']}")
        out[r["lineage_id"]] = r
    return out


def actor_passages(record: dict) -> list[str]:
    sources = [record.get("sources", {})]
    sources.extend(r.get("source_evidence", {}) for r in record["rows"])
    return [str(a[k]) for s in sources for a in s.get("actors", [])
            for k in ("text", "passage", "transitional", "in_force") if a.get(k)]


def worksheet_sha256(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_binding(record: dict, label: dict) -> None:
    if label.get("worksheet_sha256") != worksheet_sha256(record):
        raise ValueError(f"{record['lineage_id']}: nhãn cũ không khớp câu hỏi/đáp án/nguồn hiện tại; "
                         "giữ lại phiếu cũ và chuẩn bị phiếu gán lại, không tái dùng nhãn")


def validate_label(record: dict, body: dict) -> tuple[dict, list[str]]:
    """Validate the approved card; no user-supplied verdict can override Q1–Q4."""
    errors, label = [], {}
    for q, choices in OPTIONS.items():
        value = str(body.get(q) or "").strip()
        reason = str(body.get(q + "_reason") or "").strip()
        label[q], label[q + "_reason"] = value, reason
        if value not in choices:
            errors.append(f"{q.upper()}: chọn đủ câu trả lời theo thẻ 4.0")
        elif value != GOOD[q] and reason not in REASONS[q].get(value, ()):
            errors.append(f"{q.upper()}: chọn một lý do đúng với câu trả lời (thẻ 4.0)")
        elif value == GOOD[q] and reason:
            errors.append(f"{q.upper()}: câu trả lời đạt không kèm mã loại")
    for k in ("quote", "search_log", "note"):
        label[k] = str(body.get(k) or "").strip()
    if not label["quote"]:
        errors.append("quote: dán một câu trích nguyên văn từ văn bản tác động (thẻ 4.0, Dẫn chứng)")
    # The extractor may omit a passage the annotator read at the original URL.
    # Membership is a diagnostic, not a restriction on human source reading.
    passages = actor_passages(record)
    norm = lambda s: " ".join(s.split())
    label["quote_in_provided_sources"] = (any(norm(label["quote"]) in norm(s) for s in passages)
                                           if passages and label["quote"] else None)
    if record["group"] == "T6" and label["q4"] == "khong" and not label["search_log"]:
        errors.append("search_log: T6, Q4 Không phải ghi đã tìm chuyển chỗ ở đâu (thẻ 4.0, Dẫn chứng)")
    if label["q4_reason"] in ("relocated", "relocation_unclear") and not label["note"]:
        errors.append("note: ghi chỗ mới hoặc chỗ nghi chuyển chỗ (thẻ 4.0, Q4)")
    if label["q1_reason"] == "other" and not label["note"]:
        errors.append("note: ghi ý còn thiếu trong đáp án ngắn (thẻ 4.0, Q1)")
    label["verdict"] = "dat" if all(label[q] == v for q, v in GOOD.items()) else "khong_dat"
    return label, errors


def save_label(path: Path, records: list[dict], who: str, lid: str, body: dict) -> dict:
    record = next((r for r in records if r["lineage_id"] == lid), None)
    if record is None:
        return {"errors": ["lineage_id: câu hỏi không có trong phiếu của phiên này"]}
    label, errors = validate_label(record, body)
    if errors:
        return {"errors": errors}
    label.update(lineage_id=lid, labeler=who, guideline_version=GUIDELINE,
                 worksheet_sha256=worksheet_sha256(record), updated_at=datetime.now(timezone.utc).isoformat())
    with LOCK:
        rows = read_labels(path)
        if lid in rows:
            try:
                check_binding(record, rows[lid])
            except ValueError as exc:
                return {"errors": [str(exc)]}
        rows[lid] = label
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows.values())
        os.replace(tmp, path)
    return {"errors": [], "label": label}


def marked_text(text: str, other: str, short: str) -> str:
    """Escape legal text before adding only our own diff and short-answer marks."""
    intervals = []
    if other:
        intervals = [(a, b) for op, a, b, _, _ in difflib.SequenceMatcher(None, text, other, autojunk=False).get_opcodes()
                     if op != "equal" and b > a]
    short_intervals = []
    for span in short.split("…"):
        words = span.split()
        if words:
            pattern = r"\s+".join(re.escape(w) for w in words)
            short_intervals.extend((m.start(), m.end()) for m in re.finditer(pattern, text))
    edges = {0, len(text), *[x for pair in intervals + short_intervals for x in pair]}
    out = []
    bounds = sorted(edges)
    for start, end in zip(bounds, bounds[1:]):
        part = html.escape(text[start:end])
        if any(a <= start < b for a, b in intervals):
            part = f"<mark>{part}</mark>"
        if any(a <= start < b for a, b in short_intervals):
            part = f"<strong>{part}</strong>"
        out.append(part)
    return "".join(out)


def state(records: list[dict], path: Path, who: str) -> dict:
    own = read_labels(path)
    questions = []
    for record in records:
        if record["lineage_id"] in own:
            check_binding(record, own[record["lineage_id"]])
        r = dict(record)
        texts = [str(v.get("answer") or "") for v in r["rows"]]
        leads = [str(v.get("target", {}).get("lead_in") or v.get("lead_in") or "") for v in r["rows"]]
        r["rows"] = [{**v, "marked_answer": marked_text(texts[i], next((s for s in texts if s != texts[i]), ""),
                                                        str(v.get("short_answer") or "")),
                      "marked_lead_in": marked_text(leads[i], next((s for s in leads if s != leads[i]), ""),
                                                    str(v.get("short_answer") or "")),
                      "answer_status": "no_answer" if v.get("answerable") is False or not texts[i] else "answerable"}
                     for i, v in enumerate(r["rows"])]
        r["label"] = own.get(r["lineage_id"], {})
        questions.append(r)
    return {"who": who, "guideline_version": GUIDELINE, "questions": questions,
            "options": OPTIONS, "reasons": REASONS, "labelled": sum(r["lineage_id"] in own for r in records)}


def handler(records: list[dict], path: Path, who: str):
    class Handler(BaseHTTPRequestHandler):
        def send(self, value, code=200, html_page=False):
            data = value.encode() if html_page else json.dumps(value, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8" if html_page else "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/api/state":
                try:
                    self.send(state(records, path, who))
                except ValueError as exc:
                    self.send({"errors": [str(exc)]}, 409)
            elif self.path == "/":
                self.send(Path(__file__).with_name("test2_label_ui.html").read_text(encoding="utf-8"), html_page=True)
            else:
                self.send({"errors": ["đường dẫn không có"]}, 404)

        def do_POST(self):
            if self.path != "/api/save":
                self.send({"errors": ["đường dẫn không có"]}, 404)
                return
            # Browsers may not submit labels through a page from another origin.
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host"):
                self.send({"errors": ["origin không khớp phiên gán nhãn"]}, 403)
                return
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                if body.get("who", who) != who or body.get("label", {}).get("labeler", who) != who:
                    self.send({"errors": ["who: không được đổi người gán trong phiên này"]}, 403)
                    return
                result = save_label(path, records, who, body["lineage_id"], body["label"])
                self.send(result, 400 if result["errors"] else 200)
            except (ValueError, KeyError, TypeError) as exc:
                self.send({"errors": [f"phiếu không hợp lệ: {exc}"]}, 400)

        def log_message(self, *args):
            pass
    return Handler


def agreement_report(records: list[dict], a: dict, b: dict, batch: int | None = None, limit: int | None = None) -> dict:
    selected = [r for r in records if (r.get("batch") == batch if batch is not None else r.get("batch") != 0)]
    if limit is not None:
        selected = selected[:limit]
    ids = [r["lineage_id"] for r in selected]
    for who, labels in (("A", a), ("B", b)):
        unknown = set(labels) - {r["lineage_id"] for r in records}
        if unknown:
            raise ValueError(f"{who}: nhãn không thuộc phiếu: {sorted(unknown)[:3]}")
        for record in selected:
            lid = record["lineage_id"]
            if lid in labels:
                row = labels[lid]
                check_binding(record, row)
                derived, errors = validate_label(record, row)
                if errors or row.get("verdict") != derived["verdict"] or row.get("labeler") != who or row.get("guideline_version") != GUIDELINE:
                    raise ValueError(f"{who}, {lid}: nhãn không hợp lệ theo thẻ 4.0: {errors}")
    shared = [lid for lid in ids if lid in a and lid in b]
    metrics = {}
    for q in (*GOOD, "verdict"):
        va, vb = [a[lid][q] for lid in shared], [b[lid][q] for lid in shared]
        negative = "khong_dat" if q == "verdict" else next(v for v in OPTIONS[q] if v != GOOD[q])
        specific = specific_agreement(va, vb)
        metric = {"n": len(shared), "ac1": gwet_ac1(va, vb), "category_agreement": specific,
                  "p_neg": specific.get(negative), "negative_category": negative}
        if q == "q4":
            ba = ["dat" if x == "khong" else "khong_dat" for x in va]
            bb = ["dat" if x == "khong" else "khong_dat" for x in vb]
            metric.update(p_neg=None, negative_category=None, gate="unresolved_q4_categories",
                          binary_adverse_diagnostic={"ac1": gwet_ac1(ba, bb),
                                                     "p_neg": specific_agreement(ba, bb).get("khong_dat")})
        else:
            metric["gate"] = "pass" if metric["ac1"] is not None and metric["ac1"] >= AC1_TARGET and metric["p_neg"] is not None and metric["p_neg"] >= PNEG_TARGET else "not_met"
        metrics[q] = metric
    completeness = {"requested": limit, "selected": len(ids), "paired": len(shared),
                    "all_selected_paired": len(shared) == len(ids),
                    "requested_sample_available": limit is None or len(ids) >= limit,
                    "status": "insufficient_selected" if limit is not None and len(ids) < limit else
                              "missing_pairs" if len(shared) < len(ids) else "complete"}
    return {"guideline_version": GUIDELINE, "selected": len(ids), "batch": batch, "limit": limit,
            "sample_completeness": completeness,
            "paired": len(shared), "missing_A": [i for i in ids if i not in a], "missing_B": [i for i in ids if i not in b],
            "disagreements": [i for i in shared if any(a[i][q] != b[i][q] for q in GOOD)],
            "thresholds": {"ac1": AC1_TARGET, "p_neg": PNEG_TARGET}, "metrics": metrics,
            "gate": "unresolved_q4_categories",
            "note": "Q4 có ba mức; AC1 thô và thỏa thuận từng mức được báo. Gộp Có/Không chắc chỉ là chẩn đoán, chưa chọn cổng. Lô 0 bị loại khỏi báo cáo mặc định."}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--worksheet", type=Path, required=True)
    serve.add_argument("--labels-dir", type=Path, required=True)
    serve.add_argument("--who", choices=("A", "B"), required=True)
    serve.add_argument("--port", type=int)
    report = sub.add_parser("report")
    report.add_argument("--worksheet", type=Path, required=True)
    report.add_argument("--a", type=Path, required=True)
    report.add_argument("--b", type=Path, required=True)
    report.add_argument("--batch", type=int)
    report.add_argument("--limit", type=int)
    report.add_argument("--out", type=Path)
    args = ap.parse_args()
    records = load_worksheet(args.worksheet)
    if args.command == "report":
        result = agreement_report(records, read_labels(args.a), read_labels(args.b), args.batch, args.limit)
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.write_text(text, encoding="utf-8")
        print(text, end="")
    else:
        port = args.port or (8775 if args.who == "A" else 8776)
        labels = args.labels_dir / f"test2_{args.who}.tsv"
        server = ThreadingHTTPServer(("127.0.0.1", port), handler(records, labels, args.who))
        print(f"Người gán {args.who}: http://127.0.0.1:{port}; nhãn lưu tại {labels}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
