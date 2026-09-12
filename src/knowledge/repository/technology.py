"""K02 — Technology / Taxonomy repository (WBS-B4a, ADR-0011 §3).

Bitemporal primitives on top of Work-2 §2.3's single `valid_from`/`valid_to`
row. There is no contract field linking versions of "the same" taxonomy
node (ADR-0011 §3, 待確認) — this module does not invent one.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge.db.models import Technology


def open_technology_version(
    session: Session,
    *,
    category: str,
    valid_from: datetime,
    parent_technology_id: uuid.UUID | None = None,
    taxonomy_version_id: uuid.UUID | None = None,
) -> Technology:
    tech = Technology(
        category=category,
        parent_technology_id=parent_technology_id,
        taxonomy_version_id=taxonomy_version_id,
        valid_from=valid_from,
    )
    session.add(tech)
    session.flush()
    return tech


def close_technology_version(
    session: Session, technology: Technology, *, valid_to: datetime
) -> None:
    """Marks a row no longer current. Only `valid_to` changes — every other
    field on the row is left exactly as it was (history is not overwritten)."""
    technology.valid_to = valid_to
    session.flush()


def get_technology(session: Session, technology_id: uuid.UUID) -> Technology | None:
    return session.get(Technology, technology_id)


def current_technology_versions(
    session: Session, *, category: str | None = None
) -> list[Technology]:
    stmt = select(Technology).where(Technology.valid_to.is_(None))
    if category is not None:
        stmt = stmt.where(Technology.category == category)
    return list(session.execute(stmt).scalars())
