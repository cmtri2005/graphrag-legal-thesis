"""Flag worksheet actors whose `effective_from` disagrees with their own in-force clause.

The worksheet carries both the extracted date and the clause text ("có hiệu lực từ ngày …").
A mismatch means the boundary as_of rows may sit on the wrong version (case aac3cc10, lô 0).
Reads only the factual worksheet fields; no labels.

    python scripts/review/check_effective_dates.py WORKSHEET.jsonl [...] --out FILE.tsv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path

# ponytail: regex covers the common clause shapes; anything else is reported `unparsed` for a human, never `ok`.
LEAD = r"có\s+hiệu\s+lực(?:\s+thi\s+hành)?"
DATE = re.compile(LEAD + r"[^.;\n]*?(?:từ|kể\s+từ)\s+ngày\s+(\d{1,2})\s*(?:tháng|/)\s*(\d{1,2})\s*(?:năm|/)\s*(\d{4})", re.I)
SIGNED = re.compile(LEAD + r"[^.;\n]*?(?:từ|kể\s+từ)\s+ngày\s+(?:ký|ban\s+hành)", re.I)
AFTER = re.compile(LEAD + r"\s+sau\s+(\d+)\s+ngày[^.;\n]*?kể\s+từ\s+ngày\s+(?:ký|ban\s+hành)", re.I)
# Sổ quyết định 26/10 mục 3: "từ năm ngân sách X" = 01/01/X.
BUDGET = re.compile(LEAD + r"\s+từ\s+năm\s+ngân\s+sách\s+(\d{4})", re.I)
EXCEPT = re.compile(LEAD + r"[^.\n]*?\btrừ\b", re.I)


def clause_date(text: str, issued: str | None) -> tuple[str | None, str]:
    if not text:
        return None, "no_clause"
    sign = dt.date.fromisoformat(issued) if issued else None
    hits = []
    for m in DATE.finditer(text):
        hits.append((m.start(), dt.date(int(m[3]), int(m[2]), int(m[1])), "date"))
    for m in AFTER.finditer(text):
        if sign:
            hits.append((m.start(), sign + dt.timedelta(days=int(m[1])), f"signed+{m[1]}"))
    for m in SIGNED.finditer(text):
        if sign and not AFTER.match(text, m.start()):
            hits.append((m.start(), sign, "signed"))
    for m in BUDGET.finditer(text):
        hits.append((m.start(), dt.date(int(m[1]), 1, 1), "budget_year"))
    if not hits:
        return None, "unparsed"
    _, day, rule = min(hits)  # first in-force sentence = khoản 1
    return day.isoformat(), rule + ("+except" if EXCEPT.search(text) else "")


def check(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        sources = [r.get("sources", {})] + [row.get("source_evidence", {}) for row in r.get("rows", [])]
        seen = set()
        for s in sources:
            for a in s.get("actors", []):
                key = (a.get("document"), a.get("effective_from"))
                if key in seen:
                    continue
                seen.add(key)
                parsed, rule = clause_date(a.get("in_force") or "", a.get("issued"))
                status = ("unparsed" if parsed is None else
                          "mismatch" if parsed != a.get("effective_from") else
                          "partial" if rule.endswith("+except") else "ok")
                out.append({"worksheet": path.name, "lineage_id": r["lineage_id"], "group": r.get("group"),
                            "batch": r.get("batch"), "document": a.get("document"), "issued": a.get("issued"),
                            "effective_from": a.get("effective_from"), "clause_date": parsed or "", "rule": rule,
                            "status": status, "as_of": " ".join(row.get("as_of", "") for row in r.get("rows", [])),
                            "clause": " ".join((a.get("in_force") or "").split())[:300]})
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("worksheets", type=Path, nargs="+")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    rows = [x for w in args.worksheets for x in check(w)]
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    for name in dict.fromkeys(x["worksheet"] for x in rows):
        mine = [x for x in rows if x["worksheet"] == name]
        counts = {s: sum(x["status"] == s for x in mine) for s in ("ok", "partial", "mismatch", "unparsed", )}
        print(name, len(mine), "actors", counts, "lineage có mismatch:",
              len({x["lineage_id"] for x in mine if x["status"] == "mismatch"}))


if __name__ == "__main__":
    main()
