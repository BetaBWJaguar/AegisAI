from datetime import date
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any

class RuleCreate(BaseModel):
    name: str
    description: str
    type: str
    params: Dict[str, Any]

class WorkspaceCreate(BaseModel):
    name: str
    description: str
    rules: List[RuleCreate] = []

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    birth_date: date
    phone_number: str
    workspaces: List[WorkspaceCreate] = []
