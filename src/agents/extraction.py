"""A01 — Extraction agent (WBS-B6, ADR-0026): the first real LLM integration
in this codebase. Charter/Work-1-3 name Claude as the sole LLM supplier but
define no prompt, output schema, or per-source extraction rule (see
`agents/base.py`'s docstring) — that gap is what ADR-0026 closes for a
deliberately narrow v1 slice, confirmed with the Research Director before
writing any of this:

- One snapshot of raw text -> zero or more Evidence candidates (never a
  single fixed unit — one announcement commonly covers several distinct
  claims).
- Evidence is linked to an *existing* tracked Company (`entity_ref_type=
  "company"`) by name match only. A text mention that matches no tracked
  company is never used to auto-create one (GP-07: no guessed entities) —
  it comes back as an `UnknownCompanyMention` for a human to triage.
- CF1 Source Authority (`evidence.authority`) is *not* LLM-judged — it is
  a fixed function of `source_credibility_tier`, already computed
  deterministically by P05 before this runs. The same source's reliability
  shouldn't drift depending on which sentence happened to be extracted.
- Event creation/matching (`event_taxonomy_code`, attaching evidence to a
  specific Event) is explicitly OUT of this slice — deciding whether a
  mention is a new Event or belongs to one already tracked needs temporal
  dedup logic this pass doesn't attempt. Evidence produced here is
  Company-linked only; wiring it to Events is a later increment.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import anthropic
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from knowledge.db.base import EvidenceStage, EvidenceType, RefEntityType, SourceTier
from knowledge.db.models import Company, Evidence
from knowledge.repository.evidence import create_evidence, record_contradiction

DEFAULT_MODEL_ID = "claude-sonnet-5"

# ADR-0026 §2: CF1 Source Authority derived from the tier P05 already
# resolved, not guessed per candidate. An implementation default (like
# ADR-0013's CF1-CF4 weights), not a Frozen Decision — adjustable.
_AUTHORITY_BY_TIER: dict[str, float] = {
    SourceTier.S1: 1.0,
    SourceTier.S2: 0.8,
    SourceTier.S3: 0.6,
    SourceTier.S4: 0.4,
    SourceTier.S5: 0.2,
}


def authority_from_source_tier(tier: str | None) -> float | None:
    if tier is None:
        return None
    return _AUTHORITY_BY_TIER.get(tier)


class _ExtractedCandidate(BaseModel):
    matched_company_name: str | None = Field(
        default=None,
        description="Exact company_name from the provided watchlist this item is about; "
        "null if none match.",
    )
    unknown_company_mention: str | None = Field(
        default=None,
        description="Verbatim company name mentioned in the text that is NOT in the "
        "provided list; null otherwise.",
    )
    evidence_type: EvidenceType
    evidence_stage: EvidenceStage | None = Field(
        default=None,
        description="E0-E6 per the ladder given in the system prompt; null if the text "
        "does not clearly support any stage on that ladder — never guess one.",
    )
    directness: float = Field(ge=0.0, le=1.0)
    independence: float = Field(ge=0.0, le=1.0)
    temporal_quality: float = Field(ge=0.0, le=1.0)
    specificity: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(
        description="One sentence a human reviewer can use to sanity-check this item."
    )


class _ExtractionResult(BaseModel):
    candidates: list[_ExtractedCandidate]


@dataclass(slots=True, frozen=True)
class UnknownCompanyMention:
    """A01 v1 never auto-creates a Company (ADR-0026 §3) — this is the
    human-review record the caller is responsible for surfacing instead of
    a persisted review-queue row (no new table for a v1 slice this narrow)."""

    raw_name: str
    evidence_id: uuid.UUID | None
    rationale: str


class LLMClient(Protocol):
    def parse_extraction(self, *, system: str, user: str) -> _ExtractionResult: ...


class AnthropicExtractionClient:
    """Wraps `anthropic.Anthropic().messages.parse()` (structured JSON
    output validated against `_ExtractionResult`). `anthropic.Anthropic()`
    resolves credentials from the environment on its own (ANTHROPIC_API_KEY
    etc.) — never pass a key explicitly here."""

    def __init__(self, *, model: str | None = None) -> None:
        self._client = anthropic.Anthropic()
        self._model = model or os.environ.get("LLM_MODEL_ID") or DEFAULT_MODEL_ID

    def parse_extraction(self, *, system: str, user: str) -> _ExtractionResult:
        max_tokens = int(os.environ.get("LLM_MAX_OUTPUT_TOKENS") or "4096")
        response = self._client.messages.parse(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=_ExtractionResult,
        )
        if response.parsed_output is None:
            raise ValueError(
                f"model returned no parsed output (stop_reason={response.stop_reason!r})"
            )
        return response.parsed_output


_SYSTEM_PROMPT = """You are A01, the extraction agent of a CPO/silicon-photonics \
industry research system (Charter §17, AGENT_SPEC A01, autonomy level L1). \
Your only job is to turn one raw source snapshot into structured evidence \
candidates — you have NO approval or publication authority, and nothing you \
output is treated as a confirmed fact. A human always reviews it later.

