"""B2: source registry (data_source D01–D08 + source) + P03 source_snapshot

Revision ID: 0002_source_registry
Revises: 0001_initial_schema
Create Date: 2026-09-11

Adds the cross-module FKs event.source_id / evidence.source_id -> source
(both ends now exist), an append-only guard on source_snapshot (CF-08 /
GP-15), and seeds the fixed D01–D08 catalogue (earliest_reliable_date stays
NULL until DATA_AVAILABILITY_AUDIT is filled — CF-25).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from knowledge.db import models as _models  # noqa: F401
from knowledge.db.base import Base

revision: str = "0002_source_registry"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_B2_TABLES = ("data_source", "source", "source_snapshot")

_DEFERRED_FKS = (
    ("fk_event_source_id_source", "event", "source", "source_id"),
    ("fk_evidence_source_id_source", "evidence", "source", "source_id"),
)

_APPEND_ONLY_FN = """
CREATE OR REPLACE FUNCTION cpoai_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'table % is append-only (CF-08 / GP-15)', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;
"""


# D01–D08 per Work-1 §3.1. tier: D01=S1 .. D04=S4; D05/D06/D07 none; D08 disabled.
def _row(code: str, name: str, tier: str | None, enabled: bool) -> dict[str, object]:
    return {"source_code": code, "name": name, "source_tier": tier, "is_enabled": enabled}


_SEED = [
    _row("D01", "交易所／主管機關官方揭露 (TWSE/TPEx/MOPS)", "S1", True),
    _row("D02", "公司／交易對手第一手來源 (IR/財報/法說/新聞稿)", "S2", True),
    _row("D03", "技術／機構權威來源 (CPO/SiPh 標準與技術文件)", "S3", True),
    _row("D04", "可信媒體來源 (產業/財經媒體)", "S4", True),
    _row("D05", "市場資料來源 (股價/法人/信用交易)", None, True),
    _row("D06", "TDCC 股權分布來源 (集保千張大戶)", None, True),
    _row("D07", "Taxonomy／生態系參考庫", None, True),
    _row("D08", "授權付費來源 (V1 停用)", None, False),
]


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=[Base.metadata.tables[t] for t in _B2_TABLES])

    for name, table, ref, col in _DEFERRED_FKS:
        op.create_foreign_key(name, table, ref, [col], [col], ondelete="SET NULL")

    op.execute(_APPEND_ONLY_FN)
    op.execute(
        "CREATE TRIGGER source_snapshot_append_only "
        "BEFORE UPDATE OR DELETE ON source_snapshot "
        "FOR EACH ROW EXECUTE FUNCTION cpoai_append_only()"
    )

    seed_tbl = sa.table(
        "data_source",
        sa.column("source_code", sa.Text),
        sa.column("name", sa.Text),
        sa.column("source_tier", sa.Text),
        sa.column("is_enabled", sa.Boolean),
    )
    op.bulk_insert(seed_tbl, _SEED)


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("DROP TRIGGER IF EXISTS source_snapshot_append_only ON source_snapshot")
    op.execute("DROP FUNCTION IF EXISTS cpoai_append_only()")
    for name, table, _ref, _col in _DEFERRED_FKS:
        op.drop_constraint(name, table, type_="foreignkey")
    Base.metadata.drop_all(
        bind=bind, tables=[Base.metadata.tables[t] for t in reversed(_B2_TABLES)]
    )
