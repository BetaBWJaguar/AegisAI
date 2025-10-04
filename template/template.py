from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import Optional, Dict

from bson import ObjectId


@dataclass
class Template:
    id: uuid.UUID
    name: str
    pattern: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: str = field(default_factory=lambda: str(ObjectId()))

    @staticmethod
    def create(name: str, pattern: str, description: str = "") -> "Template":
        now = datetime.utcnow()
        return Template(
            id=uuid.uuid4(),
            name=name,
            pattern=pattern,
            description=description,
            created_at=now,
            updated_at=now
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data
