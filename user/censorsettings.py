from dataclasses import dataclass, field
from typing import Dict, Optional

from user.censormode import CensorMode
from user.censorvisibility import VisibilityMode


@dataclass
class CensorRule:
    mask: bool = False
    mode: CensorMode = CensorMode.PARTIAL
    threshold: float = 0.0
    visibility: VisibilityMode = VisibilityMode.PUBLIC


@dataclass
class CensorSettings:
    rules: Dict[str, CensorRule] = field(default_factory=dict)

    def get_rule(self, label: str) -> Optional[CensorRule]:
        return self.rules.get(label)

    def set_rule(self, label: str, rule: CensorRule):
        self.rules[label] = rule
