import uuid
from datetime import date, datetime
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any

class RuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    type: str
    params: Dict[str, Any]

class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    rules: List[RuleResponse] = []
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    full_name: str
    birth_date: date
    phone_number: str
    created_at: datetime
    updated_at: datetime
    status: str
    workspaces: List[WorkspaceResponse] = []
