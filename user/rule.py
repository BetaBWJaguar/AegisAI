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
    def create(name: str, description: str, type: RuleType, params: Dict[str, Any]) -> "Rule":
        now = datetime.utcnow()
        return Rule(
            id=uuid.uuid4(),
            name=name,
            description=description,
            type=type,
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
        data["type"] = self.type.value  # Enum → string
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data
