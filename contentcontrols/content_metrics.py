import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime


@dataclass
class EvaluationMetric:
    timestamp: float
    user_id: str
    allowed: bool
    detector: str
    response_time_ms: float


@dataclass
class DetectorMetric:
    detector_type: str
    total_checks: int = 0
    total_blocks: int = 0
    avg_response_time_ms: float = 0.0


@dataclass
class CacheMetric:
    total_requests: int = 0
    cache_hits: int = 0
    hit_rate: float = 0.0


@dataclass
class MetricsSummary:
    total_evaluations: int
    total_blocks: int
    block_rate: float
    avg_response_time_ms: float
    cache_hit_rate: float
    detector_stats: Dict[str, DetectorMetric]


class ContentMetrics:

    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self._lock = threading.RLock()

        self._evaluation_history: List[EvaluationMetric] = []
        self._detector_metrics: Dict[str, DetectorMetric] = defaultdict(
            lambda: DetectorMetric(detector_type="")
        )
        self._cache_metric = CacheMetric()

    def record_evaluation(
        self,
        user_id: str,
        allowed: bool,
        detector: str,
        response_time_ms: float
    ) -> None:
        with self._lock:
            metric = EvaluationMetric(
                timestamp=time.time(),
                user_id=user_id,
                allowed=allowed,
                detector=detector,
                response_time_ms=response_time_ms
            )

            self._evaluation_history.append(metric)

            if len(self._evaluation_history) > self.max_history_size:
                self._evaluation_history.pop(0)

    def record_detector_performance(
        self,
        detector_type: str,
        response_time_ms: float,
        blocked: bool
    ) -> None:
        with self._lock:
            metric = self._detector_metrics[detector_type]
            metric.detector_type = detector_type
            metric.total_checks += 1
            metric.avg_response_time_ms = (
                (metric.avg_response_time_ms * (metric.total_checks - 1) + response_time_ms) / metric.total_checks
            )

            if blocked:
                metric.total_blocks += 1

    def record_cache_hit(self) -> None:
        with self._lock:
            self._cache_metric.total_requests += 1
            self._cache_metric.cache_hits += 1
            self._cache_metric.hit_rate = (
                self._cache_metric.cache_hits / self._cache_metric.total_requests * 100
            )

    def record_cache_miss(self) -> None:
        with self._lock:
            self._cache_metric.total_requests += 1
            self._cache_metric.hit_rate = (
                self._cache_metric.cache_hits / self._cache_metric.total_requests * 100
            )

    def get_summary(self, start_time: Optional[float] = None, end_time: Optional[float] = None) -> MetricsSummary:
        with self._lock:
            now = time.time()
            start_time = start_time or (now - 3600)
            end_time = end_time or now

            filtered_evaluations = [
                e for e in self._evaluation_history
                if start_time <= e.timestamp <= end_time
            ]

            total_evaluations = len(filtered_evaluations)
            total_blocks = sum(1 for e in filtered_evaluations if not e.allowed)
            block_rate = (total_blocks / total_evaluations * 100) if total_evaluations > 0 else 0.0

            avg_response_time_ms = (
                sum(e.response_time_ms for e in filtered_evaluations) / total_evaluations
                if total_evaluations > 0 else 0.0
            )

            return MetricsSummary(
                total_evaluations=total_evaluations,
                total_blocks=total_blocks,
                block_rate=block_rate,
                avg_response_time_ms=avg_response_time_ms,
                cache_hit_rate=self._cache_metric.hit_rate,
                detector_stats=dict(self._detector_metrics)
            )

    def get_detector_stats(self, detector_type: str) -> Optional[DetectorMetric]:
        with self._lock:
            return self._detector_metrics.get(detector_type)

    def get_all_detector_stats(self) -> Dict[str, DetectorMetric]:
        with self._lock:
            return dict(self._detector_metrics)

    def get_cache_stats(self) -> CacheMetric:
        with self._lock:
            return self._cache_metric

    def get_top_blocked_detectors(self, limit: int = 10) -> List[tuple]:
        with self._lock:
            detector_blocks = defaultdict(int)

            for metric in self._evaluation_history:
                if not metric.allowed:
                    detector_blocks[metric.detector] += 1

            return sorted(detector_blocks.items(), key=lambda x: x[1], reverse=True)[:limit]

    def clear_history(self) -> None:
        with self._lock:
            self._evaluation_history.clear()

    def reset_detector_metrics(self, detector_type: Optional[str] = None) -> None:
        with self._lock:
            if detector_type:
                self._detector_metrics[detector_type] = DetectorMetric(detector_type=detector_type)
            else:
                self._detector_metrics.clear()

    def reset_cache_metrics(self) -> None:
        with self._lock:
            self._cache_metric = CacheMetric()

    def export_metrics(self) -> Dict:
        with self._lock:
            return {
                "summary": self.get_summary().__dict__,
                "detector_stats": {k: v.__dict__ for k, v in self._detector_metrics.items()},
                "cache_stats": self._cache_metric.__dict__,
                "top_blocked_detectors": self.get_top_blocked_detectors(),
                "export_timestamp": datetime.now().isoformat()
            }
