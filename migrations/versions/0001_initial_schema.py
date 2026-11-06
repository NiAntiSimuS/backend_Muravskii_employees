"""Создание отделов и сотрудников; совместимо с базой без Alembic из первой части лаб-2.

Revision ID: 0001
Revises:
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # IF NOT EXISTS позволяет проставить версию уже созданной базе, не удаляя данные.
    op.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manager TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'inactive'))
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            position TEXT NOT NULL,
            email TEXT NOT NULL,
            salary REAL NOT NULL CHECK (salary >= 0),
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
        )
    """)


def downgrade() -> None:
    op.drop_table("employees")
    op.drop_table("departments")
