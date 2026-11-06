"""CRUD отделов и сотрудников в SQLite. Все значения в SQL параметризованы."""

import sqlite3

from .database import Database
from .models import (
    Department,
    DepartmentCreate,
    DepartmentFilter,
    DepartmentStats,
    DepartmentUpdate,
    Employee,
    EmployeeCreate,
)


class DuplicateEmployeeEmailError(Exception):
    """Email уже занят другим сотрудником (бизнес-правило)."""


class DepartmentRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, data: DepartmentCreate) -> Department:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO departments (name, manager, status) VALUES (?, ?, ?)",
                (data.name, data.manager, data.status),
            )
            row = connection.execute(
                "SELECT id, name, manager, status FROM departments WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
            return Department.model_validate(dict(row))

    def get(self, department_id: int) -> Department | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, name, manager, status FROM departments WHERE id = ?",
                (department_id,),
            ).fetchone()
            return Department.model_validate(dict(row)) if row is not None else None

    def find_all(self, filters: DepartmentFilter) -> list[Department]:
        query = "SELECT id, name, manager, status FROM departments WHERE 1 = 1"
        params: list[str | int] = []
        if filters.manager is not None:
            query += " AND manager = ?"
            params.append(filters.manager)
        if filters.q is not None:
            query += " AND instr(unicode_casefold(name), unicode_casefold(?)) > 0"
            params.append(filters.q)
        if filters.status is not None:
            query += " AND status = ?"
            params.append(filters.status)
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params.extend((filters.limit, filters.offset))
        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
            return [Department.model_validate(dict(row)) for row in rows]

    def stats(self) -> list[DepartmentStats]:
        """SQL считает сотрудников и зарплаты, включая отделы без сотрудников."""
        with self.database.connect() as connection:
            rows = connection.execute(
                """SELECT
                       d.id AS department_id,
                       d.name AS department_name,
                       COUNT(e.id) AS employee_count,
                       COALESCE(SUM(e.salary), 0) AS total_salary,
                       COALESCE(AVG(e.salary), 0) AS avg_salary
                   FROM departments AS d
                   LEFT JOIN employees AS e ON e.department_id = d.id
                   GROUP BY d.id, d.name
                   ORDER BY d.id"""
            ).fetchall()
            return [DepartmentStats.model_validate(dict(row)) for row in rows]

    def update(self, department_id: int, changes: DepartmentUpdate) -> Department | None:
        values = changes.model_dump(exclude_unset=True)
        # Имена столбцов выбираются только из зафиксированного белого списка.
        columns = [name for name in ("name", "manager", "status") if name in values]
        assignments = ", ".join(f"{column} = ?" for column in columns)
        params = [values[column] for column in columns]
        with self.database.connect() as connection:
            cursor = connection.execute(
                f"UPDATE departments SET {assignments} WHERE id = ?",
                (*params, department_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT id, name, manager, status FROM departments WHERE id = ?",
                (department_id,),
            ).fetchone()
            return Department.model_validate(dict(row))

    def delete(self, department_id: int) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM departments WHERE id = ?", (department_id,)
            )
            return cursor.rowcount > 0


class EmployeeRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, department_id: int, data: EmployeeCreate) -> Employee | None:
        with self.database.connect() as connection:
            # BEGIN IMMEDIATE блокирует параллельные записи: проверка уникальности
            # и INSERT происходят внутри одной транзакции, без race condition.
            connection.execute("BEGIN IMMEDIATE")
            parent = connection.execute(
                "SELECT 1 FROM departments WHERE id = ?", (department_id,)
            ).fetchone()
            if parent is None:
                return None

            # Email должен быть уникальным во всей компании, без учёта регистра.
            # COLLATE NOCASE корректен для обычных ASCII email-адресов.
            duplicate = connection.execute(
                "SELECT 1 FROM employees WHERE email COLLATE NOCASE = ? LIMIT 1",
                (data.email,),
            ).fetchone()
            if duplicate is not None:
                raise DuplicateEmployeeEmailError()

            try:
                cursor = connection.execute(
                    """INSERT INTO employees
                       (department_id, full_name, position, email, salary)
                       VALUES (?, ?, ?, ?, ?)""",
                    (department_id, data.full_name, data.position, data.email, data.salary),
                )
            except sqlite3.IntegrityError as error:
                # Уникальный индекс в БД — дополнительная защита при прямых SQL-записях.
                if "UNIQUE constraint failed: employees.email" in str(error):
                    raise DuplicateEmployeeEmailError() from error
                raise

            row = connection.execute(
                """SELECT id, department_id, full_name, position, email, salary
                   FROM employees WHERE id = ?""",
                (cursor.lastrowid,),
            ).fetchone()
            return Employee.model_validate(dict(row))

    def find_all(self, department_id: int) -> list[Employee] | None:
        with self.database.connect() as connection:
            parent = connection.execute(
                "SELECT 1 FROM departments WHERE id = ?", (department_id,)
            ).fetchone()
            if parent is None:
                return None
            rows = connection.execute(
                """SELECT id, department_id, full_name, position, email, salary
                   FROM employees WHERE department_id = ? ORDER BY id""",
                (department_id,),
            ).fetchall()
            return [Employee.model_validate(dict(row)) for row in rows]
