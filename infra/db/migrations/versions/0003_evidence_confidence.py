"""B5a: add evidence.confidence / evidence.model_version_id (ADR-0013 §0)

Revision ID: 0003_evidence_confidence
Revises: 0002_source_registry
Create Date: 2026-09-12

Work-2 §2.1 says every entity shares confidence/cfl_status/model_version_id;
B1 missed confidence/model_version_id on `evidence` (it only got cfl_status
via CflStatusMixin). This adds the two missing, nullable columns.

IF [NOT] EXISTS, not op.add_column/op.drop_column: migration 0001 builds its
DDL from `Base.metadata.create_all(tables=_B1_TABLES)`, which reflects the
*current* ORM model, not a frozen historical snapshot — since Evidence now
declares GovernedMixin (this same commit), 0001 already creates these two
columns, and a plain ADD COLUMN here fails with DuplicateColumn (see CI run
2026-09-12). Making 0003 idempotent handles both orderings without touching
0001/0002. See ADR-0013 §0 for the general hazard this exposes.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_evidence_confidence"
down_revision: str | None = "0002_source_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS confidence NUMERIC(5, 4)")
    op.execute("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS model_version_id UUID")


def downgrade() -> None:
    op.execute("ALTER TABLE evidence DROP COLUMN IF EXISTS model_version_id")
    op.execute("ALTER TABLE evidence DROP COLUMN IF EXISTS confidence")
