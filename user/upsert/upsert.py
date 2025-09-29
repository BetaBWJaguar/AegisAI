from datetime import date
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    status: Optional[str] = None
