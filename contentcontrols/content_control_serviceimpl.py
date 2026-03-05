import time
from typing import Optional, Dict

from contentcontrols.content_control_service import ContentControlService
from contentcontrols.content_control import ContentDecision, ContentControlEngine
from user.workspace import Workspace


class ContentControlServiceImpl(ContentControlService):

    ENGINE_TTL_SECONDS = 600

    def __init__(self):
        self._engines: Dict[str, dict] = {}

    def _cleanup_cache(self):
        now = time.time()

        expired = [
            wid for wid, data in self._engines.items()
            if now - data["created_at"] > self.ENGINE_TTL_SECONDS
        ]

        for wid in expired:
            del self._engines[wid]

    def evaluate_content(
            self,
            workspace: Workspace,
            message: str,
            user_identifier: str,
            user_role: Optional[str] = None
    ) -> ContentDecision:

        self._cleanup_cache()

        workspace_id = str(workspace.id)

        if workspace_id not in self._engines:
            self._engines[workspace_id] = {
                "engine": ContentControlEngine(workspace),
                "created_at": time.time()
            }

        cache_entry = self._engines[workspace_id]
        engine: ContentControlEngine = cache_entry["engine"]

        if engine.workspace.updated_at < workspace.updated_at:
            self._engines[workspace_id] = {
                "engine": ContentControlEngine(workspace),
                "created_at": time.time()
            }
            engine = self._engines[workspace_id]["engine"]

        if not user_identifier:
            user_identifier = "anonymous"

        return engine.evaluate(
            user_id=user_identifier,
            message=message,
            user_role=user_role
        )