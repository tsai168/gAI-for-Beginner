"""I03 wiring (ADR-0025 §3): R03's dashboard reads actually go through the
cache — a DB change between two calls inside the TTL window is invisible
until the TTL expires. Needs Postgres + migrations.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from knowledge.db.models import Company, ModelVersion
from models.seco import SecoDimensions, correct_seco_score, record_seco_score
from reports.cache import InMemoryCache
from reports.dashboard import get_company_scores, get_seco_cmi_dashboard

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 9, 0, tzinfo=UTC)


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


def _company(db_session):  # type: ignore[no-untyped-def]
    c = Company(company_name="Cache Test Co", universe="Watchlist")
    db_session.add(c)
    db_session.flush()
    return c


def _model_version(db_session, label: str):  # type: ignore[no-untyped-def]
    mv = ModelVersion(model_kind="seco", version_label=label, valid_from=RETRIEVED)
    db_session.add(mv)
    db_session.flush()
    return mv


def test_dashboard_serves_stale_data_within_ttl_then_refreshes(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    mv1 = _model_version(db_session, "cache-v1")
    score_v1 = record_seco_score(
        db_session,
        company_id=company.company_id,
        as_of=RETRIEVED,
        dims=SecoDimensions(40, 40, 40, 40, 40, 40),
        confidence=0.6,
        model_version_id=mv1.model_version_id,
        valid_from=RETRIEVED,
    )

    clock = _FakeClock()
    cache = InMemoryCache(clock=clock)

    first = get_company_scores(db_session, company.company_id, cache=cache)
    assert first is not None
    assert first.seco_score == pytest.approx(40.0)

    # a real change lands in the DB — GP-10/CF-17: never overwrite the old
    # row, retire it (valid_to) and open a new one, same as production code
    # does for any Seco re-score.
    mv2 = _model_version(db_session, "cache-v2")
    correct_seco_score(
        db_session,
        score_v1,
        dims=SecoDimensions(90, 90, 90, 90, 90, 90),
        confidence=0.9,
        model_version_id=mv2.model_version_id,
        valid_from=RETRIEVED,
    )

    # ...but within the TTL window, the cached (stale) value is still served
    still_cached = get_company_scores(db_session, company.company_id, cache=cache)
    assert still_cached is not None
    assert still_cached.seco_score == pytest.approx(40.0)

    # once the TTL has elapsed, the fresh value is computed and re-cached
    clock.now += 61
    refreshed = get_company_scores(db_session, company.company_id, cache=cache)
    assert refreshed is not None
    assert refreshed.seco_score == pytest.approx(90.0)


def test_seco_cmi_dashboard_list_is_also_cached(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    mv = _model_version(db_session, "cache-list-v1")
    record_seco_score(
        db_session,
        company_id=company.company_id,
        as_of=RETRIEVED,
        dims=SecoDimensions(50, 50, 50, 50, 50, 50),
        confidence=0.7,
        model_version_id=mv.model_version_id,
        valid_from=RETRIEVED,
    )

    clock = _FakeClock()
    cache = InMemoryCache(clock=clock)

    first = get_seco_cmi_dashboard(db_session, cache=cache)
    assert any(s.company_id == company.company_id for s in first)

    other_company = Company(company_name="Not Yet Cached Co", universe="Watchlist")
    db_session.add(other_company)
    db_session.flush()
    mv2 = _model_version(db_session, "cache-list-v2")
    record_seco_score(
        db_session,
        company_id=other_company.company_id,
        as_of=RETRIEVED,
        dims=SecoDimensions(60, 60, 60, 60, 60, 60),
        confidence=0.8,
        model_version_id=mv2.model_version_id,
        valid_from=RETRIEVED,
    )

    still_cached = get_seco_cmi_dashboard(db_session, cache=cache)
    assert not any(s.company_id == other_company.company_id for s in still_cached)

    clock.now += 61
    refreshed = get_seco_cmi_dashboard(db_session, cache=cache)
    assert any(s.company_id == other_company.company_id for s in refreshed)
