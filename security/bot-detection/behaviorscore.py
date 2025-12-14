class BehaviorScore:
    @staticmethod
    def calculate(avg_interval: float, variance: float, count: int) -> float:
        score = 0.0

        if avg_interval < 1.0:
            score += 0.5
        elif avg_interval < 2.0:
            score += 0.3

        if variance < 0.2:
            score += 0.3
        elif variance < 0.5:
            score += 0.15

        if count >= 15:
            score += 0.2
        elif count >= 10:
            score += 0.1

        return min(score, 1.0)
