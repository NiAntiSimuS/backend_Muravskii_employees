"""Гарантия уникального email сотрудников (без учёта регистра ASCII).

Revision ID: 0003
Revises: 0002
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Данные предыдущих этапов сохраняются. Если уже есть одинаковые email,
    # их следует исправить перед применением этой миграции.
    op.execute(
        "CREATE UNIQUE INDEX uq_employees_email_nocase "
        "ON employees (email COLLATE NOCASE)"
    )


def downgrade() -> None:
    op.drop_index("uq_employees_email_nocase", table_name="employees")
