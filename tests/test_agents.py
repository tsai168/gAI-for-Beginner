"""WBS-B6 unit tests: A01-A08 agent skeleton (ADR-0017 §4)."""

from __future__ import annotations

import pytest

from agents.base import Agent
from agents.roster import (
    ALL_AGENTS,
    ClassificationAgent,
    CoordinatorAgent,
    ExtractionAgent,
)
from governance.autonomy import ActionKind, AutonomyViolation


def test_all_eight_agents_registered() -> None:
    assert len(ALL_AGENTS) == 8
    assert {cls.agent_id for cls in ALL_AGENTS} == {f"A0{i}" for i in range(1, 9)}


_STILL_UNIMPLEMENTED = [cls for cls in ALL_AGENTS if cls is not ExtractionAgent]


@pytest.mark.parametrize("agent_cls", _STILL_UNIMPLEMENTED)
def test_run_passes_gate_then_defers_to_not_implemented(agent_cls: type[Agent]) -> None:
    agent = agent_cls()
    with pytest.raises(NotImplementedError):
        agent.run({"payload": "irrelevant"})


def test_role_property_matches_roster() -> None:
    agent = ExtractionAgent()
    assert agent.role.agent_id == "A01"
    assert agent.role.name == "抽取代理"


def test_mismatched_action_kind_is_blocked_by_authorize() -> None:
    class RoguePowerAgent(ClassificationAgent):
        # A02 is ANALYSIS-only; pretending to approve must be rejected
        action_kind = ActionKind.APPROVE

    with pytest.raises(AutonomyViolation):
        RoguePowerAgent().run({})


def test_coordinator_is_orchestrate_only() -> None:
    with pytest.raises(NotImplementedError, match="B7"):
        CoordinatorAgent().run({})
