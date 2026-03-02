from typing import Optional

from contentcontrols.content_control_service import ContentControlService
from contentcontrols.content_control import ContentDecision, ContentControlEngine
from user.workspace import Workspace


class ContentControlServiceImpl(ContentControlService):

    def evaluate_content(
            self,
            workspace: Workspace,
            message: str,
            user_identifier: str,
            user_role: Optional[str] = None
    ) -> ContentDecision:

        engine = ContentControlEngine(workspace)

        return engine.evaluate(
            user_id=user_identifier,
            message=message,
            user_role=user_role
        )