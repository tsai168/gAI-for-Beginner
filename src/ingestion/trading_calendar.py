"""P06 — Trading calendar + Conservative Alignment (WBS-B3b, ADR-0010 §3, CF-22).

Deterministic (L0). Implements Charter §14.4 Trading-session Alignment
verbatim. A concrete official calendar (TWSE/TPEx holidays) is Deferred —
same posture as P01's concrete site adapters (ADR-0009); this module ships
the alignment algorithm plus a `SetTradingCalendar` fixture.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Protocol

DEFAULT_MARKET_OPEN = time(9, 0)
DEFAULT_MARKET_CLOSE = time(13, 30)


class AlignmentBasis(enum.StrEnum):
    PRE_MARKET = "PRE_MARKET"
    INTRADAY = "INTRADAY"
    AFTER_HOURS = "AFTER_HOURS"
    NON_TRADING_DAY = "NON_TRADING_DAY"
    CONSERVATIVE = "CONSERVATIVE"


class TradingCalendar(Protocol):
    def is_trading_day(self, d: date) -> bool: ...
    def next_trading_day(self, d: date) -> date: ...
    def previous_trading_day(self, d: date) -> date: ...


@dataclass(slots=True)
class SetTradingCalendar:
    """Fixture/test calendar backed by an explicit set of trading dates."""

    trading_days: frozenset[date]

    def is_trading_day(self, d: date) -> bool:
        return d in self.trading_days

    def next_trading_day(self, d: date) -> date:
        candidates = sorted(day for day in self.trading_days if day > d)
        if not candidates:
            raise ValueError(f"no known trading day after {d}")
        return candidates[0]

    def previous_trading_day(self, d: date) -> date:
        candidates = sorted((day for day in self.trading_days if day < d), reverse=True)
        if not candidates:
            raise ValueError(f"no known trading day before {d}")
        return candidates[0]


def trading_days_around(
    calendar: TradingCalendar, *, center: date, pre: int, post: int
) -> list[date]:
    """WBS-B5d (M06): `pre` trading days before `center`, `center` itself,
    then `post` trading days after — i.e. the [-pre, +post] event window
    (Charter §14.1). `center` (t=0) must already be a trading day (P06's
    alignment guarantees this)."""
    if pre < 0 or post < 0:
        raise ValueError("pre and post must be >= 0")
    before: list[date] = []
    cursor = center
    for _ in range(pre):
        cursor = calendar.previous_trading_day(cursor)
        before.append(cursor)
    before.reverse()

    after: list[date] = []
    cursor = center
    for _ in range(post):
        cursor = calendar.next_trading_day(cursor)
        after.append(cursor)

    return [*before, center, *after]


@dataclass(slots=True, frozen=True)
class AlignmentResult:
    event_trading_date: date
    basis: AlignmentBasis
    caveat: str | None = None


def align_event_trading_date(
    *,
    calendar: TradingCalendar,
    evidence_time: datetime | None = None,
    evidence_date: date | None = None,
    market_open: time = DEFAULT_MARKET_OPEN,
    market_close: time = DEFAULT_MARKET_CLOSE,
) -> AlignmentResult | None:
    """Charter §14.4. `evidence_time` (precise) takes priority over
    `evidence_date` (date-only). Returns None with no usable evidence at all
    (GP-07: unknown time must remain unknown, not guessed)."""
    if evidence_time is not None:
        d = evidence_time.date()
        if not calendar.is_trading_day(d):
            return AlignmentResult(calendar.next_trading_day(d), AlignmentBasis.NON_TRADING_DAY)
        t = evidence_time.time()
        if t < market_open:
            return AlignmentResult(d, AlignmentBasis.PRE_MARKET)
        if t <= market_close:
            return AlignmentResult(
                d,
                AlignmentBasis.INTRADAY,
                caveat="intraday disclosure; same-day alignment carries limited precision",
            )
        return AlignmentResult(calendar.next_trading_day(d), AlignmentBasis.AFTER_HOURS)

    if evidence_date is not None:
        # DATE_ONLY, cannot tell pre-/post-market -> Conservative Alignment:
        # always the next trading day, regardless of whether evidence_date
        # itself happens to be one (Charter §14.4 "安全 t=0").
        return AlignmentResult(
            calendar.next_trading_day(evidence_date),
            AlignmentBasis.CONSERVATIVE,
            caveat="date-only evidence; conservative next-trading-day alignment",
        )

    return None
