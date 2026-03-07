from dataclasses import dataclass, field
from typing import Optional, Dict

from contentcontrols.detectors.spam_control import SpamControl, SpamResult
from user.workspace import Workspace


@dataclass
class ContentDecision:
    allowed: bool
    reason: Optional[str] = None
    risk: Optional[str] = None
    action: Optional[str] = None
    score: float = 0.0
    metadata: Dict = field(default_factory=dict)


class ContentControlEngine:

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

        self.spam_control = SpamControl(
            workspace.content_control_settings.spam
        )

    def _determine_risk_from_score(self, score: float) -> str:
        settings = self.workspace.content_control_settings
        thresholds = settings.score_thresholds
        
        if not thresholds.enabled:
            return "LOW"
        
        if score >= thresholds.critical_threshold:
            return "CRITICAL"
        elif score >= thresholds.high_threshold:
            return "HIGH"
        elif score >= thresholds.medium_threshold:
            return "MEDIUM"
        else:
            return "LOW"

    def evaluate(self, user_id: str, message: str, user_role: Optional[str] = None) -> ContentDecision:

        settings = self.workspace.content_control_settings

        if not settings.enabled:
            return ContentDecision(True)

        if not message or not message.strip():
            return ContentDecision(
                allowed=False,
                reason="Empty message",
                risk="LOW",
                action=self.workspace.get_advisory_action("LOW"),
                metadata={
                    "detector": "engine",
                    "message_length": 0,
                    "user_id": user_id
                }
            )

        spam_result: SpamResult = self.spam_control.check(
            user_id=user_id,
            message=message,
            user_role=user_role
        )

        if not spam_result.allowed:
            if settings.use_score_based_decision and settings.score_thresholds.enabled:
                risk_level = self._determine_risk_from_score(spam_result.score)
            else:
                risk_level = spam_result.risk.value if spam_result.risk else "LOW"
            
            action = self.workspace.get_advisory_action(risk_level)

            return ContentDecision(
                allowed=False,
                reason=spam_result.reason,
                risk=risk_level,
                action=action,
                score=spam_result.score,
                metadata={
                    "detector": "spam_control",
                    "spam_type": spam_result.spam_type.value if spam_result.spam_type else None,
                    "score": spam_result.score,
                    "repeat_count": getattr(spam_result, "repeat_count", None),
                    "message_length": len(message),
                    "user_id": user_id,
                    "user_role": user_role,
                    "decision_mode": "score_based" if settings.use_score_based_decision else "risk_based"
                }
            )

        return ContentDecision(True)