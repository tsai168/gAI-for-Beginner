"""R04 — Event study / CAR report (WBS-B11, ADR-0023 §3, CF-20/23; Charter
§18 "顯著 CAR" -> always Material Review).

Same posture as R02 (`company_event_report.py`): no numbered CFL is
assigned to R04 in Work-2 §5 CFL_CONTRACT, so the gate checks the
underlying event's own `cfl_status` rather than inventing one.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from governance.cfl import CflService, default_cfl_service
from governance.publication import PublicationTier, assert_publication_allowed
from knowledge.db.base import RefEntityType, ReportType
from knowledge.db.models import ResearchReport
from knowledge.repository.event import get_event
from knowledge.repository.research_report import create_report
from models.event_window import list_event_windows
from reports._common import maybe_advance_event_to_published


def publish_event_study_report(
    session: Session,
    event_id: uuid.UUID,
    *,
    content_ref: str | None = None,
    cfl_service: CflService = default_cfl_service,
) -> ResearchReport:
    event = get_event(session, event_id)
    if event is None:
        raise LookupError(f"event {event_id} not found")
    windows = list_event_windows(session, event_id)
    if not windows:
        raise ValueError(f"event {event_id} has no valuation_event_window rows yet (M06)")

    tier = PublicationTier.MATERIAL_REVIEW
    # Re-read cfl_status through G01 (raw SQL, always current) rather than
    # trusting `event.cfl_status` as an ORM attribute — see
    # company_event_report.py for the same fix and why.
    gate_status = cfl_service.query_status(session, table="event", row_id=event_id)
    assert_publication_allowed(tier, gate_status)

    report = create_report(
        session,
        report_type=ReportType.EVENT_STUDY,
        subject_ref=event_id,
        subject_ref_type=RefEntityType.EVENT.value,
        publication_tier=tier,
        content_ref=content_ref,
    )
    maybe_advance_event_to_published(session, event, publication_tier=tier, cfl_08_status=None)
    return report
