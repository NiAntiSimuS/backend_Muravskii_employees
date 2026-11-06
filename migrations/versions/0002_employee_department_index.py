"""Индекс для GET /api/departments/{id}/employees.

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_employees_department_id", "employees", ["department_id"])


def downgrade() -> None:
    op.drop_index("idx_employees_department_id", table_name="employees")
