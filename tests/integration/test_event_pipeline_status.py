"""WBS-B8 integration tests (ADR-0020): K05 `advance_pipeline_status`
(Work-2 §3.2 state machine, TEST-EVENT-01) + G06 publication gate on the
final PUBLISHED step (CF-33, TEST-CFL-02). Needs Postgres + migrations."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from governance.publication import PublicationBlocked, PublicationTier
from knowledge.db.base import CflStatus
from knowledge.repository.event import advance_pipeline_status
from knowledge.repository.event import create_event as _create_event

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


def _event(db_session):  # type: ignore[no-untyped-def]
    return _create_event(db_session, retrieved_at=RETRIEVED, event_taxonomy_code="EV01")


def _walk_to(db_session, event, target_stage: str):  # type: ignore[no-untyped-def]
    # `event` already starts at DISCOVERED (create_event's server default) —
    # advancing *to* DISCOVERED would itself be an illegal self-transition.
    stages = (
        "FETCHED",
        "NORMALIZED",
        "EXTRACTED",
        "VERIFIED",
        "ANALYZED",
        "APPROVED",
    )
    for stage in stages:
        advance_pipeline_status(db_session, event, stage)
        if stage == target_stage:
            return event
    return event


def test_sequential_advance_is_allowed(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _event(db_session)
    advance_pipeline_status(db_session, ev, "FETCHED")
    assert ev.pipeline_status == "FETCHED"
    advance_pipeline_status(db_session, ev, "NORMALIZED")
    assert ev.pipeline_status == "NORMALIZED"


def test_skipping_a_stage_is_rejected(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _event(db_session)
    with pytest.raises(ValueError, match="illegal pipeline_status transition"):
        advance_pipeline_status(db_session, ev, "EXTRACTED")


def test_going_backward_is_rejected(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _event(db_session)
    advance_pipeline_status(db_session, ev, "FETCHED")
    with pytest.raises(ValueError, match="illegal pipeline_status transition"):
        advance_pipeline_status(db_session, ev, "DISCOVERED")


def test_internal_auto_publish_needs_no_cfl_gate(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _event(db_session)
    _walk_to(db_session, ev, "APPROVED")
    advance_pipeline_status(db_session, ev, "PUBLISHED")
    assert ev.pipeline_status == "PUBLISHED"


def test_external_approval_publish_blocked_without_cfl08_approved(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _event(db_session)
    _walk_to(db_session, ev, "APPROVED")
    with pytest.raises(PublicationBlocked):
        advance_pipeline_status(
            db_session,
            ev,
            "PUBLISHED",
            publication_tier=PublicationTier.EXTERNAL_APPROVAL,
            cfl_08_status=CflStatus.REVIEW_REQUIRED,
        )
    assert ev.pipeline_status == "APPROVED"


def test_external_approval_publish_allowed_once_cfl08_approved(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = _event(db_session)
    _walk_to(db_session, ev, "APPROVED")
    advance_pipeline_status(
        db_session,
        ev,
        "PUBLISHED",
        publication_tier=PublicationTier.EXTERNAL_APPROVAL,
        cfl_08_status=CflStatus.APPROVED,
    )
    assert ev.pipeline_status == "PUBLISHED"
