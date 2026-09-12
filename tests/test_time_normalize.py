"""WBS-B3b unit tests: P04 Observed-Time normalization (ADR-0010 §2)."""

from __future__ import annotations

from datetime import UTC, datetime

from ingestion.time_normalize import RawTimeInput, normalize_observed_time

RETRIEVED = datetime(2026, 9, 12, 8, 0, tzinfo=UTC)


def test_occurred_at_wins_when_present() -> None:
    occ = RawTimeInput(datetime(2026, 9, 5, 13, 0, tzinfo=UTC))
    pub = RawTimeInput(datetime(2026, 9, 6, 9, 0, tzinfo=UTC))
    ot = normalize_observed_time(retrieved_at=RETRIEVED, occurred_at=occ, published_at=pub)
    assert ot.time_basis == "OCCURRED"
    assert ot.time_precision == "DATETIME"
    assert ot.time_confidence == 1.0
    assert ot.occurred_at == occ.value
    assert ot.published_at == pub.value


def test_occurred_at_date_only_lowers_confidence() -> None:
    occ = RawTimeInput(datetime(2026, 9, 5, 0, 0, tzinfo=UTC), has_time_of_day=False)
    ot = normalize_observed_time(retrieved_at=RETRIEVED, occurred_at=occ)
    assert ot.time_basis == "OCCURRED"
    assert ot.time_precision == "DATE_ONLY"
    assert ot.time_confidence == 0.85


def test_falls_back_to_published_when_no_occurred() -> None:
    pub = RawTimeInput(datetime(2026, 9, 6, 9, 0, tzinfo=UTC))
    ot = normalize_observed_time(retrieved_at=RETRIEVED, published_at=pub)
    assert ot.time_basis == "PUBLISHED"
    assert ot.time_confidence == 0.70


def test_falls_back_to_retrieved_when_nothing_else() -> None:
    ot = normalize_observed_time(retrieved_at=RETRIEVED)
    assert ot.time_basis == "RETRIEVED"
    assert ot.time_precision == "DATETIME"
    assert ot.time_confidence == 0.20
    assert ot.occurred_at is None
    assert ot.published_at is None


def test_missing_fields_stay_none_not_guessed() -> None:
    ot = normalize_observed_time(retrieved_at=RETRIEVED)
    assert ot.occurred_at is None
    assert ot.published_at is None
    assert ot.market_known_at is None


def test_market_known_at_is_carried_but_not_a_basis() -> None:
    mka = RawTimeInput(datetime(2026, 9, 5, 10, 0, tzinfo=UTC))
    ot = normalize_observed_time(retrieved_at=RETRIEVED, market_known_at=mka)
    assert ot.market_known_at == mka.value
    assert ot.time_basis == "RETRIEVED"  # market_known_at never becomes the basis


def test_retrieved_at_is_always_required_and_passed_through() -> None:
    ot = normalize_observed_time(retrieved_at=RETRIEVED)
    assert ot.retrieved_at == RETRIEVED
