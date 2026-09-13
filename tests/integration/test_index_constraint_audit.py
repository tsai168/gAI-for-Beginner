"""ADR-0025 §2 (index/constraint audit, post-B12): the new CHECK
constraints actually reject out-of-range values at the DB level (not just
the application layer, which already validated these — M02/M03/M04/M05's
own `_check_scale`), and the new indexes are genuinely present. Needs
Postgres + migrations (0008_index_constraint_audit).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from knowledge.db.models import Company, Event

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 9, 0, tzinfo=UTC)


def test_company_confidence_out_of_range_rejected_at_db_level(db_session) -> None:  # type: ignore[no-untyped-def]
    company = Company(company_name="Constraint Test Co", universe="Watchlist")
    db_session.add(company)
    db_session.flush()

    with pytest.raises(DBAPIError, match="ck_company_confidence_range"):
        db_session.execute(
            text("UPDATE company SET confidence = 1.5 WHERE company_id = :i"),
            {"i": company.company_id},
        )
    db_session.rollback()


def test_event_materiality_score_out_of_range_rejected_at_db_level(db_session) -> None:  # type: ignore[no-untyped-def]
    event = Event(event_taxonomy_code="EV01", retrieved_at=RETRIEVED)
    db_session.add(event)
    db_session.flush()

    with pytest.raises(DBAPIError, match="ck_event_materiality_score_range"):
        db_session.execute(
            text("UPDATE event SET materiality_score = 150 WHERE event_id = :i"),
            {"i": event.event_id},
        )
    db_session.rollback()


def test_in_range_values_are_accepted(db_session) -> None:  # type: ignore[no-untyped-def]
    company = Company(company_name="In Range Co", universe="Watchlist", confidence=0.5)
    db_session.add(company)
    db_session.flush()  # would raise if the CHECK rejected a valid value
    assert float(company.confidence) == pytest.approx(0.5)


@pytest.mark.parametrize(
    "table,index_name",
    [
        ("company", "ix_company_cfl_status"),
        ("company", "ix_company_universe"),
        ("event", "ix_event_pipeline_status"),
        ("event", "ix_event_cfl_status"),
        ("event", "ix_event_entity_id"),
        ("evidence", "ix_evidence_cfl_status"),
        ("research_report", "ix_research_report_cfl_status"),
    ],
)
def test_index_exists(db_session, table: str, index_name: str) -> None:  # type: ignore[no-untyped-def]
    row = db_session.execute(
        text("SELECT 1 FROM pg_indexes WHERE tablename = :t AND indexname = :i"),
        {"t": table, "i": index_name},
    ).first()
    assert row is not None, f"expected index {index_name} on {table}"
