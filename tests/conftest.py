"""Shared pytest fixtures.

`db_session` is available to tests marked `integration`; it needs a live
Postgres (DATABASE_URL) with migrations applied. Without DATABASE_URL those
tests are skipped.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from knowledge.db.session import get_engine

_HAS_DB = bool(os.environ.get("DATABASE_URL"))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _HAS_DB:
        return
    skip_db = pytest.mark.skip(reason="no DATABASE_URL — integration tests skipped")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_db)


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    return get_engine()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """Function-scoped session on an outer transaction that is always rolled
    back. `create_savepoint` mode lets a test's own rollback (after an
    expected DB error) recover without killing the outer transaction."""
    conn = db_engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()
