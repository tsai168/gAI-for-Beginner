"""A01 wiring (ADR-0026): `extract_evidence_from_snapshot` against a real
Postgres, with a fake `LLMClient` standing in for the real Anthropic call
(that part is exercised for real in test_extraction_llm.py, which skips
without ANTHROPIC_API_KEY). Needs Postgres + migrations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from agents.extraction import ExtractionRequest, extract_evidence_from_snapshot
from agents.roster import ExtractionAgent
from knowledge.db.base import CflStatus, EvidenceStage, EvidenceType
from knowledge.db.models import Company

pytestmark = pytest.mark.integration

RETRIEVED = datetime(2026, 9, 14, 9, 0, tzinfo=UTC)


@dataclass(slots=True, frozen=True)
class _FakeCandidate:
    matched_company_name: str | None
    unknown_company_mention: str | None
    evidence_type: EvidenceType
    evidence_stage: EvidenceStage | None
    directness: float
    independence: float
    temporal_quality: float
    specificity: float
    rationale: str


@dataclass(slots=True, frozen=True)
class _FakeResult:
    candidates: list[_FakeCandidate]


class _FakeLLMClient:
    def __init__(self, result: _FakeResult) -> None:
        self._result = result
        self.last_system: str | None = None
        self.last_user: str | None = None

    def parse_extraction(self, *, system: str, user: str) -> _FakeResult:
        self.last_system = system
        self.last_user = user
        return self._result


def _company(db_session, name: str = "Extraction Test Co") -> Company:
    c = Company(company_name=name, universe="Watchlist")
    db_session.add(c)
    db_session.flush()
    return c


def test_matched_company_evidence_is_linked(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    candidate = _FakeCandidate(
        matched_company_name=company.company_name,
        unknown_company_mention=None,
        evidence_type=EvidenceType.SUPPORT,
        evidence_stage=EvidenceStage.E3,
        directness=0.9,
        independence=0.8,
        temporal_quality=0.7,
        specificity=0.6,
        rationale="Company's own press release states this directly.",
    )
    client = _FakeLLMClient(_FakeResult(candidates=[candidate]))

    evidence, unknown = extract_evidence_from_snapshot(
        db_session,
        snapshot_text="irrelevant for a fake client",
        content_hash="hash-1",
        retrieved_at=RETRIEVED,
        source_id=None,
        source_credibility_tier="S2",
        watchlist_companies=[company],
        llm_client=client,
    )

    assert len(evidence) == 1
    assert evidence[0].entity_ref == company.company_id
    assert evidence[0].entity_ref_type == "company"
    assert evidence[0].evidence_type == "SUPPORT"
    assert evidence[0].evidence_stage == "E3"
    assert evidence[0].authority == pytest.approx(0.8)  # S2 -> 0.8
    assert evidence[0].directness == pytest.approx(0.9)
    assert unknown == []


def test_unknown_company_mention_is_not_linked_or_auto_created(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    candidate = _FakeCandidate(
        matched_company_name=None,
        unknown_company_mention="Totally New Startup Inc",
        evidence_type=EvidenceType.NEUTRAL_CONTEXT,
        evidence_stage=None,
        directness=0.5,
        independence=0.5,
        temporal_quality=0.5,
        specificity=0.5,
        rationale="Mentions a company not currently tracked.",
    )
    client = _FakeLLMClient(_FakeResult(candidates=[candidate]))

    evidence, unknown = extract_evidence_from_snapshot(
        db_session,
        snapshot_text="irrelevant",
        content_hash="hash-2",
        retrieved_at=RETRIEVED,
        source_id=None,
        source_credibility_tier=None,
        watchlist_companies=[company],
        llm_client=client,
    )

    assert len(evidence) == 1
    assert evidence[0].entity_ref is None
    assert evidence[0].entity_ref_type is None
    assert evidence[0].authority is None  # no tier given
    assert len(unknown) == 1
    assert unknown[0].raw_name == "Totally New Startup Inc"
    assert unknown[0].evidence_id == evidence[0].evidence_id

    # GP-07: never auto-create the mentioned company.
    still_only_one = db_session.execute(select(Company)).scalars().all()
    assert len(still_only_one) == 1
    assert still_only_one[0].company_id == company.company_id


def test_contradict_evidence_raises_cfl07(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    candidate = _FakeCandidate(
        matched_company_name=company.company_name,
        unknown_company_mention=None,
        evidence_type=EvidenceType.CONTRADICT,
        evidence_stage=None,
        directness=0.8,
        independence=0.8,
        temporal_quality=0.8,
        specificity=0.8,
        rationale="Conflicts with a previously recorded claim.",
    )
    client = _FakeLLMClient(_FakeResult(candidates=[candidate]))

    evidence, _ = extract_evidence_from_snapshot(
        db_session,
        snapshot_text="irrelevant",
        content_hash="hash-3",
        retrieved_at=RETRIEVED,
        source_id=None,
        source_credibility_tier="S1",
        watchlist_companies=[company],
        llm_client=client,
    )

    assert len(evidence) == 1
    db_session.refresh(evidence[0])
    # CFL-07: CONTRADICT evidence is never auto-pass (governance.cfl.NO_AUTO_PASS).
    assert evidence[0].cfl_status != CflStatus.AUTO_PASS.value


def test_empty_candidates_creates_no_evidence(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session)
    client = _FakeLLMClient(_FakeResult(candidates=[]))

    evidence, unknown = extract_evidence_from_snapshot(
        db_session,
        snapshot_text="pure noise, nothing relevant",
        content_hash="hash-4",
        retrieved_at=RETRIEVED,
        source_id=None,
        source_credibility_tier="S3",
        watchlist_companies=[company],
        llm_client=client,
    )

    assert evidence == []
    assert unknown == []


def test_prompt_includes_watchlist_company_names(db_session) -> None:  # type: ignore[no-untyped-def]
    company = _company(db_session, name="Prompt Visible Co")
    client = _FakeLLMClient(_FakeResult(candidates=[]))

    extract_evidence_from_snapshot(
        db_session,
        snapshot_text="some snapshot text",
        content_hash="hash-5",
        retrieved_at=RETRIEVED,
        source_id=uuid.uuid4(),
        source_credibility_tier="S1",
        watchlist_companies=[company],
        llm_client=client,
    )

    assert client.last_user is not None
    assert "Prompt Visible Co" in client.last_user
    assert "some snapshot text" in client.last_user


def test_extraction_agent_run_goes_through_g02_gate(db_session) -> None:  # type: ignore[no-untyped-def]
    """Not just the bare function — `ExtractionAgent().run()` (WBS-B6, G02)
    must actually reach `_perform` and produce a real result, same as any
    other agent action authorized under GP-21."""
    company = _company(db_session)
    candidate = _FakeCandidate(
        matched_company_name=company.company_name,
        unknown_company_mention=None,
        evidence_type=EvidenceType.SUPPORT,
        evidence_stage=None,
        directness=0.7,
        independence=0.7,
        temporal_quality=0.7,
        specificity=0.7,
        rationale="Via the agent's run() path.",
    )
    client = _FakeLLMClient(_FakeResult(candidates=[candidate]))
    request = ExtractionRequest(
        session=db_session,
        snapshot_text="irrelevant",
        content_hash="hash-6",
        retrieved_at=RETRIEVED,
        source_id=None,
        source_credibility_tier="S4",
        watchlist_companies=[company],
        llm_client=client,
    )

    outcome = ExtractionAgent().run(request)

    assert len(outcome.evidence) == 1
    assert outcome.evidence[0].entity_ref == company.company_id
    assert outcome.unknown_company_mentions == []
