from profanity.maskingrules.maskingruleutil import MaskingRuleUtil


class MaskingRuleAutomation:

    @staticmethod
    def apply_if_needed(text, workspace, predicted_label, confidence):
        if not workspace or not workspace.censor_settings:
            return text, False, None

        rule = workspace.censor_settings.get_rule(predicted_label)
        if not rule or not rule.mask:
            return text, False, None

        if confidence < rule.threshold:
            return text, False, None

        if "***" in text and confidence < 0.90:
            return text, False, None

        mode = rule.mode.value if hasattr(rule.mode, "value") else str(rule.mode)

        if confidence >= 0.90:
            mode = "FULL"

        masked_text = MaskingRuleUtil.apply(text, mode)

        risk = "LOW"
        if confidence >= 0.95:
            risk = "CRITICAL"
        elif confidence >= 0.85:
            risk = "HIGH"
        elif confidence >= 0.70:
            risk = "MEDIUM"

        suggested_action = None
        policy_version = None

        if hasattr(workspace, "get_advisory_action"):
            suggested_action = workspace.get_advisory_action(risk)
            policy_version = getattr(workspace, "policy_version", "1.0")

        if masked_text.replace("*", "").strip() == "":
            return None, True, {
                "blocked": True,
                "label": predicted_label,
                "risk": risk,
                "confidence": round(confidence, 4),
                "advisory": {
                    "suggested_action": suggested_action,
                    "policy_version": policy_version,
                    "note": "Content fully masked by rule"
                }
            }

        return masked_text, True, {
            "label": predicted_label,
            "mode": mode,
            "threshold": rule.threshold,
            "confidence": round(confidence, 4),
            "risk": risk,
            "advisory": {
                "suggested_action": suggested_action,
                "policy_version": policy_version
            }
        }
