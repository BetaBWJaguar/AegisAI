from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import Optional
from bson import ObjectId


@dataclass
class Template:
    id: uuid.UUID
    name: str
    pattern: str
    description: Optional[str] = None
    category: Optional[str] = None
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: str = field(default_factory=lambda: str(ObjectId()))

    @staticmethod
    def create(name: str, pattern: str, description: str = "",
               category: Optional[str] = None, version: int = 1) -> "Template":
        now = datetime.utcnow()
        return Template(
            id=uuid.uuid4(),
            name=name,
            pattern=pattern,
            description=description,
            category=category,
            version=version,
            created_at=now,
            updated_at=now
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data
