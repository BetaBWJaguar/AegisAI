from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class AuditLog:
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    target: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
            user_id: uuid.UUID,
            action: str,
            target: Optional[str] = None,
            details: Optional[str] = None,
            ip_address: Optional[str] = None
    ) -> "AuditLog":
        return AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            target=target,
            details=details,
            ip_address=ip_address
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["user_id"] = str(self.user_id)
        data["created_at"] = self.created_at.isoformat()
        return data
