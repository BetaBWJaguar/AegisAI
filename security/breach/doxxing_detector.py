import re
from typing import Dict, Set, Tuple

from security.breach.context_detector import ContextDetector
from security.breach.pii_detector import PIIDetector
try:
    from security.breach.socialmediaformats import SocialMediaDetector
except Exception:
    SocialMediaDetector = None


class DoxxingDetector:

    _ZWSP_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
    _WS_RE = re.compile(r"\s+")

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        text = DoxxingDetector._ZWSP_RE.sub("", text)
        text = DoxxingDetector._WS_RE.sub(" ", text).strip()
        return text

    DEFAULT_THRESHOLD = 1.20
    WEIGHTS: Dict[str, float] = {
        "email": 0.30,
        "phone": 0.45,
        "ipv4": 0.25,
        "coord": 0.55,
        "maps": 0.55,
        "id_number": 0.60,
        "iban": 0.65,
        "credit_card": 0.95,
        "url": 0.20,
        "birthdate": 0.35,
        "vin": 0.55,
        "health": 0.40,
    }

    CONTEXT_WEIGHTS: Dict[str, float] = {
        "has_person": 0.35,
        "has_target": 0.25,
        "has_address_hint": 0.35,
        "has_expose_intent": 0.45,
        "has_social": 0.30,
        "has_health": 0.30,
        "has_vehicle": 0.30,
    }

    CORRELATIONS: Dict[Tuple[str, str], float] = {
        ("phone", "coord"): 0.60,
        ("phone", "maps"): 0.60,
        ("email", "phone"): 0.45,
        ("email", "id_number"): 0.55,
        ("phone", "id_number"): 0.65,
        ("iban", "id_number"): 0.70,
        ("credit_card", "id_number"): 0.85,
        ("coord", "maps"): 0.35,
        ("url", "id_number"): 0.35,
        ("url", "phone"): 0.35,
        ("birthdate", "id_number"): 0.70,
        ("birthdate", "phone"): 0.45,
        ("vin", "phone"): 0.40,
        ("health", "id_number"): 0.50,
    }

    LOW_RISK_ALONE: Set[str] = {"url", "ipv4"}

    EMAIL_ALONE_ALLOW = True
    SELF_DISCLOSURE_PENALTY = 0.40
    MULTI_KIND_BONUS = 0.25

    @staticmethod
    def _has_pair(kinds: Set[str], a: str, b: str) -> bool:
        return a in kinds and b in kinds

    @staticmethod
    def _compute_score(
            kinds: Set[str],
            has_person: bool,
            has_target: bool,
            has_address: bool,
            has_intent: bool,
            self_disc: bool,
            has_social: bool,
            has_health_ctx: bool,
            has_vehicle_ctx: bool,
    ) -> float:
        score = 0.0

        for k in kinds:
            score += DoxxingDetector.WEIGHTS.get(k, 0.0)
        if len(kinds) >= 2:
            score += DoxxingDetector.MULTI_KIND_BONUS
        if has_person:
            score += DoxxingDetector.CONTEXT_WEIGHTS["has_person"]
        if has_target:
            score += DoxxingDetector.CONTEXT_WEIGHTS["has_target"]
        if has_address:
            score += DoxxingDetector.CONTEXT_WEIGHTS["has_address_hint"]
        if has_intent:
            score += DoxxingDetector.CONTEXT_WEIGHTS["has_expose_intent"]
        if has_social:
            score += DoxxingDetector.CONTEXT_WEIGHTS["has_social"]
        if has_health_ctx:
            score += DoxxingDetector.CONTEXT_WEIGHTS["has_health"]
        if has_vehicle_ctx:
            score += DoxxingDetector.CONTEXT_WEIGHTS["has_vehicle"]

        for (a, b), bonus in DoxxingDetector.CORRELATIONS.items():
            if DoxxingDetector._has_pair(kinds, a, b):
                score += bonus

        if has_social and ("phone" in kinds or "email" in kinds):
            score += 0.45

        if has_intent and (
                has_social or has_address or
                "coord" in kinds or "maps" in kinds
        ):
            score += 0.35

        if self_disc:
            score -= DoxxingDetector.SELF_DISCLOSURE_PENALTY

        return score

    @staticmethod
    def _early_exit_rules(
            kinds: Set[str],
            has_person: bool,
            has_target: bool,
            has_intent: bool,
            has_address: bool,
            has_social: bool,
    ) -> bool:
        if (
                kinds == {"email"}
                and DoxxingDetector.EMAIL_ALONE_ALLOW
                and not (has_person or has_target or has_intent)
        ):
            return True
        if (
                kinds.issubset(DoxxingDetector.LOW_RISK_ALONE)
                and not (has_person or has_target or has_intent or has_address or has_social)
        ):
            return True

        return False

    @staticmethod
    def is_doxxing(text: str, threshold: float = None) -> bool:
        threshold = DoxxingDetector.DEFAULT_THRESHOLD if threshold is None else float(threshold)
        text = DoxxingDetector._normalize(text)
        if not text:
            return False

        pii_signals = PIIDetector.detect(text)
        if not pii_signals:
            return False

        kinds = {s.kind for s in pii_signals}

        has_person = ContextDetector.has_person(text)
        has_target = ContextDetector.has_target_reference(text)
        has_address = ContextDetector.has_address_hint(text)
        has_intent = ContextDetector.has_expose_intent(text)
        self_disc = ContextDetector.is_self_disclosure(text)
        has_health_ctx = ContextDetector.has_health_context(text)
        has_vehicle_ctx = ContextDetector.has_vehicle_context(text)

        has_social = False
        if SocialMediaDetector is not None:
            try:
                has_social = bool(SocialMediaDetector.detect(text))
            except Exception:
                pass

        if has_intent and (has_person or has_target):
            if has_address:
                return True
            if {"birthdate", "health", "vin"} & kinds:
                return True

        if DoxxingDetector._early_exit_rules(
                kinds, has_person, has_target, has_intent, has_address, has_social
        ):
            return False

        score = DoxxingDetector._compute_score(
            kinds=kinds,
            has_person=has_person,
            has_target=has_target,
            has_address=has_address,
            has_intent=has_intent,
            self_disc=self_disc,
            has_social=has_social,
            has_health_ctx=has_health_ctx,
            has_vehicle_ctx=has_vehicle_ctx,
        )

        return score >= threshold

    @staticmethod
    def explain(text: str, threshold: float = None) -> dict:
        threshold = DoxxingDetector.DEFAULT_THRESHOLD if threshold is None else float(threshold)
        text_n = DoxxingDetector._normalize(text)

        pii_signals = PIIDetector.detect(text_n)
        kinds = {s.kind for s in pii_signals}

        has_person = ContextDetector.has_person(text_n)
        has_target = ContextDetector.has_target_reference(text_n)
        has_address = ContextDetector.has_address_hint(text_n)
        has_intent = ContextDetector.has_expose_intent(text_n)
        self_disc = ContextDetector.is_self_disclosure(text_n)
        has_health_ctx = ContextDetector.has_health_context(text_n)
        has_vehicle_ctx = ContextDetector.has_vehicle_context(text_n)

        has_social = False
        if SocialMediaDetector is not None:
            try:
                has_social = bool(SocialMediaDetector.detect(text_n))
            except Exception:
                pass

        early_exit = DoxxingDetector._early_exit_rules(
            kinds, has_person, has_target, has_intent, has_address, has_social
        )

        score = 0.0 if (not pii_signals or early_exit) else DoxxingDetector._compute_score(
            kinds=kinds,
            has_person=has_person,
            has_target=has_target,
            has_address=has_address,
            has_intent=has_intent,
            self_disc=self_disc,
            has_social=has_social,
            has_health_ctx=has_health_ctx,
            has_vehicle_ctx=has_vehicle_ctx,
        )

        hard_trigger = bool(
            has_intent and (has_person or has_target) and
            (has_address or {"birthdate", "health", "vin"} & kinds)
        )

        decision = True if hard_trigger else (False if early_exit else score >= threshold)

        return {
            "normalized": text_n,
            "pii_kinds": sorted(kinds),
            "has_person": has_person,
            "has_target_reference": has_target,
            "has_address_hint": has_address,
            "has_expose_intent": has_intent,
            "is_self_disclosure": self_disc,
            "has_social": has_social,
            "has_health_context": has_health_ctx,
            "has_vehicle_context": has_vehicle_ctx,
            "hard_trigger": hard_trigger,
            "early_exit": early_exit,
            "score": round(score, 4),
            "threshold": threshold,
            "is_doxxing": decision,
        }
