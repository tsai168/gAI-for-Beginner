"""R02 — Company/Event research report (WBS-B11, ADR-0023 §3, Charter §18
"依 Materiality 分流").

Tier is derived from the underlying event's own `materiality_score` using
the *same* threshold G01's CFL-04 rule uses (`governance.cfl`) — not a new
number invented here. When Material Review applies, the gate checks the
event's *own* `cfl_status` (it must already be APPROVED via CFL-04) rather
than inventing a report-level CFL: Work-2 §5 CFL_CONTRACT never assigns a
numbered CFL to R02 itself (ADR-0023 §2).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from governance.cfl import HIGH_MATERIALITY_THRESHOLD, CflService, default_cfl_service
from governance.publication import PublicationTier, assert_publication_allowed
from knowledge.db.base import RefEntityType, ReportType
from knowledge.db.models import Event, ResearchReport
from knowledge.repository.event import get_event
from knowledge.repository.research_report import create_report
from reports._common import maybe_advance_event_to_published


def classify_event_report_tier(event: Event) -> PublicationTier:
    score = event.materiality_score
    if score is not None and float(score) >= HIGH_MATERIALITY_THRESHOLD:
        return PublicationTier.MATERIAL_REVIEW
    return PublicationTier.INTERNAL_AUTO


def publish_company_event_report(
    session: Session,
    event_id: uuid.UUID,
    *,
    content_ref: str | None = None,
    cfl_service: CflService = default_cfl_service,
) -> ResearchReport:
    event = get_event(session, event_id)
    if event is None:
        raise LookupError(f"event {event_id} not found")
    tier = classify_event_report_tier(event)
    # Re-read cfl_status through G01 (raw SQL, always current) rather than
    # trusting `event.cfl_status` as an ORM attribute — the ORM object may
    # have been loaded before a CFL decision was written elsewhere in this
    # session.
    gate_status = (
        cfl_service.query_status(session, table="event", row_id=event_id)
        if tier is not PublicationTier.INTERNAL_AUTO
        else None
    )
    assert_publication_allowed(tier, gate_status)

    report = create_report(
        session,
        report_type=ReportType.COMPANY_EVENT_REPORT,
        subject_ref=event_id,
        subject_ref_type=RefEntityType.EVENT.value,
        publication_tier=tier,
        content_ref=content_ref,
    )
    maybe_advance_event_to_published(session, event, publication_tier=tier, cfl_08_status=None)
    return report
