from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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
    *,
    request: Request | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorPayload(code=code, message=message, trace_id=trace_id, retryable=retryable)
    )
    response = JSONResponse(status_code=status_code, content=payload.model_dump())
    # 异常 handler 返回的响应绕过 CORS 中间件，必须手动附加 CORS 头
    if request is not None and "origin" in request.headers:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException,
    ) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", None)
        logger.warning(
            "http_exception",
            extra={
                "trace_id": trace_id, "module_name": "api",
                "event": "http_error", "status_code": exc.status_code,
                "error_code": "HTTP_ERROR",
            },
        )
        return _error_response(
            exc.status_code, "HTTP_ERROR",
            exc.detail or "请求处理失败",
            trace_id=trace_id,
            retryable=exc.status_code >= 500,
            request=request,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError,
    ) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", None)
        logger.warning(
            "request_validation_failed",
            extra={
                "trace_id": trace_id, "module_name": "api",
                "event": "validation_error", "error_code": "VALIDATION_ERROR",
            },
        )
        return _error_response(
            422, "VALIDATION_ERROR", str(exc),
            trace_id=trace_id, request=request,
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", None)
        logger.warning(
            "app_error",
            extra={
                "trace_id": trace_id, "module_name": "api",
                "event": "app_error", "error_code": exc.code,
            },
        )
        return _error_response(
            exc.status_code, exc.code, exc.message,
            trace_id=trace_id, retryable=exc.retryable, request=request,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, _exc: Exception,
    ) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", None)
        logger.exception(
            "unhandled_exception",
            extra={
                "trace_id": trace_id, "module_name": "api",
                "event": "internal_error", "error_code": "INTERNAL_ERROR",
            },
        )
        return _error_response(
            500, "INTERNAL_ERROR",
            "服务暂时不可用，请稍后重试",
            trace_id=trace_id, retryable=True, request=request,
        )
