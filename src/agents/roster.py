"""A01-A08 concrete agent declarations (WBS-B6, ADR-0017 §4).

Each class only declares `agent_id`/`action_kind` (matching its
`governance.rbac.AGENT_ROSTER` entry) and defers `_perform` — see
`agents.base.Agent` for what "deferred" means here.
"""

from __future__ import annotations

from typing import Any

from agents.base import Agent
from governance.autonomy import ActionKind


class ExtractionAgent(Agent):  # A01
    agent_id = "A01"
    action_kind = ActionKind.WRITE_CANDIDATE

    def _perform(self, payload: Any) -> Any:
        raise NotImplementedError("A01 extraction (LLM) deferred — no prompt/schema spec yet")


class ClassificationAgent(Agent):  # A02
    agent_id = "A02"
    action_kind = ActionKind.RECOMMEND

    def _perform(self, payload: Any) -> Any:
        raise NotImplementedError("A02 classification (LLM) deferred")


class RelationshipConflictAgent(Agent):  # A03
    agent_id = "A03"
    action_kind = ActionKind.RECOMMEND

    def _perform(self, payload: Any) -> Any:
        raise NotImplementedError("A03 relationship/conflict analysis (LLM) deferred")


class SecoCmiMaterialityAgent(Agent):  # A04
    agent_id = "A04"
    action_kind = ActionKind.RECOMMEND

    def _perform(self, payload: Any) -> Any:
        raise NotImplementedError("A04 Seco/CMI/materiality analysis (LLM) deferred")


class ComparisonAgent(Agent):  # A05
    agent_id = "A05"
    action_kind = ActionKind.RECOMMEND

    def _perform(self, payload: Any) -> Any:
        raise NotImplementedError("A05 comparison analysis (LLM) deferred")


class CriticAgent(Agent):  # A06
    agent_id = "A06"
    action_kind = ActionKind.RECOMMEND

    def _perform(self, payload: Any) -> Any:
        raise NotImplementedError("A06 contradiction/leak review (LLM) deferred")


class CoordinatorAgent(Agent):  # A07
    agent_id = "A07"
    action_kind = ActionKind.ORCHESTRATE

    def _perform(self, payload: Any) -> Any:
        raise NotImplementedError("A07 fan-out/fan-in orchestration wired in WBS-B7 (Temporal)")


class HumanGatewayAgent(Agent):  # A08
    agent_id = "A08"
    action_kind = ActionKind.ROUTE_TO_HUMAN

    def _perform(self, payload: Any) -> Any:
        raise NotImplementedError("A08 human-review routing wired in WBS-B10 (U04)")


ALL_AGENTS: tuple[type[Agent], ...] = (
    ExtractionAgent,
    ClassificationAgent,
    RelationshipConflictAgent,
    SecoCmiMaterialityAgent,
    ComparisonAgent,
    CriticAgent,
    CoordinatorAgent,
    HumanGatewayAgent,
)
