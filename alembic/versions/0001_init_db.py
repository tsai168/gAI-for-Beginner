"""init db

Revision ID: 0001
Revises: None
Create Date: 2026-09-11 11:00:00.000000

"""
from alembic import context
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 💡 關鍵：先建立 source 資料表
    sa.DataFrame = context.get_bind()
    
    # 檢查 source 表是否存在，若不存在才建立
    context.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS source (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # 💡 關鍵：source 建立完後，才建立 event 資料表，這樣外鍵才找得到 reference
    context.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS event (
            id SERIAL PRIMARY KEY,
            source_id INTEGER REFERENCES source(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))


def downgrade() -> None:
    # 刪除時順序相反，先刪除有外鍵的 event
    context.execute(sa.text("DROP TABLE IF EXISTS event CASCADE;"))
    context.execute(sa.text("DROP TABLE IF EXISTS source CASCADE;"))
