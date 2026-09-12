"""W03 — Fan-out / Fan-in orchestrator (WBS-B7b, ADR-0019 §2, SOP step 12).

A generic Temporal workflow: run one activity per item in parallel and
collect all results. It has no idea what work it's fanning out to — the
caller supplies the (already-registered) activity name and its arguments.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow

from workflows.retry_policy import retry_policy_for


@dataclass(slots=True, frozen=True)
class FanOutItem:
    activity_name: str
    args: list[Any] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class FanOutRequest:
    items: list[FanOutItem]
    start_to_close_timeout_seconds: int = 60
    max_attempts: int = 5


@workflow.defn
class FanOutFanInWorkflow:
    @workflow.run
    async def run(self, request: FanOutRequest) -> list[Any]:
        policy = retry_policy_for(max_attempts=request.max_attempts)
        handles = [
            workflow.execute_activity(
                item.activity_name,
                args=item.args,
                start_to_close_timeout=timedelta(seconds=request.start_to_close_timeout_seconds),
                retry_policy=policy,
            )
            for item in request.items
        ]
        return list(await asyncio.gather(*handles))
