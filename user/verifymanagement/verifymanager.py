from fastapi import HTTPException
from pydantic import EmailStr

from utility.emailverificationutility import EmailVerificationUtility
from user.userserviceimpl import UserServiceImpl

class VerifyManager:
    def __init__(self, service: UserServiceImpl):
        self.service = service
        self.email_util = EmailVerificationUtility(service)

    def verify_email(self, token: str) -> dict:
        try:
            user_id = self.email_util.decode_verification_token(token)

            user = self.service.get_user(user_id)
            if not user:
                return {"status": "error", "message": "User not found"}

            if getattr(user, "email_verified", False):
                return {"status": "ok", "message": "Email already verified"}

            self.service.mark_email_verified(user_id)
            return {"status": "ok", "message": "Email verified successfully"}

        except HTTPException as e:
            return {"status": "error", "message": e.detail}
        except Exception:
            return {"status": "error", "message": "Invalid or expired token"}

    def resend_verification(self, email: EmailStr) -> dict:
        user = self.service.get_user_by_email(email)

        if not user:
            return {"status": "error", "message": "User not found"}

        if getattr(user, "email_verified", False):
            return {"status": "ok", "message": "Email already verified"}

        try:
            token = self.email_util.create_verification_token(str(user.id))
            self.service.set_verification_token(str(user.id), token)

            self.email_util.send_verification_email(
                to_email=user.email,
                username=user.username,
                user_id=str(user.id)
            )
            return {"status": "ok", "message": "Verification email resent."}

        except Exception as e:
            return {"status": "error", "message": f"Failed to resend email: {str(e)}"}
