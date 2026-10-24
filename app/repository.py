from threading import RLock

from .models import Department, DepartmentCreate, DepartmentFilter, DepartmentUpdate


class DepartmentRepository:
    """Простое потокобезопасное хранилище отделов в памяти процесса."""

    def __init__(self) -> None:
        self._items: dict[int, Department] = {}
        self._next_id = 1
        self._lock = RLock()

    def create(self, data: DepartmentCreate) -> Department:
        with self._lock:
            department = Department(id=self._next_id, **data.model_dump())
            self._items[department.id] = department
            self._next_id += 1
            return department

    def get(self, department_id: int) -> Department | None:
        with self._lock:
            return self._items.get(department_id)

    def find_all(self, filters: DepartmentFilter) -> list[Department]:
        with self._lock:
            items = sorted(self._items.values(), key=lambda item: item.id)

            if filters.manager is not None:
                items = [item for item in items if item.manager == filters.manager]
            if filters.status is not None:
                items = [item for item in items if item.status == filters.status]

            start = filters.offset
            end = start + filters.limit
            return items[start:end]

    def update(self, department_id: int, changes: DepartmentUpdate) -> Department | None:
        with self._lock:
            current = self._items.get(department_id)
            if current is None:
                return None

            updated = Department.model_validate(
                current.model_dump() | changes.model_dump(exclude_unset=True)
            )
            self._items[department_id] = updated
            return updated

    def delete(self, department_id: int) -> bool:
        with self._lock:
            return self._items.pop(department_id, None) is not None
