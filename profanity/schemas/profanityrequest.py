from pydantic import BaseModel
from typing import Optional, List


class DetectRequest(BaseModel):
    text: str
    workspace_id: str
    pipeline: Optional[List[str]] = None
