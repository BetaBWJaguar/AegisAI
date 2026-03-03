from typing import Optional, Dict
from contentcontrols.content_control_service import ContentControlService
from contentcontrols.content_control import ContentDecision, ContentControlEngine
from user.workspace import Workspace


class ContentControlServiceImpl(ContentControlService):

    def __init__(self):
        self._engines: Dict[str, ContentControlEngine] = {}

    def evaluate_content(
            self,
            workspace: Workspace,
            message: str,
            user_identifier: str,
            user_role: Optional[str] = None
    ) -> ContentDecision:

        workspace_id = str(workspace.id)

        if workspace_id not in self._engines:
            self._engines[workspace_id] = ContentControlEngine(workspace)

        engine = self._engines[workspace_id]


        if engine.workspace.updated_at != workspace.updated_at:
            self._engines[workspace_id] = ContentControlEngine(workspace)
            engine = self._engines[workspace_id]

        if not user_identifier:
            user_identifier = "anonymous"

        return engine.evaluate(
            user_id=user_identifier,
            message=message,
            user_role=user_role
        )