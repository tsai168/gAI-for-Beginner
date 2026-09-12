"""WBS-B7a unit tests: W06 Batch AI Parsing gate (ADR-0018 §4)."""

from __future__ import annotations

import pytest

from ingestion.dedup import DedupVerdict
from workflows.batch_gate import evaluate_batch_gate
from workflows.priority_queue import Priority


def test_duplicate_content_never_calls_llm() -> None:
    d = evaluate_batch_gate(
        dedup_verdict=DedupVerdict.DUPLICATE_OTHER_SOURCE,
        within_wakeup_window=True,
        priority=Priority.HIGH,
    )
    assert d.should_call_llm is False


def test_high_priority_bypasses_wakeup_window() -> None:
    d = evaluate_batch_gate(
        dedup_verdict=DedupVerdict.NEW, within_wakeup_window=False, priority=Priority.HIGH
    )
    assert d.should_call_llm is True


def test_outside_window_and_not_high_blocks() -> None:
    d = evaluate_batch_gate(
        dedup_verdict=DedupVerdict.NEW, within_wakeup_window=False, priority=Priority.NORMAL
    )
    assert d.should_call_llm is False


def test_new_content_within_window_calls_llm() -> None:
    d = evaluate_batch_gate(
        dedup_verdict=DedupVerdict.NEW, within_wakeup_window=True, priority=Priority.NORMAL
    )
    assert d.should_call_llm is True


@pytest.mark.parametrize(
    "verdict,window,priority",
    [
        (DedupVerdict.NEW, True, Priority.LOW),
        (DedupVerdict.NEW, True, Priority.HIGH),
        (DedupVerdict.NEW, False, Priority.HIGH),
        (DedupVerdict.DUPLICATE_SAME_SOURCE, True, Priority.HIGH),
    ],
)
def test_every_decision_carries_a_reason(
    verdict: DedupVerdict, window: bool, priority: Priority
) -> None:
    d = evaluate_batch_gate(dedup_verdict=verdict, within_wakeup_window=window, priority=priority)
    assert d.reason
