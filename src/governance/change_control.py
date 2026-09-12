"""G07 — Change Control record shape (WBS-B8, ADR-0020, Charter §31).

Charter §31 names the frozen contract areas and what a Change Request must
state (reason, impact, backward compatibility, recompute need, acceptance
method), plus the V1.x/V2.0 version-bump rule. This project's ADRs
(`docs/decisions/`) already play the CR record role in practice — ADR-0003
says so explicitly ("本 ADR 兼任 CR 記錄"). This module gives that practice a
typed, validated shape rather than inventing a parallel database: no CR
table exists in Work-2's DATA_MODEL, and a `ChangeRequest` here is not
itself a database row.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime


class FrozenContractArea(enum.StrEnum):
    """Charter §31, verbatim list of areas whose change requires a CR."""

    UNIVERSE = "Universe"
    TAXONOMY = "Taxonomy"
    EVIDENCE_STAGE = "Evidence Stage"
    SOURCE_TIER = "Source Tier"
    RELATIONSHIP_CONFIRMATION = "Relationship Confirmation"
    SECO = "Seco"
    CMI = "CMI"
    EVENT_TIMING = "Event Timing"
    EVENT_WINDOW = "Event Window"
    CONFIDENCE = "Confidence"
    CFL = "CFL"
    PUBLICATION_POLICY = "Publication Policy"
    AGENT_AUTONOMY = "Agent Autonomy"


class VersionBump(enum.StrEnum):
    MINOR = "V1.x"  # 小幅且不改變研究契約的調整
    MAJOR = "V2.0"  # 改變核心研究邏輯、模型定義或治理邊界


@dataclass(slots=True, frozen=True)
class ChangeRequest:
    cr_id: str
    area: FrozenContractArea
    reason: str
    impact: str
    backward_compatibility: str
    recompute_required: str
    acceptance_method: str
    version_bump: VersionBump
    approved_by: str | None = None
    approved_at: datetime | None = None


class IncompleteChangeRequestError(ValueError):
    """Charter §31: a CR must state reason, impact, backward compatibility,
    recompute need and acceptance method — every one, not just some."""


_REQUIRED_TEXT_FIELDS = (
    "reason",
    "impact",
    "backward_compatibility",
    "recompute_required",
    "acceptance_method",
)


def validate_change_request(cr: ChangeRequest) -> None:
    missing = [field for field in _REQUIRED_TEXT_FIELDS if not getattr(cr, field).strip()]
    if missing:
        raise IncompleteChangeRequestError(
            f"Change Request {cr.cr_id} missing: {', '.join(missing)}"
        )


def classify_version_bump(*, changes_core_logic: bool) -> VersionBump:
    """Charter §31 ¶2: minor/non-contract-changing adjustments -> V1.x;
    changes to core research logic, model definitions or governance
    boundaries -> V2.0."""
    return VersionBump.MAJOR if changes_core_logic else VersionBump.MINOR
