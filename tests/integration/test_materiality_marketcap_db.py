"""WBS-B5c integration tests (ADR-0015): M05 CFL-04 gate, M07 PIT market cap.
Needs Postgres + migrations."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from knowledge.db.base import CflStatus
from knowledge.db.models import Company, Event, MarketData
from models.market_cap import compute_market_cap_for_date, get_current_market_data
from models.materiality import MaterialityFactors, score_event_materiality

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


def _company(db_session):  # type: ignore[no-untyped-def]
    c = Company(company_name="B5c Test Co", universe="Core")
    db_session.add(c)
    db_session.flush()
    return c


def test_score_event_materiality_sets_score_and_raises_cfl04(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV09", retrieved_at=RETRIEVED)
    db_session.add(ev)
    db_session.flush()

    factors = MaterialityFactors(
        cpo_relevance=80,
        evidence_strength=70,
        commercial_impact=60,
        ecosystem_impact=50,
        novelty=40,
    )
    status = score_event_materiality(db_session, ev, factors)

    assert ev.materiality_score == pytest.approx(
        0.25 * 80 + 0.25 * 70 + 0.20 * 60 + 0.20 * 50 + 0.10 * 40
    )
    assert status is CflStatus.PENDING  # B1 G01 stub; B8 supplies the real rule


def test_pit_market_cap_uses_each_dates_own_shares_outstanding(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    d1 = date(2026, 1, 1)
    d2 = date(2026, 6, 1)

    db_session.add(
        MarketData(
            company_id=company.company_id,
            trade_date=d1,
            close_price=100.0,
            shares_outstanding=1_000_000,
            retrieved_at=RETRIEVED,
        )
    )
    db_session.add(
        MarketData(
            company_id=company.company_id,
            trade_date=d2,
            close_price=120.0,
            shares_outstanding=1_500_000,  # a later share issuance
            retrieved_at=RETRIEVED,
        )
    )
    db_session.flush()

    cap1 = compute_market_cap_for_date(db_session, company_id=company.company_id, trade_date=d1)
    cap2 = compute_market_cap_for_date(db_session, company_id=company.company_id, trade_date=d2)

    assert cap1 == pytest.approx(100.0 * 1_000_000)
    assert cap2 == pytest.approx(120.0 * 1_500_000)
    # proves d1's cap is NOT computed with d2's (later, larger) share count
    assert cap1 != pytest.approx(100.0 * 1_500_000)


def test_market_cap_none_when_no_row_for_date(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    assert (
        compute_market_cap_for_date(
            db_session, company_id=company.company_id, trade_date=date(2026, 3, 3)
        )
        is None
    )


def test_market_cap_none_when_shares_outstanding_missing(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    d = date(2026, 2, 2)
    db_session.add(
        MarketData(
            company_id=company.company_id,
            trade_date=d,
            close_price=50.0,
            shares_outstanding=None,
            retrieved_at=RETRIEVED,
        )
    )
    db_session.flush()
    assert (
        compute_market_cap_for_date(db_session, company_id=company.company_id, trade_date=d) is None
    )


def test_get_current_market_data_ignores_closed_rows(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    d = date(2026, 4, 4)
    old = MarketData(
        company_id=company.company_id,
        trade_date=d,
        close_price=10.0,
        shares_outstanding=100,
        retrieved_at=RETRIEVED,
        valid_to=RETRIEVED,  # already closed
    )
    db_session.add(old)
    db_session.flush()
    assert get_current_market_data(db_session, company_id=company.company_id, trade_date=d) is None
