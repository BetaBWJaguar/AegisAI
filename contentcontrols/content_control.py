from dataclasses import dataclass
from typing import Optional, Dict

from contentcontrols.detectors.spam_control import SpamControl, SpamResult
from user.workspace import Workspace


@dataclass
class ContentDecision:
    allowed: bool
    reason: Optional[str] = None
    risk: Optional[str] = None
    action: Optional[str] = None
    metadata: Optional[Dict] = None


class ContentControlEngine:

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

        self.spam_control = SpamControl(
            workspace.content_control_settings.spam
        )

    def evaluate(self, user_id: str, message: str, user_role: Optional[str] = None) -> ContentDecision:

        settings = self.workspace.content_control_settings

        if not settings.enabled:
            return ContentDecision(True)

        if not message or not message.strip():
            return ContentDecision(
                allowed=False,
                reason="Empty message",
                risk="LOW",
                action=self.workspace.get_advisory_action("LOW")
            )

        spam_result: SpamResult = self.spam_control.check(
            user_id=user_id,
            message=message,
            user_role=user_role
        )

        if not spam_result.allowed:
            risk_level = spam_result.risk.value if spam_result.risk else "LOW"
            action = self.workspace.get_advisory_action(risk_level)

            return ContentDecision(
                allowed=False,
                reason=spam_result.reason,
                risk=risk_level,
                action=action,
                metadata={
                    "type": spam_result.spam_type.value if spam_result.spam_type else None
                }
            )

        return ContentDecision(True)