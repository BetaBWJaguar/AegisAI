from pydantic import BaseModel
from typing import List, Optional


class ScenarioConfig(BaseModel):
    scenario_name: str
    tags: List[str] = []
    training_hours: Optional[float] = None
    gpu_hour_price: Optional[float] = None
    cpu_hour_price: Optional[float] = None
    dataset_size_gb: Optional[float] = None
    storage_price_per_gb: Optional[float] = None
    tokens_used: Optional[int] = None
    token_price_per_million: Optional[float] = None


class ReportCreate(BaseModel):
    training_hours: float
    gpu_hour_price: float
    cpu_hour_price: float = 0.0
    dataset_size_gb: float = 0.0
    storage_price_per_gb: float = 0.0
    tokens_used: int = 0
    token_price_per_million: float = 0.0
    energy_source: str = "EXTERNAL"
    currency: str = "USD"
    title: str = "AI Training Cost Report"
    gpu_model: Optional[str] = None
    site: Optional[str] = None
    scenarios: List[ScenarioConfig] = []


class ReportConfigUpdate(BaseModel):
    training_hours: Optional[float] = None
    gpu_hour_price: Optional[float] = None
    cpu_hour_price: Optional[float] = None
    dataset_size_gb: Optional[float] = None
    storage_price_per_gb: Optional[float] = None
    tokens_used: Optional[int] = None
    token_price_per_million: Optional[float] = None
    energy_source: Optional[str] = None
    currency: Optional[str] = None
    title: Optional[str] = None
