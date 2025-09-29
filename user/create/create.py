from datetime import date
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    birth_date: date
    phone_number: str
