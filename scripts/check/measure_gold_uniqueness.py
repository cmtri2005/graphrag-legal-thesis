#!/usr/bin/env python3
"""Đáp án vàng có duy nhất không — rủi ro mà ADR 0003 tự gọi là lớn nhất của Gói C.

Bộ lọc C2 của `generate_questions.py` bắt được câu hỏi rò rỉ đáp án, nhưng
không bắt được **câu hỏi đúng dạng mà gold không duy nhất**: một điều khoản
khác trong corpus cũng trả lời đúng câu hỏi đó. Đọc một dòng không thấy được;
phải tìm trên toàn corpus. Giờ có index BM25 nên đo được.

Cách đo, cho mỗi dòng trả lời được của bảng chính:

1. Truy xuất top-k đơn vị **có hiệu lực tại `as_of`** (tier `propagated`, lớp B),
   nên mọi ứng viên đều là quy định đang áp dụng tại mốc đó — không phải phiên
   bản cũ.
2. Giữ các ứng viên thuộc điều khoản KHÁC điều khoản vàng.
3. Dùng đúng phép thử của scorer (`contains`) xem lời văn ứng viên có chứa đủ
   mọi cụm của `short_answer` hay không.

Một ứng viên như vậy nghĩa là có điều khoản khác cũng đáp đúng câu hỏi, nên
`Recall@1` và `Accuracy` đang phạt hệ thống vì một đáp án có thể chấp nhận
được. Đây là ứng viên để người rà, không phải phán quyết: hai điều khoản có
thể trùng lời văn mà câu hỏi vẫn chỉ nhắm một chỗ (ví dụ cùng một quy định
được nhắc ở hai văn bản).

Dùng đúng `k` của cấu hình eval nên cache truy xuất hâm nóng luôn cho lần chạy
eval thật.

Usage:
    python scripts/check/measure_gold_uniqueness.py --limit 200
    python scripts/check/measure_gold_uniqueness.py            # cả bảng chính
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

from vilexgraph.framework.corpus import Corpus  # noqa: E402
from vilexgraph.framework.retrieve import RetrievalCache, searcher  # noqa: E402
from vilexgraph.framework.systems import REGISTRY  # noqa: E402
from score_vilextime import contains  # noqa: E402  đúng phép thử mà metric dùng


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--index", type=Path, default=Path("data/derived/corpus/index.sqlite"))
    ap.add_argument("--strategy", default="giua_khoang")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", type=Path,
                    default=Path("data/derived/vilextime/gold_uniqueness.json"))
    args = ap.parse_args()

    rows = [r for r in map(json.loads,
                           (args.data / "derived/vilextime/release.jsonl").open(encoding="utf-8"))
            if r["as_of_strategy"] == args.strategy and r["answerable"] and r["short_answer"]]
    if args.limit:
        rows = rows[:args.limit]

    corpus = Corpus(args.index)
    spec = REGISTRY["proposed"].variant("proposed-lex", dense=False, rerank=False,
                                        expand=0, expand_edges="none")
    search = searcher(corpus, spec, RetrievalCache(args.data / "derived/rag/retrieval.sqlite"))

    findings, per_group = [], collections.Counter()
    checked = collections.Counter()
    started = time.monotonic()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    for n, row in enumerate(rows, 1):
        checked[row["group"]] += 1
        hits = search(row["question"], row["as_of"])
        others = [u for u in corpus.units([h.unit_id for h in hits])
                  if u.provision_id != row["lineage_id"]]
        alt = [u for u in others if contains(u.text, row["short_answer"])]
        if alt:
            per_group[row["group"]] += 1
            findings.append({"id": row["id"], "group": row["group"],
                             "lineage_id": row["lineage_id"],
                             "short_answer": row["short_answer"][:200],
                             "also_answered_by": [
                                 {"unit_id": u.unit_id, "provision_id": u.provision_id,
                                  "document_id": u.document_id, "level": u.level,
                                  "text": u.text[:220]} for u in alt[:3]],
                             "n_alternatives": len(alt)})
        if n % 25 == 0 or n == len(rows):
            rate = n / max(time.monotonic() - started, 1e-9)
            args.out.write_text(json.dumps(
                {"progress": f"{n}/{len(rows)}", "rows_per_s": round(rate, 2),
                 "k": spec.k, "tier": spec.temporal, "layer": spec.layer,
                 "strategy": args.strategy,
                 "checked_by_group": dict(checked),
                 "non_unique_by_group": dict(per_group),
                 "non_unique_total": len(findings),
                 "non_unique_rate": round(len(findings) / n, 4),
                 "findings": findings}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {n}/{len(rows)} · {rate:.2f} dòng/s · gold không duy nhất "
                  f"{len(findings)} ({100*len(findings)/n:.1f}%)", flush=True)

    print(f"\n{args.out}")
    print(f"  {len(findings)}/{len(rows)} dòng có điều khoản khác cũng đáp đúng "
          f"({100*len(findings)/max(len(rows),1):.1f}%)")
    print(f"  theo nhóm: {dict(sorted(per_group.items()))}")
    print("  -> hàng đợi để người rà; không phải phán quyết tự động")


if __name__ == "__main__":
    main()
