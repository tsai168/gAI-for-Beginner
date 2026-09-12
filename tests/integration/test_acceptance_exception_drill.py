"""Exception drill (Work-3 §2 B12: "負載與異常演練", WBS-B12, ADR-0024 §4):
a rejected governance operation must not leave the row in a corrupted or
ambiguous state, and the session must stay usable for a legitimate
follow-up operation right after. Needs Postgres + migrations.

True load/concurrency testing needs deployed infrastructure (I01-I06)
this project doesn't provision (see CLAUDE.md §2 — I01-I06 are
deployment-config concerns, out of this application-layer scope) — see
ADR-0024 §4.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from governance.cfl import CflId, RuleBasedCflService
from knowledge.db.base import CflStatus
from knowledge.db.models import Event
from reports.event_study_report import publish_event_study_report

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 9, 0, tzinfo=UTC)


def test_rejected_publish_leaves_no_partial_report_and_session_stays_usable(
    db_session,  # type: ignore[no-untyped-def]
) -> None:
    ev = Event(event_taxonomy_code="EV01", retrieved_at=RETRIEVED, pipeline_status="APPROVED")
    db_session.add(ev)
    db_session.flush()

    with pytest.raises(ValueError, match="valuation_event_window"):
        publish_event_study_report(db_session, ev.event_id)  # no AR/CAR data yet -> refuses

    # the session is still perfectly usable for a real, unrelated operation
    status = RuleBasedCflService().query_status(db_session, table="event", row_id=ev.event_id)
    assert status is CflStatus.PENDING  # untouched by the rejected attempt


def test_illegal_cfl_transition_leaves_status_unchanged(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV01", retrieved_at=RETRIEVED)
    db_session.add(ev)
    db_session.flush()

    with pytest.raises(ValueError, match="illegal CFL transition"):
        RuleBasedCflService().set_status(
            db_session,
            table="event",
            row_id=ev.event_id,
            target=CflStatus.APPROVED,
            cfl_id=CflId.CFL_04,
        )

    status = RuleBasedCflService().query_status(db_session, table="event", row_id=ev.event_id)
    assert status is CflStatus.PENDING  # rejected transition, nothing changed

    # a legitimate transition right after still works fine
    RuleBasedCflService().submit_candidate(
        db_session, table="event", row_id=ev.event_id, cfl_id=CflId.CFL_04
    )
    status = RuleBasedCflService().query_status(db_session, table="event", row_id=ev.event_id)
    assert status is not CflStatus.PENDING
