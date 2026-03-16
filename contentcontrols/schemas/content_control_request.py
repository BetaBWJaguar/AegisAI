from pydantic import BaseModel, Field
from typing import Optional, List


class ContentEvaluateRequest(BaseModel):
    workspace_id: str
    user_id: str
    user_identifier: Optional[str] = None
    message: str
    user_role: Optional[str] = None


class BatchContentEvaluateRequest(BaseModel):
    workspace_id: str
    user_id: str
    user_identifier: Optional[str] = None
    messages: List[str] = Field(..., min_length=1, max_length=100)
    user_role: Optional[str] = None