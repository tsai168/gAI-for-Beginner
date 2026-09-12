"""WBS-B5d unit tests: M08 robustness / time-quality check (ADR-0016 §4)."""

from __future__ import annotations

import pytest

from models.robustness import classify_time_quality, robustness_summary


@pytest.mark.parametrize(
    "confidence,expected",
    [
        (1.0, "HIGH"),
        (0.85, "HIGH"),
        (0.84, "MEDIUM"),
        (0.55, "MEDIUM"),
        (0.54, "LOW"),
        (0.0, "LOW"),
        (None, "LOW"),
    ],
)
def test_classify_time_quality_boundaries(confidence: float | None, expected: str) -> None:
    assert classify_time_quality(confidence) == expected


def test_robustness_summary_empty_buckets() -> None:
    result = robustness_summary({})
    assert result.buckets["HIGH"].n == 0
    assert result.buckets["HIGH"].mean is None
    assert result.sign_consistent is None


def test_robustness_summary_computes_mean_and_stdev() -> None:
    result = robustness_summary({"HIGH": [0.01, 0.02, 0.03]})
    assert result.buckets["HIGH"].n == 3
    assert result.buckets["HIGH"].mean == pytest.approx(0.02)
    assert result.buckets["HIGH"].stdev is not None


def test_sign_consistent_true_when_same_direction() -> None:
    result = robustness_summary({"HIGH": [0.02, 0.03], "MEDIUM": [0.01, 0.015]})
    assert result.sign_consistent is True


def test_sign_consistent_false_when_opposite_direction() -> None:
    result = robustness_summary({"HIGH": [0.02, 0.03], "MEDIUM": [-0.01, -0.02]})
    assert result.sign_consistent is False


def test_sign_consistent_none_when_a_bucket_is_empty() -> None:
    result = robustness_summary({"HIGH": [0.02, 0.03]})
    assert result.sign_consistent is None
