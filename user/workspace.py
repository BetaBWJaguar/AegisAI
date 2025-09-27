from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import List
from user.rule import Rule

@dataclass
class Workspace:
    id: uuid.UUID
    name: str
    description: str
    rules: List[Rule] = field(default_factory=list)
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    @staticmethod
    def create(name: str, description: str = "") -> "Workspace":
        now = datetime.now()
        return Workspace(
            id=uuid.uuid4(),
            name=name,
            description=description,
            rules=[],
            created_at=now,
            updated_at=now
        )

    def add_rule(self, rule: Rule):
        self.rules.append(rule)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["rules"] = [r.to_dict() for r in self.rules]
        return data
