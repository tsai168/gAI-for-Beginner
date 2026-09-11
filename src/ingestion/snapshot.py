"""P03 — snapshot / hash / version controller (WBS-B2).

Deterministic (L0): compute a content hash and record an immutable
``source_snapshot`` row. Re-capturing byte-identical content for the same
source is idempotent (unique on source_id + content_hash) — this also feeds
P02 dedup.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge.db.models import SourceSnapshot


def content_hash(raw: bytes) -> str:
    """Lower-case hex SHA-256 of the raw bytes."""
    return hashlib.sha256(raw).hexdigest()


def record_snapshot(
    session: Session,
    *,
    source_id: uuid.UUID,
    raw: bytes,
    retrieved_at: datetime,
    content_type: str | None = None,
    parser_version: str | None = None,
    source_version: str | None = None,
    snapshot_ref: str | None = None,
) -> SourceSnapshot:
    """Insert a snapshot, or return the existing one if this exact content
    was already captured for this source."""
    digest = content_hash(raw)
    existing = session.execute(
        select(SourceSnapshot).where(
            SourceSnapshot.source_id == source_id,
            SourceSnapshot.content_hash == digest,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    snap = SourceSnapshot(
        source_id=source_id,
        content_hash=digest,
        byte_size=len(raw),
        content_type=content_type,
        parser_version=parser_version,
        source_version=source_version,
        snapshot_ref=snapshot_ref,
        retrieved_at=retrieved_at,
    )
    session.add(snap)
    session.flush()
    return snap
