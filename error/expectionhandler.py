from datetime import datetime

from error.errorcodes import ErrorCode
from error.errortypes import ErrorType


class ExpectionHadnler(Exception):

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
