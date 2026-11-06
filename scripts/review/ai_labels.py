"""AI–AI research labels for ViLexTime: lock raw agent replies, then measure agreement.

These are `label_origin=ai`, `not_verified` labels from legal-annotator-a/b. They are never
written to the human A/B sheets and never count as human agreement (guideline 4.0 §5–§6).

    python scripts/review/ai_labels.py lock --run DIR      # DIR/raw/{a,b}_chunkN.md -> DIR/{a,b}.jsonl (once)
    python scripts/review/ai_labels.py measure --run DIR   # -> DIR/metrics.json
    python scripts/review/ai_labels.py review export --run DIR --out FILE.xlsx [--flags kiem_ngay_hieu_luc.tsv]
    python scripts/review/ai_labels.py review import --run DIR --xlsx FILE.xlsx --by CMT --out FILE.tsv

Review (định nghĩa §6, sửa 06/11): CMT duyệt mọi dòng, thấy nhãn hai AI và đề xuất hòa giải.
Dòng hai AI cùng Q1–Q4 được điền sẵn; dòng lệch để trống (hoặc điền đề xuất của adjudicator).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crosscheck import AC1_TARGET, PNEG_TARGET, cohen_kappa, gwet_ac1, specific_agreement  # noqa: E402
from test2_labels import GOOD, GUIDELINE, MIN_NEGATIVES, OPTIONS, REASONS, validate_label, worksheet_sha256  # noqa: E402

WHO = ("a", "b")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(run: Path) -> dict[str, dict]:
    records = {}
    for p in sorted((run / "input").glob("chunk*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["worksheet_sha256"] != worksheet_sha256(item["record"]):
                raise ValueError(f"{p}: binding không khớp record")
            records[item["record"]["lineage_id"]] = item["record"]
    return records


def lock(run: Path) -> None:
    chunks = sorted((run / "input").glob("chunk*.jsonl"))
    for who in WHO:
        out = run / f"{who}.jsonl"
        if out.exists():
            raise ValueError(f"{out}: đã khóa; không ghi đè nhãn thô")
        lines = []
        for c in chunks:
            raw = run / "raw" / f"{who}_{c.stem}.md"
            blocks = re.findall(r"```jsonl\s*\n(.*?)```", raw.read_text(encoding="utf-8"), re.S)
            if len(blocks) != 1:
                raise ValueError(f"{raw}: cần đúng một khối ```jsonl, có {len(blocks)}")
            lines += [s for s in blocks[0].splitlines() if s.strip()]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{who}: {len(lines)} dòng -> {out} sha256 {sha(out)}")


def read_labels(path: Path, who: str, records: dict[str, dict]) -> tuple[dict, list[dict]]:
    valid, rejected, seen = {}, [], set()
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            rejected.append({"line": n, "lineage_id": None, "errors": [f"JSON lỗi: {e}"]})
            continue
        lid = row.get("lineage_id")
        errors = []
        if lid in seen:
            errors.append("trùng lineage_id")
        seen.add(lid)
        record = records.get(lid)
        if record is None:
            errors.append("lineage_id không thuộc lô")
        else:
            if row.get("worksheet_sha256") != worksheet_sha256(record):
                errors.append("worksheet_sha256 không khớp")
            label, errs = validate_label(record, row)
            errors += errs
            if row.get("verdict") != label["verdict"]:
                errors.append(f"verdict {row.get('verdict')} khác nhãn suy ra {label['verdict']}")
        expect = {"labeler": f"ai-{who}", "label_origin": "ai", "verification_status": "not_verified",
                  "guideline_version": GUIDELINE}
        errors += [f"{k}={row.get(k)!r}, cần {v!r}" for k, v in expect.items() if row.get(k) != v]
        if errors or lid in valid:
            rejected.append({"line": n, "lineage_id": lid, "errors": errors})
        else:
            valid[lid] = row | {"quote_in_provided_sources": label["quote_in_provided_sources"]}
    return valid, rejected


def metric(va: list[str], vb: list[str], q: str) -> dict:
    neg = (lambda x: x == "khong_dat") if q == "verdict" else (lambda x: x != GOOD[q])
    binary = lambda xs: ["khong_dat" if neg(x) else "dat" for x in xs]
    adverse = sum(map(neg, va + vb))
    out = {"n": len(va), "ac1": gwet_ac1(va, vb), "kappa": cohen_kappa(va, vb),
           "category_agreement": specific_agreement(va, vb),
           "p_neg": specific_agreement(binary(va), binary(vb)).get("khong_dat"),
           "confusion_a_b": {f"{x}|{y}": c for (x, y), c in sorted(collections.Counter(zip(va, vb)).items())},
           "adverse_labels": adverse}
    if adverse < MIN_NEGATIVES or out["ac1"] is None or out["p_neg"] is None:
        out["gate"] = "not_evaluable"
    else:
        out["gate"] = "pass" if out["ac1"] >= AC1_TARGET and out["p_neg"] >= PNEG_TARGET else "not_met"
    return out


def measure(run: Path) -> dict:
    records = load_inputs(run)
    labels, rejected = {}, {}
    for who in WHO:
        labels[who], rejected[who] = read_labels(run / f"{who}.jsonl", who, records)
    ids = list(records)
    paired = [i for i in ids if i in labels["a"] and i in labels["b"]]
    groups = sorted({records[i]["group"] for i in ids})

    def block(sel: list[str]) -> dict:
        return {q: metric([labels["a"][i][q] for i in sel], [labels["b"][i][q] for i in sel], q)
                for q in (*GOOD, "verdict")}

    result = {
        "kind": "AI–AI (cùng model, sai số tương quan); không phải người–người, AI–người hay độ đúng pháp lý",
        "guideline_version": GUIDELINE, "batch_note": "Lô 0 là lô hiệu chuẩn (§5 mục 3): số đo thử, không phải cổng chính",
        "files_sha256": {f"{w}.jsonl": sha(run / f"{w}.jsonl") for w in WHO},
        "coverage": {"requested": len(ids), **{f"valid_{w}": len(labels[w]) for w in WHO}, "paired": len(paired),
                     "missing": {w: [i for i in ids if i not in labels[w]] for w in WHO}, "rejected": rejected},
        "evidence_status": {w: dict(collections.Counter(r.get("evidence_status") for r in labels[w].values())) for w in WHO},
        "quote_in_provided_sources": {w: dict(collections.Counter(str(r["quote_in_provided_sources"]) for r in labels[w].values())) for w in WHO},
        "thresholds": {"ac1": AC1_TARGET, "p_neg": PNEG_TARGET, "min_adverse": MIN_NEGATIVES},
        "metrics": block(paired),
        "by_group": {g: block([i for i in paired if records[i]["group"] == g]) for g in groups},
        "disagreements": [i for i in paired if any(labels["a"][i][q] != labels["b"][i][q] for q in (*GOOD, "verdict"))],
    }
    (run / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


REVIEW_SHEET = "Duyệt"
LABEL_KEYS = [k for q in GOOD for k in (q, q + "_reason")]
REVIEW_INFO = ["lineage_id", "group", "batch", "question", "cac_moc_va_dap_an", "van_ban_goc", "van_ban_tac_dong",
               "canh_bao_may", *[f"{w}_{k}" for w in ("AI_A", "AI_B") for k in ("nhan", "note", "evidence_status")],
               "de_xuat_hoa_giai", "worksheet_sha256", "a_sha256", "b_sha256"]
REVIEW_EDIT = [*["chot_" + k for k in LABEL_KEYS], "xac_nhan", "ghi_chu_cmt"]
CONFIRM = ("dong_y", "sua", "phan_van")


def compact(label: dict) -> str:
    return "\n".join(f"{q.upper()}: {label[q]}" + (f" ({label[q + '_reason']})" if label.get(q + "_reason") else "")
                     for q in GOOD) + f"\n=> {label['verdict']}"


def view(record: dict) -> dict:
    moc = []
    for row in record["rows"]:
        t = row.get("target", {})
        moc.append(f"Mốc: {row.get('as_of', '')}\nĐiều khoản: {t.get('citation') or t.get('provision_path') or ''}\n"
                   f"Lời dẫn: {t.get('lead_in') or ''}\nĐáp án đầy đủ: {row.get('answer') or '(không có đáp án)'}\n"
                   f"Đáp án ngắn: {row.get('short_answer') or '(không có đáp án)'}")
    src = record.get("sources", {})
    links = lambda xs: "\n".join(dict.fromkeys(x["source_url"] for x in xs if x.get("source_url")))
    return {"lineage_id": record["lineage_id"], "group": record["group"], "batch": record.get("batch"),
            "question": record["question"], "cac_moc_va_dap_an": "\n\n".join(moc),
            "van_ban_goc": links([src.get("base") or {}] + record["rows"]), "van_ban_tac_dong": links(src.get("actors", []))}


def review_rows(run: Path, flags: dict[str, str]) -> list[dict]:
    records = load_inputs(run)
    labels = {w: read_labels(run / f"{w}.jsonl", w, records)[0] for w in WHO}
    proposals = {}
    adj = run / "adjudication.jsonl"
    if adj.exists():
        proposals = {r["lineage_id"]: r for r in map(json.loads, adj.read_text(encoding="utf-8").splitlines())}
    rows = []
    for lid, record in records.items():
        a, b = labels["a"].get(lid), labels["b"].get(lid)
        row = view(record) | {"canh_bao_may": flags.get(lid, ""), "worksheet_sha256": worksheet_sha256(record),
                              "a_sha256": hashlib.sha256(json.dumps(a, sort_keys=True, ensure_ascii=False).encode()).hexdigest() if a else "",
                              "b_sha256": hashlib.sha256(json.dumps(b, sort_keys=True, ensure_ascii=False).encode()).hexdigest() if b else ""}
        for w, lab in (("AI_A", a), ("AI_B", b)):
            row |= {f"{w}_nhan": compact(lab) if lab else "(thiếu nhãn)", f"{w}_note": (lab or {}).get("note", ""),
                    f"{w}_evidence_status": (lab or {}).get("evidence_status", "")}
        prefill = None
        if a and b and all(a[k] == b[k] for k in LABEL_KEYS):
            prefill = a
        elif lid in proposals:
            p = proposals[lid]
            row["de_xuat_hoa_giai"] = compact(p) + ("\n" + p.get("note", "") if p.get("note") else "")
            prefill = p
        row |= {"chot_" + k: (prefill or {}).get(k, "") for k in LABEL_KEYS}
        rows.append(row)
    return rows


def review_export(run: Path, out: Path, flags: dict[str, str]) -> int:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Protection
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    if out.exists():
        raise ValueError(f"{out}: đã có; không ghi đè phiếu duyệt")
    rows = review_rows(run, flags)
    wb = Workbook()
    guide = wb.active
    guide.title = "Đọc trước"
    for t in ["Phiếu duyệt nhãn AI theo định nghĩa §6 (sửa 06/11/2026) và thẻ 4.0 (docs/vilextime-annotation.md).",
              "Mỗi hàng một câu hỏi. Cột AI_A_nhan, AI_B_nhan là nhãn hai agent gán độc lập; de_xuat_hoa_giai là đề xuất cho dòng lệch.",
              "Hai AI cùng nhãn thì cột chot_* đã điền sẵn. Đọc câu hỏi, mốc, đáp án và văn bản gốc rồi chọn xac_nhan:",
              "  dong_y = giữ nguyên chot_*;  sua = đã sửa chot_* (ghi lý do vào ghi_chu_cmt);  phan_van = để luật sư chốt.",
              "Dòng lệch mà chưa có đề xuất thì chot_* trống: tự điền đủ Q1–Q4 trước khi chọn.",
              "Q1 dung/sai · Q2 co/khong · Q3 co/khong · Q4 khong/co/khong_chac. Câu bất lợi chọn một lý do đúng; câu đạt để trống lý do.",
              "canh_bao_may: kiểm tra tự động (ví dụ ngày hiệu lực trong phiếu lệch lời văn). Chỉ sửa cột xanh."]:
        guide.append([t])
    guide.column_dimensions["A"].width = 120
    ws = wb.create_sheet(REVIEW_SHEET)
    cols = REVIEW_INFO + REVIEW_EDIT
    ws.append(cols)
    wide = {"question": 45, "cac_moc_va_dap_an": 70, "AI_A_nhan": 28, "AI_B_nhan": 28, "AI_A_note": 40, "AI_B_note": 40,
            "de_xuat_hoa_giai": 35, "canh_bao_may": 30, "ghi_chu_cmt": 35}
    for i, name in enumerate(cols, 1):
        c = ws.cell(1, i)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="44546A")
        ws.column_dimensions[get_column_letter(i)].width = wide.get(name, 16)
    for i, row in enumerate(rows, 2):
        for j, name in enumerate(cols, 1):
            v = row.get(name, "")
            if isinstance(v, str) and len(v) > 32767:
                raise ValueError(f"{row['lineage_id']}: {name} vượt giới hạn XLSX")
            c = ws.cell(i, j, v)
            if isinstance(v, str):
                c.data_type = "s"
            c.protection = Protection(locked=name not in REVIEW_EDIT)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.fill = PatternFill("solid", fgColor="EAF3EC" if name in REVIEW_EDIT else "F2F2F2")
    last = len(rows) + 1
    lists = {**{"chot_" + q: OPTIONS[q] for q in GOOD},
             **{"chot_" + q + "_reason": [r for rs in REASONS[q].values() for r in rs] for q in GOOD}, "xac_nhan": CONFIRM}
    for name, options in lists.items():
        col = get_column_letter(cols.index(name) + 1)
        dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True, showErrorMessage=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{last}")
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = ws.dimensions
    ws.protection.sheet = True
    ws.protection.autoFilter = False
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return len(rows)


def review_import(run: Path, xlsx: Path, by: str, out: Path) -> dict:
    """All-or-nothing: every row must be confirmed and valid, and bound to the current AI labels."""
    from openpyxl import load_workbook

    if not by.strip():
        raise ValueError("--by: ghi người duyệt")
    expected = {r["lineage_id"]: r for r in review_rows(run, {})}
    records = load_inputs(run)
    labels = {w: read_labels(run / f"{w}.jsonl", w, records)[0] for w in WHO}
    ws = load_workbook(xlsx)[REVIEW_SHEET]
    head = [c.value for c in ws[1]]
    if head != REVIEW_INFO + REVIEW_EDIT:
        raise ValueError("xlsx: cột bị đổi; dùng lại phiếu xuất")
    result, errors, seen = [], [], set()
    for values in ws.iter_rows(min_row=2, values_only=True):
        cells = {k: ("" if v is None else str(v).strip()) for k, v in zip(head, values)}
        lid = cells["lineage_id"]
        exp = expected.get(lid)
        if exp is None or any(cells[k] != (exp[k] or "") for k in ("worksheet_sha256", "a_sha256", "b_sha256")):
            errors.append(f"{lid}: không khớp phiếu/nhãn AI hiện tại")
            continue
        seen.add(lid)
        logs = "\n".join(dict.fromkeys(labels[w][lid]["search_log"] for w in WHO
                                        if lid in labels[w] and labels[w][lid].get("search_log")))
        body = {k: cells["chot_" + k] for k in LABEL_KEYS} | {"note": cells["ghi_chu_cmt"],
                                                              "search_log": logs or cells["ghi_chu_cmt"]}
        label, problems = validate_label(records[lid], body, require_quote=False)
        action = cells["xac_nhan"]
        prefilled = all(exp["chot_" + k] for k in GOOD)
        changed = prefilled and any(cells["chot_" + k] != (exp["chot_" + k] or "") for k in LABEL_KEYS)
        if action not in CONFIRM:
            problems.append("xac_nhan: chọn dong_y, sua hoặc phan_van")
        elif action == "dong_y" and changed:
            problems.append("đã sửa chot_* thì chọn sua")
        elif action == "sua" and not cells["ghi_chu_cmt"]:
            problems.append("sua: ghi lý do vào ghi_chu_cmt")
        if action != "phan_van":
            errors.extend(f"{lid}: {e}" for e in problems)
        result.append({"lineage_id": lid, **{k: label[k] for k in LABEL_KEYS}, "verdict": label["verdict"],
                       "xac_nhan": action, "prefilled": prefilled, "changed": changed, "note": cells["ghi_chu_cmt"],
                       "reviewer": by.strip(), "label_tier": "ai_gan_nguoi_xac_nhan" if action != "phan_van" else "cho_luat_su",
                       "worksheet_sha256": cells["worksheet_sha256"], "a_sha256": cells["a_sha256"], "b_sha256": cells["b_sha256"],
                       "guideline_version": GUIDELINE})
    errors += [f"{lid}: thiếu hàng" for lid in expected if lid not in seen]
    if errors:
        raise ValueError("Chưa duyệt hợp lệ, KHÔNG ghi gì:\n" + "\n".join(errors))
    import csv
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(result[0]), delimiter="\t")
        w.writeheader()
        w.writerows(result)
    pre = [r for r in result if r["prefilled"] and r["xac_nhan"] != "phan_van"]
    return {"rows": len(result), "phan_van": sum(r["xac_nhan"] == "phan_van" for r in result),
            "prefilled_confirmed": len(pre), "cmt_changed_ai_label": sum(r["changed"] for r in pre),
            "dat": sum(r["verdict"] == "dat" for r in result if r["xac_nhan"] != "phan_van")}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("lock", "measure", "review"))
    p.add_argument("step", nargs="?", choices=("export", "import"))
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--out", type=Path)
    p.add_argument("--xlsx", type=Path)
    p.add_argument("--by", default="")
    p.add_argument("--flags", type=Path, help="TSV của check_effective_dates.py")
    args = p.parse_args()
    if args.action == "review":
        if args.step == "export":
            import csv
            flags = collections.defaultdict(list)
            if args.flags:
                for r in csv.DictReader(args.flags.open(encoding="utf-8"), delimiter="\t"):
                    if r["status"] in ("mismatch", "unparsed"):
                        flags[r["lineage_id"]].append(f"{r['document']}: phiếu ghi hiệu lực {r['effective_from']}, "
                                                      f"lời văn {r['clause_date'] or '(không đọc được)'}")
            print(review_export(args.run, args.out, {k: "\n".join(dict.fromkeys(v)) for k, v in flags.items()}), "câu ->", args.out)
        else:
            print(review_import(args.run, args.xlsx, args.by, args.out))
    elif args.action == "lock":
        lock(args.run)
    else:
        r = measure(args.run)
        for q, m in r["metrics"].items():
            print(q, {k: m[k] for k in ("n", "ac1", "kappa", "p_neg", "adverse_labels", "gate")})
        print("coverage", {k: v for k, v in r["coverage"].items() if k != "rejected"},
              {w: len(v) for w, v in r["coverage"]["rejected"].items()})


if __name__ == "__main__":
    main()
