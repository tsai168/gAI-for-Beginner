"""WBS-B7b unit tests: W03 fan-out data structures (ADR-0019 §2).

Actual parallel-execution behaviour is exercised by
tests/test_workflows_temporal.py (needs a Temporal test environment).
"""

from __future__ import annotations

from workflows.fanout import FanOutItem, FanOutRequest


def test_fan_out_item_defaults_to_no_args() -> None:
    item = FanOutItem(activity_name="do_thing")
    assert item.args == []


def test_fan_out_request_defaults() -> None:
    req = FanOutRequest(items=[FanOutItem("a"), FanOutItem("b")])
    assert len(req.items) == 2
    assert req.start_to_close_timeout_seconds == 60
    assert req.max_attempts == 5


def test_fan_out_request_overrides() -> None:
    req = FanOutRequest(items=[], start_to_close_timeout_seconds=30, max_attempts=2)
    assert req.start_to_close_timeout_seconds == 30
    assert req.max_attempts == 2
