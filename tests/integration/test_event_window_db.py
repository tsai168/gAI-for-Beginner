"""WBS-B5d integration test (ADR-0016): ValuationEventWindow DB write.
Needs Postgres + migrations."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from knowledge.db.base import BenchmarkModel
from knowledge.db.models import Event, ModelVersion
from models.event_window import compute_car, record_valuation_event_window

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


def test_record_valuation_event_window(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV06", retrieved_at=RETRIEVED)
    db_session.add(ev)
    mv = ModelVersion(
        model_kind="benchmark", version_label="market-adjusted-v1", valid_from=RETRIEVED
    )
    db_session.add(mv)
    db_session.flush()

    ar_series = [0.01, -0.02, 0.015, 0.0, 0.005]
    row = record_valuation_event_window(
        db_session,
        event_id=ev.event_id,
        window_pre=2,
        window_post=2,
        benchmark_model=BenchmarkModel.MARKET_ADJUSTED,
        ar_series=ar_series,
        model_version_id=mv.model_version_id,
        market_cap=1_234_000.0,
    )

    assert row.car == pytest.approx(compute_car(ar_series))
    assert row.ar_series == ar_series
    assert row.benchmark_model == "MARKET_ADJUSTED"
    assert row.market_cap == pytest.approx(1_234_000.0)
    assert row.event_id == ev.event_id
    assert row.model_version_id == mv.model_version_id


def test_market_cap_is_optional(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV06", retrieved_at=RETRIEVED)
    db_session.add(ev)
    mv = ModelVersion(model_kind="benchmark", version_label="mm-v1", valid_from=RETRIEVED)
    db_session.add(mv)
    db_session.flush()

    row = record_valuation_event_window(
        db_session,
        event_id=ev.event_id,
        window_pre=1,
        window_post=1,
        benchmark_model=BenchmarkModel.MARKET_MODEL,
        ar_series=[0.0, 0.0, 0.0],
        model_version_id=mv.model_version_id,
    )
    assert row.market_cap is None
