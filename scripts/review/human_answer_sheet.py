#!/usr/bin/env python3
"""REFACTOR_PLAN 1.5: phiếu người chấm câu trả lời G4, để đo độ khớp của scorer khớp chuỗi với người.

Rút có seed, phân tầng theo hệ x (có/không đáp án), từ dự đoán lần 1 của bộ cuối (lát `all`, 318 dòng).
Người chấm KHÔNG thấy tên hệ và điểm máy: hai cột đó chỉ nằm trong file khóa riêng.
Không gọi model; không sửa dự đoán hay scorer.

    PYTHONPATH=src .venv/bin/python scripts/review/human_answer_sheet.py \\
        --g4 runs/final_g4_20261112/r1/test --release data/vilextime_final/vilextime.jsonl \\
        --out data/review/human_score_g4/  --n 100 --seed 20261113

Đọc phiếu đã chấm (sau khi chấm xong mới mở khóa), so người với scorer:

    PYTHONPATH=src .venv/bin/python scripts/review/human_answer_sheet.py \\
        --g4 runs/final_g4_20261112/r1/test --release data/vilextime_final/vilextime.jsonl \\
        --filled data/review/human_score_g4/phieu_cham_da_cham.xlsx --out runs/posthoc_g4_20261113/human_score/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
import score_vilextime as sv  # noqa: E402

SYSTEMS = ("b1", "b4", "proposed2")
LABELS = "dung | sai_phien_ban | sai_noi_dung | khong_tra_loi | tu_choi_dung | khang_dinh_bai_bo_sai"
COLUMNS = ("stt", "cau_hoi", "moc", "dap_an_dung_tai_moc", "tra_loi_cua_he", "he_noi_hieu_luc",
           "nhan_nguoi", "ghi_chu")


def sample(rows: list[dict], preds: dict[str, dict], n: int, seed: int) -> list[tuple[str, dict]]:
    """n câu chia đều cho các hệ; trong mỗi hệ, dòng không đáp án lấy đúng tỷ lệ của lát."""
    rng = random.Random(seed)
    per = n // len(SYSTEMS)
    share = sum(not r["answerable"] for r in rows) / len(rows)
    out = []
    for i, system in enumerate(SYSTEMS):
        k = per + (1 if i < n - per * len(SYSTEMS) else 0)
        no = [r for r in rows if not r["answerable"]]
        yes = [r for r in rows if r["answerable"]]
        k_no = round(k * share)
        out += [(system, r) for r in rng.sample(no, k_no) + rng.sample(yes, k - k_no)]
    rng.shuffle(out)
    return out


HUMAN_OK = ("dung", "tu_choi_dung")


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    p, d = k / n, 1 + z * z / n
    mid, half = (p + z * z / (2 * n)) / d, z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5 / d
    return [round(mid - half, 4), round(mid + half, 4)]


def kappa(pairs: list[tuple[bool, bool]]) -> float:
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return round((po - pe) / (1 - pe), 4)


def agreement(labels: list[str], key: list[dict], wrong_version: list[bool | None]) -> dict:
    """labels[i], key[i], wrong_version[i] cùng một dòng phiếu. Đúng theo người = dung | tu_choi_dung."""
    bad = sorted({l for l in labels if l not in LABELS.split(" | ")})
    if bad:
        raise SystemExit(f"nhãn lạ: {bad}")
    pairs = [(l in HUMAN_OK, bool(k["scorer_accuracy"])) for l, k in zip(labels, key)]
    agree = sum(a == b for a, b in pairs)
    per = {}
    for s in SYSTEMS:
        idx = [i for i, k in enumerate(key) if k["system"] == s]
        per[s] = {"n": len(idx), "human_correct": sum(pairs[i][0] for i in idx),
                  "scorer_correct": sum(pairs[i][1] for i in idx),
                  "labels": dict(Counter(labels[i] for i in idx).most_common()),
                  "wrong_version_flagged": sum(bool(wrong_version[i]) for i in idx),
                  "wrong_version_flagged_human_sai_phien_ban": sum(bool(wrong_version[i]) and labels[i] == "sai_phien_ban"
                                                                   for i in idx)}
    wv = Counter(f"{'gan_co' if w else 'khong_co'}|{l}" for w, l in zip(wrong_version, labels) if w is not None)
    return {"n": len(pairs), "agree": agree, "agree_rate": round(agree / len(pairs), 4),
            "agree_wilson95": wilson(agree, len(pairs)), "cohen_kappa": kappa(pairs),
            "human_ok_scorer_ok": sum(a and b for a, b in pairs), "human_ok_scorer_wrong": sum(a and not b for a, b in pairs),
            "human_wrong_scorer_ok": sum(b and not a for a, b in pairs), "human_wrong_scorer_wrong": sum(not a and not b for a, b in pairs),
            "per_system": per,
            "wrong_version_vs_human": {"flagged": sum(bool(w) for w in wrong_version),
                                       "flagged_human_sai_phien_ban": wv["gan_co|sai_phien_ban"],
                                       "human_sai_phien_ban": labels.count("sai_phien_ban"),
                                       "table": dict(sorted(wv.items()))},
            "disagreements": [{"stt": k["stt"], "system": k["system"], "group": k["group"], "human": l,
                               "scorer_accuracy": k["scorer_accuracy"]}
                              for (a, b), l, k in zip(pairs, labels, key) if a != b]}


def score_filled(args: argparse.Namespace, release: list[dict], extra: dict, preds: dict) -> None:
    from openpyxl import load_workbook
    key_path = args.filled.parent / "khoa.jsonl"
    key = [json.loads(line) for line in key_path.open(encoding="utf-8")]
    sheet = list(load_workbook(args.filled, read_only=True)["Chấm"].iter_rows(min_row=2, values_only=True))
    sheet = [r for r in sheet if r and r[0] is not None]
    if len(sheet) != len(key):
        raise SystemExit(f"phiếu {len(sheet)} dòng, khóa {len(key)} dòng")
    by_id = {r["id"]: {**r, "_distractors": extra.get(r["id"], [])} for r in release}
    labels, wrong = [], []
    for line, k in zip(sheet, key):
        r, p = by_id[k["id"]], preds[k["system"]][k["id"]]
        if int(float(line[0])) != k["stt"] or line[1] != r["question"] or (line[4] or "") != (p.get("answer") or ""):
            raise SystemExit(f"dòng {k['stt']} của phiếu không khớp khóa/dự đoán")
        if sv.correct(r, p) != k["scorer_accuracy"]:
            raise SystemExit(f"dòng {k['stt']}: scorer hiện tại khác khóa")
        if not line[6]:
            raise SystemExit(f"dòng {k['stt']} chưa có nhãn")
        labels.append(line[6].strip())
        said = f" {sv.norm(p.get('answer') if p.get('answerable') is not False else '')} "   # như row_scores
        wrong.append(any(f" {d} " in said for d in r["_distractors"]) if r["answerable"] and r["_distractors"] else None)
    out = agreement(labels, key, wrong)
    out["note"] = ("Người chấm: CMT, tự chấm toàn bộ, không có AI nháp; lần chấm đầu mù tên hệ và điểm máy; lần xem lại (dòng 93) sau khi đã thấy các dòng lệch với scorer. "
                   "Mẫu: test, giua_khoang, T2/T3/T6, lần 1; không có T1.")
    out["inputs"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in [args.filled, key_path, args.release, *(args.g4 / f"{s}.jsonl" for s in SYSTEMS)]}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "agreement.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"khớp {out['agree']}/{out['n']} {out['agree_wilson95']}, kappa {out['cohen_kappa']}; "
          f"wrong_version {out['wrong_version_vs_human']['flagged_human_sai_phien_ban']}/{out['wrong_version_vs_human']['flagged']}"
          f" → {args.out}/agreement.json")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--g4", type=Path, required=True)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261113)
    ap.add_argument("--filled", type=Path, help="phiếu đã chấm; khóa đọc ở cùng thư mục")
    args = ap.parse_args()

    release = sv.load_rows(args.release)
    extra = sv.distractors(release)
    rows = [{**r, "_distractors": extra.get(r["id"], [])} for r in release
            if r.get("split") == "test" and r["as_of_strategy"] == "giua_khoang" and r["group"] in ("T2", "T3", "T6")]
    preds = {s: {p["id"]: p for p in map(json.loads, (args.g4 / f"{s}.jsonl").open(encoding="utf-8"))} for s in SYSTEMS}
    if args.filled:
        return score_filled(args, release, extra, preds)
    picked = sample(rows, preds, args.n, args.seed)

    args.out.mkdir(parents=True, exist_ok=True)
    sheet, key = [], []
    for i, (system, r) in enumerate(picked, 1):
        p = preds[system][r["id"]]
        gold = r["answer"] if r["answerable"] else "(Đã hết hiệu lực tại mốc này; câu trả lời đúng là khẳng định hết hiệu lực)"
        said = "không" if p.get("answerable") is False else "còn / không rõ"
        sheet.append({"stt": i, "cau_hoi": r["question"], "moc": r["as_of"], "dap_an_dung_tai_moc": gold,
                      "tra_loi_cua_he": p.get("answer") or "", "he_noi_hieu_luc": said, "nhan_nguoi": "", "ghi_chu": ""})
        key.append({"stt": i, "id": r["id"], "system": system, "group": r["group"], "answerable": r["answerable"],
                    "scorer_accuracy": sv.correct(r, p)})

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Chấm"
    ws.append(COLUMNS)
    for line in sheet:
        ws.append([line[c] for c in COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col, width in zip("ABCDEFGH", (6, 50, 12, 70, 70, 14, 22, 30)):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    guide = wb.create_sheet("Hướng dẫn")
    for text in (
            "Mỗi dòng: một câu hỏi, mốc thời gian, đáp án đúng tại mốc (lời văn điều khoản), và câu trả lời của một hệ.",
            "Không có tên hệ, không có điểm máy. Chấm độc lập, không tra lại hệ.",
            f"Cột nhan_nguoi chọn đúng một nhãn: {LABELS}.",
            "dung: câu trả lời nêu đúng nội dung quy định tại mốc (được diễn đạt khác, được thừa ý nhưng không mâu thuẫn).",
            "sai_phien_ban: nêu nội dung của phiên bản khác (trước hoặc sau mốc) của cùng điều khoản.",
            "sai_noi_dung: nêu nội dung khác, không phải phiên bản nào của điều khoản này.",
            "khong_tra_loi: để trống hoặc nói không rõ khi lẽ ra có đáp án.",
            "tu_choi_dung: dòng đáp án ghi 'Đã hết hiệu lực' và hệ nói HIỆU LỰC không.",
            "khang_dinh_bai_bo_sai: hệ nói HIỆU LỰC không khi điều khoản vẫn còn hiệu lực.",
            "Phân vân thì vẫn chọn nhãn và ghi lý do ở ghi_chu."):
        guide.append([text])
    guide.column_dimensions["A"].width = 120
    wb.save(args.out / "phieu_cham.xlsx")
    (args.out / "khoa.jsonl").write_text("".join(json.dumps(k, ensure_ascii=False) + "\n" for k in key), encoding="utf-8")
    manifest = {"seed": args.seed, "n": len(sheet), "systems": SYSTEMS, "labels": LABELS,
                "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [args.release, *(args.g4 / f"{s}.jsonl" for s in SYSTEMS)]},
                "outputs": {name: hashlib.sha256((args.out / name).read_bytes()).hexdigest()
                            for name in ("phieu_cham.xlsx", "khoa.jsonl")}}
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{args.out}/phieu_cham.xlsx: {len(sheet)} câu; khóa riêng ở khoa.jsonl (không mở khi chấm)")


if __name__ == "__main__":
    main()
