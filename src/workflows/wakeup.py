"""W01 — Wake-up window check (WBS-B7a, ADR-0018 §2, Charter §19/§29).

Charter §29: specific wake-up times (23:00/06:00) are Deferred to
Operations Specification — only *candidates*, never Frozen. This module
provides zero default windows; callers must supply them from config/env
(CLAUDE.md §4 forbids baking Deferred parameters into code).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, time


@dataclass(slots=True, frozen=True)
class WakeupWindow:
    start: time
    end: time  # `end < start` means the window wraps past midnight


def _time_in_window(t: time, window: WakeupWindow) -> bool:
    if window.start <= window.end:
        return window.start <= t <= window.end
    return t >= window.start or t <= window.end


def is_within_wakeup_window(now: datetime | time, windows: Sequence[WakeupWindow]) -> bool:
    t = now.time() if isinstance(now, datetime) else now
    return any(_time_in_window(t, w) for w in windows)
