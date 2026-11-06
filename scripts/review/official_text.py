"""Attach official full-text excerpts to an AI labeling input, from the local vbpl crawl.

For every record: the target article of the base document, and the in-force and transitional
articles of each acting document (whole acting document for T6, so step 7(a) "same document"
can be done without the web). Source is `data/raw/<ItemID>.json` = the vbpl gateway payload,
i.e. the official CSDL quốc gia text. Dates come from the clause text, never from `effFrom`.

    python scripts/review/official_text.py WORKSHEET.jsonl --out BUNDLE.jsonl [--ids FILE]

Output line: {"worksheet_sha256", "record", "official": [...]}. The record is untouched so the
binding still matches the worksheet the reviewer sees.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test2_labels import load_worksheet, worksheet_sha256  # noqa: E402

RAW = Path("data/raw")
ITEM = re.compile(r"ItemID=([0-9A-Za-z-]+)")
ARTICLE = re.compile(r"(?m)^Điều\s+(\d+[a-zđ]?)\s*[.:]?")
# ponytail: caps keep a session's context bounded; a capped excerpt says so in `truncated`.
CAP_ARTICLE, CAP_FULL = 8000, 30000


def text_of(item_id: str) -> tuple[str, dict] | None:
    path = RAW / f"{item_id}.json"
    if not path.exists():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    raw = (doc.get("documentContent") or {}).get("content") or ""
    raw = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d)>", "\n", raw)
    lines = (" ".join(s.split()) for s in html.unescape(re.sub(r"<[^>]+>", "", raw)).splitlines())
    return "\n".join(s for s in lines if s), {"docNum": doc.get("docNum"), "issueDate": doc.get("issueDate")}


def articles(text: str) -> dict[str, str]:
    marks = list(ARTICLE.finditer(text))
    out = {}
    for m, nxt in zip(marks, marks[1:] + [None]):
        out.setdefault(m[1], text[m.start(): nxt.start() if nxt else len(text)].strip())
    return out


def closing_articles(text: str, cap: int = 3000) -> str:
    """The acting document's own in-force and transitional articles.

    Amending documents quote the amended articles ("Điều 21. …") inside their own body, so a
    number-keyed lookup can return a quoted article. The document's own closing articles come
    last, so take the LAST block whose heading matches, in priority order.
    """
    marks = list(ARTICLE.finditer(text))
    blocks = [text[m.start(): (n.start() if n else len(text))].strip() for m, n in zip(marks, marks[1:] + [None])]
    picked = []
    for pattern in (r"hiệu lực", r"chuyển tiếp", r"thi hành"):
        hits = [b for b in blocks if re.search(pattern, b.split("\n", 1)[0], re.I) and b not in picked]
        if hits and (pattern != r"thi hành" or not picked):
            picked.append(hits[-1])
    if not picked:  # e.g. "Điều 2. Tổ chức thực hiện / 1. Thông tư này có hiệu lực …"
        hits = [b for b in blocks if re.search(r"(này|văn bản) có hiệu lực", b, re.I)]
        picked = hits[-1:]
    return "\n\n".join(b[:cap] + (" …[cắt]" if len(b) > cap else "") for b in picked)


def excerpt(document: str, item_id: str, part: str, text: str, cap: int) -> dict:
    return {"document": document, "item_id": item_id, "part": part, "source_tier": "official",
            "source": f"vbpl CSDL quốc gia, bản crawl {RAW}/{item_id}.json", "truncated": len(text) > cap,
            "text": text[:cap]}


def official(record: dict) -> tuple[list[dict], list[str]]:
    out, missing = [], []
    src = record.get("sources", {})
    base = src.get("base") or {}
    m = ITEM.search(base.get("source_url") or "")
    target = (record["rows"][0].get("target") or {}) if record.get("rows") else {}
    got = text_of(m[1]) if m else None
    if got and target.get("article_id"):
        art = articles(got[0]).get(str(target["article_id"]))
        if art:
            out.append(excerpt(base.get("document"), m[1], f"Điều {target['article_id']} (bản ban hành)", art, CAP_ARTICLE))
        else:
            missing.append(f"base {base.get('document')}: không tách được Điều {target['article_id']}")
    else:
        missing.append(f"base {base.get('document')}: không có bản crawl")
    seen = set()
    for a in src.get("actors", []):
        m = ITEM.search(a.get("source_url") or "")
        if not m or m[1] in seen:
            continue
        seen.add(m[1])
        got = text_of(m[1])
        if not got:
            missing.append(f"actor {a.get('document')}: không có bản crawl")
            continue
        keep = closing_articles(got[0])
        if keep:
            out.append(excerpt(a.get("document"), m[1], "điều hiệu lực, chuyển tiếp", keep, CAP_ARTICLE))
        else:
            missing.append(f"actor {a.get('document')}: không thấy điều hiệu lực/chuyển tiếp")
        if record.get("group") == "T6":
            out.append(excerpt(a.get("document"), m[1], "toàn văn", got[0], CAP_FULL))
    return out, missing


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("worksheet", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--ids", type=Path, help="một lineage_id mỗi dòng; mặc định cả phiếu")
    args = p.parse_args()
    records = load_worksheet(args.worksheet)
    if args.ids:
        want = [s.strip() for s in args.ids.read_text(encoding="utf-8").splitlines() if s.strip()]
        by = {r["lineage_id"]: r for r in records}
        records = [by[i] for i in want]
    gaps = 0
    with args.out.open("w", encoding="utf-8") as f:
        for r in records:
            off, missing = official(r)
            gaps += bool(missing)
            f.write(json.dumps({"worksheet_sha256": worksheet_sha256(r), "record": r, "official": off,
                                "official_missing": missing}, ensure_ascii=False) + "\n")
    print(f"{len(records)} câu -> {args.out}; {gaps} câu thiếu ít nhất một đoạn chính thức")


if __name__ == "__main__":
    main()
