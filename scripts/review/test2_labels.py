#!/usr/bin/env python3
"""ViLexTime test2 — question-level labels under annotation guideline 4.0.

    python scripts/review/test2_labels.py serve --worksheet FILE --labels-dir DIR --who A
    python scripts/review/test2_labels.py report --worksheet FILE --a DIR/test2_A.tsv --b DIR/test2_B.tsv [--adjudicated FILE]
    python scripts/review/test2_labels.py adjudicate export --worksheet FILE --a A.tsv --b B.tsv --out FILE.xlsx [--batch N]
    python scripts/review/test2_labels.py adjudicate import --xlsx FILE.xlsx --worksheet FILE --a A.tsv --b B.tsv --by "luật sư <tên>" --out FILE.tsv

The worksheet contains one object per lineage with question, group, batch, rows
(all boundary dates), and sources {base, actors}. Sources are raw passages, not
model judgements. Serving reads only the selected person's TSV. Reports are a
separate command for the coordinator after both people finish independently.
Authority: docs/vilextime-annotation.md (4.0; Q1–Q4, evidence and agreement).
"""
from __future__ import annotations

import argparse
import csv
import collections
import difflib
import hashlib
import html
import json
import os
import re
import random
import statistics
import tempfile
import math
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from markdown_it import MarkdownIt

from crosscheck import AC1_TARGET, PNEG_TARGET, gwet_ac1, specific_agreement

GUIDELINE = "4.0"
MIN_NEGATIVES = 5
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
          "quote_in_provided_sources", "verdict", "labeler", "guideline_version", "worksheet_sha256", "updated_at",
          "seconds", "uid"]
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


def validate_label(record: dict, body: dict, *, require_quote: bool = True) -> tuple[dict, list[str]]:
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
    if require_quote and not label["quote"]:
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
    label["uid"] = str(body.get("uid") or "").strip()
    label["seconds"] = ""
    if body.get("seconds") not in (None, ""):
        try:
            seconds = float(body["seconds"])
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError
            label["seconds"] = seconds
        except (ValueError, TypeError):
            errors.append("seconds: thời gian phải là số hữu hạn không âm")
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
        if label["uid"] and any(r.get("uid") and r["uid"] != label["uid"] for r in rows.values()):
            return {"errors": ["uid: đã có nhãn của tài khoản khác cho người này; kiểm lại tên A/B"]}
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


