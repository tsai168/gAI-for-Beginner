"""WBS-B3b integration test: P05 credibility scorer (ADR-0010 §4). Needs
Postgres + migrations (D01–D08 seed from migration 0002)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ingestion.credibility import resolve_source_tier, score_evidence_credibility
from knowledge.db.base import CflStatus
from knowledge.db.models import Evidence, Source

pytestmark = pytest.mark.integration


def _make_source(db_session, data_source_code: str) -> Source:
    src = Source(data_source_code=data_source_code, retrieved_at=datetime.now(UTC))
    db_session.add(src)
    db_session.flush()
    return src


def test_resolve_source_tier_known(db_session) -> None:  # type: ignore[no-untyped-def]
    src = _make_source(db_session, "D01")
    assert resolve_source_tier(db_session, src.source_id) == "S1"


def test_resolve_source_tier_untiered_source(db_session) -> None:  # type: ignore[no-untyped-def]
    src = _make_source(db_session, "D05")
    assert resolve_source_tier(db_session, src.source_id) is None


def test_score_evidence_credibility_sets_tier_and_raises_cfl03(db_session) -> None:  # type: ignore[no-untyped-def]
    src = _make_source(db_session, "D02")
    ev = Evidence(
        source_id=src.source_id,
        evidence_type="SUPPORT",
        content_hash="deadbeef",
        retrieved_at=datetime.now(UTC),
    )
    db_session.add(ev)
    db_session.flush()

    status = score_evidence_credibility(db_session, ev)

    assert ev.source_credibility_tier == "S2"
    assert status is CflStatus.PENDING  # B1 G01 stub; B8 supplies the real rule


def test_score_evidence_credibility_without_source_leaves_tier_none(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Evidence(
        evidence_type="SUPPORT",
        content_hash="cafef00d",
        retrieved_at=datetime.now(UTC),
    )
    db_session.add(ev)
    db_session.flush()

    score_evidence_credibility(db_session, ev)

    assert ev.source_credibility_tier is None
