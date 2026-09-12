"""G08 — Non-functional compliance monitor (WBS-B8, ADR-0020, Charter §22;
Work-1 §3.8).

These are *monitors* (collect violations for reporting/auditing across
already-computed rows) rather than *guards* (block a computation inline) —
the guards already live where the computation happens: M04's
`assert_no_future_data`/`compute_cmi_guarded` for PIT, the `cpoai_cfl_guard`
DB trigger for CFL. `check_point_in_time` here mirrors M04's rule as a
post-hoc, non-raising check so it can scan many already-written rows.

Token Budget / Daily Ceiling / Cost Alert stay Deferred (Work-2 §9,
Charter §29): `CostBudget` fields default to `None` (unconfigured = no
limit enforced) — never hardcode a number here; Ops sets real values once
that Deferred decision is made.

Seco/CMI large swings route to a Material Review flag, not a new CFL
(Work-3 ADR-0005 §後續: "Seco/CMI 大幅變動走 G08 Material Review 旗標（非新
CFL）") — `is_material_score_change` feeds
`governance.publication.PublicationTier.MATERIAL_REVIEW`.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ComplianceViolation:
    check: str
    table_name: str
    row_id: uuid.UUID
    detail: str


def check_traceable(
    *, table_name: str, row_id: uuid.UUID, evidence_ids: Sequence[uuid.UUID]
) -> ComplianceViolation | None:
    """Charter §22 Traceability: every major Claim must trace to Source /
    Evidence / Citation."""
    if not evidence_ids:
        return ComplianceViolation(
            check="traceability",
            table_name=table_name,
            row_id=row_id,
            detail="no evidence_ids on record",
        )
    return None


def check_reproducible(
    *, table_name: str, row_id: uuid.UUID, model_version_id: uuid.UUID | None
) -> ComplianceViolation | None:
    """Charter §22 Reproducibility: a result must carry its Model Version
    (GP-10) — Input Version and Calculation Time already ride along via
    valid_from/created_at on every model-output row."""
    if model_version_id is None:
        return ComplianceViolation(
            check="reproducibility",
            table_name=table_name,
            row_id=row_id,
            detail="missing model_version_id",
        )
    return None


def check_point_in_time(
    *, table_name: str, row_id: uuid.UUID, as_of: datetime, available_at: datetime | None
) -> ComplianceViolation | None:
    """Charter §22 PIT Integrity monitor — the same no-future-data rule M04
    already *guards* (GP-08/CF-26), offered here as a post-hoc check for
    auditing rows computed elsewhere."""
    if available_at is None or available_at > as_of:
        return ComplianceViolation(
            check="point_in_time",
            table_name=table_name,
            row_id=row_id,
            detail=f"available_at={available_at} not <= as_of={as_of}",
        )
    return None


_MATERIAL_CHANGE_RATIO = 0.20  # adjustable, not Frozen — see module docstring


def is_material_score_change(
    old_score: float | None, new_score: float, *, threshold_ratio: float = _MATERIAL_CHANGE_RATIO
) -> bool:
    """`old_score is None` (first score ever) is never material on its own
    — nothing to compare against."""
    if old_score is None:
        return False
    if old_score == 0:
        return new_score != 0
    return abs(new_score - old_score) / abs(old_score) >= threshold_ratio


@dataclass(slots=True, frozen=True)
class CostBudget:
    """Work-2 §9 Deferred Item. All `None` = unconfigured = no limit
    enforced."""

    token_budget: int | None = None
    daily_ceiling: int | None = None
    cost_alert_ratio: float | None = None


def within_budget(budget: CostBudget, *, tokens_used_today: int) -> bool:
    if budget.daily_ceiling is None:
        return True
    return tokens_used_today <= budget.daily_ceiling


def cost_alert_triggered(budget: CostBudget, *, tokens_used_today: int) -> bool:
    if budget.daily_ceiling is None or budget.cost_alert_ratio is None:
        return False
    return tokens_used_today >= budget.daily_ceiling * budget.cost_alert_ratio
