"""K05 — Event repository: Revision Chain (WBS-B4b, ADR-0012 §3, CF-35/36).

`create_event` starts a new chain at revision_seq=1/ACTIVE. `correct_event`
and `withdraw_event` never mutate a row's substantive data: the old row
only has its `lifecycle_status` flipped to SUPERSEDED, and a brand new row
carries the revised data forward (Charter §20 — Immutable Event + Revision
Chain). Both only operate on the current head of a chain.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge.db.base import EventLifecycleStatus
from knowledge.db.models import Event

_HEAD_STATUSES = {EventLifecycleStatus.ACTIVE.value, EventLifecycleStatus.CORRECTED.value}

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
