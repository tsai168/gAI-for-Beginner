"""G05 — RBAC: agent roles and the GP-21 four-power model (WBS-B6, ADR-0017 §2)
+ the six Charter §5 human user roles (WBS-B9, ADR-0021, Work-2 §4.4).

`AgentRole.power` is a single value, not a set — "one agent, one power" is
enforced by the shape of the data. Each role also carries the *one*
specific `action_kind` it may perform (least privilege: within the `NONE`
power bucket, A07 and A08 do different mechanical jobs and must not be
interchangeable even though neither holds a substantive research power).
G02 (`governance.autonomy`) is the runtime enforcement gate that consumes
this roster.

`UserRole`/`FunctionGroup`/`USER_RBAC_MATRIX` are a separate table for the
six human roles Work-2 §4.4 defines for the U05 API layer — transcribed
verbatim from that section's matrix, not derived from the agent roster
above (a human account and an agent account are governed independently).
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


# --- Work-2 §4.4: six Charter §5 human user roles --------------------------


class UserRole(enum.StrEnum):
    """Charter §5."""

    RESEARCH_DIRECTOR = "RESEARCH_DIRECTOR"
    SEMICONDUCTOR_ANALYST = "SEMICONDUCTOR_ANALYST"
    QUANT_RESEARCHER = "QUANT_RESEARCHER"
    RESEARCH_REVIEWER = "RESEARCH_REVIEWER"
    EXECUTIVE_USER = "EXECUTIVE_USER"
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMINISTRATOR"


class FunctionGroup(enum.StrEnum):
    """Work-2 §4.4 RBAC matrix columns (讀／Evidence-實體寫／模型執行／審查佇列／
    核准-發布／Ops-設定). READ_SUMMARY is Executive User's qualified "讀（摘要）"
    — strictly weaker than READ, see `role_satisfies`."""

    READ = "READ"
    READ_SUMMARY = "READ_SUMMARY"
    EVIDENCE_WRITE = "EVIDENCE_WRITE"
    MODEL_EXEC = "MODEL_EXEC"
    REVIEW_QUEUE = "REVIEW_QUEUE"
    APPROVAL_PUBLISH = "APPROVAL_PUBLISH"
    OPS_CONFIG = "OPS_CONFIG"


# Work-2 §4.4 matrix, transcribed verbatim (✓ cells only).
USER_RBAC_MATRIX: dict[UserRole, frozenset[FunctionGroup]] = {
    UserRole.RESEARCH_DIRECTOR: frozenset(
        {FunctionGroup.READ, FunctionGroup.REVIEW_QUEUE, FunctionGroup.APPROVAL_PUBLISH}
    ),
    UserRole.SEMICONDUCTOR_ANALYST: frozenset({FunctionGroup.READ, FunctionGroup.EVIDENCE_WRITE}),
    UserRole.QUANT_RESEARCHER: frozenset({FunctionGroup.READ, FunctionGroup.MODEL_EXEC}),
    UserRole.RESEARCH_REVIEWER: frozenset({FunctionGroup.READ, FunctionGroup.REVIEW_QUEUE}),
    UserRole.EXECUTIVE_USER: frozenset({FunctionGroup.READ_SUMMARY}),
    UserRole.SYSTEM_ADMINISTRATOR: frozenset({FunctionGroup.READ, FunctionGroup.OPS_CONFIG}),
}

_FORBIDDEN_USER_COMBINATION = (FunctionGroup.EVIDENCE_WRITE, FunctionGroup.APPROVAL_PUBLISH)


class UserRbacViolation(ValueError):
    """A human role would hold both Evidence/entity-write and
    Approval/Publish — Work-2 §4.4 / GP-21 / CF-46 forbid this combination
    for any single role, agent or human."""


def assert_no_cross_power_role(
    matrix: dict[UserRole, frozenset[FunctionGroup]] = USER_RBAC_MATRIX,
) -> None:
    write, approve = _FORBIDDEN_USER_COMBINATION
    for role, groups in matrix.items():
        if write in groups and approve in groups:
            raise UserRbacViolation(
                f"{role}: holds both {write.value} and {approve.value} (GP-21/CF-46)"
            )


def role_satisfies(role: UserRole, required: FunctionGroup) -> bool:
    """A role holding full READ also satisfies a READ_SUMMARY requirement
    (full access is a superset of summary access); the reverse does not
    hold — Executive User's READ_SUMMARY never satisfies a plain READ
    requirement (Charter §5: reads summaries only)."""
    groups = USER_RBAC_MATRIX[role]
    if required is FunctionGroup.READ_SUMMARY:
        return FunctionGroup.READ_SUMMARY in groups or FunctionGroup.READ in groups
    return required in groups
