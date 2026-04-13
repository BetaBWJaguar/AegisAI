# -*- coding: utf-8 -*-
from typing import Dict, Optional, Tuple
from bisect import bisect_left


class EnhancedRiskCalculator:

    CATEGORY_WEIGHTS: Dict[str, float] = {
        "sexual": 1.3,
        "hate_speech": 1.4,
        "harassment": 1.2,
        "profanity": 1.0,
        "violence": 1.3,
        "self_harm": 1.5,
    }

    _RISK_THRESHOLDS: Tuple[float, ...] = (0.60, 0.75, 0.90)
    _RISK_LEVELS: Tuple[str, ...] = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def __init__(self, category_weights: Optional[Dict[str, float]] = None):
        self.category_weights = category_weights if category_weights is not None else self.CATEGORY_WEIGHTS

    def calculate_risk(
        self,
        confidence: float,
        category: str,
        text: Optional[str] = None
    ) -> str:
        risk_score = confidence * self._get_category_weight(category) * self._calculate_length_factor(text)
        return self._determine_risk_level(max(0.0, min(1.0, risk_score)))

    def _get_category_weight(self, category: str) -> float:
        weight = self.category_weights.get(category)
        if weight is not None:
            return weight
        return self.category_weights.get(category.split("_")[0], 1.0)

    def _calculate_length_factor(self, text: Optional[str]) -> float:
        if not text:
            return 1.0
        
        text_length = len(text.strip())
        if text_length < 20:
            return 1.0
        if text_length >= 100:
            return 1.2
        return 1.0 + (text_length - 20) / 400.0

    def _determine_risk_level(self, risk_score: float) -> str:
        return self._RISK_LEVELS[bisect_left(self._RISK_THRESHOLDS, risk_score)]
