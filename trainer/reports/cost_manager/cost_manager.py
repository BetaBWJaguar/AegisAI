from typing import Dict, Any, List, Union, Optional

from trainer.reports.cost_manager.cost_record import TrainingConfig, CostBreakdown


class CostManager:

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

    def calculate_scenario_cost(
        self,
        base_config: Dict[str, Any],
        scenario_overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged_config = {**base_config, **scenario_overrides}

        config = TrainingConfig(
            training_hours=merged_config.get("training_hours", 0.0),
            gpu_hour_price=merged_config.get("gpu_hour_price", 0.0),
            cpu_hour_price=merged_config.get("cpu_hour_price", 0.0),
            dataset_size_gb=merged_config.get("dataset_size_gb", 0.0),
            storage_price_per_gb=merged_config.get("storage_price_per_gb", 0.0),
            tokens_used=merged_config.get("tokens_used", 0),
            token_price_per_million=merged_config.get("token_price_per_million", 0.0),
            energy_source=merged_config.get("energy_source", "EXTERNAL"),
            gpu_model=merged_config.get("gpu_model"),
            site=merged_config.get("site")
        )

        manager = CostManager(config, merged_config.get("currency", "USD"))
        return manager.breakdown()




def find_best_scenario(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not scenarios:
        raise ValueError("Scenarios list cannot be empty")
    return min(scenarios, key=lambda s: s["total_cost"])


def find_worst_scenario(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not scenarios:
        raise ValueError("Scenarios list cannot be empty")
    return max(scenarios, key=lambda s: s["total_cost"])


def calculate_cost_difference(base_total: float, scenario_total: float) -> Dict[str, float]:
    diff = scenario_total - base_total
    pct = (diff / base_total * 100) if base_total > 0 else 0.0
    return {"difference": diff, "percentage": pct}


def find_dominant_cost_component(breakdown: Dict[str, Any]) -> str:
    components = {
        "Hardware": breakdown.get("hardware_cost", 0),
        "Storage": breakdown.get("storage_cost", 0),
        "Token": breakdown.get("token_cost", 0),
        "Energy": breakdown.get("energy_cost", 0),
    }
    if all(v == 0 for v in components.values()):
        return "None"
    return max(components, key=components.get)


def generate_scenario_comment(name: str, diff_info: Dict[str, float]) -> str:
    diff = diff_info["difference"]
    pct = diff_info["percentage"]

    if diff < 0:
        return f"{name} reduces total cost by {abs(pct):.1f}% compared to baseline."
    elif diff > 0:
        return f"{name} increases total cost by {pct:.1f}% compared to baseline."
    return f"{name} has the same total cost as the baseline."


def calculate_cost_breakdown(
    training_hours: float,
    gpu_hour_price: float,
    cpu_hour_price: float,
    dataset_size_gb: float,
    storage_price_per_gb: float,
    tokens_used: int,
    token_price_per_million: float,
    energy_source: str,
    currency: str,
    gpu_model: Optional[str] = None,
    site: Optional[str] = None
) -> Dict[str, Any]:
    config = TrainingConfig(
        training_hours=training_hours,
        gpu_hour_price=gpu_hour_price,
        cpu_hour_price=cpu_hour_price,
        dataset_size_gb=dataset_size_gb,
        storage_price_per_gb=storage_price_per_gb,
        tokens_used=tokens_used,
        token_price_per_million=token_price_per_million,
        energy_source=energy_source,
        gpu_model=gpu_model,
        site=site
    )

    manager = CostManager(config, currency)
    return manager.breakdown()
