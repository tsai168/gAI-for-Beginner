"""WBS-B3b unit tests: P06 trading-calendar alignment (ADR-0010 §3, Charter §14.4)."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from ingestion.trading_calendar import (
    AlignmentBasis,
    SetTradingCalendar,
    align_event_trading_date,
)

D7 = date(2026, 9, 7)  # trading day
D8 = date(2026, 9, 8)  # non-trading day (between D7 and D9)
D9 = date(2026, 9, 9)  # trading day
D11 = date(2026, 9, 11)  # trading day, last one known

CAL = SetTradingCalendar(frozenset({D7, D9, D11}))


def test_pre_market_is_same_day() -> None:
    r = align_event_trading_date(calendar=CAL, evidence_time=datetime(2026, 9, 7, 8, 0))
    assert r is not None
    assert r.event_trading_date == D7
    assert r.basis is AlignmentBasis.PRE_MARKET


def test_intraday_is_same_day_with_caveat() -> None:
    r = align_event_trading_date(calendar=CAL, evidence_time=datetime(2026, 9, 7, 10, 30))
    assert r is not None
    assert r.event_trading_date == D7
    assert r.basis is AlignmentBasis.INTRADAY
    assert r.caveat is not None


def test_after_hours_rolls_to_next_trading_day() -> None:
    r = align_event_trading_date(calendar=CAL, evidence_time=datetime(2026, 9, 7, 15, 0))
    assert r is not None
    assert r.event_trading_date == D9
    assert r.basis is AlignmentBasis.AFTER_HOURS


def test_non_trading_day_rolls_forward() -> None:
    r = align_event_trading_date(calendar=CAL, evidence_time=datetime(2026, 9, 8, 10, 0))
    assert r is not None
    assert r.event_trading_date == D9
    assert r.basis is AlignmentBasis.NON_TRADING_DAY


def test_date_only_is_conservative_next_trading_day_even_if_itself_trading() -> None:
    # D7 is itself a trading day, but with no pre/post-market info the rule
    # is still "next trading day" (Charter §14.4 conservative t=0).
    r = align_event_trading_date(calendar=CAL, evidence_date=D7)
    assert r is not None
    assert r.event_trading_date == D9
    assert r.basis is AlignmentBasis.CONSERVATIVE
    assert r.caveat is not None


def test_no_evidence_returns_none() -> None:
    assert align_event_trading_date(calendar=CAL) is None


def test_calendar_raises_when_no_future_trading_day_known() -> None:
    with pytest.raises(ValueError, match="no known trading day after"):
        CAL.next_trading_day(D11)


def test_market_boundary_is_inclusive_of_close() -> None:
    r = align_event_trading_date(calendar=CAL, evidence_time=datetime(2026, 9, 7, 13, 30))
    assert r is not None
    assert r.basis is AlignmentBasis.INTRADAY
