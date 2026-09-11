import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# 讀取 Alembic 設定
config = context.config

# 設定日誌
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 這裡我們讓 target_metadata 保持 None，讓 Alembic 改走純 migration 檔案路線
target_metadata = None

def run_migrations_online() -> None:
    """以 online 模式執行遷移，並在開跑前強制清理舊關聯。"""
    db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=db_url
    )

    with connectable.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS event CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS source CASCADE;"))
        connection.commit()

        # 這裡縮成單行，並且逗號後面補上一個空格，完全符合 Ruff/Lint 規範
                context.configure(connection=connection, target_metadata=target_metadata)

                with context.begin_transaction():
                    context.run_migrations()

if context.is_offline_mode():
    # 測試環境通常只跑 online 模式
    pass
else:
    run_migrations_online()
