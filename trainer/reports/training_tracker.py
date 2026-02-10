from typing import Dict, Union

from trainer.reports.cost_manager.cost_record import TrainingConfig
from trainer.reports.cost_manager.cost_manager import CostManager
from trainer.reports.trainingvalidation import TrainingConfigValidator


class TrainingCostTracker(CostManager):
    __slots__ = ("config", "currency")

    def __init__(self, config: TrainingConfig, currency: str):
        super().__init__(config, currency)
        TrainingConfigValidator.validate(config)
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
        if self.config.tokens_used <= 0:
            return 0.0

        return (self.config.tokens_used / 1_000_000) * self.config.token_price_per_million

    def energy_cost(self) -> float:
        return 0.0

    def total_cost(self) -> float:
        return round(sum((
            self.hardware_cost(),
            self.storage_cost(),
            self.token_cost(),
            self.energy_cost()
        )), 2)

    def breakdown(self) -> Dict[str, Union[float, str, None]]:
        return {
            "training_hours": self.config.training_hours,
            "gpu_hour_price": self.config.gpu_hour_price,
            "cpu_hour_price": self.config.cpu_hour_price,
            "dataset_size_gb": self.config.dataset_size_gb,
            "storage_price_per_gb": self.config.storage_price_per_gb,
            "tokens_used": self.config.tokens_used,
            "token_price_per_million": self.config.token_price_per_million,
            "hardware_cost": round(self.hardware_cost(), 2),
            "storage_cost": round(self.storage_cost(), 2),
            "token_cost": round(self.token_cost(), 2),
            "energy_cost": round(self.energy_cost(), 2),
            "energy_source": self.config.energy_source,
            "currency": self.currency,
            "total_cost": self.total_cost(),
            "gpu_model": self.config.gpu_model,
            "site": self.config.site,
        }
