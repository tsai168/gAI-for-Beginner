"""I03 — Cache layer (post-B12 addendum, ADR-0025 §3; originally deferred
to B5 by ADR-0005 — "I03（快取）→ B5：Seco/CMI 儀表板讀取需要時才加", concrete
tech choice explicitly left open until then: "I03 快取具體技術（Redis／
其他）——B5 定"). Filled in now.

Only R03's dashboard reads are cached (Work-1 §3.10: "高頻讀取（Dashboard／
Seco/CMI）加速") — nothing else in this codebase reads frequently enough to
need one.

TTL-bounded, not invalidate-on-write: M03/M04 (Work-1's D/P/K/M/A/W/R/G/U/I
layer order — lower than R) would have to depend on R03 to invalidate a
cache entry on write, inverting the module dependency direction. A short
default TTL keeps the staleness window small and bounded instead — an
explicit, documented tradeoff, not an oversight.

Two backends, chosen by whether `REDIS_URL` is configured (same
opt-in-or-degrade posture as `API_CORS_ORIGINS`, `OIDC_ISSUER`, ...):
- `InMemoryCache` — default, zero infra, per-process only. Always
  available, always used in tests unless a real `REDIS_URL` is set.
- `RedisCache` — shared across processes/workers, what an actual multi-
  worker deployment needs; used automatically once `REDIS_URL` is set.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Protocol

import redis as _redis


class CacheBackend(Protocol):
    def get(self, key: str) -> str | None: ...

    def set(self, key: str, value: str, *, ttl_seconds: int) -> None: ...

    def delete(self, key: str) -> None: ...


class InMemoryCache:
    """Per-process TTL cache — no infrastructure required. `clock` is
    injectable so tests can control expiry deterministically instead of
    sleeping."""

    def __init__(self, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._store: dict[str, tuple[float, str]] = {}  # key -> (expires_at, value)

    def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if self._clock() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        self._store[key] = (self._clock() + ttl_seconds, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class RedisCache:
    """Thin wrapper over a `redis.Redis`-shaped client (duck-typed via
    `_RedisLike` so tests can substitute a fake without a real server)."""

    def __init__(self, client: _RedisLike) -> None:
        self._client = client

    def get(self, key: str) -> str | None:
        value = self._client.get(key)
        if value is None:
            return None
        return value.decode("utf-8") if isinstance(value, bytes) else str(value)

    def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        self._client.setex(key, ttl_seconds, value)

    def delete(self, key: str) -> None:
        self._client.delete(key)


class _RedisLike(Protocol):
    def get(self, key: str) -> bytes | str | None: ...

    def setex(self, key: str, ttl_seconds: int, value: str) -> object: ...

    def delete(self, key: str) -> object: ...


_default_in_memory_cache = InMemoryCache()


def get_cache_backend() -> CacheBackend:
    """`REDIS_URL` unset (the default) -> a process-wide in-memory cache;
    set -> a real Redis-backed one."""
    url = os.environ.get("REDIS_URL")
    if not url:
        return _default_in_memory_cache
    return RedisCache(_redis.Redis.from_url(url))
