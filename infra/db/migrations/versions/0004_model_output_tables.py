"""B5b: seco_score + cmi_score model-output tables (ADR-0003 G-1, ADR-0014)

Revision ID: 0004_model_output_tables
Revises: 0003_evidence_confidence
Create Date: 2026-09-12

New tables only — no existing table's columns change, so this is not
exposed to the "0001/0002 read live metadata" hazard documented in
ADR-0013 §0 (that only bites when a *pre-existing* table gains a column).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from knowledge.db import models as _models  # noqa: F401
from knowledge.db.base import Base

revision: str = "0004_model_output_tables"
down_revision: str | None = "0003_evidence_confidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_B5B_TABLES = ("seco_score", "cmi_score")


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=[Base.metadata.tables[t] for t in _B5B_TABLES])


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(
        bind=bind, tables=[Base.metadata.tables[t] for t in reversed(_B5B_TABLES)]
    )
