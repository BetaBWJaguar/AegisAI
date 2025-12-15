import math


class AIModelUtils:

    @staticmethod
    def sigmoid(z: float) -> float:
        try:
            return 1 / (1 + math.exp(-z))
        except OverflowError:
            return 0.0 if z < 0 else 1.0

    @staticmethod
    def normalize(value: float, min_v: float, max_v: float) -> float:
        if max_v - min_v == 0:
            return 0.0
        return (value - min_v) / (max_v - min_v)

    @staticmethod
    def clamp01(x: float) -> float:
        return max(0.0, min(1.0, x))
