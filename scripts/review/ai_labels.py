"""AI–AI research labels for ViLexTime: lock raw agent replies, then measure agreement.

These are `label_origin=ai`, `not_verified` labels from legal-annotator-a/b. They are never
written to the human A/B sheets and never count as human agreement (guideline 4.0 §5–§6).

    python scripts/review/ai_labels.py lock --run DIR      # DIR/raw/{a,b}_chunkN.md -> DIR/{a,b}.jsonl (once)
    python scripts/review/ai_labels.py measure --run DIR   # -> DIR/metrics.json
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
from test2_labels import GOOD, GUIDELINE, MIN_NEGATIVES, OPTIONS, validate_label, worksheet_sha256  # noqa: E402

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


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("lock", "measure"))
    p.add_argument("--run", type=Path, required=True)
    args = p.parse_args()
    if args.action == "lock":
        lock(args.run)
    else:
        r = measure(args.run)
        for q, m in r["metrics"].items():
            print(q, {k: m[k] for k in ("n", "ac1", "kappa", "p_neg", "adverse_labels", "gate")})
        print("coverage", {k: v for k, v in r["coverage"].items() if k != "rejected"},
              {w: len(v) for w, v in r["coverage"]["rejected"].items()})


if __name__ == "__main__":
    main()
