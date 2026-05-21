import logging
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict, TYPE_CHECKING

from contentcontrols.detectors.spam_control import SpamControl, SpamResult
from customrules.customrule import CustomRule
from customrules.customruleengine import CustomRuleEngine, EngineConfig, EngineVerdict
from user.workspace import Workspace

if TYPE_CHECKING:
    from contentcontrols.content_metrics import ContentMetrics

logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        workspace: Workspace,
        metrics: Optional['ContentMetrics'] = None,
        rules_provider: Optional[Callable[[str], List[CustomRule]]] = None,
    ):
        self.workspace = workspace
        self._metrics = metrics
        self._rules_provider = rules_provider
        self._rule_engine = CustomRuleEngine(config=EngineConfig())

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

        processed_message = message
        custom_rule_meta: Dict = {}

        if self._rules_provider is not None:
            try:
                workspace_id = str(self.workspace.id)
                rules = self._rules_provider(workspace_id)

                if rules:
                    engine_result = self._rule_engine.evaluate(message, rules)

                    if engine_result.verdict == EngineVerdict.BLOCKED:
                        blocked_rule = engine_result.triggered_rules[0] if engine_result.triggered_rules else None
                        return ContentDecision.deny(
                            reason="custom_rule_blocked",
                            risk="HIGH",
                            action=self.workspace.get_advisory_action("HIGH"),
                            score=1.0,
                            metadata={
                                "detector": "custom_rule_engine",
                                "verdict": engine_result.verdict.value,
                                "blocked_by": {
                                    "rule_id": blocked_rule.rule_id,
                                    "rule_name": blocked_rule.rule_name,
                                } if blocked_rule else None,
                                "triggered_rule_count": engine_result.triggered_rule_count,
                                "message_length": len(message),
                                "user_id": user_id,
                                **metadata,
                            },
                        )

                    if engine_result.matched:
                        processed_message = engine_result.processed_text
                        custom_rule_meta = {
                            "custom_rule_verdict": engine_result.verdict.value,
                            "custom_rule_triggered_count": engine_result.triggered_rule_count,
                            "custom_rule_triggered": [
                                {
                                    "rule_id": tr.rule_id,
                                    "rule_name": tr.rule_name,
                                    "action": tr.action,
                                    "match_count": tr.match_count,
                                }
                                for tr in engine_result.triggered_rules
                            ],
                        }

                    if self._metrics:
                        rule_response_time = (time.time() - start_time) * 1000
                        self._metrics.record_detector_performance(
                            detector_type="custom_rule_engine",
                            response_time_ms=rule_response_time,
                            blocked=engine_result.verdict == EngineVerdict.BLOCKED,
                        )
            except Exception:
                logger.exception(
                    "Custom rule evaluation failed for workspace %s",
                    getattr(self.workspace, "id", "unknown"),
                )

        response_time_ms = (time.time() - start_time) * 1000
        return ContentDecision(
            allowed=True,
            metadata={
                "detector": "clean",
                "message_length": len(processed_message),
                "user_id": user_id,
                "response_time_ms": response_time_ms,
                "processed_message": processed_message,
                **custom_rule_meta,
                **metadata,
            },
        )