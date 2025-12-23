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

        has_person = ContextDetector.has_person(text)
        has_address = ContextDetector.has_address_hint(text)
        has_intent = ContextDetector.has_expose_intent(text)

        score = 0.0
        kinds = {s.kind for s in pii_signals}

        if "email" in kinds: score += 0.35
        if "phone" in kinds: score += 0.45
        if "ipv4" in kinds:  score += 0.25
        if "coord" in kinds: score += 0.55
        if "maps" in kinds:  score += 0.55

        if has_person:  score += 0.35
        if has_address: score += 0.35
        if has_intent:  score += 0.45

        if has_person and has_address and has_intent:
            return True

        return score >= 1.2
