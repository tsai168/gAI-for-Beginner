"""WBS-B11 integration tests (ADR-0023 §3): R05 comparison report (CFL-06)
+ R06 external publication (CFL-08) — the two report types Work-2 §5
CFL_CONTRACT actually names, gated on the report row's *own* cfl_status.
Needs Postgres + migrations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from governance.publication import PublicationBlocked
from knowledge.db.base import RefEntityType
from knowledge.db.models import Event
from reports.comparison_report import submit_comparison_report
from reports.external_publication import (
    approve_external_publication,
    submit_for_external_publication,
)

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


# --- R05 --------------------------------------------------------------------


def test_submit_comparison_report_always_review_required(db_session) -> None:  # type: ignore[no-untyped-def]
    report, status = submit_comparison_report(db_session, subject_ref=uuid.uuid4())
    assert status == "REVIEW-REQUIRED"
    assert report.cfl_status == "REVIEW-REQUIRED"
    assert report.publication_tier == "MATERIAL_REVIEW"
    assert report.report_type == "COMPARISON"


# --- R06 --------------------------------------------------------------------


def _approved_event(db_session):  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV01", retrieved_at=RETRIEVED, pipeline_status="APPROVED")
    db_session.add(ev)
    db_session.flush()
    return ev


def test_submit_for_external_publication_is_review_required(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _approved_event(db_session)
    report, status = submit_for_external_publication(
        db_session, subject_ref=ev.event_id, subject_ref_type=RefEntityType.EVENT.value
    )
    assert status == "REVIEW-REQUIRED"
    assert report.publication_tier == "EXTERNAL_APPROVAL"


def test_approve_external_publication_moves_to_approved_and_publishes_event(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _approved_event(db_session)
    report, _status = submit_for_external_publication(
        db_session, subject_ref=ev.event_id, subject_ref_type=RefEntityType.EVENT.value
    )

    approved = approve_external_publication(db_session, report.research_report_id)
    assert approved.cfl_status == "APPROVED"

    db_session.refresh(ev)
    assert ev.pipeline_status == "PUBLISHED"


def test_approve_external_publication_missing_report_raises(db_session) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(LookupError):
        approve_external_publication(db_session, uuid.uuid4())


def test_approve_external_publication_wrong_report_type_raises(db_session) -> None:  # type: ignore[no-untyped-def]
    report, _status = submit_comparison_report(db_session, subject_ref=uuid.uuid4())
    with pytest.raises(PublicationBlocked):
        approve_external_publication(db_session, report.research_report_id)
