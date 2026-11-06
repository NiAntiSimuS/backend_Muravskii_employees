"""SQLite-подключения и применение версионированных миграций Alembic."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config


class Database:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or os.environ.get("DATABASE_URL", "sqlite:///./employees.db")
        prefix = "sqlite:///"
        if not self.url.startswith(prefix):
            raise ValueError("DATABASE_URL должен начинаться с sqlite:///")
        path = self.url[len(prefix):]
        if not path or path == ":memory:":
            raise ValueError("DATABASE_URL должен указывать на файл SQLite")
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        # Встроенный NOCASE в SQLite не умеет сравнивать русский текст без учёта регистра.
        # Пользовательская функция вызывается в SQL, поэтому фильтрацию делает БД.
        connection.create_function(
            "unicode_casefold", 1,
            lambda value: value.casefold() if isinstance(value, str) else value,
            deterministic=True,
        )
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def init_schema(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        configuration = Config(str(project_root / "alembic.ini"))
        configuration.set_main_option("script_location", str(project_root / "migrations"))
        configuration.attributes["database_url"] = self.url
        # Подходит и для новой БД, и для БД предыдущего этапа без alembic_version.
        command.upgrade(configuration, "head")
