"""R05 — Comparison / competitive analysis report (WBS-B11, ADR-0023 §3,
Work-2 §5 CFL_CONTRACT: CFL-06, candidate A05, judge G01->U04).

A05 (`agents.roster.ComparisonAgent`) doesn't generate real comparison
content yet (WBS-B6, still `NotImplementedError`) — this module delivers
the governance shell for whenever it does: creating the `research_report`
row and submitting the CFL-06 candidate is real; `content_ref` carries
whatever comparison content the caller already has (opaque to this
module), never fabricated here.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from governance.cfl import CflId, CflService, default_cfl_service
from governance.publication import PublicationTier
from knowledge.db.base import CflStatus, RefEntityType, ReportType
from knowledge.db.models import ResearchReport
from knowledge.repository.research_report import create_report


def submit_comparison_report(
    session: Session,
    *,
    subject_ref: uuid.UUID,
    subject_ref_type: str = RefEntityType.COMPANY.value,
    content_ref: str | None = None,
    cfl_service: CflService = default_cfl_service,
) -> tuple[ResearchReport, CflStatus]:
    report = create_report(
        session,
        report_type=ReportType.COMPARISON,
        subject_ref=subject_ref,
        subject_ref_type=subject_ref_type,
        publication_tier=PublicationTier.MATERIAL_REVIEW,
        content_ref=content_ref,
    )
    status = cfl_service.submit_candidate(
        session,
        table="research_report",
        row_id=report.research_report_id,
        cfl_id=CflId.CFL_06,
    )
    return report, status
