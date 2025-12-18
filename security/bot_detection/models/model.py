from security.bot_detection.models.model_utils import AIModelUtils


class AIModel:
    def __init__(self, lr: float = 0.03):
        self.weights = {
            "message_rate": 1.6,
            "burst_density": 1.8,
            "avg_inter_arrival": -1.4,
            "cv": -2.2,
            "entropy": -2.4,
            "events": 0.4,
        }

        self.bias = -0.7
        self.lr = lr
        self.weight_clip = 4.0

    def predict_proba(self, features: dict) -> float:
        z = self.bias
        for k, v in features.items():
            z += self.weights.get(k, 0.0) * v
        return AIModelUtils.sigmoid(z)

    def update(self, features: dict, label: int):
        pred = self.predict_proba(features)
        error = label - pred

        for k, v in features.items():
            w = self.weights.get(k, 0.0)
            w += self.lr * error * v
            self.weights[k] = max(min(w, self.weight_clip), -self.weight_clip)

        self.bias += self.lr * error
        self.bias = max(min(self.bias, self.weight_clip), -self.weight_clip)
