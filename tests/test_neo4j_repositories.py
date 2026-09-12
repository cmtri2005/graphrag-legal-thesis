from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import date

import pytest

from legal_crawler.adapters.neo4j import Neo4jExecutor, Neo4jUnitOfWork
from legal_crawler.application import RepositoryEventApplicationService
from legal_crawler.ports import (
    EntityNotFoundError,
    RepositoryConflictError,
    RepositoryIntegrityError,
    TemporalUnitOfWork,
    WriteDisposition,
)
from legal_crawler.temporal import (
    EventStatus,
    ExtractionMethod,
    GraphEdge,
    LegalDocument,
    LegalEvent,
    LegalOperation,
    Provenance,
    Provision,
    ProvisionLevel,
    ProvisionVersion,
    RelationType,
    TemporalInterval,
)


@dataclass
class GraphState:
    nodes: dict[str, dict] = field(default_factory=dict)
    edges: dict[str, dict] = field(default_factory=dict)

    def copy(self):
        return deepcopy(self)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def data(self):
        return self._rows


class GraphTransaction:
    def __init__(self, driver, state):
        self.driver = driver
        self.state = state
        self.finished = False

    def run(self, query, parameters=None):
        return FakeResult(self._execute(query, dict(parameters or {})))

    def commit(self):
        self.driver.state = self.state
        self.finished = True

    def rollback(self):
        self.finished = True

    def _execute(self, query, params):
        tag = next(
            (line.strip()[3:] for line in query.splitlines() if line.strip().startswith("// ")),
            None,
        )
        if tag == "node.get":
            node = self.state.nodes.get(params["id"])
            return (
                [{"node": deepcopy(node)}]
                if node and node["kind"] == params["kind"]
                else []
            )
        if tag == "node.get_many":
            return [
                {"node": deepcopy(self.state.nodes[identifier])}
                for identifier in params["ids"]
                if identifier in self.state.nodes
                and self.state.nodes[identifier]["kind"] == params["kind"]
            ]
        if tag == "node.put":
            existing = self.state.nodes.get(params["id"])
            if existing is None:
                existing = {
                    "id": params["id"],
                    "kind": params["kind"],
                    "payload": params["payload"],
                    **deepcopy(params["properties"]),
                }
                self.state.nodes[params["id"]] = existing
                created = True
            else:
                created = False
            return [
                {
                    "created": created,
                    "persisted_kind": existing["kind"],
                    "persisted_payload": existing["payload"],
                }
            ]
        if tag == "node.list":
            filters = params["filters"]
            return [
                {"node": deepcopy(node)}
                for node in self.state.nodes.values()
                if node["kind"] == params["kind"]
                and all(node.get(item["name"]) == item["value"] for item in filters)
            ]
        if tag == "document.list_effective_at":
            at = params["at"]
            nodes = (
                node
                for node in self.state.nodes.values()
                if node["kind"] == params["kind"]
                and (node.get("eff_from") is None or node["eff_from"] <= at)
                and (node.get("eff_to") is None or at < node["eff_to"])
            )
            return [{"node": deepcopy(node)} for node in sorted(nodes, key=lambda n: n["id"])]
        if tag == "version.lock_chain":
            node = self.state.nodes.get(params["provision_id"])
            if node and node["kind"] == params["provision_kind"]:
                return [{"provision_id": node["id"]}]
            return []
        if tag == "version.replace_closed":
            node = self.state.nodes.get(params["id"])
            if not node or node["kind"] != params["kind"]:
                return []
            if node["payload"] != params["expected_payload"]:
                return []
            node["payload"] = params["closed_payload"]
            node.update(deepcopy(params["properties"]))
            return [{"payload": node["payload"]}]
        if tag == "event.list":
            nodes = self._events(params)
            nodes = [node for node in nodes if node.get(params["field"]) == params["value"]]
            return self._event_rows(nodes)
        if tag == "event.list_for_provision":
            nodes = self._events(params)
            nodes = [
                node
                for node in nodes
                if params["provision_id"] in node.get("resolved_target_ids", [])
            ]
            return self._event_rows(nodes)
        if tag == "event.is_applied":
            node = self.state.nodes.get(params["id"])
            if not node or node["kind"] != params["kind"]:
                return []
            return [{"applied": node.get("applied", False)}]
        if tag == "event.mark_applied":
            node = self.state.nodes.get(params["id"])
            if not node or node["kind"] != params["kind"]:
                return []
            changed = not node.get("applied", False)
            node["applied"] = True
            return [{"changed": changed}]
        if tag == "edge.put":
            if (
                params["source_id"] not in self.state.nodes
                or params["target_id"] not in self.state.nodes
            ):
                return []
            existing = self.state.edges.get(params["id"])
            if existing is None:
                existing = {
                    "id": params["id"],
                    "source_id": params["source_id"],
                    "target_id": params["target_id"],
                    "relation": params["relation"],
                    "payload": params["payload"],
                    **deepcopy(params["properties"]),
                }
                self.state.edges[params["id"]] = existing
                created = True
            else:
                created = False
            return [{"created": created, "persisted_payload": existing["payload"]}]
        if tag == "edge.get":
            edge = self.state.edges.get(params["id"])
            return [{"edge": deepcopy(edge)}] if edge else []
        if tag == "edge.list":
            edges = [edge for edge in self.state.edges.values() if self._edge_matches(edge, params)]
            return [{"edge": deepcopy(edge)} for edge in sorted(edges, key=lambda e: e["id"])]
        if tag == "provenance.get_entity":
            return [
                {
                    "node": deepcopy(self.state.nodes.get(params["id"])),
                    "edge": deepcopy(self.state.edges.get(params["id"])),
                }
            ]
        return []

    def _events(self, params):
        return [
            node
            for node in self.state.nodes.values()
            if node["kind"] == params["kind"]
            and (params["start"] is None or (node.get("effective_on") or "") >= params["start"])
            and (
                params["end"] is None
                or (node.get("effective_on") or "9999-12-31") < params["end"]
            )
        ]

    @staticmethod
    def _event_rows(nodes):
        ordered = sorted(
            nodes,
            key=lambda node: (
                node.get("effective_on") or "9999-12-31",
                node["id"],
            ),
        )
        return [{"node": deepcopy(node)} for node in ordered]

    @staticmethod
    def _edge_matches(edge, params):
        node_id = params["node_id"]
        direction = params["direction"]
        directed = {
            "outgoing": edge["source_id"] == node_id,
            "incoming": edge["target_id"] == node_id,
            "neighbors": edge["source_id"] == node_id or edge["target_id"] == node_id,
        }[direction]
        if not directed:
            return False
        if (
            params["relations"] is not None
            and edge["relation"] not in params["relations"]
        ):
            return False
        at = params["at"]
        if at is None or edge.get("eff_from") is None:
            return True
        return edge["eff_from"] <= at and (
            edge.get("eff_to") is None or at < edge["eff_to"]
        )


