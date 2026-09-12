"""WBS-B7b unit tests: W05 retry policy config (ADR-0019 §3)."""

from __future__ import annotations

from datetime import timedelta

from workflows.retry_policy import DEFAULT_RETRY_POLICY, retry_policy_for


def test_default_retry_policy_shape() -> None:
    assert DEFAULT_RETRY_POLICY.maximum_attempts == 5
    assert DEFAULT_RETRY_POLICY.backoff_coefficient == 2.0
    assert DEFAULT_RETRY_POLICY.initial_interval == timedelta(seconds=1)
    assert DEFAULT_RETRY_POLICY.maximum_interval == timedelta(minutes=5)


def test_custom_max_attempts() -> None:
    p = retry_policy_for(max_attempts=10)
    assert p.maximum_attempts == 10


def test_custom_initial_interval() -> None:
    p = retry_policy_for(initial_interval_seconds=2.5)
    assert p.initial_interval == timedelta(seconds=2.5)
