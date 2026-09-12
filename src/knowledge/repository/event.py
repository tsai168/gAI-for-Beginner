"""K05 — Event repository: Revision Chain (WBS-B4b, ADR-0012 §3, CF-35/36)
+ pipeline_status state machine (WBS-B8, ADR-0020, Work-2 §3.2).

`create_event` starts a new chain at revision_seq=1/ACTIVE. `correct_event`
and `withdraw_event` never mutate a row's substantive data: the old row
only has its `lifecycle_status` flipped to SUPERSEDED, and a brand new row
carries the revised data forward (Charter §20 — Immutable Event + Revision
Chain). Both only operate on the current head of a chain.

`advance_pipeline_status` enforces Work-2 §3.2's DISCOVERED -> ... ->
PUBLISHED sequence strictly (one stage at a time, no skipping, no going
back — Work-3 TEST-EVENT-01) and, for the final APPROVED -> PUBLISHED step,
delegates to G06 (`governance.publication`) so that step can never bypass
its required CFL-08 approval for tiers that need one (CF-33; TEST-CFL-02).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from governance.publication import PublicationTier, assert_publication_allowed
from knowledge.db.base import CflStatus, EventLifecycleStatus, PipelineStatus
from knowledge.db.models import Event

_HEAD_STATUSES = {EventLifecycleStatus.ACTIVE.value, EventLifecycleStatus.CORRECTED.value}
_PIPELINE_ORDER: tuple[PipelineStatus, ...] = tuple(PipelineStatus)
_PIPELINE_INDEX: dict[str, int] = {s.value: i for i, s in enumerate(_PIPELINE_ORDER)}

_COPY_FIELDS = (
    "project_id",
    "entity_id",
    "source_id",
    "event_taxonomy_code",
    "materiality_score",
    "version",
    "correlation_id",
    "causation_id",
    "evidence_ids",
    "pipeline_status",
    "occurred_at",
    "published_at",
    "retrieved_at",
    "market_known_at",
    "event_trading_date",
    "time_basis",
    "time_precision",
    "time_confidence",
    "valid_from",
    "valid_to",
)


def create_event(
    session: Session, *, event_taxonomy_code: str, retrieved_at: Any, **fields: Any
) -> Event:
    event = Event(event_taxonomy_code=event_taxonomy_code, retrieved_at=retrieved_at, **fields)
    session.add(event)
    session.flush()
    return event


def get_event(session: Session, event_id: uuid.UUID) -> Event | None:
    return session.get(Event, event_id)


def _require_head(event: Event) -> None:
    if event.lifecycle_status not in _HEAD_STATUSES:
        raise ValueError(
            f"event {event.event_id} is {event.lifecycle_status}, not a chain head "
            f"({sorted(_HEAD_STATUSES)}) — fetch the current head first (get_latest)"
        )


def _new_revision(
    session: Session, old: Event, *, lifecycle_status: str, changes: dict[str, Any]
) -> Event:
    _require_head(old)
    old.lifecycle_status = EventLifecycleStatus.SUPERSEDED.value

    payload: dict[str, Any] = {field: getattr(old, field) for field in _COPY_FIELDS}
    payload.update(changes)
    new_event = Event(
        revision_of_event_id=old.event_id,
        revision_seq=old.revision_seq + 1,
        lifecycle_status=lifecycle_status,
        **payload,
    )
    session.add(new_event)
    session.flush()
    return new_event


def correct_event(session: Session, event: Event, *, changes: dict[str, Any]) -> Event:
    return _new_revision(
        session, event, lifecycle_status=EventLifecycleStatus.CORRECTED.value, changes=changes
    )


def withdraw_event(session: Session, event: Event) -> Event:
    return _new_revision(
        session, event, lifecycle_status=EventLifecycleStatus.WITHDRAWN.value, changes={}
    )


def get_root(session: Session, event_id: uuid.UUID) -> Event:
    event = session.get(Event, event_id)
    if event is None:
        raise LookupError(f"event {event_id} not found")
    while event.revision_of_event_id is not None:
        parent = session.get(Event, event.revision_of_event_id)
        if parent is None:
            break
        event = parent
    return event


def get_latest(session: Session, event_id: uuid.UUID) -> Event:
    event = session.get(Event, event_id)
    if event is None:
        raise LookupError(f"event {event_id} not found")
    while True:
        child = session.execute(
            select(Event).where(Event.revision_of_event_id == event.event_id)
        ).scalar_one_or_none()
        if child is None:
            return event
        event = child


def list_revision_chain(session: Session, event_id: uuid.UUID) -> list[Event]:
    root = get_root(session, event_id)
    chain = [root]
    current = root
    while True:
        child = session.execute(
            select(Event).where(Event.revision_of_event_id == current.event_id)
        ).scalar_one_or_none()
        if child is None:
            break
        chain.append(child)
        current = child
    return chain


def _assert_valid_pipeline_transition(current: str, target: str) -> None:
    if current not in _PIPELINE_INDEX or target not in _PIPELINE_INDEX:
        raise ValueError(f"unknown pipeline_status {current!r} -> {target!r}")
    if _PIPELINE_INDEX[target] != _PIPELINE_INDEX[current] + 1:
        raise ValueError(
            f"illegal pipeline_status transition {current} -> {target} "
            "(Work-2 §3.2: must advance exactly one stage at a time)"
        )


def advance_pipeline_status(
    session: Session,
    event: Event,
    target: str,
    *,
    publication_tier: PublicationTier = PublicationTier.INTERNAL_AUTO,
    cfl_08_status: CflStatus | None = None,
) -> Event:
    """`publication_tier`/`cfl_08_status` only matter for the final
    APPROVED -> PUBLISHED step (see module docstring); they default to the
    Charter §18 "event list" case (Internal Auto, no CFL-08 needed) since
    R06 (WBS-B11) doesn't exist yet to classify a real tier."""
    _assert_valid_pipeline_transition(event.pipeline_status, target)
    if target == PipelineStatus.PUBLISHED.value:
        assert_publication_allowed(publication_tier, cfl_08_status)
    event.pipeline_status = target
    session.flush()
    return event
