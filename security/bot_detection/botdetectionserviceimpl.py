from typing import Dict, Any, List, Optional
from security.bot_detection.botdetectionservice import BotDetectionService
from security.bot_detection.bot_detection import BotDetection
from security.bot_detection.behavior_features import BehaviorFeatures
from datetime import datetime
from workspace.workspaceserviceimpl import WorkspaceServiceImpl
from user.userserviceimpl import UserServiceImpl
from auditmanager.auditlogserviceimpl import AuditLogServiceImpl


class BotDetectionServiceImpl(BotDetectionService):
    def __init__(self, max_events: int = 60, window_sec: float = 30.0):
        self.bot_detection = BotDetection(max_events=max_events, window_sec=window_sec)
        self.user_service = UserServiceImpl("config.json")
        self.audit_log_service = AuditLogServiceImpl("config.json")
        self.workspace_service = WorkspaceServiceImpl(self.user_service, self.audit_log_service)

    def _get_workspace_bot_detection_setting(self, workspace_id: str) -> bool:
        if not workspace_id:
            return False

        users = self.user_service.collection.find({"workspaces.id": workspace_id})
        for user_doc in users:
            user = self.user_service.get_user(user_doc["id"])
            for workspace in user.workspaces:
                if str(workspace.id) == workspace_id:
                    return workspace.bot_detection
        return False

    def log_message(self, actor_key: str, workspace_id: Optional[str] = None) -> None:
        if self._get_workspace_bot_detection_setting(workspace_id):
            self.bot_detection.log_message(actor_key)

    def check_actor(self, actor_key: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        if not self._get_workspace_bot_detection_setting(workspace_id):
            return {
                "actor_key": actor_key,
                "verdict": "DISABLED",
                "confidence": 0.0,
                "action": "ALLOW",
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "Bot detection is disabled for this workspace"
            }
            
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