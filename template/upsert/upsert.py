from pydantic import BaseModel
from typing import Optional

class TemplateUpsert(BaseModel):
    name: Optional[str] = None
    pattern: Optional[str] = None
    description: Optional[str] = None
