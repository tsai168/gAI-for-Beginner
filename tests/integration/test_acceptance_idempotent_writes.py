"""TEST-WF-01, part 2 of 2 (Work-3 §4, WBS-B12, ADR-0024 §2): calling P03's
idempotent write path twice — simulating what a retried activity does
after its first attempt's write actually succeeded but the ack was lost —
produces exactly one row, never two. Needs Postgres + migrations.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from ingestion.snapshot import record_snapshot
from knowledge.db.models import Source, SourceSnapshot

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 9, 0, tzinfo=UTC)


def test_retried_snapshot_write_does_not_duplicate(db_session) -> None:  # type: ignore[no-untyped-def]
    src = Source(data_source_code="D01", retrieved_at=RETRIEVED)
    db_session.add(src)
    db_session.flush()

    raw = b"same payload, retried after a lost ack"
    first_attempt = record_snapshot(
        db_session, source_id=src.source_id, raw=raw, retrieved_at=RETRIEVED
    )
    retried_attempt = record_snapshot(
        db_session, source_id=src.source_id, raw=raw, retrieved_at=RETRIEVED
    )

    assert retried_attempt.source_snapshot_id == first_attempt.source_snapshot_id
    count = db_session.execute(
        select(func.count())
        .select_from(SourceSnapshot)
        .where(SourceSnapshot.source_id == src.source_id)
    ).scalar_one()
    assert count == 1
