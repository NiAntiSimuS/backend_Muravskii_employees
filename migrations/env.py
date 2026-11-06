"""Конфигурация Alembic для SQLite без SQLAlchemy ORM."""

import os

from alembic import context
from sqlalchemy import create_engine

config = context.config


def run_migrations_online() -> None:
    url = config.attributes.get("database_url") or os.environ.get(
        "DATABASE_URL", "sqlite:///./employees.db"
    )
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            # Подключение Alembic тоже должно учитывать внешние ключи SQLite.
            connection.exec_driver_sql("PRAGMA foreign_keys = ON")
            context.configure(connection=connection, target_metadata=None)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations_online()
