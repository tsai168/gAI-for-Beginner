"""B11: research_report table (G-1, ADR-0003 §4 content_ref / ADR-0023)

Revision ID: 0007_research_report
Revises: 0006_audit_log
Create Date: 2026-09-12

New table only — same safe pattern as 0004/0005/0006. CFL-governed
(research_report is now in CFL_GOVERNED_TABLES): attaches the
`research_report_cfl_guard` trigger reusing the existing
`cpoai_cfl_guard()` function from migration 0001 — reused, not redefined.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from knowledge.db import models as _models  # noqa: F401
from knowledge.db.base import Base

revision: str = "0007_research_report"
down_revision: str | None = "0006_audit_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "research_report"


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=[Base.metadata.tables[_TABLE]])
    op.execute(
        "CREATE TRIGGER research_report_cfl_guard BEFORE UPDATE ON research_report "
        "FOR EACH ROW EXECUTE FUNCTION cpoai_cfl_guard()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS research_report_cfl_guard ON research_report")
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, tables=[Base.metadata.tables[_TABLE]])
