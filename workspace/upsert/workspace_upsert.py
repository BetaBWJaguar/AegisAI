import uuid
from pydantic import BaseModel
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
