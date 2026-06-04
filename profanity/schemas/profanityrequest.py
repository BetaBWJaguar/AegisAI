from pydantic import BaseModel, Field
from typing import Optional, List


class DetectRequest(BaseModel):
    text: str
    workspace_id: str
    pipeline: Optional[List[str]] = None
    ip: Optional[str] = Field(None)
    user_agent: Optional[str] = Field(None)
    accept_language: Optional[str] = Field(None)
