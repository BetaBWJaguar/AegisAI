import uuid
from datetime import datetime
from pydantic import BaseModel
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
    model_id: str
    model_name: str
    rules: List[RuleResponse] = []
    created_at: datetime
    updated_at: datetime
