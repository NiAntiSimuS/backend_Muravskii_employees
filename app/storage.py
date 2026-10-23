from threading import RLock

from .schemas import Department, DepartmentCreate, DepartmentListQuery, DepartmentPatch


class DepartmentStore:
    def __init__(self):
        self._departments: dict[int, Department] = {}
        self._next_id = 1
        self._lock = RLock()

    def create(self, data: DepartmentCreate) -> Department:
        with self._lock:
            department = Department(id=self._next_id, **data.model_dump())
            self._departments[department.id] = department
            self._next_id += 1
            return department

    def get(self, department_id: int) -> Department | None:
        with self._lock:
            return self._departments.get(department_id)

    def list(self, query: DepartmentListQuery) -> list[Department]:
        with self._lock:
            departments = sorted(self._departments.values(), key=lambda item: item.id)

            if query.manager is not None:
                departments = [item for item in departments if item.manager == query.manager]

            if query.status is not None:
                departments = [item for item in departments if item.status == query.status]

            return departments[query.offset : query.offset + query.limit]

    def update(self, department_id: int, data: DepartmentPatch) -> Department | None:
        with self._lock:
            current = self._departments.get(department_id)
            if current is None:
                return None

            updated = Department.model_validate(
                {**current.model_dump(), **data.model_dump(exclude_unset=True)}
            )
            self._departments[department_id] = updated
            return updated

    def delete(self, department_id: int) -> bool:
        with self._lock:
            return self._departments.pop(department_id, None) is not None
