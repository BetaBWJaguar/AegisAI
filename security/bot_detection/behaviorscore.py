from typing import Dict


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


class BehaviorScore:
    @staticmethod
    def calculate(f: Dict[str, float]) -> float:
        score = 0.0

        events = f.get("events", 0)
        rate = f.get("rate", 0.0)
        avg_i = f.get("avg_interval", 999.0)
        cv = f.get("cv", 1.0)
        ent = f.get("entropy", 2.0)
        burst = f.get("burst_ratio", 0.0)

        if rate >= 0.9:
            score += 0.30
        elif rate >= 0.6:
            score += 0.20
        elif rate >= 0.4:
            score += 0.10
        if avg_i < 0.9:
            score += 0.25
        elif avg_i < 1.5:
            score += 0.15

        if cv < 0.15:
            score += 0.25
        elif cv < 0.30:
            score += 0.15

        if ent < 1.0:
            score += 0.15
        elif ent < 1.5:
            score += 0.08

        if burst > 0.6:
            score += 0.15
        elif burst > 0.35:
            score += 0.08

        if events < 8:
            score *= 0.7
        elif events < 12:
            score *= 0.85

        return _clamp01(score)

