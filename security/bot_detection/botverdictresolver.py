class BotVerdictResolver:
    @staticmethod
    def resolve(score: float, features: dict) -> dict:
        if (
                features["rate"] < 1.0 and
                features["avg_interval"] > 1.0 and
                features["cv"] > 0.25 and
                features["entropy"] > 0.9
        ):
            return {
                "verdict": "HUMAN",
                "confidence": min(score, 0.49),
                "action": "ALLOW"
            }

        if score >= 0.85:
            return {
                "verdict": "BOT",
                "confidence": score,
                "action": "BLOCK"
            }

        if score >= 0.6:
            return {
                "verdict": "SUSPICIOUS",
                "confidence": score,
                "action": "MONITOR"
            }

        return {
            "verdict": "HUMAN",
            "confidence": score,
            "action": "ALLOW"
        }

