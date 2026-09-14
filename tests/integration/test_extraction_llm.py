"""A01 integration test (ADR-0026) against the *real* Anthropic API — same
"real, not mocked" posture as test_cache_redis.py. Skips (not fails) if
ANTHROPIC_API_KEY isn't set, matching the project's standing precedent for
optional infrastructure this sandbox may not have (ADR-0019 §1).

Only checks structural validity (types, ranges) — not semantic correctness.
Whether the model's classification is *right* is not this layer's job, same
posture B12 took for load testing this project has no infra to run for real.
"""

from __future__ import annotations

import os

import pytest

from agents.extraction import AnthropicExtractionClient

pytestmark = pytest.mark.integration

_HAS_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))


@pytest.fixture
def client() -> AnthropicExtractionClient:
    if not _HAS_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set — no real LLM call available in this environment")
    return AnthropicExtractionClient()


def test_extraction_returns_well_formed_candidates(client: AnthropicExtractionClient) -> None:
    system = (
        "You are a test harness. For the single company named 'TestCo "
        "Semiconductor', extract exactly one evidence candidate from the "
        "text below, matching the schema you were given."
    )
    user = (
        "Companies currently tracked by this system:\n- TestCo Semiconductor\n\n"
        "Source snapshot text:\n---\nTestCo Semiconductor announced today "
        "that its new optical transceiver has passed qualification testing "
        "with a major customer.\n---"
    )
    result = client.parse_extraction(system=system, user=user)

    assert len(result.candidates) >= 1
    for candidate in result.candidates:
        assert 0.0 <= candidate.directness <= 1.0
        assert 0.0 <= candidate.independence <= 1.0
        assert 0.0 <= candidate.temporal_quality <= 1.0
        assert 0.0 <= candidate.specificity <= 1.0
        assert candidate.evidence_type is not None
        assert isinstance(candidate.rationale, str) and candidate.rationale
