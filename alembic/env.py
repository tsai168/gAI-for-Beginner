import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = None


def run_migrations_online() -> None:
    db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=db_url,
    )
    with connectable.connect() as connection:
        # 🟢 同時強制清理 event、evidence 和 source，徹底粉碎外鍵殘留衝突
        connection.execute(text("DROP TABLE IF EXISTS event CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS evidence CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS source CASCADE;"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    pass
else:
    run_migrations_online()
