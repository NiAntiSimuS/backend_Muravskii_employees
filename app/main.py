import logging
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import Database
from .models import ErrorResponse
from .repository import DepartmentRepository, EmployeeRepository
from .routes import departments_router, health_router

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("departments.requests")

VALIDATION_MESSAGES = {
    "missing": "Обязательное поле отсутствует",
    "string_type": "Ожидается строка",
    "string_too_short": "Строка не должна быть пустой или состоять из пробелов",
    "literal_error": "Недопустимое значение; ожидается active или inactive",
    "extra_forbidden": "Неизвестное поле",
    "int_parsing": "Ожидается целое число",
    "int_type": "Ожидается целое число",
    "json_invalid": "Некорректный JSON",
    "model_attributes_type": "Тело запроса должно быть JSON-объектом",
    "model_type": "Тело запроса должно быть JSON-объектом",
    "null_not_allowed": "Поле не может быть null",
    "empty_patch": "Передайте хотя бы одно поле для обновления",
}


def validation_message(error: dict) -> str:
    error_type = error["type"]
    context = error.get("ctx", {})
    if error_type == "string_too_long":
        return f"Максимальная длина: {context.get('max_length')} символов"
    if error_type == "greater_than":
        return f"Значение должно быть больше {context.get('gt')}"
    if error_type == "greater_than_equal":
        return f"Значение должно быть не меньше {context.get('ge')}"
    if error_type == "less_than_equal":
        return f"Значение должно быть не больше {context.get('le')}"
    return VALIDATION_MESSAGES.get(error_type, "Некорректное значение")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Справочник сотрудников — лабораторная 2",
        version="2.0.0",
        description=(
            "Отделы и сотрудники хранятся в SQLite между перезапусками. "
            "Статусы отделов: active — активный, inactive — неактивный."
        ),
        responses={400: {"model": ErrorResponse, "description": "Ошибка валидации"}},
    )
    database = Database()
    app.state.departments = DepartmentRepository(database)
    app.state.employees = EmployeeRepository(database)
    app.include_router(health_router)
    app.include_router(departments_router)

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            path = request.url.path
            if request.url.query:
                path = f"{path}?{request.url.query}"
            logger.info(
                "%s %s %d %.1fms",
                request.method,
                path,
                status_code,
                (perf_counter() - started) * 1000,
            )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        error = exc.errors()[0]
        location = error.get("loc", ())
        field_parts = [part for part in location if part not in ("body", "query", "path")]
        field = str(field_parts[0]) if field_parts else "body"
        if error["type"] == "json_invalid":
            field = "body"
        return JSONResponse(
            status_code=400,
            content={"error": validation_message(error), "field": field},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if not isinstance(detail, dict) or "error" not in detail:
            detail = {"error": str(detail), "field": "path"}
        return JSONResponse(status_code=exc.status_code, content=detail, headers=exc.headers)

    def custom_openapi():
        if app.openapi_schema is None:
            schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
            for path in schema["paths"].values():
                for operation in path.values():
                    if isinstance(operation, dict):
                        operation.get("responses", {}).pop("422", None)
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


app = create_app()
