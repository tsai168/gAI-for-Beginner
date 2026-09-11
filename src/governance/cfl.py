"""G01 — CFL rule engine: B1 interface stub (ADR-0004 decision 2, ADR-0007 §6).

B1 provides only the contract surface + a "no auto-pass" default. B8 replaces
``DefaultCflService`` with the real rule engine; the DB trigger and callers
do not change.

Every write to a ``cfl_status`` column must go through this module. A DB
trigger (migration 0001) rejects direct updates unless the session GUC
``cpoai.cfl_engine`` is set to ``'on'`` — use ``cfl_write(session)``.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

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


class CflService(Protocol):
    def submit_candidate(
        self, session: Session, *, table: str, row_id: uuid.UUID, cfl_id: CflId
    ) -> CflStatus: ...

    def query_status(self, session: Session, *, table: str, row_id: uuid.UUID) -> CflStatus: ...


class DefaultCflService:
    """B1 stub: rows are created PENDING (DB default); no auto-pass. B8
    supplies the real decision logic."""

    def submit_candidate(
        self, session: Session, *, table: str, row_id: uuid.UUID, cfl_id: CflId
    ) -> CflStatus:
        # No-op beyond asserting the row exists and stays PENDING. The real
        # engine (B8) evaluates CFL rules here and may set AUTO-PASS /
        # REVIEW-REQUIRED (never AUTO-PASS for NO_AUTO_PASS ids).
        _ = cfl_id
        return self.query_status(session, table=table, row_id=row_id)

    def query_status(self, session: Session, *, table: str, row_id: uuid.UUID) -> CflStatus:
        pk = f"{table}_id" if table != "relationship" else "relationship_id"
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
    ) -> None:
        current = self.query_status(session, table=table, row_id=row_id)
        if not is_valid_transition(current, target):
            raise ValueError(f"illegal CFL transition {current} -> {target}")
        if target is CflStatus.AUTO_PASS and cfl_id in NO_AUTO_PASS:
            raise ValueError(f"{cfl_id} must not AUTO-PASS")
        pk = f"{table}_id" if table != "relationship" else "relationship_id"
        with cfl_write(session):
            session.execute(
                text(f"UPDATE {table} SET cfl_status = :s WHERE {pk} = :id"),
                {"s": target.value, "id": row_id},
            )


default_cfl_service: CflService = DefaultCflService()
