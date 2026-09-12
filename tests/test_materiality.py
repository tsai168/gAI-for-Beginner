"""WBS-B5c unit tests: M05 materiality scoring (ADR-0015 §2)."""

from __future__ import annotations

import pytest

from models.materiality import MaterialityFactors, compute_materiality


def test_all_100_gives_100() -> None:
    f = MaterialityFactors(100, 100, 100, 100, 100)
    assert compute_materiality(f) == pytest.approx(100.0)


def test_all_0_gives_0() -> None:
    f = MaterialityFactors(0, 0, 0, 0, 0)
    assert compute_materiality(f) == 0.0


def test_weights_applied_exactly() -> None:
    # Only cpo_relevance (25%) at 100
    assert compute_materiality(MaterialityFactors(100, 0, 0, 0, 0)) == pytest.approx(25.0)
    # Only novelty (10%) at 100
    assert compute_materiality(MaterialityFactors(0, 0, 0, 0, 100)) == pytest.approx(10.0)


@pytest.mark.parametrize("bad", [-1, 100.1])
def test_out_of_scale_raises(bad: float) -> None:
    with pytest.raises(ValueError, match="within \\[0, 100\\]"):
        compute_materiality(MaterialityFactors(bad, 50, 50, 50, 50))
