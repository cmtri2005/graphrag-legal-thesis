#!/usr/bin/env python3
"""Phân tích hậu nghiệm G4 (docs/plans/active/REFACTOR_PLAN.md, nhóm 2). THĂM DÒ, sau khi đã thấy test.

Chỉ đọc dự đoán đã lưu; không gọi model, không đổi scorer. Không thay phán quyết F1–F7 của ADR 0006.
Hiệu ghép cặp dùng đúng `confirm_vilextime.run` (bootstrap theo lineage, ADR 0006 §5).

    PYTHONPATH=src .venv/bin/python scripts/eval/posthoc_g4.py --g4 runs/final_g4_20261112 \\
        --release data/vilextime_final/vilextime.jsonl --data data/vilextime_final/internal \\
        --extra-retrieval runs/posthoc_g4_20261113/retrieval --out runs/posthoc_g4_20261113/attribution.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confirm_vilextime as cv  # noqa: E402
import score_vilextime as sv  # noqa: E402
from t6_breakdown import event_rank  # noqa: E402

RUNS = ("r1", "r2")
# (a, b, slice): Accuracy của b − a. Nửa đầu là câu hỏi quy kết; nửa sau là bảng mô tả của results.md.
PAIRS = (
    ("b7plus", "proposed2", "all"), ("b7pp", "proposed2", "all"), ("b7plus", "b7pp", "all"),
    ("b7pp", "proposed2", "t6_unanswerable"), ("b7plus", "proposed2", "t6_unanswerable"),
    ("b7plus", "b7pp", "t6_ancestor"), ("b7plus", "proposed2", "t6_ancestor"),
    ("b7", "b7plus", "gold_v1"), ("b7", "b7plus", "gold_v2plus"), ("b4", "proposed2", "all"),
    ("b1", "b2ctx", "all"), ("b2ctx", "b3", "all"), ("b3", "b4", "all"), ("b4", "b5", "all"), ("b5", "b6", "all"),
    ("b4", "b6", "all"), ("b6", "b7", "all"), ("b4", "b7", "all"), ("b7", "b7plus", "all"),
    ("b7pp", "oracle", "all"), ("oracle", "oracle_now", "all"), ("b4", "oracle_now", "all"),
)
LADDER = (("F4", "b2ctx", "b7"), ("PH-b7v-b7", "b7", "b7v"), ("PH-b7plus-b7v", "b7v", "b7plus"),
          ("F5", "b7", "b7plus"), ("PH-b7pp-b7plus", "b7plus", "b7pp"))   # F4, F5: cùng seed với confirm.json
BY_DOCUMENT = (("b7plus", "proposed2"), ("b7", "b7plus"), ("b4", "proposed2"))
RANKED = ("b4", "b7", "b7plus", "b7pp", "proposed2")


def read(path: Path) -> dict[str, dict]:
    return {p["id"]: p for p in map(json.loads, path.open(encoding="utf-8"))}


def call(result: dict) -> str:
    """Kết luận thô của một hiệu: '+' KTC trên 0, '-' KTC dưới 0, '0' KTC chứa 0."""
    lo, hi = result["ci95"]
    return "+" if lo > 0 else "-" if hi < 0 else "0"


def gold_rank(row: dict, pred: dict) -> int | None:
    """Hạng (từ 1) của căn cứ đúng phiên bản trong danh sách đưa vào prompt; None nếu không có."""
    accepted = set(row["accepted_evidence"])
    return next((i for i, u in enumerate(pred.get("retrieved") or [], 1)
                 if u in accepted or (row["version_id"] and u == row["version_id"])), None)


def bucket(rank: int | None) -> str:
    return ("không có" if rank is None else "1" if rank == 1 else "2-5" if rank <= 5 else
            "6-10" if rank <= 10 else "11-20" if rank <= 20 else ">20")


def repeal_claims(rows: list[dict], preds: dict[str, dict]) -> dict:
    """Khẳng định 'HIỆU LỰC: không': đúng trên dòng không đáp án, sai trên dòng có đáp án (ADR 0006 §4)."""
    said = [r for r in rows if preds[r["id"]].get("answerable") is False]
    gone = [r for r in rows if not r["answerable"]]
    tp = sum(not r["answerable"] for r in said)
    shown = [r for r in gone if event_rank(r, preds[r["id"]].get("retrieved") or [])]
    ok = lambda xs: sum(sv.correct(r, preds[r["id"]]) for r in xs)  # noqa: E731
    return {"claims": len(said), "true": tp, "false": len(said) - tp,
            "precision": tp / len(said) if said else None, "precision_wilson95": cv.wilson(tp, len(said)),
            "recall": tp / len(gone) if gone else None, "recall_wilson95": cv.wilson(tp, len(gone)),
            "unanswerable_rows": len(gone), "repeal_in_prompt": len(shown), "correct_given_in_prompt": ok(shown),
            "correct_given_absent": ok([r for r in gone if r not in shown])}


def writer(meta: dict) -> str:
    model = ((meta.get("question_source") or {}).get("model") or "?").lower()
    return next((name for name, keys in (("codex", ("gpt", "codex")), ("claude", ("claude",)), ("deepseek", ("deepseek",)))
                 if any(k in model for k in keys)), model)


def strata(rows: list[dict], gen: dict[str, dict], key) -> dict:
    groups = collections.defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    return {name: {"rows": len(cut), "lineages": len({r["lineage_id"] for r in cut}),
                   "accuracy": {s: sum(sv.correct(r, p[r["id"]]) for r in cut) / len(cut) for s, p in gen.items()}}
            for name, cut in sorted(groups.items(), key=lambda kv: -len(kv[1]))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--g4", type=Path, required=True)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--extra-retrieval", type=Path, help="thư mục có b7v.jsonl chạy sau G4")
    ap.add_argument("--draws", type=int, default=10_000)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    release = sv.load_rows(args.release)
    extra = sv.distractors(release)
    rows = [{**r, "_distractors": extra.get(r["id"], [])} for r in release
            if r.get("split") == "test" and r["as_of_strategy"] == "giua_khoang"]
    meta = read(args.release.with_name("vilextime_meta.jsonl"))
    cv.SLICES.update(cv.FINAL_SLICES)
    cv.SLICES["gold_v1"] = lambda r: cv.SLICES["all_answerable"](r) and sv.ordinal(r["version_id"]) == 1
    cv.SLICES["gold_v2plus"] = lambda r: cv.SLICES["all_answerable"](r) and sv.ordinal(r["version_id"]) > 1
    main_rows = [r for r in rows if cv.SLICES["all"](r)]

    files = {f"{t}/{p.stem}": p for t in RUNS for p in sorted((args.g4 / t / "test").glob("*.jsonl"))
             if not p.name.endswith(".sample.jsonl")}
    files.update({f"retrieval/{p.stem}": p for d in (args.g4 / "retrieval", args.extra_retrieval) if d
                  for p in sorted(d.glob("*.jsonl"))})
    preds = {k: read(p) for k, p in files.items()}
    gen = {t: {k.split("/")[1]: v for k, v in preds.items() if k.startswith(t + "/")} for t in RUNS}
    ret = {k.split("/")[1]: v for k, v in preds.items() if k.startswith("retrieval/")}
    units = sv.units_of(args.data, preds)[0]

    # tự kiểm: Accuracy tính lại phải khớp all.score.json của từng lần
    for t in RUNS:
        official = json.loads((args.g4 / t / "test" / "all.score.json").read_text(encoding="utf-8"))
        for s, p in gen[t].items():
            mine = sum(sv.correct(r, p[r["id"]]) for r in main_rows) / len(main_rows)
            assert abs(mine - official[s]["giua_khoang"]["all"]["accuracy"]) < 1e-9, (t, s, mine)

    def paired(name, a, b, metric, where, source, data=rows):
        return cv.run((name, "", "paired", metric, (where,), "", (a, b), +1), data, source, units, args.draws)

    out: dict = {"note": "THĂM DÒ hậu nghiệm, sau khi đã thấy test; không đổi phán quyết F1-F7 (ADR 0006).",
                 "draws": args.draws, "rows": len(main_rows),
                 "files": {k: {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                           for k, p in files.items()},
                 "pairs": [], "by_document": [], "ladder": [], "rank_accuracy": {}, "repeal_claims": {}, "strata": {}}

    for a, b, where in PAIRS:
        per_run = {t: paired(f"PH-{b}-{a}", a, b, "accuracy", where, gen[t]) for t in RUNS}
        calls = [call(per_run[t]) for t in RUNS]
        out["pairs"].append({"comparison": f"{b} − {a}", "metric": "accuracy", "slice": where, **per_run,
                             "calls": calls, "stable": calls[0] == calls[1], "sign_flip": set(calls) == {"+", "-"}})

    # ponytail: gộp cụm theo văn bản bằng cách đổi lineage_id của bản sao; chỉ đúng cho Accuracy
    # (Recall/VCR/TCS đọc lineage_id). Cần chỉ số khác thì thêm tham số cụm vào score_vilextime.bootstrap.
    by_doc = [{**r, "lineage_id": meta[r["id"]]["target"]["document_id"]} for r in rows]
    for a, b in BY_DOCUMENT:
        out["by_document"].append({"comparison": f"{b} − {a}", "slice": "all", "documents": len({r["lineage_id"] for r in by_doc if cv.SLICES["all"](r)}),
                                   **{t: paired(f"PH-{b}-{a}", a, b, "accuracy", "all", gen[t], by_doc) for t in RUNS}})

    for name, a, b in LADDER:
        if a in ret and b in ret:
            out["ladder"].append({"test": name, "comparison": f"{b} − {a}", "slice": "all_answerable",
                                  **{m: paired(name, a, b, m, "all_answerable", ret) for m in ("tv_recall@1", "recall@1")}})

    answerable = [r for r in main_rows if r["answerable"]]
    for t in RUNS:
        out["rank_accuracy"][t] = {}
        for s in RANKED:
            cells = collections.defaultdict(lambda: [0, 0])
            for r in answerable:
                cell = cells[bucket(gold_rank(r, gen[t][s][r["id"]]))]
                cell[0] += sv.correct(r, gen[t][s][r["id"]])
                cell[1] += 1
            out["rank_accuracy"][t][s] = dict(cells)
        out["repeal_claims"][t] = {s: repeal_claims(main_rows, p) for s, p in gen[t].items()}
        out["strata"][t] = {"question_writer": strata(main_rows, gen[t], lambda r: writer(meta[r["id"]])),
                            "domain": strata(main_rows, gen[t], lambda r: "+".join(meta[r["id"]].get("domain") or ["?"])),
                            "group_answerable": strata(main_rows, gen[t], lambda r: f"{r['group']}/{'có' if r['answerable'] else 'không'} đáp án")}

    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for row in out["pairs"]:
        e = lambda t: f"{row[t]['estimate']:+.3f} [{row[t]['ci95'][0]:+.3f}; {row[t]['ci95'][1]:+.3f}]"  # noqa: E731
        flag = "" if row["stable"] else " ĐỔI DẤU" if row["sign_flip"] else " không ổn định"
        print(f"{row['comparison']} · {row['slice']}: lần 1 {e('r1')} · lần 2 {e('r2')}{flag}")
    for row in out["ladder"]:
        r = row["tv_recall@1"]
        print(f"{row['test']} {row['comparison']} · tv_recall@1: {r['estimate']:+.3f} [{r['ci95'][0]:+.3f}; {r['ci95'][1]:+.3f}]")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
