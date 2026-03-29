import time
from dataclasses import dataclass, field
from typing import Optional, Dict, TYPE_CHECKING

from contentcontrols.detectors.spam_control import SpamControl, SpamResult
from user.workspace import Workspace

if TYPE_CHECKING:
    from contentcontrols.content_metrics import ContentMetrics


@dataclass
class ContentDecision:
    allowed: bool
    reason: Optional[str] = None
    risk: Optional[str] = None
    action: Optional[str] = None
    score: float = 0.0
    metadata: Dict = field(default_factory=dict)

    @staticmethod
    def allow():
        return ContentDecision(True, reason="allowed")

    @staticmethod
    def deny(reason: str, risk: str = "LOW", action: Optional[str] = None, score: float = 0.0, metadata: Optional[Dict] = None):
        return ContentDecision(
            allowed=False,
            reason=reason,
            risk=risk,
            action=action,
            score=score,
            metadata=metadata or {}
        )


class ContentControlEngine:

    def __init__(self, workspace: Workspace, metrics: Optional['ContentMetrics'] = None):
        self.workspace = workspace
        self._metrics = metrics

        self.spam_control = SpamControl(
            workspace.content_control_settings.spam,
            metrics=metrics
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

    def evaluate(
            self,
            user_id: str,
            message: str,
            user_role: Optional[str] = None,
            metadata: Optional[Dict] = None
    ) -> ContentDecision:
        start_time = time.time()
        
        settings = self.workspace.content_control_settings
        metadata = metadata or {}

        if not settings.enabled:
            response_time_ms = (time.time() - start_time) * 1000
            return ContentDecision.allow()

        if not message or not message.strip():
            return ContentDecision.deny(
                reason="empty_message",
                risk="LOW",
                action=self.workspace.get_advisory_action("LOW"),
                metadata={
                    "detector": "engine",
                    "message_length": 0,
                    "user_id": user_id
                }
            )

        if len(message) > getattr(settings, "max_message_length", 5000):
            return ContentDecision.deny(
                reason="message_too_long",
                risk="MEDIUM",
                action=self.workspace.get_advisory_action("MEDIUM"),
                metadata={
                    "detector": "engine",
                    "message_length": len(message),
                    "user_id": user_id
                }
            )

        if user_role and user_role in getattr(settings, "bypass_roles", []):
            return ContentDecision.allow()

        spam_result: SpamResult = self.spam_control.check(
            user_id=user_id,
            message=message,
            user_role=user_role
        )

        if self._metrics:
            detector_response_time = (time.time() - start_time) * 1000
            self._metrics.record_detector_performance(
                detector_type="spam_control",
                response_time_ms=detector_response_time,
                blocked=not spam_result.allowed
            )

        if not spam_result.allowed:
            if settings.use_score_based_decision and settings.score_thresholds.enabled:
                risk_level = self._determine_risk_from_score(spam_result.score)
                decision_mode = "score_based"
            else:
                risk_level = spam_result.risk.value if spam_result.risk else "LOW"
                decision_mode = "risk_based"

            action = self.workspace.get_advisory_action(risk_level)

            return ContentDecision.deny(
                reason=spam_result.reason or "spam_detected",
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
                    "decision_mode": decision_mode,
                    **metadata
                }
            )

        response_time_ms = (time.time() - start_time) * 1000
        return ContentDecision(
            allowed=True,
            metadata={
                "detector": "clean",
                "message_length": len(message),
                "user_id": user_id,
                "response_time_ms": response_time_ms,
                **metadata
            }
        )