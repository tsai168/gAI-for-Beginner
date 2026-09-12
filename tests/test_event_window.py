"""WBS-B5d unit tests: M06 event window / AR-CAR formulas (ADR-0016 §3)."""

from __future__ import annotations

from datetime import date

import pytest

from ingestion.trading_calendar import SetTradingCalendar
from models.event_window import (
    MarketModelParams,
    compute_car,
    estimate_market_model,
    event_window_dates,
    market_adjusted_ar,
    market_model_ar,
)

CAL = SetTradingCalendar(frozenset(date(2026, 9, d) for d in range(1, 21)))


def test_event_window_dates_delegates_to_trading_calendar() -> None:
    center = date(2026, 9, 10)
    dates = event_window_dates(CAL, event_trading_date=center, pre=1, post=1)
    assert dates == [date(2026, 9, 9), center, date(2026, 9, 11)]


def test_market_adjusted_ar() -> None:
    assert market_adjusted_ar(r_i=0.05, r_m=0.02) == pytest.approx(0.03)
    assert market_adjusted_ar(r_i=-0.01, r_m=0.02) == pytest.approx(-0.03)


def test_estimate_market_model_recovers_known_line() -> None:
    # r_i = 0.01 + 1.5 * r_m exactly -> alpha=0.01, beta=1.5
    r_m = [0.00, 0.01, 0.02, -0.01, 0.03]
    r_i = [0.01 + 1.5 * m for m in r_m]
    params = estimate_market_model(r_i, r_m)
    assert params.alpha == pytest.approx(0.01)
    assert params.beta == pytest.approx(1.5)


def test_estimate_market_model_needs_matching_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        estimate_market_model([0.1, 0.2], [0.1])


def test_estimate_market_model_needs_at_least_two_points() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        estimate_market_model([0.1], [0.1])


def test_estimate_market_model_rejects_zero_variance_market() -> None:
    with pytest.raises(ValueError, match="zero variance"):
        estimate_market_model([0.1, 0.2, 0.3], [0.05, 0.05, 0.05])


def test_market_model_ar_matches_actual_minus_expected() -> None:
    params = MarketModelParams(alpha=0.01, beta=1.5)
    ar = market_model_ar(r_i=0.05, r_m=0.02, params=params)
    expected = 0.01 + 1.5 * 0.02
    assert ar == pytest.approx(0.05 - expected)


def test_compute_car_sums_ar_series() -> None:
    assert compute_car([0.01, -0.02, 0.03]) == pytest.approx(0.02)
    assert compute_car([]) == 0
