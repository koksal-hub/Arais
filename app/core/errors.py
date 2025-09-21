from __future__ import annotations

from http import HTTPStatus

from fastapi import HTTPException


class AppException(Exception):
    """Uygulama genelindeki hatalar için temel sınıf."""

    def __init__(self, message: str, *, status_code: int = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def to_http(self) -> HTTPException:
        return HTTPException(status_code=self.status_code, detail=self.message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Kaynak bulunamadı"):
        super().__init__(message, status_code=HTTPStatus.NOT_FOUND)


class RateLimitError(AppException):
    def __init__(self, message: str = "Kota sınırına ulaşıldı, lütfen tekrar deneyin"):
        super().__init__(message, status_code=HTTPStatus.TOO_MANY_REQUESTS)


__all__ = ["AppException", "NotFoundError", "RateLimitError"]
