from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("load2ask")


class Load2AskException(Exception):
    """Base exception class for Load2Ask application."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class InvalidFileError(Load2AskException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class UnsupportedFormatError(Load2AskException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, details=details)


class DocumentNotFoundError(Load2AskException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class DatabaseError(Load2AskException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


class VectorStoreError(Load2AskException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


class ConfigurationError(Load2AskException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


async def load2ask_exception_handler(request: Request, exc: Load2AskException):
    logger.error(f"Load2AskException handling request {request.url}: {exc.message} (details: {exc.details})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled Exception handling request {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please check system logs.",
            "details": {"error_type": exc.__class__.__name__, "error_str": str(exc)},
            "path": str(request.url.path),
        },
    )
