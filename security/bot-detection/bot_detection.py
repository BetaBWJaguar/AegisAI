from bot_detection_logger import BotDetectionLogger
from bot_engine import BotEngine


class BotDetection:
    def __init__(self):
        self.logger = BotDetectionLogger()
        self.engine = BotEngine()

    def log_message(self, actor_key: str):
        self.logger.log_message(actor_key)

    def check(self, actor_key: str) -> dict:
        timestamps = self.logger.get_events(actor_key)
        return self.engine.analyze(timestamps)
