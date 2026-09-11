"""init db

Revision ID: 0001
Revises: None
Create Date: 2026-09-11 11:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 🟢 檢查現有的資料表
    bind = op.get_bind()
    inspect_obj = reflection.Inspector.from_engine(bind)
    existing_tables = inspect_obj.get_table_names()

    # 🟢 1. 安全建立主表 source
    if "source" not in existing_tables:
        op.create_table(
            "source",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )

    # 🟢 2. 安全建立 evidence 表
    if "evidence" not in existing_tables:
        op.create_table(
            "evidence",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "source_id",
                sa.Integer(),
                sa.ForeignKey("source.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )

    # 🟢 3. 安全建立 event 表（防範有些測試流程是用 event 當表名）
    if "event" not in existing_tables:
        op.create_table(
            "event",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "source_id",
                sa.Integer(),
                sa.ForeignKey("source.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspect_obj = reflection.Inspector.from_engine(bind)
    existing_tables = inspect_obj.get_table_names()

    if "event" in existing_tables:
        op.drop_table("event")
    if "evidence" in existing_tables:
        op.drop_table("evidence")
    if "source" in existing_tables:
        op.drop_table("source")
