from pydantic import BaseModel, Field
from typing import Optional


class ContentEvaluateRequest(BaseModel):
    workspace_id: str
    user_id: str
    user_identifier: Optional[str] = None
    message: str
    user_role: Optional[str] = None