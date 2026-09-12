"""WBS-B8 integration tests (ADR-0020): G01 real rule engine
(`RuleBasedCflService`). Needs Postgres + migrations.

Per-CFL decisions are covered where they're exercised via their real
callers (test_credibility.py CFL-03, test_company_technology_product.py
CFL-02, test_relationship_event_evidence.py CFL-05/07,
test_materiality_marketcap_db.py CFL-04). This file covers what those
don't: CFL-01 (no wired caller yet — exercised directly), idempotent
re-submission, and that every decision leaves an audit trail (G03).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text

from governance.audit import list_decisions_for_row
from governance.cfl import CflId, RuleBasedCflService
from knowledge.db.base import CflStatus
from knowledge.db.models import Company, Event

pytestmark = pytest.mark.integration


def _company(db_session, **overrides):  # type: ignore[no-untyped-def]
    fields = {"company_name": "CFL-01 Test Co", "universe": "Watchlist"}
    fields.update(overrides)
    c = Company(**fields)
    db_session.add(c)
    db_session.flush()
    return c


def test_cfl01_high_confidence_and_verifiable_auto_passes(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session, confidence=Decimal("0.95"), stock_code="6666")
    status = RuleBasedCflService().submit_candidate(
        db_session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_01
    )
    assert status is CflStatus.AUTO_PASS


def test_cfl01_missing_confidence_requires_review(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session, stock_code="6667")
    status = RuleBasedCflService().submit_candidate(
        db_session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_01
    )
    assert status is CflStatus.REVIEW_REQUIRED


def test_cfl01_unverifiable_requires_review(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session, confidence=Decimal("0.99"))
    status = RuleBasedCflService().submit_candidate(
        db_session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_01
    )
    assert status is CflStatus.REVIEW_REQUIRED


def test_submit_candidate_is_idempotent_once_decided(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session, confidence=Decimal("0.95"), stock_code="6668")
    service = RuleBasedCflService()
    first = service.submit_candidate(
        db_session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_01
    )
    # Confidence changes after the fact; re-submitting must NOT re-decide —
    # once resolved, a CFL gate only moves via explicit human set_status.
    db_session.execute(
        text("UPDATE company SET confidence = :c WHERE company_id = :i"),
        {"c": Decimal("0.01"), "i": company.company_id},
    )
    second = service.submit_candidate(
        db_session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_01
    )
    assert first is CflStatus.AUTO_PASS
    assert second is CflStatus.AUTO_PASS


def test_cfl07_never_auto_passes_even_with_high_confidence(db_session) -> None:  # type: ignore[no-untyped-def]
    ev = Event(event_taxonomy_code="EV12", retrieved_at=datetime(2026, 9, 12, tzinfo=UTC))
    db_session.add(ev)
    db_session.flush()
    status = RuleBasedCflService().submit_candidate(
        db_session, table="event", row_id=ev.event_id, cfl_id=CflId.CFL_07
    )
    assert status is CflStatus.REVIEW_REQUIRED


def test_every_decision_is_audited(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session, confidence=Decimal("0.90"), stock_code="6669")
    RuleBasedCflService().submit_candidate(
        db_session, table="company", row_id=company.company_id, cfl_id=CflId.CFL_01
    )
    entries = list_decisions_for_row(db_session, table_name="company", row_id=company.company_id)
    assert len(entries) == 1
    assert entries[0].rule_ref == "CFL-01"
    assert entries[0].decision == "AUTO-PASS"
    assert entries[0].confidence == Decimal("0.9000")
