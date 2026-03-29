from abc import ABC, abstractmethod
from typing import Optional

from contentcontrols.content_control import ContentDecision
from contentcontrols.content_metrics import ContentMetrics
from user.workspace import Workspace


class ContentControlService(ABC):

    @abstractmethod
    def evaluate_content(self, workspace: Workspace, message: str, user_identifier: str,
                        user_role: Optional[str] = None) -> ContentDecision:
        ...

    @abstractmethod
    def get_metrics(self) -> ContentMetrics:
        ...