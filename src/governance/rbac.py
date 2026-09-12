"""G05 — RBAC: agent roles and the GP-21 four-power model (WBS-B6, ADR-0017 §2).

`AgentRole.power` is a single value, not a set — "one agent, one power" is
enforced by the shape of the data. Each role also carries the *one*
specific `action_kind` it may perform (least privilege: within the `NONE`
power bucket, A07 and A08 do different mechanical jobs and must not be
interchangeable even though neither holds a substantive research power).
G02 (`governance.autonomy`) is the runtime enforcement gate that consumes
this roster.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class AgentPower(enum.StrEnum):
    """Charter §21 / GP-21's four separable powers, plus NONE for agents
    that hold no substantive research power (pure orchestration / routing)."""

    EVIDENCE = "EVIDENCE"
    ANALYSIS = "ANALYSIS"
    APPROVAL = "APPROVAL"
    PUBLICATION = "PUBLICATION"
    NONE = "NONE"


class ActionKind(enum.StrEnum):
    WRITE_CANDIDATE = "WRITE_CANDIDATE"  # L1 (EVIDENCE)
    RECOMMEND = "RECOMMEND"  # L2 (ANALYSIS)
    ORCHESTRATE = "ORCHESTRATE"  # L0 (NONE) — A07
    ROUTE_TO_HUMAN = "ROUTE_TO_HUMAN"  # L3/L4 gate (NONE) — A08
    APPROVE = "APPROVE"  # reserved: G01 / human (APPROVAL) — no agent holds this
    PUBLISH = "PUBLISH"  # reserved: G06 / human (PUBLICATION) — no agent holds this


class AutonomyLevel(enum.StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


@dataclass(slots=True, frozen=True)
class AgentRole:
    agent_id: str  # "A01".."A08"
    name: str
    autonomy: AutonomyLevel
    power: AgentPower
    action_kind: ActionKind


# Which ActionKinds are compatible with which power (consistency check,
# not itself the per-agent authorization — see assert_gp21_roster_compliance).
ACTIONS_FOR_POWER: dict[AgentPower, frozenset[ActionKind]] = {
    AgentPower.EVIDENCE: frozenset({ActionKind.WRITE_CANDIDATE}),
    AgentPower.ANALYSIS: frozenset({ActionKind.RECOMMEND}),
    AgentPower.NONE: frozenset({ActionKind.ORCHESTRATE, ActionKind.ROUTE_TO_HUMAN}),
    AgentPower.APPROVAL: frozenset({ActionKind.APPROVE}),
    AgentPower.PUBLICATION: frozenset({ActionKind.PUBLISH}),
}

# Work-1 §3.5 / Work-2 §6 AGENT_SPEC. See ADR-0017 §2 for the A02/A06
# Work-1 §5 rollup-table gap this resolves using each agent's own row.
AGENT_ROSTER: dict[str, AgentRole] = {
    "A01": AgentRole(
        "A01", "抽取代理", AutonomyLevel.L1, AgentPower.EVIDENCE, ActionKind.WRITE_CANDIDATE
    ),
    "A02": AgentRole(
        "A02", "實體判斷與分類代理", AutonomyLevel.L1, AgentPower.ANALYSIS, ActionKind.RECOMMEND
    ),
    "A03": AgentRole(
        "A03", "關係與矛盾分析代理", AutonomyLevel.L2, AgentPower.ANALYSIS, ActionKind.RECOMMEND
    ),
    "A04": AgentRole(
        "A04",
        "Seco／CMI／重大性分析代理",
        AutonomyLevel.L2,
        AgentPower.ANALYSIS,
        ActionKind.RECOMMEND,
    ),
    "A05": AgentRole(
        "A05", "比較分析代理", AutonomyLevel.L2, AgentPower.ANALYSIS, ActionKind.RECOMMEND
    ),
    "A06": AgentRole(
        "A06", "審查代理（Critic）", AutonomyLevel.L2, AgentPower.ANALYSIS, ActionKind.RECOMMEND
    ),
    "A07": AgentRole("A07", "協調代理", AutonomyLevel.L0, AgentPower.NONE, ActionKind.ORCHESTRATE),
    "A08": AgentRole(
        "A08", "人工介接閘道代理", AutonomyLevel.L3, AgentPower.NONE, ActionKind.ROUTE_TO_HUMAN
    ),
}

_FORBIDDEN_FOR_AGENTS = (AgentPower.APPROVAL, AgentPower.PUBLICATION)


class GP21Violation(ValueError):
    """An agent role would hold Approval or Publication power, or its
    declared action_kind doesn't match its power — Charter's design
    reserves Approval/Publication to governance modules (G01/G06) and
    human authority (L4), never to an A01-A08 account."""


def assert_gp21_roster_compliance(roster: dict[str, AgentRole] = AGENT_ROSTER) -> None:
    for role in roster.values():
        if role.power in _FORBIDDEN_FOR_AGENTS:
            raise GP21Violation(
                f"{role.agent_id} ({role.name}) holds {role.power.value} — "
                "no agent may hold Approval or Publication power (GP-21)"
            )
        if role.action_kind not in ACTIONS_FOR_POWER.get(role.power, frozenset()):
            raise GP21Violation(
                f"{role.agent_id}: action_kind {role.action_kind.value} is not valid "
                f"for power {role.power.value}"
            )
