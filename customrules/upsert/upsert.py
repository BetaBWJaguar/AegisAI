from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from customrules.customrule_action import CustomRuleAction
from customrules.customrule_type import CustomRuleType


class RuleUpsert(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[CustomRuleType] = None
    pattern: Optional[str] = None
    action: Optional[CustomRuleAction] = None
    description: Optional[str] = None
    scope: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0, le=1000)
    enabled: Optional[bool] = None
    case_sensitive: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
