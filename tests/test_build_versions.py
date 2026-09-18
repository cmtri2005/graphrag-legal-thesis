import hashlib
import json
from datetime import date

from build_versions import build_version_files
from legal_crawler.index import TemporalIndex
from legal_crawler.storage.documents import DocumentStore
from legal_crawler.temporal import (
    LegalDocument,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    TemporalInterval,
    make_provision_id,
    make_version_id,
)


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_builds_subtree_versions_and_audits_every_event_deterministically(tmp_path):
    data = tmp_path / "data"
    store = DocumentStore(data)
    for document_id in ("target", "actor-a"):
        store.save("raw", document_id, {"title": document_id})
    store.save(
        "derived/subtrees",
        "target",
        {
            "nodes": [
                {
                    "id": "article-1#clause-1",
                    "parent_id": "article-1",
                    "level": "Clause",
                    "title": "Khoản 1",
                    "text": "Nội dung khoản ban đầu.",
                }
            ]
        },
    )

    index_path = data / "temporal.sqlite"
    with TemporalIndex(index_path) as index:
        index.put_documents(
            [
                LegalDocument(
                    "target",
                    "01/2020",
                    "Văn bản gốc",
                    effective_from=date(2020, 1, 1),
                    effective_to=date(2024, 1, 1),
                ),
                LegalDocument("actor-a", "01/2022", "Văn bản A"),
            ]
        )
        index.put_provisions(
            [
                Provision(
                    "article-1",
                    "target",
                    ProvisionLevel.ARTICLE,
                    "Điều 1",
                    None,
                    0,
                ),
                Provision(
                    "article-1#clause-1",
                    "target",
                    ProvisionLevel.CLAUSE,
                    "Khoản 1",
                    "article-1",
                    None,
                ),
            ]
        )
        index.put_versions(
            [
                ProvisionVersion(
                    "article-1:1",
                    "article-1",
                    1,
                    "Nội dung điều ban đầu.",
                    TemporalInterval(date(2020, 1, 1), date(2024, 1, 1)),
                )
            ]
        )

    events = [
        {
            "id": "event:z-update-first",
            "actor_id": "actor-a",
            "operation": "amend",
            "effective_on": "2022-01-01",
            "target_document_id": "target",
            "target_provision_id": "article-1#clause-1",
            "text_updates": [
                {
                    "target_provision_id": "article-1#clause-1",
                    "new_text": "Nội dung khoản sau sửa đổi.",
                }
            ],
            "status": "auto_accepted",
            "status_reason": None,
            "evidence": "Sửa đổi khoản 1.",
        },
        {
            "id": "event:a-update-second",
            "actor_id": "actor-a",
            "operation": "amend",
            "effective_on": "2022-01-01",
            "target_document_id": "target",
            "target_provision_id": "article-1#clause-1",
            "text_updates": [
                {
                    "target_provision_id": "article-1#clause-1",
                    "new_text": "Không được âm thầm áp dụng.",
                }
            ],
            "status": "auto_accepted",
            "status_reason": None,
            "evidence": "Sửa đổi trùng ngày.",
        },
        {
            "id": "event:repeal",
            "actor_id": "actor-a",
            "operation": "repeal",
            "effective_on": "2023-01-01",
            "target_document_id": "target",
            "target_provision_id": "article-1",
            "text_updates": [],
            "status": "verified",
            "status_reason": None,
            "evidence": "Bãi bỏ Điều 1.",
        },
        {
            "id": "event:review",
            "actor_id": "actor-a",
            "operation": "replace",
            "effective_on": "2023-06-01",
            "target_document_id": "target",
            "target_provision_id": "article-1",
            "text_updates": [],
            "status": "needs_review",
            "status_reason": "missing_resulting_text",
            "evidence": "Ca chưa đủ bằng chứng.",
        },
    ]
    event_store = data / "derived" / "provision_events.jsonl"
    event_store.parent.mkdir(parents=True, exist_ok=True)
    event_store.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in events),
        encoding="utf-8",
    )

    versions_path = data / "derived" / "versions.jsonl"
    log_path = data / "derived" / "event_log.jsonl"
    first = build_version_files(data, index_path, versions_path, log_path)
    first_hashes = (_sha256(versions_path), _sha256(log_path))
    second = build_version_files(data, index_path, versions_path, log_path)

    assert first == second
    assert first_hashes == (_sha256(versions_path), _sha256(log_path))
    assert first["events_applied"] == 2
    assert first["events_rejected"] == 2

    versions = _jsonl(versions_path)
    by_id = {row["id"]: row for row in versions}
    article_id = make_provision_id("article-1")
    clause_id = make_provision_id("article-1#clause-1")
    article_v1 = by_id[make_version_id(article_id, 1)]
    clause_v1 = by_id[make_version_id(clause_id, 1)]
    clause_v2 = by_id[make_version_id(clause_id, 2)]
    assert article_v1["valid_to"] == "2023-01-01"
    assert article_v1["ended_by_event_id"] == "event:repeal"
    assert clause_v1["valid_to"] == "2022-01-01"
    assert clause_v2["valid_to"] is None
    assert clause_v2["created_by_event_id"] == "event:z-update-first"

    logs = {row["event_id"]: row for row in _jsonl(log_path)}
    assert logs["event:z-update-first"]["outcome"] == "applied"
    assert logs["event:a-update-second"]["reason"] == "event_not_after_version_start"
    assert logs["event:repeal"]["outcome"] == "applied"
    assert logs["event:review"]["reason"] == "status_not_applicable"
