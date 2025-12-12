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

        if avg_interval < 1.2 and variance < 0.3:
            return {
                "verdict": "BOT",
                "reason": "Fast and regular messaging"
            }

        if avg_interval < 2:
            return {
                "verdict": "SUSPICIOUS",
                "reason": "Fast messaging"
            }

        return {
            "verdict": "HUMAN",
            "reason": "Normal behavior"
        }
