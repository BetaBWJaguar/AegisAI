from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class AdvisoryPolicy:
    rules: Dict[str, str] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    VALID_RISKS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    DEFAULT_ACTION = "LOG"

    def set_rule(self, risk: str, action: str):
        risk = risk.upper()

        if risk not in self.VALID_RISKS:
            raise ValueError(f"Invalid risk '{risk}'. Allowed: {self.VALID_RISKS}")

        self.rules[risk] = action.upper()
        self.updated_at = datetime.utcnow()

    def get_action(self, risk: str) -> str:
        risk = risk.upper()

        if risk not in self.VALID_RISKS:
            raise ValueError(f"Invalid risk '{risk}'. Allowed: {self.VALID_RISKS}")

        return self.rules.get(risk, self.DEFAULT_ACTION)

    def to_dict(self):
        return {
            "rules": self.rules,
            "updated_at": self.updated_at.isoformat()
        }
