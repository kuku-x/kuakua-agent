from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from kuakua_agent.core.errors import AppError
from kuakua_agent.core.logging import get_logger
from kuakua_agent.schemas.common import ErrorPayload, ErrorResponse

logger = get_logger(__name__)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    trace_id: str | None = None,
    retryable: bool = False,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorPayload(code=code, message=message, trace_id=trace_id, retryable=retryable)
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", None)
        logger.warning(
            "request_validation_failed",
            extra={
                "trace_id": trace_id,
                "module_name": "api",
                "event": "validation_error",
                "error_code": "VALIDATION_ERROR",
            },
        )
        return _error_response(422, "VALIDATION_ERROR", str(exc), trace_id=trace_id)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", None)
        logger.warning(
            "app_error",
            extra={
                "trace_id": trace_id,
                "module_name": "api",
                "event": "app_error",
                "error_code": exc.code,
            },
        )
        return _error_response(
            exc.status_code,
            exc.code,
            exc.message,
            trace_id=trace_id,
            retryable=exc.retryable,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", None)
        logger.exception(
            "unhandled_exception",
            extra={
                "trace_id": trace_id,
                "module_name": "api",
                "event": "internal_error",
                "error_code": "INTERNAL_ERROR",
            },
        )
        return _error_response(
            500,
            "INTERNAL_ERROR",
            "服务暂时不可用，请稍后重试",
            trace_id=trace_id,
            retryable=True,
        )

