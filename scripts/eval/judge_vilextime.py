#!/usr/bin/env python3
"""LLM-as-judge for ViLexTime answers, and its calibration against a human (plan P5.6).

The scorer's Accuracy is a span-containment test. It is exact and free, but it
cannot tell a model that *chose* a version from one that recited several and let
the gold span be somewhere among them (JUDGE C2). A judge reads the whole answer
and decides. It is only worth reporting once it has been shown to agree with a
person, so calibration is part of this tool, not a separate project.

    judge    prediction file  -> judgments.jsonl + a summary
    sample   release rows     -> a TSV for a person to label (default 100)
    agree    judgments + the filled TSV -> Cohen κ and hedge recall

**The judge never decides `answerable`.** For a row whose gold is "this unit is
not in force", the verdict is the scorer's rule (the system said so, or it did
not) and costs no call; the judge reads only rows with a gold answer and a
non-empty prediction. A recited-all-versions answer is marked `hedged` and is
never `correct`, whatever it contains — that is the probe the scorer's `hedge`
checks, and the judge has to catch it.

**Use a judge outside the Claude family** for the same reason as the generator
(ADR 0004 §3): the gold was written by a Claude model.

Usage:
    python scripts/eval/judge_vilextime.py judge preds.jsonl --split dev
    python scripts/eval/judge_vilextime.py sample --out data/review/judge_sample.tsv
    python scripts/eval/judge_vilextime.py agree judgments.jsonl data/review/judge_sample.tsv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "review"))

from vilexgraph import llm  # noqa: E402

RELEASE = Path("data/derived/vilextime/release.jsonl")
CACHE = Path("data/derived/rag/judgments.sqlite")
SEED = 20261002

SYSTEM = """Bạn chấm câu trả lời về pháp luật Việt Nam theo một đáp án chuẩn. Câu hỏi hỏi về \
quy định TẠI MỘT MỐC THỜI GIAN.

ĐÚNG: có — khi câu trả lời nêu đúng nội dung quy định theo đáp án chuẩn về ý chính (mức, \
số liệu, chủ thể, thời hạn, điều kiện), dù diễn đạt khác.
ĐÚNG: không — khi sai, thiếu ý chính, hoặc nêu quy định của phiên bản khác.
RÀO ĐÓN: có — khi câu trả lời liệt kê nhiều phiên bản hoặc nhiều khả năng ("trước ngày X thì \
..., sau đó thì ...") thay vì chọn một. Câu trả lời rào đón luôn bị ĐÚNG: không, kể cả khi \
trong đó có đáp án chuẩn.

Trả lời đúng hai dòng:
ĐÚNG: có|không
RÀO ĐÓN: có|không"""

_RIGHT = re.compile(r"^\s*ĐÚNG\s*:\s*(\S+)", re.IGNORECASE | re.MULTILINE)
_HEDGE = re.compile(r"^\s*RÀO\s*ĐÓN\s*:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def prompt(row: dict, pred: dict) -> str:
    return (f"MỐC THỜI GIAN: {row['as_of']}\nCÂU HỎI: {row['question']}\n\n"
            f"ĐÁP ÁN CHUẨN (cụm bắt buộc): {row.get('short_answer') or ''}\n"
            f"ĐÁP ÁN CHUẨN (toàn văn): {row['answer']}\n\n"
            f"CÂU TRẢ LỜI CẦN CHẤM: {pred['answer']}")


def parse(raw: str) -> tuple[bool, bool]:
    """(correct, hedged). Anything unreadable is wrong and not hedged: the judge
    must not award a point it did not clearly give."""
    right, hedge = _RIGHT.search(raw), _HEDGE.search(raw)
    hedged = bool(hedge and hedge.group(1).lower().startswith("có"))
    correct = bool(right and right.group(1).lower().startswith("có")) and not hedged
    return correct, hedged


class Cache:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS j (key TEXT PRIMARY KEY, raw TEXT)")

    def get(self, key: str):
        row = self.db.execute("SELECT raw FROM j WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def put(self, key: str, raw: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO j VALUES (?,?)", (key, raw))
        self.db.commit()


def judge_one(row: dict, pred: dict, cache: Cache, provider, model) -> dict:
    """One verdict. The scorer's rule decides unanswerable rows; the judge reads the rest."""
    if row.get("answerable") is False:
        said_expired = pred.get("answerable") is False
        return {"id": row["id"], "correct": said_expired, "hedged": False, "by": "rule"}
    if pred.get("answerable") is False or not (pred.get("answer") or "").strip():
        return {"id": row["id"], "correct": False, "hedged": False, "by": "rule"}
    user = prompt(row, pred)
    key = hashlib.sha256(json.dumps([SYSTEM, user, provider, model]).encode()).hexdigest()
    raw = cache.get(key)
    if raw is None:
        raw = llm.complete(SYSTEM, user, provider=provider, model=model).text
        cache.put(key, raw)
    correct, hedged = parse(raw)
    return {"id": row["id"], "correct": correct, "hedged": hedged, "by": "judge", "raw": raw}


