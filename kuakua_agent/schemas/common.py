from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status: Literal["success"] = "success"
    data: T
    message: str | None = None


class ErrorPayload(BaseModel):
    code: str
    message: str
    trace_id: str | None = None
    retryable: bool = False


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: ErrorPayload

