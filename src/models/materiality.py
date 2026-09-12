"""M05 — Materiality scorer (WBS-B5c, ADR-0015 §2, CF-27/28, GP-12).

Charter §15 names five factors but gives no weight formula (like M02
Confidence) — V1 "Expert Rule". Weights here are a documented default, not
a Frozen Decision. `score_event_materiality` computes/raises; G01 judges
(ADR-0004 decision 1) — the B1 stub leaves it PENDING.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from governance.cfl import CflId, CflService, default_cfl_service
from knowledge.db.base import CflStatus
from knowledge.db.models import Event

_WEIGHT_CPO_RELEVANCE = 0.25
_WEIGHT_EVIDENCE_STRENGTH = 0.25
_WEIGHT_COMMERCIAL_IMPACT = 0.20
_WEIGHT_ECOSYSTEM_IMPACT = 0.20
_WEIGHT_NOVELTY = 0.10

_SCALE_MIN = 0.0
_SCALE_MAX = 100.0


@dataclass(slots=True, frozen=True)
class MaterialityFactors:
    cpo_relevance: float
    evidence_strength: float
    commercial_impact: float
    ecosystem_impact: float
    novelty: float


def _check_scale(name: str, value: float) -> None:
    if not _SCALE_MIN <= value <= _SCALE_MAX:
        raise ValueError(f"{name} must be within [0, 100], got {value}")


def compute_materiality(factors: MaterialityFactors) -> float:
    for name, value in (
        ("cpo_relevance", factors.cpo_relevance),
        ("evidence_strength", factors.evidence_strength),
        ("commercial_impact", factors.commercial_impact),
        ("ecosystem_impact", factors.ecosystem_impact),
        ("novelty", factors.novelty),
    ):
        _check_scale(name, value)
    return (
        _WEIGHT_CPO_RELEVANCE * factors.cpo_relevance
        + _WEIGHT_EVIDENCE_STRENGTH * factors.evidence_strength
        + _WEIGHT_COMMERCIAL_IMPACT * factors.commercial_impact
        + _WEIGHT_ECOSYSTEM_IMPACT * factors.ecosystem_impact
        + _WEIGHT_NOVELTY * factors.novelty
    )


def score_event_materiality(
    session: Session,
    event: Event,
    factors: MaterialityFactors,
    *,
    cfl_service: CflService = default_cfl_service,
) -> CflStatus:
    """GP-12: this only sets a score — it does not, by itself, make the
    event a "Material Event" (CF-28: that requires CFL-04 approval)."""
    event.materiality_score = compute_materiality(factors)
    session.flush()
    return cfl_service.submit_candidate(
        session, table="event", row_id=event.event_id, cfl_id=CflId.CFL_04
    )
