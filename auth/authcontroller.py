import uuid

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Body
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from config_loader import ConfigLoader
from error.errortypes import ErrorType
from error.expectionhandler import ExpectionHandler
from revokedtokenservice.revoked_token_service import RevokedTokenService
from user.devicemanager.devicemanager import DeviceManager
from user.failedloginattempt import FailedLoginAttempt
from user.userserviceimpl import UserServiceImpl
from utility.emailverificationutility import EmailVerificationUtility
from user.verifymanagement.verifyresponse import VerifyResponse
from user.verifymanagement.verifymanager import  VerifyManager

router = APIRouter()
service = UserServiceImpl("config.json")
verify_manager = VerifyManager(service)
revoked_service = RevokedTokenService("config.json")


config = ConfigLoader("config.json").get_jwt_config()
SECRET_KEY = config["secret_key"]
ALGORITHM = config["algorithm"]
ACCESS_TOKEN_EXPIRE_MINUTES = config["access_token_expire_minutes"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    birth_date: date
    phone_number: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserTokenData(BaseModel):
    user_id: str


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    jti = str(uuid.uuid4())

    to_encode.update({
        "exp": expire,
        "sub": data.get("sub"),
        "jti": jti
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> UserTokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")

        if not user_id or not jti:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        if revoked_service.is_token_revoked(jti):
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return UserTokenData(user_id=user_id)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    token_data = decode_token(token)
    user = service.get_user(token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register")
async def register(req: RegisterRequest, request: Request):
    try:
        if service.get_user_by_email(req.email):
            raise ExpectionHandler(
                message="Email already registered",
                error_type=ErrorType.VALIDATION_ERROR
            )

        new_user = service.register_user(
            username=req.username,
            email=req.email,
            password=hash_password(req.password),
            full_name=req.full_name,
            birth_date=req.birth_date,
            phone_number=req.phone_number,
            email_verified=False
        )

        ip = request.client.host
        user_agent = request.headers.get("User-Agent", "Unknown")
        device_name = DeviceManager.extract_device_name(user_agent)
        DeviceManager.add_or_update_device(str(new_user.id),service, device_name, ip, user_agent,False)

        email_util = EmailVerificationUtility(service)
        token = email_util.create_verification_token(str(new_user.id))
        service.set_verification_token(str(new_user.id), token)
        email_util.send_verification_email(req.email, req.username, str(new_user.id))

        return {
            "success": True,
            "message": "User registered. Verification email sent."
        }

    except ExpectionHandler:
        raise

    except Exception as e:
        raise ExpectionHandler(
            message="An unexpected error occurred during registration.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request):
    user = service.get_user_by_email(req.email)

    ip = request.client.host
    user_agent = request.headers.get("User-Agent", "Unknown")

    if not user:
        raise ExpectionHandler("Invalid credentials", ErrorType.AUTH_ERROR)

    if not verify_password(req.password, user.password):

        failed_log = FailedLoginAttempt(
            timestamp=datetime.utcnow(),
            ip_address=ip,
            user_agent=user_agent,
            reason="Invalid credentials"
        )

        if not hasattr(user, "failed_login_attempts") or user.failed_login_attempts is None:
            user.failed_login_attempts = []

        user.failed_login_attempts.append(failed_log)


        failed_logs = [
            f.to_dict() if hasattr(f, "to_dict") else f
            for f in user.failed_login_attempts
        ]

        service.update_user(
            user_id=str(user.id),
            updates={
                "failed_login_attempts": failed_logs,
                "updated_at": datetime.utcnow()
            }
        )

        raise ExpectionHandler("Invalid credentials", ErrorType.AUTH_ERROR)

    if not user.email_verified:
        raise ExpectionHandler("Email not verified", ErrorType.PERMISSION_DENIED)

    device_name = DeviceManager.extract_device_name(user_agent)
    DeviceManager.add_or_update_device(str(user.id), service, device_name, ip, user_agent, True)

    service.update_user(
        user_id=str(user.id),
        updates={
            "devices": [d.to_dict() for d in user.devices],
            "updated_at": datetime.utcnow()
        }
    )

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token)





@router.post("/verify-email", response_model=VerifyResponse)
async def verify_email(token: str = Query(...)):
    result = verify_manager.verify_email(token)
    return VerifyResponse(**result)

@router.post("/resend-verification-email", response_model=VerifyResponse)
async def resend_verification(email: EmailStr = Body(..., embed=True)):
    result = verify_manager.resend_verification(email)
    return VerifyResponse(**result)

@router.post("/logout")
async def logout(request: Request, token: str = Depends(oauth2_scheme, use_cache=False)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        jti = payload.get("jti")
        exp_ts = payload.get("exp")

        if not user_id:
            raise ExpectionHandler(
                message="Invalid token or user not found.",
                error_type=ErrorType.AUTH_ERROR
            )

        user = service.get_user(user_id)
        if not user:
            raise ExpectionHandler(
                message="User session already invalid or does not exist.",
                error_type=ErrorType.NOT_FOUND
            )

        was_revoked = revoked_service.revoke_token(jti, str(user.id), datetime.utcfromtimestamp(exp_ts))
        if not was_revoked:
            raise ExpectionHandler(
                message="Token already revoked or session already closed.",
                error_type=ErrorType.AUTH_ERROR
            )

        DeviceManager.set_inactive_all(str(user.id), service)

        return {
            "success": True,
            "message": "Logged out successfully."
        }

    except ExpectionHandler:
        raise

    except Exception as e:
        raise ExpectionHandler(
            message="Unexpected error during logout.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



