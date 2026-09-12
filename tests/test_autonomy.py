"""WBS-B6 unit tests: G02 autonomy controller (ADR-0017 §3)."""

from __future__ import annotations

import pytest

from governance.autonomy import ActionKind, AutonomyViolation, authorize, is_l3_eligible
from governance.rbac import AGENT_ROSTER
from knowledge.db.base import CflStatus

_CORRECT_ACTION: dict[str, ActionKind] = {
    "A01": ActionKind.WRITE_CANDIDATE,
    "A02": ActionKind.RECOMMEND,
    "A03": ActionKind.RECOMMEND,
    "A04": ActionKind.RECOMMEND,
    "A05": ActionKind.RECOMMEND,
    "A06": ActionKind.RECOMMEND,
    "A07": ActionKind.ORCHESTRATE,
    "A08": ActionKind.ROUTE_TO_HUMAN,
}


@pytest.mark.parametrize("agent_id,action", list(_CORRECT_ACTION.items()))
def test_authorize_allows_the_correct_action(agent_id: str, action: ActionKind) -> None:
    authorize(agent_id, action)  # no raise


@pytest.mark.parametrize("agent_id", list(AGENT_ROSTER))
@pytest.mark.parametrize("action", list(ActionKind))
def test_authorize_matrix(agent_id: str, action: ActionKind) -> None:
    if _CORRECT_ACTION[agent_id] is action:
        authorize(agent_id, action)
    else:
        with pytest.raises(AutonomyViolation):
            authorize(agent_id, action)


def test_no_agent_may_approve_or_publish() -> None:
    for agent_id in AGENT_ROSTER:
        with pytest.raises(AutonomyViolation):
            authorize(agent_id, ActionKind.APPROVE)
        with pytest.raises(AutonomyViolation):
            authorize(agent_id, ActionKind.PUBLISH)


def test_authorize_rejects_unknown_agent() -> None:
    with pytest.raises(AutonomyViolation, match="unknown agent_id"):
        authorize("A99", ActionKind.RECOMMEND)


# --- is_l3_eligible (Charter §21) -------------------------------------------

_BASE_KWARGS = {
    "cfl_status": CflStatus.AUTO_PASS,
    "confidence": 0.9,
    "confidence_threshold": 0.8,
    "has_conflict": False,
    "is_high_risk_transition": False,
}


def test_l3_eligible_when_all_conditions_met() -> None:
    assert is_l3_eligible(**_BASE_KWARGS) is True


@pytest.mark.parametrize(
    "override",
    [
        {"cfl_status": CflStatus.PENDING},
        {"cfl_status": CflStatus.REVIEW_REQUIRED},
        {"has_conflict": True},
        {"is_high_risk_transition": True},
        {"confidence": 0.5},
        {"confidence": None},
    ],
)
def test_l3_not_eligible_when_any_condition_fails(override: dict) -> None:
    kwargs = {**_BASE_KWARGS, **override}
    assert is_l3_eligible(**kwargs) is False


def test_l3_eligible_also_true_for_already_approved() -> None:
    kwargs = {**_BASE_KWARGS, "cfl_status": CflStatus.APPROVED}
    assert is_l3_eligible(**kwargs) is True
