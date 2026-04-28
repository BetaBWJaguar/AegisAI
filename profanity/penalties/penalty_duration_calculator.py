# -*- coding: utf-8 -*-
from typing import Dict, List, Optional


class PenaltyDurationCalculator:

    def __init__(
        self,
        base_durations: Optional[Dict[str, int]] = None,
        category_multipliers: Optional[Dict[str, float]] = None
    ):
        self.base_durations = base_durations if base_durations is not None else {}
        self.category_multipliers = category_multipliers if category_multipliers is not None else {}

    def calculate_duration(self, penalties: List[Dict]) -> Dict:
        if not penalties:
            return {"total_duration_minutes": 0}

        total = 0
        for penalty in penalties:
            risk_level = penalty.get("risk_level", "LOW")
            category = penalty.get("category")
            confidence = penalty.get("confidence", 1.0)
            
            base = self.base_durations.get(risk_level, 0)
            multiplier = self.category_multipliers.get(category, 1.0)
            
            total += int(base * multiplier * confidence)

        return {"total_duration_minutes": total}

    def calculate_statistics(self) -> Dict:
        total_base_duration = sum(self.base_durations.values()) if self.base_durations else 0
        total_categories = len(self.category_multipliers) if self.category_multipliers else 0

        if self.category_multipliers:
            multiplier_values = list(self.category_multipliers.values())
            average_multiplier = round(sum(multiplier_values) / len(multiplier_values), 4)
            min_multiplier = min(multiplier_values)
            max_multiplier = max(multiplier_values)
        else:
            average_multiplier = 1.0
            min_multiplier = 1.0
            max_multiplier = 1.0

        if self.base_durations:
            duration_values = list(self.base_durations.values())
            min_base_duration = min(duration_values)
            max_base_duration = max(duration_values)
        else:
            min_base_duration = 0
            max_base_duration = 0

        configured_risk_levels = list(self.base_durations.keys()) if self.base_durations else []
        available_risk_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        return {
            "total_base_duration_minutes": total_base_duration,
            "total_categories": total_categories,
            "average_multiplier": average_multiplier,
            "min_multiplier": min_multiplier,
            "max_multiplier": max_multiplier,
            "min_base_duration": min_base_duration,
            "max_base_duration": max_base_duration,
            "configured_risk_levels": configured_risk_levels,
            "available_risk_levels": available_risk_levels
        }