def guideline_html() -> str:
    text = (Path(__file__).resolve().parents[2] / 'docs/vilextime-annotation.md').read_text(encoding='utf-8')
    return MarkdownIt('commonmark', {'html': False}).enable('table').render(text)


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
    return {"who": who, "guideline_version": GUIDELINE, "card_html": guideline_html(), "questions": questions,
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


def agreement_report(records: list[dict], a: dict, b: dict, batch: int | None = None, limit: int | None = None,
                     adjudicated: dict | None = None) -> dict:
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
            metric.update(p_neg=specific_agreement(ba, bb).get("khong_dat"),
                          negative_category=["co", "khong_chac"])
        # Master plan, G1 (05/11): a question is gated only with >= MIN_NEGATIVES adverse labels across A and B;
        # with fewer, p_neg says almost nothing, so it is reported but cannot pass or fail the gate.
        adverse = [x for x in va + vb if (x != GOOD[q] if q != "verdict" else x == "khong_dat")]
        metric["adverse_labels"] = len(adverse)
        if len(adverse) < MIN_NEGATIVES:
            metric["gate"] = "not_evaluable"
        else:
            metric["gate"] = "pass" if metric["ac1"] is not None and metric["ac1"] >= AC1_TARGET and metric["p_neg"] is not None and metric["p_neg"] >= PNEG_TARGET else "not_met"
        metrics[q] = metric
    completeness = {"requested": limit, "selected": len(ids), "paired": len(shared),
                    "all_selected_paired": len(shared) == len(ids),
                    "requested_sample_available": limit is None or len(ids) >= limit,
                    "status": "insufficient_selected" if limit is not None and len(ids) < limit else
                              "missing_pairs" if len(shared) < len(ids) else "complete"}
    people = {}
    uid_sets = {}
    for who, labels in (("A", a), ("B", b)):
        own = [labels[lid] for lid in ids if lid in labels]
        times = [float(r["seconds"]) for r in own if r.get("seconds") not in (None, "")]
        uids = {r["uid"] for r in own if r.get("uid")}
        uid_sets[who] = uids
        people[who] = {"questions": len(own), "median_seconds": statistics.median(times) if times else None,
                       "under_30_seconds": sum(t < 30 for t in times), "missing_seconds": len(own) - len(times),
                       "uid_count": len(uids), "missing_uid": sum(not r.get("uid") for r in own)}
    timing_review = any(p["median_seconds"] is None or p["median_seconds"] < 90 or p["missing_seconds"]
                        for p in people.values())
    independent = (all(len(uid_sets[w]) == 1 and not people[w]["missing_uid"] for w in ("A", "B"))
                   and uid_sets["A"].isdisjoint(uid_sets["B"]))
    gated = [q for q in GOOD if metrics[q]["gate"] != "not_evaluable"]
    agreement_met = bool(gated) and all(metrics[q]["gate"] == "pass" for q in gated)
    result = {"guideline_version": GUIDELINE, "selected": len(ids), "batch": batch, "limit": limit,
            "sample_completeness": completeness,
            "paired": len(shared), "missing_A": [i for i in ids if i not in a], "missing_B": [i for i in ids if i not in b],
            "disagreements": [i for i in shared if any(a[i][q] != b[i][q] for q in (*GOOD, "verdict"))],
            "thresholds": {"ac1": AC1_TARGET, "p_neg": PNEG_TARGET}, "metrics": metrics,
            "people": people, "uid_A_differs_B": independent,
            "shared_uid_count": len(uid_sets["A"] & uid_sets["B"]),
            "timing_review_required": timing_review,
            "agreement_gate": "pass" if agreement_met else "not_met",
            "gate": "pass" if agreement_met and independent and not timing_review and completeness["status"] == "complete" and ids else "not_met",
            "note": "Q4: AC1 trên ba mức; p_neg gộp Có/Không chắc thành mức bất lợi theo ADR 0005, điều chỉnh 03/11/2026 mục 3. Lô 0 bị loại khỏi báo cáo mặc định."}

    if adjudicated is not None:
        by_id = {r["lineage_id"]: r for r in records}
        for lid, row in adjudicated.items():
            if lid not in by_id or lid not in a or lid not in b:
                raise ValueError(f"{lid}: hòa giải không có cặp nhãn gốc")
            record = by_id[lid]
            check_binding(record, row)
            if not any(a[lid][q] != b[lid][q] for q in (*GOOD, "verdict")):
                raise ValueError(f"{lid}: hòa giải cho câu không lệch")
            label, errors = validate_label(record, row, require_quote=False)
            if (errors or row.get("verdict") != label["verdict"]
                    or row.get("guideline_version") != GUIDELINE
                    or not str(row.get("adjudicator") or "").strip()
                    or any(row.get(w + "_sha256") != label_sha256(own[lid])
                           for w, own in (("A", a), ("B", b)))):
                raise ValueError(f"{lid}: hòa giải không hợp lệ hoặc nhãn gốc đã đổi: {errors}")
        final, unresolved = [], []
        for lid in shared:
            if lid in result["disagreements"] and lid not in adjudicated:
                unresolved.append(lid)
                continue
            row = adjudicated[lid] if lid in adjudicated else a[lid]
            if row["verdict"] == "dat":
                final.append(lid)
        result["after_adjudication"] = {"dat": len(final), "final_lineage_ids": final,
                                         "unresolved": unresolved}
    return result


# Only factual worksheet fields cross the independent-annotation boundary.
# Authority: task C4 and master-plan §5. Never copy arbitrary nested metadata.
def unlabelled_record(record: dict) -> dict:
    def take(obj, keys):
        return {k: obj[k] for k in keys if k in obj}
    def source(obj):
        return take(obj or {}, ('document', 'number', 'title', 'issued', 'effective_from', 'effective_to',
                                'source_url', 'url', 'text', 'passage', 'transitional', 'in_force'))
    result = take(record, ('lineage_id', 'group', 'stratum', 'batch', 'question'))
    result['rows'] = []
    for row in record['rows']:
        clean = take(row, ('id', 'as_of', 'as_of_strategy', 'version_id', 'answer', 'answerable',
                           'short_answer', 'source_url'))
        clean['target'] = take(row.get('target', {}), ('document_id', 'law_id', 'document_title', 'article_id',
                               'clause_id', 'point_id', 'citation', 'provision_path', 'lead_in'))
        result['rows'].append(clean)
    sources = record.get('sources', {})
    result['sources'] = {'base': source(sources.get('base')), 'actors': [source(s) for s in sources.get('actors', [])]}
    return result


def jsonl(path: Path) -> list[dict]:
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def write_worksheet(out: Path, records: list[dict], manifest: dict) -> dict:
    data = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records).encode()
    manifest['output_sha256'] = hashlib.sha256(data).hexdigest()
    out.parent.mkdir(parents=True, exist_ok=True)
    # Repeated deterministic preparation is safe; never replace different bytes.
    manifest_path = out.with_suffix('.manifest.json')
    meta = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    for path, content in ((out, data), (manifest_path, meta)):
        if path.exists() and path.read_bytes() != content:
            raise FileExistsError(f'{path}: đã có nội dung khác; giữ phiếu cũ, chọn đường dẫn mới')
    out.write_bytes(data)
    manifest_path.write_bytes(meta)
    return manifest


