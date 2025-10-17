from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TemplateResponse(BaseModel):
    id: str
    name: str
    pattern: str
    description: Optional[str]
    category: Optional[str]
    version: int
    created_at: datetime
    updated_at: datetime
