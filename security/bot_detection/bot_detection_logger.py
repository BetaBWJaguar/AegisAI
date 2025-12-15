import time
from collections import defaultdict, deque
from typing import Deque, Dict, List


class BotDetectionLogger:
    def __init__(self, max_events: int = 60, window_sec: float = 30.0):
        self.events: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=max_events))
        self.window_sec = window_sec

    def log_message(self, actor_key: str):
        now = time.time()
        q = self.events[actor_key]
        q.append(now)
        self._prune_old(q, now)

    def get_events(self, actor_key: str) -> List[float]:
        q = self.events.get(actor_key)
        if not q:
            return []
        now = time.time()
        self._prune_old(q, now)
        return list(q)

    def _prune_old(self, q: Deque[float], now: float):
        cutoff = now - self.window_sec
        while q and q[0] < cutoff:
            q.popleft()
