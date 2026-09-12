"""G02 — Agent autonomy controller (WBS-B6, ADR-0017 §3, Charter §21, CF-37..46).

`authorize()` is the runtime GP-21 enforcement gate: every agent action
must pass through it before any work happens (see agents/base.py). Each
agent may perform *only* the one `action_kind` its roster entry declares
(least privilege — even within the same power bucket, e.g. A07 vs A08).
`is_l3_eligible()` is a pure predicate for Charter §21's L3 conditions —
it does not itself execute any state transition (that's G01's full rule
engine, WBS-B8).
"""

from __future__ import annotations

from governance.rbac import AGENT_ROSTER, ActionKind
from knowledge.db.base import CflStatus

__all__ = ["ActionKind", "AutonomyViolation", "authorize", "is_l3_eligible"]


class AutonomyViolation(PermissionError):
    """GP-21 / CF-37..46: an agent attempted an action outside its role."""


def authorize(agent_id: str, action: ActionKind) -> None:
    role = AGENT_ROSTER.get(agent_id)
    if role is None:
        raise AutonomyViolation(f"unknown agent_id {agent_id!r}")
    if action is not role.action_kind:
        raise AutonomyViolation(
            f"{agent_id} ({role.power.value}) may only perform {role.action_kind.value}, "
            f"not {action.value} (GP-21 / CF-37..46)"
        )


def is_l3_eligible(
    *,
    cfl_status: CflStatus,
    confidence: float | None,
    confidence_threshold: float,
    has_conflict: bool,
    is_high_risk_transition: bool,
) -> bool:
    """Charter §21 verbatim: L3 acts only when the rule is clear, confidence
    is sufficient, there is no material conflict, and the transition is not
    high-risk — and only once CFL has passed. `confidence_threshold` is a
    caller-supplied config value (Charter gives no fixed number; specific
    thresholds are Deferred to G01's full rule engine, WBS-B8)."""
    if cfl_status not in (CflStatus.AUTO_PASS, CflStatus.APPROVED):
        return False
    if has_conflict or is_high_risk_transition:
        return False
    return confidence is not None and confidence >= confidence_threshold
