import re
from datetime import date
from pydantic import EmailStr

from config_loader import ConfigLoader
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHadnler


class ValidationMixin:

    _blocked_domains_cache = None

    @classmethod
    def _load_blocked_domains(cls) -> list:
        if cls._blocked_domains_cache is not None:
            return cls._blocked_domains_cache

        try:
            loader = ConfigLoader("config.json")
            cls._blocked_domains_cache = loader.get_blocked_domains()
        except Exception as e:
            cls._blocked_domains_cache = []
            raise ExpectionHadnler(
                message="Error loading blocked domains configuration.",
                error_type=ErrorType.INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        return cls._blocked_domains_cache

    @classmethod
    def validate_email(cls, email: EmailStr):
        blocked_domains = cls._load_blocked_domains()
        domain = str(email).split("@")[-1].lower()

        if domain in blocked_domains:
            raise ExpectionHadnler(
                message=f"Email domain '{domain}' is blocked (temporary email detected).",
                error_type=ErrorType.VALIDATION_ERROR
            )

    @staticmethod
    def validate_password(password: str):
        if len(password) < 8:
            raise ExpectionHadnler(
                message="Password must be at least 8 characters long.",
                error_type=ErrorType.VALIDATION_ERROR
            )
        if not re.search(r"[A-Z]", password):
            raise ExpectionHadnler(
                message="Password must contain at least one uppercase letter.",
                error_type=ErrorType.VALIDATION_ERROR
            )
        if not re.search(r"[a-z]", password):
            raise ExpectionHadnler(
                message="Password must contain at least one lowercase letter.",
                error_type=ErrorType.VALIDATION_ERROR
            )
        if not re.search(r"\d", password):
            raise ExpectionHadnler(
                message="Password must contain at least one number.",
                error_type=ErrorType.VALIDATION_ERROR
            )

    @staticmethod
    def validate_username(username: str):
        if len(username) < 3:
            raise ExpectionHadnler(
                message="Username must be at least 3 characters long.",
                error_type=ErrorType.VALIDATION_ERROR
            )
        if not re.match(r"^[A-Za-z0-9_.-]+$", username):
            raise ExpectionHadnler(
                message="Username contains invalid characters. Only letters, numbers, '.', '_' and '-' are allowed.",
                error_type=ErrorType.VALIDATION_ERROR
            )

    @staticmethod
    def validate_birth_date(birth_date: date):
        today = date.today()
        if birth_date > today:
            raise ExpectionHadnler(
                message="Birth date cannot be in the future.",
                error_type=ErrorType.VALIDATION_ERROR
            )
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 13:
            raise ExpectionHadnler(
                message="User must be at least 13 years old.",
                error_type=ErrorType.VALIDATION_ERROR
            )
