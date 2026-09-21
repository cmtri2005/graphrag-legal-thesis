import json
from datetime import date

from compare_consolidated_snapshots import compare, consolidation_edges
from legal_crawler.index import TemporalIndex
from legal_crawler.temporal import LegalDocument, Provision, ProvisionLevel


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_e1_report_separates_exact_mismatch_and_missing_body(tmp_path):
    data = tmp_path / "data"
    (data / "derived").mkdir(parents=True)
    (data / "raw").mkdir()
    with TemporalIndex(data / "temporal.sqlite") as index:
        index.put_documents([
            LegalDocument("document:base", "01/2020/TT-X", "Văn bản gốc",
                          issued_on=date(2020, 1, 1), effective_from=date(2020, 2, 1),
                          source_url="https://source/base"),
            *(LegalDocument(f"document:{name}", f"{name}/VBHN", "Hợp nhất",
                            issued_on=date(2022, 1, 1),
                            source_url=f"https://source/{name}")
              for name in ("exact", "different", "empty")),
        ])
        index.put_provisions([
            Provision("provision:a1", "document:base", ProvisionLevel.ARTICLE,
                      "Điều 1", None),
        ])
    _write_json(data / "raw" / "base.json", {
        "docNum": "01/2020/TT-X", "issueDate": "2020-01-01",
        "isConsolidatedDocument": False,
    })
    for name, text in (
        ("exact", "Điều 1. Quy định chung"),
        ("different", "Điều 1. Quy định mới"),
        ("empty", ""),
    ):
        _write_json(data / "raw" / f"{name}.json", {
            "docNum": f"{name}/VBHN", "title": "Hợp nhất",
            "issueDate": "2022-01-01", "isConsolidatedDocument": True,
            "documentContent": {"content": f"<p>{text}</p>"},
        })
    (data / "edges.jsonl").write_text("".join(
        json.dumps({"source_id": name, "target_id": "base", "reference_type": 7}) + "\n"
        for name in ("exact", "different", "empty")
    ), encoding="utf-8")
    (data / "derived" / "versions.jsonl").write_text(json.dumps({
        "id": "version:a1:1", "provision_id": "provision:a1", "ordinal": 1,
        "text": "Điều 1. Quy định chung", "valid_from": "2020-02-01",
        "valid_to": None, "created_by_event_id": None, "ended_by_event_id": None,
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    (data / "derived" / "provision_events.jsonl").write_text("", encoding="utf-8")

    assert len(consolidation_edges(data / "edges.jsonl")) == 3
    report = compare(data)

    assert report["document_statuses"] == {"compared": 2, "source_body_empty": 1}
    assert report["case_statuses"] == {"exact_text_match": 1, "text_mismatch": 1}
    assert report["comparable_text_units"] == 2
    assert report["exact_match_rate"] == 0.5
    assert all("source_raw_sha256" in row for row in report["documents"])
