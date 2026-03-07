import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from auditmanager.auditlogserviceimpl import AuditLogServiceImpl
from security.breach.doxxing_settings import DoxxingSettings, DoxxingPIIConfig, DoxxingContextConfig
from trainer.modelregistry import ModelRegistry
from user.censormode import CensorMode
from user.censorsettings import CensorSettings, CensorRule
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
                old_model = ws.model_name

                ws.name = updates.get("name", ws.name)
                ws.description = updates.get("description", ws.description)

                if "model_name" in updates or "model_version" in updates:
                    new_name = updates.get("model_name", ws.model_name)

                    raw_version = updates.get("model_version", ws.model_version)

                    registry = ModelRegistry()
                    model = registry.get_model(new_name, raw_version)

                    if not model:
                        raise ValueError(
                            f"Model '{new_name}' version '{raw_version}' not found"
                        )

                    ws.assign_model(model)

                if "censor_settings" in updates:
                    raw_settings = updates["censor_settings"]
                    new_cs = CensorSettings()

                    for label, rule_dict in raw_settings.get("rules", {}).items():
                        new_cs.set_rule(
                            label,
                            CensorRule(
                                mask=rule_dict.get("mask", False),
                                mode=CensorMode(rule_dict.get("mode", "partial")),
                                threshold=rule_dict.get("threshold", 0.0)
                            )
                        )

                    ws.censor_settings = new_cs

                if "advisory_policy" in updates:
                    advisory_updates = updates["advisory_policy"]

                    VALID_RISKS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

                    for risk, action in advisory_updates.items():
                        risk_upper = risk.upper()
                        if risk_upper not in VALID_RISKS:
                            raise ValueError(f"Invalid risk '{risk}'. Allowed risks: {VALID_RISKS}")
                        ws.advisory_policy[risk_upper] = action.upper()

                if "bot_detection" in updates:
                    ws.bot_detection = bool(updates["bot_detection"])

                if "doxxing_settings" in updates:
                    raw_settings = updates["doxxing_settings"]
                    ws.doxxing_settings = DoxxingSettings.from_dict(raw_settings)

                if "content_control_settings" in updates:
                    raw = updates["content_control_settings"]

                    cc = ws.content_control_settings

                    if "enabled" in raw:
                        cc.enabled = bool(raw["enabled"])

                    if "use_score_based_decision" in raw:
                        cc.use_score_based_decision = bool(raw["use_score_based_decision"])

                    if "spam" in raw:
                        spam = raw["spam"]

                        if "enabled" in spam:
                            cc.spam.enabled = bool(spam["enabled"])

                        if "rate_limit_count" in spam:
                            cc.spam.rate_limit_count = int(spam["rate_limit_count"])

                        if "rate_limit_window_seconds" in spam:
                            cc.spam.rate_limit_window_seconds = int(spam["rate_limit_window_seconds"])

                        if "burst_limit" in spam:
                            cc.spam.burst_limit = int(spam["burst_limit"])

                        if "burst_window_seconds" in spam:
                            cc.spam.burst_window_seconds = int(spam["burst_window_seconds"])

                        if "cooldown_seconds" in spam:
                            cc.spam.cooldown_seconds = int(spam["cooldown_seconds"])

                        if "duplicate_check" in spam:
                            cc.spam.duplicate_check = bool(spam["duplicate_check"])

                        if "duplicate_reset_seconds" in spam:
                            cc.spam.duplicate_reset_seconds = int(spam["duplicate_reset_seconds"])

                        if "exempt_roles" in spam:
                            cc.spam.exempt_roles = list(spam["exempt_roles"])

                        if "max_message_length" in spam:
                            cc.spam.max_message_length = int(spam["max_message_length"])

                        if "max_emojis" in spam:
                            cc.spam.max_emojis = int(spam["max_emojis"])

                        if "max_repeated_char" in spam:
                            cc.spam.max_repeated_char = int(spam["max_repeated_char"])

                    if "score_thresholds" in raw:
                        thresholds = raw["score_thresholds"]

                        if "enabled" in thresholds:
                            cc.score_thresholds.enabled = bool(thresholds["enabled"])

                        if "low_threshold" in thresholds:
                            cc.score_thresholds.low_threshold = float(thresholds["low_threshold"])

                        if "medium_threshold" in thresholds:
                            cc.score_thresholds.medium_threshold = float(thresholds["medium_threshold"])

                        if "high_threshold" in thresholds:
                            cc.score_thresholds.high_threshold = float(thresholds["high_threshold"])

                        if "critical_threshold" in thresholds:
                            cc.score_thresholds.critical_threshold = float(thresholds["critical_threshold"])

                    ws.updated_at = datetime.utcnow()

                ws.updated_at = datetime.utcnow()

                self.collection.update_one({"id": str(user.id)}, {"$set": user.to_dict()})

                details = f"Workspace '{old_name}' updated."
                if "model_name" in updates:
                    details += f" Model changed from '{old_model}' to '{ws.model_name}'."

                self.audit_log_service.create_log(
                    user_id=uuid.UUID(user_id),
                    workspace_id=uuid.UUID(workspace_id),
                    action="WORKSPACE_UPDATED",
                    target=ws.name,
                    details=details,
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

    def get_doxxing_settings(
            self,
            user_id: str,
            workspace_id: str
    ) -> Optional[DoxxingSettings]:
        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None

        if not ws.doxxing_settings:
            ws.doxxing_settings = DoxxingSettings()

        return ws.doxxing_settings

    def update_doxxing_settings(
            self,
            user_id: str,
            workspace_id: str,
            settings: Dict[str, Any]
    ) -> Optional[DoxxingSettings]:

        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None

        ws.doxxing_settings = DoxxingSettings.from_dict(settings)
        ws.updated_at = datetime.utcnow()

        user = self.user_service.get_user(user_id)
        for i, w in enumerate(user.workspaces):
            if str(w.id) == str(workspace_id):
                user.workspaces[i] = ws
                break

        self.collection.update_one(
            {"id": str(user.id)},
            {"$set": user.to_dict()}
        )

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="DOXXING_SETTINGS_UPDATED",
            target=ws.name,
            details="Doxxing settings updated.",
            ip_address=ClientIPStorage.get()
        )

        return ws.doxxing_settings

    def update_pii_config(
            self,
            user_id: str,
            workspace_id: str,
            pii_type: str,
            enabled: Optional[bool] = None,
            weight: Optional[float] = None,
    ) -> Optional[DoxxingPIIConfig]:

        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None

        ws.doxxing_settings.update_pii_config(pii_type, enabled, weight)
        ws.updated_at = datetime.utcnow()

        user = self.user_service.get_user(user_id)
        for i, w in enumerate(user.workspaces):
            if str(w.id) == str(workspace_id):
                user.workspaces[i] = ws
                break

        self.collection.update_one(
            {"id": str(user.id)},
            {"$set": user.to_dict()}
        )

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="DOXXING_PII_UPDATED",
            target=pii_type,
            details=f"PII config updated for '{pii_type}'.",
            ip_address=ClientIPStorage.get()
        )

        return ws.doxxing_settings.pii_config.get(pii_type)


    def update_context_config(
            self,
            user_id: str,
            workspace_id: str,
            context_type: str,
            enabled: Optional[bool] = None,
            weight: Optional[float] = None,
    ) -> Optional[DoxxingContextConfig]:

        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return None

        ws.doxxing_settings.update_context_config(context_type, enabled, weight)
        ws.updated_at = datetime.utcnow()

        user = self.user_service.get_user(user_id)
        for i, w in enumerate(user.workspaces):
            if str(w.id) == str(workspace_id):
                user.workspaces[i] = ws
                break

        self.collection.update_one(
            {"id": str(user.id)},
            {"$set": user.to_dict()}
        )

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="DOXXING_CONTEXT_UPDATED",
            target=context_type,
            details=f"Context config updated for '{context_type}'.",
            ip_address=ClientIPStorage.get()
        )

        return ws.doxxing_settings.context_config.get(context_type)

    def set_risk_action(
            self,
            user_id: str,
            workspace_id: str,
            risk_tier: str,
            action: str
    ) -> bool:

        ws = self.get_workspace(user_id, workspace_id)
        if not ws:
            return False

        ws.doxxing_settings.set_action_for_risk(risk_tier, action)
        ws.updated_at = datetime.utcnow()

        user = self.user_service.get_user(user_id)
        for i, w in enumerate(user.workspaces):
            if str(w.id) == str(workspace_id):
                user.workspaces[i] = ws
                break

        self.collection.update_one(
            {"id": str(user.id)},
            {"$set": user.to_dict()}
        )

        self.audit_log_service.create_log(
            user_id=uuid.UUID(user_id),
            workspace_id=uuid.UUID(workspace_id),
            action="DOXXING_RISK_ACTION_UPDATED",
            target=risk_tier.upper(),
            details=f"Risk action set to '{action.upper()}'.",
            ip_address=ClientIPStorage.get()
        )

        return True



