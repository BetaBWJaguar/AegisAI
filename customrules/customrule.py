import re
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from bson import ObjectId

from customrules.customrule_action import CustomRuleAction
from customrules.customrule_type import CustomRuleType


@dataclass
class CustomRule:
    id: uuid.UUID
    name: str
    rule_type: CustomRuleType
    pattern: str
    action: CustomRuleAction
    description: Optional[str] = None
    scope: Optional[str] = None
    priority: int = 0
    enabled: bool = True
    case_sensitive: bool = False
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    workspace_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: str = field(default_factory=lambda: str(ObjectId()))
    hit_count: int = 0
    last_triggered_at: Optional[datetime] = None
    replace_text: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"CustomRule(id={self.id}, name={self.name!r}, "
            f"rule_type={self.rule_type.value}, action={self.action.value}, "
            f"enabled={self.enabled}, priority={self.priority}, "
            f"hit_count={self.hit_count})"
        )

    def validate_pattern(self) -> bool:
        if not self.pattern or not self.pattern.strip():
            raise ValueError("Pattern cannot be empty.")

        if self.rule_type == CustomRuleType.REGEX:
            try:
                re.compile(self.pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")

        elif self.rule_type == CustomRuleType.KEYWORD:
            if len(self.pattern.strip()) < 2:
                raise ValueError("Keyword pattern must be at least 2 characters long.")

        elif self.rule_type == CustomRuleType.WILDCARD:
            if "*" not in self.pattern and "?" not in self.pattern:
                raise ValueError(
                    "Wildcard pattern must contain at least one '*' or '?' character."
                )

        elif self.rule_type == CustomRuleType.PATTERN:
            try:
                re.compile(self.pattern)
            except re.error as e:
                raise ValueError(f"Invalid pattern syntax: {e}")

        elif self.rule_type == CustomRuleType.EXACT:
            if len(self.pattern.strip()) < 1:
                raise ValueError("Exact pattern must be at least 1 character long.")

        if self.action == CustomRuleAction.REPLACE and not self.replace_text:
            raise ValueError(
                "replace_text is required when action is REPLACE."
            )

        return True

    def record_hit(self) -> None:
        self.hit_count += 1
        self.last_triggered_at = datetime.utcnow()

    @staticmethod
    def create(
        name: str,
        rule_type: CustomRuleType,
        pattern: str,
        action: CustomRuleAction,
        description: str = "",
        scope: Optional[str] = None,
        priority: int = 0,
        enabled: bool = True,
        case_sensitive: bool = False,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
        created_by: Optional[str] = None,
        replace_text: Optional[str] = None,
    ) -> "CustomRule":
        now = datetime.utcnow()
        return CustomRule(
            id=uuid.uuid4(),
            name=name,
            rule_type=rule_type,
            pattern=pattern,
            action=action,
            description=description,
            scope=scope,
            priority=priority,
            enabled=enabled,
            case_sensitive=case_sensitive,
            tags=tags or [],
            metadata=metadata or {},
            workspace_id=workspace_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            replace_text=replace_text,
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["rule_type"] = self.rule_type.value
        data["action"] = self.action.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["hit_count"] = self.hit_count
        data["last_triggered_at"] = (
            self.last_triggered_at.isoformat() if self.last_triggered_at else None
        )
        data["replace_text"] = self.replace_text
        data.pop("_id", None)
        return data
