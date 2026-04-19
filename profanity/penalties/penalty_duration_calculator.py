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
