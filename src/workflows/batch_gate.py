"""W06 — Batch AI Parsing gate (WBS-B7a, ADR-0018 §4, Charter §19, GP-16).

The single entry point deciding whether an LLM (Batch AI Parsing / A01-A06)
may be invoked at all. Ties together P02 (dedup), W01 (wake-up window) and
W02 (priority) — "Deterministic First, AI When Needed."
"""

from __future__ import annotations

from dataclasses import dataclass

from ingestion.dedup import DedupVerdict
from workflows.priority_queue import Priority


@dataclass(slots=True, frozen=True)
class BatchGateDecision:
    should_call_llm: bool
    reason: str


def evaluate_batch_gate(
    *, dedup_verdict: DedupVerdict, within_wakeup_window: bool, priority: Priority
) -> BatchGateDecision:
    if dedup_verdict is not DedupVerdict.NEW:
        return BatchGateDecision(
            False, "content already seen (P02) — deterministic dedup suffices, no LLM (GP-16)"
        )
    if priority is Priority.HIGH:
        return BatchGateDecision(
            True, "high-priority material event — Priority Trigger bypasses wake-up window"
        )
    if not within_wakeup_window:
        return BatchGateDecision(False, "outside the configured wake-up window")
    return BatchGateDecision(True, "new content, within wake-up window")
