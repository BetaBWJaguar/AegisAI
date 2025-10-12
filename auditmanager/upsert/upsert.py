from pydantic import BaseModel
from typing import Optional
import uuid


class AuditLogUpsert(BaseModel):
    user_id: Optional[uuid.UUID] = None
    workspace_id: Optional[uuid.UUID] = None
    action: Optional[str] = None
    target: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
