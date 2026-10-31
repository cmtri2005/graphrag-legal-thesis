#!/usr/bin/env python3
"""ViLexTime bộ test 2 — gói lọc ứng viên cho Claude, và chấm hiệu chuẩn (docs/plans/active/vilextime-test2.md, bước 1–2).

    python scripts/review/test2_packs.py build --out DIR              # DIR ngoài repo; khóa ở DIR/../../key_loc.tsv
    python scripts/review/test2_packs.py score --out DIR RESULT.tsv

Một mục là một lineage (một câu hỏi tương lai), không phải một dòng. Gói trộn ứng viên mới (rút ngẫu nhiên theo
tầng, bỏ văn bản của split dev và lineage đã có trong v1.0) với lineage v1.0 đã có nhãn cuối của người, theo thứ tự
ngẫu nhiên, nên bên lọc không biết mục nào bị chấm. Gói không có câu hỏi, đáp án ngắn hay nhãn. Bằng chứng dựng bằng
đúng các hàm người gán đã thấy: `kiem_hints.hints` (chuỗi phiên bản, gợi ý chỗ chuyển) và `crosscheck_evidence.py`
(trích văn bản gốc, văn bản tác động, chuyển tiếp, hiệu lực).
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/pipeline"))
sys.path.insert(0, str(Path(__file__).parent))
csv.field_size_limit(sys.maxsize)

SEED = "vilextime-test2-2910"
GROUPS = ("T2", "T3", "T6")
# Đợt 1, khoảng một nửa số cần; thiếu thì rút đợt 2 cùng seed (rút tiếp trong cùng thứ tự đã xáo)
QUOTA = {"T2": 150, "T2 gần giống": 65, "T3": 220, "T6 cấp trên": 75, "T6 đích danh": 75}
# Lý do ở cấp lineage: bên lọc nhìn được khi chưa có câu hỏi. Lý do ở cấp câu hỏi không dùng để hiệu chuẩn.
LINEAGE_CODES = {"cosmetic_only", "rename_only", "auto_reference_update", "single_change", "relocated",
                 "relocation_unclear", "reference_only", "superseded_by_other_norm", "gold_wrong",
                 "restructuring_2025", "transitional_rule"}
PACK, TEXT_MAX = 25, 3000
CATCH_MIN, FALSE_REJECT_MAX = 0.80, 0.30    # CMT 29/10: "càng chất lượng càng tốt"
OUT_COLS = ["item", "quyet_dinh", "ma", "can_cu", "ghi_chu"]


def stratum(r: dict) -> str:
    if r["group"] == "T2":
        return "T2 gần giống" if r.get("near_identical") else "T2"
    if r["group"] == "T6":
        return "T6 cấp trên" if r.get("repeal_mode") == "ancestor" else "T6 đích danh"
    return r["group"]


def independent(review: dict) -> bool:
    """A final human label made without AI help: A and B agreeing, or the lawyer deciding unaided."""
    who = review.get("labeler") or ""
    return (review.get("status") == "checked" and review.get("source") == "human"
            and (who == "A+B" or who.startswith("luật sư")) and "Claude" not in who)


def lineage_truth(reviews: list[dict]) -> tuple[str, list[str]] | None:
    """('tot', []) when every boundary row passed; ('xau', codes) on a lineage-level reason; else None."""
    if not reviews or not all(independent(r) for r in reviews):
        return None
    bad = sorted({c for r in reviews if r["verdict"] == "khong_dat" for c in r["reasons"]})
    if not bad:
        return "tot", []
    hit = [c for c in bad if c in LINEAGE_CODES]
    return ("xau", hit) if hit else None


def read_tsv(p: Path) -> dict[str, dict]:
    with p.open(encoding="utf-8", newline="") as f:
        return {r[next(iter(r))]: r for r in csv.DictReader(f, delimiter="\t")}


def build(out: Path, data: Path) -> None:
    from export_release import final_labels
    from kiem_hints import hints, versions_of
    from vilexgraph.framework.corpus import Corpus

    rows = [json.loads(l) for g in GROUPS for l in (data / f"derived/vilextime/{g}.jsonl").open(encoding="utf-8")]
    by_lineage: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_lineage[r["lineage_id"]].append(r)
    lineage_of = {r["id"]: r["lineage_id"] for r in rows}

    main = [json.loads(l) for l in (data / "vilextime_dataset/vilextime.jsonl").open(encoding="utf-8")]
    used = {r["lineage_id"] for r in main}
    doc_of = {lid: rs[0]["target"]["document_id"] for lid, rs in by_lineage.items()}
    dev_docs = {doc_of[r["lineage_id"]] for r in main if r["split"] == "dev" and r["lineage_id"] in doc_of}

    reviews: dict[str, list[dict]] = collections.defaultdict(list)
    for i, rev in final_labels(data / "review").items():
        if i in lineage_of:
            reviews[lineage_of[i]].append(rev)
    truth = {lid: t for lid, revs in reviews.items() if (t := lineage_truth(revs))}

    rng = random.Random(SEED)
    pool: dict[str, list[str]] = collections.defaultdict(list)
    for lid in sorted(by_lineage):
        # a lineage someone already labelled is calibration or was dropped, never a fresh candidate
        if lid not in used and lid not in reviews and doc_of[lid] not in dev_docs:
            pool[stratum(by_lineage[lid][0])].append(lid)
    picked = []
    for s, n in QUOTA.items():
        rng.shuffle(pool[s])
        picked += pool[s][:n]
    items = sorted(truth) + picked
    rng.shuffle(items)

    work = out.parent.parent
    out.mkdir(parents=True, exist_ok=True)
    item_rows = [r for lid in items for r in sorted(by_lineage[lid], key=lambda r: r["as_of"])]
    # the group files predate enrich_vilextime, which names each transition's operation the same way
    need = {t["event_id"] for r in item_rows for t in r["derivation"]["transitions"]}
    ops = {e["id"]: e["operation"] for e in map(json.loads, (data / "derived/provision_events.jsonl").open(encoding="utf-8"))
           if e["id"] in need}
    for r in item_rows:
        for t in r["derivation"]["transitions"]:
            t["op"] = ops.get(t["event_id"])
    (work / "rows.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in item_rows),
                                     encoding="utf-8")
    (work / "ids.txt").write_text("".join(r["id"] + "\n" for r in item_rows), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts/review/crosscheck_evidence.py"), "--data", str(data),
                    "--ids", str(work / "ids.txt"), "--release", str(work / "rows.jsonl"),
                    "--out", str(work / "evidence.jsonl")], check=True)
    evidence = {e["id"]: e for e in map(json.loads, (work / "evidence.jsonl").open(encoding="utf-8"))}
    corpus = Corpus(data / "derived/corpus/index.sqlite")
    hint = hints(item_rows, corpus)

    def record(lid: str) -> dict:
        rs = sorted(by_lineage[lid], key=lambda r: r["as_of"])
        t, first = rs[0]["target"], hint[rs[0]["id"]]
        actors = {}
        for r in rs:
            for a in evidence[r["id"]]["actors"]:
                actors.setdefault((a["document"], a["op"]), a)
        return {"item": lid, "nhom": stratum(rs[0]), "van_ban": t["law_id"], "dieu_khoan": t["citation"],
                "vi_tri": t["provision_path"], "cau_dan": t.get("lead_in"), "source_url": rs[0].get("source_url"),
                "cac_moc": [{"as_of": r["as_of"], "co_dap_an": r["answer"] is not None} for r in rs],
                "loi_van": [{**v, "text": (v["text"] or "")[:TEXT_MAX]} for v in versions_of(corpus, lid)],
                "cac_phien_ban": first["cac_phien_ban"].replace("   ◀ đáp án của dòng này", ""),
                "goi_y_cho_moi": first["goi_y_cho_moi"],
                "van_ban_goc": evidence[rs[0]["id"]]["base"],
                "van_ban_tac_dong": list(actors.values())}

    for n in range(0, len(items), PACK):
        with (out / f"pack_{n // PACK + 1:02d}.jsonl").open("w", encoding="utf-8") as f:
            for lid in items[n:n + PACK]:
                f.write(json.dumps(record(lid), ensure_ascii=False) + "\n")
    key = work / "key_loc.tsv"
    with key.open("w", encoding="utf-8") as f:
        f.write("item\tnhom\tvai_tro\tsu_that\tma\n")
        for lid in items:
            role, (fact, codes) = ("hieu_chuan", truth[lid]) if lid in truth else ("ung_vien", ("", []))
            f.write(f"{lid}\t{stratum(by_lineage[lid][0])}\t{role}\t{fact}\t{','.join(codes)}\n")
    calib = collections.Counter((stratum(by_lineage[l][0]), truth[l][0]) for l in truth)
    print(f"{len(items)} mục ({len(truth)} hiệu chuẩn, {len(picked)} ứng viên) -> {-(-len(items) // PACK)} gói ở {out}")
    print("  hiệu chuẩn:", dict(sorted(calib.items())))
    print("  ứng viên:", {s: min(n, len(pool[s])) for s, n in QUOTA.items()}, "· kho còn:",
          {s: len(v) for s, v in sorted(pool.items())})
    print(f"  khóa: {key}")


def score(out: Path, result: Path, key_path: Path | None = None) -> bool:
    key = read_tsv(key_path or out.parent.parent / "key_loc.tsv")
    got = read_tsv(result)
    strange = sorted(set(got) - set(key))
    missing = sorted(set(key) - set(got))
    print(f"quyết định {len(got)} mục; thiếu {len(missing)}; mục lạ {len(strange)}")
    calib = [i for i in key if key[i]["vai_tro"] == "hieu_chuan" and i in got]
    ok = True
    for name in ("toàn tập", *QUOTA):
        sel = [i for i in calib if name == "toàn tập" or key[i]["nhom"] == name]
        bad = [i for i in sel if key[i]["su_that"] == "xau"]
        good = [i for i in sel if key[i]["su_that"] == "tot"]
        caught = sum(got[i]["quyet_dinh"] == "loai" for i in bad) / len(bad) if bad else None
        wrong = sum(got[i]["quyet_dinh"] == "loai" for i in good) / len(good) if good else None
        fmt = lambda x: "-" if x is None else f"{x:.2f}"
        print(f"  {name:13} xấu {len(bad):3} loại đúng {fmt(caught)} · tốt {len(good):3} loại nhầm {fmt(wrong)}")
        if name == "toàn tập":
            ok = (caught or 0) >= CATCH_MIN and (wrong if wrong is not None else 1) <= FALSE_REJECT_MAX
    kept = collections.Counter(key[i]["nhom"] for i in got if key.get(i, {}).get("vai_tro") == "ung_vien"
                               and got[i]["quyet_dinh"] == "giu")
    print("  ứng viên được giữ:", dict(sorted(kept.items())))
    print(f"ngưỡng loại đúng >= {CATCH_MIN} và loại nhầm <= {FALSE_REJECT_MAX} ->", "ĐẠT" if ok else "CHƯA ĐẠT")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "score"))
    ap.add_argument("result", nargs="?", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--key", type=Path, help="khóa cho score; mặc định OUT/../../key_loc.tsv")
    args = ap.parse_intermixed_args()
    build(args.out, args.data) if args.cmd == "build" else score(args.out, args.result, args.key)
