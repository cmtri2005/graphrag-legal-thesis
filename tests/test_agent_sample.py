import csv

from openpyxl import Workbook

import agent_sample
from agent_sample import load


def _sheet(path, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "kiem_agent"
    ws.append(["id", "agent_verdict", "agent_reasons", "ly_do", "ket_luan_chot"])
    for r in rows:
        ws.append(r)
    wb.save(path)


def test_load_merges_sheets_and_takes_reason_codes_from_the_agent(tmp_path):
    out = tmp_path / "luat_su.tsv"
    _sheet(tmp_path / "a.xlsx", [("x", "khong_dat", "relocation_unclear", "chuyển\nchỗ", "khong_dat"),
                                 ("y", "khong_dat", "gold_wrong", "bãi bỏ thật", "dat")])
    _sheet(tmp_path / "b.xlsx", [("z", "dat", "", "sai", "khong_dat"),
                                 ("y", "khong_dat", "gold_wrong", "xem lại", "khong_dat")])
    load(tmp_path / "a.xlsx", out)
    load(tmp_path / "b.xlsx", out)
    rows = {r["id"]: r for r in csv.DictReader(out.open(encoding="utf-8"), delimiter="\t")}
    assert {i: (r["verdict"], r["reasons"]) for i, r in rows.items()} == {
        "x": ("khong_dat", "relocation_unclear"), "y": ("khong_dat", "gold_wrong"), "z": ("khong_dat", "other")}
    assert rows["x"]["note"] == "chuyển chỗ"


def test_sample_is_fixed_and_has_no_duplicates():
    rows = [{"id": f"r{i}"} for i in range(325)]
    a, b = agent_sample.sample(rows), agent_sample.sample(list(reversed(rows)))
    assert [r["id"] for r in a] == [r["id"] for r in b] and len({r["id"] for r in a}) == 50
