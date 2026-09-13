"""index/CHECK constraint audit (ADR-0025 §2): cfl_status/query-filter
indexes + score/confidence range backstops

Revision ID: 0008_index_constraint_audit
Revises: 0007_research_report
Create Date: 2026-09-12

All of these are now also declared directly on the ORM models (models.py
__table_args__, via the same `_range_check` helper this file mirrors), so
any *fresh* database applying 0001-0007 already gets them via those
migrations' own `Base.metadata.create_all()` calls (live metadata, same
mechanism ADR-0013 §0 documents) — this migration exists for the *other*
case: a database that already ran the old (pre-ADR-0025) 0001-0007 and is
upgrading incrementally, where these objects genuinely don't exist yet.
Every statement is written to be a safe no-op either way: `CREATE INDEX IF
NOT EXISTS` for indexes, a `duplicate_object`-catching DO block for CHECK
constraints (Postgres has no `ADD CONSTRAINT IF NOT EXISTS`). Verified via
the full `alembic upgrade head --sql` render that the generated names
below match exactly what 0001-0007 already produce.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0008_index_constraint_audit"
down_revision: str | None = "0007_research_report"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, index_name, column)
_INDEXES: tuple[tuple[str, str, str], ...] = (
    ("company", "ix_company_universe", "universe"),
    ("company", "ix_company_company_name", "company_name"),
    ("company", "ix_company_cfl_status", "cfl_status"),
    ("relationship", "ix_relationship_cfl_status", "cfl_status"),
    ("event", "ix_event_pipeline_status", "pipeline_status"),
    ("event", "ix_event_cfl_status", "cfl_status"),
    ("event", "ix_event_entity_id", "entity_id"),
    ("evidence", "ix_evidence_cfl_status", "cfl_status"),
    ("research_report", "ix_research_report_cfl_status", "cfl_status"),
)

# (table, column, lo, hi, nullable) — mirrors knowledge.db.models._range_check.
_RANGE_CHECKS: tuple[tuple[str, str, int, int, bool], ...] = (
    ("company", "confidence", 0, 1, True),
    ("relationship", "confidence", 0, 1, True),
    ("event", "confidence", 0, 1, True),
    ("event", "materiality_score", 0, 100, True),
    ("evidence", "confidence", 0, 1, True),
    ("evidence", "authority", 0, 1, True),
    ("evidence", "directness", 0, 1, True),
    ("evidence", "time", 0, 1, True),
    ("evidence", "specificity", 0, 1, True),
    ("evidence", "independence", 0, 1, True),
    ("research_report", "confidence", 0, 1, True),
    ("seco_score", "score", 0, 100, False),
    ("seco_score", "tech_relevance", 0, 100, False),
    ("seco_score", "product_readiness", 0, 100, False),
    ("seco_score", "customer_validation", 0, 100, False),
    ("seco_score", "ecosystem_position", 0, 100, False),
    ("seco_score", "commercialization", 0, 100, False),
    ("seco_score", "strategic_defensibility", 0, 100, False),
    ("seco_score", "confidence", 0, 1, False),
    ("cmi_score", "score", 0, 100, False),
    ("cmi_score", "foreign_inst_momentum", 0, 100, False),
    ("cmi_score", "domestic_inst_momentum", 0, 100, False),
    ("cmi_score", "margin_short", 0, 100, False),
    ("cmi_score", "ownership_concentration", 0, 100, False),
    ("cmi_score", "trading_structure", 0, 100, False),
)


def _constraint_name(table: str, column: str) -> str:
    return f"ck_{table}_{column}_range"


def _condition(column: str, lo: int, hi: int, *, nullable: bool) -> str:
    col = f'"{column}"' if column == "time" else column
    bounds = f"{col} >= {lo} AND {col} <= {hi}"
    return f"{col} IS NULL OR ({bounds})" if nullable else bounds


def upgrade() -> None:
    for table, name, column in _INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})")
    for table, column, lo, hi, nullable in _RANGE_CHECKS:
        name = _constraint_name(table, column)
        condition = _condition(column, lo, hi, nullable=nullable)
        op.execute(
            f"DO $$ BEGIN "
            f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({condition}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
        )


def downgrade() -> None:
    for table, column, _lo, _hi, _nullable in reversed(_RANGE_CHECKS):
        name = _constraint_name(table, column)
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}")
    for _table, name, _column in reversed(_INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {name}")
