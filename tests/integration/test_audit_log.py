"""WBS-B8 integration tests (ADR-0020): G03 audit log (`governance.audit`).
Needs Postgres + migrations (0006_audit_log)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from governance.audit import list_decisions_for_row, record_decision

pytestmark = pytest.mark.integration


def test_record_decision_round_trips(db_session) -> None:  # type: ignore[no-untyped-def]
    row_id = uuid.uuid4()
    entry = record_decision(
        db_session,
        rule_ref="CFL-03",
        table_name="evidence",
        row_id=row_id,
        decision="AUTO-PASS",
        confidence=0.75,
    )
    assert entry.audit_log_id is not None
    fetched = list_decisions_for_row(db_session, table_name="evidence", row_id=row_id)
    assert len(fetched) == 1
    assert fetched[0].decision == "AUTO-PASS"


def test_list_decisions_for_row_is_chronological(db_session) -> None:  # type: ignore[no-untyped-def]
    row_id = uuid.uuid4()
    record_decision(
        db_session, rule_ref="CFL-04", table_name="event", row_id=row_id, decision="AUTO-PASS"
    )
    record_decision(
        db_session,
        rule_ref="CFL-04",
        table_name="event",
        row_id=row_id,
        decision="APPROVED",
    )
    entries = list_decisions_for_row(db_session, table_name="event", row_id=row_id)
    assert [e.decision for e in entries] == ["AUTO-PASS", "APPROVED"]


def test_audit_log_is_append_only(db_session) -> None:  # type: ignore[no-untyped-def]
    entry = record_decision(
        db_session,
        rule_ref="CFL-01",
        table_name="company",
        row_id=uuid.uuid4(),
        decision="REVIEW-REQUIRED",
    )
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE audit_log SET decision = 'APPROVED' WHERE audit_log_id = :i"),
            {"i": entry.audit_log_id},
        )
    db_session.rollback()
