"""Small synchronous Neo4j driver boundary with explicit transactions."""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Protocol, runtime_checkable

from legal_crawler.ports import TransactionError


class Neo4jDependencyError(RuntimeError):
    """The optional official Neo4j driver is unavailable."""


@runtime_checkable
class Neo4jResult(Protocol):
    def data(self) -> list[dict[str, Any]]:
        ...


@runtime_checkable
class Neo4jTransaction(Protocol):
    def run(
        self,
        query: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> Neo4jResult:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


@runtime_checkable
class Neo4jSession(Protocol):
    def begin_transaction(self) -> Neo4jTransaction:
        ...

    def execute_read(self, callback):
        ...

    def execute_write(self, callback):
        ...

    def close(self) -> None:
        ...


@runtime_checkable
class Neo4jDriver(Protocol):
    def session(self, *, database: str) -> Neo4jSession:
        ...

    def close(self) -> None:
        ...


class Neo4jExecutor:
    """Consume query results inside the owning session or transaction."""

    def __init__(self, driver: Neo4jDriver, *, database: str = "neo4j") -> None:
        if not isinstance(driver, Neo4jDriver):
            raise TypeError("driver must satisfy Neo4jDriver")
        if not isinstance(database, str) or not database.strip():
            raise ValueError("database must not be empty")
        self._driver = driver
        self._database = database
        self._transaction: Neo4jTransaction | None = None
        self._session: Neo4jSession | None = None

    @classmethod
    def from_uri(
        cls,
        uri: str,
        username: str,
        password: str,
        *,
        database: str = "neo4j",
    ) -> "Neo4jExecutor":
        """Construct the official driver only when the optional extra exists."""
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise Neo4jDependencyError(
                "install the 'neo4j' project extra to use Neo4j storage"
            ) from exc
        driver = GraphDatabase.driver(uri, auth=(username, password))
        return cls(driver, database=database)

    @property
    def in_transaction(self) -> bool:
        return self._transaction is not None

    def read(
        self,
        query: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Run and fully consume a read before its session can close."""
        params = {} if parameters is None else parameters
        return self._run(query, params, write=False)

    def write(
        self,
        query: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Run and fully consume a write before its session can close."""
        params = {} if parameters is None else parameters
        return self._run(query, params, write=True)

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Bind repository calls to one explicit ACID transaction."""
        if self.in_transaction:
            raise TransactionError("nested Neo4j transactions are not supported")
        session: Neo4jSession | None = None
        try:
            session = self._driver.session(database=self._database)
            transaction = session.begin_transaction()
        except Exception as exc:
            if session is not None:
                session.close()
            raise TransactionError("could not begin Neo4j transaction") from exc
        self._session = session
        self._transaction = transaction
        try:
            yield None
        except BaseException:
            try:
                transaction.rollback()
            except Exception as rollback_error:
                raise TransactionError(
                    "Neo4j rollback failed after an application error"
                ) from rollback_error
            raise
        else:
            try:
                transaction.commit()
            except Exception as exc:
                raise TransactionError("could not commit Neo4j transaction") from exc
        finally:
            self._transaction = None
            self._session = None
            session.close()

    def close(self) -> None:
        if self.in_transaction:
            raise TransactionError("cannot close Neo4j driver during a transaction")
        self._driver.close()

    def _run(
        self,
        query: str,
        parameters: Mapping[str, Any],
        *,
        write: bool,
    ) -> tuple[dict[str, Any], ...]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty")
        if not isinstance(parameters, Mapping):
            raise TypeError("parameters must be a mapping")
        params = dict(parameters)
        if self._transaction is not None:
            return _consume(self._transaction.run(query, params))

        session = self._driver.session(database=self._database)
        try:
            callback = lambda transaction: _consume(
                transaction.run(query, params)
            )
            if write:
                return session.execute_write(callback)
            return session.execute_read(callback)
        finally:
            session.close()


def _consume(result: Neo4jResult) -> tuple[dict[str, Any], ...]:
    rows = result.data()
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise TransactionError("Neo4j result.data() must return a list of records")
    return tuple(dict(row) for row in rows)
