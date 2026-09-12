"""Shared helper for R02/R04/R05/R06 (WBS-B11, ADR-0023 §2). Private — not
part of the R01-R06 public surface, just avoids duplicating the "try to
complete the underlying event's pipeline_status" step.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from governance.publication import PublicationTier
from knowledge.db.base import CflStatus, PipelineStatus
from knowledge.db.models import Event
from knowledge.repository.event import advance_pipeline_status


def maybe_advance_event_to_published(
    session: Session,
    event: Event,
    *,
    publication_tier: PublicationTier,
    cfl_08_status: CflStatus | None,
) -> None:
    """Best-effort: only advances if the event is exactly at APPROVED (the
    one legal pre-state for PUBLISHED, Work-2 §3.2). An event elsewhere in
    its pipeline (not yet APPROVED, or already PUBLISHED) is left alone —
    publishing a report about it doesn't force the event's own state
    machine to jump."""
    if event.pipeline_status != PipelineStatus.APPROVED.value:
        return
    advance_pipeline_status(
        session,
        event,
        PipelineStatus.PUBLISHED.value,
        publication_tier=publication_tier,
        cfl_08_status=cfl_08_status,
    )
