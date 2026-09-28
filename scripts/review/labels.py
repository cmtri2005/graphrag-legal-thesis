#!/usr/bin/env python3
"""ViLexTime — every label on a release row, one line per (row, labeler).

`data/review/labels.tsv` holds the labels outside the D4 cross-check:
crosscheck_A/B.tsv stay human-only and blind (docs/vilextime-annotation.md §6).
Labels enter only through `add` or `import-excel`, which check the closed
vocabulary, so free-text codes cannot creep back in.

    import-excel XLSX  what a person typed into the unnamed last column of a
                       preview workbook, verbatim in `raw_label`, mapped onto the
                       vocabulary only where the mapping is mechanical; questions
                       edited in the workbook and changed review_status are kept
                       as notes, never applied
    add TSV            appends labels after checking vocabulary, that the row is
                       in the release, that (id, labeler) is new, and that a
                       model does not label a cross-check row before A and B have
                       both labelled it; sets `audit_required`
    report             labels per labeler and group, model–human agreement on
                       rows both labelled, and audit outcomes
    audit-sheet XLSX   the labels still waiting for their required audit, with
                       question, answer and lead-in beside them, as a workbook
    import-audit XLSX  writes `audit`, `auditor`, `audit_note` filled in that
                       workbook back into labels.tsv

Usage:
    python scripts/review/labels.py import-excel "Gán Nhãn Bộ Dữ Liệu ViLexTime.xlsx"
    python scripts/review/labels.py add batch.tsv
    python scripts/review/labels.py report
    python scripts/review/labels.py audit-sheet audit.xlsx --group T1
    python scripts/review/labels.py import-audit audit.xlsx
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crosscheck import REASONS, VERDICTS  # noqa: E402  one vocabulary for both files

GUIDELINE = "1.1"
COLUMNS = ["id", "group", "labeler", "guideline_version", "verdict", "reasons", "meta_issues", "note",
           "evidence", "raw_label", "audit_required", "audit", "auditor", "audit_note"]
META = {"valid_to_wrong", "valid_from_wrong", "group_wrong", "citation_path_wrong", "doc_number_wrong",
        "lead_in_wrong", "other"}
AUDITS = {"dong_y", "khong_dong_y"}
# raw token typed in the workbook -> (meta issue, or None when the token is a verdict)
RAW_META = {"valid_to": "valid_to_wrong", "lead_in": "lead_in_wrong", "citation/path": "citation_path_wrong",
            "citation": "citation_path_wrong", "provision_path": "citation_path_wrong",
            "provison_path": "citation_path_wrong", "document_number": "doc_number_wrong",
            "group": "group_wrong", "num_versions": "group_wrong", "type": "other"}
SHEET = ["id", "group", "question", "as_of", "lead_in", "answer", "citation", "law_id", "source_url",
         "labeler", "verdict", "reasons", "meta_issues", "note", "evidence", "audit", "auditor", "audit_note"]
AUDIT_SHARE = 5   # a model's `dat` is audited when sha1(id) % 5 == 0: a fixed 20% sample


def codes(cell: str) -> list[str]:
    return [c.strip() for c in (cell or "").split(",") if c.strip()]


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COLUMNS, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def release(data: Path) -> dict[str, dict]:
    """Boundary rows and their mid-interval twins; labels go on boundary rows, twins share them."""
    return {r["id"]: r for r in map(json.loads, (data / "derived/vilextime/release.jsonl").open(encoding="utf-8"))}


def is_human(labeler: str) -> bool:
    return labeler.startswith("human:")


def audit_required(label: dict) -> str:
    if is_human(label["labeler"]):
        return ""
    sampled = int(hashlib.sha1(label["id"].encode()).hexdigest(), 16) % AUDIT_SHARE == 0
    return "có" if label["verdict"] == "khong_dat" or label["meta_issues"] or sampled else ""


def problems(label: dict, rows: dict[str, dict], blind: set[str]) -> list[str]:
    out = []
    if label["id"] not in rows:
        out.append("id không có trong bản phát hành")
    if label["verdict"] not in VERDICTS | {""}:
        out.append(f"verdict ngoài từ vựng: {label['verdict']!r}")
    if not is_human(label["labeler"]) and not label["verdict"]:
        out.append("nhãn của model phải có verdict")
    bad = [c for c in codes(label["reasons"]) if c not in REASONS]
    if bad:
        out.append(f"reasons ngoài từ vựng: {bad}")
    if codes(label["reasons"]) and label["verdict"] != "khong_dat":
        out.append("reasons chỉ đi với khong_dat")
    if label["verdict"] == "khong_dat" and not codes(label["reasons"]):
        out.append("khong_dat phải có reasons")
    bad = [c for c in codes(label["meta_issues"]) if c not in META]
    if bad:
        out.append(f"meta_issues ngoài từ vựng: {bad}")
    if label.get("audit") and label["audit"] not in AUDITS:
        out.append(f"audit ngoài từ vựng: {label['audit']!r}")
    if not is_human(label["labeler"]) and label["id"] in blind:
        out.append("dòng kiểm chéo D4 chưa được cả A và B gán: model chưa được gán (§6)")
    return out


def blind_rows(data: Path) -> set[str]:
    """Cross-check rows a model must not see labelled before both people have labelled them."""
    a = {r["id"]: r for r in read(data / "review/crosscheck_A.tsv")}
    b = {r["id"]: r for r in read(data / "review/crosscheck_B.tsv")}
    return {i for i in a if not (a[i].get("verdict") and b.get(i, {}).get("verdict"))}


def add(data: Path, batch: Path) -> None:
    path = data / "review/labels.tsv"
    have = read(path)
    seen = {(r["id"], r["labeler"]) for r in have}
    rows, blind = release(data), blind_rows(data)
    new, errors = [], []
    for n, raw in enumerate(read(batch), 2):
        label = {c: (raw.get(c) or "").strip() for c in COLUMNS}
        label["group"] = rows[label["id"]]["group"] if label["id"] in rows else ""
        label["guideline_version"] = label["guideline_version"] or GUIDELINE
        errs = problems(label, rows, blind)
        if (label["id"], label["labeler"]) in seen:
            errs.append("(id, labeler) đã có nhãn")
        if errs:
            errors.append(f"dòng {n} {label['id']}: {'; '.join(errs)}")
            continue
        label["audit_required"] = audit_required(label)
        seen.add((label["id"], label["labeler"]))
        new.append(label)
    if errors:
        raise SystemExit("không ghi gì, sửa các dòng sau:\n" + "\n".join(errors[:30]))
    write(path, have + new)
    print(f"+{len(new)} nhãn -> {path} ({sum(bool(x['audit_required']) for x in new)} cần audit)")


def from_raw(raw: str) -> tuple[str, list[str], list[str], str]:
    """(verdict, reasons, meta_issues, note) for one workbook cell; empty verdict = not judged."""
    head, _, rest = raw.strip().partition("\n")
    head = head.strip()
    note = rest.strip().strip("()").strip()
    if head.lower().startswith("verified"):
        return "dat", [], [], note
    verdict, reasons, meta = "", [], []
    _, _, tail = head.partition(":")
    for token in filter(None, (t.strip() for t in re.split(r"[,+]", tail))):
        if token == "question-answer":
            verdict, reasons = "khong_dat", ["unanswerable_as_asked"]
        else:
            meta.append(RAW_META.get(token, "other"))
    return verdict, reasons, sorted(set(meta)), note


def import_excel(data: Path, xlsx: Path, labeler: str) -> None:
    from openpyxl import load_workbook

    ws = load_workbook(xlsx, read_only=True, data_only=True)["Dataset"]
    rows = list(ws.iter_rows(values_only=True))
    head = list(rows[0])
    extra = [i for i, h in enumerate(head) if h is None and any(r[i] for r in rows[1:] if i < len(r))]
    col = {h: i for i, h in enumerate(head) if h}
    released = release(data)
    batch = []
    for r in rows[1:]:
        rid = r[col["id"]]
        if rid not in released:
            continue
        raw = " | ".join(str(r[i]).strip() for i in extra if r[i])
        notes = []
        if (r[col["question"]] or "") != released[rid]["question"]:
            notes.append(f"câu hỏi sửa trong Excel: «{r[col['question']]}»")
        status = r[col["review_status"]]
        if status and status != released[rid]["review"]["status"]:
            notes.append(f"review_status={status} trong Excel")
            raw = raw or f"review_status={status}"
        if not raw and not notes:
            continue
        verdict, reasons, meta, note = from_raw(raw) if raw and not raw.startswith("review_status=") else ("", [], [], "")
        if raw == "review_status=CHECKED":      # the team's own mark for "checked and fine" (CMT, 28/09)
            verdict = "dat"
        batch.append({"id": rid, "labeler": labeler, "verdict": verdict, "reasons": ",".join(reasons),
                      "meta_issues": ",".join(meta), "note": " · ".join(filter(None, [note, *notes])),
                      "raw_label": raw, "guideline_version": "excel"})
    out = data / "review/_import_batch.tsv"
    write(out, batch)
    try:
        add(data, out)
    finally:
        out.unlink()


def report(data: Path) -> None:
    labels = read(data / "review/labels.tsv")
    table = collections.Counter((x["labeler"], x["group"], x["verdict"] or "—") for x in labels)
    for labeler in sorted({x["labeler"] for x in labels}):
        print(labeler)
        for g in sorted({x["group"] for x in labels if x["labeler"] == labeler}):
            cells = {v: table[(labeler, g, v)] for v in ("dat", "khong_dat", "—") if table[(labeler, g, v)]}
            print(f"  {g}: {cells}")
    by_id = collections.defaultdict(dict)
    for x in labels:
        by_id[x["id"]][x["labeler"]] = x
    pairs = [(h, m) for ls in by_id.values() for h in ls.values() if is_human(h["labeler"]) and h["verdict"]
             for m in ls.values() if not is_human(m["labeler"])]
    if pairs:
        agree = sum(h["verdict"] == m["verdict"] for h, m in pairs)
        print(f"model–người cùng gán {len(pairs)} dòng: đồng ý {agree} ({agree / len(pairs):.1%})")
    done = [x for x in labels if x["audit"]]
    need = sum(bool(x["audit_required"]) for x in labels)
    print(f"audit: {len(done)} đã làm / {need} bắt buộc")
    for stratum, keep in (("khong_dat/meta", lambda x: x["verdict"] == "khong_dat" or x["meta_issues"]),
                          ("mẫu 20% dat", lambda x: x["verdict"] == "dat" and not x["meta_issues"])):
        rows = [x for x in done if keep(x)]
        if rows:
            bad = sum(x["audit"] == "khong_dong_y" for x in rows)
            warn = "  → vượt 5%: audit toàn bộ dat của nhóm này (§6)" if stratum.startswith("mẫu") and bad / len(rows) > 0.05 else ""
            print(f"  {stratum}: {len(rows)} dòng, không đồng ý {bad} ({bad / len(rows):.1%}){warn}")


def audit_sheet(data: Path, out: Path, group: str | None) -> None:
    from openpyxl import Workbook

    released = release(data)
    wb = Workbook()
    ws = wb.active
    ws.title = "audit"
    ws.append(SHEET)
    todo = [x for x in read(data / "review/labels.tsv")
            if x["audit_required"] and not x["audit"] and (not group or x["group"] == group)]
    for x in sorted(todo, key=lambda x: (x["group"], x["id"])):
        r = released[x["id"]]
        answer = r["answer"] if r["answer"] is not None else f"(không có đáp án: {r['no_answer_reason']})"
        ctx = {"question": r["question"], "as_of": r["as_of"], "lead_in": r["target"].get("lead_in") or "",
               "answer": answer, "citation": r["target"]["citation"], "law_id": r["target"]["law_id"],
               "source_url": r["source_url"]}
        ws.append([{**x, **ctx}.get(c, "") for c in SHEET])
    wb.save(out)
    print(f"{len(todo)} nhãn cần audit -> {out}  (điền audit: dong_y | khong_dong_y, auditor: mã giả danh)")


def import_audit(data: Path, xlsx: Path) -> None:
    from openpyxl import load_workbook

    rows = list(load_workbook(xlsx, read_only=True, data_only=True).active.iter_rows(values_only=True))
    filled = {(r["id"], r["labeler"]): r for r in (dict(zip(rows[0], v)) for v in rows[1:]) if r.get("audit")}
    path = data / "review/labels.tsv"
    labels, errors, n = read(path), [], 0
    for x in labels:
        a = filled.pop((x["id"], x["labeler"]), None)
        if a is None:
            continue
        audit, auditor = str(a["audit"]).strip(), str(a.get("auditor") or "").strip()
        if audit not in AUDITS or not auditor:
            errors.append(f"{x['id']}: audit phải là dong_y|khong_dong_y và có auditor")
            continue
        x["audit"], x["auditor"], x["audit_note"], n = audit, auditor, str(a.get("audit_note") or "").strip(), n + 1
    errors += [f"{i} ({lab}): không có trong labels.tsv" for i, lab in filled]
    if errors:
        raise SystemExit("không ghi gì, sửa các dòng sau:\n" + "\n".join(errors[:30]))
    write(path, labels)
    print(f"{n} kết quả audit -> {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", type=Path, default=Path("data"))
    sub = ap.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import-excel", parents=[common])
    imp.add_argument("xlsx", type=Path)
    imp.add_argument("--labeler", default="human:excel", help="mã giả danh, không ghi tên thật")
    sub.add_parser("add", parents=[common]).add_argument("batch", type=Path)
    sub.add_parser("report", parents=[common])
    sheet = sub.add_parser("audit-sheet", parents=[common])
    sheet.add_argument("xlsx", type=Path)
    sheet.add_argument("--group", help="chỉ một nhóm, ví dụ T1")
    sub.add_parser("import-audit", parents=[common]).add_argument("xlsx", type=Path)
    args = ap.parse_args()
    if args.command == "import-excel":
        import_excel(args.data, args.xlsx, args.labeler)
    elif args.command == "add":
        add(args.data, args.batch)
    elif args.command == "audit-sheet":
        audit_sheet(args.data, args.xlsx, args.group)
    elif args.command == "import-audit":
        import_audit(args.data, args.xlsx)
    else:
        report(args.data)


if __name__ == "__main__":
    main()
