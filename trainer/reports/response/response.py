from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class ScenarioResultResponse(BaseModel):
    scenario: str
    total_cost: float


class TrainingCostBreakdownResponse(BaseModel):
    hardware_cost: float
    storage_cost: float
    token_cost: float
    energy_cost: float
    energy_source: str
    currency: str
    total_cost: float
    gpu_model: Optional[str] = None
    site: Optional[str] = None


class ScenarioIntelligenceResponse(BaseModel):
    summary: str
    best_scenario: Optional[str] = None
    worst_scenario: Optional[str] = None
    dominant_cost_component: Optional[str] = None
    scenario_insights: List[str] = []


class ReportConfigResponse(BaseModel):
    training_hours: float
    gpu_hour_price: float
    cpu_hour_price: float
    dataset_size_gb: float
    storage_price_per_gb: float
    tokens_used: int
    token_price_per_million: float
    energy_source: str
    currency: str
    title: str


class ReportResponse(BaseModel):
    breakdown: TrainingCostBreakdownResponse
    scenarios: List[ScenarioResultResponse] = []
    intelligence: Optional[ScenarioIntelligenceResponse] = None
    generated_at: datetime


class ReportGenerationResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None
