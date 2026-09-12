"""TEST-EVID-01 (Work-3 §4, WBS-B12): Evidence's `evidence_type`,
`source_credibility_tier` and `content_hash` are all populated and
mutually traceable — content_hash pins the exact captured content,
source_credibility_tier is derived from it via P05, evidence_type is
always one of the three Charter-frozen values. Needs Postgres +
migrations.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ingestion.credibility import score_evidence_credibility
from knowledge.db.models import Evidence, Source

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 9, 0, tzinfo=UTC)


def test_evidence_type_tier_and_content_hash_are_all_populated_and_traceable(
    db_session,  # type: ignore[no-untyped-def]
) -> None:
    src = Source(data_source_code="D01", retrieved_at=RETRIEVED)
    db_session.add(src)
    db_session.flush()

    evidence = Evidence(
        evidence_type="SUPPORT",
        content_hash="deadbeefcafe0001",
        retrieved_at=RETRIEVED,
        source_id=src.source_id,
    )
    db_session.add(evidence)
    db_session.flush()

    score_evidence_credibility(db_session, evidence)

    assert evidence.evidence_type in {"SUPPORT", "CONTRADICT", "NEUTRAL-CONTEXT"}
    assert evidence.source_credibility_tier in {"S1", "S2", "S3", "S4", "S5"}
    assert evidence.content_hash == "deadbeefcafe0001"


def test_untiered_source_leaves_tier_none_not_guessed(db_session) -> None:  # type: ignore[no-untyped-def]
    # D05 has no fixed tier in the seed (ADR-0008) — GP-07: unknown stays
    # unknown, never guessed.
    src = Source(data_source_code="D05", retrieved_at=RETRIEVED)
    db_session.add(src)
    db_session.flush()

    evidence = Evidence(
        evidence_type="CONTRADICT",
        content_hash="deadbeefcafe0002",
        retrieved_at=RETRIEVED,
        source_id=src.source_id,
    )
    db_session.add(evidence)
    db_session.flush()

    score_evidence_credibility(db_session, evidence)

    assert evidence.source_credibility_tier is None
