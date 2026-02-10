from trainer.reports.core.training_scenario import TrainingScenario
from trainer.reports.cost_manager.cost_manager import CostManager


class ScenarioCostCalculator:

    def __init__(self, tracker: CostManager):
        self.tracker = tracker

    def calculate(self, scenario: TrainingScenario) -> dict:
        base = self.tracker.breakdown()

        return {
            "scenario": scenario.name,
            "multiplier": scenario.multiplier,
            "hardware_cost": round(base["hardware_cost"] * scenario.multiplier, 2),
            "storage_cost": round(base["storage_cost"] * scenario.multiplier, 2),
            "token_cost": round(base["token_cost"] * scenario.multiplier, 2),
            "currency": base["currency"],
            "total_cost": round(base["total_cost"] * scenario.multiplier, 2),
        }
