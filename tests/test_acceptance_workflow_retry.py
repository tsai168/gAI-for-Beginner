"""TEST-WF-01, part 1 of 2 (Work-3 §4, WBS-B12, ADR-0024 §2): W05's retry
policy actually makes Temporal retry a failing activity until it
succeeds — a real execution, same posture as test_workflows_temporal.py
(WBS-B7b): skips instead of failing if the time-skipping test server isn't
available in this environment.

Part 2 ("no duplicate writes") is a separate, pure-Postgres test —
tests/integration/test_acceptance_idempotent_writes.py — since no single
CI job in this project has both a Temporal test server and Postgres
available at once.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
import pytest_asyncio
from temporalio import activity, workflow
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from workflows.retry_policy import retry_policy_for

pytestmark = pytest.mark.temporal

_ATTEMPTS: dict[str, int] = {}
_SUCCEED_ON_ATTEMPT = 3


@activity.defn(name="_flaky_downstream_call")
async def _flaky_downstream_call(key: str) -> str:
    _ATTEMPTS[key] = _ATTEMPTS.get(key, 0) + 1
    if _ATTEMPTS[key] < _SUCCEED_ON_ATTEMPT:
        raise RuntimeError(f"simulated downstream failure (attempt {_ATTEMPTS[key]})")
    return "ok"


@workflow.defn
class _FlakyDownstreamWorkflow:
    @workflow.run
    async def run(self, key: str) -> str:
        result: str = await workflow.execute_activity(
            _flaky_downstream_call,
            key,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=retry_policy_for(initial_interval_seconds=0.01),
        )
        return result


@pytest_asyncio.fixture
async def temporal_env() -> AsyncIterator[WorkflowEnvironment]:
    try:
        env = await WorkflowEnvironment.start_time_skipping()
    except Exception as exc:  # noqa: BLE001 — any startup failure -> skip, not fail
        pytest.skip(f"Temporal time-skipping test server unavailable: {exc}")
    try:
        yield env
    finally:
        await env.shutdown()


async def test_workflow_retries_a_failing_activity_until_it_succeeds(
    temporal_env: WorkflowEnvironment,
) -> None:
    key = str(uuid.uuid4())
    task_queue = f"tq-{uuid.uuid4()}"
    async with Worker(
        temporal_env.client,
        task_queue=task_queue,
        workflows=[_FlakyDownstreamWorkflow],
        activities=[_flaky_downstream_call],
    ):
        result = await temporal_env.client.execute_workflow(
            _FlakyDownstreamWorkflow.run,
            key,
            id=f"wf-{uuid.uuid4()}",
            task_queue=task_queue,
        )
    assert result == "ok"
    assert _ATTEMPTS[key] == _SUCCEED_ON_ATTEMPT
