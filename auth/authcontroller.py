from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from config_loader import ConfigLoader
from user.userserviceimpl import UserServiceImpl
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
service = UserServiceImpl("config.json")


config = ConfigLoader("config.json").get_jwt_config()
SECRET_KEY = config["secret_key"]
ALGORITHM = config["algorithm"]
ACCESS_TOKEN_EXPIRE_MINUTES = config["access_token_expire_minutes"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    birth_date: date
    phone_number: str

class LoginRequest(BaseModel):
    email: str
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
async def register(req: RegisterRequest):
    if service.get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(req.password)
    new_user = service.register_user(
        username=req.username,
        email=req.email,
        password=hashed_pw,
        full_name=req.full_name,
        birth_date=req.birth_date,
        phone_number=req.phone_number
    )
    return {"message": "User registered successfully", "user": new_user.to_dict()}

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = service.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.id})
    return TokenResponse(access_token=token)