class GraphSession:
    def __init__(self, driver):
        self.driver = driver
        self.closed = False

    def begin_transaction(self):
        return GraphTransaction(self.driver, self.driver.state.copy())

    def execute_read(self, callback):
        return callback(GraphTransaction(self.driver, self.driver.state.copy()))

    def execute_write(self, callback):
        transaction = GraphTransaction(self.driver, self.driver.state.copy())
        result = callback(transaction)
        transaction.commit()
        return result

    def close(self):
        self.closed = True


class GraphDriver:
    def __init__(self):
        self.state = GraphState()
        self.closed = False

    def session(self, *, database):
        assert database
        return GraphSession(self)

    def close(self):
        self.closed = True


@pytest.fixture
def uow():
    return Neo4jUnitOfWork(Neo4jExecutor(GraphDriver(), database="legal"))


def documents():
    return (
        LegalDocument(
            "document:law",
            "01/2020/QH",
            "Luật kiểm thử",
            effective_from=date(2020, 1, 1),
        ),
        LegalDocument(
            "document:source",
            "02/2024/QH",
            "Luật sửa đổi",
            effective_from=date(2024, 7, 1),
        ),
    )


def provisions():
    article = Provision(
        "provision:article-1",
        "document:law",
        ProvisionLevel.ARTICLE,
        "Điều 1",
        None,
        order_index=1,
    )
    clause = Provision(
        "provision:clause-1",
        "document:law",
        ProvisionLevel.CLAUSE,
        "Khoản 1",
        article.id,
        order_index=1,
    )
    return article, clause


