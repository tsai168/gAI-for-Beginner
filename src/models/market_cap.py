"""M07 — Point-in-Time market cap calculator (WBS-B5c, ADR-0015 §3, CF-24).

MarketCap(i,t) = Price(i,t) x SharesOutstanding(i,t), using the PIT shares
outstanding — never today's latest figure applied to a historical date.
`compute_market_cap_for_date` enforces this structurally: it reads price
and shares_outstanding off the *same* market_data row for that date, so
there is no code path that could mix a historical price with a different
date's share count.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge.db.models import MarketData


def compute_market_cap(*, price: float, shares_outstanding: float) -> float:
    if price < 0:
        raise ValueError(f"price must be >= 0, got {price}")
    if shares_outstanding < 0:
        raise ValueError(f"shares_outstanding must be >= 0, got {shares_outstanding}")
    return price * shares_outstanding


def get_current_market_data(
    session: Session, *, company_id: uuid.UUID, trade_date: date
) -> MarketData | None:
    return session.execute(
        select(MarketData).where(
            MarketData.company_id == company_id,
            MarketData.trade_date == trade_date,
            MarketData.valid_to.is_(None),
        )
    ).scalar_one_or_none()


def compute_market_cap_for_date(
    session: Session, *, company_id: uuid.UUID, trade_date: date
) -> float | None:
    """None (never a guess) if there's no current row for that date, or if
    price/shares_outstanding on it are missing."""
    row = get_current_market_data(session, company_id=company_id, trade_date=trade_date)
    if row is None or row.close_price is None or row.shares_outstanding is None:
        return None
    return compute_market_cap(
        price=float(row.close_price), shares_outstanding=float(row.shares_outstanding)
    )
