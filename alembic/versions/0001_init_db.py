"""init db

Revision ID: 0001
Revises: None
Create Date: 2026-09-11 11:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 🟢 步驟 1：先建立主表 source
    op.create_table(
        "source",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )

    # 🟢 步驟 2：source 建立完成後，才建立帶有外鍵的 event 表
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("source.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )


def downgrade() -> None:
    # 🔴 降級時順序相反：先刪除 event 再刪除 source
    op.drop_table("event")
    op.drop_table("source")
