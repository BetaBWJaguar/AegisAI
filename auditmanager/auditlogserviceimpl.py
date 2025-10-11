from datetime import datetime
from typing import List, Optional
import uuid
from pymongo import MongoClient

from auditmanager.auditlog_service import AuditLogService
from auditmanager.auditlog import AuditLog
from config_loader import ConfigLoader


class AuditLogServiceImpl(AuditLogService):
    def __init__(self, config_file: str = "config.json"):
        cfg = ConfigLoader(config_file).get_database_config()

        uri = f"mongodb://{cfg['username']}:{cfg['password']}@" \
              f"{cfg['host']}:{cfg['port']}/{cfg['authSource']}"
        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["audit_logs"]
        self.collection.create_index("workspace_id")
        self.collection.create_index("user_id")

    def create_log(
            self,
            user_id: uuid.UUID,
            workspace_id: uuid.UUID,
            action: str,
            target: Optional[str] = None,
            details: Optional[str] = None,
            ip_address: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog.create(
            user_id=user_id,
            workspace_id=workspace_id,
            action=action,
            target=target,
            details=details,
            ip_address=ip_address
        )

        self.collection.insert_one(log.to_dict())
        return log

    def get_all_logs(self, workspace_id: uuid.UUID) -> List[AuditLog]:
        cursor = self.collection.find({"workspace_id": str(workspace_id)})
        return [self._from_document(doc) for doc in cursor]

    def get_user_logs(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> List[AuditLog]:
        cursor = self.collection.find({
            "workspace_id": str(workspace_id),
            "user_id": str(user_id)
        })
        return [self._from_document(doc) for doc in cursor]

    def get_log_by_id(self, workspace_id: uuid.UUID, log_id: uuid.UUID) -> Optional[AuditLog]:
        doc = self.collection.find_one({
            "workspace_id": str(workspace_id),
            "id": str(log_id)
        })
        return self._from_document(doc) if doc else None

    def _from_document(self, doc: dict) -> AuditLog:
        return AuditLog(
            id=uuid.UUID(doc["id"]),
            user_id=uuid.UUID(doc["user_id"]),
            workspace_id=uuid.UUID(doc["workspace_id"]),
            action=doc["action"],
            target=doc.get("target"),
            details=doc.get("details"),
            ip_address=doc.get("ip_address"),
            created_at=datetime.fromisoformat(doc["created_at"]),
        )
