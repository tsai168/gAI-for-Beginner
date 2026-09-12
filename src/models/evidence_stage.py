"""M01 — Evidence Stage aggregation / monotonicity guard (WBS-B5a, ADR-0013 §2).

Charter §11.1 defines the E0–E6 ladder but not an algorithm for classifying
raw evidence text into a stage (that needs semantic judgment — L1/A01,
WBS-B6). M01's deterministic (L0) job is aggregation + guarding against
illegitimate regression, not text classification.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from knowledge.db.base import EvidenceStage, EvidenceType

_ORDER: tuple[EvidenceStage, ...] = (
    EvidenceStage.E0,
    EvidenceStage.E1,
    EvidenceStage.E2,
    EvidenceStage.E3,
    EvidenceStage.E4,
    EvidenceStage.E5,
    EvidenceStage.E6,
)
_RANK: dict[EvidenceStage, int] = {stage: i for i, stage in enumerate(_ORDER)}


@dataclass(slots=True, frozen=True)
class EvidenceStageTag:
    """A stage already assigned (upstream/manual/future A01) to one piece
    of evidence, plus how that evidence relates to the claim (SUPPORT vs
    CONTRADICT)."""

    stage: EvidenceStage
    evidence_type: EvidenceType


def aggregate_evidence_stage(tags: Sequence[EvidenceStageTag]) -> EvidenceStage | None:
    """Highest SUPPORTed stage that has no CONTRADICT at that exact same
    stage (a dispute of E6 says nothing about whether E2 was reached). No
    SUPPORT at all -> None (GP-02: absence of evidence is not evidence of
    absence; never default to E0)."""
    supported = {t.stage for t in tags if t.evidence_type is EvidenceType.SUPPORT}
    if not supported:
        return None
    contradicted = {t.stage for t in tags if t.evidence_type is EvidenceType.CONTRADICT}
    for stage in sorted(supported, key=lambda s: _RANK[s], reverse=True):
        if stage not in contradicted:
            return stage
    return None


def validate_stage_transition(
    old: EvidenceStage | None, new: EvidenceStage, *, allow_regression: bool = False
) -> None:
    """Charter §11.1: '有技術' != '進入供應鏈' != '量產' != '營收貢獻' — a stage
    may only move forward unless the caller explicitly marks this as a
    correction (mirrors K05's "only an explicit correction may regress")."""
    if old is None or allow_regression:
        return
    if _RANK[new] < _RANK[old]:
        raise ValueError(
            f"illegal evidence_stage regression {old.value} -> {new.value} "
            "without allow_regression=True"
        )
