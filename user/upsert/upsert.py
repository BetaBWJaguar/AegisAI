import uuid
from datetime import date
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional

class RuleUpsert(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    description: str
    type: str
    params: Dict[str, Any]

class WorkspaceUpsert(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    description: str
    rules: List[RuleUpsert] = []

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    status: Optional[str] = None
    workspaces: Optional[List[WorkspaceUpsert]] = None
