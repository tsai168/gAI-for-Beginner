"""A01 unit tests (ADR-0026): the pure-Python pieces — no DB, no LLM call.
DB-writing behavior is in tests/integration/test_extraction.py (real
Postgres + a fake LLMClient); a real Claude call is in
tests/integration/test_extraction_llm.py (skips without ANTHROPIC_API_KEY).
"""

from __future__ import annotations

from agents.extraction import authority_from_source_tier


def test_authority_from_source_tier_known_tiers() -> None:
    assert authority_from_source_tier("S1") == 1.0
    assert authority_from_source_tier("S5") == 0.2


def test_authority_from_source_tier_none_is_none() -> None:
    assert authority_from_source_tier(None) is None


def test_authority_from_source_tier_unknown_tier_is_none() -> None:
    assert authority_from_source_tier("S9") is None
