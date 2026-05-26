# -*- coding: utf-8 -*-
from profanity.penalties.penalty_duration_calculator import PenaltyDurationCalculator


class PenaltyDurationService:

    def __init__(
        self,
        base_durations: dict,
        category_multipliers: dict
    ):
        self.calculator = PenaltyDurationCalculator(
            base_durations=base_durations,
            category_multipliers=category_multipliers
        )

    def calculate(self, penalties: list, escalation_multiplier: float = 1.0) -> dict:
        return self.calculator.calculate_duration(penalties, escalation_multiplier=escalation_multiplier)

    def get_statistics(self) -> dict:
        statistics = self.calculator.calculate_statistics()
        return {
            "success": True,
            "data": {
                "configuration": {
                    "base_durations": self.calculator.base_durations,
                    "category_multipliers": self.calculator.category_multipliers
                },
                "statistics": statistics
            }
        }
