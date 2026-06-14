from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

from customrules.customrule_action import CustomRuleAction
from customrules.customrule_severity import RuleSeverity
from customrules.customrule_type import CustomRuleType


class RuleResponse(BaseModel):
    id: str
    name: str
    rule_type: CustomRuleType
    pattern: str
    action: CustomRuleAction
    description: Optional[str]
    scope: Optional[str]
    priority: int
    enabled: bool
    case_sensitive: bool
    tags: List[str]
    metadata: Dict[str, Any]
    workspace_id: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    hit_count: int = 0
    last_triggered_at: Optional[datetime] = None
    replace_text: Optional[str] = None
    expires_at: Optional[datetime] = None
    severity: RuleSeverity = RuleSeverity.MEDIUM
    cooldown_seconds: int = 0
    exceptions: List[str] = []
    last_fired_at: Optional[datetime] = None
