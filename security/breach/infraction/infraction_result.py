from dataclasses import dataclass
from typing import Dict, Any
from security.breach.actions.actiondecision import ActionDecision


@dataclass(frozen=True)
class InfractionResult:
    is_violation: bool
    risk_tier: str
    decision: ActionDecision
    score: float
    details: Dict[str, Any]
