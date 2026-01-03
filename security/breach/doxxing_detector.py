import re
from typing import Dict, Set, Tuple

try:
    from security.breach.socialmediaformats import SocialMediaDetector
except Exception:
    SocialMediaDetector = None


class DoxxingDetector:

    _ZWSP_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
    _WS_RE = re.compile(r"\s+")

    DEFAULT_THRESHOLD = 1.20
    EMAIL_ALONE_ALLOW = True
    SELF_DISCLOSURE_PENALTY = 0.40
    MULTI_KIND_BONUS = 0.25

    LOW_RISK_ALONE: Set[str] = {"url", "ipv4"}

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
        "bitcoin": 0.75,
        "ethereum": 0.75,
        "crypto_wallet": 0.70,
        "swift_bic": 0.60,
        "passport": 0.85,
        "driver_license": 0.70,
        "ssn": 0.90,
        "tax_id": 0.75,
        "national_id": 0.65,
        "student_id": 0.45,
        "university_email": 0.35,
        "fingerprint": 0.95,
        "dna": 0.95,
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
        ("crypto_wallet", "phone"): 0.55,
        ("crypto_wallet", "email"): 0.50,
        ("bitcoin", "ethereum"): 0.45,
        ("swift_bic", "iban"): 0.60,
        ("swift_bic", "id_number"): 0.55,
        ("passport", "birthdate"): 0.65,
        ("passport", "id_number"): 0.70,
        ("ssn", "birthdate"): 0.75,
        ("ssn", "id_number"): 0.80,
        ("tax_id", "id_number"): 0.60,
        ("driver_license", "birthdate"): 0.50,
        ("student_id", "university_email"): 0.70,
        ("fingerprint", "id_number"): 0.80,
        ("dna", "health"): 0.85,
    }

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        text = DoxxingDetector._ZWSP_RE.sub("", text)
        return DoxxingDetector._WS_RE.sub(" ", text).strip()

    @staticmethod
    def _detect_social(text: str) -> bool:
        if SocialMediaDetector is None:
            return False
        try:
            return bool(SocialMediaDetector.detect(text))
        except Exception:
            return False

    @staticmethod
    def _has_pair(kinds: Set[str], a: str, b: str) -> bool:
        return a in kinds and b in kinds

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

        score = sum(DoxxingDetector.WEIGHTS.get(k, 0.0) for k in kinds)

        if len(kinds) >= 2:
            score += DoxxingDetector.MULTI_KIND_BONUS

        score += (
                has_person * DoxxingDetector.CONTEXT_WEIGHTS["has_person"]
                + has_target * DoxxingDetector.CONTEXT_WEIGHTS["has_target"]
                + has_address * DoxxingDetector.CONTEXT_WEIGHTS["has_address_hint"]
                + has_intent * DoxxingDetector.CONTEXT_WEIGHTS["has_expose_intent"]
                + has_social * DoxxingDetector.CONTEXT_WEIGHTS["has_social"]
                + has_health_ctx * DoxxingDetector.CONTEXT_WEIGHTS["has_health"]
                + has_vehicle_ctx * DoxxingDetector.CONTEXT_WEIGHTS["has_vehicle"]
        )

        for (a, b), bonus in DoxxingDetector.CORRELATIONS.items():
            if DoxxingDetector._has_pair(kinds, a, b):
                score += bonus

        if has_social and ("phone" in kinds or "email" in kinds):
            score += 0.45

        if has_intent and (has_social or has_address or {"coord", "maps"} & kinds):
            score += 0.35

        if self_disc:
            score -= DoxxingDetector.SELF_DISCLOSURE_PENALTY

        return score
