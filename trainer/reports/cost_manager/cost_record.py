
from dataclasses import dataclass
from typing import Dict, Union, Optional


@dataclass(slots=True)
class TrainingConfig:
    training_hours: float
    gpu_hour_price: float
    cpu_hour_price: float = 0.0
    dataset_size_gb: float = 0.0
    storage_price_per_gb: float = 0.0
    tokens_used: int = 0
    token_price_per_million: float = 0.0
    energy_source: str = "EXTERNAL"
    gpu_model: Optional[str] = None
    site: Optional[str] = None


@dataclass(slots=True)
class CostBreakdown:
    training_hours: float
    gpu_hour_price: float
    cpu_hour_price: float
    dataset_size_gb: float
    storage_price_per_gb: float
    tokens_used: int
    token_price_per_million: float
    hardware_cost: float
    storage_cost: float
    token_cost: float
    energy_cost: float
    energy_source: str
    currency: str
    total_cost: float
    gpu_model: Optional[str] = None
    site: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Union[float, str, None]]) -> 'CostBreakdown':
        return cls(
            training_hours=data.get("training_hours", 0.0),
            gpu_hour_price=data.get("gpu_hour_price", 0.0),
            cpu_hour_price=data.get("cpu_hour_price", 0.0),
            dataset_size_gb=data.get("dataset_size_gb", 0.0),
            storage_price_per_gb=data.get("storage_price_per_gb", 0.0),
            tokens_used=data.get("tokens_used", 0),
            token_price_per_million=data.get("token_price_per_million", 0.0),
            hardware_cost=data.get("hardware_cost", 0.0),
            storage_cost=data.get("storage_cost", 0.0),
            token_cost=data.get("token_cost", 0.0),
            energy_cost=data.get("energy_cost", 0.0),
            energy_source=data.get("energy_source", "EXTERNAL"),
            currency=data.get("currency", "USD"),
            total_cost=data.get("total_cost", 0.0),
            gpu_model=data.get("gpu_model"),
            site=data.get("site"),
        )

    def to_dict(self) -> Dict[str, Union[float, str, None]]:
        return {
            "training_hours": self.training_hours,
            "gpu_hour_price": self.gpu_hour_price,
            "cpu_hour_price": self.cpu_hour_price,
            "dataset_size_gb": self.dataset_size_gb,
            "storage_price_per_gb": self.storage_price_per_gb,
            "tokens_used": self.tokens_used,
            "token_price_per_million": self.token_price_per_million,
            "hardware_cost": self.hardware_cost,
            "storage_cost": self.storage_cost,
            "token_cost": self.token_cost,
            "energy_cost": self.energy_cost,
            "energy_source": self.energy_source,
            "currency": self.currency,
            "total_cost": self.total_cost,
            "gpu_model": self.gpu_model,
            "site": self.site,
        }
