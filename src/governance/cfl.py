"""G01 — CFL rule engine (WBS-B8, ADR-0020; replaces the B1 stub — ADR-0004
decision 2, ADR-0007 §6). Callers are unchanged (Work-3 §2 DAG B8 row:
"替換 B1 介面樁，不動呼叫端"): they still import `default_cfl_service`, still
call `submit_candidate(session, table=..., row_id=..., cfl_id=...)`.

Every write to a ``cfl_status`` column must go through this module. A DB
trigger (migration 0001) rejects direct updates unless the session GUC
``cpoai.cfl_engine`` is set to ``'on'`` — use ``cfl_write(session)``.

Decision rules (Charter §17 V1 principles), each keyed off columns the
governed row already carries so no caller needs to change:

- CFL-01 公司身分 — ``company.confidence`` high *and* ``stock_code`` set
  (verifiable) -> AUTO-PASS; else REVIEW-REQUIRED. No caller raises this
  yet (A02 candidate generation isn't built) — the rule is ready for when
  it is.
- CFL-02 CPO 分類 — ``company.set_universe`` only ever submits a candidate
  for a *first* upgrade to Core (Charter: "首次升 Core 需 Human
  Review") -> always REVIEW-REQUIRED when actually raised.
- CFL-03 來源可信度 — ``evidence.source_credibility_tier`` set (known D01-D08
  official source) -> AUTO-PASS; unset (new/unknown source) ->
  REVIEW-REQUIRED.
- CFL-04 重大事件 — ``event.materiality_score`` >= threshold -> REVIEW-
  REQUIRED (high Materiality needs Human Review); else AUTO-PASS (general
  event, AI classification stands).
- CFL-05 生態系關係 — ``relationship.confirm_relationship`` only ever submits
  a candidate for a first CONFIRMED *named* relationship -> always
  REVIEW-REQUIRED when actually raised.
- CFL-06 競爭分析 — no candidate generator wired yet (R05 comparison-output
  schema doesn't exist); conservative default REVIEW-REQUIRED until a real
  Draft-vs-formal-conclusion signal exists.
- CFL-07/08 — Charter: must never AUTO-PASS (``NO_AUTO_PASS``); always
  REVIEW-REQUIRED.

HIGH_CONFIDENCE_THRESHOLD / HIGH_MATERIALITY_THRESHOLD are V1 Expert-Rule
defaults (like M02/M05's own weights) — adjustable via ADR, not a Frozen
Decision.

Every decision this engine makes is also recorded via `governance.audit`
(G03) — Agent/Rule/Input/Evidence/Confidence/Model, CF-45.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

from governance.audit import record_decision
from knowledge.db.base import CflStatus


class CflId(enum.StrEnum):
    CFL_01 = "CFL-01"  # 公司身分
    CFL_02 = "CFL-02"  # CPO 分類
    CFL_03 = "CFL-03"  # 來源可信度
    CFL_04 = "CFL-04"  # 重大事件
    CFL_05 = "CFL-05"  # 生態系關係
    CFL_06 = "CFL-06"  # 競爭分析
    CFL_07 = "CFL-07"  # 矛盾資料
    CFL_08 = "CFL-08"  # 發布核准


# Charter §17 lifecycle: PENDING -> AUTO-PASS/REVIEW-REQUIRED ->
# APPROVED/REJECTED/BLOCKED -> SUPERSEDED
CFL_TRANSITIONS: dict[CflStatus, frozenset[CflStatus]] = {
    CflStatus.PENDING: frozenset(
        {CflStatus.AUTO_PASS, CflStatus.REVIEW_REQUIRED, CflStatus.BLOCKED}
    ),
    CflStatus.AUTO_PASS: frozenset({CflStatus.APPROVED, CflStatus.SUPERSEDED}),
    CflStatus.REVIEW_REQUIRED: frozenset(
        {CflStatus.APPROVED, CflStatus.REJECTED, CflStatus.BLOCKED, CflStatus.SUPERSEDED}
    ),
    CflStatus.APPROVED: frozenset({CflStatus.SUPERSEDED}),
    CflStatus.REJECTED: frozenset({CflStatus.SUPERSEDED}),
    CflStatus.BLOCKED: frozenset({CflStatus.REVIEW_REQUIRED, CflStatus.SUPERSEDED}),
    CflStatus.SUPERSEDED: frozenset(),
}

# CFL ids that may never resolve to AUTO-PASS (Charter §17 / CFL-07).
NO_AUTO_PASS: frozenset[CflId] = frozenset({CflId.CFL_07, CflId.CFL_08})

_GUC = "cpoai.cfl_engine"

# V1 Expert-Rule defaults — adjustable via ADR, never a Frozen Decision.
HIGH_CONFIDENCE_THRESHOLD = 0.85  # CFL-01
HIGH_MATERIALITY_THRESHOLD = 70.0  # CFL-04, 0..100 scale (CF-27)


def is_valid_transition(current: CflStatus, target: CflStatus) -> bool:
    return target in CFL_TRANSITIONS.get(current, frozenset())


@contextmanager
def cfl_write(session: Session) -> Iterator[None]:
    """Open a window in which cfl_status writes are allowed (sets the GUC for
    the current transaction only)."""
    session.execute(text(f"SET LOCAL {_GUC} = 'on'"))
    try:
        yield
    finally:
        session.execute(text(f"SET LOCAL {_GUC} = 'off'"))


def _pk_column(table: str) -> str:
    return "relationship_id" if table == "relationship" else f"{table}_id"


def _fetch_one(session: Session, sql: str, row_id: uuid.UUID) -> tuple[object, ...]:
    row = session.execute(text(sql), {"id": row_id}).first()
    if row is None:
        raise LookupError(f"row {row_id} not found for CFL decision ({sql})")
    return tuple(row)


def _decide_cfl_01(session: Session, row_id: uuid.UUID) -> CflStatus:
    confidence, stock_code = _fetch_one(
        session, "SELECT confidence, stock_code FROM company WHERE company_id = :id", row_id
    )
    if (
        confidence is not None
        and float(confidence) >= HIGH_CONFIDENCE_THRESHOLD  # type: ignore[arg-type]
        and stock_code is not None
    ):
        return CflStatus.AUTO_PASS
    return CflStatus.REVIEW_REQUIRED


def _decide_cfl_03(session: Session, row_id: uuid.UUID) -> CflStatus:
    (tier,) = _fetch_one(
        session, "SELECT source_credibility_tier FROM evidence WHERE evidence_id = :id", row_id
    )
    return CflStatus.AUTO_PASS if tier is not None else CflStatus.REVIEW_REQUIRED


def _decide_cfl_04(session: Session, row_id: uuid.UUID) -> CflStatus:
    (score,) = _fetch_one(
        session, "SELECT materiality_score FROM event WHERE event_id = :id", row_id
    )
    if score is not None and float(score) >= HIGH_MATERIALITY_THRESHOLD:  # type: ignore[arg-type]
        return CflStatus.REVIEW_REQUIRED
    return CflStatus.AUTO_PASS


def _always_review(session: Session, row_id: uuid.UUID) -> CflStatus:
    return CflStatus.REVIEW_REQUIRED


_DECIDERS: dict[CflId, Callable[[Session, uuid.UUID], CflStatus]] = {
    CflId.CFL_01: _decide_cfl_01,
    CflId.CFL_02: _always_review,
    CflId.CFL_03: _decide_cfl_03,
    CflId.CFL_04: _decide_cfl_04,
    CflId.CFL_05: _always_review,
    CflId.CFL_06: _always_review,
    CflId.CFL_07: _always_review,
    CflId.CFL_08: _always_review,
}


def _decide(session: Session, *, row_id: uuid.UUID, cfl_id: CflId) -> CflStatus:
    return _DECIDERS[cfl_id](session, row_id)


class CflService(Protocol):
    def submit_candidate(
        self,
        session: Session,
        *,
        table: str,
        row_id: uuid.UUID,
        cfl_id: CflId,
        agent_id: str | None = None,
        correlation_id: uuid.UUID | None = None,
    ) -> CflStatus: ...

    def query_status(self, session: Session, *, table: str, row_id: uuid.UUID) -> CflStatus: ...

    def set_status(
        self,
        session: Session,
        *,
        table: str,
        row_id: uuid.UUID,
        target: CflStatus,
        cfl_id: CflId,
        agent_id: str | None = None,
        correlation_id: uuid.UUID | None = None,
    ) -> None: ...


class RuleBasedCflService:
    """WBS-B8: the real AUTO-PASS/REVIEW-REQUIRED engine (module docstring
    has the per-CFL rules). Replaces the B1 `DefaultCflService` stub."""

    def submit_candidate(
        self,
        session: Session,
        *,
        table: str,
        row_id: uuid.UUID,
        cfl_id: CflId,
        agent_id: str | None = None,
        correlation_id: uuid.UUID | None = None,
    ) -> CflStatus:
        current = self.query_status(session, table=table, row_id=row_id)
        if current is not CflStatus.PENDING:
            # Already decided (or a human already moved it past PENDING) —
            # submitting again is idempotent, not a re-evaluation.
            return current
        target = _decide(session, row_id=row_id, cfl_id=cfl_id)
        self.set_status(
            session,
            table=table,
            row_id=row_id,
            target=target,
            cfl_id=cfl_id,
            agent_id=agent_id,
            correlation_id=correlation_id,
        )
        return target

    def query_status(self, session: Session, *, table: str, row_id: uuid.UUID) -> CflStatus:
        pk = _pk_column(table)
        row = session.execute(
            text(f"SELECT cfl_status FROM {table} WHERE {pk} = :id"), {"id": row_id}
        ).first()
        if row is None:
            raise LookupError(f"{table} {row_id} not found")
        return CflStatus(row[0])

    def set_status(
        self,
        session: Session,
        *,
        table: str,
        row_id: uuid.UUID,
        target: CflStatus,
        cfl_id: CflId,
        agent_id: str | None = None,
        correlation_id: uuid.UUID | None = None,
    ) -> None:
        current = self.query_status(session, table=table, row_id=row_id)
        if not is_valid_transition(current, target):
            raise ValueError(f"illegal CFL transition {current} -> {target}")
        if target is CflStatus.AUTO_PASS and cfl_id in NO_AUTO_PASS:
            raise ValueError(f"{cfl_id} must not AUTO-PASS")
        pk = _pk_column(table)
        confidence_row = session.execute(
            text(f"SELECT confidence, model_version_id FROM {table} WHERE {pk} = :id"),
            {"id": row_id},
        ).first()
        confidence = (
            float(confidence_row[0])
            if confidence_row is not None and confidence_row[0] is not None
            else None
        )
        model_version_id = confidence_row[1] if confidence_row is not None else None
        with cfl_write(session):
            session.execute(
                text(f"UPDATE {table} SET cfl_status = :s WHERE {pk} = :id"),
                {"s": target.value, "id": row_id},
            )
        record_decision(
            session,
            rule_ref=cfl_id.value,
            table_name=table,
            row_id=row_id,
            decision=target.value,
            agent_id=agent_id,
            confidence=confidence,
            model_version_id=model_version_id,
            correlation_id=correlation_id,
        )


default_cfl_service: CflService = RuleBasedCflService()
