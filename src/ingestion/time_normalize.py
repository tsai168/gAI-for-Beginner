"""P04 — Observed-Time normalization (WBS-B3b, ADR-0010 §2).

Deterministic (L0). Parses/prioritizes the Observed-Time hierarchy (Charter
§14.4 / CF-21 / CF-21A). Never fabricates a value: a missing or unparsed
field stays None (GP-07 — Unknown Time Must Remain Unknown).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime


class TimeBasis(enum.StrEnum):
    """Which input the derived time is drawn from. Implementation
    convention (ADR-0010 §2) — `ObservedTimeMixin.time_basis` is free text,
    not a Charter-enumerated value."""

    OCCURRED = "OCCURRED"
    PUBLISHED = "PUBLISHED"
    RETRIEVED = "RETRIEVED"


class TimePrecision(enum.StrEnum):
    DATETIME = "DATETIME"
    DATE_ONLY = "DATE_ONLY"


@dataclass(slots=True, frozen=True)
class RawTimeInput:
    """What the parser/adapter actually knows about one time field.
    `has_time_of_day=False` means only a date was given — P04 must not
    invent a 00:00 time for it (Charter §14.4)."""

    value: datetime | None
    has_time_of_day: bool = True


@dataclass(slots=True, frozen=True)
class ObservedTime:
    occurred_at: datetime | None
    published_at: datetime | None
    retrieved_at: datetime
    market_known_at: datetime | None
    time_basis: str | None
    time_precision: str | None
    time_confidence: float | None


_CONFIDENCE: dict[tuple[TimeBasis, TimePrecision], float] = {
    (TimeBasis.OCCURRED, TimePrecision.DATETIME): 1.00,
    (TimeBasis.OCCURRED, TimePrecision.DATE_ONLY): 0.85,
    (TimeBasis.PUBLISHED, TimePrecision.DATETIME): 0.70,
    (TimeBasis.PUBLISHED, TimePrecision.DATE_ONLY): 0.55,
    (TimeBasis.RETRIEVED, TimePrecision.DATETIME): 0.20,
}


def _present(raw: RawTimeInput | None) -> bool:
    return raw is not None and raw.value is not None


def normalize_observed_time(
    *,
    retrieved_at: datetime,
    occurred_at: RawTimeInput | None = None,
    published_at: RawTimeInput | None = None,
    market_known_at: RawTimeInput | None = None,
) -> ObservedTime:
    """ADR-0010 §2: basis priority occurred > published > retrieved (fallback);
    market_known_at is carried through but never used as the basis."""
    if _present(occurred_at):
        assert occurred_at is not None  # narrows for mypy; guarded by _present
        basis = TimeBasis.OCCURRED
        precision = (
            TimePrecision.DATETIME if occurred_at.has_time_of_day else TimePrecision.DATE_ONLY
        )
    elif _present(published_at):
        assert published_at is not None
        basis = TimeBasis.PUBLISHED
        precision = (
            TimePrecision.DATETIME if published_at.has_time_of_day else TimePrecision.DATE_ONLY
        )
    else:
        basis = TimeBasis.RETRIEVED
        precision = TimePrecision.DATETIME

    confidence = _CONFIDENCE.get((basis, precision))

    return ObservedTime(
        occurred_at=occurred_at.value if occurred_at is not None else None,
        published_at=published_at.value if published_at is not None else None,
        retrieved_at=retrieved_at,
        market_known_at=market_known_at.value if market_known_at is not None else None,
        time_basis=basis.value,
        time_precision=precision.value,
        time_confidence=confidence,
    )
