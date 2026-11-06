"""Тестовые данные: python -m app.seed (только для пустой базы)."""

from .database import Database


def seed() -> bool:
    database = Database()
    with database.connect() as connection:
        # Блокируем конкурирующую запись, пока проверяем, пуста ли база.
        connection.execute("BEGIN IMMEDIATE")
        count = connection.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
        employees_count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if count or employees_count:
            return False

        development = connection.execute(
            "INSERT INTO departments (name, manager, status) VALUES (?, ?, ?)",
            ("Разработка", "Анна Смирнова", "active"),
        ).lastrowid
        marketing = connection.execute(
            "INSERT INTO departments (name, manager, status) VALUES (?, ?, ?)",
            ("Маркетинг", "Иван Петров", "active"),
        ).lastrowid
        connection.executemany(
            """INSERT INTO employees (department_id, full_name, position, email, salary)
               VALUES (?, ?, ?, ?, ?)""",
            [
                (development, "Иван Иванов", "Разработчик", "ivan@example.com", 90000),
                (development, "Мария Соколова", "Тестировщик", "maria@example.com", 80000),
                (marketing, "Ольга Орлова", "Маркетолог", "olga@example.com", 75000),
            ],
        )
        return True


if __name__ == "__main__":
    print("Добавлены 2 отдела и 3 сотрудника." if seed() else "База не пуста. Данные не изменены.")
