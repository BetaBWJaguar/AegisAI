from security.bot_detection.models.model_utils import AIModelUtils


class AIModel:
    def __init__(self, lr: float = 0.05):
        self.weights = {
            "rate": 1.4,
            "avg_interval": -1.2,
            "cv": -2.0,
            "entropy": -2.2,
            "burst_ratio": 1.6,
            "events": 0.3
        }
        self.bias = -0.6
        self.lr = lr

    def predict_proba(self, features: dict) -> float:
        z = self.bias
        for k, v in features.items():
            z += self.weights.get(k, 0.0) * v
        return AIModelUtils.sigmoid(z)

    def update(self, features: dict, label: int):
        pred = self.predict_proba(features)
        error = label - pred

        for k, v in features.items():
            self.weights[k] = self.weights.get(k, 0.0) + self.lr * error * v

        self.bias += self.lr * error
