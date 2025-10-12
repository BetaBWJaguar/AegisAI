from pydantic import BaseModel
from typing import Optional
import uuid


class AuditLogCreate(BaseModel):
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    action: str
    target: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
