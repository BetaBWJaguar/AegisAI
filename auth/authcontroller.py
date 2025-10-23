from fastapi import APIRouter, HTTPException, Depends, Query, Request, Body
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from config_loader import ConfigLoader
from user.devicemanager.devicemanager import DeviceManager
from user.userserviceimpl import UserServiceImpl
from utility.emailverificationutility import EmailVerificationUtility
from user.verifymanagement.verifyresponse import VerifyResponse
from user.verifymanagement.verifymanager import  VerifyManager

router = APIRouter()
service = UserServiceImpl("config.json")
verify_manager = VerifyManager(service)


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
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> UserTokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
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
    if service.get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(req.password)
    new_user = service.register_user(
        username=req.username,
        email=req.email,
        password=hashed_pw,
        full_name=req.full_name,
        birth_date=req.birth_date,
        phone_number=req.phone_number,
        email_verified=False
    )

    ip = request.client.host
    user_agent = request.headers.get("User-Agent", "Unknown")
    device_name = DeviceManager.extract_device_name(user_agent)
    DeviceManager.add_or_update_device(str(new_user.id),service, device_name, ip, user_agent,False)

    try:
        email_util = EmailVerificationUtility(service)
        token = email_util.create_verification_token(str(new_user.id))
        service.set_verification_token(str(new_user.id), token)

        email_util.send_verification_email(
            to_email=req.email,
            username=req.username,
            user_id=str(new_user.id)
        )

        return {
            "message": "User registered successfully. Verification email sent.",
            "user": new_user.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User created but verification email failed: {e}")


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request):
    user = service.get_user_by_email(req.email)

    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not getattr(user, "email_verified", False):
        raise HTTPException(status_code=403, detail="Email not verified.")

    ip = request.client.host
    user_agent = request.headers.get("User-Agent", "Unknown")
    device_name = DeviceManager.extract_device_name(user_agent)

    DeviceManager.add_or_update_device(str(user.id),service, device_name, ip, user_agent,True)
    service.update_user(
        user_id=str(user.id),
        updates={"devices": [d.to_dict() for d in user.devices], "updated_at": datetime.utcnow()}
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
