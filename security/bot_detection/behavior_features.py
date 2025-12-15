import math
from typing import Dict, List


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var)


def _entropy_bucketed(intervals: List[float], bucket_edges=None) -> float:
    if not intervals:
        return 0.0

    if bucket_edges is None:
        bucket_edges = [0.5, 1.0, 2.0, 4.0, 8.0]  # saniye

    buckets = [0] * (len(bucket_edges) + 1)
    for x in intervals:
        placed = False
        for i, e in enumerate(bucket_edges):
            if x <= e:
                buckets[i] += 1
                placed = True
                break
        if not placed:
            buckets[-1] += 1

    total = sum(buckets)
    probs = [b / total for b in buckets if b > 0]
    ent = -sum(p * math.log(p, 2) for p in probs)
    return ent


class BehaviorFeatures:
    @staticmethod
    def extract(timestamps: List[float], window_sec: float) -> Dict[str, float]:
        if len(timestamps) < 2:
            return {
                "events": len(timestamps),
                "rate": 0.0,
                "avg_interval": 0.0,
                "std_interval": 0.0,
                "cv": 0.0,
                "entropy": 0.0,
                "burst_ratio": 0.0,
            }

        intervals = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
        avg_i = _mean(intervals)
        std_i = _std(intervals)


        cv = (std_i / avg_i) if avg_i > 1e-9 else 0.0

        rate = len(timestamps) / max(window_sec, 1e-9)

        ent = _entropy_bucketed(intervals)

        burst_ratio = sum(1 for x in intervals if x < 1.0) / len(intervals)

        return {
            "events": float(len(timestamps)),
            "rate": rate,
            "avg_interval": avg_i,
            "std_interval": std_i,
            "cv": cv,
            "entropy": ent,
            "burst_ratio": burst_ratio,
        }

    @staticmethod
    def normalize(features: Dict[str, float]) -> Dict[str, float]:
        return {
            "events": min(features["events"] / 50.0, 1.0),
            "rate": min(features["rate"] / 2.0, 1.0),
            "avg_interval": min(features["avg_interval"] / 3.0, 1.0),
            "cv": min(features["cv"], 1.0),
            "entropy": min(features["entropy"] / 2.0, 1.0),
            "burst_ratio": min(features["burst_ratio"], 1.0),
        }
