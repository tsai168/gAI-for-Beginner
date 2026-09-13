"""I03 unit tests (ADR-0025 §3): InMemoryCache — the default, always-
available backend. RedisCache's own logic is exercised against a real
Redis in tests/integration/test_cache_redis.py (skips without REDIS_URL,
same posture as the Temporal/Postgres-dependent tests elsewhere).
"""

from __future__ import annotations

from reports.cache import InMemoryCache, get_cache_backend


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


def test_get_missing_key_returns_none() -> None:
    cache = InMemoryCache()
    assert cache.get("nope") is None


def test_set_then_get_round_trips() -> None:
    cache = InMemoryCache()
    cache.set("k", "v", ttl_seconds=60)
    assert cache.get("k") == "v"


def test_entry_expires_after_ttl() -> None:
    clock = _FakeClock()
    cache = InMemoryCache(clock=clock)
    cache.set("k", "v", ttl_seconds=10)
    clock.now = 9.999
    assert cache.get("k") == "v"
    clock.now = 10.0
    assert cache.get("k") is None


def test_delete_removes_entry() -> None:
    cache = InMemoryCache()
    cache.set("k", "v", ttl_seconds=60)
    cache.delete("k")
    assert cache.get("k") is None


def test_delete_missing_key_is_a_no_op() -> None:
    cache = InMemoryCache()
    cache.delete("never-set")  # does not raise


def test_get_cache_backend_defaults_to_in_memory(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("REDIS_URL", raising=False)
    backend = get_cache_backend()
    assert isinstance(backend, InMemoryCache)
