import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from user.workspace import Workspace
from user.rule import Rule
from user.violations import Violation
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

    def add_violation(self, user_id: str, workspace_id: str, violation: Violation) -> Optional[Violation]:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None
        ws.add_violation(violation)
        user = self.user_service.get_user(user_id)
        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})
        return violation

    def get_violations(self, user_id: str, workspace_id: str) -> List[Violation]:
        ws = self.get_workspace(user_id, workspace_id)
        return ws.violations if ws else []

    def update_violation(self, user_id: str, workspace_id: str, violation_id: str, updates: Dict[str, Any]) -> Optional[Violation]:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None
        for v in ws.violations:
            if str(v.id) == str(violation_id):
                v.description = updates.get("description", v.description)
                v.severity = updates.get("severity", v.severity)
                if "resolved" in updates:
                    v.resolved = updates["resolved"]
                    if v.resolved:
                        v.resolved_at = datetime.utcnow()
                        v.resolved_by = updates.get("resolved_by")
                ws.updated_at = datetime.utcnow()
                user = self.user_service.get_user(user_id)
                self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})
                return v
        return None

    def remove_violation(self, user_id: str, workspace_id: str, violation_id: str) -> bool:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return False
        new_violations = [v for v in ws.violations if str(v.id) != str(violation_id)]
        if len(new_violations) == len(ws.violations):
            return False
        ws.violations = new_violations
        ws.updated_at = datetime.utcnow()
        user = self.user_service.get_user(user_id)
        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})
        return True