def initial_version():
    evidence = Provenance(
        "document:source",
        ExtractionMethod.RULE,
        evidence_text="Khoản 1 Điều 1 được sửa đổi như sau...",
    )
    return ProvisionVersion(
        "version:clause-1:1",
        "provision:clause-1",
        1,
        "Nội dung ban đầu.",
        TemporalInterval(date(2020, 1, 1)),
        provenance=(evidence,),
    )


def seed(uow):
    uow.documents.put_many(documents())
    article, clause = provisions()
    uow.provisions.put_many((clause, article))
    uow.versions.put_many(
        (
            ProvisionVersion(
                "version:article-1:1",
                article.id,
                1,
                "Nội dung Điều 1.",
                TemporalInterval(date(2020, 1, 1)),
            ),
            initial_version(),
        )
    )


def amendment(identifier="event:amend"):
    return LegalEvent(
        identifier,
        LegalOperation.AMEND,
        "document:source",
        "document:law",
        date(2024, 7, 1),
        ("provision:clause-1",),
        new_text="Nội dung sau sửa đổi.",
        status=EventStatus.VERIFIED,
    )


def test_neo4j_bundle_satisfies_port_and_transaction_contracts(uow):
    assert isinstance(uow, TemporalUnitOfWork)

    document = documents()[0]
    assert uow.documents.put(document).disposition is WriteDisposition.CREATED
    assert uow.documents.put(document).disposition is WriteDisposition.UNCHANGED
    with pytest.raises(RepositoryConflictError):
        uow.documents.put(replace(document, title="Xung đột"))

    with pytest.raises(RuntimeError, match="abort"):
        with uow.transaction():
            uow.documents.put(documents()[1])
            raise RuntimeError("abort")
    assert uow.documents.get("document:source") is None


def test_neo4j_document_reads_are_half_open_and_batch_conflict_rolls_back(uow):
    document = replace(documents()[0], effective_to=date(2024, 1, 1))
    uow.documents.put(document)

    assert uow.documents.get_many((document.id, "document:missing")) == {
        document.id: document
    }
    assert uow.documents.list_effective_at(date(2023, 12, 31)) == (document,)
    assert uow.documents.list_effective_at(date(2024, 1, 1)) == ()

    with pytest.raises(RepositoryConflictError):
        uow.documents.put_many(
            (
                documents()[1],
                replace(document, title="Xung đột"),
            )
        )
    assert uow.documents.get("document:source") is None


def test_neo4j_batches_are_atomic_and_resolve_structural_dependencies(uow):
    uow.documents.put(documents()[0])
    article, clause = provisions()

    result = uow.provisions.put_many((clause, article))

    assert result.created_ids == (clause.id, article.id)
    assert uow.provisions.document_order("document:law") == (article, clause)
    assert uow.provisions.descendants_of(article.id) == (clause,)

    with pytest.raises(RepositoryIntegrityError):
        uow.provisions.put_many(
            (
                Provision(
                    "provision:valid",
                    "document:law",
                    ProvisionLevel.ARTICLE,
                    "Điều 2",
                    None,
                ),
                Provision(
                    "provision:invalid",
                    "document:law",
                    ProvisionLevel.CLAUSE,
                    "Khoản lỗi",
                    "provision:missing",
                ),
            )
        )
    assert uow.provisions.get("provision:valid") is None


