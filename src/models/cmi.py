"""M04 — CMI (Chip / Capital Market Momentum Indicator) engine (WBS-B5b,
ADR-0014 §3). Charter §13 / CF-18/19: V1 equal-weight (20% each). GP-08/09:
No Future Data — a dimension whose source data was not yet available as of
the computation time must never enter the score (no backward filling).
This is the WBS-B5 acceptance gate.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from knowledge.db.models import CmiScore

_WEIGHT = 0.20  # equal weight, five dimensions (Charter §13, CF-19)

_DIM_NAMES = (
    "foreign_inst_momentum",
    "domestic_inst_momentum",
    "margin_short",
    "ownership_concentration",
    "trading_structure",
)


class FutureDataError(ValueError):
    """GP-08 (No Future Data in CMI) / GP-09 (Effective Period != Availability
    Time): a dimension's source data was not yet available as of the
    computation time."""


@dataclass(slots=True, frozen=True)
class CmiDimensions:
    foreign_inst_momentum: float
    domestic_inst_momentum: float
    margin_short: float
    ownership_concentration: float
    trading_structure: float


@dataclass(slots=True, frozen=True)
class CmiAvailability:
    """`available_at` per dimension — the same concept as
    market_data/institutional_trading/shareholding.available_at (ADR-0003)."""

    foreign_inst_momentum: datetime | None
    domestic_inst_momentum: datetime | None
    margin_short: datetime | None
    ownership_concentration: datetime | None
    trading_structure: datetime | None


_SCALE_MIN = 0.0
_SCALE_MAX = 100.0


def _check_scale(name: str, value: float) -> None:
    if not _SCALE_MIN <= value <= _SCALE_MAX:
        raise ValueError(f"{name} must be within [0, 100], got {value}")


def compute_cmi(dims: CmiDimensions) -> float:
    values = (
        dims.foreign_inst_momentum,
        dims.domestic_inst_momentum,
        dims.margin_short,
        dims.ownership_concentration,
        dims.trading_structure,
    )
    for name, value in zip(_DIM_NAMES, values, strict=True):
        _check_scale(name, value)
    return _WEIGHT * sum(values)


def assert_no_future_data(as_of: datetime, availability: CmiAvailability) -> None:
    """GP-08/GP-09. Raises on the first offending dimension; missing
    availability is treated the same as future availability — both mean
    "we cannot prove this was knowable at as_of"."""
    values = (
        availability.foreign_inst_momentum,
        availability.domestic_inst_momentum,
        availability.margin_short,
        availability.ownership_concentration,
        availability.trading_structure,
    )
    for name, available_at in zip(_DIM_NAMES, values, strict=True):
        if available_at is None:
            raise FutureDataError(
                f"{name} has no known availability time — cannot prove it was "
                f"knowable at as_of={as_of} (GP-08/GP-09)"
            )
        if available_at > as_of:
            raise FutureDataError(
                f"{name} available_at={available_at} is after as_of={as_of} (GP-08 No Future Data)"
            )


def compute_cmi_guarded(
    *, as_of: datetime, dims: CmiDimensions, availability: CmiAvailability
) -> float:
    """The only recommended entry point: checks GP-08/09 before scoring."""
    assert_no_future_data(as_of, availability)
    return compute_cmi(dims)


def record_cmi_score(
    session: Session,
    *,
    company_id: uuid.UUID,
    as_of: datetime,
    dims: CmiDimensions,
    availability: CmiAvailability,
    model_version_id: uuid.UUID,
    valid_from: datetime,
) -> CmiScore:
    score = compute_cmi_guarded(as_of=as_of, dims=dims, availability=availability)
    row = CmiScore(
        company_id=company_id,
        as_of=as_of,
        score=score,
        foreign_inst_momentum=dims.foreign_inst_momentum,
        domestic_inst_momentum=dims.domestic_inst_momentum,
        margin_short=dims.margin_short,
        ownership_concentration=dims.ownership_concentration,
        trading_structure=dims.trading_structure,
        model_version_id=model_version_id,
        valid_from=valid_from,
    )
    session.add(row)
    session.flush()
    return row


def correct_cmi_score(
    session: Session,
    old: CmiScore,
    *,
    dims: CmiDimensions,
    availability: CmiAvailability,
    model_version_id: uuid.UUID,
    valid_from: datetime,
) -> CmiScore:
    """GP-10: never overwrite — close the old row (valid_to only), open a
    new one."""
    old.valid_to = valid_from
    session.flush()
    return record_cmi_score(
        session,
        company_id=old.company_id,
        as_of=old.as_of,
        dims=dims,
        availability=availability,
        model_version_id=model_version_id,
        valid_from=valid_from,
    )
