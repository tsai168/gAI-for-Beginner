"""WBS-B8 unit tests: G08 non-functional compliance monitor (ADR-0020 §5)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from governance.compliance import (
    CostBudget,
    check_point_in_time,
    check_reproducible,
    check_traceable,
    cost_alert_triggered,
    is_material_score_change,
    within_budget,
)

_ROW_ID = uuid.uuid4()


def test_check_traceable_flags_empty_evidence() -> None:
    violation = check_traceable(table_name="event", row_id=_ROW_ID, evidence_ids=[])
    assert violation is not None
    assert violation.check == "traceability"


def test_check_traceable_passes_with_evidence() -> None:
    assert check_traceable(table_name="event", row_id=_ROW_ID, evidence_ids=[uuid.uuid4()]) is None


def test_check_reproducible_flags_missing_model_version() -> None:
    violation = check_reproducible(table_name="seco_score", row_id=_ROW_ID, model_version_id=None)
    assert violation is not None
    assert violation.check == "reproducibility"


def test_check_reproducible_passes_with_model_version() -> None:
    assert (
        check_reproducible(table_name="seco_score", row_id=_ROW_ID, model_version_id=uuid.uuid4())
        is None
    )


def test_check_point_in_time_flags_missing_available_at() -> None:
    violation = check_point_in_time(
        table_name="cmi_score", row_id=_ROW_ID, as_of=datetime.now(UTC), available_at=None
    )
    assert violation is not None
    assert violation.check == "point_in_time"


def test_check_point_in_time_flags_future_data() -> None:
    as_of = datetime.now(UTC)
    violation = check_point_in_time(
        table_name="cmi_score",
        row_id=_ROW_ID,
        as_of=as_of,
        available_at=as_of + timedelta(days=1),
    )
    assert violation is not None


def test_check_point_in_time_passes() -> None:
    as_of = datetime.now(UTC)
    assert (
        check_point_in_time(
            table_name="cmi_score",
            row_id=_ROW_ID,
            as_of=as_of,
            available_at=as_of - timedelta(days=1),
        )
        is None
    )


def test_is_material_score_change_first_score_never_material() -> None:
    assert is_material_score_change(None, 999.0) is False


def test_is_material_score_change_detects_large_swing() -> None:
    assert is_material_score_change(50.0, 65.0) is True  # +30%


def test_is_material_score_change_ignores_small_swing() -> None:
    assert is_material_score_change(50.0, 52.0) is False  # +4%


def test_is_material_score_change_from_zero() -> None:
    assert is_material_score_change(0.0, 1.0) is True
    assert is_material_score_change(0.0, 0.0) is False


def test_within_budget_unconfigured_never_blocks() -> None:
    assert within_budget(CostBudget(), tokens_used_today=10_000_000) is True


def test_within_budget_enforces_ceiling() -> None:
    budget = CostBudget(daily_ceiling=1000)
    assert within_budget(budget, tokens_used_today=999) is True
    assert within_budget(budget, tokens_used_today=1001) is False


def test_cost_alert_triggered_unconfigured_never_fires() -> None:
    assert cost_alert_triggered(CostBudget(), tokens_used_today=10_000_000) is False


def test_cost_alert_triggered_at_ratio() -> None:
    budget = CostBudget(daily_ceiling=1000, cost_alert_ratio=0.8)
    assert cost_alert_triggered(budget, tokens_used_today=799) is False
    assert cost_alert_triggered(budget, tokens_used_today=800) is True
