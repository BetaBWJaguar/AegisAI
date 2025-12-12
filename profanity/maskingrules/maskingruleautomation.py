from profanity.maskingrules.maskingruleutil import MaskingRuleUtil


class MaskingRuleAutomation:

    @staticmethod
    def apply_if_needed(text, workspace, predicted_label, confidence):

        result = {
            "masked_text": text,
            "masked": False,
            "blocked": False,
            "label": predicted_label,
            "mode": None,
            "threshold": None,
            "confidence": round(confidence, 4),
            "risk": "LOW",
            "visibility": None,
            "advisory": {},
            "advisory_policy": {}
        }


        if not workspace or not workspace.censor_settings:
            return result


        rule = workspace.censor_settings.get_rule(predicted_label)
        if not rule or not rule.mask:
            return result

        result["threshold"] = rule.threshold

        result["visibility"] = (
            rule.visibility.value if hasattr(rule.visibility, "value") else str(rule.visibility)
        )


        if confidence < rule.threshold:
            return result

        if "***" in text and confidence < 0.90:
            return result

        mode = rule.mode.value if hasattr(rule.mode, "value") else str(rule.mode)
        if confidence >= 0.90:
            mode = "FULL"

        result["mode"] = mode
        masked_text = MaskingRuleUtil.apply(text, mode)
        result["masked_text"] = masked_text
        result["masked"] = True

        if confidence >= 0.95:
            result["risk"] = "CRITICAL"
        elif confidence >= 0.85:
            result["risk"] = "HIGH"
        elif confidence >= 0.70:
            result["risk"] = "MEDIUM"
        else:
            result["risk"] = "LOW"

        risk = result["risk"]
        advisory_action = workspace.get_advisory_action(risk)

        policy_version = getattr(workspace, "policy_version", "1.0")

        result["advisory"] = {
            "suggested_action": advisory_action,
            "policy_version": policy_version
        }

        result["advisory_policy"] = {
            risk: action
            for risk, action in workspace.advisory_policy.items()
        }

        if masked_text.replace("*", "").strip() == "":
            result["blocked"] = True
            return result

        return result
