import time
from collections import defaultdict

class RateLimitUtility:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def allow_request(self, identifier: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self.requests[identifier]

        self.requests[identifier] = [t for t in timestamps if t > window_start]

        if len(self.requests[identifier]) >= self.max_requests:
            return False

        self.requests[identifier].append(now)
        return True
