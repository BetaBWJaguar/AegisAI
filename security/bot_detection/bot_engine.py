from security.bot_detection.behavior_features import BehaviorFeatures
from security.bot_detection.botverdictresolver import BotVerdictResolver
from security.bot_detection.models.model import AIModel


class BotEngine:
    def __init__(self, window_sec: float = 30.0):
        self.window_sec = window_sec
        self.ai_model = AIModel()

    def analyze(self, timestamps: list) -> dict:
        if len(timestamps) < 5:
            return {
                "verdict": "UNKNOWN",
                "reason": "Not enough data"
            }

        raw_features = BehaviorFeatures.extract(timestamps, self.window_sec)

        features = BehaviorFeatures.normalize(raw_features)
        score = self.ai_model.predict_proba(features)

        return BotVerdictResolver.resolve(score, features)
