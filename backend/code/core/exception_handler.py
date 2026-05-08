from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

_STATUS_DEFAULT_CODES = {
    401: "NOT_AUTHENTICATED",
    404: "NOT_FOUND",
}


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    default_code = _STATUS_DEFAULT_CODES.get(exc.status_code, "UNKNOWN_ERROR")
    error_code = getattr(exc, "error_code", default_code)
    request_id = getattr(request.state, "request_id", None)
    content = {"detail": exc.detail, "error_code": error_code}
    if request_id:
        content["request_id"] = request_id
    headers = dict(getattr(exc, "headers", None) or {})
    if request_id:
        headers["X-Request-Id"] = request_id
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=headers or None,
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    content = {
        "detail": "Database temporarily unavailable.",
        "error_code": "MARIADB_CONNECTION_ERROR",
    }
    if request_id:
        content["request_id"] = request_id
    headers = {"X-Request-Id": request_id} if request_id else None
    return JSONResponse(
        status_code=503,
        content=content,
        headers=headers,
    )