def test_neo4j_version_chain_closure_and_snapshot_are_temporal(uow):
    seed(uow)
    before = initial_version()
    closed = replace(
        before,
        validity=TemporalInterval(date(2020, 1, 1), date(2024, 7, 1)),
        ended_by_event_id="event:amend",
    )

    assert uow.versions.replace_closed(before, closed).changed
    assert not uow.versions.replace_closed(before, closed).changed
    assert uow.snapshots.snapshot(before.provision_id, date(2024, 6, 30)).text == before.text
    assert uow.snapshots.snapshot(before.provision_id, date(2024, 7, 1)).text is None

    event = amendment()
    uow.events.put(event)
    assert (
        uow.snapshots.snapshot(before.provision_id, date(2024, 7, 1)).caused_by_event
        is None
    )
    uow.events.mark_applied(event.id)
    assert (
        uow.snapshots.snapshot(before.provision_id, date(2024, 7, 1)).caused_by_event
        == event
    )

    with pytest.raises(RepositoryIntegrityError):
        uow.versions.put(
            ProvisionVersion(
                "version:overlap",
                before.provision_id,
                2,
                "Chồng lấn",
                TemporalInterval(date(2024, 1, 1)),
            )
        )


def test_neo4j_event_queries_application_state_and_missing_event(uow):
    uow.documents.put_many(documents())
    event = amendment()
    uow.events.put(event)

    interval = TemporalInterval(date(2024, 1, 1), date(2025, 1, 1))
    assert uow.events.list_by_source_document(
        "document:source",
        effective_during=interval,
    ) == (event,)
    assert uow.events.list_for_provision("provision:clause-1") == (event,)
    assert uow.events.mark_applied(event.id)
    assert not uow.events.mark_applied(event.id)
    assert uow.events.is_applied(event.id)
    with pytest.raises(EntityNotFoundError):
        uow.events.mark_applied("event:missing")


def test_neo4j_graph_enforces_endpoints_and_filters_half_open_edges(uow):
    uow.documents.put_many(documents())
    edge = GraphEdge(
        "document:source",
        "document:law",
        RelationType.AMENDS,
        TemporalInterval(date(2024, 1, 1), date(2025, 1, 1)),
    )
    edge_id = uow.graph.put(edge).entity_id

    assert uow.graph.get(edge_id) == edge
    assert uow.graph.put(edge).disposition is WriteDisposition.UNCHANGED
    assert uow.graph.outgoing(
        "document:source",
        relations=frozenset({RelationType.AMENDS}),
        at=date(2024, 12, 31),
    ) == (edge,)
    assert uow.graph.outgoing("document:source", at=date(2025, 1, 1)) == ()
    with pytest.raises(EntityNotFoundError):
        uow.graph.put(GraphEdge("missing", "document:law", RelationType.REFERS_TO))

    conflicting = replace(edge, properties={"classification": "conflict"})
    with pytest.raises(RepositoryConflictError):
        uow.graph.put_many(
            (
                GraphEdge(
                    "document:law",
                    "document:source",
                    RelationType.REFERS_TO,
                ),
                conflicting,
            )
        )
    assert uow.graph.outgoing("document:law") == ()


def test_neo4j_provenance_aggregates_versions_for_stable_provision(uow):
    seed(uow)
    version = initial_version()

    assert uow.provenance.for_entity(version.id) == version.provenance
    assert uow.provenance.for_entity(version.provision_id) == version.provenance
    assert uow.provenance.for_entity("missing") == ()


def test_repository_event_application_commits_all_neo4j_writes_atomically(uow):
    seed(uow)
    event = amendment()

    result = RepositoryEventApplicationService(uow).apply(event)

    assert result.applied
    assert uow.events.is_applied(event.id)
    assert (
        uow.snapshots.snapshot("provision:clause-1", date(2024, 6, 30)).text
        == "Nội dung ban đầu."
    )
    assert (
        uow.snapshots.snapshot("provision:clause-1", date(2024, 7, 1)).text
        == "Nội dung sau sửa đổi."
    )
    assert uow.graph.outgoing(
        event.id,
        relations=frozenset({RelationType.AMENDS}),
    )
