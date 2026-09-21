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

    # With nothing generated the row falls back and says so.
    fallback = records_of(_t3_row(), DOCUMENTS, {"provision:p": CHAIN}, PARENTS, LEAD_INS, {})
    assert fallback[0]["question_source"]["kind"] == "template"
    assert len({r["question"] for r in fallback}) == 4      # the template embeds the date
