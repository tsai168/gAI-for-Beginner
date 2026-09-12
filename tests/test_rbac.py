"""WBS-B6 unit tests: G05 RBAC roster + GP-21 compliance (ADR-0017 §2)."""

from __future__ import annotations

import pytest

from governance.rbac import (
    AGENT_ROSTER,
    ActionKind,
    AgentPower,
    AgentRole,
    AutonomyLevel,
    GP21Violation,
    assert_gp21_roster_compliance,
)


def test_roster_has_all_eight_agents() -> None:
    assert set(AGENT_ROSTER) == {f"A0{i}" for i in range(1, 9)}


def test_real_roster_is_gp21_compliant() -> None:
    assert_gp21_roster_compliance()  # no raise


@pytest.mark.parametrize(
    "agent_id,expected_power",
    [
        ("A01", AgentPower.EVIDENCE),
        ("A02", AgentPower.ANALYSIS),
        ("A03", AgentPower.ANALYSIS),
        ("A04", AgentPower.ANALYSIS),
        ("A05", AgentPower.ANALYSIS),
        ("A06", AgentPower.ANALYSIS),
        ("A07", AgentPower.NONE),
        ("A08", AgentPower.NONE),
    ],
)
def test_agent_powers_match_spec(agent_id: str, expected_power: AgentPower) -> None:
    assert AGENT_ROSTER[agent_id].power is expected_power


def test_no_agent_holds_approval_or_publication() -> None:
    forbidden = {AgentPower.APPROVAL, AgentPower.PUBLICATION}
    for role in AGENT_ROSTER.values():
        assert role.power not in forbidden, role.agent_id


def test_gp21_violation_detected_for_rigged_roster() -> None:
    rigged = dict(AGENT_ROSTER)
    rigged["A01"] = AgentRole(
        "A01", "抽取代理", AutonomyLevel.L1, AgentPower.APPROVAL, ActionKind.APPROVE
    )
    with pytest.raises(GP21Violation, match="A01"):
        assert_gp21_roster_compliance(rigged)


def test_gp21_violation_when_action_kind_mismatches_power() -> None:
    rigged = dict(AGENT_ROSTER)
    rigged["A02"] = AgentRole(
        "A02", "實體判斷與分類代理", AutonomyLevel.L1, AgentPower.ANALYSIS, ActionKind.APPROVE
    )
    with pytest.raises(GP21Violation, match="A02"):
        assert_gp21_roster_compliance(rigged)


def test_agent_role_power_is_a_single_value_not_a_collection() -> None:
    # structural guarantee (ADR-0017 §2): power is a scalar field
    role = AGENT_ROSTER["A01"]
    assert isinstance(role.power, AgentPower)
