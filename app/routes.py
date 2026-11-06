from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Request, Response, status

from .models import (
    Department,
    DepartmentCreate,
    DepartmentFilter,
    DepartmentStats,
    DepartmentUpdate,
    Employee,
    EmployeeCreate,
    ErrorResponse,
    HealthResponse,
)
from .repository import (
    DepartmentRepository,
    DuplicateEmployeeEmailError,
    EmployeeRepository,
)


health_router = APIRouter(tags=["Состояние"])
departments_router = APIRouter(prefix="/api/departments", tags=["Отделы"])
DepartmentId = Annotated[int, Path(gt=0, description="Положительный идентификатор отдела")]
NOT_FOUND = {"error": "Отдел не найден", "field": "id"}


def repository(request: Request) -> DepartmentRepository:
    return request.app.state.departments


def employee_repository(request: Request) -> EmployeeRepository:
    return request.app.state.employees


def require_department(department: Department | None) -> Department:
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return department


@health_router.get("/health", response_model=HealthResponse, summary="Проверка сервиса")
def health() -> HealthResponse:
    return HealthResponse()


@departments_router.post(
    "",
    response_model=Department,
    status_code=status.HTTP_201_CREATED,
    summary="Создать отдел",
    responses={201: {"headers": {"Location": {"schema": {"type": "string"}}}}},
)
def create_department(data: DepartmentCreate, request: Request, response: Response) -> Department:
    department = repository(request).create(data)
    response.headers["Location"] = f"/api/departments/{department.id}"
    return department


@departments_router.get("", response_model=list[Department], summary="Список отделов")
def list_departments(
    request: Request,
    filters: Annotated[DepartmentFilter, Query()],
) -> list[Department]:
    return repository(request).find_all(filters)


@departments_router.get(
    "/stats", response_model=list[DepartmentStats], summary="Статистика по отделам"
)
def departments_stats(request: Request) -> list[DepartmentStats]:
    return repository(request).stats()


@departments_router.post(
    "/{department_id}/employees",
    response_model=Employee,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить сотрудника в отдел",
    responses={
        404: {"model": ErrorResponse, "description": "Отдел не найден"},
        409: {"model": ErrorResponse, "description": "Email сотрудника уже занят"},
    },
)
def create_employee(
    department_id: DepartmentId,
    data: EmployeeCreate,
    request: Request,
) -> Employee:
    try:
        employee = employee_repository(request).create(department_id, data)
    except DuplicateEmployeeEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Email уже используется другим сотрудником", "field": "email"},
        ) from None
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return employee


@departments_router.get(
    "/{department_id}/employees",
    response_model=list[Employee],
    summary="Сотрудники отдела",
    responses={404: {"model": ErrorResponse, "description": "Отдел не найден"}},
)
def list_employees(department_id: DepartmentId, request: Request) -> list[Employee]:
    employees = employee_repository(request).find_all(department_id)
    if employees is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return employees


@departments_router.get(
    "/{department_id}",
    response_model=Department,
    summary="Получить отдел",
    responses={404: {"model": ErrorResponse, "description": "Отдел не найден"}},
)
def get_department(department_id: DepartmentId, request: Request) -> Department:
    return require_department(repository(request).get(department_id))


@departments_router.patch(
    "/{department_id}",
    response_model=Department,
    summary="Изменить поля отдела",
    responses={404: {"model": ErrorResponse, "description": "Отдел не найден"}},
)
def update_department(
    department_id: DepartmentId,
    data: DepartmentUpdate,
    request: Request,
) -> Department:
    return require_department(repository(request).update(department_id, data))


@departments_router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Удалить отдел",
    responses={404: {"model": ErrorResponse, "description": "Отдел не найден"}},
)
def delete_department(department_id: DepartmentId, request: Request) -> Response:
    if not repository(request).delete(department_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
