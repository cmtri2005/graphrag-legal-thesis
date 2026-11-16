"""ADR 0006 §7: giữ dòng mà gold mù cho thấy gold sai, với gold đã sửa. Ghi bản release đã sửa vào thư mục này;
không sửa data/vilextime_final. Sửa duy nhất F019 (luật sư, gold_B 16/11; TT 36/2026/TT-BXD Điều 16 bãi bỏ
TT 11/2021/TT-BXD từ 01/07/2026, ngày hỏi 06/08/2026): thành dòng không có đáp án."""
import json, sys
from pathlib import Path
OUT = Path(sys.argv[1]); SRC = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/vilextime_final")
ROW = "vilextime:T2:provision:4cee6a60-eb71-11f0-ac45-154b0d915a56:2026-08-06"
for name, fix in (("vilextime.jsonl", dict(answerable=False, answer=None, context=None, version_id=None)),
                  ("vilextime_meta.jsonl", dict(answerable=False, answer=None, no_answer_reason="provision_repealed",
                                                in_force=False, version_id=None, valid_to="2026-07-01"))):
    rows, hit = [json.loads(l) for l in (SRC / name).open(encoding="utf-8")], 0
    for r in rows:
        if r["id"] == ROW:
            hit += 1
            for k, v in fix.items():
                if k in r: r[k] = v
            for k in ("short_answer",):
                if k in r: r[k] = None
    assert hit == 1, (name, hit)
    with (OUT / name).open("w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, "sửa 1 dòng /", len(rows))
