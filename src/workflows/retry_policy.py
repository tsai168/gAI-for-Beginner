"""W05 — Retry / timeout policy (WBS-B7b, ADR-0019 §3, Charter §22 Auditability).

"Retryable without duplicate writes" is guaranteed by the idempotent design
of the modules this wraps (P03 record_snapshot's unique
source_id+content_hash, the CFL state machine rejecting illegal
transitions, the Event Revision Chain only accepting head nodes) — not
reinvented here. This module only configures the retry/backoff schedule.
"""

from __future__ import annotations

from datetime import timedelta

from temporalio.common import RetryPolicy

_BACKOFF_COEFFICIENT = 2.0
_MAXIMUM_INTERVAL = timedelta(minutes=5)
_DEFAULT_MAX_ATTEMPTS = 5
_DEFAULT_INITIAL_INTERVAL_SECONDS = 1.0


def retry_policy_for(
    *,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    initial_interval_seconds: float = _DEFAULT_INITIAL_INTERVAL_SECONDS,
) -> RetryPolicy:
    return RetryPolicy(
        initial_interval=timedelta(seconds=initial_interval_seconds),
        backoff_coefficient=_BACKOFF_COEFFICIENT,
        maximum_interval=_MAXIMUM_INTERVAL,
        maximum_attempts=max_attempts,
    )


DEFAULT_RETRY_POLICY = retry_policy_for()
