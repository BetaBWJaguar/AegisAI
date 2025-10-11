from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from auditmanager.auditlog import AuditLog


class AuditLogService(ABC):
    @abstractmethod
    async def create_log(
            self,
            user_id: uuid.UUID,
            workspace_id: uuid.UUID,
            action: str,
            target: Optional[str] = None,
            details: Optional[str] = None,
            ip_address: Optional[str] = None
    ) -> AuditLog:
        pass

    @abstractmethod
    async def get_all_logs(self, workspace_id: uuid.UUID) -> List[AuditLog]:
        pass

    @abstractmethod
    async def get_user_logs(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> List[AuditLog]:
        pass

    @abstractmethod
    async def get_log_by_id(self, workspace_id: uuid.UUID, log_id: uuid.UUID) -> Optional[AuditLog]:
        pass
