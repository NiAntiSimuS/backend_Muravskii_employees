-- Справочная схема. Приложение применяет Alembic-миграции 0001, 0002 и 0003;
-- этот файл не исполняется автоматически.
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    manager TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    position TEXT NOT NULL,
    email TEXT NOT NULL,
    salary REAL NOT NULL CHECK (salary >= 0),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

-- Добавляется миграцией 0002.
CREATE INDEX IF NOT EXISTS idx_employees_department_id
    ON employees (department_id);

-- Добавляется миграцией 0003: глобальная уникальность email (ASCII без регистра).
CREATE UNIQUE INDEX IF NOT EXISTS uq_employees_email_nocase
    ON employees (email COLLATE NOCASE);
