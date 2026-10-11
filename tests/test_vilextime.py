"""The released record shape of ADR 0003."""
from build_vilextime import citation, parts_of, question_of, records_of, transitions_of

# (number, rank, source_url, issued_on, effective_from, title) — what the builder reads.
_TITLE = "Thông tư số 16/2012/TT-NHNN Quy định về việc cho vay bằng ngoại tệ"
DOCUMENTS = {
    "document:27581": ("16/2012/TT-NHNN", "Thông tư", "https://vbpl.vn/x?ItemID=27581", "2012-05-25", "2012-07-01", _TITLE),
    "document:96223": ("38/2015/TT-NHNN", "Thông tư", "https://vbpl.vn/x?ItemID=96223", "2015-12-31", "2016-02-15", ""),
    "document:149987": ("15/2021/TT-NHNN", "Thông tư", "https://vbpl.vn/x?ItemID=149987", "2021-09-30", "2021-11-20", ""),
    "document:158757": ("24/2022/TT-NHNN", "Thông tư", "https://vbpl.vn/x?ItemID=158757", "2022-12-30", "2023-02-15", ""),
}
PARENTS = {"provision:p": "provision:parent"}
LEAD_INS = {("provision:parent", "2021-11-21"): "1. Tổ chức tín dụng được cho vay bằng ngoại tệ khi:"}
CHAIN = [("Chapter", "Chương III"), ("Article", "Điều 18"), ("Clause", "Khoản 1")]


def _version(ordinal, start, end):
    return {"id": f"version:p:{ordinal}", "ordinal": ordinal, "text": f"nội dung {ordinal}",
            "effective_from": start, "effective_to": end}


def _t3_row():
    """The real chain from the audit: three amendments, ids that sort wrongly."""
    return {
        "id": "vilextime:T3:provision:p", "group": "T3", "provision_id": "provision:p",
        "document_id": "document:27581", "level": "Clause",
        "versions": [_version(1, "2012-07-01", "2016-02-15"), _version(2, "2016-02-15", "2021-11-20"),
                     _version(3, "2021-11-20", "2023-02-15"), _version(4, "2023-02-15", None)],
        # sorted(set(...)): event:149987 sorts before event:96223, so index order
        # is NOT chronological order. This is the bug the schema removes.
        "event_ids": ["event:149987:9fc3f29d8b312b8192ba29c9",
                      "event:158757:371fafa93f8acf0fa1f030ac",
                      "event:96223:3d6c034aa9aa475d54ac2874"],
        "gold": [{"as_of": "2012-07-02", "in_force": True, "version_id": "version:p:1", "text": "nội dung 1"},
                 {"as_of": "2016-02-16", "in_force": True, "version_id": "version:p:2", "text": "nội dung 2"},
                 {"as_of": "2021-11-21", "in_force": True, "version_id": "version:p:3", "text": "nội dung 3"},
                 {"as_of": "2023-02-16", "in_force": True, "version_id": "version:p:4", "text": "nội dung 4"}],
    }


def test_citation_reads_innermost_first_and_drops_the_outer_containers():
    assert citation(CHAIN) == "Khoản 1 Điều 18"
    assert citation([("Chapter", "Chương II"), ("Section", "Mục 3"), ("Article", "Điều 23"),
                     ("Clause", "Khoản 3"), ("Point", "Điểm đ")]) == "Điểm đ Khoản 3 Điều 23"
    assert citation([("Article", "Điều 5")]) == "Điều 5"


def test_the_provision_numbers_no_published_vietnamese_dataset_carries():
    assert parts_of(CHAIN) == {"article_id": "18", "clause_id": "1", "point_id": None}
    # An article can be "23a" and a point is a letter, so the label is the whole tail.
    assert parts_of([("Article", "Điều 23a"), ("Point", "Điểm đ")])["article_id"] == "23a"
    assert parts_of([("Article", "Điều 23a"), ("Point", "Điểm đ")])["point_id"] == "đ"


def test_the_question_carries_the_as_of_date():
    got = question_of("Khoản 1 Điều 18", "Thông tư", "16/2012/TT-NHNN", "2021-11-21")
    assert got == "Tính đến ngày 21/11/2021, Khoản 1 Điều 18 Thông tư số 16/2012/TT-NHNN quy định nội dung gì?"


