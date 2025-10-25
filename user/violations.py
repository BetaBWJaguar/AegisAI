from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import Optional, Dict, Any


@dataclass
class Violation:
    id: uuid.UUID
    description: str
    severity: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    @staticmethod
    def create(description: str, severity: str, metadata: Optional[Dict[str, Any]] = None) -> "Violation":
        now = datetime.utcnow()
        return Violation(
            id=uuid.uuid4(),
            description=description,
            severity=severity,
            metadata=metadata or {},
            created_at=now,
            resolved=False
        )

    def mark_resolved(self):
        self.resolved = True
        self.resolved_at = datetime.utcnow()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)

        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        else:
            data["created_at"] = str(self.created_at)

        if self.resolved_at:
            if isinstance(self.resolved_at, datetime):
                data["resolved_at"] = self.resolved_at.isoformat()
            else:
                data["resolved_at"] = str(self.resolved_at)
        else:
            data["resolved_at"] = None

        return data
