"""initial schema: K01–K06 + §2.9 raw-data tables + model_version + CFL guard

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-11

WBS-B1. Tables come from the ORM metadata (single source of truth,
knowledge.db.models); this migration also installs the extensions and the
G01 direct-write guard (ADR-0004 / ADR-0007 §6).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from knowledge.db import models as _models  # noqa: F401  (populate metadata)
from knowledge.db.base import Base

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CFL_GUARD_TABLES = ("company", "relationship", "event", "evidence")

# Explicit B1 table set (scoped per batch; B2+ migrations create their own).
_B1_TABLES = (
    "model_version",
    "company",
    "technology",
    "company_taxonomy",
    "product",
    "relationship",
    "person",
    "event",
    "evidence",
    "market_data",
    "institutional_trading",
    "shareholding",
)

_GUARD_FN = """
CREATE OR REPLACE FUNCTION cpoai_cfl_guard() RETURNS trigger AS $$
BEGIN
    IF NEW.cfl_status IS DISTINCT FROM OLD.cfl_status
       AND coalesce(current_setting('cpoai.cfl_engine', true), 'off') <> 'on' THEN
        RAISE EXCEPTION 'cfl_status may only be changed via G01 (governance.cfl)';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    Base.metadata.create_all(bind=bind, tables=[Base.metadata.tables[t] for t in _B1_TABLES])

    op.execute(_GUARD_FN)
    for tbl in _CFL_GUARD_TABLES:
        op.execute(
            f"CREATE TRIGGER {tbl}_cfl_guard BEFORE UPDATE ON {tbl} "
            f"FOR EACH ROW EXECUTE FUNCTION cpoai_cfl_guard()"
        )


def downgrade() -> None:
    bind = op.get_bind()
    for tbl in _CFL_GUARD_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS {tbl}_cfl_guard ON {tbl}")
    op.execute("DROP FUNCTION IF EXISTS cpoai_cfl_guard()")

    Base.metadata.drop_all(
        bind=bind, tables=[Base.metadata.tables[t] for t in reversed(_B1_TABLES)]
    )

    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
