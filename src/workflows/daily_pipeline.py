"""W04 — Daily research pipeline workflow skeleton (WBS-B7b, ADR-0019 §4).

Sequences Work-2 §3.2's frozen EVENT_CONTRACT pipeline_status states
verbatim: DISCOVERED -> FETCHED -> NORMALIZED -> EXTRACTED -> VERIFIED ->
ANALYZED -> APPROVED -> PUBLISHED. This delivers the *sequencing and retry
wiring* — each stage's real business logic (P01 fetch, A01 extraction, G01's
full rule engine, G06 publication, ...) is wired in as those land in later
batches; `run_stage` documents the single integration point and raises
NotImplementedError until then (same posture as agents/base.py, ADR-0017).
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import activity, workflow

from workflows.retry_policy import retry_policy_for

PIPELINE_STAGES: tuple[str, ...] = (
    "DISCOVERED",
    "FETCHED",
    "NORMALIZED",
    "EXTRACTED",
    "VERIFIED",
    "ANALYZED",
    "APPROVED",
    "PUBLISHED",
)


@activity.defn
async def run_stage(stage: str, event_id: str) -> None:
    raise NotImplementedError(
        f"pipeline stage {stage!r} for event {event_id} not yet wired — see ADR-0019 §4"
    )


@workflow.defn
class DailyResearchPipelineWorkflow:
    @workflow.run
    async def run(self, event_id: str) -> None:
        policy = retry_policy_for()
        timeout = timedelta(seconds=120)
        for stage in PIPELINE_STAGES:
            await workflow.execute_activity(
                run_stage,
                args=[stage, event_id],
                start_to_close_timeout=timeout,
                retry_policy=policy,
            )
