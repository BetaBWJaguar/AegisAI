from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid

@dataclass
class Violation:
    id: uuid.UUID
    user_id: str
    rule_id: str
    description: str
    created_at: datetime
    severity: str
    resolved: bool = False
    resolved_at: datetime = None
    resolved_by: str = None

    @staticmethod
    def create(user_id: str, rule_id: str, description: str, severity: str,) -> "Violation":
        now = datetime.utcnow()
        return Violation(
            id=uuid.uuid4(),
            user_id=user_id,
            rule_id=rule_id,
            description=description,
            created_at=now,
            severity=severity,
            resolved=False
        )

    def mark_resolved(self, admin_id: str):
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.resolved_by = admin_id

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        if self.resolved_at and isinstance(self.resolved_at, datetime):
            data["resolved_at"] = self.resolved_at.isoformat()
        return data
