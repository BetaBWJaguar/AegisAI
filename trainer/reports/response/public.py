from pydantic import BaseModel
from datetime import datetime


class SimpleReportResponse(BaseModel):
    hardware_cost: float
    storage_cost: float
    token_cost: float
    energy_cost: float
    energy_source: str
    currency: str
    total_cost: float
    generated_at: datetime
