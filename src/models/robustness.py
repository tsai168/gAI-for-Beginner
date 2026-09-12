"""M08 — Robustness / time-quality check (WBS-B5d, ADR-0016 §4, Charter §14.4).

Charter says CAR results *may* be split into High/Medium/Low Time-Quality
samples for a robustness check, but gives no thresholds or statistical
test. Buckets below align with P04's own time_confidence table (ADR-0010
§2); the summary is descriptive-statistics-only for V1 — a formal test
(t-test/bootstrap) is a documented Phase 2 candidate, not implemented here.
"""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

TimeQuality = Literal["HIGH", "MEDIUM", "LOW"]

_HIGH_THRESHOLD = 0.85
_MEDIUM_THRESHOLD = 0.55


def classify_time_quality(time_confidence: float | None) -> TimeQuality:
    """Aligned with P04's confidence table (ADR-0010 §2): OCCURRED-based
    (>=0.85) -> HIGH, PUBLISHED-based (>=0.55) -> MEDIUM, RETRIEVED
    fallback (or missing) -> LOW."""
    if time_confidence is not None and time_confidence >= _HIGH_THRESHOLD:
        return "HIGH"
    if time_confidence is not None and time_confidence >= _MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


@dataclass(slots=True, frozen=True)
class BucketStats:
    n: int
    mean: float | None
    stdev: float | None


@dataclass(slots=True, frozen=True)
class RobustnessResult:
    buckets: Mapping[TimeQuality, BucketStats]
    sign_consistent: bool | None  # None if not enough buckets to compare


def _bucket_stats(values: Sequence[float]) -> BucketStats:
    if not values:
        return BucketStats(n=0, mean=None, stdev=None)
    mean = statistics.fmean(values)
    stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
    return BucketStats(n=len(values), mean=mean, stdev=stdev)


_QUALITIES: tuple[TimeQuality, ...] = ("HIGH", "MEDIUM", "LOW")


def robustness_summary(car_by_quality: Mapping[TimeQuality, Sequence[float]]) -> RobustnessResult:
    buckets = {quality: _bucket_stats(car_by_quality.get(quality, ())) for quality in _QUALITIES}
    high_mean = buckets["HIGH"].mean
    medium_mean = buckets["MEDIUM"].mean
    sign_consistent: bool | None = None
    if high_mean is not None and medium_mean is not None:
        sign_consistent = (high_mean >= 0) == (medium_mean >= 0)
    return RobustnessResult(buckets=buckets, sign_consistent=sign_consistent)
