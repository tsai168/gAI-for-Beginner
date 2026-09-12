"""WBS-B7a unit tests: W01 wake-up window (ADR-0018 §2)."""

from __future__ import annotations

from datetime import datetime, time

from workflows.wakeup import WakeupWindow, is_within_wakeup_window

NIGHT = WakeupWindow(time(23, 0), time(2, 0))  # wraps midnight
MORNING = WakeupWindow(time(6, 0), time(7, 0))  # does not wrap


def test_empty_windows_always_false() -> None:
    assert is_within_wakeup_window(time(12, 0), []) is False


def test_non_wrapping_window_boundaries_inclusive() -> None:
    assert is_within_wakeup_window(time(6, 0), [MORNING]) is True
    assert is_within_wakeup_window(time(7, 0), [MORNING]) is True
    assert is_within_wakeup_window(time(6, 30), [MORNING]) is True
    assert is_within_wakeup_window(time(5, 59), [MORNING]) is False
    assert is_within_wakeup_window(time(7, 1), [MORNING]) is False


def test_wrapping_window_covers_both_sides_of_midnight() -> None:
    assert is_within_wakeup_window(time(23, 30), [NIGHT]) is True
    assert is_within_wakeup_window(time(1, 0), [NIGHT]) is True
    assert is_within_wakeup_window(time(23, 0), [NIGHT]) is True
    assert is_within_wakeup_window(time(2, 0), [NIGHT]) is True
    assert is_within_wakeup_window(time(12, 0), [NIGHT]) is False


def test_multiple_windows_are_unioned() -> None:
    assert is_within_wakeup_window(time(6, 30), [NIGHT, MORNING]) is True
    assert is_within_wakeup_window(time(23, 30), [NIGHT, MORNING]) is True
    assert is_within_wakeup_window(time(12, 0), [NIGHT, MORNING]) is False


def test_accepts_datetime_not_just_time() -> None:
    dt = datetime(2026, 9, 12, 6, 30)
    assert is_within_wakeup_window(dt, [MORNING]) is True