def test_each_transition_keeps_its_own_actor_however_the_event_ids_sort():
    """The pool's three parallel lists drift apart from three amendments on."""
    got = transitions_of(_t3_row(), DOCUMENTS)

    assert [t["on"] for t in got] == ["2016-02-15", "2021-11-20", "2023-02-15"]
    assert [t["actor"]["law_id"] for t in got] == ["38/2015/TT-NHNN", "15/2021/TT-NHNN", "24/2022/TT-NHNN"]
    # 38/2015 is the FIRST amendment but its event id sorts LAST — the alignment
    # comes from the date, never from the position in the list.
    assert got[0]["event_id"] == "event:96223:3d6c034aa9aa475d54ac2874"
    assert [(t["from_version"], t["to_version"]) for t in got] == [(1, 2), (2, 3), (3, 4)]
    assert all(t["actor"]["effective_from"] == t["on"] for t in got)


def test_one_record_per_as_of_and_never_a_status_string_in_the_answer():
    records = records_of(_t3_row(), DOCUMENTS, {"provision:p": CHAIN}, PARENTS, LEAD_INS, {})

    assert len(records) == 4                       # four dates, four records
    assert len({r["id"] for r in records}) == 4    # the as_of makes the id unique
    assert records[2]["as_of"] == "2021-11-21"
    assert records[2]["id"].endswith(":2021-11-21")
    assert all(r["lineage_id"] == "provision:p" for r in records)   # split groups on this
    assert records[2]["valid_from"] == "2021-11-20" and records[2]["valid_to"] == "2023-02-15"
    assert records[2]["utilized_version_ids"] == ["version:p:3"]
    assert len(records[2]["relevant_version_ids"]) == 4
    assert records[2]["num_transitions"] == 3
    assert all(r["split"] is None for r in records)  # P4.9 assigns it
    # The lead-in that makes a list item legible, as it stood at that date.
    assert records[2]["target"]["lead_in"] == "1. Tổ chức tín dụng được cho vay bằng ngoại tệ khi:"
    assert records[0]["target"]["lead_in"] is None      # no parent version at that date
    assert records[2]["target"]["document_title"].startswith("Thông tư số 16/2012/TT-NHNN")


def test_a_repealed_provision_says_so_in_three_fields_not_in_the_answer_text():
    row = _t3_row()
    row["group"] = "T6"
    row["versions"] = [_version(1, "2012-07-01", "2020-01-01")]
    row["event_ids"] = []
    row["gold"] = [{"as_of": "2019-12-31", "in_force": True, "version_id": "version:p:1", "text": "nội dung 1"},
                   {"as_of": "2020-01-01", "in_force": False, "version_id": None, "text": None}]

    before, after = records_of(row, DOCUMENTS, {"provision:p": CHAIN}, PARENTS, LEAD_INS, {})

    assert before["answerable"] is True and before["no_answer_reason"] is None
    assert after["answer"] is None                      # never "KHÔNG CÒN HIỆU LỰC"
    assert after["answerable"] is False
    assert after["in_force"] is False
    assert after["no_answer_reason"] == "provision_repealed"
    assert after["utilized_version_ids"] == []


def test_flags_name_structural_faults_and_never_judge_length():
    from build_vilextime import flags_of

    # A Chương is not a provision, and its "text" is its own heading.
    assert flags_of("Chapter", "", "Chương IV", [("Chapter", "Chương IV")]) == [
        "not_a_provision", "heading_only"]
    # A source node titled just "Điều" makes the citation unusable.
    assert flags_of("Clause", "Khoản 3 Điều", "3.2. Mức thu lệ phí …",
                    [("Part", "Phần"), ("Article", "Điều"), ("Clause", "Khoản 3")]) == ["untitled_ancestor"]
    # A numbered citation is fine, however deeply nested.
    assert flags_of("Point", "Điểm đ Khoản 1 Điều 17", "đ) Số lượng, khối lượng dịch vụ thủy nông được trợ cấp;",
                    [("Article", "Điều 17"), ("Clause", "Khoản 1"), ("Point", "Điểm đ")]) == []
    # A heading or a lead-in whose content lives in child nodes is not an answer.
    art = [("Article", "Điều 10")]
    assert flags_of("Article", "Điều 10", "Điều 10. Gia hạn tạm ứng ngân quỹ nhà nước", art,
                    has_children=True) == ["answer_in_children"]
    assert flags_of("Clause", "Khoản 4 Điều 10", "4. Những hàng hóa cấm mang theo người bao gồm:",
                    art + [("Clause", "Khoản 4")]) == ["answer_in_children"]
    assert flags_of("Article", "Điều 4", "Điều 4. Hiệu lực thi hành", [("Article", "Điều 4")]) == [
        "answer_in_children"]                              # the crawl lost its body
    assert flags_of("Article", "Điều 38", "Điều 38. Vốn nhận ủy thác Vốn nhận ủy thác theo quy định tại "
                    "Điều 32 Nghị định này không thuộc vốn hoạt động của Quỹ và được hạch toán tách bạch.",
                    [("Article", "Điều 38")]) == []        # heading and body in one text
    # 54 characters and entirely valid: length is the hand-check's call, not ours.
    assert flags_of("Point", "Điểm a Khoản 4 Điều 17", "a) Chi tổ chức hội nghị, hội thảo, sơ kết, tổng kết;",
                    [("Article", "Điều 17"), ("Clause", "Khoản 4"), ("Point", "Điểm a")]) == []


