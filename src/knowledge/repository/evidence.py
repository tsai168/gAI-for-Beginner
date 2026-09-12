"""K06 — Evidence repository (WBS-B4b, ADR-0012 §4).

`record_contradiction` is the CFL-07 gate: CONTRADICT evidence must never
auto-pass (Charter §17 CFL-07; enforced in `governance.cfl.NO_AUTO_PASS`
from B1 onward).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from governance.cfl import CflId, CflService, default_cfl_service
from knowledge.db.base import CflStatus
from knowledge.db.models import Evidence


def create_evidence(
    session: Session, *, evidence_type: str, content_hash: str, retrieved_at: Any, **fields: Any
) -> Evidence:
    evidence = Evidence(
        evidence_type=evidence_type,
        content_hash=content_hash,
        retrieved_at=retrieved_at,
        **fields,
    )
    session.add(evidence)
    session.flush()
    return evidence


def get_evidence(session: Session, evidence_id: uuid.UUID) -> Evidence | None:
    return session.get(Evidence, evidence_id)


def record_contradiction(
    session: Session,
    evidence: Evidence,
    *,
    cfl_service: CflService = default_cfl_service,
) -> CflStatus:
    if evidence.evidence_type != "CONTRADICT":
        raise ValueError("record_contradiction requires evidence_type == 'CONTRADICT'")
    return cfl_service.submit_candidate(
        session, table="evidence", row_id=evidence.evidence_id, cfl_id=CflId.CFL_07
    )
