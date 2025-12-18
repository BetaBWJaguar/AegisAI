import math


class AIModelUtils:

    @staticmethod
    def sigmoid(z: float) -> float:
        z = max(min(z, 500), -500)
        return 1.0 / (1.0 + math.exp(-z))

    @staticmethod
    def clamp01(x: float) -> float:
        return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

    @staticmethod
    def minmax(value: float, min_v: float, max_v: float) -> float:
        if max_v <= min_v:
            return 0.0
        return (value - min_v) / (max_v - min_v)

    @staticmethod
    def zscore(value: float, mean: float, std: float) -> float:
        if std <= 1e-9:
            return 0.0
        return (value - mean) / std
