from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from customrules.customrule_type import CustomRuleType
from customrules.customrule_action import CustomRuleAction


class RuleCreate(BaseModel):
    name: str
    rule_type: CustomRuleType
    pattern: str
    action: CustomRuleAction
    description: Optional[str] = ""
    scope: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=1000)
    enabled: bool = True
    case_sensitive: bool = False
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    workspace_id: Optional[str] = None
    replace_text: Optional[str] = None
