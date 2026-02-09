from pydantic import BaseModel, Field, validator
from typing import Optional


class SimpleReportCreate(BaseModel):
    training_hours: float = Field(..., gt=0, le=1000, description="Training duration in hours, max 1000 hours")
    gpu_hour_price: float = Field(..., gt=0, le=10.0, description="GPU hourly price, max $10/hour")
    cpu_hour_price: float = Field(default=0.0, ge=0, le=5.0, description="CPU hourly price, max $5/hour")
    dataset_size_gb: float = Field(default=0.0, ge=0, le=10000, description="Dataset size in GB, max 10TB")
    storage_price_per_gb: float = Field(default=0.0, ge=0, le=1.0, description="Storage price per GB, max $1/GB")
    tokens_used: int = Field(default=0, ge=0, le=1000000000, description="Number of tokens used, max 1B")
    token_price_per_million: float = Field(default=0.0, ge=0, le=100.0, description="Token price per million, max $100")
    energy_source: str = Field(default="EXTERNAL", description="Energy source (EXTERNAL, RENEWABLE, GRID)")
    currency: str = Field(default="USD", description="Currency (USD, EUR, TRY)")
    gpu_model: Optional[str] = Field(default=None, description="GPU model used for training (e.g., NVIDIA A100, RTX 4090)")
    site: Optional[str] = Field(default=None, description="Site or platform where the report was generated from")

    @validator('energy_source')
    def validate_energy_source(cls, v):
        valid_sources = ['EXTERNAL', 'RENEWABLE', 'GRID']
        if v not in valid_sources:
            raise ValueError(f'Energy source must be one of: {valid_sources}')
        return v

    @validator('currency')
    def validate_currency(cls, v):
        valid_currencies = ['USD', 'EUR', 'TRY']
        if v not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v
