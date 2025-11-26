from pydantic import BaseModel
from typing import List, Dict, Any

from user.ruletype import RuleType


class RuleCreate(BaseModel):
    name: str
    description: str
    type: RuleType
    params: Dict[str, Any]

class WorkspaceCreate(BaseModel):
    name: str
    description: str
    model_name: str
    model_version: str
    rules: List[RuleCreate] = []
