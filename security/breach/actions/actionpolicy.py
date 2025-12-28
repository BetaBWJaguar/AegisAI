from typing import Dict

from security.breach.actions.actiondecision import ActionDecision


class DoxxingActionPolicy:
    POLICY: Dict[str, ActionDecision] = {

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
    def decide(risk_tier: str) -> ActionDecision:
        return DoxxingActionPolicy.POLICY.get(
            risk_tier.upper(),
            DoxxingActionPolicy.POLICY["LOW"]
        )
