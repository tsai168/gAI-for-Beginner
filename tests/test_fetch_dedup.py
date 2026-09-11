"""WBS-B3a unit tests (pure Python): P01 adapter contract + P02 verdict logic.

DB-backed behaviour is in tests/integration/.
"""

from __future__ import annotations

import pytest

from ingestion.dedup import DedupVerdict
from ingestion.fetch import AdapterRegistry, FixtureAdapter, HttpAdapter


def test_fixture_adapter_returns_payload() -> None:
    ad = FixtureAdapter("D01", payloads={"k1": b"hello"})
    r = ad.fetch({"key": "k1"})
    assert r.raw == b"hello"
    assert r.data_source_code == "D01"
    assert r.retrieved_at.tzinfo is not None


def test_fixture_adapter_defaults_to_key_bytes() -> None:
    ad = FixtureAdapter("D02")
    assert ad.fetch({"key": "abc"}).raw == b"abc"


def test_registry_roundtrip() -> None:
    reg = AdapterRegistry()
    ad = FixtureAdapter("D07")
    reg.register(ad)
    assert reg.get("D07") is ad
    with pytest.raises(KeyError):
        reg.get("D99")


def test_http_adapter_base_is_abstract() -> None:
    ad = HttpAdapter("D01", base_url="https://example.invalid")
    with pytest.raises(NotImplementedError):
        ad.fetch({})


def test_dedup_verdict_values() -> None:
    assert {v.value for v in DedupVerdict} == {
        "NEW",
        "DUPLICATE_SAME_SOURCE",
        "DUPLICATE_OTHER_SOURCE",
    }
