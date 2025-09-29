from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from user.workspace import Workspace
from user.rule import Rule

class WorkspaceService(ABC):

    @abstractmethod
    def add_workspace(self, user_id: str, workspace: Workspace) -> Workspace:
        pass

    @abstractmethod
    def get_workspaces(self, user_id: str) -> List[Workspace]:
        pass

    @abstractmethod
    def get_workspace(self, user_id: str, workspace_id: str) -> Optional[Workspace]:
        pass

    @abstractmethod
    def update_workspace(self, user_id: str, workspace_id: str, updates: Dict[str, Any]) -> Optional[Workspace]:
        pass

    @abstractmethod
    def remove_workspace(self, user_id: str, workspace_id: str) -> bool:
        pass

    @abstractmethod
    def add_rule(self, user_id: str, workspace_id: str, rule: Rule) -> Optional[Rule]:
        pass

    @abstractmethod
    def remove_rule(self, user_id: str, workspace_id: str, rule_id: str) -> bool:
        pass
