from typing import Dict, Any, List
from security.bot_detection.botdetectionservice import BotDetectionService
from security.bot_detection.bot_detection import BotDetection
from security.bot_detection.behavior_features import BehaviorFeatures
from datetime import datetime


class BotDetectionServiceImpl(BotDetectionService):
    def __init__(self, max_events: int = 60, window_sec: float = 30.0):
        self.bot_detection = BotDetection(max_events=max_events, window_sec=window_sec)

    def log_message(self, actor_key: str) -> None:
        self.bot_detection.log_message(actor_key)

    def check_actor(self, actor_key: str) -> Dict[str, Any]:
        result = self.bot_detection.check(actor_key)

        result["actor_key"] = actor_key
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result

    def get_actor_events(self, actor_key: str) -> Dict[str, Any]:
        timestamps = self.bot_detection.logger.get_events(actor_key)
        
        if not timestamps:
            return {
                "actor_key": actor_key,
                "event_count": 0,
                "events": [],
                "statistics": {}
            }

        raw_features = BehaviorFeatures.extract(timestamps, self.bot_detection.logger.window_sec)
        
        return {
            "actor_key": actor_key,
            "event_count": len(timestamps),
            "events": timestamps,
            "statistics": raw_features,
            "window_sec": self.bot_detection.logger.window_sec
        }

    def clear_actor_data(self, actor_key: str) -> bool:
        if actor_key in self.bot_detection.logger.events:
            del self.bot_detection.logger.events[actor_key]
            return True
        return False