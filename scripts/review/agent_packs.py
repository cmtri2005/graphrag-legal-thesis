#!/usr/bin/env python3
"""ViLexTime — gói gán nhãn cho một model ngoài (Codex...) và đo độ khớp với nhãn người (26/10).

    python scripts/review/agent_packs.py build --out DIR     # DIR nằm NGOÀI repo; khóa đáp án ghi ở DIR/../../key_calib.tsv
    python scripts/review/agent_packs.py score --out DIR RESULT.tsv

Gói trộn dòng cần gán (test, ranh_gioi, chưa có nhãn người theo 3.0) với dòng hiệu chuẩn (đã có nhãn người
theo 3.0: A=B, hoặc luật sư chốt) theo thứ tự ngẫu nhiên, nên model không biết dòng nào bị chấm. Gói không chứa
nhãn nào. Đo bằng chính hàm của crosscheck.py (AC1, p_neg), báo riêng theo nhóm.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
csv.field_size_limit(sys.maxsize)
from crosscheck import gwet_ac1, specific_agreement  # noqa: E402

KEEP = ("id", "group", "subgroup", "question", "as_of", "lead_in", "answer", "short_answer", "changed_span",
        "citation", "law_id", "valid_from", "valid_to", "source_url", "trich_van_ban_goc",
        "trich_van_ban_tac_dong", "cac_phien_ban")
LONG = ("cac_phien_ban", "trich_van_ban_tac_dong", "trich_van_ban_goc")
OUT_COLS = ["id", "verdict", "reasons", "da_xem_van_ban_tac_dong", "cham_lan_sua", "noi_dung_con_o_dau", "note"]
PACK = 50


def read(p: Path) -> dict[str, dict]:
    with p.open(encoding="utf-8", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f, delimiter="\t")}


def calibration_verdict(a: dict, b: dict | None, adjudicated: dict | None) -> str | None:
    """Use independent agreement, or the lawyer's unaided lot-0 decision."""
    if not b or not a["verdict"] or not b["verdict"]:
        return None
    if a["guideline_version"] != "3.0" or b["guideline_version"] != "3.0":
        return None
    if a["verdict"] == b["verdict"]:
        return a["verdict"]
    return adjudicated["verdict"] if a["lo"] == "0" and adjudicated else None


def build(out: Path, data: Path) -> None:
    a, b = read(data / "review/kiem_A.tsv"), read(data / "review/kiem_B.tsv")
    adj = read(data / "review/hoa_giai_kiem.tsv")
    rel = {}
    for line in (data / "vilextime_dataset/vilextime.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        rel[d["id"]] = d
    calib: dict[str, str] = {}
    for i, r in a.items():
        verdict = calibration_verdict(r, b.get(i), adj.get(i))
        if verdict:
            calib[i] = verdict
    target = [i for i, r in a.items() if i not in calib and rel.get(i, {}).get("split") == "test"
              and rel[i]["as_of_strategy"] == "ranh_gioi" and i not in adj]
    ids = sorted(calib) + sorted(target)
    random.Random("agent-packs-2610").shuffle(ids)
    out.mkdir(parents=True, exist_ok=True)
    for n in range(0, len(ids), PACK):
        with (out / f"pack_{n // PACK + 1:02d}.jsonl").open("w", encoding="utf-8") as f:
            for i in ids[n:n + PACK]:
                row = {k: (a[i][k][:3000] if k in LONG else a[i][k]) for k in KEEP}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    key = out.parent.parent / "key_calib.tsv"
    with key.open("w", encoding="utf-8") as f:
        f.write("id\tgroup\tverdict\n")
        for i, v in sorted(calib.items()):
            f.write(f"{i}\t{a[i]['group']}\t{v}\n")
    print(f"{len(ids)} dòng ({len(calib)} hiệu chuẩn, {len(target)} cần gán) -> {-(-len(ids) // PACK)} gói ở {out}; khóa: {key}")


def score(out: Path, result: Path, key_path: Path | None = None) -> None:
    key = {r["id"]: r for r in read(key_path or out.parent.parent / "key_calib.tsv").values()}
    got = read(result)
    bad = sorted(set(got) - set(key) - set(read_ids(out)))
    ids = sorted(set(key) & set(got))
    print(f"gán {len(got)} dòng, trong đó hiệu chuẩn {len(ids)}/{len(key)}; id lạ: {len(bad)}")
    for name, sel in [("toàn tập", ids)] + [(g, [i for i in ids if key[i]["group"] == g]) for g in ("T1", "T2", "T3", "T5", "T6")]:
        x, y = [key[i]["verdict"] for i in sel], [got[i]["verdict"] for i in sel]
        if not x:
            continue
        ac1 = gwet_ac1(x, y)
        pn = specific_agreement(x, y).get("khong_dat")
        print(f"  {name:9} n={len(sel):3}  AC1={'-' if ac1 is None else f'{ac1:.3f}'}  p_neg={'-' if pn is None else f'{pn:.3f}'}"
              f"  khong_dat: người {x.count('khong_dat')} / model {y.count('khong_dat')}")
    x, y = [key[i]["verdict"] for i in ids], [got[i]["verdict"] for i in ids]
    ok = (gwet_ac1(x, y) or 0) >= 0.80 and (specific_agreement(x, y).get("khong_dat") or 0) >= 0.60
    print("ngưỡng AC1 >= 0.80 và p_neg >= 0.60 ->", "ĐẠT" if ok else "CHƯA ĐẠT")


def read_ids(out: Path) -> set[str]:
    return {json.loads(l)["id"] for p in out.glob("pack_*.jsonl") for l in p.open(encoding="utf-8")}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "score"))
    ap.add_argument("result", nargs="?", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--key", type=Path, help="calibration key for score; default: OUT/../../key_calib.tsv")
    args = ap.parse_intermixed_args()
    build(args.out, args.data) if args.cmd == "build" else score(args.out, args.result, args.key)
