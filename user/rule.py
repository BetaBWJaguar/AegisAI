from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, Any
import uuid
from user.ruletype import RuleType

@dataclass
class Rule:
    id: uuid.UUID
    name: str
    description: str
    type: RuleType
    params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(name: str, description: str, types: RuleType, params: Dict[str, Any]) -> "Rule":
        now = datetime.utcnow()
        return Rule(
            id=uuid.uuid4(),
            name=name,
            description=description,
            type=types,
            params=params,
            created_at=now,
            updated_at=now
        )

    def update_params(self, new_params: Dict[str, Any]):
        self.params.update(new_params)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["type"] = getattr(self.type, "value", self.type)

        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        else:
            data["created_at"] = str(self.created_at)

        if isinstance(self.updated_at, datetime):
            data["updated_at"] = self.updated_at.isoformat()
        else:
            data["updated_at"] = str(self.updated_at)

        return data

