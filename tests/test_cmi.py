"""WBS-B5b unit tests: M04 CMI engine + GP-08 No-Future-Data guard
(ADR-0014 §3, Charter §13)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from models.cmi import (
    CmiAvailability,
    CmiDimensions,
    FutureDataError,
    assert_no_future_data,
    compute_cmi,
    compute_cmi_guarded,
)

AS_OF = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)
BEFORE = AS_OF - timedelta(days=1)
AFTER = AS_OF + timedelta(days=1)

FULL_DIMS = CmiDimensions(100, 100, 100, 100, 100)
ALL_AVAILABLE = CmiAvailability(BEFORE, BEFORE, BEFORE, BEFORE, BEFORE)


def test_equal_weight_all_100_gives_100() -> None:
    assert compute_cmi(FULL_DIMS) == pytest.approx(100.0)


def test_equal_weight_single_dimension() -> None:
    dims = CmiDimensions(100, 0, 0, 0, 0)
    assert compute_cmi(dims) == pytest.approx(20.0)


@pytest.mark.parametrize("bad", [-1, 100.1])
def test_out_of_scale_raises(bad: float) -> None:
    with pytest.raises(ValueError, match="within \\[0, 100\\]"):
        compute_cmi(CmiDimensions(bad, 50, 50, 50, 50))


def test_no_future_data_passes_when_all_available_before_as_of() -> None:
    assert_no_future_data(AS_OF, ALL_AVAILABLE)  # no raise


def test_available_exactly_at_as_of_is_allowed() -> None:
    avail = CmiAvailability(AS_OF, AS_OF, AS_OF, AS_OF, AS_OF)
    assert_no_future_data(AS_OF, avail)  # boundary inclusive


def test_future_availability_blocks_computation() -> None:
    avail = CmiAvailability(BEFORE, BEFORE, BEFORE, BEFORE, AFTER)
    with pytest.raises(FutureDataError, match="trading_structure"):
        assert_no_future_data(AS_OF, avail)


def test_missing_availability_blocks_computation() -> None:
    avail = CmiAvailability(BEFORE, None, BEFORE, BEFORE, BEFORE)
    with pytest.raises(FutureDataError, match="domestic_inst_momentum"):
        assert_no_future_data(AS_OF, avail)


def test_compute_cmi_guarded_blocks_future_data_before_scoring() -> None:
    avail = CmiAvailability(BEFORE, BEFORE, BEFORE, BEFORE, AFTER)
    with pytest.raises(FutureDataError):
        compute_cmi_guarded(as_of=AS_OF, dims=FULL_DIMS, availability=avail)


def test_compute_cmi_guarded_returns_score_when_clean() -> None:
    v = compute_cmi_guarded(as_of=AS_OF, dims=FULL_DIMS, availability=ALL_AVAILABLE)
    assert v == pytest.approx(100.0)
