"""WBS-B7a unit tests: W02 priority classification + queue (ADR-0018 §3)."""

from __future__ import annotations

from ingestion.dedup import DedupVerdict
from workflows.priority_queue import Priority, PriorityTriggerQueue, classify_priority


def test_duplicate_content_is_low_regardless_of_materiality() -> None:
    p = classify_priority(materiality_score=95, dedup_verdict=DedupVerdict.DUPLICATE_SAME_SOURCE)
    assert p is Priority.LOW


def test_high_materiality_new_content_is_high() -> None:
    p = classify_priority(materiality_score=70, dedup_verdict=DedupVerdict.NEW)
    assert p is Priority.HIGH


def test_low_materiality_new_content_is_normal() -> None:
    p = classify_priority(materiality_score=10, dedup_verdict=DedupVerdict.NEW)
    assert p is Priority.NORMAL


def test_missing_materiality_is_normal() -> None:
    p = classify_priority(materiality_score=None, dedup_verdict=DedupVerdict.NEW)
    assert p is Priority.NORMAL


def test_queue_pops_high_before_normal_before_low() -> None:
    q = PriorityTriggerQueue()
    q.push(Priority.NORMAL, "normal")
    q.push(Priority.LOW, "low")
    q.push(Priority.HIGH, "high")
    assert [q.pop(), q.pop(), q.pop()] == ["high", "normal", "low"]


def test_queue_is_fifo_within_same_priority() -> None:
    q = PriorityTriggerQueue()
    q.push(Priority.NORMAL, "first")
    q.push(Priority.NORMAL, "second")
    q.push(Priority.NORMAL, "third")
    assert [q.pop(), q.pop(), q.pop()] == ["first", "second", "third"]


def test_queue_len_and_bool() -> None:
    q = PriorityTriggerQueue()
    assert len(q) == 0
    assert bool(q) is False
    q.push(Priority.LOW, "x")
    assert len(q) == 1
    assert bool(q) is True
