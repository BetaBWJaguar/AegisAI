class BotVerdictResolver:
    @staticmethod
    def resolve(score: float) -> dict:
        if score >= 0.8:
            return {
                "verdict": "BOT",
                "confidence": score,
                "action": "BLOCK"
            }

        if score >= 0.5:
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
