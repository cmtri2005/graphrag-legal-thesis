"""A phrase edit that missed the as-published text is resolved on the text in force (plan phase-4, J3)."""
from build_versions import REBASED_IN_FORCE, phrase_in_force


def _row(**kw):
    return {"id": "event:X", "status": "needs_review", "status_reason": "phrase_not_found",
            "target_provision_id": "provision:k1", "text_updates": [],
            "phrase_edits": [["Tổng cục Đường bộ", "Cục Đường bộ"]], **kw}


ORDER = ("provision:k1", "provision:a", "provision:b", "provision:k2")
CHILDREN = {"provision:k1": ["provision:a", "provision:b"]}


def test_the_phrase_an_earlier_amendment_put_in_is_found_in_the_subtree():
    now = {"provision:k1": "1. Hồ sơ gồm:", "provision:a": "a) Văn bản của Tổng cục Đường bộ;",
           "provision:b": "b) Bản sao giấy phép.", "provision:k2": "2. Tổng cục Đường bộ quyết định."}
    row = phrase_in_force(_row(), ORDER, CHILDREN, now.get)
    assert row["status"] == "auto_accepted" and row["status_reason"] == REBASED_IN_FORCE
    assert row["text_updates"] == [{"target_provision_id": "provision:a", "new_text": "a) Văn bản của Cục Đường bộ;"}]


def test_nothing_to_apply_leaves_the_event_for_review():
    assert phrase_in_force(_row(), ORDER, CHILDREN, {"provision:k1": "1. Không có cụm từ."}.get) is None
    assert phrase_in_force(_row(phrase_edits=None), ORDER, CHILDREN, {}.get) is None


def test_on_one_day_a_phrase_edit_yields_to_the_same_documents_other_instructions():
    from build_versions import EventEnvelope

    phrase = EventEnvelope(1, {"effective_on": "2024-07-01", "actor_id": "document:A", "phrase_edits": [["a", "b"]]})
    rewrite = EventEnvelope(2, {"effective_on": "2024-07-01", "actor_id": "document:A"})
    earlier = EventEnvelope(3, {"effective_on": "2024-06-01", "actor_id": "document:B", "phrase_edits": [["a", "b"]]})
    order = sorted([phrase, rewrite, earlier], key=lambda e: e.application_sort_key)
    assert [e.line_number for e in order] == [3, 2, 1]
