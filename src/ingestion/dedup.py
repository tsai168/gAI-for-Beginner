"""P02 — hash-based content dedup (WBS-B3a).

Deterministic (L0). Hash only — semantic / entity similarity is K04's job,
not P02 (ADR-0006 G4-11). The verdict lets the pipeline skip LLM work on
content already seen (Charter §19, Deterministic First).
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ingestion.snapshot import content_hash
from knowledge.db.models import SourceSnapshot


class DedupVerdict(enum.StrEnum):
    NEW = "NEW"
    DUPLICATE_SAME_SOURCE = "DUPLICATE_SAME_SOURCE"
    DUPLICATE_OTHER_SOURCE = "DUPLICATE_OTHER_SOURCE"


def _hashes_for(session: Session, digest: str) -> list[uuid.UUID]:
    return list(
        session.execute(
            select(SourceSnapshot.source_id).where(SourceSnapshot.content_hash == digest)
        ).scalars()
    )


def classify(session: Session, *, raw: bytes, source_id: uuid.UUID | None = None) -> DedupVerdict:
    digest = content_hash(raw)
    seen = _hashes_for(session, digest)
    if not seen:
        return DedupVerdict.NEW
    if source_id is not None and source_id in seen:
        return DedupVerdict.DUPLICATE_SAME_SOURCE
    return DedupVerdict.DUPLICATE_OTHER_SOURCE


def is_duplicate(session: Session, *, raw: bytes, source_id: uuid.UUID | None = None) -> bool:
    return classify(session, raw=raw, source_id=source_id) is not DedupVerdict.NEW
