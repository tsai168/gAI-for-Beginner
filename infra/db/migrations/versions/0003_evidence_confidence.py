"""B5a: add evidence.confidence / evidence.model_version_id (ADR-0013 §0)

Revision ID: 0003_evidence_confidence
Revises: 0002_source_registry
Create Date: 2026-09-12

Work-2 §2.1 says every entity shares confidence/cfl_status/model_version_id;
B1 missed confidence/model_version_id on `evidence` (it only got cfl_status
via CflStatusMixin). This adds the two missing, nullable columns without
touching any other migration.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003_evidence_confidence"
down_revision: str | None = "0002_source_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evidence", sa.Column("confidence", sa.Numeric(5, 4), nullable=True))
    op.add_column("evidence", sa.Column("model_version_id", UUID(as_uuid=True), nullable=True))


def downgrade() -> None:
    op.drop_column("evidence", "model_version_id")
    op.drop_column("evidence", "confidence")
