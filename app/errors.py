"""Application-level error type and JSON representation.

Every business-rule violation raises AppError, which is rendered as
{"detail": <string>, "code": <CODE>} with the appropriate HTTP status.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def _init_(self, status_code: int, code: str, detail: str) -> None:
        super()._init_(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail


async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.code,
        },
    )
