"""Rule R6: a pending event on the row's provision or any ancestor keeps the row out of test."""
from pending_events import ancestors


def test_a_derived_point_reaches_its_clause_its_article_and_the_tree_above():
    parent_of = {"provision:A": "provision:CH", "provision:CH": "provision:PH"}
    assert ancestors("provision:A#k2#b", parent_of) == [
        "provision:A#k2#b", "provision:A#k2", "provision:A", "provision:CH", "provision:PH"]
    assert ancestors("provision:X", {}) == ["provision:X"]
