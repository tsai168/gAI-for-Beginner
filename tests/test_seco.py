"""WBS-B5b unit tests: M03 Seco engine (ADR-0014 §2, Charter §12)."""

from __future__ import annotations

import pytest

from models.seco import SecoDimensions, compute_seco, seco_band

FULL = SecoDimensions(100, 100, 100, 100, 100, 100)
ZERO = SecoDimensions(0, 0, 0, 0, 0, 0)


def test_all_100_gives_100() -> None:
    assert compute_seco(FULL) == pytest.approx(100.0)


def test_all_0_gives_0() -> None:
    assert compute_seco(ZERO) == 0.0


def test_charter_weights_applied_exactly() -> None:
    # Only tech_relevance (15%) at 100, rest 0 -> score == 15
    dims = SecoDimensions(100, 0, 0, 0, 0, 0)
    assert compute_seco(dims) == pytest.approx(15.0)
    # Only customer_validation (20%) at 100
    dims = SecoDimensions(0, 0, 100, 0, 0, 0)
    assert compute_seco(dims) == pytest.approx(20.0)
    # Only strategic_defensibility (10%) at 100
    dims = SecoDimensions(0, 0, 0, 0, 0, 100)
    assert compute_seco(dims) == pytest.approx(10.0)


@pytest.mark.parametrize("bad", [-1, 100.1, 200])
def test_out_of_scale_dimension_raises(bad: float) -> None:
    with pytest.raises(ValueError, match="within \\[0, 100\\]"):
        compute_seco(SecoDimensions(bad, 50, 50, 50, 50, 50))


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "Minimal/Insufficient"),
        (19.9, "Minimal/Insufficient"),
        (20, "Emerging"),
        (39.9, "Emerging"),
        (40, "Developing"),
        (59.9, "Developing"),
        (60, "Established"),
        (79.9, "Established"),
        (80, "Strong"),
        (100, "Strong"),
    ],
)
def test_seco_band_boundaries(score: float, expected: str) -> None:
    assert seco_band(score) == expected


def test_seco_band_rejects_out_of_scale() -> None:
    with pytest.raises(ValueError, match="within \\[0, 100\\]"):
        seco_band(101)
