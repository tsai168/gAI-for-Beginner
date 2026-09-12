"""W02 — Priority trigger queue (WBS-B7a, ADR-0018 §3, Charter §19).

Deterministic (L0) ordering only — this does not itself judge materiality
(that's M05, WBS-B5c) or dedup (P02, WBS-B3a); it just prioritizes based
on their outputs.
"""

from __future__ import annotations

import enum
import heapq
import itertools
from dataclasses import dataclass, field
from typing import Any

from ingestion.dedup import DedupVerdict

_HIGH_MATERIALITY_THRESHOLD = 70.0  # implementation default, not a Charter-frozen value


class Priority(enum.IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


def classify_priority(*, materiality_score: float | None, dedup_verdict: DedupVerdict) -> Priority:
    if dedup_verdict is not DedupVerdict.NEW:
        return Priority.LOW
    if materiality_score is not None and materiality_score >= _HIGH_MATERIALITY_THRESHOLD:
        return Priority.HIGH
    return Priority.NORMAL


@dataclass(order=True)
class _QueueItem:
    sort_key: tuple[int, int]
    payload: Any = field(compare=False)


class PriorityTriggerQueue:
    """HIGH pops before NORMAL before LOW; same-priority items are FIFO."""

    def __init__(self) -> None:
        self._heap: list[_QueueItem] = []
        self._counter = itertools.count()

    def push(self, priority: Priority, payload: Any) -> None:
        # negate priority: heapq is a min-heap, higher Priority must pop first
        heapq.heappush(self._heap, _QueueItem((-priority.value, next(self._counter)), payload))

    def pop(self) -> Any:
        return heapq.heappop(self._heap).payload

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)
