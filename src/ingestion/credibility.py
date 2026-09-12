"""P05 — Source credibility scorer (WBS-B3b, ADR-0010 §4, CF-07).

Deterministic (L0): resolves the S1–S5 tier for an evidence's source from
the fixed D01–D08 catalogue and raises the CFL-03 candidate via G01
(ADR-0004 pattern — this module computes/raises, G01 decides; the B1 stub
leaves it PENDING, B8 supplies the real AUTO-PASS/REVIEW-REQUIRED rule).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from governance.cfl import CflId, CflService, default_cfl_service
from knowledge.db.base import CflStatus
from knowledge.db.models import DataSource, Evidence, Source


class UnknownSourceTierError(LookupError):
    """`source.data_source_code` doesn't match any `data_source` row.
    Defensive only: `source.data_source_code` carries a FK to `data_source`
    (ADR-0008), so this should not be reachable with valid data — CFL-03
    still requires Review for new/unknown sources (Charter §17), never a
    silent guess."""


def resolve_source_tier(session: Session, source_id: uuid.UUID) -> str | None:
    """`source -> data_source.source_tier`. None for D05/D06/D07, which
    have no fixed tier in the seed (ADR-0008) — that is not an error."""
    source = session.get(Source, source_id)
    if source is None:
        raise LookupError(f"source {source_id} not found")
    data_source = session.get(DataSource, source.data_source_code)
    if data_source is None:
        raise UnknownSourceTierError(source.data_source_code)
    return data_source.source_tier


def score_evidence_credibility(
    session: Session,
    evidence: Evidence,
    *,
    cfl_service: CflService = default_cfl_service,
) -> CflStatus:
    """Sets `evidence.source_credibility_tier` (left None if the evidence
    has no source_id, or its source's data_source carries no fixed tier)
    and raises the CFL-03 candidate. Returns the resulting cfl_status —
    PENDING under the B1 G01 stub."""
    if evidence.source_id is not None:
        evidence.source_credibility_tier = resolve_source_tier(session, evidence.source_id)
    session.flush()
    return cfl_service.submit_candidate(
        session, table="evidence", row_id=evidence.evidence_id, cfl_id=CflId.CFL_03
    )
