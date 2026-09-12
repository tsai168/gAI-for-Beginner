"""K-layer — research_report repository (WBS-B11, ADR-0023 §1).

Not numbered K01-K06 (same as `audit_log`) — `research_report` is a
§2.9-style gap-filled table (ADR-0003 G-1), not part of the frozen
DATA_MODEL's core six entities.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge.db.models import ResearchReport


def create_report(
    session: Session,
    *,
    report_type: str,
    publication_tier: str,
    subject_ref: uuid.UUID | None = None,
    subject_ref_type: str | None = None,
    content_ref: str | None = None,
) -> ResearchReport:
    report = ResearchReport(
        report_type=report_type,
        publication_tier=publication_tier,
        subject_ref=subject_ref,
        subject_ref_type=subject_ref_type,
        content_ref=content_ref,
    )
    session.add(report)
    session.flush()
    return report


def get_report(session: Session, research_report_id: uuid.UUID) -> ResearchReport | None:
    return session.get(ResearchReport, research_report_id)


def list_reports(
    session: Session,
    *,
    report_type: str | None = None,
    subject_ref: uuid.UUID | None = None,
    cfl_status: str | None = None,
) -> list[ResearchReport]:
    stmt = select(ResearchReport)
    if report_type is not None:
        stmt = stmt.where(ResearchReport.report_type == report_type)
    if subject_ref is not None:
        stmt = stmt.where(ResearchReport.subject_ref == subject_ref)
    if cfl_status is not None:
        stmt = stmt.where(ResearchReport.cfl_status == cfl_status)
    return list(session.execute(stmt).scalars())
