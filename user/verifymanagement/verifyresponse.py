from pydantic import BaseModel

class VerifyResponse(BaseModel):
    status: str
    message: str
