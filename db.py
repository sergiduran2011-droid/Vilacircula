from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def is_postgres_url(url: str | None) -> bool:
    return bool(url and url.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://", "postgres://")))


class PostgresConnection:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, statement: str, parameters: tuple[Any, ...] = ()) -> Any:
        statement = statement.replace("BEGIN IMMEDIATE", "BEGIN").replace("?", "%s")
        try:
            return self._connection.execute(statement, parameters)
        except Exception as error:
            if (getattr(error, "sqlstate", "") or "").startswith("23"):
                raise sqlite3.IntegrityError(str(error)) from error
            raise

    def executescript(self, script: str) -> None:
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self) -> None:
        self.execute("COMMIT")

    def rollback(self) -> None:
        self.execute("ROLLBACK")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)


def connect_database(database_url: str, database_path: str | Path) -> Any:
    if not is_postgres_url(database_url):
        connection = sqlite3.connect(str(database_path), timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    import psycopg
    from psycopg.rows import dict_row

    url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    url = url.replace("postgres://", "postgresql://", 1)
    separator = "&" if "?" in url else "?"
    if "sslmode=" not in url:
        url = f"{url}{separator}sslmode=require"
    connection = psycopg.connect(url, autocommit=True, row_factory=dict_row, prepare_threshold=None)
    return PostgresConnection(connection)