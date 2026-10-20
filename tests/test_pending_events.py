"""Rule R6: a pending event on the row's provision or any ancestor keeps the row out of test."""
from pending_events import ancestors


def test_a_derived_point_reaches_its_clause_its_article_and_the_tree_above():
    parent_of = {"provision:A": "provision:CH", "provision:CH": "provision:PH"}
    assert ancestors("provision:A#k2#b", parent_of) == [
        "provision:A#k2#b", "provision:A#k2", "provision:A", "provision:CH", "provision:PH"]
    assert ancestors("provision:X", {}) == ["provision:X"]


def test_r6_blocks_amendments_and_repeals_before_as_of_but_not_a_supplement(tmp_path):
    import json
    import sqlite3

    from pending_events import blocked

    (tmp_path / "derived").mkdir()
    (tmp_path / "review").mkdir()
    events = [
        {"id": "e1", "status": "needs_review", "effective_on": "2020-01-01", "operation": "amend",
         "affected_provision_ids": ["provision:ART"]},
        {"id": "e2", "status": "needs_review", "effective_on": "2020-01-01", "operation": "supplement",
         "affected_provision_ids": ["provision:B"]},
        {"id": "e3", "status": "needs_review", "effective_on": "2030-01-01", "operation": "repeal",
         "affected_provision_ids": ["provision:C"]},
    ]
    (tmp_path / "derived/provision_events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    db = sqlite3.connect(tmp_path / "temporal.sqlite")
    db.execute("CREATE TABLE provisions (id TEXT, parent_id TEXT)")
    db.executemany("INSERT INTO provisions VALUES (?, ?)", [("provision:A", "provision:ART")])
    db.commit()
    rows = [{"id": f"r{x}", "lineage_id": f"provision:{x}", "as_of": "2025-01-01"} for x in "ABC"]
    assert blocked(rows, tmp_path) == {"provision:A"}   # via its Điều; B only gained a sibling; C later
    (tmp_path / "review/pending_events.tsv").write_text("id\tevent_id\tdecision\nrA\te1\tno_effect\n")
    assert blocked(rows, tmp_path) == set()
