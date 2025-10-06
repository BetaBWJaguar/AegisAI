from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException

from error.errorcodes import ErrorCode
from error.errortypes import ErrorType
from datetime import datetime


class ExpectionHandler(Exception):
    def __init__(
            self,
            message: str,
            error_type: ErrorType = ErrorType.INTERNAL_SERVER_ERROR,
            detail: str = None,
            context: dict = None
    ):
        self.message = message
        self.error_type = error_type
        self.detail = detail
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.status_code = ErrorCode.get_code(error_type.value)

    def to_dict(self):
        return {
            "success": False,
            "error": {
                "type": self.error_type.value,
                "message": self.message,
                "detail": self.detail,
                "context": self.context,
                "timestamp": self.timestamp
            }
        }


async def expection_handler(request: Request, exc: ExpectionHandler):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_detail = exc.errors()
    return JSONResponse(
        status_code=ErrorCode.VALIDATION_ERROR.value,
        content={
            "success": False,
            "error": {
                "type": ErrorType.VALIDATION_ERROR.value,
                "message": "Validation failed for input data.",
                "detail": error_detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    status = exc.status_code
    error_type = ErrorType.INTERNAL_SERVER_ERROR

    if status == 400:
        error_type = ErrorType.VALIDATION_ERROR
    elif status == 401:
        error_type = ErrorType.AUTH_ERROR
    elif status == 403:
        error_type = ErrorType.PERMISSION_DENIED
    elif status == 404:
        error_type = ErrorType.NOT_FOUND
    elif status == 429:
        error_type = ErrorType.RATE_LIMIT_EXCEEDED

    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "error": {
                "type": error_type.value,
                "message": exc.detail or "An unexpected HTTP error occurred.",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
