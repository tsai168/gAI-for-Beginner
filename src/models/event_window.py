"""M06 — Event window / AR-CAR engine (WBS-B5d, ADR-0016 §3, CF-20/23/24).

Charter §14.1/§14.2, implemented verbatim:
- window = [-pre, +post] trading days around an already-aligned
  event_trading_date (P06 guarantees t=0 is a trading day).
- Market-adjusted AR(i,t) = R(i,t) - R(m,t).
- Market Model: R(i,t) = alpha + beta*R(m,t) + eps; AR = actual - expected.
  alpha/beta come from an *estimation window* the caller supplies (this
  module does not pick one — avoiding overlap with the event window is the
  caller's responsibility).
- CAR[a,b] = sum(AR).
"""

from __future__ import annotations

import statistics
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from ingestion.trading_calendar import TradingCalendar, trading_days_around
from knowledge.db.base import BenchmarkModel
from knowledge.db.models import ValuationEventWindow


def event_window_dates(
    calendar: TradingCalendar, *, event_trading_date: date, pre: int, post: int
) -> list[date]:
    return trading_days_around(calendar, center=event_trading_date, pre=pre, post=post)


def market_adjusted_ar(*, r_i: float, r_m: float) -> float:
    """Charter §14.2: AR(i,t) = R(i,t) - R(m,t)."""
    return r_i - r_m


@dataclass(slots=True, frozen=True)
class MarketModelParams:
    alpha: float
    beta: float


_MIN_ESTIMATION_OBSERVATIONS = 2
_VARIANCE_EPSILON = 1e-12


def estimate_market_model(
    r_i_estimation: Sequence[float], r_m_estimation: Sequence[float]
) -> MarketModelParams:
    """Simple OLS on an estimation-window return series (supplied by the
    caller — this module does not select the window)."""
    if len(r_i_estimation) != len(r_m_estimation):
        raise ValueError("r_i_estimation and r_m_estimation must be the same length")
    if len(r_i_estimation) < _MIN_ESTIMATION_OBSERVATIONS:
        raise ValueError("need at least 2 observations to estimate alpha/beta")

    mean_i = statistics.fmean(r_i_estimation)
    mean_m = statistics.fmean(r_m_estimation)
    cov = sum(
        (i - mean_i) * (m - mean_m) for i, m in zip(r_i_estimation, r_m_estimation, strict=True)
    )
    var_m = sum((m - mean_m) ** 2 for m in r_m_estimation)
    if var_m < _VARIANCE_EPSILON:
        raise ValueError("market return series has zero variance; cannot estimate beta")
    beta = cov / var_m
    alpha = mean_i - beta * mean_m
    return MarketModelParams(alpha=alpha, beta=beta)


def market_model_ar(*, r_i: float, r_m: float, params: MarketModelParams) -> float:
    """Charter §14.2: AR = actual - expected, expected = alpha + beta*R_m."""
    expected = params.alpha + params.beta * r_m
    return r_i - expected


def compute_car(ar_series: Sequence[float]) -> float:
    """Charter §14.2: CAR[a,b] = sum(AR)."""
    return sum(ar_series)


def record_valuation_event_window(
    session: Session,
    *,
    event_id: uuid.UUID,
    window_pre: int,
    window_post: int,
    benchmark_model: BenchmarkModel,
    ar_series: Sequence[float],
    model_version_id: uuid.UUID,
    market_cap: float | None = None,
) -> ValuationEventWindow:
    row = ValuationEventWindow(
        event_id=event_id,
        window_pre=window_pre,
        window_post=window_post,
        benchmark_model=benchmark_model.value,
        ar_series=list(ar_series),
        car=compute_car(ar_series),
        market_cap=market_cap,
        model_version_id=model_version_id,
    )
    session.add(row)
    session.flush()
    return row
