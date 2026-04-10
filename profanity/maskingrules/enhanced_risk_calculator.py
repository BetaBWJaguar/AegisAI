# -*- coding: utf-8 -*-
from typing import Dict, Optional


class EnhancedRiskCalculator:


    CATEGORY_WEIGHTS = {
        "sexual": 1.3,
        "hate_speech": 1.4,
        "harassment": 1.2,
        "profanity": 1.0,
        "violence": 1.3,
        "self_harm": 1.5,
    }

    def __init__(self, category_weights: Optional[Dict[str, float]] = None):
        self.category_weights = category_weights or self.CATEGORY_WEIGHTS

    def calculate_risk(
        self,
        confidence: float,
        category: str,
        text: Optional[str] = None
    ) -> str:
        category_weight = self._get_category_weight(category)

        length_factor = self._calculate_length_factor(text)

        risk_score = confidence * category_weight * length_factor

        risk_score = max(0.0, min(1.0, risk_score))

        return self._determine_risk_level(risk_score)

    def _get_category_weight(self, category: str) -> float:
        if category in self.category_weights:
            return self.category_weights[category]

        main_category = category.split("_")[0]
        if main_category in self.category_weights:
            return self.category_weights[main_category]

        return 1.0

    def _calculate_length_factor(self, text: Optional[str]) -> float:
        if not text:
            return 1.0

        text_length = len(text.strip())

        if text_length < 20:
            return 1.0
        elif text_length < 100:
            return 1.0 + (text_length - 20) / 80 * 0.2
        else:
            return 1.2

    def _determine_risk_level(self, risk_score: float) -> str:
        if risk_score >= 0.90:
            return "CRITICAL"
        elif risk_score >= 0.75:
            return "HIGH"
        elif risk_score >= 0.60:
            return "MEDIUM"
        else:
            return "LOW"
