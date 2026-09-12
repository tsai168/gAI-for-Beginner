"""WBS-B5a unit tests: M02 confidence engine (ADR-0013 §3)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from models.confidence import compute_confidence, score_evidence_confidence


def test_all_ones_gives_confidence_one() -> None:
    assert compute_confidence(authority=1, directness=1, independence=1, temporal_quality=1) == 1.0


def test_all_zeros_gives_confidence_zero() -> None:
    assert compute_confidence(authority=0, directness=0, independence=0, temporal_quality=0) == 0.0


def test_weights_sum_to_one_at_uniform_input() -> None:
    v = compute_confidence(authority=0.5, directness=0.5, independence=0.5, temporal_quality=0.5)
    assert v == pytest.approx(0.5)


def test_conflict_penalty_reduces_and_floors_at_zero() -> None:
    v = compute_confidence(
        authority=0.5, directness=0.5, independence=0.5, temporal_quality=0.5, conflict_penalty=10
    )
    assert v == 0.0


@pytest.mark.parametrize("field", ["authority", "directness", "independence", "temporal_quality"])
def test_out_of_range_dimension_raises(field: str) -> None:
    kwargs = {"authority": 0.5, "directness": 0.5, "independence": 0.5, "temporal_quality": 0.5}
    kwargs[field] = 1.5
    with pytest.raises(ValueError, match="within \\[0, 1\\]"):
        compute_confidence(**kwargs)


def test_negative_conflict_penalty_raises() -> None:
    with pytest.raises(ValueError, match="conflict_penalty"):
        compute_confidence(
            authority=0.5,
            directness=0.5,
            independence=0.5,
            temporal_quality=0.5,
            conflict_penalty=-0.1,
        )


@dataclass
class _FakeEvidence:
    authority: float | None
    directness: float | None
    independence: float | None
    time_: float | None


def test_score_evidence_confidence_reads_cf10_fields() -> None:
    ev = _FakeEvidence(authority=1.0, directness=1.0, independence=1.0, time_=1.0)
    assert score_evidence_confidence(ev) == 1.0  # type: ignore[arg-type]


@pytest.mark.parametrize("missing", ["authority", "directness", "independence", "time_"])
def test_score_evidence_confidence_none_when_dimension_missing(missing: str) -> None:
    values = {"authority": 0.8, "directness": 0.8, "independence": 0.8, "time_": 0.8}
    values[missing] = None
    ev = _FakeEvidence(**values)
    assert score_evidence_confidence(ev) is None  # type: ignore[arg-type]
