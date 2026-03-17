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
            wid for wid, data in list(self._engines.items())
            if now - data.get("created_at", 0) > self.ENGINE_TTL_SECONDS
        ]

        for wid in expired:
            self._engines.pop(wid, None)

    def evaluate_content(
            self,
            workspace: Workspace,
            message: str,
            user_identifier: str,
            user_role: Optional[str] = None
    ) -> ContentDecision:

        if workspace is None:
            raise ValueError("Workspace cannot be None")

        if message is None:
            raise ValueError("Message cannot be None")

        self._cleanup_cache()

        workspace_id = str(workspace.id)

        cache_entry = self._engines.get(workspace_id)

        if cache_entry is None:
            cache_entry = {
                "engine": ContentControlEngine(workspace),
                "created_at": time.time()
            }
            self._engines[workspace_id] = cache_entry

        engine: ContentControlEngine = cache_entry["engine"]

        if engine.workspace.updated_at < workspace.updated_at:
            cache_entry = {
                "engine": ContentControlEngine(workspace),
                "created_at": time.time()
            }
            self._engines[workspace_id] = cache_entry
            engine = cache_entry["engine"]

        if not user_identifier:
            user_identifier = "anonymous"

        return engine.evaluate(
            user_id=user_identifier,
            message=message,
            user_role=user_role
        )