from behaviorscore import BehaviorScore
from behavior_features import BehaviorFeatures
from botverdictresolver import BotVerdictResolver


class BotEngine:
    def __init__(self, window_sec: float = 30.0):
        self.window_sec = window_sec

    def analyze(self, timestamps: list) -> dict:
        if len(timestamps) < 5:
            return {"verdict": "UNKNOWN", "reason": "Not enough data"}

        f = BehaviorFeatures.extract(timestamps, window_sec=self.window_sec)
        score = BehaviorScore.calculate(f)
        verdict = BotVerdictResolver.resolve(score)

        verdict.update({
            "confidence": round(verdict["confidence"], 3),
            "score": round(score, 3),
            "events": int(f["events"]),
            "rate": round(f["rate"], 3),
            "avg_interval": round(f["avg_interval"], 3),
            "std_interval": round(f["std_interval"], 3),
            "cv": round(f["cv"], 3),
            "entropy": round(f["entropy"], 3),
            "burst_ratio": round(f["burst_ratio"], 3),
        })
        return verdict
