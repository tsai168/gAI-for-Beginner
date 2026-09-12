"""B5d: valuation_event_window table (ADR-0003 G-1, ADR-0016)

Revision ID: 0005_valuation_event_window
Revises: 0004_model_output_tables
Create Date: 2026-09-12

New table only — same safe pattern as 0004 (ADR-0013 §0 only bites when an
existing table's columns change).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from knowledge.db import models as _models  # noqa: F401
from knowledge.db.base import Base

revision: str = "0005_valuation_event_window"
down_revision: str | None = "0004_model_output_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "valuation_event_window"


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=[Base.metadata.tables[_TABLE]])


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, tables=[Base.metadata.tables[_TABLE]])
