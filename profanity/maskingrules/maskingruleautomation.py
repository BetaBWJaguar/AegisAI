from profanity.maskingrules.maskingruleutil import MaskingRuleUtil


class MaskingRuleAutomation:

    @staticmethod
    def _calculate_risk(confidence: float) -> str:
        if confidence >= 0.95:
            return "CRITICAL"
        if confidence >= 0.85:
            return "HIGH"
        if confidence >= 0.70:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _value_or_str(obj):
        return obj.value if hasattr(obj, "value") else str(obj)

    @staticmethod
    def apply_if_needed(text, workspace, predicted_label, confidence):

        confidence = round(confidence, 4)

        result = {
            "masked_text": text,
            "masked": False,
            "blocked": False,
            "label": predicted_label,
            "mode": None,
            "threshold": None,
            "confidence": confidence,
            "risk": "LOW",
            "visibility": None,
            "advisory": {},
            "advisory_policy": {}
        }

        if not workspace or not getattr(workspace, "censor_settings", None):
            return result

        rule = workspace.censor_settings.get_rule(predicted_label)

        if not rule or not rule.mask:
            return result

        result["threshold"] = rule.threshold
        result["visibility"] = MaskingRuleAutomation._value_or_str(rule.visibility)

        if confidence < rule.threshold:
            return result

        if "***" in text and confidence < 0.90:
            return result


        mode = MaskingRuleAutomation._value_or_str(rule.mode)
        if confidence >= 0.90:
            mode = "FULL"

        result["mode"] = mode

        masked_text = MaskingRuleUtil.apply(text, mode)

        result.update({
            "masked_text": masked_text,
            "masked": True
        })


        risk = MaskingRuleAutomation._calculate_risk(confidence)
        result["risk"] = risk


        result["advisory"] = {
            "suggested_action": workspace.get_advisory_action(risk),
            "policy_version": getattr(workspace, "policy_version", "1.0")
        }

        result["advisory_policy"] = dict(workspace.advisory_policy)

        if masked_text.replace("*", "").strip() == "":
            result["blocked"] = True

        return result
