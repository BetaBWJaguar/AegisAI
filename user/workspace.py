from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import List, Optional

from trainer.modelregistry import ModelRegistry
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
    model_id: str = None
    model_name: str = None,
    model_version: str = None

    @staticmethod
    def create(
            name: str,
            description: str = "",
            language: str = "tr",
            model_name: str = None,
            model_version: Optional[str] = None
    ) -> "Workspace":

        if model_name is None:
            raise ValueError("model_name is required when creating a Workspace")

        if model_version is None:
            raise ValueError("model_version is required")

        now = datetime.utcnow()

        ws = Workspace(
            id=uuid.uuid4(),
            name=name,
            description=description,
            rules=[],
            violations=[],
            language=language,
            created_at=now,
            updated_at=now,
        )

        registry = ModelRegistry()
        model = registry.get_model(model_name,model_version)

        if model is None:
            raise ValueError(f"Model '{model_name}' and Version '{model_version}' not found in Model Database")

        ws.assign_model(model)

        return ws

    def assign_model(self, model: dict):
        self.model_id = str(model["_id"])
        self.model_name = model["name"]
        self.updated_at = datetime.utcnow()


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
