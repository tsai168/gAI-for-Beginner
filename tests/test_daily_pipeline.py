"""WBS-B7b unit tests: W04 pipeline stage sequence (ADR-0019 §4)."""

from __future__ import annotations

import asyncio

import pytest

from workflows.daily_pipeline import PIPELINE_STAGES, run_stage


def test_pipeline_stages_match_event_contract_state_machine() -> None:
    # Work-2 §3.2, verbatim order.
    assert PIPELINE_STAGES == (
        "DISCOVERED",
        "FETCHED",
        "NORMALIZED",
        "EXTRACTED",
        "VERIFIED",
        "ANALYZED",
        "APPROVED",
        "PUBLISHED",
    )


def test_run_stage_is_deferred() -> None:
    with pytest.raises(NotImplementedError, match="DISCOVERED"):
        asyncio.run(run_stage("DISCOVERED", "evt-123"))
