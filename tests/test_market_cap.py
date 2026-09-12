"""WBS-B5c unit tests: M07 PIT market cap formula (ADR-0015 §3)."""

from __future__ import annotations

import pytest

from models.market_cap import compute_market_cap


def test_basic_multiplication() -> None:
    assert compute_market_cap(price=100.0, shares_outstanding=1_000_000) == 100_000_000.0


def test_zero_price_or_shares_gives_zero() -> None:
    assert compute_market_cap(price=0.0, shares_outstanding=1_000) == 0.0
    assert compute_market_cap(price=50.0, shares_outstanding=0) == 0.0


def test_negative_price_raises() -> None:
    with pytest.raises(ValueError, match="price"):
        compute_market_cap(price=-1.0, shares_outstanding=1_000)


def test_negative_shares_raises() -> None:
    with pytest.raises(ValueError, match="shares_outstanding"):
        compute_market_cap(price=10.0, shares_outstanding=-1)
