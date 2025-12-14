from behaviorscore import BehaviorScore
from botverdictresolver import BotVerdictResolver


class BotEngine:
    @staticmethod
    def analyze(timestamps: list) -> dict:
        if len(timestamps) < 5:
            return {
                "verdict": "UNKNOWN",
                "reason": "Not enough data"
            }

        intervals = [
            timestamps[i] - timestamps[i - 1]
            for i in range(1, len(timestamps))
        ]

        avg_interval = sum(intervals) / len(intervals)
        variance = max(intervals) - min(intervals)
        count = len(timestamps)

        score = BehaviorScore.calculate(
            avg_interval=avg_interval,
            variance=variance,
            count=count
        )

        verdict = BotVerdictResolver.resolve(score)

        verdict.update({
            "avg_interval": round(avg_interval, 3),
            "variance": round(variance, 3),
            "events": count
        })

        return verdict
