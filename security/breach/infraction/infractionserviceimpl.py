from typing import Optional
from security.breach.actions.actiondecision import ActionDecision
from security.breach.actions.actionpolicy import DoxxingActionPolicy
from security.breach.doxxing_detector import DoxxingDetector
from security.breach.doxxing_settings import DoxxingSettings
from security.breach.infraction.infraction_result import InfractionResult
from security.breach.infraction.infractionservice import InfractionService

try:
    from security.breach.pii_detector import PIIDetector
    from security.breach.context_detector import ContextDetector
    from security.breach.socialmediaformats import SocialMediaDetector
except Exception:
    PIIDetector = None
    ContextDetector = None
    SocialMediaDetector = None


class InfractionServiceImpl(InfractionService):

    DEFAULT_RISK_LEVELS = [
        ("CRITICAL", 2.40),
        ("HIGH", 1.80),
        ("MEDIUM", 1.20),
        ("LOW", 0.00),
    ]

    def analyze(self, text: str, doxxing_settings: Optional[DoxxingSettings] = None, lang_code: str = "tr") -> InfractionResult:
        if doxxing_settings is None:
            doxxing_settings = DoxxingSettings()

        if not doxxing_settings.enabled:
            return InfractionResult(
                is_violation=False,
                risk_tier="LOW",
                decision=ActionDecision(action="ALLOW"),
                score=0.0,
                details={"enabled": False}
            )

        explanation = self._analyze_text(text, doxxing_settings, lang_code)

        score = explanation["score"]
        is_doxxing = explanation["is_doxxing"]

        risk_tier = self._resolve_risk_tier(score, explanation, doxxing_settings)

        decision = DoxxingActionPolicy.decide(risk_tier, doxxing_settings)

        return InfractionResult(
            is_violation=is_doxxing,
            risk_tier=risk_tier,
            decision=decision,
            score=score,
            details=explanation
        )

    def _analyze_text(self, text: str, doxxing_settings: DoxxingSettings, lang_code: str = "tr") -> dict:
        text = DoxxingDetector._normalize(text)

        pii_kinds = set()
        pii_signals = []
        if PIIDetector:
            signals = PIIDetector.detect(text)
            for signal in signals:
                if doxxing_settings.is_pii_enabled(signal.kind):
                    pii_kinds.add(signal.kind)
                    pii_signals.append({
                        "kind": signal.kind,
                        "spans": signal.spans
                    })

        context_info = {}
        if ContextDetector:
            has_person = ContextDetector.has_person(text, lang_code)
            has_target = ContextDetector.has_target_reference(text, lang_code)
            has_address = ContextDetector.has_address_hint(text, lang_code)
            has_intent = ContextDetector.has_expose_intent(text, lang_code)
            has_health_ctx = ContextDetector.has_health_context(text, lang_code)
            has_vehicle_ctx = ContextDetector.has_vehicle_context(text, lang_code)
            
            context_info = {
                "has_person": has_person,
                "has_target": has_target,
                "has_address_hint": has_address,
                "has_expose_intent": has_intent,
                "has_health": has_health_ctx,
                "has_vehicle": has_vehicle_ctx
            }

        has_social = False
        social_signals = []
        if doxxing_settings.detect_social_media and SocialMediaDetector:
            social_signals_list = SocialMediaDetector.detect(text)
            if social_signals_list:
                has_social = True
                social_signals = [
                    {"platform": s.platform, "spans": s.spans}
                    for s in social_signals_list
                ]

        self_disc = False
        if ContextDetector:
            self_disc = ContextDetector.is_self_disclosure(text, lang_code)

        hard_trigger = False
        high_risk_kinds = {"credit_card", "ssn", "passport", "fingerprint", "dna", "iban"}
        if pii_kinds & high_risk_kinds:
            if has_intent or has_target:
                hard_trigger = True

        score = DoxxingDetector._compute_score(
            kinds=pii_kinds,
            has_person=context_info.get("has_person", False),
            has_target=context_info.get("has_target", False),
            has_address=context_info.get("has_address_hint", False),
            has_intent=context_info.get("has_expose_intent", False),
            self_disc=self_disc,
            has_social=has_social,
            has_health_ctx=context_info.get("has_health", False),
            has_vehicle_ctx=context_info.get("has_vehicle", False),
        )

        if doxxing_settings.pii_config:
            for kind in pii_kinds:
                if doxxing_settings.is_pii_enabled(kind):
                    default_weight = DoxxingDetector.WEIGHTS.get(kind, 0.0)
                    custom_weight = doxxing_settings.get_pii_weight(kind, default_weight)
                    if custom_weight != default_weight:
                        score += (custom_weight - default_weight)
        
        if doxxing_settings.context_config:
            for ctx_key, ctx_value in context_info.items():
                if ctx_value and doxxing_settings.is_context_enabled(ctx_key):
                    default_weight = DoxxingDetector.CONTEXT_WEIGHTS.get(ctx_key, 0.0)
                    custom_weight = doxxing_settings.get_context_weight(ctx_key, default_weight)
                    if custom_weight != default_weight:
                        score += (custom_weight - default_weight)

        if self_disc and doxxing_settings.allow_self_disclosure:
            score -= doxxing_settings.self_disclosure_penalty

        is_doxxing = score >= doxxing_settings.threshold or hard_trigger
        
        return {
            "score": score,
            "is_doxxing": is_doxxing,
            "hard_trigger": hard_trigger,
            "detected_kinds": list(pii_kinds),
            "context": context_info,
            "has_social": has_social,
            "self_disclosure": self_disc,
            "pii_signals": pii_signals,
            "social_signals": social_signals,
            "threshold": doxxing_settings.threshold
        }

    def _resolve_risk_tier(self, score: float, explain: dict, doxxing_settings: DoxxingSettings) -> str:
        if explain.get("hard_trigger"):
            return "CRITICAL"

        threshold = doxxing_settings.threshold

        if score >= 2.40:
            return "CRITICAL"
        elif score >= 1.80:
            return "HIGH"
        elif score >= threshold:
            return "MEDIUM"
        else:
            return "LOW"

    def analyze_risk(self, text: str, doxxing_settings: Optional[DoxxingSettings] = None, lang_code: str = "tr") -> tuple[str, float, bool]:
        r = self.analyze(text, doxxing_settings, lang_code)
        return r.risk_tier, r.score, r.is_violation

    def decide_action(self, text: str, doxxing_settings: Optional[DoxxingSettings] = None, lang_code: str = "tr") -> ActionDecision:
        return self.analyze(text, doxxing_settings, lang_code).decision

