from pydantic import BaseModel
from datetime import datetime

class TemplateResponse(BaseModel):
    id: str
    name: str
    pattern: str
    description: str | None
    created_at: datetime
    updated_at: datetime
