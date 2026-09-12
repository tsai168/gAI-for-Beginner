"""A01-A08 — Agent base class (WBS-B6, ADR-0017 §4).

Every `run()` call is gated by G02 (`governance.autonomy.authorize`) before
any work happens. `_perform` — the actual extraction/analysis logic, which
would call an LLM (Claude, per ADR-0001 §3.1) — is deferred: Charter/Work-1
through 3 specify no prompts, output schemas, or per-source extraction
rules. That is product design work, out of scope here (same posture as
P01's concrete site adapters, ADR-0009).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from governance.autonomy import ActionKind, authorize
from governance.rbac import AGENT_ROSTER, AgentRole


class Agent(ABC):
    agent_id: ClassVar[str]
    action_kind: ClassVar[ActionKind]

    @property
    def role(self) -> AgentRole:
        return AGENT_ROSTER[self.agent_id]

    def run(self, payload: Any) -> Any:
        authorize(self.agent_id, self.action_kind)
        return self._perform(payload)

    @abstractmethod
    def _perform(self, payload: Any) -> Any: ...
