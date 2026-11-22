"""Machine side of the W3 recall gate: fed the six known actors, compare.judge must flag all six; fed an actor
the store did apply on the chain, it must flag nothing. python3 data/review/qa_v6/w3/test_compare.py"""
import json
from pathlib import Path

import compare as c

HERE = Path(__file__).resolve().parent
KNOWN = {"20/2008/NĐ-CP": "92/2017/NĐ-CP", "33/2010/NĐ-CP": "53/2012/NĐ-CP", "05/2015/NĐ-CP": "145/2020/NĐ-CP",
         "135/2004/NĐ-CP": "221/2013/NĐ-CP", "23/2014/TT-NHNN": "32/2016/TT-NHNN", "11/2021/TT-BXD": "36/2026/TT-BXD"}
store = c.load_store()
targets = {t["law_id"]: t for t in map(json.loads, open(HERE / "gate_batch.jsonl", encoding="utf-8"))}
for law, actor in KNOWN.items():
    assert c.judge(targets[law], {"actor_number": actor}, store), (law, actor)
assert c.judge(targets["20/2008/NĐ-CP"], {"actor_number": "48/2013/NĐ-CP"}, store) is None
print("compare: 6/6 lỗi đã biết bị gắn ứng viên; sửa đổi kho đã áp dụng không bị gắn")
