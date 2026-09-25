"""An accepted effFrom correction reaches the store; the raw record does not change."""
import json
from datetime import date

from legal_crawler.ingest import IngestReport, accepted_effective_from, build_document

RAW = {"docNum": "41/2021/TT-BGTVT", "issueDate": "2021-12-31T00:00:00", "effFrom": "2021-02-15T00:00:00"}


def test_only_accepted_effective_from_decisions_are_applied(tmp_path):
    review = tmp_path / "review"
    review.mkdir()
    rows = [
        {"document_id": "1", "field": "effective_from", "value": "2022-02-15", "decision": "accept"},
        {"document_id": "2", "field": "effective_from", "value": "2022-02-15", "decision": "reject"},
        {"document_id": "3", "field": "effective_to", "value": "2022-02-15", "decision": "accept"},
    ]
    (review / "temporal_candidates.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert accepted_effective_from(tmp_path) == {"1": date(2022, 2, 15)}

    report = IngestReport()
    document = build_document("1", dict(RAW), report, date(2022, 2, 15))
    assert document.effective_from == date(2022, 2, 15) and report["effective_from_corrected"] == 1
    assert build_document("1", dict(RAW), IngestReport()).effective_from == date(2021, 2, 15)
