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
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)
        data["rule_type"] = self.rule_type.value
        data["action"] = self.action.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data
