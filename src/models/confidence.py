"""M02 — Confidence engine (WBS-B5a, ADR-0013 §3, CF-29/30, GP-11).

Charter §16 names CF1–CF5 but gives no weight formula (unlike Seco/CMI,
which are Charter-frozen). The weights below are an implementation default
("V1 Rule-based / Expert Prior"), not a Frozen Decision — see ADR-0013 §3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge.db.models import Evidence

# CF1..CF4 weights (sum to 1.0); CF5 Conflict Penalty is a subtracted term,
# supplied by the caller (not computed here — see ADR-0013 §3 "not done").
_WEIGHT_AUTHORITY = 0.30  # CF1 Source Authority
_WEIGHT_DIRECTNESS = 0.25  # CF2 Evidence Directness
_WEIGHT_INDEPENDENCE = 0.25  # CF3 Independent Corroboration
_WEIGHT_TEMPORAL = 0.20  # CF4 Temporal Quality


def _check_unit_range(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be within [0, 1], got {value}")


def compute_confidence(
    *,
    authority: float,
    directness: float,
    independence: float,
    temporal_quality: float,
    conflict_penalty: float = 0.0,
) -> float:
    for name, value in (
        ("authority", authority),
        ("directness", directness),
        ("independence", independence),
        ("temporal_quality", temporal_quality),
    ):
        _check_unit_range(name, value)
    if conflict_penalty < 0.0:
        raise ValueError(f"conflict_penalty must be >= 0, got {conflict_penalty}")

    base = (
        _WEIGHT_AUTHORITY * authority
        + _WEIGHT_DIRECTNESS * directness
        + _WEIGHT_INDEPENDENCE * independence
        + _WEIGHT_TEMPORAL * temporal_quality
    )
    return max(0.0, min(1.0, base - conflict_penalty))


def score_evidence_confidence(evidence: Evidence, *, conflict_penalty: float = 0.0) -> float | None:
    """Reads the CF-10 fields already on `evidence` (Work-2 §2.7). Returns
    None — never a guessed default — if any required dimension is missing
    (GP-11: LLM Confidence != Research Confidence)."""
    authority = evidence.authority
    directness = evidence.directness
    independence = evidence.independence
    temporal_quality = evidence.time_
    if authority is None or directness is None or independence is None or temporal_quality is None:
        return None
    return compute_confidence(
        authority=float(authority),
        directness=float(directness),
        independence=float(independence),
        temporal_quality=float(temporal_quality),
        conflict_penalty=conflict_penalty,
    )
