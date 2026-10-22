import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))


def test_the_timeline_marks_the_rows_version_and_shows_what_each_act_changed():
    from kiem_hints import timeline

    versions = [{"ordinal": 1, "from": "2015-09-01", "to": "2026-01-15", "text": "trong 15 ngày"},
                {"ordinal": 2, "from": "2026-01-15", "to": None, "text": "trong 10 ngày"}]
    got = timeline(versions, {2: "sửa bởi 18/2026/NĐ-CP (hiệu lực 2026-01-15)"}, mine=2)
    assert got.splitlines() == [
        "[1] 2015-09-01 → 2026-01-15 · bản gốc",
        "[2] 2026-01-15 → nay · sửa bởi 18/2026/NĐ-CP (hiệu lực 2026-01-15)   ◀ đáp án của dòng này",
        "    chỗ đổi: «15» → «10»"]
    repealed = timeline(versions[:1], {}, mine=1, repeal="Hết hiệu lực từ 2026-01-15 (bãi bỏ đích danh) bởi X")
    assert repealed.endswith("bởi X") and "◀" in repealed
