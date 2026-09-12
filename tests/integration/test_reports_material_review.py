"""WBS-B11 integration tests (ADR-0023 §3): R02 company/event report + R04
event-study report — both gated on the underlying EVENT's own cfl_status
(no numbered CFL of their own). Needs Postgres + migrations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from governance.cfl import CflId, RuleBasedCflService
from governance.publication import PublicationBlocked
from knowledge.db.base import BenchmarkModel, CflStatus
from knowledge.db.models import Event, ModelVersion
from models.event_window import record_valuation_event_window
from reports.company_event_report import (
    classify_event_report_tier,
    publish_company_event_report,
)
from reports.event_study_report import publish_event_study_report

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


def _approved_event(db_session, *, materiality_score: float | None) -> Event:  # type: ignore[no-untyped-def]
    ev = Event(
        event_taxonomy_code="EV01",
        retrieved_at=RETRIEVED,
        materiality_score=materiality_score,
        pipeline_status="APPROVED",
    )
    db_session.add(ev)
    db_session.flush()
    return ev


# --- R02 ------------------------------------------------------------------------


def test_low_materiality_event_report_is_internal_auto(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _approved_event(db_session, materiality_score=20.0)
    assert classify_event_report_tier(ev) == "INTERNAL_AUTO"

    report = publish_company_event_report(db_session, ev.event_id)
    assert report.publication_tier == "INTERNAL_AUTO"

    db_session.refresh(ev)
    assert ev.pipeline_status == "PUBLISHED"  # Internal Auto needs no CFL-08 gate


def test_high_materiality_event_report_requires_event_approved(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(
        event_taxonomy_code="EV01",
        retrieved_at=RETRIEVED,
        materiality_score=90.0,
        pipeline_status="APPROVED",
        cfl_status="PENDING",
    )
    db_session.add(ev)
    db_session.flush()

    with pytest.raises(PublicationBlocked):
        publish_company_event_report(db_session, ev.event_id)


def test_high_materiality_event_report_succeeds_once_event_cfl_approved(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(
        event_taxonomy_code="EV01",
        retrieved_at=RETRIEVED,
        materiality_score=95.0,
        pipeline_status="APPROVED",
    )
    db_session.add(ev)
    db_session.flush()
    # PENDING can't jump straight to APPROVED (Charter §17 state machine) —
    # go through the real CFL-04 decision first (materiality_score=95 ->
    # REVIEW-REQUIRED), then a human approves it, same as production.
    RuleBasedCflService().submit_candidate(
        db_session, table="event", row_id=ev.event_id, cfl_id=CflId.CFL_04
    )
    RuleBasedCflService().set_status(
        db_session,
        table="event",
        row_id=ev.event_id,
        target=CflStatus.APPROVED,
        cfl_id=CflId.CFL_04,
    )
    db_session.refresh(ev)

    report = publish_company_event_report(db_session, ev.event_id)
    assert report.publication_tier == "MATERIAL_REVIEW"

    db_session.refresh(ev)
    assert ev.pipeline_status == "PUBLISHED"


def test_publish_company_event_report_missing_event_raises(db_session) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(LookupError):
        publish_company_event_report(db_session, uuid.uuid4())


# --- R04 ------------------------------------------------------------------------


def _model_version(db_session):  # type: ignore[no-untyped-def]
    mv = ModelVersion(model_kind="benchmark", version_label="r04-v1", valid_from=RETRIEVED)
    db_session.add(mv)
    db_session.flush()
    return mv


def test_event_study_report_requires_event_windows(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _approved_event(db_session, materiality_score=None)
    with pytest.raises(ValueError, match="valuation_event_window"):
        publish_event_study_report(db_session, ev.event_id)


def test_event_study_report_is_always_material_review(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(
        event_taxonomy_code="EV06",
        retrieved_at=RETRIEVED,
        pipeline_status="APPROVED",
    )
    db_session.add(ev)
    db_session.flush()
    mv = _model_version(db_session)
    record_valuation_event_window(
        db_session,
        event_id=ev.event_id,
        window_pre=1,
        window_post=1,
        benchmark_model=BenchmarkModel.MARKET_ADJUSTED,
        ar_series=[0.01, 0.02],
        model_version_id=mv.model_version_id,
    )
    # No materiality_score -> CFL-04 auto-passes (governance/cfl.py); still
    # needs the AUTO-PASS -> APPROVED step, same PENDING-can't-skip rule.
    RuleBasedCflService().submit_candidate(
        db_session, table="event", row_id=ev.event_id, cfl_id=CflId.CFL_04
    )
    RuleBasedCflService().set_status(
        db_session,
        table="event",
        row_id=ev.event_id,
        target=CflStatus.APPROVED,
        cfl_id=CflId.CFL_04,
    )
    db_session.refresh(ev)

    report = publish_event_study_report(db_session, ev.event_id)
    assert report.publication_tier == "MATERIAL_REVIEW"
    assert report.report_type == "EVENT_STUDY"

    db_session.refresh(ev)
    assert ev.pipeline_status == "PUBLISHED"
