from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BotDetectionService(ABC):

    @abstractmethod
    def log_message(self, actor_key: str, workspace_id: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def check_actor(self, actor_key: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_actor_events(self, actor_key: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def clear_actor_data(self, actor_key: str) -> bool:
        pass