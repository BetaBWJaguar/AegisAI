import time
from collections import defaultdict


class BotDetectionLogger:
    def __init__(self, max_events: int = 20):
        self.events = defaultdict(list)
        self.max_events = max_events

    def log_message(self, actor_key: str):
        now = time.time()
        self.events[actor_key].append(now)

        self.events[actor_key] = self.events[actor_key][-self.max_events:]

    def get_events(self, actor_key: str):
        return self.events.get(actor_key, [])
