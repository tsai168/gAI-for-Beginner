"""TEST-E2E-01 (Work-3 §4, WBS-B12, ADR-0024): a full daily-pipeline run,
DISCOVERED -> ... -> PUBLISHED, chaining real modules end to end exactly
as Work-2 §3.2 describes.

A01 (LLM-based Entity/Event extraction, EXTRACTED stage) has no real
implementation yet (no LLM integration built — agents/roster.py's
ExtractionAgent still raises NotImplementedError). That is the one
deliberately-simulated step: rather than call a module that doesn't
exist, this test constructs the Evidence row A01 would eventually
produce and moves on. Every other stage — P01 fetch/register, P04 time
normalization, P05 source credibility (+ CFL-03), M05 materiality
(+ CFL-04), G01 manual approval, R02 publish (+ G06 gate) — is real
production code. Needs Postgres + migrations.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from governance.audit import list_decisions_for_row
from governance.cfl import CflId, RuleBasedCflService
from ingestion.credibility import score_evidence_credibility
from ingestion.fetch import FixtureAdapter, fetch_and_register
from ingestion.time_normalize import RawTimeInput, normalize_observed_time
from knowledge.db.base import CflStatus, PipelineStatus, RefEntityType
from knowledge.repository.company import create_company
from knowledge.repository.event import advance_pipeline_status
from knowledge.repository.event import create_event as _create_event
from knowledge.repository.evidence import create_evidence
from models.materiality import MaterialityFactors, score_event_materiality
from reports.company_event_report import publish_company_event_report

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 12, 9, 0, tzinfo=UTC)


def test_full_daily_pipeline_discover_to_publish(db_session) -> None:  # type: ignore[no-untyped-def]
    # --- DISCOVERED ---------------------------------------------------------
    # W01/W02 would have queued this source; a company already on the
    # Watchlist gets a new press release.
    company = create_company(db_session, company_name="E2E Test Co", universe="Watchlist")
    adapter = FixtureAdapter(
        "D02", payloads={"pr": b"E2E Test Co announces new customer qualification"}
    )
    registered = fetch_and_register(db_session, adapter, {"key": "pr"})
    event = _create_event(
        db_session,
        retrieved_at=RETRIEVED,
        event_taxonomy_code="EV03",  # Qualification
        entity_id=company.company_id,
        source_id=registered.source.source_id,
    )
    assert event.pipeline_status == PipelineStatus.DISCOVERED.value

    # --- FETCHED -------------------------------------------------------------
    # P01 already ran above (fetch_and_register); this just advances the
    # formal state machine to match.
    advance_pipeline_status(db_session, event, PipelineStatus.FETCHED.value)

    # --- NORMALIZED ------------------------------------------------------------
    # P04 time normalization (P02 dedup / P06 trading-day alignment already
    # have their own dedicated coverage — test_fetch_dedup.py /
    # test_trading_calendar.py — not duplicated here).
    observed = normalize_observed_time(
        retrieved_at=RETRIEVED, published_at=RawTimeInput(value=RETRIEVED)
    )
    assert observed.published_at == RETRIEVED
    advance_pipeline_status(db_session, event, PipelineStatus.NORMALIZED.value)

    # --- EXTRACTED -------------------------------------------------------------
    # A01 (see module docstring): the one simulated step.
    evidence = create_evidence(
        db_session,
        evidence_type="SUPPORT",
        content_hash=registered.snapshot.content_hash,
        retrieved_at=RETRIEVED,
        entity_ref=event.event_id,
        entity_ref_type=RefEntityType.EVENT.value,
        source_id=registered.source.source_id,
    )
    advance_pipeline_status(db_session, event, PipelineStatus.EXTRACTED.value)

    # --- VERIFIED -------------------------------------------------------------
    # P05 real source-credibility scoring + its CFL-03 gate.
    cfl03_status = score_evidence_credibility(db_session, evidence)
    assert evidence.source_credibility_tier == "S2"  # D02 = S2 (ADR-0008 seed)
    assert cfl03_status is CflStatus.AUTO_PASS  # known official source
    advance_pipeline_status(db_session, event, PipelineStatus.VERIFIED.value)

    # --- ANALYZED -------------------------------------------------------------
    # M05 real materiality scoring + its CFL-04 gate.
    factors = MaterialityFactors(
        cpo_relevance=60,
        evidence_strength=60,
        commercial_impact=55,
        ecosystem_impact=50,
        novelty=40,
    )
    cfl04_status = score_event_materiality(db_session, event, factors)
    assert cfl04_status is CflStatus.AUTO_PASS  # score (55) below CFL-04's Review threshold
    advance_pipeline_status(db_session, event, PipelineStatus.ANALYZED.value)

    # --- APPROVED -------------------------------------------------------------
    # G01 already resolved CFL-04 above (AUTO-PASS); Work-2 §3.2 describes
    # APPROVED as "通過對應 CFL 規則之人工或自動核准" — confirm it through.
    RuleBasedCflService().set_status(
        db_session,
        table="event",
        row_id=event.event_id,
        target=CflStatus.APPROVED,
        cfl_id=CflId.CFL_04,
    )
    advance_pipeline_status(db_session, event, PipelineStatus.APPROVED.value)

    # --- PUBLISHED -------------------------------------------------------------
    # R02, gated by G06 (Internal Auto here — low materiality).
    report = publish_company_event_report(db_session, event.event_id)
    db_session.refresh(event)
    assert event.pipeline_status == PipelineStatus.PUBLISHED.value
    assert report.report_type == "COMPANY_EVENT_REPORT"
    assert report.publication_tier == "INTERNAL_AUTO"

    # --- Auditability (Charter §22, CF-45) ---------------------------------
    # Two real governance actions happened against this event: G01's own
    # AUTO-PASS decision (score_event_materiality's submit_candidate), then
    # the separate human-confirmed APPROVED transition (set_status above) —
    # G03 logs both, not just the latest.
    event_decisions = list_decisions_for_row(db_session, table_name="event", row_id=event.event_id)
    assert [d.rule_ref for d in event_decisions] == ["CFL-04", "CFL-04"]
    assert [d.decision for d in event_decisions] == ["AUTO-PASS", "APPROVED"]
    evidence_decisions = list_decisions_for_row(
        db_session, table_name="evidence", row_id=evidence.evidence_id
    )
    assert [d.rule_ref for d in evidence_decisions] == ["CFL-03"]
