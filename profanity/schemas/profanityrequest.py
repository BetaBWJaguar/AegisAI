from pydantic import BaseModel, Field
from typing import Dict, Optional, List


class DetectRequest(BaseModel):
    text: str
    workspace_id: str
    pipeline: Optional[List[str]] = None
    ip: Optional[str] = Field(None)
    user_agent: Optional[str] = Field(None)
    accept_language: Optional[str] = Field(None)
    base_durations: Optional[Dict[str, int]] = Field(None)
    category_multipliers: Optional[Dict[str, float]] = Field(None)
