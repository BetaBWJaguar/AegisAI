from pydantic import BaseModel

class TemplateCreate(BaseModel):
    name: str
    pattern: str
    description: str = ""
