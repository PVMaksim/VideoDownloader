"""
Alembic env.py — поддерживает async SQLAlchemy (asyncpg)
Использует синхронный URL для миграций (psycopg2)
"""
import sys
import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Добавляем src/ в путь чтобы импортировать модели и конфиг
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import settings
from db.models import Base   # импортируем Base со всеми моделями

# Alembic Config объект — даёт доступ к alembic.ini
config = context.config

# Настраиваем логирование из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для autogenerate — Alembic сравнивает с реальной БД
target_metadata = Base.metadata

# Берём синхронный URL из settings (psycopg2, не asyncpg)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)


def run_migrations_offline() -> None:
    """
    Режим offline — генерирует SQL без подключения к БД.
    Полезно для ревью миграций перед применением.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,        # замечать изменения типов колонок
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Режим online — подключается к БД и применяет миграции.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # не держим соединения открытыми
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
