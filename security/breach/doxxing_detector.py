import re
from security.breach.context_detector import ContextDetector
from security.breach.pii_detector import PIIDetector


class DoxxingDetector:

    @staticmethod
    def _normalize(text: str) -> str:
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def is_doxxing(text: str) -> bool:
        text = DoxxingDetector._normalize(text)

        pii_signals = PIIDetector.detect(text)
        if not pii_signals:
            return False

        kinds = {s.kind for s in pii_signals}

        has_person  = ContextDetector.has_person(text)
        has_address = ContextDetector.has_address_hint(text)
        has_intent  = ContextDetector.has_expose_intent(text)
        self_disc   = ContextDetector.is_self_disclosure(text)

        if kinds == {"email"} and not (has_person or has_intent):
            return False

        score = 0.0

        weights = {
            "email": 0.30,
            "phone": 0.45,
            "ipv4":  0.25,
            "coord": 0.55,
            "maps":  0.55,
            "id_number": 0.60,
            "iban": 0.65,
            "url": 0.20,
        }

        for k in kinds:
            score += weights.get(k, 0.0)

        if len(kinds) >= 2:
            score += 0.25

        if has_person:
            score += 0.35
        if has_address:
            score += 0.35
        if has_intent:
            score += 0.45

        if self_disc:
            score -= 0.4

        if has_person and has_address and has_intent:
            return True

        return score >= 1.2
