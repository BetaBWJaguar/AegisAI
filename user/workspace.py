from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
from typing import List, Optional, Dict

from contentcontrols.utils.contentcontrolsettings import ContentControlSettings
from security.breach.doxxing_settings import DoxxingSettings
from trainer.modelregistry import ModelRegistry
from user.censorsettings import CensorSettings
from user.rule import Rule
from user.violations import Violation

VALID_RISKS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


@dataclass
class Workspace:
    id: uuid.UUID
    name: str
    description: str
    rules: List[Rule] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    censor_settings: CensorSettings = field(default_factory=CensorSettings)
    doxxing_settings: DoxxingSettings = field(default_factory=DoxxingSettings)
    language: str = "tr"
    bot_detection: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    advisory_policy: Dict[str, str] = field(
        default_factory=lambda: {
            "LOW": "LOG",
            "MEDIUM": "LOG",
            "HIGH": "LOG",
            "CRITICAL": "LOG"
        }
    )
    model_id: str = None
    model_name: str = None
    model_version: str = None
    content_control_settings: ContentControlSettings = field(default_factory=ContentControlSettings)

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
        self.model_version = model["version"]
        self.updated_at = datetime.utcnow()


    def add_rule(self, rule: Rule):
        self.rules.append(rule)
        self.updated_at = datetime.utcnow()


    def add_violation(self, violation: Violation):
        self.violations.append(violation)
        self.updated_at = datetime.utcnow()

    def set_advisory_policy(self, risk: str, action: str):
        risk = risk.upper()
        if risk not in VALID_RISKS:
            raise ValueError(f"Invalid risk '{risk}'. Allowed risks: {VALID_RISKS}")

        self.advisory_policy[risk] = action.upper()
        self.updated_at = datetime.utcnow()


    def get_advisory_action(self, risk: str) -> str:
        risk = risk.upper()
        if risk not in VALID_RISKS:
            raise ValueError(f"Invalid risk '{risk}'. Allowed risks: {VALID_RISKS}")

        return self.advisory_policy.get(risk, "LOG")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)

        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        if isinstance(self.updated_at, datetime):
            data["updated_at"] = self.updated_at.isoformat()
        data["rules"] = [r.to_dict() for r in self.rules]
        data["violations"] = [v.to_dict() for v in self.violations]

        if self.censor_settings and hasattr(self.censor_settings, "rules"):
            data["censor_settings"] = {
                label: {
                    "mask": rule.mask,
                    "mode": rule.mode.value if hasattr(rule.mode, "value") else str(rule.mode),
                    "threshold": rule.threshold
                }
                for label, rule in self.censor_settings.rules.items()
            }
        else:
            data["censor_settings"] = {}

        if self.doxxing_settings:
            data["doxxing_settings"] = self.doxxing_settings.to_dict()
        else:
            data["doxxing_settings"] = {}

        if self.content_control_settings:
            data["content_control_settings"] = {
                "enabled": self.content_control_settings.enabled,
                "spam": {
                    "enabled": self.content_control_settings.spam.enabled,
                    "rate_limit_count": self.content_control_settings.spam.rate_limit_count,
                    "rate_limit_window_seconds": self.content_control_settings.spam.rate_limit_window_seconds,
                    "duplicate_check": self.content_control_settings.spam.duplicate_check,
                    "duplicate_reset_seconds": self.content_control_settings.spam.duplicate_reset_seconds,
                    "burst_limit": self.content_control_settings.spam.burst_limit,
                    "cooldown_seconds": self.content_control_settings.spam.cooldown_seconds
                }
            }
        else:
            data["content_control_settings"] = {}

        return data