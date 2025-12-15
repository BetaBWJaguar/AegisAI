from bot_detection_logger import BotDetectionLogger
from bot_engine import BotEngine


class BotDetection:
    def __init__(self, max_events: int = 60, window_sec: float = 30.0):
        self.logger = BotDetectionLogger(max_events=max_events, window_sec=window_sec)
        self.engine = BotEngine(window_sec=window_sec)

    def log_message(self, actor_key: str):
        self.logger.log_message(actor_key)

    def check(self, actor_key: str) -> dict:
        timestamps = self.logger.get_events(actor_key)
        return self.engine.analyze(timestamps)
