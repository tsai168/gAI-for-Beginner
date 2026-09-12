"""K04 — Relationship repository (WBS-B4b, ADR-0012 §2).

`confirm_relationship` is the CFL-05 gate: the first CANDIDATE -> CONFIRMED
transition of a *named* relationship raises the candidate via G01
(ADR-0004 pattern). See ADR-0012 §2 for the "materiality" simplification.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from governance.cfl import CflId, CflService, default_cfl_service
from knowledge.db.base import CflStatus, RelationshipStatus
from knowledge.db.models import Relationship


def create_relationship(
    session: Session,
    *,
    source_entity_id: uuid.UUID,
    source_entity_type: str,
    target_entity_id: uuid.UUID,
    target_entity_type: str,
    relationship_type: str,
    is_named: bool = False,
) -> Relationship:
    rel = Relationship(
        source_entity_id=source_entity_id,
        source_entity_type=source_entity_type,
        target_entity_id=target_entity_id,
        target_entity_type=target_entity_type,
        relationship_type=relationship_type,
        is_named=is_named,
    )
    session.add(rel)
    session.flush()
    return rel


def get_relationship(session: Session, relationship_id: uuid.UUID) -> Relationship | None:
    return session.get(Relationship, relationship_id)


def confirm_relationship(
    session: Session,
    relationship: Relationship,
    *,
    cfl_service: CflService = default_cfl_service,
) -> CflStatus | None:
    first_confirm = (
        relationship.is_named and relationship.status != RelationshipStatus.CONFIRMED.value
    )
    relationship.status = RelationshipStatus.CONFIRMED.value
    session.flush()
    if not first_confirm:
        return None
    return cfl_service.submit_candidate(
        session,
        table="relationship",
        row_id=relationship.relationship_id,
        cfl_id=CflId.CFL_05,
    )
