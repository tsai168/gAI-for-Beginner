"""P01 — Crawler / API fetcher (WBS-B3a).

Deterministic (L0): retrieve raw bytes from a source and register a
``source`` row + immutable ``source_snapshot`` (via P03). No LLM.

Concrete site adapters (TWSE / TPEx / MOPS / TDCC ...) are **deferred**
until ``docs/audit/DATA_AVAILABILITY_AUDIT.md`` is filled (ADR-0009).
``FixtureAdapter`` and the ``HttpAdapter`` base are provided now.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

import httpx
from sqlalchemy.orm import Session

from ingestion.dedup import DedupVerdict, classify
from ingestion.snapshot import record_snapshot
from knowledge.db.models import Source, SourceSnapshot


@dataclass(slots=True)
class FetchResult:
    data_source_code: str
    raw: bytes
    retrieved_at: datetime
    url: str | None = None
    title: str | None = None
    publisher: str | None = None
    source_ref: str | None = None
    published_at: datetime | None = None
    content_type: str | None = None
    parser_version: str | None = None
    source_version: str | None = None


class SourceAdapter(Protocol):
    """Maps request params to raw content for one ``data_source`` code."""

    data_source_code: str

    def fetch(self, params: dict[str, object]) -> FetchResult: ...


@dataclass(slots=True)
class FixtureAdapter:
    """Test/local adapter: returns bytes handed to it, no I/O."""

    data_source_code: str
    payloads: dict[str, bytes] = field(default_factory=dict)

    def fetch(self, params: dict[str, object]) -> FetchResult:
        key = str(params.get("key", ""))
        raw = self.payloads.get(key, key.encode("utf-8"))
        return FetchResult(
            data_source_code=self.data_source_code,
            raw=raw,
            retrieved_at=datetime.now(UTC),
            url=str(params.get("url")) if params.get("url") else None,
            source_ref=key or None,
        )


@dataclass(slots=True)
class HttpAdapter:
    """Reusable GET base. Subclasses build the URL and parse params; this
    class does not know any specific site (endpoints are Deferred)."""

    data_source_code: str
    base_url: str
    user_agent: str = "cpo-ai-ingestion/0"
    min_interval_s: float = 1.0
    _last_call: float = field(default=0.0, init=False, repr=False)

    def _throttle(self) -> None:
        wait = self.min_interval_s - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def _get(
        self, path: str, query: dict[str, str | int | float | bool | None] | None = None
    ) -> httpx.Response:
        self._throttle()
        with httpx.Client(
            base_url=self.base_url, headers={"User-Agent": self.user_agent}, timeout=30.0
        ) as client:
            resp = client.get(path, params=query)
        resp.raise_for_status()
        return resp

    def fetch(self, params: dict[str, object]) -> FetchResult:  # pragma: no cover - base
        raise NotImplementedError("concrete site adapter required (ADR-0009)")


class AdapterRegistry:
    def __init__(self) -> None:
        self._by_code: dict[str, SourceAdapter] = {}

    def register(self, adapter: SourceAdapter) -> None:
        self._by_code[adapter.data_source_code] = adapter

    def get(self, data_source_code: str) -> SourceAdapter:
        return self._by_code[data_source_code]


@dataclass(slots=True)
class Registered:
    source: Source
    snapshot: SourceSnapshot
    verdict: DedupVerdict


def fetch_and_register(
    session: Session,
    adapter: SourceAdapter,
    params: dict[str, object],
) -> Registered:
    """P01 -> P02 -> P03. Always records the source row; the snapshot is
    deduped (P03 idempotent) and classified (P02)."""
    result = adapter.fetch(params)
    verdict = classify(session, raw=result.raw)

    source = Source(
        data_source_code=result.data_source_code,
        url=result.url,
        title=result.title,
        publisher=result.publisher,
        source_ref=result.source_ref,
        published_at=result.published_at,
        retrieved_at=result.retrieved_at,
        parser_version=result.parser_version,
        source_version=result.source_version,
    )
    session.add(source)
    session.flush()

    snapshot = record_snapshot(
        session,
        source_id=source.source_id,
        raw=result.raw,
        retrieved_at=result.retrieved_at,
        content_type=result.content_type,
        parser_version=result.parser_version,
        source_version=result.source_version,
    )
    return Registered(source=source, snapshot=snapshot, verdict=verdict)
