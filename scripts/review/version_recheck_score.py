#!/usr/bin/env python3
"""Mở khóa phiếu chấm lại sai phiên bản (33 câu, version_recheck_sheet.py) và đo cờ wrong_version của scorer.

    .venv/bin/python scripts/review/version_recheck_score.py \\
        --dir data/review/human_score_g4/recheck_versions --filled phieu_da_cham.xlsx \\
        --out runs/version_recheck_20261117/agreement.json --note "<ai chấm, có AI nháp không>"
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from human_answer_sheet import wilson  # noqa: E402

LABELS = {"dung", "sai_phien_ban", "sai_noi_dung"}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731


def rows(path: Path) -> list[tuple]:
    from openpyxl import load_workbook
    return [r for r in load_workbook(path, read_only=True)["Chấm"].iter_rows(min_row=2, values_only=True)
            if r and r[0] is not None]


def summarize(labels: list[str], key: list[dict]) -> dict:
    by = collections.defaultdict(collections.Counter)
    for l, k in zip(labels, key):
        by[k["why"]][l] += 1
    flag, miss = by["wrong_version"], by["b1_sai_noi_dung"]
    nf, nm = sum(flag.values()), sum(miss.values())
    return {"table": {w: dict(c) for w, c in sorted(by.items())},
            "flag_precision": {"k": flag["sai_phien_ban"], "n": nf, "wilson95": wilson(flag["sai_phien_ban"], nf)},
            "unflagged_b1_human_sai_phien_ban": {"k": miss["sai_phien_ban"], "n": nm,
                                                 "wilson95": wilson(miss["sai_phien_ban"], nm)},
            "changed_vs_1_5": [{"stt": k["stt"], "system": k["system"], "why": k["why"], "label_1_5": k["label_1_5"],
                                "label": l} for l, k in zip(labels, key) if l != k["label_1_5"]]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--filled", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--note", required=True)
    a = ap.parse_args()
    manifest = json.loads((a.dir / "manifest.json").read_text(encoding="utf-8"))
    for name, h in manifest["outputs"].items():
        if sha(a.dir / name) != h:
            raise SystemExit(f"{name} khác hash trong manifest")
    key = [json.loads(line) for line in (a.dir / "khoa.jsonl").open(encoding="utf-8")]
    blank, filled = rows(a.dir / "phieu.xlsx"), rows(a.dir / a.filled)
    if len(filled) != len(key) or any(b[:5] != f[:5] for b, f in zip(blank, filled)):
        raise SystemExit("phiếu đã chấm khác phiếu gốc ở cột 1–5 hoặc số dòng")
    labels = [(f[5] or "").strip() for f in filled]
    bad = [i + 1 for i, l in enumerate(labels) if l not in LABELS]
    if bad:
        raise SystemExit(f"dòng thiếu/lạ nhãn: {bad}")
    out = {**summarize(labels, key), "note": a.note, "caveat_sheet": manifest["caveat"],
           "inputs": {str(p): sha(p) for p in (a.dir / a.filled, a.dir / "khoa.jsonl", a.dir / "phieu.xlsx")}}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    p, m = out["flag_precision"], out["unflagged_b1_human_sai_phien_ban"]
    print(f"cờ đúng {p['k']}/{p['n']} {p['wilson95']}; không cờ mà sai phiên bản {m['k']}/{m['n']} {m['wilson95']} → {a.out}")


if __name__ == "__main__":
    assert summarize(["sai_phien_ban", "dung"], [{"why": "wrong_version", "label_1_5": "x", "stt": 1, "system": "b4"},
                     {"why": "b1_sai_noi_dung", "label_1_5": "dung", "stt": 2, "system": "b1"}])["flag_precision"]["k"] == 1
    main()
