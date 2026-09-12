"""G03 — Audit log / decision trail (WBS-B8, ADR-0020, CF-45, Charter §22
Auditability).

Every governance decision keeps Agent, Rule, Input, Evidence, Confidence
and Model on record (Work-1 §3.8 G03), per an append-only row — a DB
trigger (migration 0006) rejects UPDATE/DELETE on `audit_log`, the same
guard `source_snapshot` already uses (CF-08/GP-15): history is written
once, never edited.

`governance.cfl.RuleBasedCflService.set_status` is the first caller (every
cfl_status write logs one entry here); nothing else is wired to this module
yet — future Agent/Recommendation decisions (A01–A08) can call
`record_decision` the same way once they exist.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge.db.models import AuditLogEntry


def record_decision(
    session: Session,
    *,
    rule_ref: str,
    table_name: str,
    row_id: uuid.UUID,
    decision: str,
    agent_id: str | None = None,
    evidence_ids: Sequence[uuid.UUID] = (),
    confidence: float | None = None,
    model_version_id: uuid.UUID | None = None,
    correlation_id: uuid.UUID | None = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        agent_id=agent_id,
        rule_ref=rule_ref,
        table_name=table_name,
        row_id=row_id,
        decision=decision,
        evidence_ids=list(evidence_ids),
        confidence=confidence,
        model_version_id=model_version_id,
        correlation_id=correlation_id,
    )
    session.add(entry)
    session.flush()
    return entry


def list_decisions_for_row(
    session: Session, *, table_name: str, row_id: uuid.UUID
) -> list[AuditLogEntry]:
    """Traceability lookup (Charter §22): the full decision history for one
    governed row, oldest first."""
    return list(
        session.execute(
            select(AuditLogEntry)
            .where(AuditLogEntry.table_name == table_name, AuditLogEntry.row_id == row_id)
            .order_by(AuditLogEntry.created_at)
        ).scalars()
    )


def list_decisions_since(
    session: Session,
    *,
    since: datetime,
    until: datetime | None = None,
    rule_ref: str | None = None,
) -> list[AuditLogEntry]:
    """WBS-B11 (R01 daily digest): decisions in a time window, oldest
    first."""
    stmt = select(AuditLogEntry).where(AuditLogEntry.created_at >= since)
    if until is not None:
        stmt = stmt.where(AuditLogEntry.created_at < until)
    if rule_ref is not None:
        stmt = stmt.where(AuditLogEntry.rule_ref == rule_ref)
    stmt = stmt.order_by(AuditLogEntry.created_at)
    return list(session.execute(stmt).scalars())
