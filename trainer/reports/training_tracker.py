from dataclasses import dataclass
from typing import Dict, Union


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


class TrainingCostTracker:
    __slots__ = ("config", "currency")

    def __init__(self, config: TrainingConfig, currency: str):
        self.config = config
        self.currency = currency

    def hardware_cost(self) -> float:
        hours = self.config.training_hours
        return hours * (
                self.config.gpu_hour_price + self.config.cpu_hour_price
        )

    def storage_cost(self) -> float:
        return self.config.dataset_size_gb * self.config.storage_price_per_gb

    def token_cost(self) -> float:
        if not self.config.tokens_used:
            return 0.0
        return (
                self.config.tokens_used * self.config.token_price_per_million
        ) / 1_000_000

    def energy_cost(self) -> float:
        return 0.0


    def total_cost(self) -> float:
        return round(
            self.hardware_cost()
            + self.storage_cost()
            + self.token_cost()
            + self.energy_cost(),
            2
        )

    def breakdown(self) -> Dict[str, Union[float, str]]:
        return {
            "hardware_cost": round(self.hardware_cost(), 2),
            "storage_cost": round(self.storage_cost(), 2),
            "token_cost": round(self.token_cost(), 2),
            "energy_cost": round(self.energy_cost(), 2),
            "energy_source": self.config.energy_source,
            "currency": self.currency,
            "total_cost": self.total_cost(),
        }
