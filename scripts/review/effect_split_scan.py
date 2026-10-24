#!/usr/bin/env python3
"""ViLexTime — văn bản tác động có hiệu lực tách phần (hướng dẫn 3.0 §7, mục 24/10 số 5).

Mốc của máy lấy ngày hiệu lực chung của văn bản tác động. Văn bản có điều hiệu lực tách phần
("trừ quy định tại khoản 2, 3 Điều này", "các quy định về … có hiệu lực kể từ ngày ký") có thể làm
mốc sai (NĐ 17/2020/NĐ-CP, lô 0). Đọc điều hiệu lực trong toàn văn `data/raw/<id>.json` của mọi văn
bản tác động mà bản phát hành dùng, ghi ứng viên ra TSV. Chỉ là ứng viên: người kiểm đọc
`dieu_hieu_luc` để biết lần sửa của dòng có thuộc phần ngoại lệ không.

    python scripts/review/effect_split_scan.py      # -> data/review/hieu_luc_tach.tsv
"""
from __future__ import annotations

import collections
import csv
import html
import json
import re
from pathlib import Path

DATE = re.compile(r"ngày (\d{1,2}) tháng (\d{1,2}) năm (\d{4})|(\d{1,2})/(\d{1,2})/(\d{4})")
HEAD = re.compile(r"Điều \d+[a-z]?\s*[.:]?\s*(?:Hiệu lực|Điều khoản thi hành|Tổ chức thực hiện và hiệu lực)", re.I)
# "sau 45 ngày kể từ ngày ký" là ngày chung, không phải tách phần; "kê" là lỗi gõ có trong Công báo số hoá
SIGNS = (("trừ", r"\btrừ\b"), ("ngày ký", r"(?<!\d ngày )k[ểê] từ ngày ký|có hiệu lực(?: thi hành)? từ ngày ký"),
         ("riêng", r"\b[Rr]iêng\b"), ("các quy định về", r"Các quy định về"))


def effect_article(raw: Path) -> str | None:
    body = json.loads(raw.read_text(encoding="utf-8"))["documentContent"] or ""
    body = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))
    heads = list(HEAD.finditer(text))
    if not heads:
        return None
    seg = text[heads[-1].start():]
    nxt = re.search(r" Điều \d+[a-z]?\s*[.:]", seg[10:])
    return seg[:10 + nxt.start()] if nxt else seg[:2500]


def main(data: Path = Path("data")) -> None:
    docs = {d["document_id"]: d for d in map(json.loads, open(data / "derived/corpus/documents.jsonl", encoding="utf-8"))}
    use = collections.defaultdict(list)          # văn bản tác động -> dòng dùng nó làm mốc
    for line in open(data / "vilextime_dataset/vilextime_meta.jsonl", encoding="utf-8"):
        m = json.loads(line)
        for t in m["derivation"]["transitions"]:
            use[t["actor"]["document_id"]].append(m)
    rows = []
    for did, metas in use.items():
        raw = data / "raw" / f"{did.split(':', 1)[1]}.json"
        seg = effect_article(raw) if raw.exists() else None
        if seg is None:
            continue
        doc = docs[did]
        signs = [name for name, pat in SIGNS if re.search(pat, seg)]
        if "ngày ký" in signs and doc["issued_on"] == doc["effective_from"]:
            signs.remove("ngày ký")              # cả văn bản hiệu lực từ ngày ký, kho đã ghi đúng
        if not signs:                            # ngày khác trong điều này thường là ngày của văn bản bị thay
            continue
        rows.append({"law_id": doc["law_id"], "ngay_ky": doc["issued_on"], "hieu_luc_chung": doc["effective_from"],
                     "dau_hieu": ", ".join(signs),
                     "cac_ngay": ", ".join(sorted({f"{g[2] or g[5]}-{int(g[1] or g[4]):02d}-{int(g[0] or g[3]):02d}"
                                                   for g in DATE.findall(seg)})),
                     "so_lineage": len({m["target"]["provision_id"] for m in metas}), "so_dong": len(metas),
                     "nhom": ", ".join(f"{k}:{v}" for k, v in sorted(collections.Counter(m["subgroup"] for m in metas).items())),
                     "dieu_hieu_luc": seg[:900], "ids": " ".join(m["id"] for m in metas)})
    rows.sort(key=lambda r: (-r["so_lineage"], r["law_id"]))
    out = data / "review/hieu_luc_tach.tsv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{out}: {len(rows)}/{len(use)} văn bản tác động có hiệu lực tách phần, "
          f"{sum(r['so_lineage'] for r in rows)} lineage, {sum(r['so_dong'] for r in rows)} dòng")
    for r in rows:
        print(f"  {r['law_id']:<20} chung {r['hieu_luc_chung']}  [{r['dau_hieu']}]  {r['so_lineage']} lineage  {r['nhom']}")


if __name__ == "__main__":
    main()