def pilot(source: Path, release: Path, out: Path) -> dict:
    seed = 'vilextime-g1-0511'
    allowed = {r['lineage_id'] for r in jsonl(release)}
    pool = load_worksheet(source)
    rng = random.Random(seed)
    quota = {'T2': 10, 'T2 gần giống': 5, 'T3': 5, 'T6 đích danh': 7, 'T6 cấp trên': 3}
    chosen = []
    for tier, n in quota.items():
        candidates = sorted((r for r in pool if r['lineage_id'] in allowed and r['stratum'] == tier),
                            key=lambda r: r['lineage_id'])
        if len(candidates) < n:
            raise ValueError(f'{tier}: chỉ có {len(candidates)}/{n} câu thuộc test 2')
        chosen.extend(unlabelled_record({**r, 'batch': 0}) for r in rng.sample(candidates, n))
    rng.shuffle(chosen)
    return write_worksheet(out, chosen, {'seed': seed, 'questions': len(chosen), 'strata': quota,
        'inputs_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, release)}})


def silver_worksheet(data: Path, source: Path, release: Path, out: Path) -> dict:
    """Reuse v3 assembly and the raw-text extractor, keeping existing silver intact."""
    import subprocess
    import sys
    import tempfile
    from test2_prepare import lineage_rows, published_scope, prepare_records, source_links

    selected = [r for r in jsonl(source) if r['group'] in ('T2', 'T3') and r['as_of_strategy'] == 'ranh_gioi']
    ids = {r['lineage_id'] for r in selected}
    counts = {g: len({r['lineage_id'] for r in selected if r['group'] == g}) for g in ('T2', 'T3')}
    if counts != {'T2': 137, 'T3': 31}:
        raise ValueError(f'silver: cần 137 T2 + 31 T3, nhận {counts}')
    rows = lineage_rows(data, ids)
    used, dev_docs = published_scope(data)
    test2 = {r['lineage_id'] for r in jsonl(release)}
    if set(rows) != ids or ids & (used | test2):
        raise ValueError('silver: thiếu chuỗi phiên bản hoặc trùng lineage v1.0/test 2')
    if any(r['target']['document_id'] in dev_docs for rs in rows.values() for r in rs):
        raise ValueError('silver: trùng văn bản dev')
    if {r['id'] for r in selected} != {r['id'] for rs in rows.values() for r in rs}:
        raise ValueError('silver: các mốc ranh giới khác dữ liệu gốc; dừng, không tự sửa')
    questions, shorts = {}, {}
    for r in selected:
        lid = r['lineage_id']
        q = {'question': r['question'], 'group': r['group']}
        if lid in questions and questions[lid] != q:
            raise ValueError(f'{lid}: câu hỏi không thống nhất qua các mốc')
        questions[lid] = q
        key = (lid, r['version_id'])
        s = {'short_answer': r.get('answer')}
        if key in shorts and shorts[key] != s:
            raise ValueError(f'{lid}: đáp án ngắn không thống nhất qua các mốc')
        shorts[key] = s
    with tempfile.TemporaryDirectory(prefix='vilextime-silver-') as tmp:
        tmp = Path(tmp)
        raw, wanted, evidence_path = tmp / 'rows.jsonl', tmp / 'ids.txt', tmp / 'evidence.jsonl'
        raw.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for rs in rows.values() for r in rs), encoding='utf-8')
        wanted.write_text('\n'.join(r['id'] for rs in rows.values() for r in rs), encoding='utf-8')
        subprocess.run([sys.executable, str(Path(__file__).with_name('crosscheck_evidence.py')), '--data', str(data),
                        '--release', str(raw), '--ids', str(wanted), '--out', str(evidence_path)], check=True)
        evidence = {r['id']: r for r in jsonl(evidence_path)}
    source_links(data, evidence, strict=False)
    prepared, thieu = prepare_records(questions, rows, shorts, evidence, strict=False)
    missing_sources = {r['lineage_id'] for r in thieu if r['field'] == 'sources'}
    manifest = {'seed': 'vilextime-silver-0511', 'questions': len(ids), 'groups': counts,
                'boundary_rows': len(selected), 'thieu': thieu, 'missing_source_lineages': len(missing_sources),
                'inputs_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                    (source, release, data / 'vilextime_dataset/vilextime.jsonl',
                     data / 'vilextime_dataset/vilextime_meta.jsonl')},
                'exclusion_check': {'test2': 0, 'v1.0': 0, 'dev_documents': 0}}
    if len(missing_sources) > len(ids) / 10:
        manifest['status'] = 'stopped_missing_sources_over_10_percent'
        out.parent.mkdir(parents=True, exist_ok=True)
        manifest_path = out.with_suffix('.manifest.json')
        with manifest_path.open('x', encoding='utf-8') as f:
            f.write(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        raise ValueError(f'silver: {len(missing_sources)}/{len(ids)} câu thiếu nguồn (>10%); dừng, xem {manifest_path}')
    rng = random.Random(manifest['seed'])
    prepared.sort(key=lambda r: r['lineage_id'])
    rng.shuffle(prepared)
    clean = [unlabelled_record({**r, 'batch': i // 30 + 1}) for i, r in enumerate(prepared)]
    manifest['batches'] = dict(collections.Counter(r['batch'] for r in clean))
    return write_worksheet(out, clean, manifest)


def doc_id(lid: str) -> str:
    return 'q_' + hashlib.sha256(lid.encode()).hexdigest()


def web_page(records: list[dict]) -> str:
    # state() remains the owner of escaped diff/short-answer highlighting.
    clean = [unlabelled_record(r) for r in records]
    with tempfile.TemporaryDirectory(prefix='vilextime-web-') as tmp:
        payload = state(clean, Path(tmp) / 'empty.tsv', '')
    for r, original in zip(payload['questions'], clean):
        r.pop('label')
        r['worksheet_sha256'] = worksheet_sha256(original)
        r['doc_id'] = doc_id(r['lineage_id'])
    payload.pop('who')
    payload.pop('labelled')
    payload['good'] = GOOD
    blob = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
    page = Path(__file__).with_name('test2_label_ui.html').read_text(encoding='utf-8')
    page = re.sub(r'/\*SERVER_BEGIN\*/.*?/\*SERVER_END\*/', '', page, flags=re.S)
    return page.replace('/*EMBEDDED_STATE*/null', blob)


def pull(path: Path, dump: Path, records: list[dict], who: str) -> tuple[int, list[str]]:
    saved, errors, seen = 0, [], set()
    indexed = {r['lineage_id']: r for r in records}
    files = sorted(dump.glob('*.json'))
    if not files:
        return 0, [f'{dump}: không có document JSON']
    for file in files:
        try:
            document = json.loads(file.read_text(encoding='utf-8'))
            document = document.get('data', document)
            lid = document.get('lineage_id', document.get('id'))
            if document.get('id') != lid:
                raise ValueError(f'{lid}: id và lineage_id không khớp')
            if lid in seen:
                raise ValueError(f'{lid}: document trùng')
            seen.add(lid)
            if lid not in indexed:
                raise ValueError(f'{lid}: câu hỏi không thuộc phiếu')
            if document.get('guideline') != GUIDELINE or document.get('who') != who:
                raise ValueError(f'{lid}: sai thẻ hoặc người gán')
            check_binding(indexed[lid], document)
            body = dict(document['label'])
            body.update(seconds=document.get('seconds'), uid=document.get('uid'))
            if not body['uid'] or body['seconds'] is None:
                raise ValueError(f'{lid}: thiếu uid/seconds')
            result = save_label(path, records, who, lid, body)
            if result['errors']:
                raise ValueError('; '.join(result['errors']))
            saved += 1
        except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
            errors.append(f'{file.name}: {exc}')
    return saved, errors


# C13 authority: annotation 4.0 §2, §5 and the requested lawyer-only card.
ADJ_SHEET = "Hòa giải"
ADJ_LABEL_FIELDS = [k for q in GOOD for k in (q, q + "_reason")] + ["quote", "search_log", "note", "verdict"]
ADJ_EDIT = [k for q in GOOD for k in ("chot_" + q, "chot_" + q + "_reason")] + ["ghi_chu_luat_su"]
ADJ_COLUMNS = ["lineage_id", "group", "batch", "question", "cac_moc_va_dap_an", "van_ban_goc",
               "van_ban_tac_dong", "worksheet_sha256", "A_sha256", "B_sha256",
               *[w + "_" + k for k in ADJ_LABEL_FIELDS for w in ("A", "B")], *ADJ_EDIT]
ADJ_GUIDE = [
    "Phiếu hòa giải theo hướng dẫn 4.0 — docs/vilextime-annotation.md §2, §5.",
    "Luật sư đọc câu hỏi, mọi mốc, đáp án đầy đủ và đáp án ngắn; mở văn bản gốc và văn bản tác động.",
    "Đọc nhãn, lý do và dẫn chứng A/B; tự chốt đủ Q1–Q4. Không dùng AI.",
    "Chỉ điền chot_q1…chot_q4, lý do tương ứng và ghi_chu_luat_su; không sửa ô khóa.",
    "Chọn câu bất lợi phải chọn một lý do đúng câu trả lời; câu đạt để trống lý do.",
    "other: ghi ý thiếu; relocated/relocation_unclear: ghi chỗ mới/chỗ nghi vào ghi_chu_luat_su.",
    "Không đòi câu trích mới. T6, Q4 Không: dùng nơi đã tìm của A/B; nếu chưa có, ghi vào ghi_chu_luat_su.",
    "Nhãn dat được suy khi Q1 dung, Q2 co, Q3 co, Q4 khong. Nhãn thô A/B giữ nguyên để đo AC1.",
    "Dòng khong_dat bị loại hoặc thay bằng câu dự trữ; không sửa tay đáp án chuẩn.",
]


def label_sha256(label: dict) -> str:
    # Bind the complete raw TSV row, without copying arbitrary metadata into XLSX.
    return hashlib.sha256(json.dumps(label, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def adjudication_rows(records: list[dict], a: dict, b: dict, batch: int | None) -> list[dict]:
    report = agreement_report(records, a, b, batch)
    wanted = set(report["disagreements"])
    rows = []
    for record in records:
        lid = record["lineage_id"]
        if lid not in wanted:
            continue
        clean = unlabelled_record(record)
        sources = [record.get("sources", {})] + [r.get("source_evidence", {}) for r in record["rows"]]
        def links(items):
            return "\n".join(dict.fromkeys(str(s[k]) for s in items for k in ("source_url", "url") if s.get(k)))
        row = {k: clean.get(k, "") for k in ("lineage_id", "group", "batch", "question")}
        boundaries = []
        for boundary in clean["rows"]:
            target = boundary.get("target", {})
            boundaries.append("\n".join([
                f"Mốc: {boundary.get('as_of', '')}",
                f"Điều khoản: {target.get('citation') or target.get('provision_path') or ''}",
                f"Lời dẫn: {target.get('lead_in') or ''}",
                f"Đáp án đầy đủ: {boundary.get('answer') or '(không có đáp án)'}",
                f"Đáp án ngắn: {boundary.get('short_answer') or '(không có đáp án)'}",
            ]))
        row.update(cac_moc_va_dap_an="\n\n".join(boundaries),
                   van_ban_goc=links([s.get("base") or {} for s in sources] + clean["rows"]),
                   van_ban_tac_dong=links([actor for s in sources for actor in s.get("actors", [])]),
                   worksheet_sha256=worksheet_sha256(record), A_sha256=label_sha256(a[lid]), B_sha256=label_sha256(b[lid]))
        for who, own in (("A", a), ("B", b)):
            row.update({who + "_" + k: own[lid].get(k, "") for k in ADJ_LABEL_FIELDS})
        rows.append(row)
    return rows


def adjudication_workbook(records: list[dict], a: dict, b: dict, batch: int | None):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Protection
    from openpyxl.workbook.defined_name import DefinedName
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    rows = adjudication_rows(records, a, b, batch)
    wb = Workbook()
    guide = wb.active
    guide.title = "Đọc trước"
    guide.append(["Lô", "all" if batch is None else batch])
    for text in ADJ_GUIDE:
        guide.append([text])
    guide.column_dimensions["A"].width = 115
    guide.protection.sheet = True
    ws = wb.create_sheet(ADJ_SHEET)
    ws.append(ADJ_COLUMNS)
    for i, name in enumerate(ADJ_COLUMNS, 1):
        cell = ws.cell(1, i)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="44546A")
        ws.column_dimensions[get_column_letter(i)].width = 50 if name in (
            "question", "cac_moc_va_dap_an", "ghi_chu_luat_su") else 24
    for i, row in enumerate(rows, 2):
        for j, name in enumerate(ADJ_COLUMNS, 1):
            value = row.get(name, "")
            if isinstance(value, str) and (len(value) > 32767 or "\r" in value):
                raise ValueError(f"{row['lineage_id']}: {name} vượt giới hạn văn bản XLSX")
            cell = ws.cell(i, j, value)
            # Treat human quotes and source text literally, including leading '='.
            if isinstance(value, str):
                cell.data_type = "s"
            cell.protection = Protection(locked=name not in ADJ_EDIT)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if name in ADJ_EDIT:
                cell.fill = PatternFill("solid", fgColor="EAF3EC")
    # Separate reason ranges by answer: Q4 Có and Không chắc have different vocabularies.
    vocab = wb.create_sheet("Mã lý do")
    for q in GOOD:
        for answer, reasons in REASONS[q].items():
            vocab.append([q + "_" + answer, *reasons])
    vocab.protection.sheet = True
    for n, (key, *reasons) in enumerate(vocab.values, 1):
        last = get_column_letter(1 + len([r for r in reasons if r]))
        wb.defined_names.add(DefinedName(key, attr_text=f"'Mã lý do'!$B${n}:${last}${n}"))
    for q, options in OPTIONS.items():
        col = get_column_letter(ADJ_COLUMNS.index("chot_" + q) + 1)
        dv = DataValidation(type="list", formula1='"' + ','.join(options) + '"',
                            allow_blank=True, showErrorMessage=True, errorStyle="stop")
        ws.add_data_validation(dv)
        if rows:
            dv.add(f"{col}2:{col}{len(rows) + 1}")
        reason_col = get_column_letter(ADJ_COLUMNS.index("chot_" + q + "_reason") + 1)
        for i in range(2, len(rows) + 2):
            formula = '""'
            for n, (key, *reasons) in reversed(list(enumerate(vocab.values, 1))):
                if key.startswith(q + "_"):
                    answer = key[len(q) + 1:]
                    formula = f'IF({col}{i}="{answer}",{key},{formula})'
            dv = DataValidation(type="list", formula1=formula, allow_blank=True,
                                showErrorMessage=True, errorStyle="stop")
            ws.add_data_validation(dv)
            dv.add(f"{reason_col}{i}")
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = ws.dimensions
    ws.protection.sheet = True
    return wb


def adjudicate_export(records: list[dict], a: dict, b: dict, out: Path, batch: int | None = None) -> int:
    if out.exists():
        raise ValueError(f"{out}: đã có; không ghi đè phiếu hòa giải")
    wb = adjudication_workbook(records, a, b, batch)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return wb[ADJ_SHEET].max_row - 1


def adjudicate_import(xlsx: Path, records: list[dict], a: dict, b: dict, by: str, out: Path) -> int:
    from openpyxl import load_workbook

    if not by.strip():
        raise ValueError("adjudicator: ghi tên hoặc bí danh luật sư chốt theo hướng dẫn 4.0 §5")
    wb = load_workbook(xlsx, data_only=False)
    if "Đọc trước" not in wb.sheetnames or ADJ_SHEET not in wb.sheetnames:
        raise ValueError("xlsx: thiếu trang của phiếu hòa giải 4.0")
    batch = wb["Đọc trước"]["B1"].value
    if batch == "all":
        batch = None
    elif type(batch) is not int:
        raise ValueError("xlsx: lô không hợp lệ")
    expected = adjudication_workbook(records, a, b, batch)
    if wb.sheetnames != expected.sheetnames:
        raise ValueError("xlsx: các trang dữ liệu bị sửa; dùng lại phiếu xuất")
    for sheet in expected:
        actual = wb[sheet.title]
        if actual.max_row != sheet.max_row or actual.max_column != sheet.max_column:
            raise ValueError(f"{sheet.title}: thiếu/thừa hàng hoặc cột; không ghi gì")
        for row in sheet:
            for cell in row:
                other = actual[cell.coordinate]
                if sheet.title == ADJ_SHEET and cell.row > 1 and ADJ_COLUMNS[cell.column - 1] in ADJ_EDIT:
                    if other.data_type == "f":
                        raise ValueError(f"{other.coordinate}: phần chốt không nhận công thức")
                    continue
                if (other.value if other.value is not None else "") != (cell.value if cell.value is not None else "") or other.data_type == "f":
                    raise ValueError(f"{sheet.title}!{cell.coordinate}: ô dữ liệu khóa bị sửa; không ghi gì")
    ws = wb[ADJ_SHEET]
    by_id = {r["lineage_id"]: r for r in records}
    result, errors = [], []
    for values in ws.iter_rows(min_row=2, values_only=True):
        cells = dict(zip(ADJ_COLUMNS, values))
        lid = cells["lineage_id"]
        body = {q: cells["chot_" + q] for q in GOOD}
        body.update({q + "_reason": cells["chot_" + q + "_reason"] for q in GOOD})
        body["note"] = cells["ghi_chu_luat_su"]
        body["search_log"] = "\n".join(dict.fromkeys(str(cells[w + "_search_log"]) for w in ("A", "B") if cells[w + "_search_log"]))
        if not body["search_log"]:
            body["search_log"] = body["note"]
        label, problems = validate_label(by_id[lid], body, require_quote=False)
        errors.extend(f"{lid}: {e}" for e in problems)
        label.update(lineage_id=lid, adjudicator=by.strip(), guideline_version=GUIDELINE,
                     worksheet_sha256=cells["worksheet_sha256"], A_sha256=cells["A_sha256"], B_sha256=cells["B_sha256"],
                     updated_at=datetime.now(timezone.utc).isoformat())
        result.append(label)
    if errors:
        raise ValueError("Chưa chốt hợp lệ — KHÔNG ghi gì:\n" + "\n".join(errors))
    if out.resolve() == xlsx.resolve():
        raise ValueError("out: không ghi đè phiếu nguồn")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=out.parent, delete=False) as f:
        tmp = Path(f.name)
        try:
            writer = csv.DictWriter(f, fieldnames=[*FIELDS, "adjudicator", "A_sha256", "B_sha256"], delimiter="\t")
            writer.writeheader()
            writer.writerows(result)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    os.replace(tmp, out)
    return len(result)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('pilot')
    p.add_argument('--source', type=Path, default=Path('data/review/test2_candidate_worksheet_v3.jsonl'))
    p.add_argument('--release', type=Path, default=Path('data/vilextime/test2_release_v2.jsonl'))
    p.add_argument('--out', type=Path, default=Path('data/review/the4/lo0_worksheet.jsonl'))
    p = sub.add_parser('silver')
    p.add_argument('--data', type=Path, default=Path('data'))
    p.add_argument('--source', type=Path, default=Path('data/vilextime_dataset/vilextime_silver.jsonl'))
    p.add_argument('--release', type=Path, default=Path('data/vilextime/test2_release_v2.jsonl'))
    p.add_argument('--out', type=Path, default=Path('data/review/the4/lo1_silver_worksheet.jsonl'))
    for command in ('serve', 'web', 'pull', 'report'):
        p = sub.add_parser(command)
        p.add_argument('--worksheet', type=Path, action='append', required=True)
        if command in ('serve', 'pull'):
            p.add_argument('--labels-dir', type=Path, default=Path('data/review/the4'))
            p.add_argument('--who', choices=('A', 'B'), required=True)
        if command == 'serve':
            p.add_argument('--port', type=int)
        if command == 'web':
            p.add_argument('--out', type=Path, required=True)
            p.add_argument('--exclude', type=Path, action='append', default=[],
                           help='TSV with lineage_id: held back until the blind gold sheets are done (B6)')
        if command == 'pull':
            p.add_argument('--from', dest='dump', type=Path, required=True)
        if command == 'report':
            p.add_argument('--a', type=Path, required=True)
            p.add_argument('--b', type=Path, required=True)
            p.add_argument('--batch', type=int)
            p.add_argument('--limit', type=int)
            p.add_argument('--adjudicated', type=Path)
            p.add_argument('--out', type=Path)
    p = sub.add_parser('adjudicate')
    adj = p.add_subparsers(dest='action', required=True)
    for action in ('export', 'import'):
        p = adj.add_parser(action)
        p.add_argument('--worksheet', type=Path, action='append', required=True)
        p.add_argument('--a', type=Path, required=True)
        p.add_argument('--b', type=Path, required=True)
        p.add_argument('--out', type=Path, required=True)
        if action == 'export':
            p.add_argument('--batch', type=int)
        else:
            p.add_argument('--xlsx', type=Path, required=True)
            p.add_argument('--by', required=True)
    args = ap.parse_args()
    try:
        if args.command == 'pilot':
            print(json.dumps(pilot(args.source, args.release, args.out), ensure_ascii=False, indent=2))
            return
        if args.command == 'silver':
            print(json.dumps(silver_worksheet(args.data, args.source, args.release, args.out), ensure_ascii=False, indent=2))
            return
        records = [r for f in args.worksheet for r in load_worksheet(f)]
        if len({r['lineage_id'] for r in records}) != len(records):
            raise ValueError('lineage trùng giữa các phiếu')
        if args.command == 'adjudicate':
            if args.out.resolve() in {args.a.resolve(), args.b.resolve(), *(f.resolve() for f in args.worksheet)}:
                raise ValueError('out: không ghi đè nhãn thô hoặc worksheet')
            a, b = read_labels(args.a), read_labels(args.b)
            if args.action == 'export':
                count = adjudicate_export(records, a, b, args.out, args.batch)
            else:
                count = adjudicate_import(args.xlsx, records, a, b, args.by, args.out)
            print(f'{count} câu -> {args.out}')
        elif args.command == 'web':
            held = {r['lineage_id'] for f in args.exclude
                    for r in csv.DictReader(f.open(encoding='utf-8'), delimiter='\t')}
            records = [r for r in records if r['lineage_id'] not in held]
            page = web_page(records)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(page, encoding='utf-8')
            print(f'{len(records)} câu; {len(page.encode())} byte -> {args.out}')
        elif args.command == 'pull':
            saved, errors = pull(args.labels_dir / f'test2_{args.who}.tsv', args.dump, records, args.who)
            print(f'{saved} câu đã lưu; {len(errors)} lỗi')
            for error in errors:
                print(error)
            if errors:
                raise SystemExit(1)
        elif args.command == 'report':
            if args.adjudicated and not args.adjudicated.is_file():
                raise ValueError(f'{args.adjudicated}: không có tệp hòa giải')
            result = agreement_report(records, read_labels(args.a), read_labels(args.b), args.batch, args.limit,
                                      read_labels(args.adjudicated) if args.adjudicated else None)
            text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
            if args.out:
                args.out.write_text(text, encoding='utf-8')
            print(text, end='')
        else:
            port = args.port or (8775 if args.who == 'A' else 8776)
            labels = args.labels_dir / f'test2_{args.who}.tsv'
            server = ThreadingHTTPServer(('127.0.0.1', port), handler(records, labels, args.who))
            print(f'Người gán {args.who}: http://127.0.0.1:{port}; nhãn lưu tại {labels}', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == '__main__':
    main()
