from pydantic import BaseModel
from typing import Optional, Dict, Any


class ContentDecisionResponse(BaseModel):
    allowed: bool
    risk: Optional[str] = None
    action: Optional[str] = None
    reason: Optional[str] = None
    score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None