def cmd_judge(args) -> None:
    rows = {r["id"]: r for r in read(args.release)
            if args.split is None or r.get("split") == args.split}
    preds = {p["id"]: p for p in read(args.preds) if p["id"] in rows}
    cache, out, groups = Cache(args.cache), [], {}
    for n, (i, pred) in enumerate(preds.items(), 1):
        out.append(judge_one(rows[i], pred, cache, args.provider, args.model))
        groups.setdefault(rows[i]["group"], []).append(out[-1]["correct"])
        if n % 50 == 0:
            print(f"  {n}/{len(preds)}", file=sys.stderr)
    args.out.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out),
                        encoding="utf-8")
    print(f"{len(out)} judged · accuracy {sum(o['correct'] for o in out) / max(len(out), 1):.3f}"
          f" · hedged {sum(o['hedged'] for o in out)}")
    for g in sorted(groups):
        print(f"  {g}: {sum(groups[g]) / len(groups[g]):.3f} (n={len(groups[g])})")


def cmd_sample(args) -> None:
    """A stratified sample of predictions for a person to label `dung|sai`."""
    rows = {r["id"]: r for r in read(args.release)
            if args.split is None or r.get("split") == args.split}
    preds = [p for p in read(args.preds) if p["id"] in rows and rows[p["id"]]["answerable"]
             and (p.get("answer") or "").strip()]
    random.Random(SEED).shuffle(preds)
    with args.out.open("w", encoding="utf-8", newline="") as sink:
        w = csv.writer(sink, delimiter="\t")
        w.writerow(["id", "as_of", "question", "gold_short", "gold", "prediction", "human"])
        for p in preds[:args.n]:
            r = rows[p["id"]]
            w.writerow([r["id"], r["as_of"], r["question"], r.get("short_answer") or "",
                        r["answer"], p["answer"], ""])
    print(f"{min(args.n, len(preds))} rows -> {args.out}; fill `human` with dung|sai|raodon")


def cmd_agree(args) -> None:
    from crosscheck import cohen_kappa
    judged = {j["id"]: j for j in read(args.judgments)}
    human = {r["id"]: r["human"].strip() for r in csv.DictReader(args.labels.open(encoding="utf-8"),
                                                                  delimiter="\t")
             if r["human"].strip()}
    ids = [i for i in human if i in judged]
    mine = ["dung" if judged[i]["correct"] else "sai" for i in ids]
    theirs = ["dung" if human[i] == "dung" else "sai" for i in ids]
    hedged = [i for i in ids if human[i] == "raodon"]
    print(f"{len(ids)} rows labelled by a person")
    print(f"  agreement {sum(a == b for a, b in zip(mine, theirs)) / max(len(ids), 1):.3f}"
          f" · Cohen κ {cohen_kappa(mine, theirs)}")
    print(f"  hedge recall {sum(judged[i]['hedged'] for i in hedged)}/{len(hedged)}"
          " (P5.6 requires the judge to catch hedged answers)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("judge", cmd_judge), ("sample", cmd_sample)):
        p = sub.add_parser(name)
        p.add_argument("preds", type=Path) if name == "judge" else p.add_argument("--preds", type=Path, required=True)
        p.add_argument("--release", type=Path, default=RELEASE)
        p.add_argument("--split")
        p.set_defaults(fn=fn)
        if name == "judge":
            p.add_argument("--out", type=Path, default=Path("judgments.jsonl"))
            p.add_argument("--cache", type=Path, default=CACHE)
            p.add_argument("--provider")
            p.add_argument("--model")
        else:
            p.add_argument("--out", type=Path, default=Path("data/review/judge_sample.tsv"))
            p.add_argument("-n", type=int, default=100)
    p = sub.add_parser("agree")
    p.add_argument("judgments", type=Path)
    p.add_argument("labels", type=Path)
    p.set_defaults(fn=cmd_agree)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
