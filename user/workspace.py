from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import List
from user.rule import Rule
from user.violations import Violation


@dataclass
class Workspace:
    id: uuid.UUID
    name: str
    description: str
    rules: List[Rule] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    language: str = "tr"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(name: str, description: str = "", language: str = "en") -> "Workspace":
        now = datetime.utcnow()
        return Workspace(
            id=uuid.uuid4(),
            name=name,
            description=description,
            rules=[],
            violations=[],
            language=language,
            created_at=now,
            updated_at=now
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)

        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        if isinstance(self.updated_at, datetime):
            data["updated_at"] = self.updated_at.isoformat()

        data["rules"] = [r.to_dict() for r in self.rules]
        data["violations"] = [v.to_dict() for v in self.violations]
        return data

    def add_rule(self, rule: Rule):
        self.rules.append(rule)
        self.updated_at = datetime.utcnow()


    def add_violation(self, violation: Violation):
        self.violations.append(violation)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)

        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        if isinstance(self.updated_at, datetime):
            data["updated_at"] = self.updated_at.isoformat()

        data["rules"] = [r.to_dict() for r in self.rules]
        data["violations"] = [v.to_dict() for v in self.violations]
        return data
