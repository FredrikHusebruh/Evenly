import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app")


class AppError(Exception):
    status_code = 500
    public_message = "Something went wrong."

    def __init__(self, public_message: str | None = None) -> None:
        if public_message:
            self.public_message = public_message
        super().__init__(self.public_message)


class UnauthorizedError(AppError):
    status_code = 401
    public_message = "Authentication required."


class ForbiddenError(AppError):
    status_code = 403
    public_message = "You don't have permission to do that."


class NotFoundError(AppError):
    status_code = 404
    public_message = "Not found."


class ValidationError(AppError):
    status_code = 400
    public_message = "Invalid request."


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.exception("Unhandled AppError on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.public_message})


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong."})
