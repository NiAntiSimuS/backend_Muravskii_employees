from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError


TextField = Annotated[
    str,
    StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=100),
]
DepartmentStatus = Literal["active", "inactive"]


class StrictModel(BaseModel):
    """Базовая модель: неизвестные поля в JSON считаются ошибкой."""

    model_config = ConfigDict(extra="forbid")


class DepartmentCreate(StrictModel):
    name: TextField = Field(description="Название отдела", examples=["Разработка"])
    manager: TextField = Field(description="Руководитель отдела", examples=["Анна Смирнова"])
    status: DepartmentStatus = Field(default="active", description="Статус отдела")


class DepartmentUpdate(StrictModel):
    name: TextField | None = None
    manager: TextField | None = None
    status: DepartmentStatus | None = None

    @field_validator("name", "manager", "status", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise PydanticCustomError("null_not_allowed", "Поле не может быть null")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise PydanticCustomError("empty_patch", "Передайте хотя бы одно поле для обновления")
        return self


class Department(DepartmentCreate):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: int = Field(gt=0, description="Идентификатор, назначенный сервером")


class DepartmentFilter(StrictModel):
    limit: int = Field(default=10, ge=1, le=100, description="Размер страницы")
    offset: int = Field(default=0, ge=0, description="Количество пропускаемых записей")
    manager: TextField | None = Field(default=None, description="Точное имя руководителя")
    status: DepartmentStatus | None = Field(default=None, description="Фильтр по статусу")


class ErrorResponse(BaseModel):
    error: str
    field: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
