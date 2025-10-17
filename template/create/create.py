from pydantic import BaseModel
from typing import Optional

class TemplateCreate(BaseModel):
    name: str
    pattern: str
    description: Optional[str] = ""
    category: Optional[str] = None
    version: int = 1
