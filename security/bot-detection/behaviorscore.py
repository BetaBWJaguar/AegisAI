# behaviorscore.py
from typing import Dict


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


class BehaviorScore:
    @staticmethod
    def calculate(f: Dict[str, float]) -> float:
        score = 0.0

        events = f["events"]
        rate = f["rate"]
        avg_i = f["avg_interval"]
        cv = f["cv"]
        ent = f["entropy"]
        burst = f["burst_ratio"]

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
            score *= 0.6

        return _clamp01(score)
