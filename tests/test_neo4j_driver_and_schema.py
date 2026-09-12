from dataclasses import dataclass, field

import pytest

from legal_crawler.adapters.neo4j import (
    Neo4jExecutor,
    initialize_schema,
    schema_statements,
    validate_relation,
)
from legal_crawler.ports import TransactionError
from legal_crawler.temporal import RelationType


class FakeResult:
    def __init__(self, rows=None):
        self.rows = [] if rows is None else rows

    def data(self):
        return self.rows


@dataclass
class FakeTransaction:
    calls: list = field(default_factory=list)
    rows: list = field(default_factory=lambda: [{"ok": True}])
    committed: bool = False
    rolled_back: bool = False
    fail_commit: bool = False
    fail_rollback: bool = False

    def run(self, query, parameters=None):
        self.calls.append((query, dict(parameters or {})))
        return FakeResult(self.rows)

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("commit unavailable")
        self.committed = True

    def rollback(self):
        if self.fail_rollback:
            raise RuntimeError("rollback unavailable")
        self.rolled_back = True


class FakeSession:
    def __init__(self, transaction=None):
        self.transaction = transaction or FakeTransaction()
        self.closed = False
        self.read_calls = 0
        self.write_calls = 0

    def begin_transaction(self):
        return self.transaction

    def execute_read(self, callback):
        self.read_calls += 1
        return callback(self.transaction)

    def execute_write(self, callback):
        self.write_calls += 1
        return callback(self.transaction)

    def close(self):
        self.closed = True


class BeginFailureSession(FakeSession):
    def begin_transaction(self):
        raise RuntimeError("cannot begin")


class FakeDriver:
    def __init__(self, sessions=None):
        self.sessions = list(sessions or [])
        self.created_sessions = []
        self.databases = []
        self.closed = False

    def session(self, *, database):
        self.databases.append(database)
        session = self.sessions.pop(0) if self.sessions else FakeSession()
        self.created_sessions.append(session)
        return session

    def close(self):
        self.closed = True


def test_executor_consumes_read_and_write_inside_short_lived_sessions():
    read_session = FakeSession(FakeTransaction(rows=[{"id": "document:1"}]))
    write_session = FakeSession(FakeTransaction(rows=[{"created": True}]))
    driver = FakeDriver((read_session, write_session))
    executor = Neo4jExecutor(driver, database="legal")

    read_rows = executor.read("MATCH (n) RETURN n.id AS id", {"limit": 1})
    write_rows = executor.write("CREATE (n) RETURN true AS created")

    assert read_rows == ({"id": "document:1"},)
    assert write_rows == ({"created": True},)
    assert read_session.read_calls == 1
    assert read_session.write_calls == 0
    assert write_session.write_calls == 1
    assert read_session.closed and write_session.closed
    assert driver.databases == ["legal", "legal"]


def test_explicit_transaction_routes_all_queries_to_one_transaction_and_commits():
    transaction = FakeTransaction()
    session = FakeSession(transaction)
    executor = Neo4jExecutor(FakeDriver((session,)))

    with executor.transaction():
        assert executor.in_transaction
        executor.read("MATCH (n) RETURN n", {"id": "a"})
        executor.write("CREATE (n)", {"id": "b"})

    assert not executor.in_transaction
    assert transaction.committed
    assert not transaction.rolled_back
    assert len(transaction.calls) == 2
    assert session.read_calls == session.write_calls == 0
    assert session.closed


def test_explicit_transaction_rolls_back_and_preserves_application_error():
    transaction = FakeTransaction()
    session = FakeSession(transaction)
    executor = Neo4jExecutor(FakeDriver((session,)))

    with pytest.raises(ValueError, match="invalid event"):
        with executor.transaction():
            executor.write("CREATE (n)")
            raise ValueError("invalid event")

    assert transaction.rolled_back
    assert not transaction.committed
    assert not executor.in_transaction
    assert session.closed


def test_executor_rejects_nested_transaction_and_close_while_active():
    executor = Neo4jExecutor(FakeDriver())

    with executor.transaction():
        with pytest.raises(TransactionError, match="nested"):
            with executor.transaction():
                pass
        with pytest.raises(TransactionError, match="cannot close"):
            executor.close()


def test_commit_and_rollback_failures_are_backend_neutral_transaction_errors():
    commit_tx = FakeTransaction(fail_commit=True)
    rollback_tx = FakeTransaction(fail_rollback=True)
    executor = Neo4jExecutor(
        FakeDriver((FakeSession(commit_tx), FakeSession(rollback_tx)))
    )

    with pytest.raises(TransactionError, match="commit"):
        with executor.transaction():
            pass
    with pytest.raises(TransactionError, match="rollback failed"):
        with executor.transaction():
            raise ValueError("application failure")


def test_begin_failure_closes_the_session_and_uses_transaction_error():
    session = BeginFailureSession()
    executor = Neo4jExecutor(FakeDriver((session,)))

    with pytest.raises(TransactionError, match="could not begin"):
        with executor.transaction():
            pass

    assert session.closed
    assert not executor.in_transaction


def test_executor_validates_driver_database_query_parameters_and_results():
    with pytest.raises(TypeError, match="Neo4jDriver"):
        Neo4jExecutor(object())
    with pytest.raises(ValueError, match="database"):
        Neo4jExecutor(FakeDriver(), database="")

    bad_result = FakeSession(FakeTransaction(rows=["not-a-record"]))
    executor = Neo4jExecutor(FakeDriver((bad_result,)))
    with pytest.raises(TransactionError, match="list of records"):
        executor.read("MATCH (n) RETURN n")
    with pytest.raises(ValueError, match="query"):
        Neo4jExecutor(FakeDriver()).read("")
    with pytest.raises(TypeError, match="parameters"):
        Neo4jExecutor(FakeDriver()).read("RETURN 1", [])


def test_executor_close_delegates_to_driver():
    driver = FakeDriver()
    executor = Neo4jExecutor(driver)

    executor.close()

    assert driver.closed


def test_schema_contains_domain_constraints_temporal_indexes_and_every_relation():
    statements = schema_statements()
    combined = "\n".join(statements)

    assert "DomainEntity" in combined
    assert "n.id IS UNIQUE" in combined
    assert "n.eff_from, n.eff_to" in combined
    for relation in RelationType:
        assert f"[r:{relation.value}]" in combined


def test_schema_initialization_executes_every_statement_without_swallowing_errors():
    class Recorder:
        def __init__(self):
            self.calls = []

        def write(self, query, parameters):
            self.calls.append((query, parameters))

    recorder = Recorder()

    initialize_schema(recorder)

    assert tuple(query for query, _ in recorder.calls) == schema_statements()
    assert all(parameters == {} for _, parameters in recorder.calls)
    with pytest.raises(TypeError, match="provide write"):
        initialize_schema(object())


def test_relation_validation_allows_only_typed_vocabulary():
    assert validate_relation(RelationType.AMENDS.value) == "AMENDS"
    with pytest.raises(ValueError, match="unsupported"):
        validate_relation("AMENDS`) DELETE n //")
