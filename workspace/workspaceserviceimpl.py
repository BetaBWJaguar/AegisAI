import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from user.workspace import Workspace
from user.rule import Rule
from user.userserviceimpl import UserServiceImpl
from workspace.workspaceservice import WorkspaceService

class WorkspaceServiceImpl(WorkspaceService):
    def __init__(self, user_service: UserServiceImpl):
        self.user_service = user_service
        self.collection = user_service.collection

    def add_workspace(self, user_id: str, workspace: Workspace) -> Workspace:
        user = self.user_service.get_user(user_id)
        if not user:
            return None
        user.add_workspace(workspace)
        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})
        return workspace

    def get_workspaces(self, user_id: str) -> List[Workspace]:
        user = self.user_service.get_user(user_id)
        return user.workspaces if user else []

    def get_workspace(self, user_id: str, workspace_id: str) -> Optional[Workspace]:
        user = self.user_service.get_user(user_id)
        if not user:
            return None
        return next((ws for ws in user.workspaces if str(ws.id) == str(workspace_id)), None)

    def update_workspace(self, user_id: str, workspace_id: str, updates: Dict[str, Any]) -> Optional[Workspace]:
        user = self.user_service.get_user(user_id)
        if not user:
            return None
        for ws in user.workspaces:
            if str(ws.id) == str(workspace_id):
                ws.name = updates.get("name", ws.name)
                ws.description = updates.get("description", ws.description)
                ws.updated_at = datetime.utcnow()
                self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})
                return ws
        return None

    def remove_workspace(self, user_id: str, workspace_id: str) -> bool:
        user = self.user_service.get_user(user_id)
        if not user:
            return False
        new_workspaces = [ws for ws in user.workspaces if str(ws.id) != str(workspace_id)]
        if len(new_workspaces) == len(user.workspaces):
            return False
        user.workspaces = new_workspaces
        user.updated_at = datetime.utcnow()
        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})
        return True

    def add_rule(self, user_id: str, workspace_id: str, rule: Rule) -> Optional[Rule]:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None
        ws.add_rule(rule)
        user = self.user_service.get_user(user_id)
        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})
        return rule

    def remove_rule(self, user_id: str, workspace_id: str, rule_id: str) -> bool:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return False
        new_rules = [r for r in ws.rules if str(r.id) != str(rule_id)]
        if len(new_rules) == len(ws.rules):
            return False
        ws.rules = new_rules
        ws.updated_at = datetime.utcnow()
        user = self.user_service.get_user(user_id)
        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})
        return True
