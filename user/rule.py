from dataclasses import dataclass, asdict
import uuid
from typing import Dict, Any

@dataclass
class Rule:
    id: uuid.UUID
    name: str
    description: str
    type: str
    params: Dict[str, Any]

    @staticmethod
    def create(name: str, description: str, type: str, params: Dict[str, Any]) -> "Rule":
        return Rule(
            id=uuid.uuid4(),
            name=name,
            description=description,
            type=type,
            params=params
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        return data
