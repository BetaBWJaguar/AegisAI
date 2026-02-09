from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SimpleReportResponse(BaseModel):
    hardware_cost: float
    storage_cost: float
    token_cost: float
    energy_cost: float
    energy_source: str
    currency: str
    total_cost: float
    gpu_model: Optional[str] = None
    site: Optional[str] = None
    generated_at: datetime
