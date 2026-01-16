from dataclasses import dataclass
from typing import Dict


@dataclass
class TrainingConfig:
    training_hours: float
    gpu_hour_price: float
    cpu_hour_price: float = 0.0
    dataset_size_gb: float = 0.0
    storage_price_per_gb: float = 0.0
    tokens_used: int = 0
    token_price_per_million: float = 0.0
    energy_source: str = "EXTERNAL"


class TrainingCostTracker:

    def __init__(self, config: TrainingConfig, currency: str):
        self.config = config
        self.currency = currency

    def hardware_cost(self) -> float:
        return (
                self.config.training_hours * self.config.gpu_hour_price
                + self.config.training_hours * self.config.cpu_hour_price
        )

    def storage_cost(self) -> float:
        return self.config.dataset_size_gb * self.config.storage_price_per_gb

    def token_cost(self) -> float:
        if self.config.tokens_used <= 0:
            return 0.0
        return (
                self.config.tokens_used / 1_000_000
        ) * self.config.token_price_per_million

    def total_cost(self) -> float:
        return round(
            self.hardware_cost()
            + self.storage_cost()
            + self.token_cost(),
            2
        )

    def breakdown(self) -> Dict[str, float | str]:
        return {
            "hardware_cost": round(self.hardware_cost(), 2),
            "storage_cost": round(self.storage_cost(), 2),
            "token_cost": round(self.token_cost(), 2),
            "energy_cost": 0.0,
            "energy_source": self.config.energy_source,
            "currency": self.currency,
            "total_cost": self.total_cost()
        }