def test_a_generated_question_replaces_the_template_across_every_date():
    """C3: one question per lineage, and the row records what produced it."""
    generated = {"provision:p": {"question": "Theo quy định về cho vay bằng ngoại tệ, "
                                             "tổ chức tín dụng được cho vay trong trường hợp nào?",
                                 "provider": "groq", "model": "llama-3.3-70b-versatile",
                                 "temperature": 0.0, "prompt_sha": "4c766103a79e"}}
    records = records_of(_t3_row(), DOCUMENTS, {"provision:p": CHAIN}, PARENTS, LEAD_INS, generated)

    assert len({r["question"] for r in records}) == 1       # same question at all four dates
    assert "ngoại tệ" in records[0]["question"]
    assert records[0]["question_source"] == {"kind": "llm", "provider": "groq",
                                             "model": "llama-3.3-70b-versatile",
                                             "temperature": 0.0, "prompt_sha": "4c766103a79e"}
    assert "2021" not in records[2]["question"]             # the date lives in as_of, not the text

    # A question a person rewrote during the hand-check says who and when.
    generated["provision:p"].update(edited_by="human:excel", edited_at="2026-09-28")
    edited = records_of(_t3_row(), DOCUMENTS, {"provision:p": CHAIN}, PARENTS, LEAD_INS, generated)
    assert edited[0]["question_source"]["edited_by"] == "human:excel"

    # With nothing generated the row falls back and says so.
    fallback = records_of(_t3_row(), DOCUMENTS, {"provision:p": CHAIN}, PARENTS, LEAD_INS, {})
    assert fallback[0]["question_source"]["kind"] == "template"
    assert len({r["question"] for r in fallback}) == 4      # the template embeds the date


def test_the_sample_skips_flags_caps_documents_and_never_splits_a_lineage():
    from sample_vilextime import sample

    def rec(lid, doc, flags=()):
        return {"lineage_id": lid, "target": {"document_id": doc}, "flags": list(flags)}

    records = [rec(f"l{i}", "big") for i in range(10) for _ in range(2)]           # 10 two-date lineages, one doc
    records += [rec("bad", "other", ["not_a_provision"]), rec("ok", "other")]

    picked = sample(records, target=100)       # asks for far more than exists
    ids = [p["lineage_id"] for p in picked]
    assert "bad" not in ids and "ok" in ids
    assert sum(p["document_id"] == "big" for p in picked) == 2      # PER_DOCUMENT
    assert all(p["rows"] == 2 for p in picked if p["document_id"] == "big")
    assert picked == sample(records, target=100)                    # seeded
    assert [p["rank"] for p in picked] == list(range(len(picked)))


def test_the_release_fills_the_quota_exactly_in_rank_order():
    from sample_vilextime import select

    ranked = [{"rank": i, "lineage_id": f"l{i}", "rows": rows} for i, rows in enumerate([3, 4, 3, 3, 4])]
    assert select(ranked, {"l0", "l1", "l2", "l3", "l4"}, quota=10) == ["l0", "l1", "l2"]
    assert select(ranked, {"l1", "l2", "l3", "l4"}, quota=10) == ["l1", "l2", "l3"]      # l0 failed C2
    assert select(ranked, {"l0", "l1", "l3", "l4"}, quota=9) == ["l1", "l4"]   # 9 unreachable: closest below, never over
    # Greedy stranded T3 at 198/200: 3+3+3 leaves 1 and nothing fits.
    chains = [{"rank": i, "lineage_id": f"c{i}", "rows": rows} for i, rows in enumerate([3, 3, 3, 4])]
    assert select(chains, {"c0", "c1", "c2", "c3"}, quota=10) == ["c0", "c1", "c3"]


def test_the_versions_file_is_read_whatever_its_json_separators():
    """versions.jsonl went compact on 22/09 and every lead-in vanished silently."""
    from build_vilextime import _PROVISION_ID

    for line in ('{"id":"v:1","provision_id":"provision:p","text":"x"}',
                 '{"id": "v:1", "provision_id": "provision:p", "text": "x"}'):
        assert _PROVISION_ID.search(line).group(1) == "provision:p"


