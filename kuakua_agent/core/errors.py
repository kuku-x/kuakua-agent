from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    """Normalized application error for API and service layers."""

    code: str
    message: str
    status_code: int = 400
    retryable: bool = False

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
