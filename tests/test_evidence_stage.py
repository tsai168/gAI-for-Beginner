"""WBS-B5a unit tests: M01 evidence-stage aggregation (ADR-0013 §2)."""

from __future__ import annotations

import pytest

from knowledge.db.base import EvidenceStage, EvidenceType
from models.evidence_stage import (
    EvidenceStageTag,
    aggregate_evidence_stage,
    validate_stage_transition,
)

SUP = EvidenceType.SUPPORT
CON = EvidenceType.CONTRADICT
NEU = EvidenceType.NEUTRAL_CONTEXT


def test_no_support_returns_none() -> None:
    assert aggregate_evidence_stage([]) is None
    assert aggregate_evidence_stage([EvidenceStageTag(EvidenceStage.E3, CON)]) is None


def test_highest_supported_stage_wins() -> None:
    tags = [
        EvidenceStageTag(EvidenceStage.E1, SUP),
        EvidenceStageTag(EvidenceStage.E3, SUP),
        EvidenceStageTag(EvidenceStage.E2, NEU),
    ]
    assert aggregate_evidence_stage(tags) == EvidenceStage.E3


def test_contradiction_at_top_stage_blocks_it() -> None:
    tags = [
        EvidenceStageTag(EvidenceStage.E2, SUP),
        EvidenceStageTag(EvidenceStage.E5, SUP),
        EvidenceStageTag(EvidenceStage.E5, CON),
    ]
    assert aggregate_evidence_stage(tags) == EvidenceStage.E2


def test_contradiction_above_supported_stage_does_not_block() -> None:
    tags = [
        EvidenceStageTag(EvidenceStage.E2, SUP),
        EvidenceStageTag(EvidenceStage.E6, CON),
    ]
    assert aggregate_evidence_stage(tags) == EvidenceStage.E2


def test_all_stages_contradicted_returns_none() -> None:
    tags = [
        EvidenceStageTag(EvidenceStage.E1, SUP),
        EvidenceStageTag(EvidenceStage.E1, CON),
    ]
    assert aggregate_evidence_stage(tags) is None


def test_forward_transition_allowed() -> None:
    validate_stage_transition(EvidenceStage.E1, EvidenceStage.E3)


def test_regression_without_flag_raises() -> None:
    with pytest.raises(ValueError, match="illegal evidence_stage regression"):
        validate_stage_transition(EvidenceStage.E4, EvidenceStage.E2)


def test_regression_with_flag_allowed() -> None:
    validate_stage_transition(EvidenceStage.E4, EvidenceStage.E2, allow_regression=True)


def test_first_assignment_has_no_old_stage() -> None:
    validate_stage_transition(None, EvidenceStage.E0)