def test_a_change_of_case_or_punctuation_is_not_a_change():
    from build_vilextime import cosmetic_only

    assert cosmetic_only(["tỉnh, thành phố trực thuộc Trung ương.", "tỉnh, thành phố trực thuộc trung ương;"])
    assert not cosmetic_only(["giao Bộ Tài nguyên và Môi trường", "giao Bộ Nông nghiệp và Môi trường"])
    assert cosmetic_only(["a", "b thay", "B thay."])         # any consecutive pair counts


def test_retroactive_kind_is_measured_not_guessed_from_wording():
    from build_question_pool import retro_kind

    effective = {"100/2016/NĐ-CP": "2016-07-01", "242/2025/NĐ-CP": "2025-09-10"}
    # Guidance that takes effect with the decree it details: excluded by the adviser.
    assert retro_kind("130/2016/TT-BTC", "Thông tư số 130/2016/TT-BTC Hướng dẫn thực hiện Nghị định số "
                      "100/2016/NĐ-CP", "2016-07-01", effective) == "guidance_in_sync"
    # An amendment quoting its target's title, and the title opening with its own number.
    assert retro_kind("119/2026/NĐ-CP", "Nghị định 119/2026/NĐ-CP Sửa đổi, bổ sung Nghị định 242/2025/NĐ-CP "
                      "quy định chi tiết", "2026-01-01", effective) == "stated_retroactive"
    assert retro_kind("2714/QĐ-BTC", "Quyết định về việc đính chính Thông tư", "2013-08-12", {}) == "correction"


def test_the_ranking_on_disk_survives_a_lineage_leaving_its_group():
    from sample_vilextime import sample

    def rec(lid, doc):
        return {"lineage_id": lid, "target": {"document_id": doc}, "flags": []}

    records = [rec(f"l{i}", f"d{i}") for i in range(6)]
    first = [p["lineage_id"] for p in sample(records, target=6)]
    moved = first[1]                                           # say it went to T5
    second = [p["lineage_id"] for p in sample([r for r in records if r["lineage_id"] != moved],
                                              target=5, prior=first)]
    assert second == [lid for lid in first if lid != moved]


def test_t5_worksheet_quotes_an_undated_from_signing_clause():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))
    from t5_worksheet import effectivity_words

    words = effectivity_words("<p>Điều 30. Hiệu lực thi hành 1. Nghị định này có hiệu lực thi hành kể từ ngày ký "
                              "ban hành, trừ khoản 2. 2. Điều 25 có hiệu lực thi hành từ ngày 01 tháng 7 năm 2026</p>")
    assert "kể từ ngày ký ban hành" in words.split(" | ")[0]
    assert "01 tháng 7 năm 2026" in words


def test_t6_ranks_its_ancestor_part_apart_and_old_ranking_lines_read_as_direct():
    from sample_vilextime import T6_ANCESTOR_ROWS, part_of, parts

    records = [{"lineage_id": "a", "repeal_mode": "direct"}, {"lineage_id": "b", "repeal_mode": "ancestor"}]
    split = {part: [r["lineage_id"] for r in recs] for part, recs, _ in parts("T6", records, 300)}
    assert split == {"direct": ["a"], "ancestor": ["b"]}
    assert dict((p, n) for p, _, n in parts("T6", records, 300))["ancestor"] == 2 * T6_ANCESTOR_ROWS
    assert part_of({"group": "T6"}) == "direct" and part_of({"group": "T3"}) is None


def test_t2_ranks_its_near_identical_slice_apart_and_a_pair_stays_in_one_part():
    from sample_vilextime import OVERSAMPLE, T2_NEAR_ROWS, part_of, parts

    # one row of a pair carries the facet: the whole lineage is "near"
    records = [{"lineage_id": "a", "near_identical": False}, {"lineage_id": "a", "near_identical": False},
               {"lineage_id": "b", "near_identical": True}, {"lineage_id": "b", "near_identical": False}]
    split = {part: sorted({r["lineage_id"] for r in recs}) for part, recs, _ in parts("T2", records, 900)}
    assert split == {"regular": ["a"], "near": ["b"]}
    assert dict((p, n) for p, _, n in parts("T2", records, 900))["near"] == T2_NEAR_ROWS * OVERSAMPLE["T2"]
    assert part_of({"group": "T2"}) == "regular" and part_of({"group": "T2", "near_identical": True}) == "near"
