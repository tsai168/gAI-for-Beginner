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
from reports.cache import get_cache_backend
from reports.dashboard import _DASHBOARD_CACHE_KEY

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


@pytest.fixture(autouse=True)
def _reset_dashboard_cache() -> None:
    """I03 (ADR-0025 §2): `get_seco_cmi_dashboard`'s list is cached under one
    fixed key, outside any test's DB transaction — with a real, shared
    REDIS_URL (as CI's `integration` job now sets), a value one test caches
    would otherwise leak into whichever test runs next within the TTL. Clear
    it before every test so cache state never crosses test boundaries.
    Per-company keys aren't at risk here: each test's company gets a fresh
    UUID, so they never collide."""
    get_cache_backend().delete(_DASHBOARD_CACHE_KEY)


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
