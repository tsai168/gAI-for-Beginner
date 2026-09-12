"""B8: audit_log table (G03, ADR-0020, CF-45 / Charter §22 Auditability)

Revision ID: 0006_audit_log
Revises: 0005_valuation_event_window
Create Date: 2026-09-12

New table only — same safe pattern as 0004/0005 (ADR-0013 §0 only bites
when an existing table's columns change). Append-only via the
`cpoai_append_only()` trigger function created in migration 0002 — reused
here, not redefined.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from knowledge.db import models as _models  # noqa: F401
from knowledge.db.base import Base

revision: str = "0006_audit_log"
down_revision: str | None = "0005_valuation_event_window"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "audit_log"


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=[Base.metadata.tables[_TABLE]])
    op.execute(
        "CREATE TRIGGER audit_log_append_only "
        "BEFORE UPDATE OR DELETE ON audit_log "
        "FOR EACH ROW EXECUTE FUNCTION cpoai_append_only()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_log_append_only ON audit_log")
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, tables=[Base.metadata.tables[_TABLE]])
