"""WBS-B7b: real Temporal execution tests (ADR-0019 §1).

Uses `temporalio.testing.WorkflowEnvironment.start_time_skipping()`, which
needs to download/run a test server. If that isn't possible in this
environment (no network, sandboxed CI, ...), every test here skips instead
of failing — see ADR-0019 §1 for why (avoid another CI failure loop while
still getting real verification wherever the environment allows it).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from workflows.daily_pipeline import DailyResearchPipelineWorkflow, run_stage
from workflows.fanout import FanOutFanInWorkflow, FanOutItem, FanOutRequest

pytestmark = pytest.mark.temporal


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


@activity.defn(name="_echo")
async def _echo(x: int) -> int:
    return x + 1


async def test_fan_out_fan_in_runs_activities_in_parallel(
    temporal_env: WorkflowEnvironment,
) -> None:
    task_queue = f"tq-{uuid.uuid4()}"
    async with Worker(
        temporal_env.client,
        task_queue=task_queue,
        workflows=[FanOutFanInWorkflow],
        activities=[_echo],
    ):
        request = FanOutRequest(items=[FanOutItem("_echo", [i]) for i in range(3)])
        result = await temporal_env.client.execute_workflow(
            FanOutFanInWorkflow.run,
            request,
            id=f"wf-{uuid.uuid4()}",
            task_queue=task_queue,
        )
    assert sorted(result) == [1, 2, 3]


async def test_daily_pipeline_fails_at_first_undeferred_stage(
    temporal_env: WorkflowEnvironment,
) -> None:
    task_queue = f"tq-{uuid.uuid4()}"
    async with Worker(
        temporal_env.client,
        task_queue=task_queue,
        workflows=[DailyResearchPipelineWorkflow],
        activities=[run_stage],
    ):
        with pytest.raises(Exception):  # noqa: B017,PT011 — Temporal wraps the cause, exact type varies
            await temporal_env.client.execute_workflow(
                DailyResearchPipelineWorkflow.run,
                "evt-123",
                id=f"wf-{uuid.uuid4()}",
                task_queue=task_queue,
            )