For each distinct factual claim in the text (a single snapshot commonly \
contains several), produce one candidate with:

- matched_company_name: the exact name, copied verbatim, of whichever \
company in the provided list this claim is about. Null if none match.
- unknown_company_mention: if the claim is clearly about a company that is \
NOT in the provided list, the verbatim name as it appears in the text. \
Null otherwise. Never invent or normalize a name — copy it exactly as \
written.
- evidence_type: SUPPORT (backs the claim), CONTRADICT (conflicts with a \
claim already believed true), or NEUTRAL-CONTEXT (relevant background, \
neither).
- evidence_stage: which of these seven stages the claim best supports, or \
null if the text does not clearly reach any of them — absence of evidence \
is not evidence of the earliest stage, so never default to E0:
  E0 Rumor / Mention · E1 Technology Capability · E2 Development / Sampling \
· E3 Qualification / Validation · E4 Design-in / Customer Adoption · \
E5 Production / Shipment · E6 Revenue Contribution
- directness (0-1): 1.0 = a primary, first-hand claim (the company's own \
filing/announcement stating the fact directly); lower for secondhand \
reporting, paraphrase, or inference.
- independence (0-1): 1.0 = this claim stands on its own account, not \
merely restating something already reported elsewhere in the same text; \
lower when it is clearly derivative of another claim in the same snapshot.
- temporal_quality (0-1): 1.0 = the claim states or clearly implies a \
specific, recent point in time; lower for vague, old, or undated claims.
- specificity (0-1): 1.0 = concrete, verifiable details (numbers, named \
products, named parties, dates); lower for vague or generic statements.
- rationale: one sentence a human reviewer can use to sanity-check your \
classification.

If the text supports no claims about any given company at all (pure noise, \
unrelated content), return an empty candidates list. Never guess a value \
you are not confident in — leave evidence_stage null rather than pick one \
that only loosely fits."""


def _build_user_prompt(*, snapshot_text: str, watchlist_company_names: Sequence[str]) -> str:
    company_list = (
        "\n".join(f"- {name}" for name in watchlist_company_names) or "(none currently tracked)"
    )
    return (
        f"Companies currently tracked by this system:\n{company_list}\n\n"
        f"Source snapshot text:\n---\n{snapshot_text}\n---"
    )


@dataclass(slots=True, frozen=True)
class ExtractionRequest:
    """`agents.roster.ExtractionAgent`'s `run()` payload — `Agent.run()`
    takes `payload: Any`, so this is the concrete shape A01 expects."""

    session: Session
    snapshot_text: str
    content_hash: str
    retrieved_at: datetime
    source_id: uuid.UUID | None
    source_credibility_tier: str | None
    watchlist_companies: Sequence[Company]
    llm_client: LLMClient | None = None


@dataclass(slots=True, frozen=True)
class ExtractionOutcome:
    evidence: list[Evidence]
    unknown_company_mentions: list[UnknownCompanyMention]


def extract_evidence_from_snapshot(
    session: Session,
    *,
    snapshot_text: str,
    content_hash: str,
    retrieved_at: datetime,
    source_id: uuid.UUID | None,
    source_credibility_tier: str | None,
    watchlist_companies: Sequence[Company],
    llm_client: LLMClient | None = None,
) -> tuple[list[Evidence], list[UnknownCompanyMention]]:
    """One snapshot -> zero or more Evidence rows (module docstring). Each
    CONTRADICT candidate is also routed through `record_contradiction`
    (CFL-07) — A01 must not bypass G01 (CLAUDE.md §4)."""
    client = llm_client or AnthropicExtractionClient()
    name_to_company = {c.company_name: c for c in watchlist_companies}
    result = client.parse_extraction(
        system=_SYSTEM_PROMPT,
        user=_build_user_prompt(
            snapshot_text=snapshot_text, watchlist_company_names=list(name_to_company)
        ),
    )
    authority = authority_from_source_tier(source_credibility_tier)

    created: list[Evidence] = []
    unknown: list[UnknownCompanyMention] = []
    for candidate in result.candidates:
        company = (
            name_to_company.get(candidate.matched_company_name)
            if candidate.matched_company_name
            else None
        )
        evidence = create_evidence(
            session,
            evidence_type=candidate.evidence_type.value,
            content_hash=content_hash,
            retrieved_at=retrieved_at,
            source_id=source_id,
            entity_ref=company.company_id if company is not None else None,
            entity_ref_type=RefEntityType.COMPANY.value if company is not None else None,
            evidence_stage=candidate.evidence_stage.value if candidate.evidence_stage else None,
            source_credibility_tier=source_credibility_tier,
            authority=authority,
            directness=candidate.directness,
            independence=candidate.independence,
            time_=candidate.temporal_quality,
            specificity=candidate.specificity,
        )
        if candidate.evidence_type is EvidenceType.CONTRADICT:
            record_contradiction(session, evidence)
        created.append(evidence)
        if company is None and candidate.unknown_company_mention:
            unknown.append(
                UnknownCompanyMention(
                    raw_name=candidate.unknown_company_mention,
                    evidence_id=evidence.evidence_id,
                    rationale=candidate.rationale,
                )
            )
    return created, unknown
