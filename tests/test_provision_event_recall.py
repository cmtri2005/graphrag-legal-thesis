"""Recall must not silently count review-only events as applicable."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "measure_events", Path(__file__).parents[1] / "scripts/check/measure_provision_events.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_extracted_and_applicable_are_separate():
    gold = {("d", "p1"), ("d", "p2"), ("other", "p3")}
    events = [
        {"target_document_id": "d", "affected_provision_ids": ["p1"],
         "operation": "amend", "status": "needs_review", "locator": [["Điều", "1"]]},
        {"target_document_id": "d", "affected_provision_ids": [],
         "operation": "repeal", "status": "needs_review", "locator": None},
    ]
    result = module.recall_diagnostics(events, gold)
    assert result["extracted_covered"] == 1
    assert result["applicable_covered"] == 0
    assert result["missing_reasons"] == {
        "document_scope_mention_only_for_pair": 1, "no_target_event": 1}
    events[0]["status"] = "verified"
    assert module.recall_diagnostics(events, gold)["applicable_covered"] == 1


def test_supplement_does_not_end_a_version():
    events = [{"target_document_id": "d", "affected_provision_ids": ["p"],
               "operation": "supplement", "status": "auto_accepted", "locator": []}]
    result = module.recall_diagnostics(events, {("d", "p")})
    assert result["extracted_covered"] == result["applicable_covered"] == 0
    assert module.recall_diagnostics([], set())["extracted_recall"] is None


def test_gold_readiness_requires_wording_for_in_force(tmp_path):
    path = tmp_path / 'gold_A.tsv'
    path.write_text('hieu_luc\tnoi_dung\n' 'còn\t\n' 'còn\tĐiều khoản\n'
                    'không\t\n' 'không rõ\t\n' '\t\n', encoding='utf-8')
    assert module.gold_readiness(tmp_path)[str(path)] == {'requested': 5, 'filled': 3}
