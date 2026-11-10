from datetime import date

from compare_benchmark_vbhn import (
    ReadOnlyIndex, classify, date_evidence, load_readonly_states, pdf_units,
    text_statistics, wilson,
)
from vilexgraph.build.temporal import ProvisionVersion, TemporalInterval


def version(n, text):
    return ProvisionVersion(f"version:x:{n}", "provision:x", n, text,
                            TemporalInterval(date(2020 + n, 1, 1)))


def test_full_text_selects_other_version_after_1500_characters():
    prefix = "quy định " * 220
    old = version(1, prefix + "phạt 10 triệu đồng")
    new = version(2, prefix + "phạt 20 triệu đồng")
    result = classify(new.text, old, (old, new))
    assert result["category"] == "chon_sai_phien_ban"
    assert result["nearest_relation"] == "other_closer"
    assert result["versions"][0]["ratio"] < 1


def test_near_match_is_not_automatic_error_or_minor_change():
    old = version(1, "1. Phạt tiền 100 đồng")
    new = version(2, "1. Phạt tiền 101 đồng")
    assert classify("1. Phạt tiền 102 đồng", old, (old, new))["category"] == "can_nguoi_xem"
    assert classify("1. Phạt tiền 100 đồng.", old, (old, new))["category"] == "khac_nho"
    assert classify(old.text, old, (old, new))["category"] == "khop"
    numeric = version(1, "Phạt 1,5 triệu đồng")
    assert classify("Phạt 15 triệu đồng", numeric, (numeric,))["category"] == "can_nguoi_xem"
    words = version(1, "không được phép")
    assert classify("khôngđược phép", words, (words,))["category"] == "can_nguoi_xem"


def test_numbered_points_page_notes_and_duplicate_keys():
    text = """Hà Nội, ngày 01 tháng 02 năm 2024
Điều 1. Phạm vi
1. Điều kiện:
a) Phần một
tiếp tục toàn văn.
2 Điều này được sửa đổi
bởi văn bản khác.
\f2
b) Phần hai.
Điều 2. Quy định
1. Một
1. Trùng
"""
    units, preamble, notes = pdf_units(text)
    assert units[("1", "1", "a")] == ["a) Phần một tiếp tục toàn văn."]
    assert units[("1", "1", "b")] == ["b) Phần hai."]
    assert units[("1", "1", None)] == ["1. Điều kiện:"]
    assert len(units[("2", "1", None)]) == 2
    assert len(notes) == 2
    assert "2024" in preamble


def test_header_date_is_not_original_effective_date():
    text = """Số: 10/VBHN-X Hà Nội, ngày 02 tháng 03 năm 2024
Văn bản gốc ngày 01 tháng 01 năm 2020 có hiệu lực
Điều 1. Nội dung
"""
    assert date_evidence(text, "2024-03-02")["usable"]
    assert not date_evidence(text, "2020-02-01")["usable"]
    assert not date_evidence(text.replace("năm 2020 có hiệu lực", "năm 2025 có hiệu lực"), "2024-03-02")["usable"]


def test_certification_date_at_end_and_cited_date_rejected():
    text = """Thông tư số 1 ngày 01 tháng 01 năm 2020
Điều 1. Nội dung
XÁC THỰC VĂN BẢN HỢP NHẤT
Số: 10/VBHN-X Hà Nội, ngày 02 tháng 03 năm 2024
"""
    assert date_evidence(text, "2024-03-02")["usable"]
    assert not date_evidence(text, "2020-01-01")["usable"]


def test_readonly_adapter_and_empty_wilson(tmp_path):
    import sqlite3
    import pytest
    path = tmp_path / "graph.sqlite"
    sqlite3.connect(path).close()
    with ReadOnlyIndex(path) as index:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            index._db.execute("CREATE TABLE forbidden (id)")
    assert wilson(0, 0) is None
    lo, hi = wilson(10, 10)
    assert 0.72 < lo < 0.73
    assert abs(hi - 1) < 1e-12


def test_unresolved_full_text_pairs_stay_in_match_denominator():
    pairs = [dict(category=c, selected_version_id="version:x:1",
                  reason="full_own_text_structural_alignment")
             for c in ("khop", "khac_nho", "can_nguoi_xem", "chon_sai_phien_ban", "dau_bai_bo")]
    pairs.append(dict(category="khong_can_duoc"))
    pairs.append(dict(category="can_nguoi_xem", selected_version_id=None,
                      reason="full_own_text_structural_alignment"))
    result = text_statistics(pairs)
    assert result["comparable"] == 4
    assert result["matches"] == 2
    assert result["unresolved_comparable"] == 1
    assert result["match_rate"] == 0.5
    assert result["wilson95"] == wilson(2, 4)


def test_loader_restores_accepted_repeal_without_replaying_it(tmp_path, monkeypatch):
    import json
    from vilexgraph.build.temporal import (
        LegalDocument, Provision, ProvisionLevel, SnapshotService,
    )
    monkeypatch.chdir(tmp_path)
    derived = tmp_path / "data/derived"
    derived.mkdir(parents=True)
    document = LegalDocument("document:x", "1/2020/X", "Test")
    provision = Provision("provision:x", document.id, ProvisionLevel.ARTICLE, "Điều 1", None)

    class Index:
        def document(self, _):
            return document

        def document_order(self, _):
            return (provision,)

    (derived / "versions.jsonl").write_text(json.dumps(dict(
        id="version:x:1", provision_id=provision.id, ordinal=1, text="Điều 1. Nội dung",
        valid_from="2020-01-01", valid_to="2021-01-01",
        created_by_event_id=None, ended_by_event_id="event:repeal")) + "\n")
    (derived / "provision_events.jsonl").write_text(json.dumps(dict(
        id="event:repeal", operation="repeal", actor_id="document:y",
        target_document_id=document.id, target_provision_id=provision.id,
        effective_on="2021-01-01", status="auto_accepted")) + "\n")
    state = load_readonly_states(Index(), {document.id})[document.id]
    assert SnapshotService(state).snapshot(provision.id, date(2020, 1, 1)).text == "Điều 1. Nội dung"
    snapshot = SnapshotService(state).snapshot(provision.id, date(2021, 1, 1))
    assert snapshot.validity.reason.value == "provision_repealed"
    assert state.event("event:repeal").resolved_target_ids == (provision.id,)


def test_a_footnote_number_after_the_point_letter_still_opens_that_point():
    # TT 23/2018 Điều 5 khoản 1: "đ)19 (được bãi bỏ)." was read as part of point d, so the repeal
    # signal landed on a point that was not repealed (H5 L6).
    text = """Điều 5. Điều kiện
1. Hạng III:
d) Có giấy chứng nhận bồi dưỡng;
đ)19 (được bãi bỏ).
2. Hạng II:
"""
    units, _, _ = pdf_units(text)
    assert units[("5", "1", "d")] == ["d) Có giấy chứng nhận bồi dưỡng;"]
    assert units[("5", "1", "đ")] == ["đ)19 (được bãi bỏ)."]
