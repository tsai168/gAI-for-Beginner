"""I03 integration tests (ADR-0025 §3): RedisCache against a *real* Redis —
same "real, not mocked" posture as the Temporal/Postgres-backed tests
elsewhere in this project. Skips (not fails) if REDIS_URL isn't set or the
server isn't reachable, matching test_workflows_temporal.py's precedent
(ADR-0019 §1) for optional infrastructure this sandbox may not have.
"""

from __future__ import annotations

import os
import uuid

import pytest
import redis

from reports.cache import RedisCache, get_cache_backend

pytestmark = pytest.mark.integration

_REDIS_URL = os.environ.get("REDIS_URL")


@pytest.fixture
def redis_cache() -> RedisCache:
    if not _REDIS_URL:
        pytest.skip("REDIS_URL not set — no Redis available in this environment")
    client = redis.Redis.from_url(_REDIS_URL)
    try:
        client.ping()
    except Exception as exc:  # noqa: BLE001 — any connectivity failure -> skip, not fail
        pytest.skip(f"Redis unreachable at REDIS_URL: {exc}")
    return RedisCache(client)


def test_set_then_get_round_trips(redis_cache: RedisCache) -> None:
    key = f"test:{uuid.uuid4()}"
    redis_cache.set(key, "hello", ttl_seconds=30)
    assert redis_cache.get(key) == "hello"
    redis_cache.delete(key)


def test_missing_key_returns_none(redis_cache: RedisCache) -> None:
    assert redis_cache.get(f"test:{uuid.uuid4()}") is None


def test_delete_removes_entry(redis_cache: RedisCache) -> None:
    key = f"test:{uuid.uuid4()}"
    redis_cache.set(key, "v", ttl_seconds=30)
    redis_cache.delete(key)
    assert redis_cache.get(key) is None


def test_get_cache_backend_returns_redis_cache_when_configured(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    if not _REDIS_URL:
        pytest.skip("REDIS_URL not set — no Redis available in this environment")
    monkeypatch.setenv("REDIS_URL", _REDIS_URL)
    assert isinstance(get_cache_backend(), RedisCache)
