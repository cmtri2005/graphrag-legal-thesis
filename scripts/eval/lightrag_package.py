#!/usr/bin/env python3
"""LightRAG thật làm baseline "GraphRAG phi thời gian" (REFACTOR_PLAN 3.3). Gói cho Colab và đường về.

Kho: lời văn gốc (lớp A, chỉ đơn vị điều khoản, theo thứ tự đọc) của văn bản mà dev và bộ cuối hỏi tới,
cộng văn bản ban hành lệnh sửa đổi/bãi bỏ nhắm vào chúng. Không có thông tin thời gian: đúng vai baseline.
Truy xuất do LightRAG (Colab, `colab_upload/lightrag/lightrag_colab.py`); câu trả lời sinh bằng ĐÚNG prompt
và generator của các hệ khác, nên chỉ cách truy xuất khác. LightRAG trả đoạn văn, không trả mã đơn vị, nên
các chỉ số dựa trên trích dẫn (TVER, phủ trích dẫn, VCR) không xác định.

    python scripts/eval/lightrag_package.py corpus  --out colab_upload/lightrag/corpus.jsonl
    python scripts/eval/lightrag_package.py queries --out colab_upload/lightrag/queries.jsonl
    python scripts/eval/lightrag_package.py prompts --contexts <contexts.jsonl> --split dev --out <dir>/lightrag.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import colab_b1  # noqa: E402
from vilexgraph.framework import generate  # noqa: E402

NAME = "lightrag"
CONTEXT_ID = "lightrag:context"     # the one evidence block; not a corpus unit, so citations stay unresolved
INDEX = Path("data/derived/corpus/index.sqlite")
RELEASES = {"dev": Path("data/vilextime_dataset_h6/vilextime.jsonl"),
            "test": Path("data/vilextime_final/vilextime.jsonl")}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows_of(split: str) -> list[dict]:
    rows = [json.loads(line) for line in RELEASES[split].open(encoding="utf-8")]
    return [r for r in rows if r.get("split") == split and r["as_of_strategy"] == "giua_khoang"]


def target_documents() -> set[str]:
    docs = set()
    for split, release in RELEASES.items():
        keep = {r["id"] for r in rows_of(split)}
        for line in release.with_name("vilextime_meta.jsonl").open(encoding="utf-8"):
            meta = json.loads(line)
            if meta["id"] in keep:
                docs.add(meta["target"]["document_id"])
    return docs


def corpus(args) -> None:
    db = sqlite3.connect(f"file:{args.index}?mode=ro", uri=True)
    targets = sorted(target_documents())
    marks = ",".join("?" * len(targets))
    acting = {d for (d,) in db.execute(
        "SELECT DISTINCT u.document_id FROM units u WHERE u.kind='instruction' AND u.provision_id IN "
        f"(SELECT provision_id FROM units WHERE layer='asis' AND kind='provision' AND document_id IN ({marks}))",
        targets)}
    out, chars = [], 0
    for doc in sorted(set(targets) | acting):
        title = db.execute("SELECT title FROM documents WHERE document_id=?", (doc,)).fetchone()
        body = "\n".join(t for (t,) in db.execute(
            "SELECT text FROM units WHERE layer='asis' AND kind='provision' AND document_id=? ORDER BY rowid", (doc,)) if t)
        if not body:
            continue
        text = f"{(title[0] if title else doc).strip()}\n{body}"
        chars += len(text)
        out.append({"id": doc, "role": "target" if doc in targets else "acting", "text": text})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in out), encoding="utf-8")
    print(f"{args.out}: {len(out)} văn bản ({sum(d['role'] == 'target' for d in out)} đích, "
          f"{sum(d['role'] == 'acting' for d in out)} văn bản tác động), {chars:,} ký tự; sha256 {sha(args.out)}")


def queries(args) -> None:
    out = [{"id": r["id"], "split": split, "as_of": r["as_of"], "question": r["question"],
            "query": f"Mốc thời gian: {r['as_of']}. {r['question']}"}
           for split in ("dev", "test") for r in rows_of(split)]
    args.out.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in out), encoding="utf-8")
    print(f"{args.out}: {len(out)} truy vấn; sha256 {sha(args.out)}")


def prompts(args) -> None:
    """Contexts from Colab -> the scorer's prompt file, through the shared `generate.build_prompt`."""
    contexts = {c["id"]: c for c in map(json.loads, args.contexts.open(encoding="utf-8"))}
    rows = rows_of(args.split)
    missing = [r["id"] for r in rows if r["id"] not in contexts]
    if missing:
        raise SystemExit(f"{len(missing)} {args.split} rows have no LightRAG context, e.g. {missing[:3]}")

    class Block:      # duck-types corpus.Unit for build_prompt
        def __init__(self, text):
            self.unit_id, self.text = CONTEXT_ID, text

        def retrieval_text(self, with_context):
            return self.text

    out = []
    for r in rows:
        context = (contexts[r["id"]].get("context") or "").strip()
        units = [Block(context)] if context else []
        system, user, ids = generate.build_prompt(r["question"], r["as_of"], units, with_context=True)
        row = {"id": r["id"], "system": system, "user": user, "ids": ids, "retrieved": [],
               "system_name": NAME, "split": args.split, "as_of": r["as_of"], "signals": {}}
        row["prompt_sha256"] = colab_b1.digest(row)
        out.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    record = {"system": NAME, "spec": None, "split": args.split, "as_of_strategy": "giua_khoang", "rows": len(out),
              "release_sha256": sha(RELEASES[args.split]), "contexts_sha256": sha(args.contexts),
              "empty_contexts": sum(not o["ids"] for o in out), "prompt_file_sha256": sha(args.out)}
    args.out.with_suffix(".export.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                                    encoding="utf-8")
    print(f"{args.out}: {len(out)} prompt {args.split}, {record['empty_contexts']} ngữ cảnh rỗng")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("corpus")
    c.add_argument("--index", type=Path, default=INDEX)
    c.add_argument("--out", type=Path, required=True)
    q = sub.add_parser("queries")
    q.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("prompts")
    p.add_argument("--contexts", type=Path, required=True)
    p.add_argument("--split", choices=("dev", "test"), required=True)
    p.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    {"corpus": corpus, "queries": queries, "prompts": prompts}[args.cmd](args)


if __name__ == "__main__":
    main()
