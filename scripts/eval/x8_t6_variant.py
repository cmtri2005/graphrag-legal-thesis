#!/usr/bin/env python3
"""X8 mở rộng (chẩn đoán, chỉ dev, dùng gold): dựng prompt C0/C1 cho 21 dòng T6 KHÔNG đáp án.

C0 = prompt proposed2 giữ nguyên (dựng lại từ ids, phải khớp từng byte `user` cũ).
C1 = như C0 nhưng lệnh bãi bỏ gold (accepted_evidence) ở vị trí 1, đánh số lại; system không đổi.

    python scripts/eval/x8_t6_variant.py [--run runs/rebuild_20261110_dev] [--out runs/x8_t6_dev_20261111]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from colab_b1 import digest  # noqa: E402
from run_vilextime import INDEX  # noqa: E402
from vilexgraph.framework import generate  # noqa: E402
from vilexgraph.framework.corpus import Corpus  # noqa: E402

REL = Path("data/vilextime_dataset_h6/vilextime.jsonl")


def jl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def promote(ids: list[str], ev: str) -> list[str]:
    """Event first, rest in original order (move if present, insert if absent)."""
    return [ev] + [u for u in ids if u != ev]


def build(prompt: dict, ids: list[str], corpus: Corpus) -> dict:
    units = corpus.units(ids)
    assert [u.unit_id for u in units] == ids, "unit missing from corpus"
    system, user, out_ids = generate.build_prompt(
        _question(prompt["user"]), prompt["as_of"], units, with_context=True)
    row = {**prompt, "system": system, "user": user, "ids": out_ids, "retrieved": out_ids}
    row["prompt_sha256"] = digest(row)
    return row


def _question(user: str) -> str:
    return user.split("CÂU HỎI: ", 1)[1].split("\n\nCÁC ĐOẠN CĂN CỨ:", 1)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/rebuild_20261110_dev")
    ap.add_argument("--out", default="runs/x8_t6_dev_20261111")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    gold = {r["id"]: r for r in jl(REL)
            if r["group"] == "T6" and r["split"] == "dev" and r["as_of_strategy"] == "giua_khoang" and not r["answerable"]}
    assert len(gold) == 21, len(gold)
    old = {p["id"]: p for p in jl(f"{a.run}/prompts/proposed2.jsonl")}
    corpus = Corpus(INDEX)
    c0, c1, log = [], [], []
    for i, r in gold.items():
        p, ev = old[i], r["accepted_evidence"][0]
        row0 = build(p, p["ids"], corpus)
        assert row0["user"] == p["user"] and row0["system"] == p["system"], f"C0 không khớp byte: {i}"
        action = "chuyen" if ev in p["ids"] else "chen"
        row1 = build(p, promote(p["ids"], ev), corpus)
        assert row1["system"] == p["system"] and row1["ids"][0] == ev
        c0.append(row0)
        c1.append(row1)
        log.append({"id": i, "event": ev, "action": action, "old_rank": p["ids"].index(ev) + 1 if ev in p["ids"] else None,
                    "n_ids_old": len(p["ids"]), "n_ids_c1": len(row1["ids"])})
    for name, rows in (("C0", c0), ("C1", c1)):
        (out / f"prompts_{name}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    rec = json.loads(Path(f"{a.run}/prompts/proposed2.export.json").read_text(encoding="utf-8"))
    for name in ("C0", "C1"):  # import reads this record: row count and file hash
        f = out / f"prompts_{name}.jsonl"
        new = {**rec, "rows": 21, "prompt_file_sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
               "note": f"X8 mở rộng {name}: 21 dòng T6 không đáp án dev, chẩn đoán dùng gold"}
        f.with_suffix(".export.json").write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "c1_changes.json").write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print({k: sum(x["action"] == k for x in log) for k in ("chuyen", "chen")})


if __name__ == "__main__":
    main()
