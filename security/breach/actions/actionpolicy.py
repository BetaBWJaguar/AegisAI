from typing import Dict, Optional

from security.breach.actions.actiondecision import ActionDecision
from security.breach.doxxing_settings import DoxxingSettings


class DoxxingActionPolicy:
    DEFAULT_POLICY: Dict[str, ActionDecision] = {

        "LOW": ActionDecision(
            action="ALLOW",
            notify_user=False,
            notify_admin=False,
            mask_content=False,
            log_event=False
        ),

        "MEDIUM": ActionDecision(
            action="WARN",
            notify_user=True,
            notify_admin=False,
            mask_content=False,
            log_event=True,
            reason="Potential sensitive information detected"
        ),

        "HIGH": ActionDecision(
            action="MASK",
            notify_user=True,
            notify_admin=True,
            mask_content=True,
            log_event=True,
            reason="Sensitive personal information detected"
        ),

        "CRITICAL": ActionDecision(
            action="BLOCK",
            notify_user=True,
            notify_admin=True,
            mask_content=True,
            log_event=True,
            reason="Doxxing attempt detected"
        ),
    }

    @staticmethod
    def decide(risk_tier: str, doxxing_settings: Optional[DoxxingSettings] = None) -> ActionDecision:
        if doxxing_settings is None:
            doxxing_settings = DoxxingSettings()

        risk_upper = risk_tier.upper()

        action = doxxing_settings.get_action_for_risk(risk_upper)

        default_decision = DoxxingActionPolicy.DEFAULT_POLICY.get(
            risk_upper,
            DoxxingActionPolicy.DEFAULT_POLICY["LOW"]
        )

        return ActionDecision(
            action=action,
            notify_user=doxxing_settings.notify_user and default_decision.notify_user,
            notify_admin=doxxing_settings.notify_admin and default_decision.notify_admin,
            mask_content=doxxing_settings.mask_content and default_decision.mask_content,
            log_event=doxxing_settings.log_violations and default_decision.log_event,
            reason=default_decision.reason
        )
