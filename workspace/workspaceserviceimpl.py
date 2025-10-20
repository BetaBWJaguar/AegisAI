import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from user.workspace import Workspace
from user.rule import Rule
from user.violations import Violation
from user.userserviceimpl import UserServiceImpl
from utility.client import ClientIPStorage
from workspace.workspaceservice import WorkspaceService


class WorkspaceServiceImpl(WorkspaceService):
    def __init__(self, user_service: UserServiceImpl,audit_log_service: AuditLogServiceImpl):
        self.user_service = user_service
        self.collection = user_service.collection
        self.audit_log_service = audit_log_service

    def add_workspace(self, user_id: str, workspace: Workspace,) -> Workspace:
        user = self.user_service.get_user(user_id)
        if not user:
            return None
        user.add_workspace(workspace)
        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=workspace.id,
            action="WORKSPACE_CREATED",
            target=workspace.name,
            details=f"Workspace '{workspace.name}' created by user {user.username}.",
            ip_address=ClientIPStorage.get()
        )

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
                old_name = ws.name
                ws.name = updates.get("name", ws.name)
                ws.description = updates.get("description", ws.description)
                ws.updated_at = datetime.utcnow()
                self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})

                self.audit_log_service.create_log(
                    user_id=uuid.UUID(user_id),
                    workspace_id=uuid.UUID(workspace_id),
                    action="WORKSPACE_UPDATED",
                    target=ws.name,
                    details=f"Workspace '{old_name}' updated. New name: '{ws.name}'.",
                    ip_address=ClientIPStorage.get()
                )
                return ws
        return None

    def remove_workspace(self, user_id: str, workspace_id: str) -> bool:
        user = self.user_service.get_user(user_id)
        if not user:
            return False

        workspace = next((ws for ws in user.workspaces if str(ws.id) == str(workspace_id)), None)
        if not workspace:
            return False

        user.workspaces = [ws for ws in user.workspaces if str(ws.id) != str(workspace_id)]
        user.updated_at = datetime.utcnow()

        result = self.collection.update_one(
            {"id": str(user.id)},
            {"$set": {"workspaces": [w.to_dict() for w in user.workspaces]}}
        )

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="WORKSPACE_DELETED",
            target=workspace.name,
            details=f"Workspace '{workspace.name}' was deleted by {user.username}.",
            ip_address=ClientIPStorage.get()
        )

        return result.modified_count > 0


    def add_rule(self, user_id: str, workspace_id: str, rule: Rule) -> Optional[Rule]:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None

        ws.add_rule(rule)

        user = self.user_service.get_user(user_id)

        for i, w in enumerate(user.workspaces):
            if str(w.id) == str(workspace_id):
                user.workspaces[i] = ws
                break

        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="RULE_ADDED",
            target=rule.name,
            details=f"Rule '{rule.name}' added to workspace '{ws.name}'.",
            ip_address=ClientIPStorage.get()
        )

        return rule

    def remove_rule(self, user_id: str, workspace_id: str, rule_id: str) -> bool:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return False

        rule = next((r for r in ws.rules if str(r.id) == str(rule_id)), None)
        if not rule:
            return False

        ws.rules = [r for r in ws.rules if str(r.id) != str(rule_id)]
        ws.updated_at = datetime.utcnow()

        user = self.user_service.get_user(user_id)

        for i, w in enumerate(user.workspaces):
            if str(w.id) == str(workspace_id):
                user.workspaces[i] = ws
                break

        self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="RULE_REMOVED",
            target=rule.name,
            details=f"Rule '{rule.name}' removed from workspace '{ws.name}'.",
            ip_address=ClientIPStorage.get()
        )

        return True

    def add_violation(self, user_id: str, workspace_id: str, violation: Violation) -> Optional[Violation]:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None

        ws.add_violation(violation)
        user = self.user_service.get_user(user_id)

        self.collection.update_one(
            {"id": str(user.id), "workspaces.id": str(ws.id)},
            {"$set": {"workspaces.$": ws.to_dict()}}
        )

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="VIOLATION_ADDED",
            target=violation.description,
            details=f"Violation added in workspace '{ws.name}' with severity '{violation.severity}'.",
            ip_address=ClientIPStorage.get()
        )

        return violation

    def get_violations(self, user_id: str, workspace_id: str) -> List[Violation]:
        ws = self.get_workspace(user_id, workspace_id)
        return ws.violations if ws else []

    def update_violation(
            self,
            user_id: str,
            workspace_id: str,
            violation_id: str,
            updates: Dict[str, Any]
    ) -> Optional[Violation]:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None

        for v in ws.violations:
            if str(v.id) == str(violation_id):
                prev_status = v.resolved
                v.description = updates.get("description", v.description)
                v.severity = updates.get("severity", v.severity)

                if "metadata" in updates and isinstance(updates["metadata"], dict):
                    if hasattr(v, "metadata") and isinstance(v.metadata, dict):
                        v.metadata.update(updates["metadata"])
                    else:
                        v.metadata = updates["metadata"]

                if "resolved" in updates:
                    v.resolved = updates["resolved"]
                    if v.resolved:
                        v.resolved_at = datetime.utcnow()
                        v.resolved_by = updates.get("resolved_by")

                ws.updated_at = datetime.utcnow()

                user = self.user_service.get_user(user_id)

                self.collection.update_one(
                    {"id": str(user.id), "workspaces.id": str(ws.id)},
                    {"$set": {"workspaces.$": ws.to_dict()}}
                )

                status = "resolved" if v.resolved and not prev_status else "updated"
                self.audit_log_service.create_log(
                    user_id=uuid.UUID(user_id),
                    workspace_id=uuid.UUID(workspace_id),
                    action=f"VIOLATION_{status.upper()}",
                    target=v.description,
                    details=f"Violation '{v.description}' was {status} in workspace '{ws.name}'.",
                    ip_address=ClientIPStorage.get()
                )
                return v
        return None

    def remove_violation(self, user_id: str, workspace_id: str, violation_id: str) -> bool:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return False

        violation = next((v for v in ws.violations if str(v.id) == str(violation_id)), None)
        if not violation:
            return False

        ws.violations = [v for v in ws.violations if str(v.id) != str(violation_id)]
        ws.updated_at = datetime.utcnow()

        user = self.user_service.get_user(user_id)

        result = self.collection.update_one(
            {"id": str(user.id), "workspaces.id": str(ws.id)},
            {"$set": {"workspaces.$": ws.to_dict()}}
        )

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="VIOLATION_REMOVED",
            target=violation.description,
            details=f"Violation '{violation.description}' removed from workspace '{ws.name}'.",
            ip_address=ClientIPStorage.get()
        )


        return result.modified_count > 0

