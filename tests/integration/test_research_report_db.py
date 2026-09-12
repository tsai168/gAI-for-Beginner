"""WBS-B11 integration tests (ADR-0023): research_report repository + CFL
guard trigger. Needs Postgres + migrations (0007_research_report)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from governance.publication import PublicationTier
from knowledge.db.base import ReportType
from knowledge.repository.research_report import create_report, get_report, list_reports

pytestmark = pytest.mark.integration


def test_create_and_get_report(db_session) -> None:  # type: ignore[no-untyped-def]
    subject = uuid.uuid4()
    report = create_report(
        db_session,
        report_type=ReportType.COMPANY_EVENT_REPORT,
        subject_ref=subject,
        publication_tier=PublicationTier.INTERNAL_AUTO,
    )
    assert report.cfl_status == "PENDING"
    assert report.version == 1

    fetched = get_report(db_session, report.research_report_id)
    assert fetched is not None
    assert fetched.subject_ref == subject


def test_get_report_not_found(db_session) -> None:  # type: ignore[no-untyped-def]
    assert get_report(db_session, uuid.uuid4()) is None


def test_list_reports_filters(db_session) -> None:  # type: ignore[no-untyped-def]
    subject = uuid.uuid4()
    create_report(
        db_session,
        report_type=ReportType.EVENT_STUDY,
        subject_ref=subject,
        publication_tier=PublicationTier.MATERIAL_REVIEW,
    )
    create_report(
        db_session,
        report_type=ReportType.DAILY_DIGEST,
        publication_tier=PublicationTier.INTERNAL_AUTO,
    )

    by_type = list_reports(db_session, report_type=ReportType.EVENT_STUDY.value)
    assert len(by_type) == 1
    assert by_type[0].subject_ref == subject

    by_subject = list_reports(db_session, subject_ref=subject)
    assert len(by_subject) == 1


def test_cfl_status_direct_write_blocked(db_session) -> None:  # type: ignore[no-untyped-def]
    report = create_report(
        db_session,
        report_type=ReportType.DAILY_DIGEST,
        publication_tier=PublicationTier.INTERNAL_AUTO,
    )
    with pytest.raises(DBAPIError):
        db_session.execute(
            text(
                "UPDATE research_report SET cfl_status = 'APPROVED' WHERE research_report_id = :i"
            ),
            {"i": report.research_report_id},
        )
    db_session.rollback()
