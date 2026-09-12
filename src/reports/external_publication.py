"""R06 — Formal external publication package (WBS-B11, ADR-0023 §3,
Work-2 §5 CFL_CONTRACT: CFL-08, candidate R06, judge G06->U04; §4.2
POST /publications/{id}/approve).

`submit_for_external_publication` opens the CFL-08 gate (always
REVIEW-REQUIRED — CFL-08 is in `governance.cfl.NO_AUTO_PASS`, so an
External Approval package can never auto-pass, only a human via
`approve_external_publication` can move it to APPROVED).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from governance.cfl import CflId, CflService, default_cfl_service
from governance.publication import PublicationBlocked, PublicationTier
from knowledge.db.base import CflStatus, RefEntityType, ReportType
from knowledge.db.models import ResearchReport
from knowledge.repository.event import get_event
from knowledge.repository.research_report import create_report, get_report
from reports._common import maybe_advance_event_to_published


def submit_for_external_publication(
    session: Session,
    *,
    subject_ref: uuid.UUID,
    subject_ref_type: str = RefEntityType.EVENT.value,
    content_ref: str | None = None,
    cfl_service: CflService = default_cfl_service,
) -> tuple[ResearchReport, CflStatus]:
    report = create_report(
        session,
        report_type=ReportType.EXTERNAL_PUBLICATION,
        subject_ref=subject_ref,
        subject_ref_type=subject_ref_type,
        publication_tier=PublicationTier.EXTERNAL_APPROVAL,
        content_ref=content_ref,
    )
    status = cfl_service.submit_candidate(
        session,
        table="research_report",
        row_id=report.research_report_id,
        cfl_id=CflId.CFL_08,
    )
    return report, status


def approve_external_publication(
    session: Session,
    research_report_id: uuid.UUID,
    *,
    cfl_service: CflService = default_cfl_service,
) -> ResearchReport:
    """Backs `POST /publications/{id}/approve` (WBS-B9 stub, wired for real
    here). A Research Director's approval *is* the CFL-08
    REVIEW-REQUIRED -> APPROVED transition — this is a dedicated,
    R06-scoped entry point for exactly that; rejection still goes through
    the generic `POST /cfl/CFL-08/decision` (target=REJECTED)."""
    report = get_report(session, research_report_id)
    if report is None:
        raise LookupError(f"research_report {research_report_id} not found")
    if report.report_type != ReportType.EXTERNAL_PUBLICATION.value:
        raise PublicationBlocked(
            f"research_report {research_report_id} is {report.report_type}, "
            f"not {ReportType.EXTERNAL_PUBLICATION.value}"
        )

    cfl_service.set_status(
        session,
        table="research_report",
        row_id=research_report_id,
        target=CflStatus.APPROVED,
        cfl_id=CflId.CFL_08,
    )

    if report.subject_ref is not None and report.subject_ref_type == RefEntityType.EVENT.value:
        event = get_event(session, report.subject_ref)
        if event is not None:
            maybe_advance_event_to_published(
                session,
                event,
                publication_tier=PublicationTier.EXTERNAL_APPROVAL,
                cfl_08_status=CflStatus.APPROVED,
            )
    return report
