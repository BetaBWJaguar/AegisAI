from profanity.maskingrules.maskingruleutil import MaskingRuleUtil


class MaskingRuleAutomation:

    @staticmethod
    def apply_if_needed(text: str, workspace, predicted_label: str, confidence: float):
        if not workspace.censor_settings:
            return text, False, None

        rule = workspace.censor_settings.get_rule(predicted_label)
        if not rule:
            return text, False, None

        if not rule.mask:
            return text, False, None

        if confidence < rule.threshold:
            return text, False, None

        mode = rule.mode.value if hasattr(rule.mode, "value") else str(rule.mode)

        masked_text = MaskingRuleUtil.apply(text, mode)

        return masked_text, True, {
            "label": predicted_label,
            "mode": mode,
            "threshold": rule.threshold,
            "confidence": round(confidence, 4)
        }
