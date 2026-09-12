"""M03 — Seco (Ecosystem Positioning Score) engine (WBS-B5b, ADR-0014 §2).

Charter §12 / CF-12..17: exact V1 weights (0.15/0.15/0.20/0.20/0.20/0.10),
scale 0-100, mandatory confidence (CF-15), Point-in-Time/Bitemporal
versioning (CF-16/17). Weights are Frozen — do not change them here; a
weight change needs a new Model Version (GP-10) and a Charter/Work
amendment, not an edit to this constant.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from knowledge.db.models import SecoScore

# Charter §12 (CF-13), frozen.
_WEIGHT_TECH_RELEVANCE = 0.15
_WEIGHT_PRODUCT_READINESS = 0.15
_WEIGHT_CUSTOMER_VALIDATION = 0.20
_WEIGHT_ECOSYSTEM_POSITION = 0.20
_WEIGHT_COMMERCIALIZATION = 0.20
_WEIGHT_STRATEGIC_DEFENSIBILITY = 0.10

_BANDS: tuple[tuple[float, str], ...] = (
    (20.0, "Minimal/Insufficient"),
    (40.0, "Emerging"),
    (60.0, "Developing"),
    (80.0, "Established"),
)
_TOP_BAND = "Strong"


@dataclass(slots=True, frozen=True)
class SecoDimensions:
    tech_relevance: float
    product_readiness: float
    customer_validation: float
    ecosystem_position: float
    commercialization: float
    strategic_defensibility: float


_SCALE_MIN = 0.0
_SCALE_MAX = 100.0


def _check_scale(name: str, value: float) -> None:
    if not _SCALE_MIN <= value <= _SCALE_MAX:
        raise ValueError(f"{name} must be within [0, 100], got {value}")


def compute_seco(dims: SecoDimensions) -> float:
    for name, value in (
        ("tech_relevance", dims.tech_relevance),
        ("product_readiness", dims.product_readiness),
        ("customer_validation", dims.customer_validation),
        ("ecosystem_position", dims.ecosystem_position),
        ("commercialization", dims.commercialization),
        ("strategic_defensibility", dims.strategic_defensibility),
    ):
        _check_scale(name, value)
    return (
        _WEIGHT_TECH_RELEVANCE * dims.tech_relevance
        + _WEIGHT_PRODUCT_READINESS * dims.product_readiness
        + _WEIGHT_CUSTOMER_VALIDATION * dims.customer_validation
        + _WEIGHT_ECOSYSTEM_POSITION * dims.ecosystem_position
        + _WEIGHT_COMMERCIALIZATION * dims.commercialization
        + _WEIGHT_STRATEGIC_DEFENSIBILITY * dims.strategic_defensibility
    )


def seco_band(score: float) -> str:
    _check_scale("score", score)
    for threshold, label in _BANDS:
        if score < threshold:
            return label
    return _TOP_BAND


def record_seco_score(
    session: Session,
    *,
    company_id: uuid.UUID,
    as_of: datetime,
    dims: SecoDimensions,
    confidence: float,
    model_version_id: uuid.UUID,
    valid_from: datetime,
) -> SecoScore:
    """CF-15: confidence is mandatory, no default."""
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence must be within [0, 1], got {confidence}")
    row = SecoScore(
        company_id=company_id,
        as_of=as_of,
        score=compute_seco(dims),
        tech_relevance=dims.tech_relevance,
        product_readiness=dims.product_readiness,
        customer_validation=dims.customer_validation,
        ecosystem_position=dims.ecosystem_position,
        commercialization=dims.commercialization,
        strategic_defensibility=dims.strategic_defensibility,
        confidence=confidence,
        model_version_id=model_version_id,
        valid_from=valid_from,
    )
    session.add(row)
    session.flush()
    return row


def correct_seco_score(
    session: Session,
    old: SecoScore,
    *,
    dims: SecoDimensions,
    confidence: float,
    model_version_id: uuid.UUID,
    valid_from: datetime,
) -> SecoScore:
    """GP-10/CF-17: never overwrite — close the old row (valid_to only) and
    open a brand new one for the same company/as_of."""
    old.valid_to = valid_from
    session.flush()
    return record_seco_score(
        session,
        company_id=old.company_id,
        as_of=old.as_of,
        dims=dims,
        confidence=confidence,
        model_version_id=model_version_id,
        valid_from=valid_from,
    )
