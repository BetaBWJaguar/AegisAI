from enum import Enum

class ErrorCode(Enum):
    VALIDATION_ERROR = 400
    AUTH_ERROR = 401
    PERMISSION_DENIED = 403
    NOT_FOUND = 404
    DATABASE_ERROR = 500
    EXTERNAL_SERVICE_ERROR = 502
    INTERNAL_SERVER_ERROR = 500
    RATE_LIMIT_EXCEEDED = 429

    @classmethod
    def get_code(cls, error_type: str) -> int:
        try:
            return cls[error_type].value
        except KeyError:
            return 500
